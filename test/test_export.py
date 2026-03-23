#!/usr/bin/env python3
"""
数据导出测试脚本

测试数据导出和上传功能。
使用方法：
    python test_export.py              # 测试导出最近会话
    python test_export.py --session 1  # 测试导出指定会话
    python test_export.py --all        # 测试导出所有会话
    python test_export.py --upload URL # 测试上传到服务器
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data_exporter import DataExporter, DataUploader
from src.database import Database


def test_export_session(session_id: int, compress: bool = False):
    """测试导出单个会话"""
    print(f"\n{'='*60}")
    print(f"测试导出会话 {session_id}")
    print(f"{'='*60}")
    
    try:
        exporter = DataExporter()
        
        # 导出为JSON
        output_path = exporter.export_to_json(
            session_id=session_id,
            compress=compress
        )
        
        print(f"✓ 导出成功: {output_path}")
        
        # 显示文件大小
        file_size = output_path.stat().st_size
        print(f"  文件大小: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        # 验证JSON格式
        import json
        if compress:
            import gzip
            with gzip.open(output_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        print(f"  会话ID: {data['session']['id']}")
        print(f"  记录数: {len(data['records'])}")
        print(f"  深蹲次数: {data['summary'].get('total_squats', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ 导出失败: {e}")
        return False


def test_export_all(limit: int = 10):
    """测试导出所有会话"""
    print(f"\n{'='*60}")
    print(f"测试导出所有会话 (最多 {limit} 个)")
    print(f"{'='*60}")
    
    try:
        db = Database()
        sessions = db.get_recent_sessions(limit)
        
        if not sessions:
            print("没有找到训练记录")
            return False
        
        print(f"找到 {len(sessions)} 个会话")
        
        exporter = DataExporter()
        success_count = 0
        
        for session in sessions:
            if test_export_session(session.id, compress=True):
                success_count += 1
        
        print(f"\n总结: {success_count}/{len(sessions)} 个会话导出成功")
        return success_count > 0
        
    except Exception as e:
        print(f"✗ 批量导出失败: {e}")
        return False


def test_upload(session_id: int, server_url: str, auth_token: str = None):
    """测试上传到服务器"""
    print(f"\n{'='*60}")
    print(f"测试上传会话 {session_id} 到 {server_url}")
    print(f"{'='*60}")
    
    try:
        exporter = DataExporter()
        
        result = exporter.upload_session(
            session_id=session_id,
            server_url=server_url,
            auth_token=auth_token,
            compress=True
        )
        
        print(f"✓ 上传成功")
        print(f"  服务器响应: {result}")
        return True
        
    except Exception as e:
        print(f"✗ 上传失败: {e}")
        return False


def list_sessions(limit: int = 10):
    """列出所有会话"""
    print(f"\n{'='*60}")
    print(f"训练会话列表 (最近 {limit} 个)")
    print(f"{'='*60}")
    
    db = Database()
    sessions = db.get_recent_sessions(limit)
    
    if not sessions:
        print("没有找到训练记录")
        return
    
    print(f"\n{'ID':<8} {'开始时间':<26} {'深蹲次数':<10} {'总帧数':<10}")
    print("-" * 60)
    
    for session in sessions:
        print(f"{session.id:<8} {session.start_time:<26} {session.total_squats:<10} {session.total_frames:<10}")
    
    print(f"\n共 {len(sessions)} 个会话")


def main():
    parser = argparse.ArgumentParser(
        description="数据导出测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_export.py              # 导出最近会话
  python test_export.py --session 1  # 导出会话1
  python test_export.py --all        # 导出所有会话
  python test_export.py --list       # 列出所有会话
  python test_export.py --upload http://localhost:8000/api/upload
        """
    )
    
    parser.add_argument(
        "-s", "--session",
        type=int,
        help="导出指定会话ID"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="导出所有会话"
    )
    
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="列出所有会话"
    )
    
    parser.add_argument(
        "--upload",
        type=str,
        metavar="URL",
        help="上传到服务器URL"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        help="认证令牌"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="限制会话数量 (默认: 10)"
    )
    
    parser.add_argument(
        "--compress",
        action="store_true",
        help="使用gzip压缩"
    )
    
    args = parser.parse_args()
    
    # 列出会话
    if args.list:
        list_sessions(args.limit)
        return
    
    # 上传到服务器
    if args.upload:
        session_id = args.session or 1
        test_upload(session_id, args.upload, args.token)
        return
    
    # 导出所有会话
    if args.all:
        test_export_all(args.limit)
        return
    
    # 导出指定会话
    if args.session:
        test_export_session(args.session, args.compress)
        return
    
    # 默认：导出最近会话
    db = Database()
    sessions = db.get_recent_sessions(1)
    if sessions:
        test_export_session(sessions[0].id, args.compress)
    else:
        print("没有找到训练记录。请先运行训练程序。")


if __name__ == "__main__":
    main()
