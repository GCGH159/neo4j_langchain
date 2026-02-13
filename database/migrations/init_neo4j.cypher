// ============================================
// 速记软件后端系统 - Neo4j图数据库初始化脚本
// ============================================

// 创建全文索引
CREATE FULLTEXT INDEX note_fulltext IF NOT EXISTS FOR (n:Note) ON EACH [n.title, n.content];
CREATE FULLTEXT INDEX event_fulltext IF NOT EXISTS FOR (e:Event) ON EACH [e.title, e.description];

// 创建节点属性索引
CREATE INDEX user_id_index IF NOT EXISTS FOR (u:User) ON (u.id);
CREATE INDEX category_id_index IF NOT EXISTS FOR (c:Category) ON (c.id);
CREATE INDEX tag_id_index IF NOT EXISTS FOR (t:Tag) ON (t.id);
CREATE INDEX event_id_index IF NOT EXISTS FOR (e:Event) ON (e.id);
CREATE INDEX note_id_index IF NOT EXISTS FOR (n:Note) ON (n.id);
CREATE INDEX audio_id_index IF NOT EXISTS FOR (a:Audio) ON (a.id);

// 创建用户ID索引
CREATE INDEX user_created_index IF NOT EXISTS FOR (n:Note) ON (n.user_id);
CREATE INDEX user_created_index_event IF NOT EXISTS FOR (e:Event) ON (e.user_id);

// 创建时间索引
CREATE INDEX note_created_at_index IF NOT EXISTS FOR (n:Note) ON (n.created_at);
CREATE INDEX event_created_at_index IF NOT EXISTS FOR (e:Event) ON (e.created_at);

// ============================================
// 约束定义（确保唯一性）
// ============================================

// 用户ID唯一约束
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;

// 分类ID唯一约束
CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE;

// 标签ID唯一约束
CREATE CONSTRAINT tag_id_unique IF NOT EXISTS FOR (t:Tag) REQUIRE t.id IS UNIQUE;

// 事件ID唯一约束
CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;

// 速记ID唯一约束
CREATE CONSTRAINT note_id_unique IF NOT EXISTS FOR (n:Note) REQUIRE n.id IS UNIQUE;

// 音频ID唯一约束
CREATE CONSTRAINT audio_id_unique IF NOT EXISTS FOR (a:Audio) REQUIRE a.id IS UNIQUE;

// ============================================
// 示例：创建节点和关系（用于测试）
// ============================================

// 创建示例用户
// MERGE (u:User {id: 1, username: 'test_user', created_at: datetime()});

// 创建示例分类
// MERGE (c1:Category {id: 1, name: '学习资料', level: 1, created_at: datetime()});
// MERGE (c2:Category {id: 2, name: '编程', level: 2, parent_id: 1, created_at: datetime()});

// 创建用户-分类偏好关系
// MATCH (u:User {id: 1}), (c1:Category {id: 1})
// MERGE (u)-[:PREFERS {weight: 1.0}]->(c1);

// 创建示例事件
// MERGE (e:Event {id: 1, user_id: 1, title: '学习LangChain', event_type: 'project', status: 'in_progress', priority: 5, created_at: datetime()});

// 创建示例速记
// MERGE (n:Note {id: 1, user_id: 1, title: 'LangChain笔记', content: 'LangChain是一个强大的LLM应用开发框架', source: 'text', created_at: datetime()});

// 创建示例标签
// MERGE (t:Tag {id: 1, name: 'AI', created_at: datetime()});
// MERGE (t2:Tag {id: 2, name: 'Python', created_at: datetime()});

// 创建关系
// MATCH (u:User {id: 1}), (e:Event {id: 1})
// MERGE (u)-[:CREATED]->(e);

// MATCH (u:User {id: 1}), (n:Note {id: 1})
// MERGE (u)-[:CREATED]->(n);

// MATCH (n:Note {id: 1}), (t:Tag {id: 1})
// MERGE (n)-[:TAGGED_WITH {confidence: 0.95, auto_generated: true}]->(t);

// MATCH (n:Note {id: 1}), (t2:Tag {id: 2})
// MERGE (n)-[:TAGGED_WITH {confidence: 0.90, auto_generated: true}]->(t2);

// MATCH (e:Event {id: 1}), (n:Note {id: 1})
// MERGE (e)-[:RELATED_TO {weight: 0.85, reason: 'topic_similarity'}]->(n);

// ============================================
// 常用查询模板
// ============================================

// 查询用户的所有内容
// MATCH (u:User {id: $userId})-[:CREATED]->(content)
// WHERE content:Note OR content:Event
// RETURN content
// ORDER BY content.created_at DESC;

// 查询用户的关系图谱
// MATCH (u:User {id: $userId})-[r*1..2]-(n)
// WHERE n:Category OR n:Tag OR n:Event OR n:Note
// RETURN n, type(r), properties(r)
// LIMIT 100;

// 查询速记的关联内容
// MATCH (n:Note {id: $noteId})-[r:RELATED_TO|:TAGGED_WITH|:BELONGS_TO]-(related)
// RETURN n, related, type(r), properties(r);

// 全文搜索
// CALL db.index.fulltext.queryNodes('note_fulltext', $keyword) YIELD node, score
// RETURN node, score
// ORDER BY score DESC
// LIMIT 50;
