# test_vectordb.py - 测试向量数据库功能
import pickle
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 加载向量数据库
def load_vectordb(filepath):
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    return data

# 测试Q2SQL向量数据库
print("=== 测试Q2SQL向量数据库 ===")
try:
    q2sql_db = load_vectordb("q2sql_vectordb.pkl")
    print(f"✓ Q2SQL数据库加载成功")
    print(f"  - 向量数量: {len(q2sql_db['vectors'])}")
    print(f"  - 元数据数量: {len(q2sql_db['metadata'])}")
    
    # 显示前3个问答对
    print("\n前3个问答对:")
    for i in range(min(3, len(q2sql_db['metadata']))):
        meta = q2sql_db['metadata'][i]
        print(f"  {i+1}. 问题: {meta['question']}")
        print(f"     SQL: {meta['sql_text']}")
        
except Exception as e:
    print(f"✗ Q2SQL数据库加载失败: {e}")

print("\n" + "="*50)

# 测试DBDESC向量数据库
print("=== 测试DBDESC向量数据库 ===")
try:
    dbdesc_db = load_vectordb("dbdesc_vectordb.pkl")
    print(f"✓ DBDESC数据库加载成功")
    print(f"  - 向量数量: {len(dbdesc_db['vectors'])}")
    print(f"  - 元数据数量: {len(dbdesc_db['metadata'])}")
    
    # 显示前5个字段描述
    print("\n前5个字段描述:")
    for i in range(min(5, len(dbdesc_db['metadata']))):
        meta = dbdesc_db['metadata'][i]
        print(f"  {i+1}. {meta['table_name']}.{meta['column_name']}: {meta['description']}")
        
except Exception as e:
    print(f"✗ DBDESC数据库加载失败: {e}")

print("\n" + "="*50)

# 测试搜索功能
print("=== 测试搜索功能 ===")
try:
    # 手动测试向量搜索
    vectorizer = dbdesc_db['vectorizer']
    vectors = dbdesc_db['vectors']
    metadata = dbdesc_db['metadata']
    
    test_query = "actor name"
    query_vector = vectorizer.transform([test_query]).toarray()[0]
    
    print(f"查询: {test_query}")
    print(f"查询向量维度: {len(query_vector)}")
    print(f"查询向量非零元素: {sum(1 for x in query_vector if x > 0)}")
    
    # 计算相似度
    similarities = []
    for i, doc_vector in enumerate(vectors):
        similarity = cosine_similarity([query_vector], [doc_vector])[0][0]
        if similarity > 0:  # 只显示有相似度的结果
            similarities.append((similarity, i))
    
    similarities.sort(reverse=True)
    
    print(f"找到 {len(similarities)} 个相关结果:")
    for similarity, idx in similarities[:5]:
        meta = metadata[idx]
        print(f"  相似度: {similarity:.4f} - {meta['table_name']}.{meta['column_name']}: {meta['description']}")
        
    if not similarities:
        print("  没有找到相关结果，可能是向量化问题")
        
        # 检查一些具体的字段
        print("\n检查包含'actor'的字段:")
        for i, meta in enumerate(metadata):
            if 'actor' in meta['table_name'].lower() or 'actor' in meta['description'].lower():
                print(f"  {meta['table_name']}.{meta['column_name']}: {meta['description']}")
        
except Exception as e:
    print(f"✗ 搜索测试失败: {e}")

print("\n" + "="*50)

# 检查JSON元数据文件
print("=== 检查JSON元数据文件 ===")
try:
    with open("dbdesc_metadata.json", 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    print(f"✓ JSON文件加载成功，包含 {len(json_data)} 个字段")
    
    # 按表分组显示
    tables = {}
    for item in json_data:
        table = item['table_name']
        if table not in tables:
            tables[table] = []
        tables[table].append(item)
    
    print(f"\n包含的表: {list(tables.keys())}")
    for table, fields in tables.items():
        print(f"  {table}: {len(fields)} 个字段")
        
except Exception as e:
    print(f"✗ JSON文件加载失败: {e}")