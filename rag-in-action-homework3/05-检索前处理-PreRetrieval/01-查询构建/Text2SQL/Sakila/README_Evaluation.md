# Sakila Text2SQL 评估体系

## 概述

本评估体系为 Sakila 数据库的 Text2SQL 任务提供了完整的评估工具和基准测试框架。

## 推荐的评估工具组合

### 1. 核心评估工具

#### A. 评估指标
- **精确匹配 (Exact Match)**: SQL 语句完全匹配
- **Token 级别准确率**: 基于 token 的相似度评分
- **执行准确率**: SQL 执行结果的正确性
- **组件准确率**: SELECT、FROM、WHERE 等 SQL 组件的准确性

#### B. 评估维度
- **难度分级**: Easy、Medium、Hard
- **查询类型**: 基础查询、聚合、连接、子查询等
- **错误分析**: 语法错误、逻辑错误、执行错误

### 2. 工具文件说明

#### `evaluation_framework.py`
- **Text2SQLEvaluator**: 核心评估器
- **SakilaTestCaseGenerator**: 测试用例生成器
- **功能**: 批量评估、指标计算、结果保存

#### `evaluation_tools.py`
- **Text2SQLMetrics**: 专用评估指标
- **EvaluationVisualizer**: 结果可视化
- **BenchmarkComparison**: 模型性能比较

#### `test_ddl_search.py`
- DDL 向量搜索功能测试
- 验证知识库构建是否成功

## 使用方法

### 1. 基础评估

```python
from evaluation_framework import Text2SQLEvaluator, SakilaTestCaseGenerator

# 生成测试用例
generator = SakilaTestCaseGenerator()
test_cases = generator.generate_basic_cases()

# 准备你的模型预测结果
predictions = [
    "SELECT first_name, last_name FROM actor",
    "SELECT COUNT(*) FROM film",
    # ... 更多预测结果
]

# 运行评估
evaluator = Text2SQLEvaluator()
eval_cases = [
    {
        'question': case['question'],
        'predicted': pred,
        'ground_truth': case['ground_truth']
    }
    for case, pred in zip(test_cases, predictions)
]

results = evaluator.evaluate_batch(eval_cases)
print(f"精确匹配准确率: {results['exact_match_accuracy']:.2%}")
```

### 2. 高级评估和可视化

```python
from evaluation_tools import Text2SQLMetrics, EvaluationVisualizer, BenchmarkComparison

# 难度分析
difficulty_results = Text2SQLMetrics.difficulty_based_evaluation(
    results['detailed_results'], test_cases
)

# 可视化
visualizer = EvaluationVisualizer()
visualizer.plot_accuracy_by_difficulty(difficulty_results)
visualizer.plot_error_analysis(results['detailed_results'])

# 模型比较
benchmark = BenchmarkComparison()
benchmark.add_benchmark('Model A', results_a)
benchmark.add_benchmark('Model B', results_b)
benchmark.compare_models()
benchmark.generate_report()
```

### 3. 数据库连接评估

如果你有 Sakila 数据库，可以启用执行准确率评估：

```python
# 连接到 Sakila 数据库
evaluator = Text2SQLEvaluator(db_path='sakila.db')
results = evaluator.evaluate_batch(eval_cases)
```

## 评估指标详解

### 1. 精确匹配 (Exact Match)
- **定义**: 预测的 SQL 与标准答案完全一致（忽略大小写和空格）
- **优点**: 严格、无歧义
- **缺点**: 可能过于严格，不同但等价的 SQL 会被判错

### 2. Token 级别准确率
- **定义**: 基于 token 序列的相似度计算
- **算法**: 使用 SequenceMatcher 计算相似度比例
- **优点**: 对语法变化更宽容
- **缺点**: 可能给语义错误的 SQL 高分

### 3. 执行准确率
- **定义**: 执行 SQL 并比较结果集
- **优点**: 最能反映实际效果
- **缺点**: 需要数据库连接，计算开销大

### 4. 组件准确率
- **定义**: 分别评估 SELECT、FROM、WHERE 等组件
- **优点**: 提供细粒度的错误分析
- **用途**: 帮助识别模型的薄弱环节

## 测试用例分类

### Easy (简单)
- 基础 SELECT 查询
- 简单 WHERE 条件
- COUNT 等基础聚合

### Medium (中等)
- JOIN 查询
- GROUP BY 聚合
- 多表查询

### Hard (困难)
- 复杂子查询
- 多层嵌套
- 窗口函数

## 基准测试建议

### 1. 内部基准
- 使用生成的 Sakila 测试用例
- 定期评估模型性能
- 跟踪改进进度

### 2. 外部基准
- **Spider**: 跨域 Text2SQL 基准
- **WikiSQL**: 单表查询基准
- **CoSQL**: 对话式 SQL 基准

### 3. 评估频率
- **开发阶段**: 每次模型更新后
- **实验阶段**: 每个实验配置
- **生产阶段**: 定期监控

## 错误分析指南

### 1. 常见错误类型
- **语法错误**: SQL 语法不正确
- **表名错误**: 使用了不存在的表名
- **列名错误**: 使用了不存在的列名
- **逻辑错误**: 语法正确但逻辑错误
- **连接错误**: JOIN 条件不正确

### 2. 改进建议
- **语法错误** → 改进 SQL 生成模板
- **表名/列名错误** → 增强 schema 理解
- **逻辑错误** → 改进语义理解
- **连接错误** → 增强关系推理

## 扩展建议

### 1. 添加更多测试用例
```python
# 在 SakilaTestCaseGenerator 中添加
def generate_advanced_cases(self):
    return [
        {
            'question': '查找每个演员参演电影的平均租赁价格',
            'ground_truth': '''SELECT a.first_name, a.last_name, AVG(f.rental_rate)
                              FROM actor a
                              JOIN film_actor fa ON a.actor_id = fa.actor_id
                              JOIN film f ON fa.film_id = f.film_id
                              GROUP BY a.actor_id''',
            'difficulty': 'hard',
            'category': 'complex_aggregation'
        }
    ]
```

### 2. 集成更多评估指标
- BLEU 分数
- ROUGE 分数
- 语义相似度

### 3. 自动化评估流程
- CI/CD 集成
- 自动报告生成
- 性能回归检测

## 文件结构

```
Sakila/
├── evaluation_framework.py     # 核心评估框架
├── evaluation_tools.py         # 高级评估工具
├── test_ddl_search.py         # DDL 搜索测试
├── sakila_test_cases.json     # 测试用例
├── evaluation_results.json    # 评估结果
├── ddl_embedding_model.pkl    # DDL 嵌入模型
├── ddl_faiss_index.bin       # FAISS 向量索引
├── ddl_metadata.json         # 元数据
└── README_Evaluation.md      # 本文档
```

## 总结

这个评估体系提供了：
1. **完整的评估指标**: 从语法到语义的多维度评估
2. **灵活的测试框架**: 支持自定义测试用例和评估标准
3. **可视化分析**: 直观的性能分析和错误诊断
4. **基准比较**: 多模型性能对比
5. **扩展性**: 易于添加新的评估指标和测试用例

建议根据具体需求选择合适的评估工具组合，并定期更新测试用例以保持评估的有效性。