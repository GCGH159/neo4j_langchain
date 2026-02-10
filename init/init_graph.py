"""
知识图谱初始化脚本
直接执行 Cypher 语句，创建基础关系网
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.graph import execute_cypher


def execute_cypher_file(file_path: str, description: str = "") -> None:
    """
    执行 Cypher 文件中的所有语句

    Args:
        file_path: Cypher 文件路径
        description: 执行描述
    """
    print(f"\n{'='*60}")
    print(f"📝 执行: {description}")
    print(f"📁 文件: {file_path}")
    print('='*60)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 按分号分割语句（简单处理）
        # 更精确的方式是使用 Cypher 解析器，但这里用简单方法
        statements = [s.strip() for s in content.split(';') if s.strip()]

        success_count = 0
        error_count = 0

        for i, statement in enumerate(statements, 1):
            if not statement:
                continue

            # 跳过注释
            if statement.startswith('//'):
                continue

            try:
                result = execute_cypher(statement)
                success_count += 1

                # 显示部分结果
                if result and len(result) > 0:
                    if 'message' in result[0]:
                        print(f"  ✅ [{i}/{len(statements)}] {result[0]['message']}")
                    elif 'result' in result[0]:
                        print(f"  ✅ [{i}/{len(statements)}] {result[0]['result']}")
                    else:
                        print(f"  ✅ [{i}/{len(statements)}] 执行成功")
                else:
                    print(f"  ✅ [{i}/{len(statements)}] 执行成功")

            except Exception as e:
                error_count += 1
                print(f"  ❌ [{i}/{len(statements)}] 错误: {str(e)[:100]}")

        print(f"\n📊 执行结果: {success_count} 成功, {error_count} 失败")

    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")


def init_all():
    """
    执行所有初始化脚本
    """
    print("\n" + "="*60)
    print("🚀 开始初始化知识图谱")
    print("="*60)

    init_dir = Path(__file__).parent

    # 1. 基础关系网
    base_relations = init_dir / "01_init_base_relations.cypher"
    if base_relations.exists():
        execute_cypher_file(str(base_relations), "基础关系网初始化")
    else:
        print(f"⚠️  文件不存在: {base_relations}")

    # 2. 扩展分类
    extended_categories = init_dir / "02_extended_categories.cypher"
    if extended_categories.exists():
        execute_cypher_file(str(extended_categories), "扩展分类初始化")
    else:
        print(f"⚠️  文件不存在: {extended_categories}")

    print("\n" + "="*60)
    print("✅ 初始化完成！")
    print("="*60)


def verify_init():
    """
    验证初始化结果
    """
    print("\n" + "="*60)
    print("🔍 验证初始化结果")
    print("="*60)

    queries = [
        ("统计分类节点", "MATCH (c:Category) RETURN count(c) AS 数量"),
        ("统计笔记节点", "MATCH (n:Note) RETURN count(n) AS 数量"),
        ("统计实体节点", "MATCH (e:Entity) RETURN count(e) AS 数量"),
        ("统计标签节点", "MATCH (t:Tag) RETURN count(t) AS 数量"),
        ("统计关系总数", "MATCH ()-[r]->() RETURN count(r) AS 数量"),
    ]

    for desc, query in queries:
        try:
            result = execute_cypher(query)
            if result:
                count = result[0].get('数量', 0)
                print(f"  {desc}: {count}")
        except Exception as e:
            print(f"  {desc}: 查询失败 - {str(e)}")

    print("\n" + "="*60)


def show_categories():
    """
    显示所有分类
    """
    print("\n" + "="*60)
    print("📋 所有分类")
    print("="*60)

    query = """
    MATCH (c:Category)
    OPTIONAL MATCH (c)<-[:BELONGS_TO]-(n:Note)
    RETURN c.name AS 分类, c.description AS 描述, count(n) AS 笔记数量
    ORDER BY 笔记数量 DESC
    """

    try:
        result = execute_cypher(query)
        if result:
            for row in result:
                print(f"\n  📌 {row['分类']}")
                print(f"     {row['描述']}")
                print(f"     笔记数: {row['笔记数量']}")
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")

    print("\n" + "="*60)


def show_recent_notes(limit: int = 10):
    """
    显示最近的笔记
    """
    print(f"\n{'='*60}")
    print(f"📝 最近的 {limit} 条笔记")
    print('='*60)

    query = """
    MATCH (n:Note)
    OPTIONAL MATCH (n)-[:BELONGS_TO]->(c:Category)
    OPTIONAL MATCH (n)-[:HAS_TAG]->(t:Tag)
    RETURN n.content AS 笔记, c.name AS 分类, collect(t.name) AS 标签, n.created_at AS 时间
    ORDER BY n.created_at DESC
    LIMIT $limit
    """

    try:
        result = execute_cypher(query, {"limit": limit})
        if result:
            for i, row in enumerate(result, 1):
                tags = ', '.join(row['标签']) if row['标签'] else '无'
                category = row['分类'] if row['分类'] else '无分类'
                content = row['笔记'][:60] + '...' if len(row['笔记']) > 60 else row['笔记']
                print(f"\n  {i}. [{row['时间']}] {content}")
                print(f"     分类: {category} | 标签: {tags}")
        else:
            print("  暂无笔记")
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")

    print("\n" + "="*60)


def main():
    """
    主函数
    """
    print("\n" + "="*60)
    print("🧠 知识图谱初始化工具")
    print("="*60)

    while True:
        print("\n请选择操作:")
        print("  1. 🚀 初始化基础关系网")
        print("  2. 📋 查看所有分类")
        print("  3. 📝 查看最近笔记")
        print("  4. 🔍 验证初始化结果")
        print("  5. 📊 统计数据库")
        print("  6. 🗑️  清空数据库（危险！）")
        print("  7. 🚪 退出")

        choice = input("\n请输入选项 (1-7): ").strip()

        if choice == '1':
            confirm = input("⚠️  这将创建基础关系网，是否继续? (y/n): ").strip().lower()
            if confirm == 'y':
                init_all()
                verify_init()

        elif choice == '2':
            show_categories()

        elif choice == '3':
            try:
                limit = int(input("请输入要显示的笔记数量 (默认10): ") or 10)
                show_recent_notes(limit)
            except ValueError:
                print("❌ 无效的数字")
                show_recent_notes(10)

        elif choice == '4':
            verify_init()

        elif choice == '5':
            verify_init()

        elif choice == '6':
            confirm = input("⚠️  这将删除所有数据，是否继续? (输入 'DELETE' 确认): ").strip()
            if confirm == 'DELETE':
                query = "MATCH (n) DETACH DELETE n"
                try:
                    execute_cypher(query)
                    print("✅ 数据库已清空")
                except Exception as e:
                    print(f"❌ 清空失败: {str(e)}")

        elif choice == '7':
            print("\n👋 再见！")
            break

        else:
            print("❌ 无效选项")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
