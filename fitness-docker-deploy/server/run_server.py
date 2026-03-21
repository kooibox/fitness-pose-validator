#!/usr/bin/env python3
"""
健身数据服务器启动脚本

使用方法：
    cd server && python3 run_server.py                # 默认启动 (0.0.0.0:8080)
    cd server && python3 run_server.py --port 9000    # 指定端口
"""

import argparse
from server_receiver import run_server


def main():
    parser = argparse.ArgumentParser(description="健身数据服务器")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8080, help="监听端口")
    
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
