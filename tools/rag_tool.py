"""
================================================================================
RAG 工具 — 本地知识库检索（阿里云 DashScope Embedding API 版）
================================================================================

v5 改动：
  1. 支持读取 docs/ 目录下所有常用格式：.txt / .md / .py / .pdf / .docx / .csv
  2. 同步懒加载，首次查询时构建，避免多线程竞争 chroma.sqlite3 文件
  3. embedding 实例缓存 — 避免重复创建
  4. 所有重型 import 延迟加载，启动快
"""

import os
import shutil
import time

PERSIST_DIRECTORY = "./chroma_db"
DOC_DIR = "./docs"
VERSION_FILE = os.path.join(PERSIST_DIRECTORY, ".embedding_version")
CURRENT_VERSION = "v5"                          # v5: 去除后台预加载，触发重建DB

_vector_db = None
_embeddings = None


def _get_embeddings():
    """延迟导入重型库，只在首次调用时加载。实例级缓存。"""
    global _embeddings
    if _embeddings is not None:
        return _embeddings

    from langchain_core.embeddings import Embeddings
    from dashscope import TextEmbedding
    from core.config import settings

    class DashScopeEmbeddings(Embeddings):
        """LangChain 兼容的 DashScope Embedding 包装类"""

        def embed_documents(self, texts):
            """DashScope API 每次最多 10 条，需分批调用"""
            all_embeddings = []
            batch_size = 10
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                resp = TextEmbedding.call(
                    model="text-embedding-v4",
                    input=batch,
                    api_key=settings.API_KEY,
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"Embedding API 调用失败: {resp.message}")
                all_embeddings.extend([item["embedding"] for item in resp.output["embeddings"]])
            return all_embeddings

        def embed_query(self, text):
            resp = TextEmbedding.call(
                model="text-embedding-v4",
                input=[text],
                api_key=settings.API_KEY,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Embedding API 调用失败: {resp.message}")
            return resp.output["embeddings"][0]["embedding"]

    _embeddings = DashScopeEmbeddings()
    return _embeddings


def _load_all_documents(doc_dir: str):
    """逐个格式加载 docs/ 下所有文档
    支持格式：.txt / .md / .py / .csv / .pdf / .docx
    """
    from langchain_community.document_loaders import (
        DirectoryLoader, TextLoader, CSVLoader, PyPDFLoader, Docx2txtLoader,
    )

    FORMATS = [
        ("*.txt",       TextLoader,      {"encoding": "utf-8"}),
        ("*.md",        TextLoader,      {"encoding": "utf-8"}),
        ("*.py",        TextLoader,      {"encoding": "utf-8"}),
        ("*.csv",       CSVLoader,       {"encoding": "utf-8"}),
        ("*.pdf",       PyPDFLoader,     {}),
        ("*.docx",      Docx2txtLoader,  {}),
    ]

    all_docs = []
    for glob_pattern, loader_cls, kwargs in FORMATS:
        try:
            loader = DirectoryLoader(
                doc_dir,
                glob=[glob_pattern],
                loader_cls=loader_cls,
                loader_kwargs=kwargs,
                show_progress=True,
                silent_errors=False,
            )
            docs = loader.load()
            if docs:
                print(f"[RAG]   {glob_pattern}: 加载 {len(docs)} 个文档")
                all_docs.extend(docs)
        except Exception as e:
            print(f"[RAG]   {glob_pattern}: 跳过（{e}）")

    return all_docs


def _load_vector_db_sync():
    """同步加载向量库 — 首次构建或从磁盘加载已有DB"""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma

    embeddings = _get_embeddings()

    need_rebuild = not (os.path.exists(PERSIST_DIRECTORY) and os.path.exists(VERSION_FILE))
    if not need_rebuild:
        with open(VERSION_FILE, "r") as f:
            need_rebuild = f.read().strip() != CURRENT_VERSION

    if need_rebuild:
        if os.path.exists(PERSIST_DIRECTORY):
            shutil.rmtree(PERSIST_DIRECTORY)

        print("[RAG] 正在通过 DashScope API 构建向量数据库...")
        t0 = time.time()
        if not os.path.exists(DOC_DIR):
            raise FileNotFoundError(f"文档目录不存在: {DOC_DIR}")

        documents = _load_all_documents(DOC_DIR)
        if not documents:
            raise RuntimeError(f"文档目录 {DOC_DIR} 下没有找到任何可读取的文件")

        print(f"[RAG] 共加载 {len(documents)} 个文档")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
        chunks = text_splitter.split_documents(documents)
        print(f"[RAG] 文档切分为 {len(chunks)} 段，调用 Embedding API 生成向量...")

        db = Chroma.from_documents(
            documents=chunks, embedding=embeddings, persist_directory=PERSIST_DIRECTORY,
        )
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
        with open(VERSION_FILE, "w") as f:
            f.write(CURRENT_VERSION)
        print(f"[RAG] 向量数据库构建完成（耗时 {time.time()-t0:.1f}秒）")
    else:
        t0 = time.time()
        print("[RAG] 加载已有向量数据库...")
        db = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embeddings)
        print(f"[RAG] 向量数据库就绪（耗时 {time.time()-t0:.1f}秒）")

    return db


def _get_vector_db():
    """懒加载向量数据库 — 同步加载，首次调用时构建或加载"""
    global _vector_db
    if _vector_db is not None:
        return _vector_db
    _vector_db = _load_vector_db_sync()
    return _vector_db


def search_knowledge_base(query: str) -> str:
    """在本地知识库中搜索。"""
    print(f"   -> [RAG Search] 搜索: {query}")
    db = _get_vector_db()
    t0 = time.time()
    docs = db.similarity_search(query, k=3)
    print(f"   -> [RAG Search] 向量检索耗时: {time.time()-t0:.1f}秒")

    if not docs:
        return "本地知识库中未找到相关信息。"

    return "\n\n".join([f"片段 {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])
