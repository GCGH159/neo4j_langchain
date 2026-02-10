// ========================================
// 扩展初始化脚本 - 添加灵感和其他关联
// ========================================

// 1. 添加灵感分类
// ========================================
CREATE (inspiration:Category {name: '灵感', type: 'category', description: '灵感和创意记录', created_at: datetime()});

// 2. 灵感的关联关系
// ========================================

// 灵感与各个领域的关联
CREATE (inspiration)-[:RELATED_TO]->(study);
CREATE (inspiration)-[:RELATED_TO]->(coding);
CREATE (inspiration)-[:RELATED_TO]->(work);
CREATE (inspiration)-[:RELATED_TO]->(life);
CREATE (inspiration)-[:RELATED_TO]->(anime);
CREATE (inspiration)-[:RELATED_TO]->(daily);

// 灵感可以转化为目标或任务
CREATE (inspiration)-[:CAN_BECOME]->(goal);
CREATE (inspiration)-[:CAN_BECOME]->(task);
CREATE (inspiration)-[:CAN_BECOME]->(todo);

// 灵感来源于学习和生活
CREATE (study)-[:GENERATES]->(inspiration);
CREATE (life)-[:GENERATES]->(inspiration);
CREATE (anime)-[:GENERATES]->(inspiration);

// ========================================
// 3. 添加更多实用分类
// ========================================

CREATE (reading:Category {name: '阅读', type: 'category', description: '阅读相关记录', created_at: datetime()});
CREATE (movie:Category {name: '电影', type: 'category', description: '电影观看记录', created_at: datetime()});
CREATE (music:Category {name: '音乐', type: 'category', description: '音乐相关记录', created_at: datetime()});
CREATE (food:Category {name: '美食', type: 'category', description: '美食记录', created_at: datetime()});
CREATE (travel:Category {name: '旅行', type: 'category', description: '旅行记录', created_at: datetime()});
CREATE (game:Category {name: '游戏', type: 'category', description: '游戏相关', created_at: datetime()});
CREATE (finance:Category {name: '理财', type: 'category', description: '理财相关', created_at: datetime()});
CREATE (health:Category {name: '健康', type: 'category', description: '健康管理', created_at: datetime()});
CREATE (social:Category {name: '社交', type: 'category', description: '社交活动', created_at: datetime()});

// ========================================
// 4. 新分类的关联关系
// ========================================

// 阅读的关联
CREATE (reading)-[:RELATED_TO]->(study);
CREATE (reading)-::PART_OF]->(daily);
CREATE (reading)-::HELPS_ACHIEVE]->(goal);

// 电影的关联
CREATE (movie)-[:RELATED_TO]->(anime);
CREATE (movie)-::PART_OF]->(life);
CREATE (movie)-::PART_OF]->(daily);

// 音乐的关联
CREATE (music)-[:RELATED_TO]->(life);
CREATE (music)-::PART_OF]->(daily);

// 美食的关联
CREATE (food)-[:RELATED_TO]->(life);
CREATE (food)-::PART_OF]->(daily);

// 旅行的关联
CREATE (travel)-[:RELATED_TO]->(life);
CREATE (travel)-::PART_OF]->(goal);
CREATE (travel)-::HELPS_RELAX]->(daily);

// 游戏的关联
CREATE (game)-[:RELATED_TO]->(life);
CREATE (game)-::PART_OF]->(daily);

// 理财的关联
CREATE (finance)-[:RELATED_TO]->(work);
CREATE (finance)-::PART_OF]->(daily);
CREATE (finance)-::HELPS_ACHIEVE]->(goal);

// 健康的关联
CREATE (health)-[:RELATED_TO]->(fitness);
CREATE (health)-::PART_OF]->(life);
CREATE (health)-::HELPS_ACHIEVE]->(goal);

// 社交的关联
CREATE (social)-[:RELATED_TO]->(life);
CREATE (social)-::PART_OF]->(daily);
CREATE (social)-::HELPS_ACHIEVE]->(work);

// ========================================
// 5. 添加示例笔记（包含灵感）
// ========================================

// 灵感笔记
CREATE (note6:Note {
    id: 'init_note_006',
    content: '突然想到一个好点子：可以用 LangChain + Neo4j 构建一个智能知识管理系统',
    created_at: datetime()
});

CREATE (note7:Note {
    id: 'init_note_007',
    content: '阅读了《深度工作》这本书，很有启发',
    created_at: datetime()
});

CREATE (note8:Note {
    id: 'init_note_008',
    content: '看了一部电影《星际穿越》，思考了时间旅行的概念',
    created_at: datetime()
});

CREATE (note9:Note {
    id: 'init_note_009',
    content: '制定了一个理财计划：每月存收入的20%',
    created_at: datetime()
});

CREATE (note10:Note {
    id: 'init_note_010',
    content: '和朋友们聚会，聊了很多有趣的话题',
    created_at: datetime()
});

// ========================================
// 6. 建立新笔记与分类的关联
// ========================================

CREATE (note6)-[:BELONGS_TO]->(inspiration);
CREATE (note6)-[:BELONGS_TO]->(coding);
CREATE (note6)-[:BELONGS_TO]->(study);

CREATE (note7)-[:BELONGS_TO]->(reading);
CREATE (note7)-[:BELONGS_TO]->(study);

CREATE (note8)-[:BELONGS_TO]->(movie);
CREATE (note8)-[:BELONGS_TO]->(life);

CREATE (note9)-[:BELONGS_TO]->(finance);
CREATE (note9)-[:BELONGS_TO]->(goal);

CREATE (note10)-[:BELONGS_TO]->(social);
CREATE (note10)-[:BELONGS_TO]->(life);

// ========================================
// 7. 添加标签系统
// ========================================

CREATE (tag1:Tag {name: '创意', type: 'tag', created_at: datetime()});
CREATE (tag2:Tag {name: '重要', type: 'tag', created_at: datetime()});
CREATE (tag3:Tag {name: '待跟进', type: 'tag', created_at: datetime()});
CREATE (tag4:Tag {name: '已完成', type: 'tag', created_at: datetime()});
CREATE (tag5:Tag {name: '长期', type: 'tag', created_at: datetime()});
CREATE (tag6:Tag {name: '短期', type: 'tag', created_at: datetime()});

// ========================================
// 8. 建立标签与笔记的关联
// ========================================

CREATE (note6)-[:HAS_TAG]->(tag1);
CREATE (note6)-[:HAS_TAG]->(tag2);

CREATE (note9)-[:HAS_TAG]->(tag2);
CREATE (note9)-[:HAS_TAG]->(tag5);

CREATE (note4)-[:HAS_TAG]->(tag4);

CREATE (note5)-[:HAS_TAG]->(tag3);
CREATE (note5)-[:HAS_TAG]->(tag6);

// ========================================
// 9. 创建时间维度节点（用于时间线查询）
// ========================================

CREATE (today:TimeNode {date: date(), type: 'day', created_at: datetime()});
CREATE (this_week:TimeNode {date: date() - duration('P7D'), type: 'week', created_at: datetime()});
CREATE (this_month:TimeNode {date: date() - duration('P30D'), type: 'month', created_at: datetime()});

// ========================================
// 10. 建立时间与笔记的关联
// ========================================

// 为今天的笔记添加时间关联
MATCH (n:Note), (t:TimeNode {type: 'day', date: date()})
WHERE n.id IN ['init_note_001', 'init_note_002', 'init_note_003', 'init_note_004', 'init_note_005', 
              'init_note_006', 'init_note_007', 'init_note_008', 'init_note_009', 'init_note_010']
CREATE (t)-[:CONTAINS]->(n);

// ========================================
// 完成
// ========================================

RETURN '✅ 扩展初始化完成！已添加灵感等新分类和关联。' AS message;
