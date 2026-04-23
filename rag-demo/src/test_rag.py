"""
RAG系统测试脚本
包含准确率测试、延迟测试等
"""

import os
import time
import json
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from rag_engine import RAGEngine
from llm_generator import LLMGenerator, SimpleRAGChain


@dataclass
class TestResult:
    """测试结果"""
    query: str
    expected_keywords: List[str]
    retrieved_count: int
    relevant_count: int
    precision: float
    latency_ms: float
    top_sources: List[str]
    

class RAGTester:
    """RAG测试器"""
    
    def __init__(self, rag_engine: RAGEngine, rag_chain: SimpleRAGChain):
        self.rag_engine = rag_engine
        self.rag_chain = rag_chain
    
    def test_retrieval_accuracy(
        self,
        test_cases: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[TestResult]:
        """
        测试检索准确率
        
        Args:
            test_cases: 测试用例列表
            top_k: 检索数量
            
        Returns:
            测试结果列表
        """
        results = []
        
        print("\n" + "="*60)
        print("🧪 Testing Retrieval Accuracy")
        print("="*60)
        
        for i, case in enumerate(test_cases, 1):
            query = case['query']
            expected_keywords = case.get('expected_keywords', [])
            expected_sources = case.get('expected_sources', [])
            
            print(f"\n[{i}] Query: '{query}'")
            
            # 执行检索并计时
            start_time = time.time()
            chunks = self.rag_engine.hybrid_search(query, top_k=top_k)
            latency = (time.time() - start_time) * 1000  # ms
            
            # 分析结果相关性
            relevant_count = 0
            top_sources = []
            
            for chunk in chunks:
                content = chunk.content.lower()
                source = chunk.metadata.get('source', '')
                
                # 检查关键词匹配
                keyword_match = any(
                    kw.lower() in content or kw.lower() in source.lower()
                    for kw in expected_keywords
                )
                
                # 检查来源匹配
                source_match = any(
                    exp_src.lower() in source.lower()
                    for exp_src in expected_sources
                )
                
                if keyword_match or source_match:
                    relevant_count += 1
                
                top_sources.append(source.split('/')[-1] if '/' in source else source)
            
            # 计算精确率
            precision = relevant_count / len(chunks) if chunks else 0
            
            result = TestResult(
                query=query,
                expected_keywords=expected_keywords,
                retrieved_count=len(chunks),
                relevant_count=relevant_count,
                precision=precision,
                latency_ms=round(latency, 2),
                top_sources=top_sources[:3]
            )
            
            results.append(result)
            
            # 打印结果
            status = "✅" if precision >= 0.6 else "⚠️"
            print(f"    {status} Precision: {precision:.2f} ({relevant_count}/{len(chunks)})")
            print(f"    ⏱️ Latency: {latency:.2f}ms")
            print(f"    📚 Top sources: {', '.join(top_sources[:2])}")
        
        return results
    
    def test_generation_quality(
        self,
        test_queries: List[str]
    ) -> List[Dict[str, Any]]:
        """
        测试生成质量
        
        Args:
            test_queries: 查询列表
            
        Returns:
            生成结果列表
        """
        results = []
        
        print("\n" + "="*60)
        print("🤖 Testing Generation Quality")
        print("="*60)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n[{i}] Query: '{query}'")
            
            start_time = time.time()
            result = self.rag_chain.query_with_sources(query, top_k=5)
            latency = (time.time() - start_time) * 1000
            
            results.append({
                'query': query,
                'answer': result['answer'][:200] + "...",
                'model': result['model'],
                'tokens': result['tokens_used'],
                'latency_ms': round(latency, 2)
            })
            
            print(f"    Model: {result['model']}")
            print(f"    Tokens: {result['tokens_used']}")
            print(f"    ⏱️ Total latency: {latency:.2f}ms")
            print(f"    📝 Answer preview: {result['answer'][:150]}...")
        
        return results
    
    def run_benchmark(
        self,
        iterations: int = 10,
        test_query: str = "RAG系统架构"
    ) -> Dict[str, float]:
        """
        性能基准测试
        
        Args:
            iterations: 测试次数
            test_query: 测试查询
            
        Returns:
            性能统计
        """
        print("\n" + "="*60)
        print("⚡ Running Performance Benchmark")
        print("="*60)
        
        latencies = []
        
        # 预热
        print("\n🔄 Warming up...")
        for _ in range(3):
            self.rag_engine.hybrid_search(test_query, top_k=5)
        
        # 正式测试
        print(f"\n🔄 Running {iterations} iterations...")
        for i in range(iterations):
            start = time.time()
            chunks = self.rag_engine.hybrid_search(test_query, top_k=5)
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            print(f"   Iteration {i+1}: {latency:.2f}ms ({len(chunks)} chunks)")
        
        # 计算统计
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print(f"\n📊 Results:")
        print(f"   Average: {avg_latency:.2f}ms")
        print(f"   Min: {min_latency:.2f}ms")
        print(f"   Max: {max_latency:.2f}ms")
        
        return {
            'avg_latency_ms': round(avg_latency, 2),
            'min_latency_ms': round(min_latency, 2),
            'max_latency_ms': round(max_latency, 2),
            'iterations': iterations
        }


def run_tests(db_path: str = "./data/chroma_db"):
    """运行完整测试套件"""
    print("\n" + "="*60)
    print("🚀 RAG System Test Suite")
    print("="*60)
    
    # 初始化组件
    print("\n📦 Initializing RAG Engine...")
    rag_engine = RAGEngine(chroma_db_path=db_path)
    
    stats = rag_engine.get_collection_stats()
    print(f"   Database: {stats['total_documents']} documents")
    
    if stats['total_documents'] == 0:
        print("\n❌ Error: Database is empty. Please run index_documents.py first.")
        return None
    
    print("\n🤖 Initializing LLM Generator...")
    llm_generator = LLMGenerator()
    
    rag_chain = SimpleRAGChain(rag_engine, llm_generator)
    
    # 创建测试器
    tester = RAGTester(rag_engine, rag_chain)
    
    # 定义测试用例（基于hermes-knowledge-system的文档内容）
    retrieval_test_cases = [
        {
            'query': '什么是益生菌？它有什么作用？',
            'expected_keywords': ['益生菌', 'probiotics', '肠道', '菌株', '健康'],
            'expected_sources': ['akk-probiotics.md']
        },
        {
            'query': '镁补充剂有哪些类型？',
            'expected_keywords': ['镁', 'magnesium', '补充剂', '甘氨酸镁', '柠檬酸'],
            'expected_sources': ['magnesium-supplements.md']
        },
        {
            'query': '如何构建RAG检索系统',
            'expected_keywords': ['RAG', '检索', '向量', 'embedding', '知识库'],
            'expected_sources': ['ai-architecture.md']
        },
        {
            'query': '向量数据库有什么选型建议',
            'expected_keywords': ['向量数据库', 'Chroma', 'Qdrant', 'Milvus', '选型'],
            'expected_sources': ['ai-architecture.md']
        },
        {
            'query': 'Embedding模型如何选择',
            'expected_keywords': ['Embedding', 'BGE', 'M3', 'text-embedding', '模型'],
            'expected_sources': ['ai-architecture.md']
        }
    ]
    
    # 运行检索准确率测试
    retrieval_results = tester.test_retrieval_accuracy(retrieval_test_cases, top_k=5)
    
    # 运行生成质量测试
    generation_queries = [
        "RAG系统的主要组件有哪些？",
        "向量数据库和Embedding模型有什么关系？",
        "如何评估RAG系统的性能？"
    ]
    generation_results = tester.test_generation_quality(generation_queries)
    
    # 运行性能基准测试
    benchmark_results = tester.run_benchmark(iterations=10)
    
    # 汇总结果
    avg_precision = sum(r.precision for r in retrieval_results) / len(retrieval_results)
    avg_latency = sum(r.latency_ms for r in retrieval_results) / len(retrieval_results)
    
    summary = {
        'retrieval_tests': [asdict(r) for r in retrieval_results],
        'generation_tests': generation_results,
        'benchmark': benchmark_results,
        'summary': {
            'avg_precision': round(avg_precision, 2),
            'avg_retrieval_latency_ms': round(avg_latency, 2),
            'total_documents': stats['total_documents'],
            'embedding_model': stats['embedding_model'],
            'embedding_dimension': stats['embedding_dimension']
        }
    }
    
    # 保存测试报告
    report_path = "../rag-test-report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # 打印总结
    print("\n" + "="*60)
    print("📋 Test Summary")
    print("="*60)
    print(f"\n✅ Average Retrieval Precision: {avg_precision:.2f}")
    print(f"⏱️ Average Retrieval Latency: {avg_latency:.2f}ms")
    print(f"📚 Total Documents Indexed: {stats['total_documents']}")
    print(f"🔤 Embedding Model: {stats['embedding_model']}")
    print(f"\n📝 Full report saved to: {report_path}")
    
    return summary


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RAG System")
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/chroma_db",
        help="Path to ChromaDB storage"
    )
    
    args = parser.parse_args()
    
    run_tests(args.db_path)


if __name__ == "__main__":
    main()
