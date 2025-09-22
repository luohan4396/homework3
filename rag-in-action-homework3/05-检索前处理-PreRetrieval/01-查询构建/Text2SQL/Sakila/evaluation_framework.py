# evaluation_framework.py - Sakila Text2SQL 评估框架
import json
import sqlite3
from typing import List, Dict, Tuple
import difflib
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Text2SQLEvaluator:
    """Text2SQL 评估器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.results = defaultdict(list)
        
    def normalize_sql(self, sql: str) -> str:
        """标准化 SQL 语句"""
        # 移除多余空格，转换为小写
        sql = ' '.join(sql.split()).lower()
        # 移除分号
        sql = sql.rstrip(';')
        return sql
    
    def exact_match_score(self, predicted: str, ground_truth: str) -> float:
        """计算精确匹配分数"""
        pred_norm = self.normalize_sql(predicted)
        gt_norm = self.normalize_sql(ground_truth)
        return 1.0 if pred_norm == gt_norm else 0.0
    
    def token_level_accuracy(self, predicted: str, ground_truth: str) -> float:
        """计算 token 级别准确率"""
        pred_tokens = self.normalize_sql(predicted).split()
        gt_tokens = self.normalize_sql(ground_truth).split()
        
        if not gt_tokens:
            return 1.0 if not pred_tokens else 0.0
        
        # 使用序列匹配算法
        matcher = difflib.SequenceMatcher(None, pred_tokens, gt_tokens)
        return matcher.ratio()
    
    def execution_accuracy(self, predicted: str, ground_truth: str) -> Tuple[float, str]:
        """计算执行准确率"""
        if not self.db_path:
            return 0.0, "No database connection"
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 执行预测的 SQL
            try:
                cursor.execute(predicted)
                pred_result = cursor.fetchall()
            except Exception as e:
                return 0.0, f"Predicted SQL execution error: {str(e)}"
            
            # 执行标准答案 SQL
            try:
                cursor.execute(ground_truth)
                gt_result = cursor.fetchall()
            except Exception as e:
                return 0.0, f"Ground truth SQL execution error: {str(e)}"
            
            # 比较结果
            try:
                if pred_result == gt_result:
                    return 1.0, "Results match"
                else:
                    return 0.0, "Results differ"
            except Exception as e:
                return 0.0, f"Result comparison error: {str(e)}"
                
        except Exception as e:
            return 0.0, f"Database connection error: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    def evaluate_single(self, question: str, predicted: str, ground_truth: str) -> Dict:
        """评估单个样本"""
        # 精确匹配
        exact_match = self.exact_match_score(predicted, ground_truth)
        
        # Token 级别准确率
        token_acc = self.token_level_accuracy(predicted, ground_truth)
        
        # 执行准确率
        exec_acc, exec_msg = self.execution_accuracy(predicted, ground_truth)
        
        result = {
            'question': question,
            'predicted': predicted,
            'ground_truth': ground_truth,
            'exact_match': exact_match,
            'token_accuracy': token_acc,
            'execution_accuracy': exec_acc,
            'execution_message': exec_msg
        }
        
        return result
    
    def evaluate_batch(self, test_cases: List[Dict]) -> Dict:
        """批量评估"""
        results = []
        
        for case in test_cases:
            question = case['question']
            predicted = case['predicted']
            ground_truth = case['ground_truth']
            
            result = self.evaluate_single(question, predicted, ground_truth)
            results.append(result)
            
            logging.info(f"Evaluated: {question[:50]}... - EM: {result['exact_match']:.2f}, "
                        f"Token: {result['token_accuracy']:.2f}, Exec: {result['execution_accuracy']:.2f}")
        
        # 计算总体指标
        total_cases = len(results)
        exact_match_avg = sum(r['exact_match'] for r in results) / total_cases
        token_acc_avg = sum(r['token_accuracy'] for r in results) / total_cases
        exec_acc_avg = sum(r['execution_accuracy'] for r in results) / total_cases
        
        summary = {
            'total_cases': total_cases,
            'exact_match_accuracy': exact_match_avg,
            'token_level_accuracy': token_acc_avg,
            'execution_accuracy': exec_acc_avg,
            'detailed_results': results
        }
        
        return summary

class SakilaTestCaseGenerator:
    """Sakila 测试用例生成器"""
    
    def __init__(self):
        self.test_cases = []
    
    def generate_basic_cases(self) -> List[Dict]:
        """生成基础测试用例"""
        basic_cases = [
            {
                'question': '查找所有演员的姓名',
                'ground_truth': 'SELECT first_name, last_name FROM actor',
                'difficulty': 'easy',
                'category': 'basic_select'
            },
            {
                'question': '有多少部电影？',
                'ground_truth': 'SELECT COUNT(*) FROM film',
                'difficulty': 'easy',
                'category': 'aggregation'
            },
            {
                'question': '查找评级为 PG 的电影标题',
                'ground_truth': 'SELECT title FROM film WHERE rating = "PG"',
                'difficulty': 'easy',
                'category': 'filtering'
            },
            {
                'question': '查找演员 John 参演的所有电影',
                'ground_truth': '''SELECT f.title 
                                  FROM film f 
                                  JOIN film_actor fa ON f.film_id = fa.film_id 
                                  JOIN actor a ON fa.actor_id = a.actor_id 
                                  WHERE a.first_name = "John"''',
                'difficulty': 'medium',
                'category': 'join'
            },
            {
                'question': '每个类别有多少部电影？',
                'ground_truth': '''SELECT c.name, COUNT(fc.film_id) as film_count
                                  FROM category c
                                  LEFT JOIN film_category fc ON c.category_id = fc.category_id
                                  GROUP BY c.category_id, c.name''',
                'difficulty': 'medium',
                'category': 'group_by'
            },
            {
                'question': '查找租赁次数最多的前5部电影',
                'ground_truth': '''SELECT f.title, COUNT(r.rental_id) as rental_count
                                  FROM film f
                                  JOIN inventory i ON f.film_id = i.film_id
                                  JOIN rental r ON i.inventory_id = r.inventory_id
                                  GROUP BY f.film_id, f.title
                                  ORDER BY rental_count DESC
                                  LIMIT 5''',
                'difficulty': 'hard',
                'category': 'complex_aggregation'
            },
            {
                'question': '查找从未被租赁的电影',
                'ground_truth': '''SELECT f.title
                                  FROM film f
                                  LEFT JOIN inventory i ON f.film_id = i.film_id
                                  LEFT JOIN rental r ON i.inventory_id = r.inventory_id
                                  WHERE r.rental_id IS NULL''',
                'difficulty': 'hard',
                'category': 'subquery'
            }
        ]
        
        return basic_cases
    
    def save_test_cases(self, filename: str = 'sakila_test_cases.json'):
        """保存测试用例到文件"""
        test_cases = self.generate_basic_cases()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_cases, f, ensure_ascii=False, indent=2)
        
        logging.info(f"已保存 {len(test_cases)} 个测试用例到 {filename}")
        return test_cases

def run_evaluation_demo():
    """运行评估演示"""
    logging.info("=== Sakila Text2SQL 评估演示 ===")
    
    # 1. 生成测试用例
    generator = SakilaTestCaseGenerator()
    test_cases = generator.save_test_cases()
    
    # 2. 模拟一些预测结果（实际使用时这些会来自你的 Text2SQL 模型）
    predictions = [
        'SELECT first_name, last_name FROM actor',  # 完全正确
        'SELECT COUNT(*) FROM film',  # 完全正确
        'SELECT title FROM film WHERE rating = "PG"',  # 完全正确
        'SELECT title FROM film JOIN film_actor ON film.film_id = film_actor.film_id JOIN actor ON film_actor.actor_id = actor.actor_id WHERE first_name = "John"',  # 结构正确但缺少表别名
        'SELECT category.name, COUNT(*) FROM category JOIN film_category ON category.category_id = film_category.category_id GROUP BY category.name',  # 基本正确但略有差异
        'SELECT film.title, COUNT(rental.rental_id) FROM film JOIN inventory ON film.film_id = inventory.film_id JOIN rental ON inventory.inventory_id = rental.inventory_id GROUP BY film.title ORDER BY COUNT(rental.rental_id) DESC LIMIT 5',  # 基本正确
        'SELECT title FROM film WHERE film_id NOT IN (SELECT DISTINCT film_id FROM inventory JOIN rental ON inventory.inventory_id = rental.inventory_id)'  # 不同的实现方式
    ]
    
    # 3. 准备评估数据
    eval_cases = []
    for i, (case, pred) in enumerate(zip(test_cases, predictions)):
        eval_cases.append({
            'question': case['question'],
            'predicted': pred,
            'ground_truth': case['ground_truth']
        })
    
    # 4. 运行评估
    evaluator = Text2SQLEvaluator()  # 没有数据库连接，只评估文本相似度
    results = evaluator.evaluate_batch(eval_cases)
    
    # 5. 输出结果
    print(f"\n=== 评估结果 ===")
    print(f"总测试用例数: {results['total_cases']}")
    print(f"精确匹配准确率: {results['exact_match_accuracy']:.2%}")
    print(f"Token级别准确率: {results['token_level_accuracy']:.2%}")
    print(f"执行准确率: {results['execution_accuracy']:.2%}")
    
    # 6. 保存详细结果
    with open('evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logging.info("详细评估结果已保存到 evaluation_results.json")
    
    return results

if __name__ == "__main__":
    run_evaluation_demo()