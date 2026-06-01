"""
================================================================================
RAG 工具 — 本地知识库检索（阿里云 DashScope Embedding API 版）
================================================================================

优势：
- 不下载 400MB 本地模型，无需等待加载
- 复用已有的 DashScope API Key（和 qwen-plus 同一个）
- 每次查询只需一次 API 调用，秒级响应

首次使用时会自动从 docs/company_docs.txt 构建向量库（调用 Embedding API），
之后持久化到 chroma_db/，重启后直接加载（秒级）。
"""

import os
import json
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from core.config import settings

PERSIST_DIRECTORY = "./chroma_db"
DOC_PATH = "./docs/company_docs.txt"
VERSION_FILE = os.path.join(PERSIST_DIRECTORY, ".embedding_version")

# 当前使用的 Embedding 模型标识（换了模型就自动重建）
CURRENT_EMBEDDING_MODEL = "dashscope-text-embedding-v2"

# 全局缓存
_vector_db = None


def _get_embeddings():
    """
    使用阿里云 DashScope 的 Embedding API（通过 OpenAI 兼容接口）。
    无需下载模型，一个 API 调用就返回向量，速度快且不占本地磁盘。
    """
    return OpenAIEmbeddings(
        model="text-embedding-v2",        # DashScope 的 Embedding 模型
        api_key=settings.API_KEY,         # 复用你的 DashScope Key
        base_url=settings.BASE_URL,       # https://dashscope.aliyuncs.com/compatible-mode/v1
    )


def _get_vector_db():
    """懒加载向量数据库：已有就直接读，没有就从文档构建"""
    global _vector_db

    if _vector_db is not None:
        return _vector_db

    embeddings = _get_embeddings()

    # 检查是否需要重建（换了 embedding 模型或数据库不存在）
    need_rebuild = True
    if os.path.exists(PERSIST_DIRECTORY) and os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            saved_version = f.read().strip()
        if saved_version == CURRENT_EMBEDDING_MODEL:
            need_rebuild = False

    if not need_rebuild and os.path.exists(PERSIST_DIRECTORY):
        print("[RAG] 加载已有向量数据库（Embedding: DashScope API，秒级）...")
        _vector_db = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings
        )
        print("[RAG] 向量数据库就绪。")
    else:
        # 需要重建：删掉旧数据库（如果有）
        if need_rebuild and os.path.exists(PERSIST_DIRECTORY):
            import shutil
            print("[RAG] Embedding 模型已更换或数据库损坏，删除旧库重建...")
            shutil.rmtree(PERSIST_DIRECTORY)

        print("[RAG] 正在从文档构建向量数据库（调用 DashScope Embedding API）...")
        if not os.path.exists(DOC_PATH):
            raise FileNotFoundError(f"文档文件不存在: {DOC_PATH}")

        loader = TextLoader(DOC_PATH, encoding="utf-8")
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        chunks = text_splitter.split_documents(documents)
        print(f"[RAG] 文档已切分为 {len(chunks)} 个片段，正在生成向量...")

        _vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY
        )

        # 标记版本，下次启动知道用的是什么模型
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
        with open(VERSION_FILE, "w") as f:
            f.write(CURRENT_EMBEDDING_MODEL)

        print("[RAG] 知识库构建完成（Embedding: DashScope API）。")

    return _vector_db


def search_knowledge_base(query: str) -> str:
    """
    在本地知识库中搜索相关内容。
    首次调用会自动构建/加载向量库（API 调用，秒级），后续查询直接检索。
    """
    print(f"   -> [RAG Search] 搜索: {query}")
    db = _get_vector_db()
    docs = db.similarity_search(query, k=3)

    if not docs:
        return "本地知识库中未找到相关机密信息。"

    result_text = "\n\n".join(
        [f"片段 {i + 1}:\n{doc.page_content}" for i, doc in enumerate(docs)]
    )
    return result_text
