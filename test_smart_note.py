"""
测试智能笔记 Agent - Plan-and-Execute 模式
"""
from app.agent.smart_note_agent import smart_save, smart_planner, SmartNoteAgent


def test_smart_save():
    """测试智能保存功能"""
    print("=" * 70)
    print("🧪 测试智能笔记保存功能")
    print("=" * 70)

    test_cases = [
        # 测试 1: 包含已有实体的笔记
        """
        今天学习了 LangChain 的使用方法，
        它是一个用于构建 LLM 应用的框架。
        我还了解了 Neo4j 图数据库的用法，
        发现 LangChain 和 Neo4j 可以很好地配合使用。
        主要参考了 OpenAI 的官方文档。
        """,

        # 测试 2: 新概念笔记
        """
        最近开始学习 Rust 编程语言，
        它是一门注重安全性和性能的现代编程语言。
        打算用它来写一些系统级的东西。
        """,

        # 测试 3: 简单笔记
        """
        Python 是最受欢迎的编程语言之一。
        """,
    ]

    for i, content in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"📝 测试用例 {i}")
        print(f"{'='*70}")
        print(f"\n原文：\n{content.strip()}")
        print(f"\n{'-'*70}")

        try:
            result = smart_save(content.strip())
            print(f"\n{result}")
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()

        print(f"\n{'='*70}\n")


def test_step_by_step():
    """逐步测试工作流的每个阶段"""
    print("\n" + "=" * 70)
    print("🔬 逐步测试工作流")
    print("=" * 70)

    content = """
    在学习 React 开发时，我发现它和 Vue 有很多相似之处。
    但 React 更注重函数式编程，而 Vue 更简单易学。
    两者都可以用 Node.js 来开发。
    """

    print(f"\n原文：{content.strip()}\n")

    # Step 1: 规划
    print("📋 Step 1: 规划阶段")
    print("-" * 40)
    plan = smart_planner.plan(content)
    print(f"实体分析结果：\n{plan['entities_analysis']}\n")

    # Step 2: 分析位置
    print("🔍 Step 2: 分析现有位置")
    print("-" * 40)
    analysis = smart_planner.analyze_positions(plan)
    print(f"发现的实体：{analysis['entities']}")
    print(f"\n位置信息：")
    for entity, position in analysis['positions'].items():
        print(f"\n  📌 {entity}:")
        print(f"     {position[:150]}..." if len(position) > 150 else f"     {position}")
    print()

    # Step 3: 反思
    print("💭 Step 3: 反思与规划")
    print("-" * 40)
    reflection = smart_planner.reflect(analysis)
    print(f"行动计划：\n{reflection['action_plan']}\n")

    # Step 4: 执行
    print("✅ Step 4: 执行保存")
    print("-" * 40)
    execution = smart_planner.execute(reflection)
    print(f"保存结果：{execution['save_result']}\n")
    if execution['relations_added']:
        print(f"补充的关系：")
        for rel in execution['relations_added']:
            print(f"  • {rel}")


def test_agent_chat():
    """测试 Agent 对话模式"""
    print("\n" + "=" * 70)
    print("🤖 测试 Agent 对话模式")
    print("=" * 70)

    agent = SmartNoteAgent()

    queries = [
        "帮我保存一条笔记：最近在学习 Docker 容器技术，它和 Kubernetes 配合可以实现容器编排。",
        "帮我分析一下'Neo4j'这个实体在图中的位置",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"💬 查询 {i}: {query}")
        print(f"{'='*70}")

        try:
            response = agent.chat(query)
            print(f"\n🤖 Agent: {response}")
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("🚀 启动智能笔记 Agent 测试...\n")

    # 选择测试模式
    print("请选择测试模式：")
    print("  1. 完整智能保存测试")
    print("  2. 逐步测试工作流")
    print("  3. Agent 对话测试")
    print("  4. 全部测试")

    choice = input("\n请输入选项 (1-4): ").strip()

    if choice == "1":
        test_smart_save()
    elif choice == "2":
        test_step_by_step()
    elif choice == "3":
        test_agent_chat()
    elif choice == "4":
        test_smart_save()
        test_step_by_step()
        test_agent_chat()
    else:
        print("无效选项")
