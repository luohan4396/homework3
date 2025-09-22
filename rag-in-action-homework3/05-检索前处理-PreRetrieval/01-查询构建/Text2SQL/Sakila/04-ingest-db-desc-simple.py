# ingest_dbdesc_simple.py - 简化版本，不依赖Milvus
import logging
import os
import yaml
import pickle
import json
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 加载环境变量
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 简单的向量数据库类（复用之前的实现）
class SimpleVectorDB:
    def __init__(self):
        self.vectors = []
        self.metadata = []
        self.vectorizer = TfidfVectorizer(max_features=512, stop_words='english', ngram_range=(1, 2))
        self.fitted = False
    
    def add_documents(self, texts, metadata_list):
        """添加文档到向量数据库"""
        if not self.fitted:
            vectors = self.vectorizer.fit_transform(texts)
            self.fitted = True
        else:
            vectors = self.vectorizer.transform(texts)
        
        self.vectors.extend(vectors.toarray())
        self.metadata.extend(metadata_list)
        
        logging.info(f"添加了 {len(texts)} 个文档到向量数据库")
    
    def search(self, query_text, top_k=3):
        """搜索相似文档"""
        if not self.fitted:
            return []
        
        query_vector = self.vectorizer.transform([query_text]).toarray()[0]
        
        similarities = []
        for i, doc_vector in enumerate(self.vectors):
            similarity = cosine_similarity([query_vector], [doc_vector])[0][0]
            similarities.append((similarity, i))
        
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

# 2. 加载 DB 描述
desc_file = "90-文档-Data/sakila/db_description.yaml"
if not os.path.exists(desc_file):
    print(f"错误：找不到文件 {desc_file}")
    print("创建示例数据库描述文件...")
    
    # 创建示例数据库描述
    sample_desc = {
        "actor": {
            "actor_id": "演员的唯一标识符",
            "first_name": "演员的名字",
            "last_name": "演员的姓氏",
            "last_update": "记录最后更新时间"
        },
        "film": {
            "film_id": "电影的唯一标识符",
            "title": "电影标题",
            "description": "电影描述",
            "release_year": "电影发行年份",
            "language_id": "电影语言标识符",
            "rental_duration": "租赁期限（天数）",
            "rental_rate": "租赁费用",
            "length": "电影时长（分钟）",
            "replacement_cost": "替换成本",
            "rating": "电影评级（G, PG, PG-13, R, NC-17）",
            "special_features": "特殊功能",
            "last_update": "记录最后更新时间"
        },
        "customer": {
            "customer_id": "客户的唯一标识符",
            "store_id": "客户所属商店标识符",
            "first_name": "客户的名字",
            "last_name": "客户的姓氏",
            "email": "客户邮箱地址",
            "address_id": "客户地址标识符",
            "active": "客户是否活跃",
            "create_date": "客户创建日期",
            "last_update": "记录最后更新时间"
        },
        "rental": {
            "rental_id": "租赁记录的唯一标识符",
            "rental_date": "租赁日期",
            "inventory_id": "库存标识符",
            "customer_id": "客户标识符",
            "return_date": "归还日期",
            "staff_id": "处理租赁的员工标识符",
            "last_update": "记录最后更新时间"
        },
        "category": {
            "category_id": "电影类别的唯一标识符",
            "name": "类别名称（如动作、喜剧、戏剧等）",
            "last_update": "记录最后更新时间"
        },
        "film_actor": {
            "actor_id": "演员标识符",
            "film_id": "电影标识符",
            "last_update": "记录最后更新时间"
        },
        "film_category": {
            "film_id": "电影标识符",
            "category_id": "类别标识符",
            "last_update": "记录最后更新时间"
        },
        "store": {
            "store_id": "商店的唯一标识符",
            "manager_staff_id": "商店经理的员工标识符",
            "address_id": "商店地址标识符",
            "last_update": "记录最后更新时间"
        },
        "staff": {
            "staff_id": "员工的唯一标识符",
            "first_name": "员工的名字",
            "last_name": "员工的姓氏",
            "address_id": "员工地址标识符",
            "email": "员工邮箱地址",
            "store_id": "员工所属商店标识符",
            "active": "员工是否活跃",
            "username": "员工用户名",
            "password": "员工密码",
            "last_update": "记录最后更新时间"
        }
    }
    
    os.makedirs("90-文档-Data/sakila", exist_ok=True)
    with open(desc_file, "w", encoding='utf-8') as f:
        yaml.dump(sample_desc, f, allow_unicode=True, default_flow_style=False)
    print(f"✓ 已创建示例文件 {desc_file}")

try:
    with open(desc_file, "r", encoding='utf-8') as f:
        desc_map = yaml.safe_load(f)
        logging.info(f"[DBDESC] 从YAML文件加载了 {len(desc_map)} 个表的描述")
except Exception as e:
    print(f"✗ 读取文件失败: {e}")
    exit(1)

# 3. 创建向量数据库
vector_db = SimpleVectorDB()

# 4. 准备数据
texts = []
metadata_list = []
for tbl, cols in desc_map.items():
    for col, desc in cols.items():
        # 组合表名、列名和描述作为搜索文本
        search_text = f"{tbl}.{col}: {desc}"
        texts.append(search_text)
        metadata_list.append({
            "table_name": tbl, 
            "column_name": col, 
            "description": desc
        })

logging.info(f"[DBDESC] 准备处理 {len(texts)} 个字段描述")

# 5. 添加文档到向量数据库
vector_db.add_documents(texts, metadata_list)

# 6. 保存向量数据库
db_file = "05-检索前处理-PreRetrieval/01-查询构建/Text2SQL/Sakila/dbdesc_vectordb.pkl"
vector_db.save(db_file)

# 7. 测试搜索功能
test_queries = [
    "演员姓名",
    "电影标题",
    "客户邮箱",
    "租赁费用",
    "电影类别"
]

print("\n=== 测试搜索功能 ===")
for query in test_queries:
    print(f"\n查询: {query}")
    results = vector_db.search(query, top_k=3)
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        print(f"  {i}. 相似度: {result['similarity']:.4f}")
        print(f"     表.字段: {metadata['table_name']}.{metadata['column_name']}")
        print(f"     描述: {metadata['description']}")

# 8. 保存为JSON格式（便于其他脚本使用）
json_file = "05-检索前处理-PreRetrieval/01-查询构建/Text2SQL/Sakila/dbdesc_metadata.json"
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(metadata_list, f, ensure_ascii=False, indent=2)

logging.info("[DBDESC] 知识库构建完成！")
print(f"\n✓ 生成的文件:")
print(f"  - {db_file}")
print(f"  - {json_file}")
print("✓ 可以使用 SimpleVectorDB.load() 加载数据库进行查询")