"""
自然语言查询模块 - 使用 GraphCypherQAChain 实现
"""
from langchain_neo4j import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from app.core.graph import Neo4jConnection
from config import config


class NaturalLanguageQuery:
    """自然语言查询处理器"""
    
    def __init__(self, verbose: bool = True):
        """
        初始化查询处理器
        
        Args:
            verbose: 是否显示详细信息（包括生成的 Cypher）
        """
        self.verbose = verbose
        self._chain = None
        self._llm = None
    
    def _get_llm(self) -> ChatOpenAI:
        """获取 LLM 实例"""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=config.LLM_MODEL,
                api_key=config.LLM_API_KEY,
                base_url=config.LLM_BASE_URL,
                temperature=0,  # 使用低温度以获得更稳定的 Cypher
            )
        return self._llm
    
    def _get_chain(self) -> GraphCypherQAChain:
        """获取查询链实例"""
        if self._chain is None:
            graph = Neo4jConnection.get_graph()
            llm = self._get_llm()
            
            self._chain = GraphCypherQAChain.from_llm(
                llm=llm,
                graph=graph,
                verbose=self.verbose,
                allow_dangerous_requests=True,  # 允许执行生成的 Cypher
                return_intermediate_steps=True,  # 返回中间步骤（包括 Cypher）
            )
        return self._chain
    
    def query(self, question: str) -> dict:
        """
        执行自然语言查询
        
        Args:
            question: 自然语言问题
            
        Returns:
            包含 result 和 intermediate_steps 的字典
        """
        chain = self._get_chain()
        result = chain.invoke({"query": question})
        return result
    
    def simple_query(self, question: str) -> str:
        """
        简化查询，只返回答案字符串
        
        Args:
            question: 自然语言问题
            
        Returns:
            答案字符串
        """
        result = self.query(question)
        return result.get("result", "无法获取答案")
    
    def get_generated_cypher(self, question: str) -> str:
        """
        获取为问题生成的 Cypher 查询（不执行）
        
        Args:
            question: 自然语言问题
            
        Returns:
            生成的 Cypher 查询字符串
        """
        result = self.query(question)
        steps = result.get("intermediate_steps", [])
        if steps and "query" in steps[0]:
            return steps[0]["query"]
        return "无法生成 Cypher"


# 便捷函数
def ask(question: str, verbose: bool = False) -> str:
    """
    便捷函数：用自然语言查询数据库
    
    Args:
        question: 自然语言问题
        verbose: 是否显示详细信息
        
    Returns:
        答案字符串
        
    Example:
        >>> ask("有多少员工？")
        "数据库中共有 10 名员工。"
    """
    nlq = NaturalLanguageQuery(verbose=verbose)
    return nlq.simple_query(question)


def ask_with_cypher(question: str) -> tuple[str, str]:
    """
    查询并返回答案和生成的 Cypher
    
    Args:
        question: 自然语言问题
        
    Returns:
        (答案, Cypher 查询) 元组
    """
    nlq = NaturalLanguageQuery(verbose=False)
    result = nlq.query(question)
    
    answer = result.get("result", "无法获取答案")
    steps = result.get("intermediate_steps", [])
    cypher = steps[0].get("query", "") if steps else ""
    
    return answer, cypher
