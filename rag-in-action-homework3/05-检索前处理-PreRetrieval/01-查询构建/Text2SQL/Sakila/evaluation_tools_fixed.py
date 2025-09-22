# evaluation_tools_fixed.py - 评估工具集合（无外部依赖版本）
import json
import sqlite3
from typing import List, Dict
from collections import Counter

class Text2SQLMetrics:
    """Text2SQL 专用评估指标"""
    
    @staticmethod
    def component_accuracy(predicted: str, ground_truth: str) -> Dict[str, float]:
        """SQL 组件级别准确率分析"""
        def extract_components(sql: str) -> Dict[str, List[str]]:
            sql = sql.lower().strip()
            components = {
                'select': [],
                'from': [],
                'where': [],
                'join': [],
                'group_by': [],
                'order_by': [],
                'having': [],
                'limit': []
            }
            
            # 简单的 SQL 解析（实际项目中建议使用 sqlparse）
            if 'select' in sql:
                select_part = sql.split('from')[0].replace('select', '').strip()
                components['select'] = [col.strip() for col in select_part.split(',')]
            
            if 'from' in sql:
                from_part = sql.split('from')[1].split('where')[0] if 'where' in sql else sql.split('from')[1]
                from_part = from_part.split('join')[0] if 'join' in sql else from_part
                from_part = from_part.split('group by')[0] if 'group by' in sql else from_part
                from_part = from_part.split('order by')[0] if 'order by' in sql else from_part
                components['from'] = [table.strip() for table in from_part.split(',')]
            
            return components
        
        pred_components = extract_components(predicted)
        gt_components = extract_components(ground_truth)
        
        accuracies = {}
        for component in pred_components:
            pred_set = set(pred_components[component])
            gt_set = set(gt_components[component])
            
            if not gt_set:
                accuracies[component] = 1.0 if not pred_set else 0.0
            else:
                intersection = len(pred_set & gt_set)
                union = len(pred_set | gt_set)
                accuracies[component] = intersection / union if union > 0 else 0.0
        
        return accuracies
    
    @staticmethod
    def difficulty_based_evaluation(results: List[Dict], test_cases: List[Dict]) -> Dict:
        """基于难度的评估分析"""
        difficulty_results = {'easy': [], 'medium': [], 'hard': []}
        
        for result, case in zip(results, test_cases):
            difficulty = case.get('difficulty', 'unknown')
            if difficulty in difficulty_results:
                difficulty_results[difficulty].append(result)
        
        summary = {}
        for difficulty, cases in difficulty_results.items():
            if cases:
                summary[difficulty] = {
                    'count': len(cases),
                    'exact_match': sum(c['exact_match'] for c in cases) / len(cases),
                    'token_accuracy': sum(c['token_accuracy'] for c in cases) / len(cases),
                    'execution_accuracy': sum(c['execution_accuracy'] for c in cases) / len(cases)
                }
        
        return summary

class EvaluationVisualizer:
    """评估结果可视化 - 简化版（文本输出）"""
    
    @staticmethod
    def print_accuracy_by_difficulty(difficulty_results: Dict):
        """打印按难度分组的准确率"""
        print("\n=== 按难度级别的准确率分析 ===")
        for difficulty, stats in difficulty_results.items():
            print(f"\n{difficulty.upper()} 级别:")
            print(f"  测试用例数: {stats['count']}")
            print(f"  精确匹配: {stats['exact_match']:.2%}")
            print(f"  Token准确率: {stats['token_accuracy']:.2%}")
            print(f"  执行准确率: {stats['execution_accuracy']:.2%}")
    
    @staticmethod
    def print_error_analysis(results: List[Dict]):
        """打印错误分析"""
        print("\n=== 错误分析 ===")
        
        total = len(results)
        exact_match_correct = sum(1 for r in results if r['exact_match'] == 1)
        execution_correct = sum(1 for r in results if r['execution_accuracy'] == 1)
        
        print(f"总测试用例: {total}")
        print(f"精确匹配正确: {exact_match_correct} ({exact_match_correct/total:.1%})")
        print(f"执行结果正确: {execution_correct} ({execution_correct/total:.1%})")
        
        # Token准确率分布
        token_accuracies = [r['token_accuracy'] for r in results]
        avg_token_acc = sum(token_accuracies) / len(token_accuracies)
        min_token_acc = min(token_accuracies)
        max_token_acc = max(token_accuracies)
        
        print(f"\nToken准确率统计:")
        print(f"  平均值: {avg_token_acc:.2%}")
        print(f"  最小值: {min_token_acc:.2%}")
        print(f"  最大值: {max_token_acc:.2%}")

class BenchmarkComparison:
    """基准测试比较"""
    
    def __init__(self):
        self.benchmarks = {}
    
    def add_benchmark(self, name: str, results: Dict):
        """添加基准测试结果"""
        self.benchmarks[name] = results
    
    def compare_models(self):
        """比较不同模型的性能 - 文本输出版"""
        if len(self.benchmarks) < 2:
            print("需要至少两个模型进行比较")
            return
        
        print("\n=== 模型性能对比 ===")
        models = list(self.benchmarks.keys())
        metrics = ['exact_match_accuracy', 'token_level_accuracy', 'execution_accuracy']
        metric_names = ['精确匹配准确率', 'Token级别准确率', '执行准确率']
        
        # 打印表头
        print(f"{'指标':<15}", end="")
        for model in models:
            print(f"{model:<15}", end="")
        print()
        print("-" * (15 + 15 * len(models)))
        
        # 打印各项指标
        for metric, name in zip(metrics, metric_names):
            print(f"{name:<15}", end="")
            for model in models:
                value = self.benchmarks[model][metric]
                print(f"{value:<15.3f}", end="")
            print()
        
        # 找出最佳模型
        print(f"\n最佳模型分析:")
        for metric, name in zip(metrics, metric_names):
            best_model = max(models, key=lambda m: self.benchmarks[m][metric])
            best_score = self.benchmarks[best_model][metric]
            print(f"  {name}: {best_model} ({best_score:.3f})")
    
    def generate_report(self, save_path: str = 'evaluation_report.html'):
        """生成 HTML 评估报告"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Text2SQL Evaluation Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; }
                .metric { font-weight: bold; color: #2c3e50; }
                .score { color: #27ae60; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>Text2SQL Evaluation Report</h1>
        """
        
        for model_name, results in self.benchmarks.items():
            html_content += f"""
            <h2>{model_name}</h2>
            <table>
                <tr><th>Metric</th><th>Score</th></tr>
                <tr><td class="metric">Exact Match Accuracy</td><td class="score">{results['exact_match_accuracy']:.3f}</td></tr>
                <tr><td class="metric">Token Level Accuracy</td><td class="score">{results['token_level_accuracy']:.3f}</td></tr>
                <tr><td class="metric">Execution Accuracy</td><td class="score">{results['execution_accuracy']:.3f}</td></tr>
                <tr><td class="metric">Total Test Cases</td><td>{results['total_cases']}</td></tr>
            </table>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"评估报告已保存到 {save_path}")

# 使用示例
def create_comprehensive_evaluation():
    """创建综合评估示例"""
    try:
        from evaluation_framework import Text2SQLEvaluator, SakilaTestCaseGenerator
    except ImportError:
        print("无法导入 evaluation_framework，请确保文件在同一目录下")
        return
    
    # 1. 生成测试用例
    generator = SakilaTestCaseGenerator()
    test_cases = generator.generate_basic_cases()
    
    # 2. 运行评估
    evaluator = Text2SQLEvaluator()
    
    # 模拟两个不同模型的结果
    model1_predictions = [
        'SELECT first_name, last_name FROM actor',
        'SELECT COUNT(*) FROM film',
        'SELECT title FROM film WHERE rating = "PG"',
        'SELECT f.title FROM film f JOIN film_actor fa ON f.film_id = fa.film_id JOIN actor a ON fa.actor_id = a.actor_id WHERE a.first_name = "John"',
        'SELECT c.name, COUNT(fc.film_id) FROM category c LEFT JOIN film_category fc ON c.category_id = fc.category_id GROUP BY c.name',
        'SELECT f.title, COUNT(r.rental_id) FROM film f JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY f.title ORDER BY COUNT(r.rental_id) DESC LIMIT 5',
        'SELECT f.title FROM film f LEFT JOIN inventory i ON f.film_id = i.film_id LEFT JOIN rental r ON i.inventory_id = r.inventory_id WHERE r.rental_id IS NULL'
    ]
    
    model2_predictions = [
        'SELECT first_name, last_name FROM actor',
        'SELECT COUNT(*) FROM film',
        'SELECT title FROM film WHERE rating = "PG"',
        'SELECT title FROM film WHERE film_id IN (SELECT film_id FROM film_actor WHERE actor_id IN (SELECT actor_id FROM actor WHERE first_name = "John"))',
        'SELECT category.name, COUNT(*) FROM category JOIN film_category ON category.category_id = film_category.category_id GROUP BY category.name',
        'SELECT film.title FROM film JOIN inventory ON film.film_id = inventory.film_id JOIN rental ON inventory.inventory_id = rental.inventory_id GROUP BY film.title ORDER BY COUNT(*) DESC LIMIT 5',
        'SELECT title FROM film WHERE film_id NOT IN (SELECT DISTINCT film_id FROM inventory JOIN rental ON inventory.inventory_id = rental.inventory_id WHERE rental.rental_id IS NOT NULL)'
    ]
    
    # 评估两个模型
    eval_cases1 = [{'question': tc['question'], 'predicted': pred, 'ground_truth': tc['ground_truth']} 
                   for tc, pred in zip(test_cases, model1_predictions)]
    eval_cases2 = [{'question': tc['question'], 'predicted': pred, 'ground_truth': tc['ground_truth']} 
                   for tc, pred in zip(test_cases, model2_predictions)]
    
    results1 = evaluator.evaluate_batch(eval_cases1)
    results2 = evaluator.evaluate_batch(eval_cases2)
    
    # 3. 高级分析
    print("=== 模型1 (JOIN-based) 分析 ===")
    
    # 难度分析
    difficulty_results1 = Text2SQLMetrics.difficulty_based_evaluation(results1['detailed_results'], test_cases)
    visualizer = EvaluationVisualizer()
    visualizer.print_accuracy_by_difficulty(difficulty_results1)
    
    # 错误分析
    visualizer.print_error_analysis(results1['detailed_results'])
    
    # 模型比较
    benchmark = BenchmarkComparison()
    benchmark.add_benchmark('Model 1 (Join-based)', results1)
    benchmark.add_benchmark('Model 2 (Subquery-based)', results2)
    benchmark.compare_models()
    benchmark.generate_report()
    
    return results1, results2

def test_evaluation_tools():
    """测试评估工具功能"""
    print("=== 评估工具测试 ===")
    
    # 测试组件准确率
    predicted = "SELECT first_name, last_name FROM actor WHERE actor_id = 1"
    ground_truth = "SELECT first_name, last_name FROM actor WHERE actor_id = 1"
    
    component_acc = Text2SQLMetrics.component_accuracy(predicted, ground_truth)
    print("组件准确率测试:")
    for component, acc in component_acc.items():
        if acc > 0:
            print(f"  {component}: {acc:.2f}")
    
    # 测试模拟数据
    mock_results = [
        {'exact_match': 1, 'token_accuracy': 1.0, 'execution_accuracy': 1},
        {'exact_match': 0, 'token_accuracy': 0.8, 'execution_accuracy': 0},
        {'exact_match': 1, 'token_accuracy': 1.0, 'execution_accuracy': 1}
    ]
    
    mock_test_cases = [
        {'difficulty': 'easy'},
        {'difficulty': 'medium'},
        {'difficulty': 'easy'}
    ]
    
    difficulty_results = Text2SQLMetrics.difficulty_based_evaluation(mock_results, mock_test_cases)
    
    visualizer = EvaluationVisualizer()
    visualizer.print_accuracy_by_difficulty(difficulty_results)
    visualizer.print_error_analysis(mock_results)

if __name__ == "__main__":
    test_evaluation_tools()