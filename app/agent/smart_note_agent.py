"""
智能笔记 Agent - Plan-and-Execute 模式，支持多轮反思
"""
from typing import List, Dict, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from app.tools.analysis_tools import (
    analyze_text_entities,
    get_entity_position,
    suggest_relations,
    analyze_graph_position
)
from app.tools.note_tools import save_note, execute_raw_cypher, get_graph_schema
from config import config


class SmartNoteAgent:
    """
    智能笔记助手，采用 Plan-and-Execute 模式

    工作流程：
    1. 接收用户输入
    2. 分析文本，提取实体和标签
    3. 查询实体的现有位置
    4. 反思和规划：确定应该放在哪里
    5. 执行保存操作
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
            temperature=0.7,
        )

        self.tools = [
            analyze_text_entities,
            get_entity_position,
            suggest_relations,
            analyze_graph_position,
            save_note,
            execute_raw_cypher,
            get_graph_schema
        ]

        self.system_prompt = """你是一个智能笔记助手，采用"先思考后行动"的工作模式。

你的工作流程：

1. **第1步：提取分析**
   - 当用户要保存笔记时，先调用 `analyze_text_entities` 分析文本
   - 识别出关键实体和标签

2. **第2步：查询位置**
   - 对每个识别出的实体，调用 `get_entity_position` 查询现有位置
   - 调用 `analyze_graph_position` 分析实体的重要性
   - 了解这些实体在图中的上下文

3. **第3步：反思规划**
   - 基于查询结果，调用 `suggest_relations` 思考新实体应该放在哪里
   - 和谁建立关系？关系类型是什么？
   - 是否需要补充现有的关联？

4. **第4步：执行保存**
   - 调用 `save_note` 保存笔记
   - 根据规划补充必要的关联关系

重要原则：
- 不要急于保存，先了解情况
- 每次只处理一个任务
- 如果发现问题，及时调整计划
- 用中文回复，解释你的思考过程

你的回应应该包含：
- 你正在做什么（分析/查询/反思/执行）
- 你发现了什么
- 你打算怎么做
"""

        self.graph = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt
        )

    def chat(self, user_input: str) -> str:
        """
        与 Agent 对话
        """
        try:
            inputs = {"messages": [{"role": "user", "content": user_input}]}
            final_state = self.graph.invoke(inputs)

            messages = final_state.get("messages", [])
            if messages:
                last_message = messages[-1]
                return last_message.content
            return "Agent 没有回应。"

        except Exception as e:
            return f"❌ Agent 运行出错: {e}"


class PlannerThenExecutor:
    """
    规划器-执行器分离模式
    更清晰地展示"先规划后执行"的工作流
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
            temperature=0.3,
        )

    def plan(self, content: str) -> Dict:
        """
        规划阶段：分析并制定保存计划

        Args:
            content: 要保存的笔记内容

        Returns:
            包含分析结果的字典
        """
        from langchain_core.messages import HumanMessage
        from langchain_core.prompts import ChatPromptTemplate

        messages = [
            ("system", "分析以下文本，提取关键实体（人名、技术名词、地点等）和标签（主题分类）。用中文回复。"),
            ("human", f"文本内容：\n{content}")
        ]

        prompt = ChatPromptTemplate.from_messages(messages)
        response = self.llm.invoke(prompt.format_messages())
        entities_analysis = response.content if hasattr(response, 'content') else str(response)

        return {
            "content": content,
            "entities_analysis": entities_analysis,
            "status": "planned"
        }

    def analyze_positions(self, plan: Dict) -> Dict:
        """
        分析阶段：查询实体的现有位置

        Args:
            plan: 规划阶段的结果

        Returns:
            包含位置分析结果的字典
        """
        import re

        content = plan["content"]
        entities = []
        noise_entities = []

        # 1. 提取技术关键词（这是核心实体）
        tech_keywords = [
            'Python', 'JavaScript', 'Java', 'Go', 'Rust', 'C++', 'TypeScript',
            'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'Spring',
            'LangChain', 'OpenAI', 'Neo4j', 'PostgreSQL', 'MongoDB', 'Redis',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'AI', 'LLM',
            'ChatGPT', 'TensorFlow', 'PyTorch', 'FastAPI', 'GraphQL',
            '数据分析', '机器学习', '深度学习', '神经网络', '大语言模型'
        ]

        for kw in tech_keywords:
            if kw.lower() in content.lower():
                if kw not in entities:
                    entities.append(kw)

        # 2. 提取有意义的词组（3-5个字的完整概念）
        meaningful_phrases = [
            '编程语言', '系统编程', '机器学习', '深度学习', '自然语言处理',
            '图数据库', '关系型数据库', '微服务架构', '前后端分离',
            '知识图谱', '向量数据库', '容器编排', '持续集成'
        ]

        for phrase in meaningful_phrases:
            if phrase in content and phrase not in entities:
                entities.append(phrase)

        # 3. 提取中文实体（只保留真正有意义的）
        # 常见无意义词汇列表
        stop_words = set([
            '一个', '这个', '那个', '什么', '如何', '可以', '应该', '然后',
            '因为', '所以', '但是', '而且', '或者', '如果', '虽然', '只是',
            '还有', '就是', '不是', '自己', '现在', '已经', '开始',
            '用于', '适合', '主要', '最近', '今天', '昨天', '明天',
            '学习', '了解', '发现', '使用', '参考', '打算', '创建',
            '一门', '用于', '非常', '一起', '一起', '东西', '最近'
        ])

        # 只提取4-5个字的完整概念
        chinese_concepts = re.findall(r'[\u4e00-\u9fa5]{4,6}', content)
        for concept in chinese_concepts:
            # 过滤掉包含停用词的
            is_noise = False
            for stop in stop_words:
                if stop in concept:
                    is_noise = True
                    break
            # 过滤掉纯数字或纯标点的
            if re.match(r'^[\d\s，。！？]+$', concept):
                is_noise = True
            
            if not is_noise and concept not in entities and len(concept) >= 3:
                entities.append(concept)

        # 4. 只保留核心实体（最多5个），其他作为噪音
        core_entities = []
        for e in entities:
            # 保留技术关键词和完整概念
            is_core = any(kw.lower() == e.lower() for kw in tech_keywords)
            is_concept = any(phrase == e for phrase in meaningful_phrases)
            if is_core or is_concept:
                core_entities.append(e)

        final_entities = core_entities if core_entities else entities[:3]
        
        # 查询每个核心实体的位置
        positions = {}
        for entity in final_entities[:5]:
            result = get_entity_position.invoke({"entity_name": entity})
            positions[entity] = result

        return {
            "content": plan["content"],
            "entities_analysis": plan["entities_analysis"],
            "entities": final_entities,
            "positions": positions,
            "status": "analyzed"
        }

    def reflect(self, analysis: Dict) -> Dict:
        """
        反思阶段：基于分析结果，制定具体行动计划

        Args:
            analysis: 分析阶段的结果

        Returns:
            包含行动计划的结果
        """
        from langchain_core.prompts import ChatPromptTemplate

        content = analysis["content"]
        entities = analysis["entities"]
        positions = analysis["positions"]

        content_text = analysis["content"]
        entities_list = analysis["entities"]
        positions_dict = analysis["positions"]

        entities_str = ', '.join(entities_list) if entities_list else '新实体'
        
        positions_text = []
        for entity, pos in positions_dict.items():
            positions_text.append(f"【{entity}】{pos}")
        positions_str = '\n'.join(positions_text) if positions_text else '暂无现有关联'

        messages = [
            ("system", "你是一个知识图谱规划专家。根据以下分析结果，制定具体的行动计划。用中文回复，条理清晰。"),
            ("human", f"【文本内容】\n{content_text}\n\n【提取的实体】\n{entities_str}\n\n【实体位置分析】\n{positions_str}")
        ]

        prompt = ChatPromptTemplate.from_messages(messages)
        response = self.llm.invoke(prompt.format_messages())
        action_plan = response.content if hasattr(response, 'content') else str(response)

        return {
            "content": content,
            "entities_analysis": analysis["entities_analysis"],
            "entities": entities,
            "positions": positions,
            "action_plan": action_plan,
            "status": "reflected"
        }

    def execute(self, reflection: Dict) -> Dict:
        """
        执行阶段：根据行动计划保存笔记

        Args:
            reflection: 反思阶段的结果

        Returns:
            执行结果
        """
        content = reflection["content"]
        entities = reflection["entities"]
        action_plan = reflection["action_plan"]

        # 提取标签
        tags = []
        if "编程" in content or "代码" in content:
            tags.append("编程")
        if "AI" in content or "模型" in content:
            tags.append("AI")
        if "数据库" in content or "存储" in content:
            tags.append("数据库")
        if not tags:
            tags = ["通用"]

        # 调用 save_note 保存
        result = save_note.invoke({
            "content": content,
            "entities": entities,
            "tags": tags
        })

        # 补充关系（只对核心有意义实体建立关系）
        relations_added = []
        meaningful_entities = [e for e in entities if len(e) >= 3 and not any(c in e for c in ['的', '是', '了', '在', '和', '与'])]
        
        if len(meaningful_entities) > 1:
            # 只创建前5个实体之间的关系
            for i in range(min(len(meaningful_entities), 5)):
                for j in range(i + 1, min(len(meaningful_entities), 5)):
                    e1, e2 = meaningful_entities[i], meaningful_entities[j]
                    
                    # 只建立有意义的关系（避免噪音）
                    if len(e1) > 2 and len(e2) > 2:
                        rel_result = execute_raw_cypher.invoke({
                            "query": """
                            MERGE (e1:Entity {name: $e1})
                            MERGE (e2:Entity {name: $e2})
                            MERGE (e1)-[:RELATED_TO]->(e2)
                            """,
                            "params": {"e1": e1, "e2": e2}
                        })
                        relations_added.append(f"{e1} <-> {e2}")

        return {
            "content": content,
            "entities": entities,
            "tags": tags,
            "save_result": result,
            "relations_added": relations_added,
            "action_plan": action_plan,
            "status": "executed"
        }

    def smart_save(self, content: str) -> str:
        """
        完整的智能保存流程（先规划后执行）

        Args:
            content: 要保存的笔记内容

        Returns:
            完整的执行报告
        """
        report = ["🧠 **智能保存流程开始**\n"]

        # Step 1: 规划
        plan = self.plan(content)
        report.append("📋 **第1步：规划**")
        report.append(f"  提取的实体分析：\n  {plan['entities_analysis']}\n")

        # Step 2: 分析位置
        analysis = self.analyze_positions(plan)
        report.append("🔍 **第2步：分析现有位置**")
        if analysis["entities"]:
            report.append(f"  发现 {len(analysis['entities'])} 个实体：")
            for entity, position in analysis["positions"].items():
                report.append(f"\n  📌 {entity}:")
                report.append(f"     {position[:100]}..." if len(position) > 100 else f"     {position}")
        else:
            report.append("  都是新实体，暂无现有关联")
        report.append("")

        # Step 3: 反思
        reflection = self.reflect(analysis)
        report.append("💭 **第3步：反思与规划**")
        report.append(f"  行动计划：\n  {reflection['action_plan']}\n")

        # Step 4: 执行
        execution = self.execute(reflection)
        report.append("✅ **第4步：执行保存**")
        report.append(f"  保存结果：{execution['save_result']}")
        if execution['relations_added']:
            report.append(f"\n  补充关系：")
            for rel in execution['relations_added']:
                report.append(f"    • {rel}")

        return "\n".join(report)


smart_note_agent = SmartNoteAgent()
smart_planner = PlannerThenExecutor()


def smart_save(content: str) -> str:
    """
    智能保存笔记（入口函数）

    Args:
        content: 笔记内容

    Returns:
        执行报告
    """
    return smart_planner.smart_save(content)
