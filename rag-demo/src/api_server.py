"""
FastAPI Web服务 - 提供RAG检索API接口
"""

import os
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_engine import RAGEngine, Chunk
from llm_generator import LLMGenerator, SimpleRAGChain, GenerationResult


# 全局实例
rag_engine: Optional[RAGEngine] = None
rag_chain: Optional[SimpleRAGChain] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global rag_engine, rag_chain
    
    # 启动时初始化
    print("🚀 Initializing RAG Engine...")
    db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    rag_engine = RAGEngine(chroma_db_path=db_path)
    
    llm_generator = LLMGenerator()
    rag_chain = SimpleRAGChain(rag_engine, llm_generator)
    
    stats = rag_engine.get_collection_stats()
    print(f"✅ RAG Engine ready: {stats['total_documents']} documents")
    
    yield
    
    # 关闭时清理
    print("👋 Shutting down...")


# 创建FastAPI应用
app = FastAPI(
    title="RAG Demo API",
    description="Hermes Knowledge System - RAG Retrieval API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 数据模型 =====

class RetrieveRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., description="查询文本")
    mode: str = Field("hybrid", description="检索模式: semantic/keyword/hybrid")
    top_k: int = Field(5, description="返回结果数量", ge=1, le=20)


class RetrieveResponse(BaseModel):
    """检索响应"""
    query: str
    mode: str
    results: List[Dict[str, Any]]
    total_found: int


class ChatRequest(BaseModel):
    """对话请求"""
    question: str = Field(..., description="用户问题")
    retrieval_mode: str = Field("hybrid", description="检索模式")
    top_k: int = Field(5, description="检索数量", ge=1, le=20)


class ChatResponse(BaseModel):
    """对话响应"""
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    model: str
    tokens_used: int


class StatsResponse(BaseModel):
    """统计信息响应"""
    total_documents: int
    embedding_model: str
    embedding_dimension: int
    collection_name: str
    db_path: str


# ===== API端点 =====

@app.get("/", tags=["Health"])
async def root():
    """根路径 - 服务状态"""
    return {
        "service": "RAG Demo API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查"""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")
    
    stats = rag_engine.get_collection_stats()
    return {
        "status": "healthy",
        "documents": stats["total_documents"],
        "model": stats["embedding_model"]
    }


@app.get("/stats", response_model=StatsResponse, tags=["Stats"])
async def get_stats():
    """获取向量数据库统计信息"""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")
    
    stats = rag_engine.get_collection_stats()
    return StatsResponse(**stats)


@app.post("/retrieve", response_model=RetrieveResponse, tags=["Retrieval"])
async def retrieve(request: RetrieveRequest):
    """
    文档检索接口
    
    支持三种检索模式：
    - **semantic**: 纯语义检索（向量相似度）
    - **keyword**: 纯关键词检索（BM25）
    - **hybrid**: 混合检索（默认，融合两种方法）
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")
    
    try:
        chunks = rag_engine.retrieve(
            query=request.query,
            mode=request.mode,
            top_k=request.top_k
        )
        
        results = [
            {
                "id": chunk.id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "score": round(chunk.score, 4)
            }
            for chunk in chunks
        ]
        
        return RetrieveResponse(
            query=request.query,
            mode=request.mode,
            results=results,
            total_found=len(results)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    对话接口 - 完整的RAG流程
    
    执行检索+生成的完整流程，返回答案和来源
    """
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG Chain not initialized")
    
    try:
        result = rag_chain.query_with_sources(
            question=request.question,
            retrieval_mode=request.retrieval_mode,
            top_k=request.top_k
        )
        
        return ChatResponse(
            question=result["question"],
            answer=result["answer"],
            sources=result["sources"],
            model=result["model"],
            tokens_used=result["tokens_used"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search", tags=["Retrieval"])
async def simple_search(
    q: str = Query(..., description="Search query"),
    mode: str = Query("hybrid", description="Search mode"),
    top_k: int = Query(5, description="Number of results", ge=1, le=20)
):
    """
    简单搜索接口（GET方法）
    
    便于浏览器直接测试: /search?q=your+query
    """
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")
    
    try:
        chunks = rag_engine.retrieve(query=q, mode=mode, top_k=top_k)
        
        results = [
            {
                "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "source": chunk.metadata.get("source", "unknown"),
                "score": round(chunk.score, 4)
            }
            for chunk in chunks
        ]
        
        return {
            "query": q,
            "mode": mode,
            "count": len(results),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== 启动命令 =====
# uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"🌐 Starting API server at http://{host}:{port}")
    print(f"📚 API docs: http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)
