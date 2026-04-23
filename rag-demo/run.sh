#!/bin/bash
#
# RAG Demo System - Quick Start Script
# Usage: ./run.sh [command]
# Commands:
#   index   - Index documents
#   chat    - Start CLI chat
#   api     - Start API server
#   test    - Run tests
#   help    - Show help
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
DATA_DIR="$SCRIPT_DIR/data"
DOCS_DIR="/Users/agent/hermes-knowledge-system/llm-wiki"

# Python command
PYTHON="${PYTHON:-python3}"

echo -e "${BLUE}🚀 RAG Demo System${NC}"
echo "===================="

# Check if src directory exists
if [ ! -d "$SRC_DIR" ]; then
    echo -e "${YELLOW}⚠️ Error: src directory not found at $SRC_DIR${NC}"
    exit 1
fi

# Function to show help
show_help() {
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  index [path]  - Index documents (default: $DOCS_DIR)"
    echo "  chat          - Start interactive CLI chat"
    echo "  api           - Start API server (port 8000)"
    echo "  test          - Run validation tests"
    echo "  quickstart    - Index docs and start chat"
    echo "  setup         - Install dependencies"
    echo "  help          - Show this help"
    echo ""
    echo "Examples:"
    echo "  ./run.sh index                    # Index default docs"
    echo "  ./run.sh index /path/to/docs      # Index custom docs"
    echo "  ./run.sh chat                     # Start chat"
    echo "  ./run.sh quickstart               # Full demo"
    echo ""
}

# Function to setup
setup() {
    echo -e "${GREEN}📦 Installing dependencies...${NC}"
    pip install -r "$SCRIPT_DIR/requirements.txt"
    echo -e "${GREEN}✅ Setup complete!${NC}"
}

# Function to index documents
index_docs() {
    local docs_path="${1:-$DOCS_DIR}"
    echo -e "${GREEN}📚 Indexing documents from: $docs_path${NC}"
    cd "$SRC_DIR"
    $PYTHON index_documents.py "$docs_path" --clear --test
    cd "$SCRIPT_DIR"
}

# Function to start chat
start_chat() {
    echo -e "${GREEN}💬 Starting CLI chat...${NC}"
    cd "$SRC_DIR"
    $PYTHON cli_chat.py
}

# Function to start API
start_api() {
    echo -e "${GREEN}🌐 Starting API server...${NC}"
    echo "API docs will be available at: http://localhost:8000/docs"
    cd "$SRC_DIR"
    $PYTHON api_server.py
}

# Function to run tests
run_tests() {
    echo -e "${GREEN}🧪 Running tests...${NC}"
    cd "$SRC_DIR"
    $PYTHON test_rag.py
}

# Main command handler
case "${1:-help}" in
    index)
        index_docs "$2"
        ;;
    chat)
        start_chat
        ;;
    api)
        start_api
        ;;
    test)
        run_tests
        ;;
    quickstart)
        echo -e "${GREEN}⚡ Quickstart mode${NC}"
        index_docs
        echo ""
        start_chat
        ;;
    setup)
        setup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${YELLOW}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
