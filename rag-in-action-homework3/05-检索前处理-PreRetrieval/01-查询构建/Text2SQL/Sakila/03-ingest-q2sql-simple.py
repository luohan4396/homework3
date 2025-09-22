# ingest_q2sql_simple.py - 简化版本，不依赖Milvus
import logging
import os
import json
import pickle
import numpy as np
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 加载环境变量
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 检查OpenAI API密钥
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("错误：未找到 OPENAI_API_KEY")
    print("请在 .env 文件中设置 OPENAI_API_KEY=your_openai_api_key")
    exit(1)

print("✓ API密钥配置成功")

# 简单的向量数据库类
class SimpleVectorDB:
    def __init__(self):
        self.vectors = []
        self.metadata = []
        self.vectorizer = TfidfVectorizer(max_features=512, stop_words='english', ngram_range=(1, 2))
        self.fitted = False
    
    def add_documents(self, texts, metadata_list):
        """添加文档到向量数据库"""
        if not self.fitted:
            # 第一次添加文档时训练向量化器
            vectors = self.vectorizer.fit_transform(texts)
            self.fitted = True
        else:
            # 后续添加文档时使用已训练的向量化器
            vectors = self.vectorizer.transform(texts)
        
        self.vectors.extend(vectors.toarray())
        self.metadata.extend(metadata_list)
        
        logging.info(f"添加了 {len(texts)} 个文档到向量数据库")
    
    def search(self, query_text, top_k=3):
        """搜索相似文档"""
        if not self.fitted:
            return []
        
        query_vector = self.vectorizer.transform([query_text]).toarray()[0]
        
        # 计算余弦相似度
        similarities = []
        for i, doc_vector in enumerate(self.vectors):
            similarity = cosine_similarity([query_vector], [doc_vector])[0][0]
            similarities.append((similarity, i))
        
        # 按相似度排序并返回top_k结果
        similarities.sort(reverse=True)
        results = []
        for similarity, idx in similarities[:top_k]:
            results.append({
                'similarity': similarity,
                'metadata': self.metadata[idx]
            })
        
        return results
    
    def save(self, filepath):
        """保存向量数据库"""
        data = {
            'vectors': self.vectors,
            'metadata': self.metadata,
            'vectorizer': self.vectorizer,
            'fitted': self.fitted
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        logging.info(f"向量数据库已保存到 {filepath}")
    
    @classmethod
    def load(cls, filepath):
        """加载向量数据库"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        db = cls()
        db.vectors = data['vectors']
        db.metadata = data['metadata']
        db.vectorizer = data['vectorizer']
        db.fitted = data['fitted']
        
        logging.info(f"从 {filepath} 加载了向量数据库")
        return db

# 2. 加载 Q->SQL 对
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
        },
        {
            "question": "显示所有客户的姓名和邮箱",
            "sql": "SELECT first_name, last_name, email FROM customer"
        },
        {
            "question": "查找租赁费用最高的电影",
            "sql": "SELECT title, rental_rate FROM film ORDER BY rental_rate DESC LIMIT 1"
        },
        {
            "question": "统计每个演员参演的电影数量",
            "sql": "SELECT a.first_name, a.last_name, COUNT(fa.film_id) as film_count FROM actor a JOIN film_actor fa ON a.actor_id = fa.actor_id GROUP BY a.actor_id"
        },
        {
            "question": "查找最受欢迎的电影类别",
            "sql": "SELECT c.name, COUNT(fc.film_id) as film_count FROM category c JOIN film_category fc ON c.category_id = fc.category_id GROUP BY c.category_id ORDER BY film_count DESC LIMIT 1"
        },
        {
            "question": "显示所有商店的地址信息",
            "sql": "SELECT s.store_id, a.address, c.city, co.country FROM store s JOIN address a ON s.address_id = a.address_id JOIN city c ON a.city_id = c.city_id JOIN country co ON c.country_id = co.country_id"
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

# 3. 创建向量数据库
vector_db = SimpleVectorDB()

# 4. 准备数据
texts = []
metadata_list = []
for pair in pairs:
    texts.append(pair["question"])
    metadata_list.append({
        "question": pair["question"], 
        "sql_text": pair["sql"]
    })

logging.info(f"[Q2SQL] 准备处理 {len(pairs)} 个问答对")

# 5. 添加文档到向量数据库
vector_db.add_documents(texts, metadata_list)

# 6. 保存向量数据库
db_file = "05-检索前处理-PreRetrieval/01-查询构建/Text2SQL/Sakila/q2sql_vectordb.pkl"
vector_db.save(db_file)

# 7. 测试搜索功能
test_queries = [
    "查找所有演员",
    "电影数量统计",
    "PG级别的电影"
]

print("\n=== 测试搜索功能 ===")
for query in test_queries:
    print(f"\n查询: {query}")
    results = vector_db.search(query, top_k=3)
    for i, result in enumerate(results, 1):
        print(f"  {i}. 相似度: {result['similarity']:.4f}")
        print(f"     问题: {result['metadata']['question']}")
        print(f"     SQL: {result['metadata']['sql_text']}")

logging.info("[Q2SQL] 知识库构建完成！")
print(f"\n✓ 生成的文件: {db_file}")
print("✓ 可以使用 SimpleVectorDB.load() 加载数据库进行查询")