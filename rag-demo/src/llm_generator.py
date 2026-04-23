"""
LLM生成模块 - 支持OpenAI API和本地模型占位
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

try:
    import openai
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

load_dotenv()

@dataclass
class GenerationResult:
    """生成结果"""
    answer: str
    context_used: List[Dict[str, Any]]
    tokens_used: int = 0
    model: str = ""

class LLMGenerator:
    """LLM生成器 - 基于检索上下文生成回答"""
    
    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        初始化LLM生成器
        
        Args:
            model: 模型名称
            api_key: API密钥
            temperature: 温度参数
            max_tokens: 最大生成token数
        """
        self.model = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 初始化OpenAI客户端
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if HAS_OPENAI and api_key and api_key != "your_openai_api_key_here":
            self.client = OpenAI(api_key=api_key)
            self.use_openai = True
            print(f"OpenAI client initialized (model: {self.model})")
        else:
            self.client = None
            self.use_openai = False
            print("OpenAI not available - will use mock generation")
    
    def build_prompt(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        system_prompt: str = None
    ) -> str:
        """
        构建Prompt
        
        Args:
            query: 用户查询
            contexts: 检索到的上下文列表
            system_prompt: 系统提示词
            
        Returns:
            完整的Prompt
        """
        if system_prompt is None:
            system_prompt = """你是一个智能助手，基于提供的参考资料回答用户问题。
请遵循以下规则：
1. 仅基于提供的参考资料回答问题
2. 如果参考资料中没有相关信息，请明确说明"根据现有资料无法回答"
3. 保持回答简洁、准确
4. 适当引用参考资料中的内容
"""
        
        # 组装上下文
        context_text = ""
        for i, ctx in enumerate(contexts, 1):
            content = ctx.get('content', '')
            source = ctx.get('metadata', {}).get('source', 'unknown')
            context_text += f"\n[{i}] 来源: {source}\n{content}\n"
        
        prompt = f"""{system_prompt}

## 参考资料
{context_text}

## 用户问题
{query}

## 回答
"""
        
        return prompt
    
    def generate(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        system_prompt: str = None
    ) -> GenerationResult:
        """
        生成回答
        
        Args:
            query: 用户查询
            contexts: 检索上下文
            system_prompt: 系统提示词
            
        Returns:
            GenerationResult对象
        """
        prompt = self.build_prompt(query, contexts, system_prompt)
        
        if self.use_openai:
            return self._generate_openai(prompt, contexts)
        else:
            return self._generate_mock(prompt, contexts)
    
    def _generate_openai(
        self,
        prompt: str,
        contexts: List[Dict[str, Any]]
    ) -> GenerationResult:
        """使用OpenAI生成"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return GenerationResult(
                answer=answer,
                context_used=contexts,
                tokens_used=tokens_used,
                model=self.model
            )
        
        except Exception as e:
            print(f"OpenAI generation error: {e}")
            return self._generate_mock(prompt, contexts)
    
    def _generate_mock(
        self,
        prompt: str,
        contexts: List[Dict[str, Any]]
    ) -> GenerationResult:
        """Mock生成 - 当OpenAI不可用时使用"""
        # 提取关键信息作为回答
        if contexts:
            # 简单的摘要回答
            answer = "【Mock Mode - OpenAI API not available】\n\n"
            answer += "基于检索到的参考资料，我可以提供以下信息：\n\n"
            
            for i, ctx in enumerate(contexts, 1):
                content = ctx.get('content', '')[:200]
                source = ctx.get('metadata', {}).get('source', 'unknown')
                answer += f"{i}. [{source}] {content}...\n\n"
            
            answer += "\n（注：这是模拟回答。如需完整回答，请配置OpenAI API密钥）"
        else:
            answer = "未找到相关参考资料，无法回答问题。"
        
        return GenerationResult(
            answer=answer,
            context_used=contexts,
            tokens_used=0,
            model="mock"
        )
    
    def generate_stream(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        system_prompt: str = None
    ):
        """
        流式生成（仅支持OpenAI）
        
        Args:
            query: 用户查询
            contexts: 检索上下文
            system_prompt: 系统提示词
            
        Yields:
            生成的文本片段
        """
        if not self.use_openai:
            # Mock模式不支持流式
            result = self._generate_mock(self.build_prompt(query, contexts, system_prompt), contexts)
            yield result.answer
            return
        
        prompt = self.build_prompt(query, contexts, system_prompt)
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            print(f"Streaming error: {e}")
            yield "生成失败，请稍后重试。"


class SimpleRAGChain:
    """简单的RAG链 - 整合检索和生成"""
    
    def __init__(self, rag_engine, llm_generator):
        """
        初始化RAG链
        
        Args:
            rag_engine: RAG引擎实例
            llm_generator: LLM生成器实例
        """
        self.rag_engine = rag_engine
        self.llm_generator = llm_generator
    
    def query(
        self,
        question: str,
        retrieval_mode: str = "hybrid",
        top_k: int = 5
    ) -> GenerationResult:
        """
        执行RAG查询
        
        Args:
            question: 用户问题
            retrieval_mode: 检索模式
            top_k: 检索结果数量
            
        Returns:
            GenerationResult
        """
        # 1. 检索相关文档
        print(f"\n🔍 Retrieving documents (mode: {retrieval_mode})...")
        chunks = self.rag_engine.retrieve(question, mode=retrieval_mode, top_k=top_k)
        print(f"   Found {len(chunks)} relevant chunks")
        
        # 2. 转换为context格式
        contexts = [
            {
                'content': chunk.content,
                'metadata': chunk.metadata,
                'score': chunk.score
            }
            for chunk in chunks
        ]
        
        # 3. 生成回答
        print("🤖 Generating answer...")
        result = self.llm_generator.generate(question, contexts)
        
        return result
    
    def query_with_sources(
        self,
        question: str,
        retrieval_mode: str = "hybrid",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        执行RAG查询并返回完整信息
        
        Args:
            question: 用户问题
            retrieval_mode: 检索模式
            top_k: 检索结果数量
            
        Returns:
            包含回答、上下文和元数据的字典
        """
        result = self.query(question, retrieval_mode, top_k)
        
        return {
            'question': question,
            'answer': result.answer,
            'sources': [
                {
                    'content': c['content'][:300] + "..." if len(c['content']) > 300 else c['content'],
                    'source': c['metadata'].get('source', 'unknown'),
                    'score': c.get('score', 0)
                }
                for c in result.context_used
            ],
            'model': result.model,
            'tokens_used': result.tokens_used
        }
