"""
================================================================================
RAG 工具 — 本地知识库检索（阿里云 DashScope Embedding API 版）
================================================================================

使用 dashscope.TextEmbedding 原生 API（不走兼容接口），
无需下载本地模型，API 调用秒级返回向量。

首次使用自动从 docs/company_docs.txt 构建向量库，之后持久化到 chroma_db/。
"""

import os
import shutil
from typing import List
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from dashscope import TextEmbedding

from core.config import settings

PERSIST_DIRECTORY = "./chroma_db"
DOC_PATH = "./docs/company_docs.txt"
VERSION_FILE = os.path.join(PERSIST_DIRECTORY, ".embedding_version")
CURRENT_VERSION = "v2"

_vector_db = None


class DashScopeEmbeddings(Embeddings):
    """
    LangChain 兼容的 DashScope Embedding 包装类。
    调用阿里云原生 TextEmbedding API（text-embedding-v2），不走 OpenAI 兼容接口。
    """

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量把文档转成向量（构建/更新知识库时用）"""
        # DashScope API 接受字符串列表，自动批处理
        resp = TextEmbedding.call(
            model="text-embedding-v2",
            input=texts,
            api_key=settings.API_KEY,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding API 调用失败: {resp.message}")
        # 按输入顺序返回向量
        return [item["embedding"] for item in resp.output["embeddings"]]

    def embed_query(self, text: str) -> List[float]:
        """把单个查询文本转成向量（检索时用）"""
        resp = TextEmbedding.call(
            model="text-embedding-v2",
            input=[text],
            api_key=settings.API_KEY,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding API 调用失败: {resp.message}")
        return resp.output["embeddings"][0]["embedding"]


def _get_vector_db():
    """懒加载向量数据库"""
    global _vector_db

    if _vector_db is not None:
        return _vector_db

    embeddings = DashScopeEmbeddings()

    # 检查是否需要重建（换模型 / 数据库不存在）
    need_rebuild = not (os.path.exists(PERSIST_DIRECTORY) and os.path.exists(VERSION_FILE))
    if not need_rebuild:
        with open(VERSION_FILE, "r") as f:
            need_rebuild = f.read().strip() != CURRENT_VERSION

    if need_rebuild:
        if os.path.exists(PERSIST_DIRECTORY):
            shutil.rmtree(PERSIST_DIRECTORY)

        print("[RAG] 正在通过 DashScope API 构建向量数据库...")
        if not os.path.exists(DOC_PATH):
            raise FileNotFoundError(f"文档文件不存在: {DOC_PATH}")

        loader = TextLoader(DOC_PATH, encoding="utf-8")
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        chunks = text_splitter.split_documents(documents)
        print(f"[RAG] 文档切分为 {len(chunks)} 段，正在调用 Embedding API 生成向量...")

        _vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY,
        )
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
        with open(VERSION_FILE, "w") as f:
            f.write(CURRENT_VERSION)
        print("[RAG] 向量数据库构建完成！")
    else:
        print("[RAG] 加载已有向量数据库...")
        _vector_db = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings,
        )
        print("[RAG] 向量数据库就绪。")

    return _vector_db


def search_knowledge_base(query: str) -> str:
    """
    在本地知识库中搜索。首次调用构建向量库（API 调用），后续秒回。
    """
    print(f"   -> [RAG Search] 搜索: {query}")
    db = _get_vector_db()
    docs = db.similarity_search(query, k=3)

    if not docs:
        return "本地知识库中未找到相关机密信息。"

    return "\n\n".join(
        [f"片段 {i + 1}:\n{doc.page_content}" for i, doc in enumerate(docs)]
    )
