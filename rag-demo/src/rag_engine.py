"""
RAG Engine - Core retrieval and generation logic
支持混合检索（语义+关键词）和上下文组装
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import numpy as np

# Load environment variables
load_dotenv()

@dataclass
class Chunk:
    """文档分块数据类"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float = 0.0

class RAGEngine:
    """RAG检索引擎 - 支持混合检索"""
    
    def __init__(
        self,
        embedding_model: str = None,
        chroma_db_path: str = None,
        collection_name: str = None,
        top_k: int = None,
        bm25_weight: float = None,
        semantic_weight: float = None
    ):
        """
        初始化RAG引擎
        
        Args:
            embedding_model: 嵌入模型名称
            chroma_db_path: ChromaDB存储路径
            collection_name: 集合名称
            top_k: 检索结果数量
            bm25_weight: BM25检索权重
            semantic_weight: 语义检索权重
        """
        # 配置参数
        self.embedding_model_name = embedding_model or os.getenv("EMBEDDING_MODEL", "bge-m3")
        self.chroma_db_path = chroma_db_path or os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "hermes_knowledge")
        self.top_k = top_k or int(os.getenv("TOP_K", 5))
        self.bm25_weight = bm25_weight if bm25_weight is not None else float(os.getenv("BM25_WEIGHT", 0.3))
        self.semantic_weight = semantic_weight if semantic_weight is not None else float(os.getenv("SEMANTIC_WEIGHT", 0.7))
        
        # 初始化嵌入模型
        self._init_embedding_model()
        
        # 初始化ChromaDB
        self._init_chroma()
        
        # BM25索引（运行时构建）
        self.bm25 = None
        self.bm25_chunks = []
        
    def _init_embedding_model(self):
        """初始化嵌入模型"""
        try:
            if self.embedding_model_name == "bge-m3":
                # BGE-M3 - 多语言，高性能
                model_path = "BAAI/bge-m3"
            elif self.embedding_model_name == "bge-small-zh":
                model_path = "BAAI/bge-small-zh-v1.5"
            elif self.embedding_model_name == "bge-base-en":
                model_path = "BAAI/bge-base-en-v1.5"
            else:
                model_path = self.embedding_model_name
            
            print(f"Loading embedding model: {model_path}")
            self.embedding_model = SentenceTransformer(model_path)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            print(f"Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            # Fallback to a smaller model
            print("Falling back to bge-small-en-v1.5")
            self.embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
    
    def _init_chroma(self):
        """初始化ChromaDB客户端"""
        os.makedirs(self.chroma_db_path, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"ChromaDB initialized at: {self.chroma_db_path}")
        print(f"Collection: {self.collection_name}")
        print(f"Documents count: {self.collection.count()}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        文本向量化
        
        Args:
            text: 输入文本
            
        Returns:
            向量表示
        """
        # BGE模型建议使用的指令前缀
        if self.embedding_model_name == "bge-m3":
            text = f"Represent this sentence for searching relevant passages: {text}"
        
        embedding = self.embedding_model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None
    ):
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档内容列表
            metadatas: 元数据列表
            ids: 文档ID列表
        """
        if not documents:
            return
        
        # 自动生成ID
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(documents))]
        
        # 生成嵌入向量
        print(f"Generating embeddings for {len(documents)} documents...")
        embeddings = []
        for doc in documents:
            emb = self.embed_text(doc)
            embeddings.append(emb)
        
        # 添加到ChromaDB
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in documents]
        )
        
        # 重建BM25索引
        self._rebuild_bm25_index()
        
        print(f"Added {len(documents)} documents. Total: {self.collection.count()}")
    
    def _rebuild_bm25_index(self):
        """重建BM25索引"""
        # 获取所有文档
        all_docs = self.collection.get()
        
        if not all_docs["documents"]:
            return
        
        # 分词处理
        self.bm25_chunks = []
        tokenized_docs = []
        
        for i, doc in enumerate(all_docs["documents"]):
            # 简单中文/英文分词
            tokens = self._tokenize(doc)
            tokenized_docs.append(tokens)
            
            chunk = Chunk(
                id=all_docs["ids"][i],
                content=doc,
                metadata=all_docs["metadatas"][i] if all_docs["metadatas"] else {}
            )
            self.bm25_chunks.append(chunk)
        
        # 构建BM25索引
        self.bm25 = BM25Okapi(tokenized_docs)
        print(f"BM25 index rebuilt with {len(tokenized_docs)} documents")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        简单分词 - 支持中英文
        
        Args:
            text: 输入文本
            
        Returns:
            分词结果列表
        """
        # 转小写
        text = text.lower()
        
        # 中文分词：按字符分割，过滤标点
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        
        # 英文分词：提取单词
        english_words = re.findall(r'[a-zA-Z]+', text)
        
        # 数字
        numbers = re.findall(r'\d+', text)
        
        return chinese_chars + english_words + numbers
    
    def semantic_search(self, query: str, top_k: int = None) -> List[Chunk]:
        """
        语义检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        k = top_k or self.top_k
        
        # 生成查询向量
        query_embedding = self.embed_text(query)
        
        # 向量检索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        chunks = []
        for i in range(len(results["ids"][0])):
            chunk = Chunk(
                id=results["ids"][0][i],
                content=results["documents"][0][i],
                metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                score=results["distances"][0][i] if results["distances"] else 1.0
            )
            chunks.append(chunk)
        
        return chunks
    
    def keyword_search(self, query: str, top_k: int = None) -> List[Chunk]:
        """
        关键词检索 (BM25)
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        k = top_k or self.top_k
        
        if self.bm25 is None or not self.bm25_chunks:
            return []
        
        # 分词
        query_tokens = self._tokenize(query)
        
        # BM25检索
        scores = self.bm25.get_scores(query_tokens)
        
        # 获取top-k
        top_indices = np.argsort(scores)[::-1][:k]
        
        chunks = []
        for idx in top_indices:
            if scores[idx] > 0:
                chunk = Chunk(
                    id=self.bm25_chunks[idx].id,
                    content=self.bm25_chunks[idx].content,
                    metadata=self.bm25_chunks[idx].metadata,
                    score=float(scores[idx])
                )
                chunks.append(chunk)
        
        return chunks
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = None,
        rerank: bool = True
    ) -> List[Chunk]:
        """
        混合检索 - 语义 + 关键词
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            rerank: 是否进行重排序
            
        Returns:
            融合后的检索结果列表
        """
        k = top_k or self.top_k
        
        # 获取语义检索结果
        semantic_results = self.semantic_search(query, top_k=k * 2)
        
        # 获取关键词检索结果
        keyword_results = self.keyword_search(query, top_k=k * 2)
        
        # 融合分数
        all_chunks: Dict[str, Chunk] = {}
        
        # 语义检索分数归一化 (Chroma返回的是距离，需要转换为相似度)
        if semantic_results:
            max_dist = max([c.score for c in semantic_results])
            min_dist = min([c.score for c in semantic_results])
            dist_range = max_dist - min_dist if max_dist != min_dist else 1.0
            
            for chunk in semantic_results:
                # 距离转相似度 (余弦距离 -> 余弦相似度)
                normalized_score = 1.0 - (chunk.score - min_dist) / dist_range
                chunk.score = normalized_score * self.semantic_weight
                all_chunks[chunk.id] = chunk
        
        # 关键词检索分数归一化
        if keyword_results:
            max_score = max([c.score for c in keyword_results])
            if max_score > 0:
                for chunk in keyword_results:
                    normalized_score = chunk.score / max_score
                    if chunk.id in all_chunks:
                        # 融合分数
                        all_chunks[chunk.id].score += normalized_score * self.bm25_weight
                    else:
                        chunk.score = normalized_score * self.bm25_weight
                        all_chunks[chunk.id] = chunk
        
        # 按分数排序
        sorted_chunks = sorted(all_chunks.values(), key=lambda x: x.score, reverse=True)
        
        return sorted_chunks[:k]
    
    def retrieve(self, query: str, mode: str = "hybrid", top_k: int = None) -> List[Chunk]:
        """
        统一的检索接口
        
        Args:
            query: 查询文本
            mode: 检索模式 - "semantic", "keyword", "hybrid"
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        if mode == "semantic":
            return self.semantic_search(query, top_k)
        elif mode == "keyword":
            return self.keyword_search(query, top_k)
        else:  # hybrid
            return self.hybrid_search(query, top_k)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        return {
            "total_documents": self.collection.count(),
            "embedding_model": self.embedding_model_name,
            "embedding_dimension": self.embedding_dim,
            "collection_name": self.collection_name,
            "db_path": self.chroma_db_path
        }
    
    def delete_collection(self):
        """删除当前集合"""
        try:
            self.chroma_client.delete_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' deleted")
        except Exception as e:
            print(f"Error deleting collection: {e}")
