"""
Neo4j + LangChain 自然语言查询系统 - 主程序
"""
import sys
from config import config


def print_banner():
    """打印欢迎信息"""
    print("=" * 60)
    print("🦜️🔗 Neo4j + LangChain 自然语言查询系统")
    print("=" * 60)
    print()


def print_menu():
    """打印菜单"""
    print("\n📌 请选择操作：")
    print("  1. 🔍 自然语言查询")
    print("  2. 📊 查看数据库 Schema")
    print("  3. 📈 查看数据库统计")
    print("  4. 📥 加载示例数据")
    print("  5. 💬 示例查询")
    print("  6. 🤖 笔记智能体 (Agent) [NEW]")
    print("  7. 🚪 退出")
    print()


def check_neo4j_connection() -> bool:
    """检查 Neo4j 连接"""
    try:
        from app.core.graph import execute_cypher
        execute_cypher("RETURN 1")
        return True
    except Exception as e:
        print(f"❌ 无法连接到 Neo4j: {e}")
        print(f"\n请确认：")
        print(f"  • Neo4j 服务是否运行在 {config.NEO4J_URI}")
        print(f"  • 用户名/密码是否正确")
        print(f"  • .env 文件配置是否正确")
        return False


def show_schema():
    """显示数据库 Schema"""
    from app.core.graph import get_schema
    print("\n📊 数据库 Schema:")
    print("-" * 40)
    print(get_schema())


def show_stats():
    """显示数据库统计"""
    from app.core.graph import execute_cypher, get_node_labels, get_relationship_types
    
    print("\n📈 数据库统计:")
    print("-" * 40)
    
    # 节点标签
    labels = get_node_labels()
    print(f"\n节点标签: {', '.join(labels) if labels else '(无)'}")
    
    # 关系类型
    rel_types = get_relationship_types()
    print(f"关系类型: {', '.join(rel_types) if rel_types else '(无)'}")
    
    # 节点数量
    for label in labels:
        result = execute_cypher(f"MATCH (n:`{label}`) RETURN count(n) as count")
        count = result[0]['count'] if result else 0
        print(f"  • {label}: {count} 个")
    
    # 总关系数
    result = execute_cypher("MATCH ()-[r]->() RETURN count(r) as count")
    rel_count = result[0]['count'] if result else 0
    print(f"\n总关系数: {rel_count} 条")


def natural_language_query():
    """自然语言查询交互"""
    from app.agent.nl_query import NaturalLanguageQuery
    
    print("\n🔍 自然语言查询模式")
    print("  输入你的问题，系统会自动转换为 Cypher 并执行")
    print("  输入 'q' 返回主菜单")
    print("-" * 40)
    
    nlq = NaturalLanguageQuery(verbose=True)
    
    while True:
        try:
            question = input("\n❓ 你的问题: ").strip()
            
            if not question:
                continue
            if question.lower() == 'q':
                break
            
            print("\n⏳ 处理中...")
            result = nlq.query(question)
            
            print("\n💡 答案:")
            print(f"   {result.get('result', '无法获取答案')}")
            
            # 显示生成的 Cypher
            steps = result.get('intermediate_steps', [])
            if steps and 'query' in steps[0]:
                print(f"\n📝 生成的 Cypher:")
                print(f"   {steps[0]['query']}")
                
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"\n❌ 查询出错: {e}")


def load_example_data_interactive():
    """加载示例数据（交互确认）"""
    print("\n⚠️  警告: 这将清空现有数据并加载示例数据！")
    confirm = input("确认继续? (y/n): ").strip().lower()
    
    if confirm == 'y':
        from example_data import load_example_data
        print()
        load_example_data()
    else:
        print("已取消。")


def show_example_queries():
    """显示并运行示例查询"""
    from example_data import get_example_queries
    from app.agent.nl_query import ask_with_cypher
    
    queries = get_example_queries()
    
    print("\n📝 示例查询:")
    print("-" * 40)
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")
    
    print("\n  输入编号执行查询，或输入 'q' 返回")
    
    while True:
        choice = input("\n选择 (1-10/q): ").strip()
        
        if choice.lower() == 'q':
            break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(queries):
                question = queries[idx]
                print(f"\n❓ 问题: {question}")
                print("⏳ 处理中...")
                
                answer, cypher = ask_with_cypher(question)
                
                print(f"\n💡 答案: {answer}")
                print(f"📝 Cypher: {cypher}")
            else:
                print("无效选择")
        except ValueError:
            print("请输入数字")
        except Exception as e:
            print(f"❌ 出错: {e}")


def run_note_agent_mode():
    """笔记 Agent 模式"""
    from app.agent.note_agent import note_agent
    
    print("\n🤖 笔记智能体 (Agent) 已启动")
    print("  你可以说：")
    print("  - \"记录：LangChain 是一个开发 LLM 应用的框架，支持 Python\"")
    print("  - \"查询关于 Python 的笔记\"")
    print("  - \"张三和李四是同事关系\"")
    print("  - \"看看最近记了什么\"")
    print("  输入 'q' 返回主菜单")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            
            if not user_input:
                continue
            if user_input.lower() == 'q':
                break
                
            print("🤖 Agent 思考中...")
            response = note_agent.chat(user_input)
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n")
            break


def main():
    """主函数"""
    print_banner()
    
    # 检查配置
    missing = config.validate()
    if "LLM_API_KEY" in missing:
        print("⚠️  警告: LLM_API_KEY 未配置，自然语言查询功能将不可用")
    
    print("🔌 正在连接 Neo4j...")
    if not check_neo4j_connection():
        print("\n💡 提示: 请先启动 Neo4j 数据库，然后配置 .env 文件")
        sys.exit(1)
    
    print("✅ Neo4j 连接成功！")
    
    while True:
        print_menu()
        choice = input("请输入选项 (1-7): ").strip()  # Update range
        
        try:
            if choice == '1':
                natural_language_query()
            elif choice == '2':
                show_schema()
            elif choice == '3':
                show_stats()
            elif choice == '4':
                load_example_data_interactive()
            elif choice == '5':
                show_example_queries()
            elif choice == '6':
                run_note_agent_mode()
            elif choice == '7':
                print("\n👋 再见！")
                break
            else:
                print("无效选项，请重新选择")
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")


if __name__ == "__main__":
    main()
