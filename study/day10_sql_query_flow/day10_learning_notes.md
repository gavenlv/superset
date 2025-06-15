# Day 10: Superset SQL查询完整流程深度分析

## 学习目标
- 理解Superset中SQL查询的完整生命周期
- 掌握从用户界面到数据库执行的全链路调用
- 分析图表查询和SQL Lab查询的不同路径
- 精确定位每个步骤涉及的类和方法

## 1. SQL查询流程概览

Superset中有两种主要的SQL查询方式：
1. **图表查询 (Chart Query)**: 通过Explore界面或Dashboard触发
2. **SQL Lab查询**: 通过SQL Lab界面直接执行SQL

### 1.1 流程分类

```
用户触发查询
├── 图表查询 (Chart Data API)
│   ├── 前端构建QueryContext
│   ├── 后端解析FormData
│   ├── 生成SQL语句
│   └── 执行并返回结果
└── SQL Lab查询 (SQL Lab API)
    ├── 前端发送SQL语句
    ├── 后端创建Query对象
    ├── 执行SQL语句
    └── 返回结果集
```

## 2. 图表查询完整流程

### 2.1 前端发起查询

**类**: `ChartDataRestApi` (superset/charts/data/api.py)
**方法**: `data()` -> `post()`

```python
@api.expose("/data", methods=("POST",))
@protect()
@statsd_metrics
@event_logger.log_this_with_context()
def data(self) -> Response:
    """
    Takes a query context constructed in the client and returns payload
    data response for the given query.
    """
```

### 2.2 构建查询上下文

**类**: `ChartDataQueryContextSchema`
**方法**: `load()`

```python
def _create_query_context_from_form(self, form_data: dict[str, Any]) -> QueryContext:
    """
    Create the query context from the form data.
    """
    try:
        return ChartDataQueryContextSchema().load(form_data)
    except KeyError as ex:
        raise ValidationError("Request is incorrect") from ex
```

### 2.3 查询上下文处理

**类**: `QueryContext` (superset/common/query_context.py)
**关键方法**:
- `get_query_result()`: 获取查询结果
- `get_df_payload()`: 获取DataFrame payload

### 2.4 数据集查询

**类**: `SqlaTable` (superset/connectors/sqla/models.py)
**方法**: `query(query_obj: QueryObjectDict) -> QueryResult`

```python
def query(self, query_obj: QueryObjectDict) -> QueryResult:
    """Executes the query and returns a dataframe"""
    qry_start_dttm = datetime.now()
    
    # 构建SQL查询
    sql = self.get_query_str_extended(query_obj).sql
    
    # 执行查询
    try:
        df = self.database.get_df(
            sql,
            self.catalog,
            self.schema or None,
            mutator=assign_column_label,
        )
    except Exception as ex:
        # 错误处理
        pass
    
    return QueryResult(
        status=status,
        df=df,
        duration=datetime.now() - qry_start_dttm,
        query=sql,
        errors=errors,
        error_message=error_message,
    )
```

### 2.5 数据库连接与执行

**类**: `Database` (superset/models/core.py)
**方法**: `get_df()`

```python
def get_df(self, sql: str, catalog: str | None = None, schema: str | None = None) -> pd.DataFrame:
    """Execute SQL and return DataFrame"""
    sqls = self.db_engine_spec.parse_sql(sql)
    
    with self.get_raw_connection(catalog=catalog, schema=schema) as conn:
        cursor = conn.cursor()
        
        for i, sql_ in enumerate(sqls):
            sql_ = self.mutate_sql_based_on_config(sql_, is_split=True)
            
            # 执行SQL
            self.db_engine_spec.execute(cursor, sql_, self)
            
            if i < len(sqls) - 1:
                cursor.fetchall()
            else:
                # 最后一个查询，获取结果
                data = self.db_engine_spec.fetch_data(cursor)
                result_set = SupersetResultSet(
                    data, cursor.description, self.db_engine_spec
                )
                df = result_set.to_pandas_df()
    
    return self.post_process_df(df)
```

## 3. SQL Lab查询完整流程

### 3.1 前端发起查询

**前端文件**: `superset-frontend/src/SqlLab/actions/sqlLab.js`
**方法**: `runQuery(query)`

```javascript
export function runQuery(query) {
  return function (dispatch) {
    dispatch(startQuery(query));
    const postPayload = {
      client_id: query.id,
      database_id: query.dbId,
      json: true,
      runAsync: query.runAsync,
      catalog: query.catalog,
      schema: query.schema,
      sql: query.sql,
      sql_editor_id: query.sqlEditorId,
      // ... 其他参数
    };

    return SupersetClient.post({
      endpoint: `/api/v1/sqllab/execute/${search}`,
      body: JSON.stringify(postPayload),
      headers: { 'Content-Type': 'application/json' },
      parseMethod: 'json-bigint',
    })
    .then(({ json }) => {
      if (!query.runAsync) {
        dispatch(querySuccess(query, json));
      }
    });
  };
}
```

### 3.2 后端API接收

**类**: `SqlLabRestApi` (superset/sqllab/api.py)
**方法**: `execute_sql_query()`

```python
@expose("/execute/", methods=("POST",))
@protect()
@statsd_metrics
@requires_json
def execute_sql_query(self) -> FlaskResponse:
    """Execute a SQL query"""
    try:
        execution_context = SqlJsonExecutionContext(request.json)
        command = self._create_sql_json_command(execution_context, log_params)
        command_result: CommandResult = command.run()
        
        response_status = (
            202 if command_result["status"] == SqlJsonExecutionStatus.QUERY_IS_RUNNING
            else 200
        )
        return json_success(command_result["payload"], response_status)
    except SqlLabException as ex:
        payload = {"errors": [ex.to_dict()]}
        return self.response(response_status, **payload)
```

### 3.3 执行命令处理

**类**: `ExecuteSqlCommand` (superset/commands/sql_lab/execute.py)
**方法**: `run()`

```python
@transaction()
def run(self) -> CommandResult:
    """Runs arbitrary sql and returns data as json"""
    try:
        query = self._try_get_existing_query()
        if self.is_query_handled(query):
            self._execution_context.set_query(query)
            status = SqlJsonExecutionStatus.QUERY_ALREADY_CREATED
        else:
            status = self._run_sql_json_exec_from_scratch()

        self._execution_context_convertor.set_payload(
            self._execution_context, status
        )
        
        return {
            "status": status,
            "payload": self._execution_context_convertor.serialize_payload(),
        }
    except Exception as ex:
        raise SqlLabException(self._execution_context, exception=ex) from ex
```

### 3.4 SQL执行核心

**类**: `SqlJsonExecutor`
**方法**: `execute()`

同步执行或异步执行，最终都会调用：

**函数**: `execute_sql_statements()` (superset/sql_lab.py)

```python
def execute_sql_statements(
    query_id: int,
    rendered_query: str,
    return_results: bool,
    store_results: bool,
    start_time: Optional[float],
    expand_data: bool,
    log_params: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """Executes the sql query returns the results."""
    
    query = get_query(query_id)
    database = query.database
    db_engine_spec = database.db_engine_spec
    
    # 解析SQL语句
    parsed_query = ParsedQuery(rendered_query, engine=db_engine_spec.engine)
    statements = parsed_query.get_statements()
    
    # 设置查询状态为运行中
    query.status = QueryStatus.RUNNING
    query.start_running_time = now_as_float()
    db.session.commit()
    
    # 执行每个SQL语句
    with database.get_raw_connection(catalog=query.catalog, schema=query.schema) as conn:
        cursor = conn.cursor()
        
        for i, statement in enumerate(statements):
            result_set = execute_sql_statement(
                statement, query, cursor, log_params, apply_ctas
            )
    
    # 构建返回结果
    payload.update({
        "status": QueryStatus.SUCCESS,
        "data": data,
        "columns": all_columns,
        "query": query.to_dict(),
    })
    
    return payload
```

### 3.5 单个SQL语句执行

**函数**: `execute_sql_statement()` (superset/sql_lab.py)

```python
def execute_sql_statement(
    sql_statement: str,
    query: Query,
    cursor: Any,
    log_params: Optional[dict[str, Any]],
    apply_ctas: bool = False,
) -> SupersetResultSet:
    """Executes a single SQL statement"""
    
    database: Database = query.database
    db_engine_spec = database.db_engine_spec
    
    # 解析和处理SQL
    parsed_query = ParsedQuery(sql_statement, engine=db_engine_spec.engine)
    sql = parsed_query.stripped()
    
    # 应用限制和安全检查
    if not database.allow_dml:
        # DML检查
        pass
    
    # 应用LIMIT
    if db_engine_spec.is_select_query(parsed_query):
        sql = apply_limit_if_exists(database, increased_limit, query, sql)
    
    # 执行SQL
    try:
        query.executed_sql = sql
        
        with event_logger.log_context(action="execute_sql", database=database):
            # 执行查询
            db_engine_spec.execute_with_cursor(cursor, sql, query)
            
            # 获取数据
            data = db_engine_spec.fetch_data(cursor, increased_limit)
    
    except Exception as ex:
        # 错误处理
        raise SqlLabException(db_engine_spec.extract_error_message(ex)) from ex
    
    # 返回结果集
    return SupersetResultSet(data, cursor.description, db_engine_spec)
```

## 4. 数据库引擎规范层

### 4.1 基础引擎规范

**类**: `BaseEngineSpec` (superset/db_engine_specs/base.py)
**关键方法**:

```python
@classmethod
def execute_with_cursor(cls, cursor: Any, sql: str, query: Query) -> None:
    """执行SQL并处理游标"""
    logger.debug("Query %d: Running query: %s", query.id, sql)
    cls.execute(cursor, sql, query.database, async_=True)
    logger.debug("Query %d: Handling cursor", query.id)
    cls.handle_cursor(cursor, query)

@classmethod
def fetch_data(cls, cursor: Any, limit: Optional[int] = None) -> list[tuple[Any, ...]]:
    """从游标获取数据"""
    if cls.arraysize:
        cursor.arraysize = cls.arraysize
    
    if limit:
        return cursor.fetchmany(limit)
    return cursor.fetchall()
```

### 4.2 特定数据库实现

**PostgreSQL示例**:
**类**: `PostgresEngineSpec` (superset/db_engine_specs/postgres.py)

```python
@classmethod
def get_prequeries(cls, catalog: str | None = None, schema: str | None = None) -> list[str]:
    """设置schema的预查询"""
    return [f'set search_path = "{schema}"'] if schema else []

@classmethod
def estimate_statement_cost(cls, statement: str, cursor: Any) -> dict[str, Any]:
    """估算查询成本"""
    sql = f"EXPLAIN {statement}"
    cursor.execute(sql)
    result = cursor.fetchone()[0]
    # 解析成本信息
    return cost_info
```

## 5. 结果集处理

### 5.1 结果集封装

**类**: `SupersetResultSet` (superset/result_set.py)

```python
class SupersetResultSet:
    def __init__(
        self,
        data: list[tuple[Any, ...]],
        cursor_description: Sequence[Any],
        db_engine_spec: BaseEngineSpec,
    ):
        self._data = data
        self._cursor_description = cursor_description
        self._db_engine_spec = db_engine_spec
    
    def to_pandas_df(self) -> pd.DataFrame:
        """转换为Pandas DataFrame"""
        columns = [col_desc[0] for col_desc in self._cursor_description]
        df = pd.DataFrame(self._data, columns=columns)
        return self._db_engine_spec.post_process_df(df)
    
    @property
    def columns(self) -> list[ResultSetColumnType]:
        """获取列信息"""
        return [
            {
                "column_name": column[0],
                "name": column[0],
                "type": self._db_engine_spec.column_datatype_to_string(column[1], column[0]),
                "type_generic": self._db_engine_spec.get_generic_type(column[1]),
                "is_dttm": self._db_engine_spec.is_db_column_type_match(
                    column[1], utils.GenericDataType.TEMPORAL
                ),
            }
            for column in self._cursor_description
        ]
```

## 6. 异步执行机制

### 6.1 Celery任务

**函数**: `get_sql_results()` (superset/sql_lab.py)

```python
@celery_app.task(
    name="sql_lab.get_sql_results",
    time_limit=SQLLAB_HARD_TIMEOUT,
    soft_time_limit=SQLLAB_TIMEOUT,
)
def get_sql_results(
    query_id: int,
    rendered_query: str,
    return_results: bool = True,
    store_results: bool = False,
    username: Optional[str] = None,
    start_time: Optional[float] = None,
    expand_data: bool = False,
    log_params: Optional[dict[str, Any]] = None,
) -> Optional[dict[str, Any]]:
    """Executes the sql query returns the results."""
    with current_app.test_request_context():
        with override_user(security_manager.find_user(username)):
            try:
                return execute_sql_statements(
                    query_id, rendered_query, return_results, store_results,
                    start_time=start_time, expand_data=expand_data, log_params=log_params,
                )
            except Exception as ex:
                logger.debug("Query %d: %s", query_id, ex)
                query = get_query(query_id)
                return handle_query_error(ex, query)
```

## 7. 总结

Superset的SQL查询流程是一个复杂但设计良好的系统：

1. **多层架构**: 前端 -> API -> Command -> Executor -> Database Engine -> DB
2. **异步支持**: 通过Celery支持长时间运行的查询
3. **安全机制**: DML检查、权限验证、SQL注入防护
4. **性能优化**: 查询限制、结果缓存、连接池
5. **监控日志**: 完整的查询执行链路追踪
6. **错误处理**: 多层次的异常处理和用户友好的错误信息 