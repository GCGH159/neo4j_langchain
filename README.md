# Neo4j + LangChain 自然语言查询系统

使用 LangChain 和 Neo4j 实现的自然语言查询系统，支持用中文自然语言查询图数据库。

## 功能特性

- 🔍 **自然语言查询**: 用中文问题查询 Neo4j，自动生成 Cypher
- 📊 **Schema 探索**: 查看数据库节点和关系结构
- 📥 **示例数据**: 内置公司组织结构示例数据

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件，配置 Neo4j 连接信息：

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=你的密码
```

### 3. 启动 Neo4j

确保 Neo4j 数据库正在运行。推荐使用：
- [Neo4j Desktop](https://neo4j.com/download/)
- Docker: `docker run -p 7474:7474 -p 7687:7687 neo4j`

### 4. 运行程序

```bash
python main.py
```

## 使用示例

```python
from nl_query import ask

# 自然语言查询
answer = ask("有多少员工？")
print(answer)

# 显示生成的 Cypher
from nl_query import ask_with_cypher
answer, cypher = ask_with_cypher("张三在哪个部门？")
print(f"答案: {answer}")
print(f"Cypher: {cypher}")
```

## 项目结构

```
├── config.py         # 配置模块
├── neo4j_graph.py    # Neo4j 连接封装
├── nl_query.py       # 自然语言查询
├── example_data.py   # 示例数据
├── main.py           # 交互式主程序
└── requirements.txt  # 依赖
```

## 示例查询

加载示例数据后，可以尝试以下查询：

- "有多少员工？"
- "列出所有部门"
- "张三在哪个部门工作？"
- "谁是研发部的经理？"
- "哪些员工向张三汇报？"
- "谁的工资最高？"
