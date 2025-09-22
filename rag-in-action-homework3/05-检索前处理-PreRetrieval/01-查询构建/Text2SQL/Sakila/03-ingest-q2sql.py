# ingest_q2sql.py
import logging
import os
from dotenv import load_dotenv
from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema
from pymilvus import model
import torch
import json

# 加载环境变量
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 检查OpenAI API密钥
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("错误：未找到 OPENAI_API_KEY")
    print("请在 .env 文件中设置 OPENAI_API_KEY=your_openai_api_key")
    exit(1)

# 1. 初始化嵌入函数
try:
    embedding_function = model.dense.OpenAIEmbeddingFunction(
        model_name='text-embedding-3-large',
        api_key=api_key
    )
    print("✓ OpenAI嵌入函数初始化成功")
except Exception as e:
    print(f"✗ OpenAI嵌入函数初始化失败: {e}")
    exit(1)

# 2. 加载 Q->SQL 对（假设 q2sql_pairs.json 数组，每项 { "question": ..., "sql": ... }）
q2sql_file = "90-文档-Data/sakila/q2sql_pairs.json"
if not os.path.exists(q2sql_file):
    print(f"错误：找不到文件 {q2sql_file}")
    print("请确保该文件存在，或者创建示例数据")
    
    # 创建示例数据
    sample_pairs = [
        {
            "question": "显示所有演员的姓名",
            "sql": "SELECT first_name, last_name FROM actor"
        },
        {
            "question": "统计电影总数",
            "sql": "SELECT COUNT(*) FROM film"
        },
        {
            "question": "查找评级为PG的电影",
            "sql": "SELECT title FROM film WHERE rating = 'PG'"
        }
    ]
    
    os.makedirs("90-文档-Data/sakila", exist_ok=True)
    with open(q2sql_file, "w", encoding='utf-8') as f:
        json.dump(sample_pairs, f, ensure_ascii=False, indent=2)
    print(f"✓ 已创建示例文件 {q2sql_file}")

try:
    with open(q2sql_file, "r", encoding='utf-8') as f:
        pairs = json.load(f)
        logging.info(f"[Q2SQL] 从JSON文件加载了 {len(pairs)} 个问答对")
except Exception as e:
    print(f"✗ 读取文件失败: {e}")
    exit(1)

# 3. 连接 Milvus (使用内存模式避免milvus-lite依赖)
try:
    client = MilvusClient(uri="./text2sql_milvus_sakila.db")
    print("✓ Milvus客户端连接成功")
except Exception as e:
    print(f"✗ Milvus连接失败: {e}")
    print("尝试使用内存模式...")
    try:
        client = MilvusClient(uri=":memory:")
        print("✓ 使用内存模式连接成功")
    except Exception as e2:
        print(f"✗ 内存模式也失败: {e2}")
        exit(1)

# 4. 定义 Collection Schema
vector_dim = len(embedding_function(["dummy"])[0])
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=vector_dim),
    FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="sql_text", dtype=DataType.VARCHAR, max_length=2000),
]
schema = CollectionSchema(fields, description="Q2SQL Knowledge Base", enable_dynamic_field=False)

# 5. 创建 Collection（如不存在）
collection_name = "q2sql_knowledge"
if not client.has_collection(collection_name):
    client.create_collection(collection_name=collection_name, schema=schema)
    logging.info(f"[Q2SQL] 创建了新的集合 {collection_name}")
else:
    logging.info(f"[Q2SQL] 集合 {collection_name} 已存在")

# 6. 为向量字段添加索引
index_params = client.prepare_index_params()
index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="COSINE", params={"nlist": 1024})
client.create_index(collection_name=collection_name, index_params=index_params)

# 7. 批量插入 Q2SQL 对
data = []
texts = []
for pair in pairs:
    texts.append(pair["question"])
    data.append({"question": pair["question"], "sql_text": pair["sql"]})

logging.info(f"[Q2SQL] 准备处理 {len(data)} 个问答对")

# 生成全部嵌入
embeddings = embedding_function(texts)
logging.info(f"[Q2SQL] 成功生成了 {len(embeddings)} 个向量嵌入")

# 组织为 Milvus insert 格式
records = []
for emb, rec in zip(embeddings, data):
    rec["vector"] = emb
    records.append(rec)

res = client.insert(collection_name=collection_name, data=records)
logging.info(f"[Q2SQL] 成功插入了 {len(records)} 条记录到Milvus")
logging.info(f"[Q2SQL] 插入结果: {res}")

logging.info("[Q2SQL] 知识库构建完成")
