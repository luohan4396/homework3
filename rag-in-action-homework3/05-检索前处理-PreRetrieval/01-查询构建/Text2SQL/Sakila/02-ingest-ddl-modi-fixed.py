# ingest_ddl_fixed.py
import logging
from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema
import yaml
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 1. 初始化嵌入函数
def get_embedding_function():
    """尝试不同的嵌入方法"""
    try:
        # 首先尝试使用 OpenAI
        from pymilvus.model.dense import OpenAIEmbeddingFunction
        return OpenAIEmbeddingFunction(model_name='text-embedding-3-large')
    except Exception as e:
        logging.warning(f"[DDL] OpenAI 嵌入函数初始化失败: {e}")
        
        try:
            # 尝试使用 SentenceTransformer
            from pymilvus.model.dense import SentenceTransformerEmbeddingFunction
            logging.info("[DDL] 使用 SentenceTransformer 作为备选嵌入函数")
            return SentenceTransformerEmbeddingFunction(model_name='all-MiniLM-L6-v2')
        except Exception as e2:
            logging.error(f"[DDL] SentenceTransformer 嵌入函数也失败: {e2}")
            raise Exception("无法初始化任何嵌入函数")

embedding_function = get_embedding_function()

# 2. 读取 DDL 列表
ddl_file_path = os.path.join("..", "..", "..", "..", "90-文档-Data", "sakila", "ddl_statements.yaml")
with open(ddl_file_path, "r", encoding='utf-8') as f:
    ddl_map = yaml.safe_load(f)
    logging.info(f"[DDL] 从YAML文件加载了 {len(ddl_map)} 个表/视图定义")

# 3. 连接 Milvus
client = MilvusClient("text2sql_milvus_sakila.db")

# 4. 获取向量维度（先测试一个样本）
sample_embedding = embedding_function(["dummy text"])
vector_dim = len(sample_embedding[0])
logging.info(f"[DDL] 向量维度: {vector_dim}")

# 5. 定义 Collection Schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=vector_dim),
    FieldSchema(name="table_name", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="ddl_text", dtype=DataType.VARCHAR, max_length=5000),  # 增加长度以容纳复杂的DDL
]
schema = CollectionSchema(fields, description="DDL Knowledge Base", enable_dynamic_field=False)

# 6. 创建 Collection（如不存在）
collection_name = "ddl_knowledge"
if client.has_collection(collection_name):
    client.drop_collection(collection_name)
    logging.info(f"[DDL] 删除已存在的集合 {collection_name}")

client.create_collection(collection_name=collection_name, schema=schema)
logging.info(f"[DDL] 创建了新的集合 {collection_name}")

# 7. 为向量字段添加索引
index_params = client.prepare_index_params()
index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="COSINE")
client.create_index(collection_name=collection_name, index_params=index_params)
logging.info(f"[DDL] 为集合 {collection_name} 创建了向量索引")

# 8. 批量处理 DDL
data = []
texts = []
for tbl, ddl in ddl_map.items():
    texts.append(ddl)
    data.append({"table_name": tbl, "ddl_text": ddl})

logging.info(f"[DDL] 准备处理 {len(data)} 个表/视图的DDL语句")

# 9. 生成嵌入
logging.info(f"[DDL] 开始生成 {len(texts)} 个文本的向量嵌入")

try:
    embeddings = embedding_function(texts)
    logging.info(f"[DDL] 成功生成了 {len(embeddings)} 个向量嵌入")
    
    # 组织为 Milvus insert 格式
    records = []
    for emb, rec in zip(embeddings, data):
        rec["vector"] = emb
        records.append(rec)
        
except Exception as e:
    logging.error(f"[DDL] 生成嵌入时出错: {e}")
    raise

# 10. 插入数据到 Milvus
res = client.insert(collection_name=collection_name, data=records)
logging.info(f"[DDL] 成功插入了 {len(records)} 条记录到Milvus")
logging.info(f"[DDL] 插入结果: {res}")

# 11. 验证插入结果
collection_stats = client.get_collection_stats(collection_name)
logging.info(f"[DDL] 集合统计信息: {collection_stats}")

logging.info("[DDL] 知识库构建完成")