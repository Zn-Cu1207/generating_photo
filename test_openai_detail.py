#!/usr/bin/env python3
"""测试OpenAI具体问题"""

try:
    from openai import OpenAI
    print("✅ OpenAI导入成功")
    
    # 查看版本
    import openai
    print(f"  版本: {openai.__version__}")
    
    # 测试简单功能
    client = OpenAI(api_key="dummy")
    print("✅ OpenAI客户端创建成功")
    
except TypeError as e:
    print(f"❌ OpenAI TypeError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ OpenAI其他错误: {type(e).__name__}: {e}")
