# text2sql_simple_rag.py - 简化版Text2SQL RAG系统
import os
import pickle
import json
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

class SimpleText2SQL:
    def __init__(self):
        # 初始化DeepSeek客户端
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")
        
        self.client = OpenAI(
            base_url="https://api.deepseek.com",
            api_key=api_key
        )
        
        # 加载向量数据库
        self.load_databases()
        
    def load_databases(self):
        """加载所有向量数据库"""
        try:
            # 获取脚本所在目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 加载Q2SQL数据库
            q2sql_path = os.path.join(script_dir, "q2sql_vectordb.pkl")
            with open(q2sql_path, 'rb') as f:
                self.q2sql_db = pickle.load(f)
            print("✓ Q2SQL数据库加载成功")
            
            # 加载DBDESC数据库
            dbdesc_path = os.path.join(script_dir, "dbdesc_vectordb.pkl")
            with open(dbdesc_path, 'rb') as f:
                self.dbdesc_db = pickle.load(f)
            print("✓ DBDESC数据库加载成功")
            
            # 加载DDL信息（如果存在）
            ddl_file = os.path.join(os.getcwd(), "90-文档-Data", "sakila", "ddl_statements.yaml")
            if os.path.exists(ddl_file):
                import yaml
                with open(ddl_file, 'r', encoding='utf-8') as f:
                    self.ddl_info = yaml.safe_load(f)
                print("✓ DDL信息加载成功")
            else:
                self.ddl_info = {}
                print("⚠ DDL文件不存在，将使用基本schema信息")
                
        except Exception as e:
            print(f"✗ 数据库加载失败: {e}")
            raise
    
    def search_similar_questions(self, query, top_k=3):
        """搜索相似的问答对"""
        vectorizer = self.q2sql_db['vectorizer']
        vectors = self.q2sql_db['vectors']
        metadata = self.q2sql_db['metadata']
        
        query_vector = vectorizer.transform([query]).toarray()[0]
        
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = []
        for i, doc_vector in enumerate(vectors):
            similarity = cosine_similarity([query_vector], [doc_vector])[0][0]
            similarities.append((similarity, i))
        
        similarities.sort(reverse=True)
        
        results = []
        for similarity, idx in similarities[:top_k]:
            results.append({
                'similarity': similarity,
                'question': metadata[idx]['question'],
                'sql': metadata[idx]['sql_text']
            })
        
        return results
    
    def search_relevant_fields(self, query, top_k=5):
        """搜索相关的数据库字段"""
        vectorizer = self.dbdesc_db['vectorizer']
        vectors = self.dbdesc_db['vectors']
        metadata = self.dbdesc_db['metadata']
        
        query_vector = vectorizer.transform([query]).toarray()[0]
        
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = []
        for i, doc_vector in enumerate(vectors):
            similarity = cosine_similarity([query_vector], [doc_vector])[0][0]
            similarities.append((similarity, i))
        
        similarities.sort(reverse=True)
        
        results = []
        for similarity, idx in similarities[:top_k]:
            meta = metadata[idx]
            results.append({
                'similarity': similarity,
                'table': meta['table_name'],
                'column': meta['column_name'],
                'description': meta['description']
            })
        
        return results
    
    def get_basic_schema(self):
        """获取基本的数据库schema信息"""
        schema_info = """
Sakila数据库主要表结构：

1. actor - 演员表
   - actor_id: 演员ID
   - first_name: 名字
   - last_name: 姓氏

2. film - 电影表
   - film_id: 电影ID
   - title: 电影标题
   - description: 描述
   - release_year: 发行年份
   - rental_rate: 租赁费用
   - length: 时长
   - rating: 评级

3. customer - 客户表
   - customer_id: 客户ID
   - first_name: 名字
   - last_name: 姓氏
   - email: 邮箱
   - store_id: 商店ID

4. rental - 租赁表
   - rental_id: 租赁ID
   - rental_date: 租赁日期
   - customer_id: 客户ID
   - inventory_id: 库存ID

5. category - 类别表
   - category_id: 类别ID
   - name: 类别名称

6. film_actor - 电影演员关联表
   - film_id: 电影ID
   - actor_id: 演员ID

7. film_category - 电影类别关联表
   - film_id: 电影ID
   - category_id: 类别ID
"""
        return schema_info
    
    def generate_sql(self, user_query):
        """生成SQL查询"""
        print(f"\n🔍 用户查询: {user_query}")
        
        # 1. 搜索相似问答对
        similar_questions = self.search_similar_questions(user_query, top_k=3)
        print(f"📝 找到 {len(similar_questions)} 个相似问题")
        
        # 2. 搜索相关字段
        relevant_fields = self.search_relevant_fields(user_query, top_k=5)
        print(f"🏷️ 找到 {len(relevant_fields)} 个相关字段")
        
        # 3. 构建提示词
        prompt = self.build_prompt(user_query, similar_questions, relevant_fields)
        
        # 4. 调用DeepSeek生成SQL
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个SQL专家。请根据提供的信息生成正确的SQL查询语句。只返回SQL语句，不要包含任何解释。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            sql = response.choices[0].message.content.strip()
            # 清理可能的markdown标记
            sql = sql.replace('```sql', '').replace('```', '').strip()
            
            return sql
            
        except Exception as e:
            print(f"✗ LLM调用失败: {e}")
            return None
    
    def build_prompt(self, user_query, similar_questions, relevant_fields):
        """构建LLM提示词"""
        prompt = f"""
基于以下信息为用户查询生成SQL语句：

=== 数据库Schema ===
{self.get_basic_schema()}

=== 相关字段信息 ===
"""
        
        for field in relevant_fields:
            prompt += f"- {field['table']}.{field['column']}: {field['description']}\n"
        
        prompt += "\n=== 相似查询示例 ===\n"
        
        for i, example in enumerate(similar_questions, 1):
            prompt += f"{i}. 问题: {example['question']}\n"
            prompt += f"   SQL: {example['sql']}\n\n"
        
        prompt += f"""
=== 用户查询 ===
{user_query}

请生成对应的SQL查询语句：
"""
        
        return prompt
    
    def query(self, user_input):
        """处理用户查询的主函数"""
        print("="*60)
        
        # 生成SQL
        sql = self.generate_sql(user_input)
        
        if sql:
            print(f"\n✅ 生成的SQL:")
            print(f"```sql\n{sql}\n```")
            
            # 这里可以添加SQL执行逻辑
            print(f"\n💡 提示: 可以将此SQL在Sakila数据库中执行")
        else:
            print(f"\n❌ SQL生成失败")
        
        print("="*60)
        return sql

def main():
    """主函数"""
    print("🚀 启动简化版Text2SQL RAG系统")
    
    try:
        # 初始化系统
        text2sql = SimpleText2SQL()
        print("\n✅ 系统初始化完成")
        
        # 测试查询
        test_queries = [
            "显示所有演员的姓名",
            "查找评级为PG的电影",
            "统计每个类别的电影数量",
            "查找租赁费用最高的电影",
            "显示客户的邮箱地址"
        ]
        
        print(f"\n🧪 运行测试查询:")
        for query in test_queries:
            text2sql.query(query)
            
        # 交互模式
        print(f"\n💬 进入交互模式 (输入 'quit' 退出):")
        while True:
            user_input = input("\n请输入您的查询: ").strip()
            if user_input.lower() in ['quit', 'exit', '退出']:
                break
            if user_input:
                text2sql.query(user_input)
        
        print("👋 再见!")
        
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")

if __name__ == "__main__":
    main()