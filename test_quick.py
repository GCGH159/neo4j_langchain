"""
简洁测试智能笔记保存功能
"""
from app.agent.smart_note_agent import smart_save


def main():
    print("🧪 测试智能笔记保存功能")
    print("=" * 60)

    test_content = """
    今天学习了 LangChain 的使用方法，
    它是一个用于构建 LLM 应用的框架。
    我还了解了 Neo4j 图数据库的用法，
    发现 LangChain 和 Neo4j 可以很好地配合使用。
    主要参考了 OpenAI 的官方文档。
    """

    print(f"\n📝 测试内容：")
    print(test_content.strip())
    print("\n" + "=" * 60)

    print("\n🚀 开始智能保存流程...\n")

    try:
        result = smart_save(test_content.strip())
        print(result)
        print("\n✅ 测试完成！")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
