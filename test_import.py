#!/usr/bin/env python3
"""
测试导入
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 测试导入")
print("=" * 50)

# 测试 api.dependencies
print("1. 测试 api.dependencies...")
try:
    from api.dependencies import HTTPException, get_db, get_current_user
    print("   ✅ 导入成功")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 api.pic
print("\n2. 测试 api.pic...")
try:
    from api.pic import router
    print("   ✅ 导入成功")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 api.main
print("\n3. 测试 api.main...")
try:
    from api.main import app
    print(f"   ✅ 导入成功: {app.title}")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 FastAPI
print("\n4. 测试 FastAPI...")
try:
    from fastapi import FastAPI, HTTPException
    app = FastAPI()
    print(f"   ✅ FastAPI 导入成功")
except Exception as e:
    print(f"   ❌ FastAPI 导入失败: {e}")

print("\n" + "=" * 50)
