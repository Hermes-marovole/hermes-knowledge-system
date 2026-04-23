"""
命令行交互式对话界面
"""

import sys
import argparse
from typing import Optional

from rag_engine import RAGEngine
from document_processor import DocumentProcessor
from llm_generator import LLMGenerator, SimpleRAGChain


class InteractiveChat:
    """交互式命令行对话"""
    
    def __init__(self, rag_chain: SimpleRAGChain):
        """
        初始化交互式对话
        
        Args:
            rag_chain: RAG链实例
        """
        self.rag_chain = rag_chain
        self.history = []
        
    def start(self):
        """启动交互式对话"""
        print("\n" + "="*60)
        print("🤖 RAG Demo - Interactive Chat")
        print("="*60)
        print("\n可用命令:")
        print("  /quit, /q  - 退出")
        print("  /help, /h  - 显示帮助")
        print("  /sources   - 显示上一次的检索来源")
        print("  /mode      - 切换检索模式 (semantic/keyword/hybrid)")
        print("  /clear     - 清空对话历史")
        print("\n输入你的问题开始对话...\n")
        
        current_mode = "hybrid"
        last_result = None
        
        while True:
            try:
                # 获取用户输入
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.lower() in ['/quit', '/q', 'exit', 'quit']:
                    print("\n👋 Goodbye!")
                    break
                
                if user_input.lower() in ['/help', '/h', 'help']:
                    self._show_help()
                    continue
                
                if user_input.lower() == '/clear':
                    self.history.clear()
                    print("\n🧹 History cleared.\n")
                    continue
                
                if user_input.lower() == '/sources':
                    if last_result:
                        self._show_sources(last_result)
                    else:
                        print("\n⚠️ No previous query to show sources.\n")
                    continue
                
                if user_input.lower().startswith('/mode'):
                    parts = user_input.split()
                    if len(parts) > 1:
                        mode = parts[1].lower()
                        if mode in ['semantic', 'keyword', 'hybrid']:
                            current_mode = mode
                            print(f"\n🔄 Retrieval mode set to: {current_mode}\n")
                        else:
                            print(f"\n⚠️ Invalid mode. Available: semantic, keyword, hybrid\n")
                    else:
                        print(f"\n📍 Current mode: {current_mode}\n")
                    continue
                
                # 处理问题
                print(f"\n🤔 Processing (mode: {current_mode})...")
                
                result = self.rag_chain.query_with_sources(
                    question=user_input,
                    retrieval_mode=current_mode,
                    top_k=5
                )
                
                last_result = result
                
                # 显示回答
                print(f"\n🤖 Assistant: {result['answer']}\n")
                
                # 显示来源信息（可选）
                if result['sources']:
                    print(f"📚 Sources ({len(result['sources'])} chunks retrieved)")
                    for i, src in enumerate(result['sources'], 1):
                        filename = src['source'].split('/')[-1] if '/' in src['source'] else src['source']
                        print(f"   {i}. [{filename}] score: {src['score']:.3f}")
                    print()
                
                # 保存历史
                self.history.append({
                    'question': user_input,
                    'answer': result['answer']
                })
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
    
    def _show_help(self):
        """显示帮助信息"""
        print("""
┌─────────────────────────────────────────────────────────────┐
│                       Command Help                          │
├─────────────────────────────────────────────────────────────┤
│  /quit, /q      - Exit the chat                             │
│  /help, /h      - Show this help message                    │
│  /sources       - Show sources from last query              │
│  /mode [name]   - Set retrieval mode:                       │
│                   • semantic - Semantic search only         │
│                   • keyword  - Keyword search only          │
│                   • hybrid   - Combined (default)            │
│  /clear         - Clear conversation history                │
└─────────────────────────────────────────────────────────────┘
""")
    
    def _show_sources(self, result: dict):
        """显示检索来源详情"""
        print("\n" + "="*60)
        print("📚 Retrieved Sources (detailed)")
        print("="*60)
        
        for i, src in enumerate(result['sources'], 1):
            print(f"\n[{i}] Score: {src['score']:.3f}")
            print(f"    Source: {src['source']}")
            print(f"    Content: {src['content'][:400]}...")
        
        print("\n" + "="*60 + "\n")


def load_documents_to_rag(
    rag_engine: RAGEngine,
    docs_path: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50
):
    """
    加载文档到RAG系统
    
    Args:
        rag_engine: RAG引擎实例
        docs_path: 文档目录路径
        chunk_size: 分块大小
        chunk_overlap: 分块重叠
    """
    print(f"\n📂 Loading documents from: {docs_path}")
    
    # 初始化文档处理器
    processor = DocumentProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    # 加载文档
    documents = processor.load_directory(docs_path, pattern="*.md", recursive=True)
    
    if not documents:
        print("⚠️ No Markdown documents found!")
        return False
    
    print(f"\n📄 Loaded {len(documents)} documents")
    
    # 处理分块
    chunks = processor.process_documents(documents, show_progress=True)
    
    # 添加到RAG
    print("\n📊 Adding to vector database...")
    
    documents_list = [c['content'] for c in chunks]
    metadatas_list = [c['metadata'] for c in chunks]
    
    rag_engine.add_documents(documents_list, metadatas_list)
    
    print(f"✅ Successfully indexed {len(chunks)} chunks")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RAG Demo CLI Chat")
    parser.add_argument(
        "--docs",
        type=str,
        default="/Users/agent/hermes-knowledge-system/llm-wiki",
        help="Path to documents directory"
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
        help="Document chunk size"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Chunk overlap size"
    )
    parser.add_argument(
        "--skip-indexing",
        action="store_true",
        help="Skip document indexing (use existing DB)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="hybrid",
        choices=["semantic", "keyword", "hybrid"],
        help="Default retrieval mode"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("🚀 RAG Demo System - Starting...")
    print("="*60)
    
    # 初始化RAG引擎
    print("\n📦 Initializing RAG Engine...")
    rag_engine = RAGEngine(chroma_db_path=args.db_path)
    
    # 加载文档
    if not args.skip_indexing:
        success = load_documents_to_rag(
            rag_engine=rag_engine,
            docs_path=args.docs,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )
        
        if not success:
            print("\n⚠️ Document loading failed. Check the path and try again.")
            return
    else:
        print("\n⏭️ Skipping indexing - using existing database")
        stats = rag_engine.get_collection_stats()
        print(f"   Database contains {stats['total_documents']} documents")
    
    # 初始化LLM生成器
    print("\n🤖 Initializing LLM Generator...")
    llm_generator = LLMGenerator()
    
    # 创建RAG链
    rag_chain = SimpleRAGChain(rag_engine, llm_generator)
    
    # 启动交互式对话
    chat = InteractiveChat(rag_chain)
    chat.start()


if __name__ == "__main__":
    main()
