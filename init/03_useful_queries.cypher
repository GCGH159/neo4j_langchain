// ========================================
// 实用查询脚本 - 快速查找你需要的内容
// ========================================

// ========================================
// 1. 按分类查询笔记
// ========================================

// 查询某个分类下的所有笔记
// 用法：将 '编程技巧' 替换为你想要的分类名称
MATCH (c:Category {name: '编程技巧'})<-[:BELONGS_TO]-(n:Note)
RETURN c.name AS 分类, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 10;

// 查询多个分类的笔记
MATCH (c:Category)<-[:BELONGS_TO]-(n:Note)
WHERE c.name IN ['编程技巧', '学习', '工作']
RETURN c.name AS 分类, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 20;

// ========================================
// 2. 按时间查询笔记
// ========================================

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

// 查询本周的笔记
MATCH (n:Note)
WHERE n.created_at >= date() - duration('P7D')
RETURN n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC;

// 查询本月的笔记
MATCH (n:Note)
WHERE n.created_at >= date() - duration('P30D')
RETURN n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC;

// ========================================
// 3. 按实体查询
// ========================================

// 查询某个实体相关的所有笔记
// 用法：将 'Python' 替换为你想查询的实体
MATCH (e:Entity {name: 'Python'})<-[:MENTIONS]-(n:Note)
RETURN e.name AS 实体, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 10;

// 查询多个实体相关的笔记
MATCH (e:Entity)<-[:MENTIONS]-(n:Note)
WHERE e.name IN ['Python', 'LangChain', 'Neo4j']
RETURN e.name AS 实体, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 20;

// ========================================
// 4. 按标签查询
// ========================================

// 查询某个标签下的所有笔记
// 用法：将 '重要' 替换为你想查询的标签
MATCH (t:Tag {name: '重要'})<-[:HAS_TAG]-(n:Note)
RETURN t.name AS 标签, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 10;

// 查询多个标签的笔记
MATCH (t:Tag)<-[:HAS_TAG]-(n:Note)
WHERE t.name IN ['重要', '创意', '待跟进']
RETURN t.name AS 标签, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 20;

// ========================================
// 5. 关系查询 - 查找相关内容
// ========================================

// 查询某个分类的相关分类（通过 RELATED_TO 关系）
MATCH (c:Category {name: '编程技巧'})-[:RELATED_TO]-(related:Category)
RETURN c.name AS 当前分类, related.name AS 相关分类;

// 查询某个实体的相关实体
MATCH (e:Entity {name: 'Python'})-[:RELATED_TO]-(related:Entity)
RETURN e.name AS 当前实体, related.name AS 相关实体;

// 查询某个笔记相关的笔记（通过共同实体）
MATCH (n1:Note)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(n2:Note)
WHERE n1.id = 'init_note_001' AND n1 <> n2
RETURN n1.content AS 原笔记, n2.content AS 相关笔记, e.name AS 共同实体
LIMIT 10;

// ========================================
// 6. 组合查询 - 多维度筛选
// ========================================

// 查询某个分类下包含某个实体的笔记
MATCH (c:Category {name: '编程技巧'})<-[:BELONGS_TO]-(n:Note)-[:MENTIONS]->(e:Entity)
WHERE e.name = 'Python'
RETURN c.name AS 分类, e.name AS 实体, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC;

// 查询某个分类下有某个标签的笔记
MATCH (c:Category {name: '学习'})<-[:BELONGS_TO]-(n:Note)-[:HAS_TAG]->(t:Tag)
WHERE t.name = '重要'
RETURN c.name AS 分类, t.name AS 标签, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC;

// 查询最近N天某个分类的笔记
MATCH (c:Category)<-[:BELONGS_TO]-(n:Note)
WHERE c.name = '工作' AND n.created_at >= datetime() - duration('P7D')
RETURN c.name AS 分类, n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC;

// ========================================
// 7. 统计查询
// ========================================

// 统计每个分类的笔记数量
MATCH (c:Category)<-[:BELONGS_TO]-(n:Note)
RETURN c.name AS 分类, count(n) AS 笔记数量
ORDER BY count(n) DESC;

// 统计每个实体的出现次数
MATCH (e:Entity)<-[:MENTIONS]-(n:Note)
RETURN e.name AS 实体, count(n) AS 提及次数
ORDER BY count(n) DESC
LIMIT 20;

// 统计每个标签的使用次数
MATCH (t:Tag)<-[:HAS_TAG]-(n:Note)
RETURN t.name AS 标签, count(n) AS 使用次数
ORDER BY count(n) DESC
LIMIT 20;

// 统计最近7天每天的笔记数量
MATCH (n:Note)
WHERE n.created_at >= datetime() - duration('P7D')
RETURN date(n.created_at) AS 日期, count(n) AS 笔记数量
ORDER BY date DESC;

// ========================================
// 8. 路径查询 - 查找知识链
// ========================================

// 查询两个实体之间的最短路径
MATCH path = shortestPath(
  (e1:Entity {name: 'Python'})-[*]-(e2:Entity {name: 'Neo4j'})
)
RETURN [node in nodes(path) | node.name] AS 知识路径;

// 查询从一个分类到另一个分类的路径
MATCH path = (c1:Category {name: '编程技巧'})-[*]-(c2:Category {name: '目标'})
RETURN [node in nodes(path) | node.name] AS 分类路径;

// ========================================
// 9. 高级查询 - 灵感相关
// ========================================

// 查询所有灵感笔记
MATCH (c:Category {name: '灵感'})<-[:BELONGS_TO]-(n:Note)
RETURN n.content AS 灵感内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 20;

// 查询灵感相关的分类（通过 CAN_BECOME 关系）
MATCH (inspiration:Category {name: '灵感'})-[:CAN_BECOME]->(related:Category)
RETURN inspiration.name AS 灵感, related.name AS 可转化为
ORDER BY related.name;

// 查询生成灵感的来源
MATCH (inspiration:Category {name: '灵感'})<-[:GENERATES]-(source:Category)
RETURN source.name AS 灵感来源, inspiration.name AS 灵感;

// ========================================
// 10. 待办和目标查询
// ========================================

// 查询所有待办事项
MATCH (c:Category {name: '待办'})<-[:BELONGS_TO]-(n:Note)
RETURN n.content AS 待办内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC;

// 查询所有目标
MATCH (c:Category {name: '目标'})<-[:BELONGS_TO]-(n:Note)
RETURN n.content AS 目标内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC;

// 查询未完成的目标（没有"已完成"标签的）
MATCH (c:Category {name: '目标'})<-[:BELONGS_TO]-(n:Note)
WHERE NOT (n)-[:HAS_TAG]->(:Tag {name: '已完成'})
RETURN n.content AS 未完成目标, n.created_at AS 创建时间
ORDER BY n.created_at DESC;

// ========================================
// 11. 全文搜索
// ========================================

// 搜索笔记内容（模糊匹配）
MATCH (n:Note)
WHERE n.content CONTAINS 'LangChain'
RETURN n.content AS 笔记内容, n.created_at AS 创建时间
ORDER BY n.created_at DESC
LIMIT 10;

// 搜索实体名称
MATCH (e:Entity)
WHERE e.name CONTAINS 'Py'
RETURN e.name AS 实体, [(e)<-[:MENTIONS]-(n) | n.content][0..2] AS 相关笔记
LIMIT 10;

// ========================================
// 12. 聚合查询 - 获取概览
// ========================================

// 获取最近的笔记概览（包含分类和标签）
MATCH (n:Note)
OPTIONAL MATCH (n)-[:BELONGS_TO]->(c:Category)
OPTIONAL MATCH (n)-[:HAS_TAG]->(t:Tag)
WHERE n.created_at >= datetime() - duration('P7D')
RETURN n.content AS 笔记, c.name AS 分类, collect(t.name) AS 标签, n.created_at AS 时间
ORDER BY n.created_at DESC
LIMIT 20;

// 获取某个实体的完整信息（笔记、分类、标签、相关实体）
MATCH (e:Entity {name: 'Python'})
OPTIONAL MATCH (e)<-[:MENTIONS]-(n:Note)
OPTIONAL MATCH (n)-[:BELONGS_TO]->(c:Category)
OPTIONAL MATCH (n)-[:HAS_TAG]->(t:Tag)
OPTIONAL MATCH (e)-[:RELATED_TO]-(related:Entity)
RETURN 
  e.name AS 实体,
  collect(DISTINCT n.content)[0..5] AS 相关笔记,
  collect(DISTINCT c.name) AS 涉及分类,
  collect(DISTINCT t.name) AS 相关标签,
  collect(DISTINCT related.name)[0..5] AS 关联实体
LIMIT 1;

// ========================================
// 13. 清理和维护查询
// ========================================

// 查找孤立节点（没有关系的节点）
MATCH (n)
WHERE NOT (n)-[]-()
RETURN labels(n) AS 类型, count(n) AS 数量
ORDER BY count(n) DESC;

// 查找重复的笔记（内容相似的）
MATCH (n1:Note), (n2:Note)
WHERE n1.id < n2.id 
  AND n1.content = n2.content
RETURN n1.id AS 笔记1, n2.id AS 笔记2, n1.content AS 内容
LIMIT 20;

// ========================================
// 完成
// ========================================

RETURN '✅ 查询脚本加载完成！' AS message;
