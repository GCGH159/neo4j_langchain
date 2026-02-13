"""
标签生成Agent
使用LLM分析文本内容，生成智能标签
"""
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.config.logging_config import log
from app.config.settings import settings


class TagSuggestion(BaseModel):
    """标签建议模型"""
    tag_name: str = Field(description="标签名称，简洁明了，1-4个字")
    confidence: float = Field(description="置信度，0-1之间的浮点数")
    tag_type: str = Field(description="标签类型：topic, emotion, action, time, location, person")


class TagGenerationResult(BaseModel):
    """标签生成结果模型"""
    tags: List[TagSuggestion] = Field(description="生成的标签列表")
    summary: str = Field(description="标签生成摘要")


class TagGenerationAgent:
    """标签生成Agent类"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,
            api_key=settings.openai_api_key
        )
        self.parser = PydanticOutputParser(pydantic_object=TagGenerationResult)
        
        # 标签类型定义
        self.tag_types = {
            "topic": "主题",
            "emotion": "情感",
            "action": "动作",
            "time": "时间",
            "location": "地点",
            "person": "人物"
        }
        
        # 提示词模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能标签生成助手，负责根据文本内容生成合适的标签。

标签类型说明：
- topic: 主题标签（如：工作、学习、健康、旅行、美食等）
- emotion: 情感标签（如：开心、焦虑、期待、满足等）
- action: 动作标签（如：会议、运动、阅读、购物等）
- time: 时间标签（如：早晨、下午、周末、节日等）
- location: 地点标签（如：办公室、家里、咖啡厅、公园等）
- person: 人物标签（如：家人、朋友、同事、客户等）

标签生成规则：
1. 标签名称要简洁明了，1-4个字
2. 每个标签应该准确反映文本的一个方面
3. 优先生成主题和情感标签
4. 避免生成过于宽泛的标签（如"其他"）
5. 标签之间应该有一定的区分度
6. 只保留置信度大于0.5的标签
7. 最多生成5个标签

请根据用户提供的文本，生成合适的标签。

{format_instructions}"""),
            ("user", "文本内容：{text}")
        ])
    
    def generate_tags(self, text: str) -> TagGenerationResult:
        """
        生成标签
        
        Args:
            text: 待分析的文本内容
        
        Returns:
            标签生成结果
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
            
            # 过滤低置信度标签
            result.tags = [tag for tag in result.tags if tag.confidence > 0.5]
            
            log.info(f"Generated {len(result.tags)} tags")
            return result
        
        except Exception as e:
            log.error(f"Error generating tags: {e}")
            return TagGenerationResult(
                tags=[],
                summary="生成标签时出错"
            )
    
    def generate_tags_batch(
        self,
        texts: List[str]
    ) -> List[TagGenerationResult]:
        """
        批量生成标签
        
        Args:
            texts: 待分析的文本列表
        
        Returns:
            标签生成结果列表
        """
        results = []
        for text in texts:
            try:
                result = self.generate_tags(text)
                results.append(result)
            except Exception as e:
                log.error(f"Error generating tags for text: {e}")
                results.append(TagGenerationResult(
                    tags=[],
                    summary="生成标签时出错"
                ))
        return results
    
    def suggest_tags_from_context(
        self,
        text: str,
        existing_tags: List[str]
    ) -> Dict:
        """
        基于上下文建议标签
        
        Args:
            text: 待分析的文本内容
            existing_tags: 已存在的标签列表
        
        Returns:
            标签建议字典
        """
        try:
            # 1. 生成新标签
            new_result = self.generate_tags(text)
            
            # 2. 检查与现有标签的相似性
            suggested_tags = []
            for new_tag in new_result.tags:
                similar_tag = self._find_similar_tag(
                    new_tag.tag_name,
                    existing_tags
                )
                
                if similar_tag:
                    suggested_tags.append({
                        "tag_name": similar_tag,
                        "confidence": new_tag.confidence,
                        "tag_type": new_tag.tag_type,
                        "action": "use_existing",
                        "reason": f"与现有标签'{similar_tag}'相似"
                    })
                else:
                    suggested_tags.append({
                        "tag_name": new_tag.tag_name,
                        "confidence": new_tag.confidence,
                        "tag_type": new_tag.tag_type,
                        "action": "create_new",
                        "reason": "新标签"
                    })
            
            return {
                "tags": suggested_tags,
                "summary": new_result.summary
            }
        
        except Exception as e:
            log.error(f"Error suggesting tags from context: {e}")
            return {
                "tags": [],
                "summary": "生成标签建议时出错"
            }
    
    def _find_similar_tag(
        self,
        new_tag: str,
        existing_tags: List[str]
    ) -> Optional[str]:
        """
        查找相似的现有标签
        
        Args:
            new_tag: 新标签名称
            existing_tags: 现有标签列表
        
        Returns:
            相似的标签名称，如果没有则返回None
        """
        # 简单的字符串匹配
        for tag in existing_tags:
            if new_tag in tag or tag in new_tag:
                return tag
        
        return None
    
    def merge_tags(
        self,
        tags1: List[TagSuggestion],
        tags2: List[TagSuggestion]
    ) -> List[TagSuggestion]:
        """
        合并标签列表，去重并按置信度排序
        
        Args:
            tags1: 标签列表1
            tags2: 标签列表2
        
        Returns:
            合并后的标签列表
        """
        # 合并标签
        all_tags = tags1 + tags2
        
        # 去重（相同标签名称保留置信度高的）
        tag_dict = {}
        for tag in all_tags:
            if tag.tag_name not in tag_dict:
                tag_dict[tag.tag_name] = tag
            else:
                if tag.confidence > tag_dict[tag.tag_name].confidence:
                    tag_dict[tag.tag_name] = tag
        
        # 按置信度排序
        merged_tags = sorted(
            tag_dict.values(),
            key=lambda x: x.confidence,
            reverse=True
        )
        
        return merged_tags
    
    def extract_emotion_tags(self, text: str) -> List[TagSuggestion]:
        """
        提取情感标签
        
        Args:
            text: 文本内容
        
        Returns:
            情感标签列表
        """
        try:
            prompt = f"""请从以下文本中提取情感标签（如：开心、焦虑、期待、满足、愤怒、悲伤等），每行一个标签：
{text}

只输出情感标签列表，不要其他内容。"""
            response = self.llm.invoke(prompt)
            
            emotions = [
                line.strip()
                for line in response.content.strip().split('\n')
                if line.strip()
            ]
            
            return [
                TagSuggestion(
                    tag_name=emotion,
                    confidence=0.7,
                    tag_type="emotion"
                )
                for emotion in emotions
            ]
        
        except Exception as e:
            log.error(f"Error extracting emotion tags: {e}")
            return []


# 全局标签生成Agent实例
tag_agent = TagGenerationAgent()
