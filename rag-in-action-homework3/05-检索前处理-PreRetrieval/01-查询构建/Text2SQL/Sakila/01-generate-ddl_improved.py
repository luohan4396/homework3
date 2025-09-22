# generate_ddl_yaml.py - 改进版本
import os
import yaml
import pymysql
from dotenv import load_dotenv

# 1. 加载 .env 中的数据库配置
load_dotenv()  

# 从环境变量读取配置
host = os.getenv("MYSQL_HOST", "localhost")
port = int(os.getenv("MYSQL_PORT", "3306"))
user = os.getenv("MYSQL_USER", "root")
password = os.getenv("MYSQL_PASSWORD")
db_name = os.getenv("MYSQL_DATABASE", "sakila")

# 检查必要的配置
if not password:
    print("错误：未找到 MYSQL_PASSWORD 环境变量")
    print("\n请在 .env 文件中设置以下配置：")
    print("MYSQL_HOST=localhost")
    print("MYSQL_PORT=3306")
    print("MYSQL_USER=root")
    print("MYSQL_PASSWORD=your_mysql_password")
    print("MYSQL_DATABASE=sakila")
    exit(1)

print(f"连接配置：")
print(f"  主机: {host}:{port}")
print(f"  用户: {user}")
print(f"  数据库: {db_name}")

# 2. 连接 MySQL
try:
    print("正在连接 MySQL...")
    conn = pymysql.connect(
        host=host, 
        port=port, 
        user=user, 
        password=password,
        database=db_name, 
        cursorclass=pymysql.cursors.Cursor
    )
    print("✓ MySQL 连接成功")
except pymysql.Error as e:
    print(f"✗ MySQL 连接失败: {e}")
    print("\n请检查：")
    print("1. MySQL 服务是否启动")
    print("2. 数据库配置是否正确")
    print("3. sakila 数据库是否存在")
    exit(1)

ddl_map = {}
try:
    with conn.cursor() as cursor:
        # 3. 检查数据库是否存在
        cursor.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s", (db_name,))
        if not cursor.fetchone():
            print(f"✗ 数据库 '{db_name}' 不存在")
            print("请先创建 sakila 数据库或导入 sakila 示例数据")
            exit(1)
        
        # 4. 获取所有表名
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = %s ORDER BY table_name;", (db_name,)
        )  
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print(f"✗ 数据库 '{db_name}' 中没有找到任何表")
            exit(1)
        
        print(f"找到 {len(tables)} 个表: {', '.join(tables)}")

        # 5. 遍历表列表，执行 SHOW CREATE TABLE
        for i, tbl in enumerate(tables, 1):
            print(f"正在处理表 {i}/{len(tables)}: {tbl}")
            cursor.execute(f"SHOW CREATE TABLE `{db_name}`.`{tbl}`;")
            result = cursor.fetchone()
            # result[0]=表名, result[1]=完整 DDL
            ddl_map[tbl] = result[1]

except pymysql.Error as e:
    print(f"✗ 数据库操作失败: {e}")
    exit(1)
finally:
    conn.close()
    print("数据库连接已关闭")

# 6. 确保输出目录存在
output_dir = "90-文档-Data/sakila"
os.makedirs(output_dir, exist_ok=True)

# 7. 写入 YAML 文件
output_file = os.path.join(output_dir, "ddl_statements.yaml")
try:
    with open(output_file, "w", encoding='utf-8') as f:
        yaml.safe_dump(ddl_map, f, sort_keys=True, allow_unicode=True, default_flow_style=False)
    print(f"✅ {output_file} 已生成")
    print(f"共包含 {len(ddl_map)} 个表: {', '.join(sorted(ddl_map.keys()))}")
except Exception as e:
    print(f"✗ 写入文件失败: {e}")
    exit(1)