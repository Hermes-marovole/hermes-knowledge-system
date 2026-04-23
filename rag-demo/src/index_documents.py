"""
文档批量索引脚本
用于将文档批量添加到向量数据库
"""

import os
import sys
import argparse
from pathlib import Path

from rag_engine import RAGEngine
from document_processor import DocumentProcessor


def index_documents(
    docs_path: str,
    db_path: str = "./data/chroma_db",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    collection_name: str = "hermes_knowledge",
    clear_existing: bool = False,
    file_pattern: str = "*.md"
):
    """
    索引文档到向量数据库
    
    Args:
        docs_path: 文档目录路径
        db_path: 数据库路径
        chunk_size: 分块大小
        chunk_overlap: 分块重叠
        collection_name: 集合名称
        clear_existing: 是否清空现有数据
        file_pattern: 文件匹配模式
    """
    print("="*60)
    print("📚 RAG Document Indexing")
    print("="*60)
    
    # 初始化RAG引擎
    print(f"\n📦 Initializing RAG Engine...")
    print(f"   DB Path: {db_path}")
    print(f"   Collection: {collection_name}")
    
    rag_engine = RAGEngine(
        chroma_db_path=db_path,
        collection_name=collection_name
    )
    
    # 清空现有数据（如果需要）
    if clear_existing:
        print("\n🗑️ Clearing existing collection...")
        rag_engine.delete_collection()
        # 重新初始化
        rag_engine = RAGEngine(
            chroma_db_path=db_path,
            collection_name=collection_name
        )
    
    # 显示当前统计
    stats = rag_engine.get_collection_stats()
    print(f"\n📊 Current database: {stats['total_documents']} documents")
    
    # 初始化文档处理器
    processor = DocumentProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    # 检查路径
    docs_path = Path(docs_path)
    if not docs_path.exists():
        print(f"\n❌ Error: Path does not exist: {docs_path}")
        return False
    
    print(f"\n📂 Loading documents from: {docs_path}")
    print(f"   Pattern: {file_pattern}")
    
    # 加载文档
    if docs_path.is_file():
        # 单个文件
        documents = [processor.load_markdown(str(docs_path))]
    else:
        # 目录
        documents = processor.load_directory(
            str(docs_path),
            pattern=file_pattern,
            recursive=True
        )
    
    if not documents:
        print("\n⚠️ No documents found!")
        return False
    
    print(f"\n📄 Found {len(documents)} documents")
    
    # 显示文档列表
    for i, doc in enumerate(documents, 1):
        filename = doc.metadata.get('filename', 'unknown')
        title = doc.metadata.get('title', 'N/A')
        print(f"   {i}. {filename} - {title}")
    
    # 处理分块
    print(f"\n✂️ Chunking documents (size: {chunk_size}, overlap: {chunk_overlap})...")
    chunks = processor.process_documents(documents, show_progress=True)
    
    # 准备数据
    documents_list = [c['content'] for c in chunks]
    metadatas_list = [c['metadata'] for c in chunks]
    
    # 添加到RAG
    print("\n📊 Adding to vector database...")
    rag_engine.add_documents(documents_list, metadatas_list)
    
    # 显示最终统计
    final_stats = rag_engine.get_collection_stats()
    print("\n" + "="*60)
    print("✅ Indexing Complete!")
    print("="*60)
    print(f"\n📈 Final Statistics:")
    print(f"   Total documents: {final_stats['total_documents']}")
    print(f"   Embedding model: {final_stats['embedding_model']}")
    print(f"   Embedding dimension: {final_stats['embedding_dimension']}")
    print(f"   Database path: {final_stats['db_path']}")
    
    return True


def test_retrieval(db_path: str, collection_name: str = "hermes_knowledge"):
    """测试检索功能"""
    print("\n🧪 Testing retrieval...")
    
    rag_engine = RAGEngine(
        chroma_db_path=db_path,
        collection_name=collection_name
    )
    
    test_queries = [
        "什么是RAG系统",
        "向量数据库",
        "embedding模型",
        "如何构建知识库"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = rag_engine.hybrid_search(query, top_k=3)
        
        if results:
            for i, chunk in enumerate(results, 1):
                source = chunk.metadata.get('source', 'unknown')
                filename = source.split('/')[-1] if '/' in source else source
                print(f"   {i}. [{filename}] score: {chunk.score:.3f}")
        else:
            print("   No results found")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Index documents to RAG vector database"
    )
    parser.add_argument(
        "docs_path",
        type=str,
        help="Path to documents or directory"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/chroma_db",
        help="Path to ChromaDB storage"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Document chunk size (default: 512)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Chunk overlap size (default: 50)"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="hermes_knowledge",
        help="Collection name (default: hermes_knowledge)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing collection before indexing"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.md",
        help="File pattern to match (default: *.md)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run retrieval test after indexing"
    )
    
    args = parser.parse_args()
    
    # 执行索引
    success = index_documents(
        docs_path=args.docs_path,
        db_path=args.db_path,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        collection_name=args.collection,
        clear_existing=args.clear,
        file_pattern=args.pattern
    )
    
    if success and args.test:
        test_retrieval(args.db_path, args.collection)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
