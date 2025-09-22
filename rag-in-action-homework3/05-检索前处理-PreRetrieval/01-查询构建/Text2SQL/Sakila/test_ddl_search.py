# test_ddl_search.py - 测试DDL向量搜索功能
import pickle
import json
import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer

# 需要重新定义类以便pickle能够正确加载
class SimpleTfidfEmbedding:
    def __init__(self, max_features=384):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.fitted = False
    
    def fit_transform(self, texts):
        """训练并转换文本"""
        vectors = self.vectorizer.fit_transform(texts)
        self.fitted = True
        return vectors.toarray()
    
    def transform(self, texts):
        """转换文本（需要先fit）"""
        if not self.fitted:
            raise ValueError("需要先调用 fit_transform")
        vectors = self.vectorizer.transform(texts)
        return vectors.toarray()

def test_ddl_search():
    print("=== DDL 向量搜索测试 ===")
    
    # 1. 加载嵌入模型
    with open("ddl_embedding_model.pkl", "rb") as f:
        embedding_model = pickle.load(f)
    print("✓ 嵌入模型加载成功")
    
    # 2. 加载 FAISS 索引和元数据
    index = faiss.read_index("ddl_faiss_index.bin")
    with open("ddl_metadata.json", "r", encoding='utf-8') as f:
        metadata = json.load(f)
    print(f"✓ FAISS 索引加载成功，包含 {index.ntotal} 个向量")
    
    # 3. 测试不同类型的查询
    test_queries = [
        "查找演员相关的表",
        "电影信息表",
        "客户数据",
        "租赁记录",
        "地址信息",
        "CREATE TABLE actor",
        "film category relationship"
    ]
    
    for query in test_queries:
        print(f"\n查询: '{query}'")
        
        # 生成查询向量
        query_vector = embedding_model.transform([query])[0]
        query_vector = query_vector / np.linalg.norm(query_vector)  # 归一化
        
        # 搜索
        scores, indices = index.search(query_vector.reshape(1, -1).astype('float32'), 3)
        
        print("搜索结果:")
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx != -1:
                table_name = metadata[idx]['table_name']
                ddl_preview = metadata[idx]['ddl_text'][:100] + "..."
                print(f"  {i+1}. 表名: {table_name}")
                print(f"     相似度: {score:.4f}")
                print(f"     DDL预览: {ddl_preview}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_ddl_search()