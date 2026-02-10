# 知识图谱初始化说明

## 📁 文件说明

`init/` 目录包含用于初始化知识图谱的脚本和 Cypher 语句：

| 文件 | 说明 |
|------|------|
| `01_init_base_relations.cypher` | 创建基础分类和关系（日常、生活、编程技巧、动漫、学习、英语、健身、任务、工作、待办、目标）|
| `02_extended_categories.cypher` | 扩展分类（添加灵感、阅读、电影、音乐、美食、旅行、游戏、理财、健康、社交）|
| `03_useful_queries.cypher` | 实用查询语句集合 |
| `init_graph.py` | Python 初始化脚本（推荐使用）|

---

## 🚀 快速开始

### 方法1：使用 Python 脚本（推荐）

```bash
cd d:\com\slixils\ai\neo4j_langchain
py -3.11 init/init_graph.py
```

**菜单选项：**
1. 🚀 初始化基础关系网
2. 📋 查看所有分类
3. 📝 查看最近笔记
4. 🔍 验证初始化结果
5. 📊 统计数据库
6. 🗑️ 清空数据库（危险！）
7. 🚪 退出

### 方法2：直接执行 Cypher 文件

如果你熟悉 Cypher，可以直接在 Neo4j Browser 中执行这些文件：

```bash
# 1. 执行基础关系网
# 复制 init/01_init_base_relations.cypher 的内容到 Neo4j Browser

# 2. 执行扩展分类
# 复制 init/02_extended_categories.cypher 的内容到 Neo4j Browser
```

---

## 📋 分类体系

### 核心分类（基础）
- **日常** - 日常生活的记录和活动
- **生活** - 生活相关的记录
- **编程技巧** - 编程相关的技巧和经验
- **动漫** - 动漫相关的记录
- **学习** - 学习相关的记录
- **英语** - 英语学习相关
- **健身** - 健身运动相关
- **任务** - 待完成的任务
- **工作** - 工作相关记录
- **待办** - 待办事项
- **目标** - 目标和计划

### 扩展分类
- **灵感** - 灵感和创意记录
- **阅读** - 阅读相关记录
- **电影** - 电影观看记录
- **音乐** - 音乐相关记录
- **美食** - 美食记录
- **旅行** - 旅行记录
- **游戏** - 游戏相关
- **理财** - 理财相关
- **健康** - 健康管理
- **社交** - 社交活动

---

## 🔗 关系类型

### 分类间的关系
- `RELATED_TO` - 相关的分类
- `PART_OF` - 是某分类的一部分
- `HELPS_ACHIEVE` - 帮助实现某目标
- `CONTRIBUTES_TO` - 贡献给某领域
- `CAN_BECOME` - 可以转化为
- `GENERATES` - 产生/生成

### 笔记与分类的关系
- `BELONGS_TO` - 笔记属于某个分类

### 笔记与实体的关系
- `MENTIONS` - 笔记提到某个实体

### 笔记与标签的关系
- `HAS_TAG` - 笔记有某个标签

---

## 🔍 实用查询示例

### 1. 按分类查询笔记

```cypher
// 查询"编程技巧"分类下的所有笔记
MATCH (c:Category {name: '编程技巧'})<-[:BELONGS_TO]-(n:Note)
RETURN c.name AS 分类, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 10;
```

### 2. 按时间查询笔记

```cypher
// 查询今天的所有笔记
MATCH (n:Note)
WHERE date(n.created_at) = date()
RETURN n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC;

// 查询最近7天的笔记
MATCH (n:Note)
WHERE n.created_at >= datetime() - duration('P7D')
RETURN n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC;
```

### 3. 按实体查询

```cypher
// 查询"Python"实体相关的所有笔记
MATCH (e:Entity {name: 'Python'})<-[:MENTIONS]-(n:Note)
RETURN e.name AS 实体, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 10;
```

### 4. 查询相关内容

```cypher
// 查询某个分类的相关分类
MATCH (c:Category {name: '编程技巧'})-[:RELATED_TO]-(related:Category)
RETURN c.name AS 当前分类, related.name AS 相关分类;

// 查询某个实体的相关实体
MATCH (e:Entity {name: 'Python'})-[:RELATED_TO]-(related:Entity)
RETURN e.name AS 当前实体, related.name AS 相关实体;
```

### 5. 灵感相关查询

```cypher
// 查询所有灵感笔记
MATCH (c:Category {name: '灵感'})<-[:BELONGS_TO]-(n:Note)
RETURN n.content AS 灵感内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 20;

// 查询灵感可以转化为哪些分类
MATCH (inspiration:Category {name: '灵感'})-[:CAN_BECOME]->(related:Category)
RETURN inspiration.name AS 灵感, related.name AS 可转化为;
```

### 6. 统计查询

```cypher
// 统计每个分类的笔记数量
MATCH (c:Category)<-[:BELONGS_TO]-(n:Note)
RETURN c.name AS 分类, count(n) AS 笔记数量
ORDER BY count(n) DESC;

// 统计每个实体的出现次数
MATCH (e:Entity)<-[:MENTIONS]-(n:Note)
RETURN e.name AS 实体, count(n) AS 提及次数
ORDER BY count(n) DESC
LIMIT 20;
```

---

## 💡 使用建议

### 1. 灵感的处理
灵感是一个特殊的分类，它可以：
- 与其他分类相关联（学习、编程、工作等）
- 转化为具体的目标或任务
- 由学习和生活等活动产生

**建议：**
- 记录灵感时，可以标记它可能相关的分类
- 定期回顾灵感，将可执行的转化为任务或目标

### 2. 分类间的关联
分类之间建立了丰富的关联关系，可以：
- 快速找到相关领域的内容
- 发现知识之间的联系
- 支持多维度查询

**示例：**
- 编程技巧 → 学习（编程需要学习）
- 学习 → 目标（学习帮助实现目标）
- 灵感 → 任务（灵感可以转化为任务）

### 3. 实体和标签
- **实体**：具体的名词（Python、LangChain、健身房等）
- **标签**：抽象的标记（重要、创意、待跟进等）

**建议：**
- 实体用于关联具体的知识点
- 标签用于标记笔记的属性和状态

---

## 🔄 日常使用流程

### 添加新笔记

```python
from app.agent.smart_note_agent import smart_save

content = """
今天学习了 Python 的装饰器用法，很强大！
同时想到了一个灵感：可以用装饰器来实现日志记录。
"""

result = smart_save(content)
print(result)
```

### 查询相关内容

```cypher
// 方法1：通过分类查询
MATCH (c:Category {name: '编程技巧'})<-[:BELONGS_TO]-(n:Note)
RETURN n.content, n.created_at
ORDER BY n.created_at DESC;

// 方法2：通过实体查询
MATCH (e:Entity {name: 'Python'})<-[:MENTIONS]-(n:Note)
RETURN n.content, n.created_at
ORDER BY n.created_at DESC;

// 方法3：通过关系查询相关内容
MATCH (n:Note)-[:MENTIONS]->(e:Entity)-[:RELATED_TO]-(related:Entity)<-[:MENTIONS]-(related_note:Note)
WHERE n.id = 'your_note_id'
RETURN DISTINCT related_note.content AS 相关笔记
LIMIT 10;
```

### 查找知识路径

```cypher
// 查找两个实体之间的最短路径
MATCH path = shortestPath(
  (e1:Entity {name: 'Python'})-[*]-(e2:Entity {name: 'Neo4j'})
RETURN [node in nodes(path) | node.name] AS 知识路径;
```

---

## 📊 数据库结构

### 节点类型
- **Category** - 分类节点
- **Note** - 笔记节点
- **Entity** - 实体节点
- **Tag** - 标签节点
- **TimeNode** - 时间节点（可选）

### 关系类型
- **BELONGS_TO** - 笔记属于分类
- **MENTIONS** - 笔记提到实体
- **HAS_TAG** - 笔记有标签
- **RELATED_TO** - 相关关系
- **PART_OF** - 组成关系
- **HELPS_ACHIEVE** - 帮助实现
- **CONTRIBUTES_TO** - 贡献给
- **CAN_BECOME** - 可以转化为
- **GENERATES** - 产生/生成

---

## ⚠️ 注意事项

1. **初始化前备份数据**
   - 如果数据库已有数据，建议先备份
   - 可以使用 Neo4j 的导出功能

2. **清空数据库**
   - 菜单选项6会清空所有数据
   - 操作不可逆，请谨慎使用

3. **自定义分类**
   - 可以根据个人需求修改 Cypher 文件
   - 添加或删除分类
   - 调整关系类型

4. **性能优化**
   - 初始化脚本已创建索引
   - 大量数据时考虑分批导入
   - 定期清理孤立节点

---

## 🔧 自定义扩展

### 添加新分类

```cypher
CREATE (new_category:Category {
    name: '新分类名称',
    type: 'category',
    description: '分类描述',
    created_at: datetime()
});

// 建立与其他分类的关联
MATCH (new_category:Category {name: '新分类名称'})
MATCH (existing:Category {name: '已有分类'})
CREATE (new_category)-[:RELATED_TO]->(existing);
```

### 添加新关系类型

```cypher
// 在笔记和分类之间创建新关系
MATCH (n:Note), (c:Category)
WHERE n.id = 'note_id' AND c.name = '分类名称'
CREATE (n)-[:NEW_RELATION_TYPE]->(c);
```

---

## 📞 技术支持

如有问题，请参考：
- **Neo4j 文档**: https://neo4j.com/docs/
- **Cypher 手册**: https://neo4j.com/docs/cypher-manual/
- **项目 Issues**: https://github.com/GCGH159/neo4j_langchain/issues

---

**最后更新**: 2026-02-10
