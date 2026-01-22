"""
验证 Neo4j 连接和基本功能
"""
import sys
import os
import io

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.graph import execute_cypher, Neo4jConnection
from example_data import load_example_data

def verify_connection():
    print("🔌 1. 测试 Neo4j 连接...")
    try:
        results = execute_cypher("RETURN 1 as val")
        if results and results[0]['val'] == 1:
            print("   ✅ 连接成功！")
        else:
            print("   ❌ 连接失败: 返回值不匹配")
            return
    except Exception as e:
        print(f"   ❌ 连接异常: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n📥 2. 测试数据加载...")
    try:
        # 捕获输出以避免混乱
        # sys.stdout = io.StringIO()
        load_example_data()
        # sys.stdout = sys.__stdout__
        print("   ✅ 示例数据加载成功")
    except Exception as e:
        # sys.stdout = sys.__stdout__
        print(f"   ❌ 数据加载失败: {e}")
        return

    print("\n🔍 3. 测试自然语言查询模块...")
    try:
        from app.agent.nl_query import NaturalLanguageQuery
        nlq = NaturalLanguageQuery()
        print("   ✅ NaturalLanguageQuery 初始化成功")
        
        question = "有多少员工？"
        print(f"   尝试查询: {question}")
        result = nlq.query(question)
        print(f"   答案: {result.get('result')}")
        
        if result.get('result'):
            print("   ✅ 查询功能正常")
        else:
            print("   ❌ 查询结果为空")
            
    except Exception as e:
        print(f"   ❌ 查询模块异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_connection()
