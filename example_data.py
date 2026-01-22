"""
示例数据加载 - 创建公司组织结构的示例数据
"""
from app.core.graph import execute_cypher, Neo4jConnection


def clear_database():
    """清空数据库（谨慎使用！）"""
    execute_cypher("MATCH (n) DETACH DELETE n")
    print("✓ 数据库已清空")


def load_example_data():
    """
    加载示例数据：公司组织结构
    
    创建的数据结构：
    - 部门 (Department): 研发部、市场部、人力资源部
    - 员工 (Employee): 多名员工
    - 关系: WORKS_IN, REPORTS_TO, MANAGES
    """
    # 清空现有数据
    execute_cypher("MATCH (n) DETACH DELETE n")
    
    # 创建部门
    departments_cypher = """
    CREATE (dev:Department {name: '研发部', code: 'DEV', budget: 1000000})
    CREATE (marketing:Department {name: '市场部', code: 'MKT', budget: 500000})
    CREATE (hr:Department {name: '人力资源部', code: 'HR', budget: 300000})
    RETURN dev, marketing, hr
    """
    execute_cypher(departments_cypher)
    print("✓ 创建部门完成")
    
    # 创建员工
    employees_cypher = """
    // 研发部员工
    CREATE (zhang:Employee {name: '张三', employee_id: 'E001', title: '技术总监', salary: 50000, hire_date: '2020-01-15'})
    CREATE (li:Employee {name: '李四', employee_id: 'E002', title: '高级工程师', salary: 35000, hire_date: '2021-03-20'})
    CREATE (wang:Employee {name: '王五', employee_id: 'E003', title: '工程师', salary: 25000, hire_date: '2022-06-01'})
    CREATE (zhao:Employee {name: '赵六', employee_id: 'E004', title: '工程师', salary: 24000, hire_date: '2022-08-15'})
    
    // 市场部员工
    CREATE (chen:Employee {name: '陈七', employee_id: 'E005', title: '市场总监', salary: 45000, hire_date: '2019-05-10'})
    CREATE (liu:Employee {name: '刘八', employee_id: 'E006', title: '市场经理', salary: 30000, hire_date: '2021-07-01'})
    CREATE (sun:Employee {name: '孙九', employee_id: 'E007', title: '市场专员', salary: 18000, hire_date: '2023-01-10'})
    
    // 人力资源部员工
    CREATE (zhou:Employee {name: '周十', employee_id: 'E008', title: 'HR总监', salary: 40000, hire_date: '2018-09-01'})
    CREATE (wu:Employee {name: '吴十一', employee_id: 'E009', title: 'HR专员', salary: 15000, hire_date: '2023-03-15'})
    
    RETURN zhang, li, wang, zhao, chen, liu, sun, zhou, wu
    """
    execute_cypher(employees_cypher)
    print("✓ 创建员工完成")
    
    # 创建 WORKS_IN 关系
    works_in_cypher = """
    MATCH (e:Employee), (d:Department)
    WHERE (e.name IN ['张三', '李四', '王五', '赵六'] AND d.name = '研发部')
       OR (e.name IN ['陈七', '刘八', '孙九'] AND d.name = '市场部')
       OR (e.name IN ['周十', '吴十一'] AND d.name = '人力资源部')
    CREATE (e)-[:WORKS_IN]->(d)
    """
    execute_cypher(works_in_cypher)
    print("✓ 创建 WORKS_IN 关系完成")
    
    # 创建 MANAGES 和 REPORTS_TO 关系
    management_cypher = """
    // 张三管理研发部
    MATCH (zhang:Employee {name: '张三'}), (dev:Department {name: '研发部'})
    CREATE (zhang)-[:MANAGES]->(dev)
    
    // 陈七管理市场部
    WITH 1 as dummy
    MATCH (chen:Employee {name: '陈七'}), (mkt:Department {name: '市场部'})
    CREATE (chen)-[:MANAGES]->(mkt)
    
    // 周十管理人力资源部
    WITH 1 as dummy
    MATCH (zhou:Employee {name: '周十'}), (hr:Department {name: '人力资源部'})
    CREATE (zhou)-[:MANAGES]->(hr)
    """
    execute_cypher(management_cypher)
    print("✓ 创建 MANAGES 关系完成")
    
    # 创建 REPORTS_TO 关系
    reports_cypher = """
    // 研发部汇报关系
    MATCH (li:Employee {name: '李四'}), (zhang:Employee {name: '张三'})
    CREATE (li)-[:REPORTS_TO]->(zhang)
    
    WITH 1 as dummy
    MATCH (wang:Employee {name: '王五'}), (li:Employee {name: '李四'})
    CREATE (wang)-[:REPORTS_TO]->(li)
    
    WITH 1 as dummy
    MATCH (zhao:Employee {name: '赵六'}), (li:Employee {name: '李四'})
    CREATE (zhao)-[:REPORTS_TO]->(li)
    
    // 市场部汇报关系
    WITH 1 as dummy
    MATCH (liu:Employee {name: '刘八'}), (chen:Employee {name: '陈七'})
    CREATE (liu)-[:REPORTS_TO]->(chen)
    
    WITH 1 as dummy
    MATCH (sun:Employee {name: '孙九'}), (liu:Employee {name: '刘八'})
    CREATE (sun)-[:REPORTS_TO]->(liu)
    
    // 人力资源部汇报关系
    WITH 1 as dummy
    MATCH (wu:Employee {name: '吴十一'}), (zhou:Employee {name: '周十'})
    CREATE (wu)-[:REPORTS_TO]->(zhou)
    """
    execute_cypher(reports_cypher)
    print("✓ 创建 REPORTS_TO 关系完成")
    
    # 刷新 Schema
    Neo4jConnection.refresh_schema()
    print("✓ Schema 已刷新")
    
    # 显示统计信息
    stats = execute_cypher("""
        MATCH (e:Employee) WITH count(e) as employees
        MATCH (d:Department) WITH employees, count(d) as departments
        MATCH ()-[r]->() WITH employees, departments, count(r) as relationships
        RETURN employees, departments, relationships
    """)
    if stats:
        s = stats[0]
        print(f"\n📊 数据统计:")
        print(f"   员工: {s['employees']} 人")
        print(f"   部门: {s['departments']} 个")
        print(f"   关系: {s['relationships']} 条")


def get_example_queries() -> list[str]:
    """返回一些示例自然语言查询"""
    return [
        "有多少员工？",
        "列出所有部门",
        "张三在哪个部门工作？",
        "谁是研发部的经理？",
        "哪些员工向张三汇报？",
        "市场部有几个人？",
        "谁的工资最高？",
        "2022年入职的员工有哪些？",
        "李四的下属有谁？",
        "研发部的总薪资是多少？",
    ]


if __name__ == "__main__":
    print("加载示例数据...")
    load_example_data()
    print("\n✅ 示例数据加载完成！")
    print("\n示例查询：")
    for q in get_example_queries()[:5]:
        print(f"  • {q}")
