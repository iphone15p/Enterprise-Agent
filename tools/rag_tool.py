import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 1. 设定本地向量数据库的存储路径
PERSIST_DIRECTORY = "./chroma_db"
# 2. 设定我们要读取的机密文件路径
DOC_PATH = "./docs/company_docs.txt"


def build_or_load_vector_db():
    """
    初始化或加载本地向量数据库。
    设计思路：
    如果本地已经有了数据库，就直接读取，避免每次运行都重新消耗 API Token 去算向量。
    如果没有，就读取 txt 文件，切块，并生成数据库。
    """
    # 🌟 换成本地开源的轻量级中文向量引擎！完全不走网络 API，秒级计算！
    embeddings = HuggingFaceEmbeddings(  # 名字换了，参数不变
        model_name="shibing624/text2vec-base-chinese",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    if os.path.exists(PERSIST_DIRECTORY):
        print("📦 [RAG 引擎] 发现本地知识库缓存，正在极速加载...")
        vectordb = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embeddings)
    else:
        print("🔨 [RAG 引擎] 未发现本地数据库，正在读取机密文件并构建知识库...")

        # 确保文件存在
        if not os.path.exists(DOC_PATH):
            raise FileNotFoundError(f"🚨 找不到机密文件，请确保 {DOC_PATH} 存在！")

        # 第 1 步：读取文件
        loader = TextLoader(DOC_PATH, encoding="utf-8")
        documents = loader.load()

        # 第 2 步：切割文本 (每段100字，段落之间重叠20字以保留上下文语义)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        chunks = text_splitter.split_documents(documents)

        # 第 3 步：构建数据库并持久化保存到本地
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY
        )
        print("✅ [RAG 引擎] 私有知识库构建完成！")

    return vectordb


# 在模块加载时，初始化全局的向量数据库实例
vector_db = build_or_load_vector_db()


def search_knowledge_base(query: str) -> str:
    """
    暴露给 Agent 调用的终极武器工具。
    接收问题，去向量数据库中寻找答案。
    """
    print(f"   -> 🔍 [内部检索库] 正在机密档案中搜索: {query}")

    # 执行相似度搜索，提取最相关的 3 个文档片段
    docs = vector_db.similarity_search(query, k=3)

    if not docs:
        return "本地知识库中未找到相关机密信息。"

    # 将找到的多个片段拼接成一段长字符串，返回给大模型
    result_text = "\n\n".join([f"片段 {i + 1}:\n{doc.page_content}" for i, doc in enumerate(docs)])
    return result_text