"""
文档处理模块 - 加载、解析、分块
支持Markdown文档和多种格式
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Document:
    """文档数据类"""
    content: str
    metadata: Dict[str, Any]
    source: str

class DocumentProcessor:
    """文档处理器 - 支持多种文档格式"""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        """
        初始化文档处理器
        
        Args:
            chunk_size: 分块大小（字符数）
            chunk_overlap: 分块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load_markdown(self, file_path: str) -> Document:
        """
        加载Markdown文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Document对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取元数据（YAML frontmatter）
        metadata = self._extract_frontmatter(content)
        
        # 提取标题
        title = self._extract_title(content)
        if title:
            metadata['title'] = title
        
        metadata['source'] = file_path
        metadata['filename'] = os.path.basename(file_path)
        
        # 移除frontmatter后的内容
        content = self._remove_frontmatter(content)
        
        return Document(
            content=content,
            metadata=metadata,
            source=file_path
        )
    
    def load_directory(
        self,
        dir_path: str,
        pattern: str = "*.md",
        recursive: bool = True
    ) -> List[Document]:
        """
        加载目录下的所有Markdown文件
        
        Args:
            dir_path: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归子目录
            
        Returns:
            Document列表
        """
        documents = []
        path = Path(dir_path)
        
        if recursive:
            files = path.rglob(pattern)
        else:
            files = path.glob(pattern)
        
        for file_path in files:
            if file_path.is_file():
                try:
                    doc = self.load_markdown(str(file_path))
                    documents.append(doc)
                    print(f"Loaded: {file_path}")
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        return documents
    
    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """提取YAML frontmatter"""
        metadata = {}
        
        # 匹配YAML frontmatter
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            frontmatter = match.group(1)
            # 简单解析key: value格式
            for line in frontmatter.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip().strip('"\'')
        
        return metadata
    
    def _remove_frontmatter(self, content: str) -> str:
        """移除YAML frontmatter"""
        pattern = r'^---\s*\n.*?\n---\s*\n'
        return re.sub(pattern, '', content, flags=re.DOTALL, count=1).strip()
    
    def _extract_title(self, content: str) -> Optional[str]:
        """提取文档标题（第一个#标题）"""
        # 移除frontmatter
        content = self._remove_frontmatter(content)
        
        # 匹配第一个#标题
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def chunk_document(self, document: Document) -> List[Dict[str, Any]]:
        """
        文档分块 - 基于段落和语义边界
        
        Args:
            document: Document对象
            
        Returns:
            分块列表，每个块包含content和metadata
        """
        content = document.content
        
        # 按标题分割（Markdown标题作为自然边界）
        sections = self._split_by_headers(content)
        
        chunks = []
        chunk_id = 0
        
        for section in sections:
            section_content = section['content']
            section_header = section['header']
            
            # 如果section太大，进一步分割
            if len(section_content) > self.chunk_size:
                sub_chunks = self._chunk_text(section_content)
                for sub_chunk in sub_chunks:
                    chunk_metadata = document.metadata.copy()
                    chunk_metadata.update({
                        'section': section_header,
                        'chunk_id': chunk_id,
                        'chunk_index': len(chunks)
                    })
                    
                    chunks.append({
                        'content': sub_chunk,
                        'metadata': chunk_metadata
                    })
                    chunk_id += 1
            else:
                # Section大小合适，直接作为一个chunk
                chunk_metadata = document.metadata.copy()
                chunk_metadata.update({
                    'section': section_header,
                    'chunk_id': chunk_id,
                    'chunk_index': len(chunks)
                })
                
                chunks.append({
                    'content': section_content,
                    'metadata': chunk_metadata
                })
                chunk_id += 1
        
        return chunks
    
    def _split_by_headers(self, content: str) -> List[Dict[str, str]]:
        """按Markdown标题分割文档"""
        # 匹配各级标题
        header_pattern = r'^(#{1,3}\s+.+)$'
        
        lines = content.split('\n')
        sections = []
        current_header = "Introduction"
        current_content = []
        
        for line in lines:
            header_match = re.match(header_pattern, line)
            
            if header_match:
                # 保存上一个section
                if current_content:
                    sections.append({
                        'header': current_header,
                        'content': '\n'.join(current_content).strip()
                    })
                
                current_header = line.strip()
                current_content = [line]
            else:
                current_content.append(line)
        
        # 保存最后一个section
        if current_content:
            sections.append({
                'header': current_header,
                'content': '\n'.join(current_content).strip()
            })
        
        # 过滤空section
        sections = [s for s in sections if s['content'].strip()]
        
        return sections if sections else [{'header': 'Content', 'content': content}]
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        文本分块 - 滑动窗口
        
        Args:
            text: 输入文本
            
        Returns:
            分块列表
        """
        chunks = []
        start = 0
        
        while start < len(text):
            # 计算结束位置
            end = start + self.chunk_size
            
            if end >= len(text):
                # 最后一个块
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break
            
            # 尝试在句子边界分割
            chunk_text = text[start:end]
            
            # 向后查找句子边界
            sentence_end = self._find_sentence_boundary(text, end)
            if sentence_end > end:
                end = sentence_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 移动窗口（考虑重叠）
            start = end - self.chunk_overlap
            if start <= 0:
                start = end
        
        return chunks
    
    def _find_sentence_boundary(self, text: str, start_pos: int) -> int:
        """
        查找句子边界
        
        Args:
            text: 文本内容
            start_pos: 开始搜索位置
            
        Returns:
            句子结束位置
        """
        max_search = min(start_pos + 100, len(text))
        
        for i in range(start_pos, max_search):
            if i < len(text) and text[i] in '.。!！?？':
                # 检查是否是缩写（如Mr. Dr.等）
                if i + 1 < len(text) and text[i + 1] in ' \n':
                    return i + 1
        
        return start_pos
    
    def process_documents(
        self,
        documents: List[Document],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量处理文档
        
        Args:
            documents: Document列表
            show_progress: 是否显示进度
            
        Returns:
            所有分块列表
        """
        all_chunks = []
        
        for i, doc in enumerate(documents):
            if show_progress:
                print(f"Processing document {i+1}/{len(documents)}: {doc.metadata.get('filename', 'unknown')}")
            
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
            
            if show_progress:
                print(f"  -> {len(chunks)} chunks")
        
        if show_progress:
            print(f"\nTotal chunks: {len(all_chunks)}")
        
        return all_chunks
    
    def load_text_file(self, file_path: str) -> Document:
        """
        加载纯文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Document对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return Document(
            content=content,
            metadata={
                'source': file_path,
                'filename': os.path.basename(file_path),
                'type': 'text'
            },
            source=file_path
        )


class SimpleMarkdownChunker:
    """简单的Markdown分块器 - 仅按字符数分块"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, text: str, source: str = "") -> List[Dict[str, Any]]:
        """简单分块"""
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    'content': chunk_text,
                    'metadata': {
                        'source': source,
                        'chunk_id': chunk_id
                    }
                })
                chunk_id += 1
            
            start = end
            if start < len(text):
                start = max(start - self.chunk_overlap, start)
        
        return chunks
