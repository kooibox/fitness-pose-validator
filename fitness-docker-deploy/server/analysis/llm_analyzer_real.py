"""
LLM 分析器真实实现

接入硅基流动 API 进行训练报告生成。
使用 Qwen/Qwen2.5-72B-Instruct 模型。
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .llm_analyzer import (
    LLMAnalyzerInterface,
    LLMAnalysisRequest,
    LLMAnalysisResponse,
    AnalysisType,
    AnalysisStatus,
)
from .data_preprocessor import DataPreprocessor
from .prompt_templates import PromptBuilder


class LLMAnalyzerReal(LLMAnalyzerInterface):
    """
    LLM 分析器真实实现
    
    支持硅基流动 API，使用 Qwen/Qwen2.5-72B-Instruct 模型。
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        db_path: Optional[Path] = None,
        base_url: Optional[str] = None,
        response_mode: str = "json",  # "json" 或 "raw"
    ):
        """
        初始化分析器
        
        Args:
            api_key: API 密钥，默认从环境变量读取
            model: 模型名称，默认为 Qwen/Qwen2.5-72B-Instruct
            db_path: 数据库路径
            base_url: API 基础 URL
            response_mode: 响应模式 ("json" 或 "raw")
        """
        self.api_key = api_key or os.environ.get("SILICONFLOW_API_KEY")
        self.model = model or os.environ.get("SILICONFLOW_MODEL", "Qwen/Qwen2.5-72B-Instruct")
        self.base_url = base_url or os.environ.get(
            "SILICONFLOW_BASE_URL", 
            "https://api.siliconflow.cn/v1"
        )
        self.db_path = db_path
        self.response_mode = response_mode
        
        if not self.api_key:
            raise ValueError("API 密钥未设置，请设置 SILICONFLOW_API_KEY 环境变量")
        
        # 初始化子模块
        self.preprocessor = DataPreprocessor(db_path)
        self.prompt_builder = PromptBuilder()
        
        # 初始化 LLM 客户端
        self.client = self._init_client()
        
        # 结果缓存
        self._results: Dict[str, LLMAnalysisResponse] = {}
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        try:
            from openai import OpenAI
            return OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError("请安装 openai 库: pip install openai")
    
    async def analyze(self, request: LLMAnalysisRequest) -> LLMAnalysisResponse:
        """
        执行分析
        
        Args:
            request: 分析请求
            
        Returns:
            LLMAnalysisResponse: 分析响应
        """
        try:
            # 1. 数据预处理
            training_data = self.preprocessor.prepare(
                session_ids=request.session_ids,
                analysis_type=request.analysis_type,
            )
            
            # 2. 构建 Prompt
            prompt = self.prompt_builder.build(
                analysis_type=request.analysis_type,
                training_data=training_data,
                language=request.language,
            )
            
            # 3. 调用 LLM API
            llm_response = self._call_llm(prompt)
            
            # 4. 解析响应
            response = self._parse_response(
                request_id=request.request_id,
                llm_output=llm_response,
            )
            
            # 5. 缓存结果
            self._results[request.request_id] = response
            
            return response
            
        except Exception as e:
            return LLMAnalysisResponse(
                request_id=request.request_id,
                status=AnalysisStatus.FAILED,
                error=str(e),
                completed_at=datetime.now().isoformat(),
            )
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM API"""
        import urllib.request
        import urllib.error
        
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': self.model,
            'messages': [
                {
                    "role": "system",
                    "content": "你是一位专业的健身教练，擅长分析训练数据并提供科学的训练建议。请以 JSON 格式返回分析结果。"
                },
                {"role": "user", "content": prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000,
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = response.read().decode('utf-8')
                
                # 处理流式响应（多个JSON对象）
                if result.startswith('{"id"'):
                    # 尝试解析多个JSON对象
                    parts = result.split('}{"id"')
                    if len(parts) > 1:
                        # 重新组合并解析每个部分
                        json_objects = []
                        for i, part in enumerate(parts):
                            if i == 0:
                                json_str = part + '}'
                            else:
                                json_str = '{"id"' + part if not part.endswith('}') else '{"id"' + part
                            try:
                                obj = json.loads(json_str)
                                if obj.get('choices') and obj['choices'][0].get('message'):
                                    json_objects.append(obj)
                            except:
                                pass
                        
                        # 合并所有消息
                        full_content = ''
                        for obj in json_objects:
                            if obj.get('choices') and obj['choices'][0].get('message'):
                                content = obj['choices'][0]['message'].get('content', '')
                                if content:
                                    full_content += content
                        
                        if full_content:
                            return full_content
                
                # 尝试解析单个JSON
                try:
                    obj = json.loads(result)
                    if obj.get('choices') and obj['choices'][0].get('message'):
                        return obj['choices'][0]['message'].get('content', '')
                except:
                    pass
                
                return result
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            raise Exception(f"API请求失败: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"API请求失败: {str(e)}")
    
    def _extract_json_from_text(self, text: str) -> str:
        import re
        
        text = text.strip()
        
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```.*$', '', text, flags=re.MULTILINE)
        
        depth = 0
        start = -1
        for i, char in enumerate(text):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    return text[start:i+1]
        
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return match.group()
        
        return text
    
    def _parse_response(
        self,
        request_id: str,
        llm_output: str,
    ) -> LLMAnalysisResponse:
        if self.response_mode == "raw":
            return LLMAnalysisResponse(
                request_id=request_id,
                status=AnalysisStatus.COMPLETED,
                summary=llm_output,
                insights=[],
                suggestions=[],
                score=None,
                metadata={"raw_response": True},
                completed_at=datetime.now().isoformat(),
            )
        
        try:
            json_str = self._extract_json_from_text(llm_output)
            data = json.loads(json_str)
            
            insights = data.get("insights", [])
            if insights is None:
                insights = []
            elif isinstance(insights, str):
                insights = [insights]
            
            suggestions = data.get("suggestions", [])
            if suggestions is None:
                suggestions = []
            elif isinstance(suggestions, str):
                suggestions = [suggestions]
            
            return LLMAnalysisResponse(
                request_id=request_id,
                status=AnalysisStatus.COMPLETED,
                summary=data.get("summary", "") or "",
                insights=insights,
                suggestions=suggestions,
                score=data.get("score"),
                metadata=data.get("metadata"),
                completed_at=datetime.now().isoformat(),
            )
        
        except json.JSONDecodeError as e:
            print(f"[LLM] JSON解析失败: {e}")
            print(f"[LLM] 原始输出前500字符: {llm_output[:500]}")
            return LLMAnalysisResponse(
                request_id=request_id,
                status=AnalysisStatus.COMPLETED,
                summary=llm_output,
                insights=[],
                suggestions=[],
                score=None,
                metadata={"raw_response": True, "json_parse_error": str(e)},
                completed_at=datetime.now().isoformat(),
            )
        except Exception as e:
            print(f"[LLM] 解析异常: {e}")
            return LLMAnalysisResponse(
                request_id=request_id,
                status=AnalysisStatus.COMPLETED,
                summary=llm_output,
                insights=[],
                suggestions=[],
                score=None,
                metadata={"raw_response": True, "error": str(e)},
                completed_at=datetime.now().isoformat(),
            )
    
    def get_status(self, request_id: str) -> Optional[LLMAnalysisResponse]:
        """获取分析状态"""
        return self._results.get(request_id)