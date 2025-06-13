# Day 4 实践指南：数据库连接与数据源管理 🛠️

## 练习目标

通过今天的实践，你将亲手操作：
- **数据库连接配置**：连接不同类型的数据库
- **数据源创建管理**：创建和配置数据表
- **查询性能优化**：理解缓存和查询优化
- **权限安全实践**：配置数据访问权限
- **多数据库支持**：体验跨数据库查询

## 环境准备

确保你已经完成了前三天的学习，并且：
- Superset 环境正常运行
- 至少有一个数据库可用（SQLite、MySQL、PostgreSQL等）
- 已创建管理员用户

---

## 练习 1：第一个数据库连接 🔌

### 步骤 1：连接 SQLite 数据库（最简单）

SQLite 是最容易开始的数据库，无需额外安装。

1. **以管理员身份登录 Superset**

2. **创建数据库连接**：
   - 访问 **Data → Databases**
   - 点击 **+ DATABASE** 按钮
   - 选择 **SQLite**

3. **配置连接信息**：
   ```
   Host: (留空)
   Port: (留空)
   Database Name: examples
   Username: (留空)
   Password: (留空)
   ```
   
   **SQLAlchemy URI**：
   ```
   sqlite:///path/to/your/database.db
   ```
   
   或者使用内存数据库测试：
   ```
   sqlite:///:memory:
   ```

4. **测试连接**：
   - 点击 **TEST CONNECTION** 按钮
   - 看到 "Connection looks good!" 表示成功

### 步骤 2：创建示例数据（如果使用内存数据库）

如果使用内存数据库，我们需要创建一些示例数据：

1. **访问 SQL Lab**：
   - 点击 **SQL Lab → SQL Editor**
   - 选择刚创建的数据库

2. **创建示例表**：
   ```sql
   -- 创建销售数据表
   CREATE TABLE sales_data (
       id INTEGER PRIMARY KEY,
       product_name TEXT NOT NULL,
       category TEXT NOT NULL,
       sales_amount DECIMAL(10,2),
       sales_date DATE,
       region TEXT,
       sales_rep TEXT
   );
   
   -- 插入示例数据
   INSERT INTO sales_data VALUES
   (1, 'Laptop', 'Electronics', 1200.00, '2023-01-15', 'North', 'Alice'),
   (2, 'Mouse', 'Electronics', 25.00, '2023-01-16', 'South', 'Bob'),
   (3, 'Keyboard', 'Electronics', 75.00, '2023-01-17', 'East', 'Alice'),
   (4, 'Monitor', 'Electronics', 300.00, '2023-01-18', 'West', 'Charlie'),
   (5, 'Desk', 'Furniture', 250.00, '2023-01-19', 'North', 'Bob'),
   (6, 'Chair', 'Furniture', 150.00, '2023-01-20', 'South', 'Alice'),
   (7, 'Tablet', 'Electronics', 400.00, '2023-01-21', 'East', 'Charlie'),
   (8, 'Phone', 'Electronics', 800.00, '2023-01-22', 'West', 'Bob');
   ```

3. **验证数据**：
   ```sql
   SELECT * FROM sales_data LIMIT 5;
   ```

**练习要点**：
- 理解 SQLAlchemy URI 的格式
- 掌握数据库连接测试流程
- 学会在 SQL Lab 中执行 SQL

---

## 练习 2：数据源管理深度实践 📊

### 步骤 1：添加数据表到 Superset

1. **自动发现表**：
   - 访问 **Data → Databases**
   - 点击数据库名称进入详情页面
   - 点击 **Tables** 标签
   - 点击 **+ ADD TABLE** 按钮

2. **手动添加表**：
   - **Table Name**: `sales_data`
   - **Schema**: (如果有的话)
   - 点击 **Save**

### 步骤 2：配置表的列和指标

1. **访问表配置**：
   - **Data → Datasets**
   - 找到 `sales_data` 表，点击编辑

2. **配置列属性**：
   
   **日期列配置**：
   - 找到 `sales_date` 列
   - **Is temporal**: ✅
   - **Datetime Format**: `%Y-%m-%d`
   - **Type**: `DATE`

   **数值列配置**：
   - 找到 `sales_amount` 列
   - **Type**: `NUMERIC`
   - **Is filterable**: ✅
   - **Is groupable**: ✅

   **分类列配置**：
   - `product_name`, `category`, `region`, `sales_rep`
   - **Type**: `STRING`
   - **Is filterable**: ✅
   - **Is groupable**: ✅

3. **创建自定义指标**：
   
   **总销售额**：
   ```sql
   Metric Name: total_sales
   SQL Expression: SUM(sales_amount)
   Metric Type: sum
   ```

   **平均销售额**：
   ```sql
   Metric Name: avg_sales  
   SQL Expression: AVG(sales_amount)
   Metric Type: avg
   ```

   **销售数量**：
   ```sql
   Metric Name: sales_count
   SQL Expression: COUNT(*)
   Metric Type: count
   ```

### 步骤 3：测试数据源查询

1. **访问 Explore 界面**：
   - 在数据集列表中，点击 `sales_data` 的 **Explore** 按钮

2. **创建基础查询**：
   - **Visualization Type**: Table
   - **Dimensions**: `category`, `region`
   - **Metrics**: `total_sales`, `sales_count`
   - 点击 **RUN QUERY**

3. **验证结果**：
   - 查看生成的 SQL（点击 **VIEW QUERY**）
   - 确认数据正确显示

**期望结果**：
```
Category    | Region | Total Sales | Sales Count
Electronics | North  | 1200.00     | 1
Electronics | South  | 25.00       | 1
Electronics | East   | 475.00      | 2
...
```

---

## 练习 3：查询性能优化实践 ⚡

### 步骤 1：理解查询缓存

1. **启用缓存**：
   - 编辑数据库连接
   - 设置 **Cache Timeout**: `300` (5分钟)
   - 保存

2. **测试缓存效果**：
   
   **第一次查询**：
   - 执行一个复杂查询
   - 记录查询时间
   
   **第二次查询**：
   - 执行相同查询
   - 对比查询时间（应该显著更快）

3. **查看缓存状态**：
   - 在查询结果页面查看是否显示 "cached" 标识

### 步骤 2：查询优化技巧

**限制查询行数**：
```sql
-- 在 SQL Lab 中测试
SELECT * FROM sales_data 
ORDER BY sales_amount DESC 
LIMIT 10;
```

**使用聚合减少数据量**：
```sql
-- 而不是返回所有行，使用聚合
SELECT 
    region,
    category,
    SUM(sales_amount) as total_sales,
    COUNT(*) as sales_count
FROM sales_data 
GROUP BY region, category
ORDER BY total_sales DESC;
```

**有效的过滤条件**：
```sql
-- 使用索引友好的过滤条件
SELECT * FROM sales_data 
WHERE sales_date >= '2023-01-15' 
AND category = 'Electronics';
```

### 步骤 3：监控查询性能

1. **查看查询历史**：
   - **SQL Lab → Query History**
   - 查看各查询的执行时间

2. **分析慢查询**：
   - 找出执行时间最长的查询
   - 分析是否可以优化

**性能优化清单**：
- ✅ 适当的缓存设置
- ✅ 限制查询结果行数
- ✅ 使用聚合代替明细数据
- ✅ 高效的过滤条件
- ✅ 避免 `SELECT *`

---

## 练习 4：多数据库连接实践 🌐

### 步骤 1：连接第二个数据库

如果你有多个数据库可用，尝试连接不同类型的数据库：

**PostgreSQL 示例**：
```
Database Name: postgres_db
SQLAlchemy URI: postgresql://username:password@localhost:5432/dbname
```

**MySQL 示例**：
```
Database Name: mysql_db  
SQLAlchemy URI: mysql+pymysql://username:password@localhost:3306/dbname
```

### 步骤 2：跨数据库查询对比

1. **在不同数据库中创建相似的表结构**
2. **对比不同数据库的查询性能**
3. **测试数据库特有的功能**

**PostgreSQL 特有功能测试**：
```sql
-- 时间函数
SELECT 
    DATE_TRUNC('month', sales_date) as month,
    SUM(sales_amount) as monthly_sales
FROM sales_data 
GROUP BY DATE_TRUNC('month', sales_date);
```

**MySQL 特有功能测试**：
```sql
-- 时间函数
SELECT 
    DATE_FORMAT(sales_date, '%Y-%m') as month,
    SUM(sales_amount) as monthly_sales
FROM sales_data 
GROUP BY DATE_FORMAT(sales_date, '%Y-%m');
```

### 步骤 3：数据库引擎差异体验

1. **时间处理差异**：
   - 在不同数据库中测试时间函数
   - 观察 Superset 如何处理差异

2. **数据类型差异**：
   - 测试不同数据库的数据类型支持
   - 观察 Superset 的自动适配

---

## 练习 5：数据安全与权限实践 🔒

### 步骤 1：配置数据库级别权限

1. **创建受限用户**：
   - 创建一个新的 Superset 用户
   - 分配 `Gamma` 角色

2. **配置数据库访问权限**：
   - **Security → List Roles → Gamma**
   - 检查数据库访问权限

3. **测试权限限制**：
   - 以受限用户身份登录
   - 尝试访问不同数据库
   - 验证权限控制效果

### 步骤 2：行级安全模拟

虽然完整的 RLS 需要更复杂的配置，我们可以模拟其效果：

1. **创建用户特定视图**：
   ```sql
   -- 为特定销售代表创建视图
   CREATE VIEW alice_sales AS
   SELECT * FROM sales_data 
   WHERE sales_rep = 'Alice';
   
   CREATE VIEW bob_sales AS  
   SELECT * FROM sales_data
   WHERE sales_rep = 'Bob';
   ```

2. **将不同视图分配给不同用户**：
   - 为不同用户角色配置不同的数据源访问权限

### 步骤 3：敏感数据保护

1. **数据脱敏示例**：
   ```sql
   -- 创建脱敏视图
   CREATE VIEW sales_data_masked AS
   SELECT 
       id,
       product_name,
       category,
       -- 脱敏销售额（只显示范围）
       CASE 
           WHEN sales_amount < 100 THEN '< 100'
           WHEN sales_amount < 500 THEN '100-500'
           WHEN sales_amount < 1000 THEN '500-1000'
           ELSE '> 1000'
       END as sales_range,
       sales_date,
       region,
       -- 脱敏销售代表姓名
       SUBSTR(sales_rep, 1, 1) || '***' as sales_rep_masked
   FROM sales_data;
   ```

2. **配置敏感数据访问**：
   - 为不同角色用户配置不同的数据视图访问权限

---

## 练习 6：高级数据源配置 🔧

### 步骤 1：虚拟数据集创建

1. **基于 SQL 的虚拟数据集**：
   - **Data → Datasets → + DATASET**
   - **Database**: 选择数据库
   - **SQL**: 输入复杂查询
   ```sql
   SELECT 
       category,
       region,
       DATE_TRUNC('month', sales_date) as sales_month,
       SUM(sales_amount) as monthly_sales,
       COUNT(*) as transaction_count,
       AVG(sales_amount) as avg_transaction
   FROM sales_data
   WHERE sales_date >= '2023-01-01'
   GROUP BY category, region, DATE_TRUNC('month', sales_date)
   ```

2. **配置虚拟数据集**：
   - **Dataset Name**: `monthly_sales_summary`
   - 配置列属性和指标

### 步骤 2：模板参数使用

1. **带参数的 SQL**：
   ```sql
   SELECT * FROM sales_data 
   WHERE sales_date >= '{{ from_dttm }}'
   AND sales_date < '{{ to_dttm }}'
   {% if filter_values('region') %}
   AND region IN ({{ filter_values('region')|join(',') }})
   {% endif %}
   ```

2. **测试模板参数**：
   - 在 Explore 界面中使用时间过滤器
   - 验证 SQL 模板的动态生成

### 步骤 3：数据刷新策略

1. **配置自动刷新**：
   - 编辑数据集
   - 设置 **Cache Timeout**
   - 配置 **Offset**

2. **手动刷新数据**：
   - 理解何时需要刷新元数据
   - 测试数据变更后的同步

---

## 思考题 🤔

### 基础理解题

1. **连接字符串题**：请解释以下 SQLAlchemy URI 的各个部分：
   ```
   postgresql://user:pass@localhost:5432/mydb?sslmode=require
   ```

2. **缓存策略题**：在什么情况下应该使用长缓存时间？什么情况下应该禁用缓存？

3. **数据类型题**：Superset 如何处理不同数据库的数据类型差异？

### 高级应用题

4. **性能优化题**：对于一个包含千万级数据的表，如何优化 Superset 的查询性能？

5. **安全架构题**：如何设计一个支持多租户的 Superset 数据访问权限架构？

6. **扩展性题**：如何为 Superset 添加对新数据库（如 ClickHouse）的支持？

---

## 深入练习（可选）🚀

### 1. 自定义数据库引擎

```python
# 尝试理解和修改数据库引擎规范
# 查看 superset/db_engine_specs/ 目录下的文件
```

### 2. 查询性能分析

```bash
# 启用查询日志，分析慢查询
# 研究不同查询模式的性能差异
```

### 3. 缓存系统深入

```python
# 研究 Superset 缓存机制的实现
# 尝试配置 Redis 缓存
```

### 4. 安全增强配置

```python
# 配置数据库连接的 SSL
# 实现更复杂的行级安全规则
```

---

## 成果验证 ✅

完成今天的练习后，你应该能够：

### 技能掌握
- [x] 熟练连接和配置多种数据库
- [x] 创建和管理数据源及其元数据
- [x] 优化查询性能和缓存策略
- [x] 配置数据访问安全权限

### 理论理解
- [x] 深度理解数据库抽象层设计
- [x] 掌握查询执行和优化原理
- [x] 理解缓存机制的工作方式
- [x] 知晓数据安全的最佳实践

### 实际应用
- [x] 能够为生产环境配置数据库连接
- [x] 具备查询性能调优能力
- [x] 掌握数据安全配置技能
- [x] 理解多数据库环境的管理

**恭喜你完成第四天的学习！** 🎉

现在你已经深入理解了 Superset 的数据层架构，掌握了从数据库连接到查询优化的完整技能链。这为你构建高性能、安全的数据分析平台奠定了坚实基础！ 