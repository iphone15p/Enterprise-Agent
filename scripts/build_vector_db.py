import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

print("1. 📖 正在读取绝密档案...")
loader = TextLoader("data/secret_document.txt", encoding="utf-8")
docs = loader.load()

print("2. ✂️ 正在把长文档切成小块...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=150,    # 每个小块大约 150 个字
    chunk_overlap=30   # 上下文重叠 30 个字，防止一句话被从中间硬生生切断
)
chunks = text_splitter.split_documents(docs)
print(f"   -> 成功切分为 {len(chunks)} 个小段落！")

print("3. 🧠 正在下载/加载向量大模型 (初次运行可能需要一点时间下载，请保持网络畅通，耐心等待)...")
# 使用一个轻量级的开源模型，把人类的文字翻译成机器能懂的“数学坐标”
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

print("4. 🧮 正在把所有段落转化为数学坐标，并构建 FAISS 向量数据库...")
vector_db = FAISS.from_documents(chunks, embeddings)

print("5. 💾 正在把数据库保存到本地硬盘...")
vector_db.save_local("data/faiss_index")

print("\n🎉 大功告成！企业知识库已建立！请查看左边 data 文件夹下是不是多了一个叫 'faiss_index' 的文件夹！")