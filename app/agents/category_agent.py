"""
分类生成Agent
使用LLM分析文本内容，生成合适的分类建议
"""
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.config.logging_config import log
from app.config.settings import settings


class CategorySuggestion(BaseModel):
    """分类建议模型"""
    category_name: str = Field(description="分类名称，简洁明了，2-6个字")
    confidence: float = Field(description="置信度，0-1之间的浮点数")
    reason: str = Field(description="生成该分类的原因说明")


class CategoryGenerationAgent:
    """分类生成Agent类"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,
            api_key=settings.openai_api_key
        )
        self.parser = PydanticOutputParser(pydantic_object=CategorySuggestion)
        
        # 提示词模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能分类助手，负责根据文本内容生成合适的分类名称。

分类规则：
1. 分类名称要简洁明了，2-6个字
2. 分类应该反映文本的核心主题或内容类型
3. 避免使用过于宽泛的分类（如"其他"、"杂项"）
4. 优先使用常见的分类名称（如：工作、生活、学习、健康、旅行、美食、技术、娱乐等）
5. 如果文本内容涉及多个主题，选择最主要的一个

请根据用户提供的文本，生成一个合适的分类建议。

{format_instructions}"""),
            ("user", "文本内容：{text}")
        ])
    
    def generate_category(self, text: str) -> CategorySuggestion:
        """
        生成分类建议
        
        Args:
            text: 待分析的文本内容
        
        Returns:
            分类建议对象
        """
        try:
            # 限制文本长度
            if len(text) > 500:
                text = text[:500] + "..."
            
            # 构建提示词
            prompt_value = self.prompt.format_prompt(
                text=text,
                format_instructions=self.parser.get_format_instructions()
            )
            
            # 调用LLM
            response = self.llm.invoke(prompt_value.to_messages())
            
            # 解析结果
            result = self.parser.parse(response.content)
            
            log.info(f"Generated category: {result.category_name} (confidence: {result.confidence})")
            return result
        
        except Exception as e:
            log.error(f"Error generating category: {e}")
            # 返回默认分类
            return CategorySuggestion(
                category_name="未分类",
                confidence=0.0,
                reason="生成分类时出错，使用默认分类"
            )
    
    def generate_categories_batch(
        self,
        texts: List[str]
    ) -> List[CategorySuggestion]:
        """
        批量生成分类建议
        
        Args:
            texts: 待分析的文本列表
        
        Returns:
            分类建议列表
        """
        results = []
        for text in texts:
            try:
                result = self.generate_category(text)
                results.append(result)
            except Exception as e:
                log.error(f"Error generating category for text: {e}")
                results.append(CategorySuggestion(
                    category_name="未分类",
                    confidence=0.0,
                    reason="生成分类时出错"
                ))
        return results
    
    def suggest_category_tree(
        self,
        text: str,
        existing_categories: List[str]
    ) -> Dict:
        """
        建议分类树结构
        
        Args:
            text: 待分析的文本内容
            existing_categories: 已存在的分类列表
        
        Returns:
            分类建议字典
        """
        try:
            # 1. 生成新分类建议
            new_category = self.generate_category(text)
            
            # 2. 检查是否与现有分类相似
            similar_category = self._find_similar_category(
                new_category.category_name,
                existing_categories
            )
            
            if similar_category:
                return {
                    "action": "use_existing",
                    "category_name": similar_category,
                    "confidence": new_category.confidence,
                    "reason": f"与现有分类'{similar_category}'相似，建议使用现有分类"
                }
            else:
                return {
                    "action": "create_new",
                    "category_name": new_category.category_name,
                    "confidence": new_category.confidence,
                    "reason": new_category.reason
                }
        
        except Exception as e:
            log.error(f"Error suggesting category tree: {e}")
            return {
                "action": "use_default",
                "category_name": "未分类",
                "confidence": 0.0,
                "reason": "生成分类建议时出错"
            }
    
    def _find_similar_category(
        self,
        new_category: str,
        existing_categories: List[str]
    ) -> Optional[str]:
        """
        查找相似的现有分类
        
        Args:
            new_category: 新分类名称
            existing_categories: 现有分类列表
        
        Returns:
            相似的分类名称，如果没有则返回None
        """
        # 简单的字符串匹配
        for category in existing_categories:
            if new_category in category or category in new_category:
                return category
        
        return None


# 全局分类生成Agent实例
category_agent = CategoryGenerationAgent()
