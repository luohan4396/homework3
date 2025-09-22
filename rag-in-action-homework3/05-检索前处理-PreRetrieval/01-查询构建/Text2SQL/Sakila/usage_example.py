# 使用示例
import pickle
import json
import numpy as np

# 加载嵌入模型
with open("ddl_embedding_model.pkl", "rb") as f:
    embedding_model = pickle.load(f)

# 查询示例
query = "查找演员相关的表"
query_vector = embedding_model.transform([query])[0]

try:
    import faiss
    # 使用 FAISS
    index = faiss.read_index("ddl_faiss_index.bin")
    with open("ddl_metadata.json", "r", encoding='utf-8') as f:
        metadata = json.load(f)
    
    query_vector = query_vector / np.linalg.norm(query_vector)
    scores, indices = index.search(query_vector.reshape(1, -1).astype('float32'), 5)
    
    print("搜索结果:")
    for score, idx in zip(scores[0], indices[0]):
        if idx != -1:
            print(f"表名: {metadata[idx]['table_name']}, 相似度: {score:.4f}")
            
except ImportError:
    # 使用简单向量数据库
    from your_script import SimpleVectorDB
    vector_db = SimpleVectorDB.load("ddl_simple_vectordb.json")
    results = vector_db.search(query_vector, top_k=5)
    
    print("搜索结果:")
    for result in results:
        print(f"表名: {result['metadata']['table_name']}, 相似度: {result['similarity']:.4f}")
