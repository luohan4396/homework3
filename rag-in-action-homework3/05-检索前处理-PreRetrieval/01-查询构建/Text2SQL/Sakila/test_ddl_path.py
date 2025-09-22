# test_ddl_path.py - 测试DDL文件路径
import os

# 获取当前脚本目录
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"当前脚本目录: {script_dir}")

# 计算DDL文件路径
ddl_path1 = os.path.join(os.path.dirname(script_dir), "..", "..", "..", "..", "90-文档-Data", "sakila", "ddl_statements.yaml")
ddl_path1 = os.path.normpath(ddl_path1)
print(f"计算的DDL路径1: {ddl_path1}")
print(f"路径1是否存在: {os.path.exists(ddl_path1)}")

# 尝试另一种路径计算方式
current_dir = os.getcwd()
print(f"当前工作目录: {current_dir}")

ddl_path2 = os.path.join(current_dir, "90-文档-Data", "sakila", "ddl_statements.yaml")
print(f"计算的DDL路径2: {ddl_path2}")
print(f"路径2是否存在: {os.path.exists(ddl_path2)}")

# 直接检查已知存在的文件
known_path = "90-文档-Data/sakila/ddl_statements.yaml"
print(f"已知路径: {known_path}")
print(f"已知路径是否存在: {os.path.exists(known_path)}")

# 列出90-文档-Data目录
data_dir = "90-文档-Data"
if os.path.exists(data_dir):
    print(f"\n{data_dir} 目录内容:")
    for item in os.listdir(data_dir):
        print(f"  {item}")
        
    sakila_dir = os.path.join(data_dir, "sakila")
    if os.path.exists(sakila_dir):
        print(f"\n{sakila_dir} 目录内容:")
        for item in os.listdir(sakila_dir):
            print(f"  {item}")
else:
    print(f"{data_dir} 目录不存在")