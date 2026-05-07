#!/usr/bin/env python3
"""
Hermes-Agent 命令行聊天客户端

使用方法:
    python cli_chat.py                    # 交互式聊天
    python cli_chat.py "你好"             # 发送单条消息
    python cli_chat.py "你好" abc123      # 继续之前的对话

功能:
    - 支持交互式对话
    - 支持单条消息发送
    - 自动管理 session_id
    - 显示统计信息（模型、耗时、成本）
"""

import requests
import sys
import json
from typing import Optional

# 服务地址
BASE_URL = "http://localhost:8001/api/v1"


def chat(message: str, session_id: Optional[str] = None, verbose: bool = False) -> tuple[str, str]:
    """
    发送聊天消息
    
    Args:
        message: 用户消息
        session_id: 会话 ID（可选，用于继续对话）
        verbose: 是否显示详细信息
        
    Returns:
        (session_id, response) 元组
    """
    url = f"{BASE_URL}/chat/completions"
    
    data = {
        "message": message,
    }
    
    if session_id:
        data["session_id"] = session_id
    
    try:
        response = requests.post(url, json=data, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        new_session_id = result.get('session_id', session_id)
        ai_response = result.get('response', 'No response')
        
        # 显示响应
        print(f"\n🤖 AI: {ai_response}")
        
        # 显示统计信息
        if verbose:
            print(f"\n📊 统计信息:")
            print(f"   - Session ID: {new_session_id}")
            print(f"   - 模型：{result.get('model', 'unknown')}")
            print(f"   - 耗时：{result.get('duration', 0):.2f}秒")
            cost = result.get('cost_usd', 0)
            if cost is not None:
                print(f"   - 成本：${cost:.6f}")
        
        return new_session_id, ai_response
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 错误：无法连接到服务")
        print(f"   请确保服务正在运行：http://localhost:8001")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"\n❌ 错误：请求超时")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 错误：{e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n👋 中断退出")
        sys.exit(0)


def interactive_chat(verbose: bool = False):
    """
    交互式聊天模式
    
    Args:
        verbose: 是否显示详细信息
    """
    print("=" * 60)
    print("🤖 Hermes-Agent 交互式聊天")
    print("=" * 60)
    print("💡 提示:")
    print("   - 输入消息开始聊天")
    print("   - 输入 'quit' 或 'exit' 退出")
    print("   - 输入 'stats' 查看统计信息")
    print("   - 输入 'clear' 开始新对话")
    print("=" * 60)
    
    session_id = None
    message_count = 0
    total_duration = 0
    
    while True:
        try:
            # 获取用户输入
            user_input = input(f"\n👤 你 [{session_id or '新对话'}]: ").strip()
            
            if not user_input:
                continue
            
            # 处理特殊命令
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(f"\n👋 再见！")
                if message_count > 0:
                    print(f"📊 本次对话统计:")
                    print(f"   - 消息数：{message_count}")
                    print(f"   - 平均耗时：{total_duration / message_count:.2f}秒")
                break
            
            if user_input.lower() == 'stats':
                print(f"\n📊 当前对话统计:")
                print(f"   - Session ID: {session_id or '无'}")
                print(f"   - 消息数：{message_count}")
                print(f"   - 平均耗时：{total_duration / message_count:.2f}秒" if message_count > 0 else "   - 平均耗时：N/A")
                continue
            
            if user_input.lower() == 'clear':
                session_id = None
                message_count = 0
                total_duration = 0
                print(f"\n✅ 已开始新对话")
                continue
            
            # 发送消息
            new_session_id, response = chat(user_input, session_id, verbose)
            
            # 更新统计
            session_id = new_session_id
            message_count += 1
            
        except KeyboardInterrupt:
            print(f"\n\n👋 中断退出")
            break
        except EOFError:
            print(f"\n\n👋 再见！")
            break


def send_single_message(message: str, session_id: Optional[str] = None, verbose: bool = False):
    """
    发送单条消息并退出
    
    Args:
        message: 消息内容
        session_id: 会话 ID（可选）
        verbose: 是否显示详细信息
    """
    new_session_id, _ = chat(message, session_id, verbose)
    
    if not session_id:
        print(f"\n💡 提示：使用以下 session_id 继续对话：{new_session_id}")
        print(f"   命令：python cli_chat.py \"你的消息\" {new_session_id}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Hermes-Agent 命令行聊天客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli_chat.py                    # 交互式聊天
  python cli_chat.py "你好"             # 发送单条消息
  python cli_chat.py "你好" abc123      # 继续之前的对话
  python cli_chat.py --verbose          # 显示详细信息
        """
    )
    
    parser.add_argument(
        "message",
        nargs="?",
        default=None,
        help="消息内容（不提供则进入交互式模式）"
    )
    
    parser.add_argument(
        "session_id",
        nargs="?",
        default=None,
        help="会话 ID（用于继续之前的对话）"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细信息（模型、耗时、成本等）"
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:8001/api/v1",
        help="服务地址（默认：http://localhost:8001/api/v1）"
    )
    
    args = parser.parse_args()
    
    # 更新全局变量
    base_url = args.url.rstrip('/')
    
    # 执行聊天
    if args.message:
        # 单条消息模式
        send_single_message(args.message, args.session_id, args.verbose)
    else:
        # 交互式模式
        interactive_chat(args.verbose)


if __name__ == "__main__":
    main()
