"""
验证笔记 Agent 功能
"""
import sys
import os
import time

# 添加项目根目录到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.note_agent import note_agent
from app.core.graph import execute_cypher

def verify_agent():
    print("🤖 开始验证笔记 Agent...")
    
    # 1. 测试保存笔记
    print("\n1. 测试: 保存笔记 'Neo4j 是一个高性能的图数据库'")
    res1 = note_agent.chat("记录一下：Neo4j 是一个高性能的图数据库，非常适合存关系数据。")
    print(f"   Agent 回复: {res1}")
    
    # 验证是否存入数据库
    result = execute_cypher("MATCH (n:Note) WHERE n.content CONTAINS 'Neo4j' RETURN n")
    if result:
        print("   ✅ 数据库验证: 笔记已找到")
    else:
        print("   ❌ 数据库验证: 笔记未找到")
        
    # 2. 测试查询
    print("\n2. 测试: 查询 'Neo4j'")
    res2 = note_agent.chat("我都记了哪些关于 Neo4j 的内容？")
    print(f"   Agent 回复: {res2}")
    
    # 3. 测试建立关系
    print("\n3. 测试: 建立关系 '张三 认识 李四'")
    res3 = note_agent.chat("记录一下，张三 认识 李四，他们是朋友") 
    # 注意：Agent 可能会先存笔记，也可能调用 create_relation。
    # 显式一点测试工具调用：
    res4 = note_agent.chat("在图谱中把 张三 和 李四 连起来，关系是 FRIEND_OF")
    print(f"   Agent 回复: {res4}")
    
    # 验证关系
    rel_check = execute_cypher("MATCH (a:Entity {name: '张三'})-[r:FRIEND_OF]->(b:Entity {name: '李四'}) RETURN r")
    if rel_check:
        print("   ✅ 数据库验证: 关系已建立")
    else:
        print("   ❌ 数据库验证: 关系未建立")

if __name__ == "__main__":
    verify_agent()
