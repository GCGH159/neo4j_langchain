"""
直接测试修改后的 Note Agent
"""
from app.agent.note_agent import NoteAgent

def test_agent():
    print("🚀 启动 Note Agent 测试...\n")
    
    agent = NoteAgent()
    
    test_queries = [
        # 测试 1: 让 AI 直接用 Cypher 统计员工数量
        "请直接用 Cypher 查询有多少个员工？",
        
        # 测试 2: 让 AI 直接用 Cypher 查询工资最高的员工
        "请用 Cypher 找出工资最高的员工是谁？",
        
        # 测试 3: 让 AI 直接用 Cypher 统计每个部门有多少人
        "请用 Cypher 统计每个部门有多少人？",
        
        # 测试 4: 正常使用 save_note
        "记录：Python 是一种优雅的编程语言，适合数据分析和 AI 开发。标签：编程，AI",
        
        # 测试 5: 混合使用 - 查询笔记并用 Cypher 分析
        "请用 Cypher 查询有多少条笔记？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"📝 测试 {i}: {query}")
        print('='*60)
        
        try:
            response = agent.chat(query)
            print(f"\n🤖 Agent: {response}")
        except Exception as e:
            print(f"❌ 错误: {e}")
        
        print("\n")

if __name__ == "__main__":
    test_agent()
