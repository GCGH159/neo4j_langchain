// ========================================
// 知识图谱基础关系网初始化脚本
// ========================================
// 用途：创建日常生活中的基础关系网络
// 包含：日常、生活、编程技巧、动漫、学习、英语、健身、任务、工作、待办、目标
// ========================================

// 清理旧数据（可选，谨慎使用）
// MATCH (n) DETACH DELETE n;

// ========================================
// 1. 创建核心分类实体
// ========================================

CREATE (daily:Category {name: '日常', type: 'category', description: '日常生活的记录和活动', created_at: datetime()})
CREATE (life:Category {name: '生活', type: 'category', description: '生活相关的记录', created_at: datetime()})
CREATE (coding:Category {name: '编程技巧', type: 'category', description: '编程相关的技巧和经验', created_at: datetime()})
CREATE (anime:Category {name: '动漫', type: 'category', description: '动漫相关的记录', created_at: datetime()})
CREATE (study:Category {name: '学习', type: 'category', description: '学习相关的记录', created_at: datetime()})
CREATE (english:Category {name: '英语', type: 'category', description: '英语学习相关', created_at: datetime()})
CREATE (fitness:Category {name: '健身', type: 'category', description: '健身运动相关', created_at: datetime()})
CREATE (task:Category {name: '任务', type: 'category', description: '待完成的任务', created_at: datetime()})
CREATE (work:Category {name: '工作', type: 'category', description: '工作相关记录', created_at: datetime()})
CREATE (todo:Category {name: '待办', type: 'category', description: '待办事项', created_at: datetime()})
CREATE (goal:Category {name: '目标', type: 'category', description: '目标和计划', created_at: datetime()});

// ========================================
// 2. 创建实体间的关联关系
// ========================================

// 日常 的关联
CREATE (daily)-[:RELATED_TO]->(life)
CREATE (daily)-[:RELATED_TO]->(work)
CREATE (daily)-[:RELATED_TO]->(study)
CREATE (daily)-[:RELATED_TO]->(task)
CREATE (daily)-[:RELATED_TO]->(todo);

// 生活的关联
CREATE (life)-[:RELATED_TO]->(fitness)
CREATE (life)-[:RELATED_TO]->(anime)
CREATE (life)-[:RELATED_TO]->(english);
CREATE (life)-[:RELATED_TO]->(daily);

// 编程技巧的关联
CREATE (coding)-[:RELATED_TO]->(study)
CREATE (coding)-[:RELATED_TO]->(work)
CREATE (coding)-[:RELATED_TO]->(goal);
CREATE (coding)-[:PART_OF]->(work);

// 动漫的关联
CREATE (anime)-[:RELATED_TO]->(life);
CREATE (anime)-[:PART_OF]->(daily);

// 学习的关联
CREATE (study)-[:RELATED_TO]->(english)
CREATE (study)-[:RELATED_TO]->(coding)
CREATE (study)-[:RELATED_TO]->(goal);
CREATE (study)-[:HELPS_ACHIEVE]->(goal);

// 英语的关联
CREATE (english)-[:RELATED_TO]->(study);
CREATE (english)-::PART_OF]->(study);
CREATE (english)-[:HELPS_ACHIEVE]->(goal);

// 健身的关联
CREATE (fitness)-[:RELATED_TO]->(life);
CREATE (fitness)-::PART_OF]->(daily);
CREATE (fitness)-::HELPS_ACHIEVE]->(goal);
CREATE (fitness)-::RELATED_TO]->(todo);

// 任务的关联
CREATE (task)-[:RELATED_TO]->(work);
CREATE (task)-::PART_OF]->(todo);
CREATE (task)-::CONTRIBUTES_TO]->(goal);

// 工作的关联
CREATE (work)-::PART_OF]->(daily);
CREATE (work)-::RELATED_TO]->(coding);
CREATE (work)-::CONTRIBUTES_TO]->(goal);

// 待办的关联
CREATE (todo)-::PART_OF]->(task);
CREATE (todo)-::HELPS_ACHIEVE]->(goal);
CREATE (todo)-::RELATED_TO]->(daily);

// 目标的关联
CREATE (goal)-::RELATED_TO]->(study);
CREATE (goal)-::RELATED_TO]->(work);
CREATE (goal)-::RELATED_TO]->(fitness);

// ========================================
// 3. 创建一些示例实体和笔记
// ========================================

// 示例笔记
CREATE (note1:Note {
    id: 'init_note_001',
    content: '今天学习了 Python 的装饰器用法，很强大！',
    created_at: datetime()
});

CREATE (note2:Note {
    id: 'init_note_002',
    content: '晚上去健身房锻炼了1小时，感觉很棒',
    created_at: datetime()
});

CREATE (note3:Note {
    id: 'init_note_003',
    content: '看了一集动漫，剧情很精彩',
    created_at: datetime()
});

CREATE (note4:Note {
    id: 'init_note_004',
    content: '完成了项目中的 API 接口开发任务',
    created_at: datetime()
});

CREATE (note5:Note {
    id: 'init_note_005',
    content: '制定了本周的学习计划：每天学习英语30分钟',
    created_at: datetime()
});

// ========================================
// 4. 建立笔记与分类的关联
// ========================================

CREATE (note1)-[:BELONGS_TO]->(coding);
CREATE (note1)-[:BELONGS_TO]->(study);

CREATE (note2)-[:BELONGS_TO]->(fitness);
CREATE (note2)-[:BELONGS_TO]->(daily);

CREATE (note3)-[:BELONGS_TO]->(anime);
CREATE (note3)-[:BELONGS_TO]->(life);

CREATE (note4)-[:BELONGS_TO]->(work);
CREATE (note4)-[:BELONGS_TO]->(task);

CREATE (note5)-[:BELONGS_TO]->(english);
CREATE (note5)-[:BELONGS_TO]->(goal);

// ========================================
// 5. 创建一些实体节点（用于更细粒度的管理）
// ========================================

// 技术实体
CREATE (python:Entity {name: 'Python', type: 'technology', created_at: datetime()});
CREATE (langchain:Entity {name: 'LangChain', type: 'technology', created_at: datetime()});
CREATE (neo4j:Entity {name: 'Neo4j', type: 'technology', created_at: datetime()});

// 活动实体
CREATE (gym:Entity {name: '健身房', type: 'activity', created_at: datetime()});
CREATE (running:Entity {name: '跑步', type: 'activity', created_at: datetime()});

// 目标实体
CREATE (learn_goal:Entity {name: '学习目标', type: 'goal', created_at: datetime()});
CREATE (work_goal:Entity {name: '工作目标', type: 'goal', created_at: datetime()});

// ========================================
// 6. 建立实体与分类的关联
// ========================================

CREATE (python)-[:RELATED_TO]->(coding);
CREATE (langchain)-[:RELATED_TO]->(coding);
CREATE (neo4j)-[:RELATED_TO]->(coding);

CREATE (gym)-[:RELATED_TO]->(fitness);
CREATE (running)-[:RELATED_TO]->(fitness);

CREATE (learn_goal)-[:RELATED_TO]->(goal);
CREATE (work_goal)-[:RELATED_TO]->(goal);

// ========================================
// 7. 创建索引（优化查询性能）
// ========================================

// 为分类名称创建索引
CREATE INDEX category_name_index IF NOT EXISTS FOR (c:Category) ON (c.name);

// 为笔记创建索引
CREATE INDEX note_id_index IF NOT EXISTS FOR (n:Note) ON (n.id);
CREATE INDEX note_created_at_index IF NOT EXISTS FOR (n:Note) ON (n.created_at);

// 为实体创建索引
CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name);

// ========================================
// 8. 验证创建结果
// ========================================

// 统计各类节点数量
MATCH (c:Category) RETURN 'Category 节点数: ' + toString(count(c)) AS result;
MATCH (n:Note) RETURN 'Note 节点数: ' + toString(count(n)) AS result;
MATCH (e:Entity) RETURN 'Entity 节点数: ' + toString(count(e)) AS result;

// 统计关系数量
MATCH ()-[r]->() RETURN '总关系数: ' + toString(count(r)) AS result;

// ========================================
// 完成
// ========================================

RETURN '✅ 基础关系网初始化完成！' AS message;
