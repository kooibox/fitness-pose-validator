"""
Prompt 模板管理模块
"""

from typing import Any, Dict
from .llm_analyzer import AnalysisType


class PromptBuilder:
    """Prompt 构建器"""
    
    TEMPLATES = {
        AnalysisType.SESSION: """
你是一位专业的健身教练，擅长分析深蹲训练数据。请根据以下训练数据，生成详细的训练报告。

## 训练数据
{training_data}

## 分析要求
请从以下维度进行分析：
1. **动作质量**: 下蹲深度是否标准（90°为佳）、左右对称性、动作稳定性
2. **训练强度**: 深蹲次数、训练时长、密度
3. **具体问题**: 发现的具体问题和风险点
4. **改进建议**: 针对性的、可操作的改进建议

## 输出格式
请以 JSON 格式返回，包含以下字段：
{{
    "summary": "一段话总结本次训练表现",
    "insights": ["洞察1", "洞察2", "洞察3"],
    "suggestions": ["具体建议1", "具体建议2", "具体建议3"],
    "score": 85.5,
    "metadata": {{
        "depth_assessment": "良好/一般/需改进",
        "symmetry_assessment": "良好/一般/需改进",
        "stability_assessment": "良好/一般/需改进"
    }}
}}
""",
        
        AnalysisType.TREND: """
你是一位专业的健身教练。请分析以下多日训练趋势数据，评估用户的进步情况。

## 趋势数据
{training_data}

## 分析要求
请关注：
1. 训练频率是否稳定
2. 训练质量是否提升
3. 是否存在平台期
4. 下一步的训练方向

## 输出格式
{{
    "summary": "趋势总结",
    "insights": ["趋势洞察1", "趋势洞察2", ...],
    "suggestions": ["改进建议1", "改进建议2", ...],
    "score": 88.0,
    "metadata": {{
        "trend_direction": "上升/平稳/下降",
        "improvement_rate": 0.15
    }}
}}
""",
        
        AnalysisType.COMPARISON: """
你是一位专业的健身教练。请对比分析以下两次训练数据，找出差异和进步。

## 对比数据
{training_data}

## 分析要求
请从以下维度对比：
1. 深蹲次数变化
2. 动作质量变化
3. 对称性和稳定性变化
4. 整体进步幅度

## 输出格式
{{
    "summary": "对比总结",
    "insights": ["对比洞察1", "对比洞察2", ...],
    "suggestions": ["针对性建议1", "针对性建议2", ...],
    "score": 86.0,
    "metadata": {{
        "improvements": ["进步项目"],
        "regressions": ["退步项目"]
    }}
}}
""",
        
        AnalysisType.ADVICE: """
你是一位专业的健身教练。请根据用户的训练历史，提供个性化的改进建议。

## 训练历史
{training_data}

## 分析要求
请提供：
1. 短期目标 (1-2周)
2. 中期目标 (1个月)
3. 具体训练建议
4. 注意事项和风险提示

## 输出格式
{{
    "summary": "个性化建议总结",
    "insights": ["优势分析", "待改进方面", ...],
    "suggestions": ["短期目标", "中期目标", "训练建议", ...],
    "score": 79.0,
    "metadata": {{
        "focus_areas": ["重点改进领域"],
        "strengths": ["现有优势"]
    }}
}}
""",
        
        AnalysisType.GOAL: """
你是一位专业的健身教练。请根据用户的训练水平，推荐合适的训练目标。

## 训练数据
{training_data}

## 分析要求
请设定：
1. 每周训练频率目标
2. 每次训练次数目标
3. 动作质量目标
4. 进阶目标

## 输出格式
{{
    "summary": "目标设定建议",
    "insights": ["当前水平评估", "潜力分析", ...],
    "suggestions": ["周目标", "月目标", "质量目标", "进阶目标"],
    "score": null,
    "metadata": {{
        "current_level": "初级/中级/高级",
        "recommended_goals": [
            {{"type": "weekly_sessions", "target": 4}},
            {{"type": "monthly_squats", "target": 1000}},
            {{"type": "quality_score", "target": 90}}
        ]
    }}
}}
""",
    }
    
    def build(
        self,
        analysis_type: AnalysisType,
        training_data: str,
        language: str = "zh",
    ) -> str:
        """
        构建 Prompt
        
        Args:
            analysis_type: 分析类型
            training_data: 训练数据文本
            language: 输出语言
            
        Returns:
            str: 完整的 Prompt
        """
        template = self.TEMPLATES.get(analysis_type)
        
        if not template:
            raise ValueError(f"未知的分析类型: {analysis_type}")
        
        return template.format(training_data=training_data)