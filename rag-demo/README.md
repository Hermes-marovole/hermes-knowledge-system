# 🔍 RAG Demo System

基于向量数据库 + Embedding模型的检索增强生成（RAG）演示系统。

## 📋 项目概述

本项目是Hermes Knowledge System Phase 3的技术验证Demo，实现了完整的RAG检索流程：

- ✅ **向量数据库**: ChromaDB（轻量、本地运行）
- ✅ **Embedding模型**: BGE-M3（多语言、高性能）
- ✅ **混合检索**: 语义检索 + BM25关键词检索
- ✅ **文档处理**: Markdown加载、智能分块
- ✅ **LLM生成**: OpenAI API支持（可选）
- ✅ **交互界面**: 命令行对话 + FastAPI Web服务

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
├──────────────────┬──────────────────┬───────────────────────┤
│   CLI Chat       │   FastAPI        │   Python API          │
│   (cli_chat.py)  │   (api_server.py)│   (rag_engine.py)     │
└──────────────────┴──────────────────┴───────────────────────┘
                            │
                    ┌───────▼───────┐
                    │   RAG Chain   │
                    │ (retrieval +  │
                    │  generation)  │
                    └───────┬───────┘
            ┌─────────────┴─────────────┐
            │                           │
    ┌───────▼───────┐       ┌──────────▼────┐
    │    Hybrid     │       │    LLM        │
    │   Retrieval   │       │  Generator    │
    └───────┬───────┘       └───────────────┘
    │       │       │
┌───▼───┐ ┌─▼───┐ ┌─▼────┐
│Chroma │ │BM25 │ │Sentence│
│  DB   │ │Index│ │Transformers│
└───────┘ └─────┘ └─────────┘
```

## 📦 安装

### 环境要求

- Python 3.9+
- macOS / Linux / Windows

### 安装依赖

```bash
# 进入项目目录
cd rag-demo

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装额外依赖（用于解析复杂Markdown）
pip install unstructured[md]
```

### 配置环境变量

```bash
cp .env.example .env

# 编辑 .env 文件（可选配置）
# 如需使用OpenAI，设置 OPENAI_API_KEY
```

## 🚀 快速开始

### 1. 文档索引

将Markdown文档索引到向量数据库：

```bash
cd src

# 索引单个文件
python index_documents.py /path/to/document.md

# 索引整个目录
python index_documents.py /Users/agent/hermes-knowledge-system/llm-wiki

# 索引并清空现有数据
python index_documents.py /Users/agent/hermes-knowledge-system/llm-wiki --clear

# 指定分块参数
python index_documents.py ../docs --chunk-size 512 --chunk-overlap 50
```

### 2. 命令行对话

启动交互式对话界面：

```bash
cd src
python cli_chat.py
```

交互命令：
- 直接输入问题开始对话
- `/quit` 或 `/q` - 退出
- `/sources` - 查看上一次检索来源
- `/mode semantic` - 切换到纯语义检索
- `/mode keyword` - 切换到纯关键词检索
- `/mode hybrid` - 切换到混合检索（默认）
- `/help` - 显示帮助

### 3. Web API服务

启动FastAPI服务：

```bash
cd src
python api_server.py
```

或使用uvicorn：
```bash
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

API端点：
- `GET /` - 服务状态
- `GET /health` - 健康检查
- `GET /stats` - 数据库统计
- `POST /retrieve` - 文档检索
- `POST /chat` - 完整对话
- `GET /search?q=query` - 简单搜索

### 4. 运行测试

执行验证测试套件：

```bash
cd src
python test_rag.py
```

测试内容包括：
- 检索准确率测试（5个典型问题）
- 生成质量测试
- 性能基准测试

## 📁 项目结构

```
rag-demo/
├── README.md                   # 项目说明
├── requirements.txt            # Python依赖
├── .env.example                # 环境变量模板
├── src/
│   ├── rag_engine.py          # RAG检索引擎核心
│   ├── document_processor.py  # 文档处理与分块
│   ├── llm_generator.py       # LLM生成模块
│   ├── cli_chat.py            # 命令行交互界面
│   ├── api_server.py          # FastAPI Web服务
│   ├── index_documents.py     # 文档批量索引脚本
│   └── test_rag.py            # 测试套件
├── data/                       # 数据目录（自动创建）
│   └── chroma_db/             # ChromaDB存储
└── docs/                       # 文档目录
```

## 🔧 核心组件说明

### RAGEngine (rag_engine.py)

核心检索引擎，支持：

- **语义检索**: 基于向量相似度（余弦距离）
- **关键词检索**: 基于BM25算法
- **混合检索**: 加权融合两种检索方式
- **可配置参数**:
  - `semantic_weight`: 语义检索权重（默认0.7）
  - `bm25_weight`: BM25权重（默认0.3）
  - `top_k`: 返回结果数量（默认5）

### DocumentProcessor (document_processor.py)

文档处理模块：

- **Markdown解析**: 提取frontmatter元数据、标题
- **智能分块**: 基于标题边界 + 滑动窗口
- **分块策略**: 支持重叠，保持上下文连贯
- **配置参数**:
  - `chunk_size`: 分块大小（默认512字符）
  - `chunk_overlap`: 重叠大小（默认50字符）

### LLMGenerator (llm_generator.py)

文本生成模块：

- **OpenAI支持**: GPT-3.5-turbo / GPT-4
- **Mock模式**: 无API密钥时使用模拟回答
- **上下文组装**: 自动构建prompt
- **流式生成**: 支持流式输出（SSE）

## ⚙️ 配置选项

环境变量（`.env`文件）：

```bash
# OpenAI配置（可选）
OPENAI_API_KEY=sk-xxx
LLM_MODEL=gpt-3.5-turbo

# Embedding配置
EMBEDDING_MODEL=bge-m3  # 可选: bge-small-zh, bge-base-en

# 数据库配置
CHROMA_DB_PATH=./data/chroma_db
COLLECTION_NAME=hermes_knowledge

# 检索配置
TOP_K=5
SEMANTIC_WEIGHT=0.7
BM25_WEIGHT=0.3

# 分块配置
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# API配置
API_HOST=127.0.0.1
API_PORT=8000
```

## 🧪 技术验证报告

运行测试后生成的报告包含：

1. **检索准确率**: 5个典型问题的精确率测试
2. **检索延迟**: 平均响应时间（毫秒）
3. **性能基准**: 多次检索的统计分布
4. **生成质量**: LLM回答示例（需配置OpenAI API）

测试报告位置：`rag-test-report.json`

## 💰 成本估算

### Embedding成本（BGE-M3）
- **本地运行**: 免费
- **首次下载**: 约500MB模型文件

### OpenAI API成本（可选）
- **Embedding**: text-embedding-3-small 约 $0.02/1M tokens
- **Chat**: GPT-3.5-turbo 约 $0.002/1K tokens

### 本地运行成本
- **总成本**: 免费（仅需计算资源）
- **内存占用**: 约1-2GB（模型加载后）
- **磁盘占用**: 约500MB（模型）+ 文档向量化存储

## 🔍 检索模式对比

| 模式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| Semantic | 理解语义，容错性强 | 计算成本高 | 概念性问题 |
| Keyword | 精确匹配，速度快 | 无法理解同义词 | 精确查找 |
| Hybrid | 两者结合，效果好 | 需要调参 | 通用场景（推荐） |

## 🐛 常见问题

### 1. 首次运行下载模型慢
```bash
# 手动下载模型到缓存
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
```

### 2. ChromaDB权限错误
```bash
# 删除旧数据库重新创建
rm -rf ./data/chroma_db
python index_documents.py /path/to/docs --clear
```

### 3. 内存不足
```bash
# 使用更小的模型
export EMBEDDING_MODEL=bge-small-zh
```

### 4. 检索结果不理想
```bash
# 调整分块大小
python index_documents.py /path/to/docs --chunk-size 256 --chunk-overlap 25

# 调整检索权重（修改.env）
SEMANTIC_WEIGHT=0.6
BM25_WEIGHT=0.4
```

## 📊 性能参考

在 MacBook Pro M3 / 16GB 环境下的测试结果：

| 指标 | 数值 |
|------|------|
| 平均检索延迟 | ~150-300ms |
| 平均生成延迟（Mock）| ~10ms |
| 平均生成延迟（GPT-3.5）| ~1000-2000ms |
| 1000文档索引时间 | ~2-5分钟 |
| 内存占用 | ~1.5GB |

## 🔗 相关链接

- [Sentence Transformers](https://www.sbert.net/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [BGE-M3 Paper](https://arxiv.org/abs/2402.03216)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)

## 📄 License

MIT License - 详见父项目 Hermes Knowledge System

## 🤝 Contributing

欢迎提交Issue和PR！
