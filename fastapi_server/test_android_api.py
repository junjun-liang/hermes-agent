#!/usr/bin/env python3
"""
Android 客户端 FastAPI 接口连通性测试脚本
"""

import requests
import json
import sys
import time
from typing import Optional, Tuple

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8001
BASE_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/api/v1"


def print_header(text: str):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_subheader(text: str):
    print(f"\n{'─' * 60}")
    print(f"  {text}")
    print(f"{'─' * 60}")


def test_health_check() -> bool:
    print_subheader("测试 1: 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态码：200")
            print(f"✅ 服务状态：{data.get('status')}")
            print(f"✅ 版本：{data.get('version')}")
            print(f"✅ 运行时间：{data.get('uptime'):.0f}秒")
            return True
        else:
            print(f"❌ 状态码：{response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def test_readiness_check() -> bool:
    print_subheader("测试 2: 就绪检查")
    try:
        response = requests.get(f"{BASE_URL}/ready", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态码：200")
            print(f"✅ 就绪状态：{data.get('status')}")
            print(f"✅ 数据库：{data.get('database')}")
            print(f"✅ LLM 提供商：{data.get('llm_provider')}")
            return True
        else:
            print(f"❌ 状态码：{response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def test_chat_completion() -> Tuple[bool, Optional[str]]:
    print_subheader("测试 3: 聊天接口")
    try:
        payload = {
            "message": "你好，请用一句话介绍你自己",
            "max_iterations": 50
        }
        print(f"📤 发送请求...")
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            timeout=120
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"✅ 状态码：200")
            print(f"✅ Session ID：{session_id}")
            print(f"✅ 模型：{data.get('model')}")
            print(f"✅ 完成：{data.get('completed')}")
            print(f"✅ 耗时：{data.get('duration', 0):.2f}秒")
            response_text = data.get('response', '')
            if len(response_text) > 200:
                response_text = response_text[:200] + "..."
            print(f"\n💬 AI 响应：{response_text}")
            return True, session_id
        else:
            print(f"❌ 状态码：{response.status_code}")
            print(f"❌ 错误：{response.text}")
            return False, None
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False, None


def test_session_list() -> bool:
    print_subheader("测试 4: 会话列表")
    try:
        response = requests.get(
            f"{BASE_URL}/sessions",
            params={"limit": 10, "offset": 0},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            sessions = data.get('sessions', [])
            total = data.get('total', 0)
            print(f"✅ 状态码：200")
            print(f"✅ 总会话数：{total}")
            print(f"✅ 返回数量：{len(sessions)}")
            return True
        else:
            print(f"❌ 状态码：{response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def test_get_config() -> bool:
    print_subheader("测试 5: 获取配置")
    try:
        response = requests.get(f"{BASE_URL}/config", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态码：200")
            print(f"✅ 模型：{data.get('model')}")
            print(f"✅ 最大迭代：{data.get('max_iterations')}")
            print(f"✅ 提供商：{data.get('provider')}")
            return True
        else:
            print(f"❌ 状态码：{response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Android 客户端 FastAPI 接口连通性测试")
    parser.add_argument("--host", default=DEFAULT_HOST, help="服务器 IP 地址")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="服务器端口")
    args = parser.parse_args()
    
    global BASE_URL
    BASE_URL = f"http://{args.host}:{args.port}/api/v1"
    
    print_header("🧪 Android 客户端 FastAPI 接口连通性测试")
    print(f"📡 服务器地址：http://{args.host}:{args.port}")
    print(f"🔗 API 基础 URL：{BASE_URL}")
    
    results = {}
    results["health_check"] = test_health_check()
    results["readiness_check"] = test_readiness_check()
    results["config"] = test_get_config()
    results["chat_completion"], session_id = test_chat_completion()
    
    if session_id:
        results["session_list"] = test_session_list()
    
    print_header("📊 测试总结")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Android 客户端可以正常连接 FastAPI 服务！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查服务状态和网络配置")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
