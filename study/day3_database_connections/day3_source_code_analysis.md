# Day 3: 数据库连接与SQL查询 - 源码深度分析

## 1. 数据库连接架构源码分析

### 1.1 数据库模型核心实现

#### Database 模型详细分析
```python
# superset/models/core.py
class Database(Model, AuditMixinNullable, ImportExportMixin):
    """数据库连接模型 - 支持多种数据库引擎"""
    
    __tablename__ = "dbs"
    
    id = Column(Integer, primary_key=True)
    database_name = Column(String(250), unique=True, nullable=False)
    sqlalchemy_uri = Column(String(1024), nullable=False)
    password = Column(EncryptedType(String(1024), secret_key=SECRET_KEY))
    impersonate_user = Column(Boolean, default=False)
    encrypted_extra = Column(EncryptedType(Text, secret_key=SECRET_KEY))
    extra = Column(Text, default=lambda: json.dumps({}))
    server_cert = Column(EncryptedType(Text, secret_key=SECRET_KEY))
    
    # 功能开关
    allow_run_async = Column(Boolean, default=False)
    allow_file_upload = Column(Boolean, default=False)
    allow_ctas = Column(Boolean, default=False)      # CREATE TABLE AS
    allow_cvas = Column(Boolean, default=False)      # CREATE VIEW AS
    allow_dml = Column(Boolean, default=False)       # INSERT/UPDATE/DELETE
    
    # 性能配置
    cache_timeout = Column(Integer)
    select_as_create_table_as = Column(Boolean, default=False)
    expose_in_sqllab = Column(Boolean, default=True)
    force_ctas_schema = Column(String(250))
    
    @property
    def db_engine_spec(self) -> type[BaseEngineSpec]:
        """获取数据库引擎规范"""
        return db_engine_specs.get_engine_spec(self.backend)
    
    @property
    def backend(self) -> str:
        """获取数据库后端类型"""
        return self.url_object.get_backend_name()
    
    @property
    def url_object(self) -> URL:
        """获取SQLAlchemy URL对象"""
        return make_url_safe(self.sqlalchemy_uri_decrypted)
    
    @property
    def sqlalchemy_uri_decrypted(self) -> str:
        """解密后的连接URI"""
        conn = sqla.engine.url.make_url(self.sqlalchemy_uri)
        if custom_password_store := current_app.config["SQLALCHEMY_CUSTOM_PASSWORD_STORE"]:
            conn = conn.set(password=custom_password_store(conn))
        return str(conn)
```

### 1.2 数据库引擎规范系统

#### BaseEngineSpec 基类架构
```python
# superset/db_engine_specs/base.py
class BaseEngineSpec:
    """数据库引擎规范基类"""
    
    engine = "base"
    engine_name: str | None = None
    default_driver = ""
    sqlalchemy_uri_placeholder = (
        "engine+driver://user:password@host:port/dbname[?key=value&key=value...]"
    )
    
    # 功能支持
    allows_joins = True
    allows_subqueries = True
    allows_alias_to_source_column = True
    allows_hidden_orderbys_in_subqueries = True
    
    # SQL方言特性
    supports_dynamic_schema = False
    supports_catalog = False
    supports_file_upload = False
    
    # 时间相关
    time_groupby_inline = False
    time_grain_expressions: dict[str, str] = {}
    
    @classmethod
    def get_dbapi_exception_mapping(cls) -> dict[type[Exception], type[Exception]]:
        """数据库异常映射"""
        return {}
    
    @classmethod
    def get_dbapi_mapped_exception(cls, exception: Exception) -> Exception:
        """映射数据库异常到Superset异常"""
        new_exception = cls.get_dbapi_exception_mapping().get(type(exception))
        if new_exception:
            return new_exception(str(exception))
        return exception
    
    @classmethod
    def epoch_to_dttm(cls) -> str:
        """时间戳转换表达式"""
        return "datetime({col}, 'unixepoch')"
    
    @classmethod
    def epoch_ms_to_dttm(cls) -> str:
        """毫秒时间戳转换表达式"""
        return "datetime({col}/1000, 'unixepoch')"
    
    @classmethod
    def get_sqla_column_type(cls, column_type: str) -> type[TypeEngine] | None:
        """获取SQLAlchemy列类型"""
        return None
```

#### PostgreSQL 引擎规范实现
```python
# superset/db_engine_specs/postgres.py
class PostgresEngineSpec(BasicParametersMixin, PostgresBaseEngineSpec):
    engine = "postgresql"
    engine_name = "PostgreSQL"
    default_driver = "psycopg2"
    
    sqlalchemy_uri_placeholder = (
        "postgresql://user:password@host:port/dbname[?key=value&key=value...]"
    )
    
    # PostgreSQL特有配置
    max_column_name_length = 63
    try_remove_schema_from_table_name = False
    
    # 时间粒度表达式
    time_grain_expressions = {
        None: "{col}",
        "PT1S": "date_trunc('second', {col})",
        "PT1M": "date_trunc('minute', {col})",
        "PT1H": "date_trunc('hour', {col})",
        "P1D": "date_trunc('day', {col})",
        "P1W": "date_trunc('week', {col})",
        "P1M": "date_trunc('month', {col})",
        "P0.25Y": "date_trunc('quarter', {col})",
        "P1Y": "date_trunc('year', {col})",
    }
    
    @classmethod
    def get_default_schema_for_query(cls, database: Database, query: Query) -> str | None:
        """获取查询的默认schema"""
        script = SQLScript(query.sql, engine=cls.engine)
        settings = script.get_settings()
        
        # 安全检查：不允许设置search_path
        if "search_path" in settings:
            raise SupersetSecurityException(
                SupersetError(
                    error_type=SupersetErrorType.QUERY_SECURITY_ACCESS_ERROR,
                    message=__("Users are not allowed to set a search path for security reasons."),
                    level=ErrorLevel.ERROR,
                )
            )
        
        return super().get_default_schema_for_query(database, query)
    
    @classmethod
    def adjust_engine_params(
        cls,
        uri: URL,
        connect_args: dict[str, Any],
        catalog: str | None = None,
        schema: str | None = None,
    ) -> tuple[URL, dict[str, Any]]:
        """调整引擎参数"""
        if catalog:
            uri = uri.set(database=catalog)
        return uri, connect_args
```

### 1.3 连接池管理机制

#### 数据库连接获取流程
```python
# superset/models/core.py - Database类
@contextmanager
def get_sqla_engine(
    self,
    catalog: str | None = None,
    schema: str | None = None,
    nullpool: bool = True,
    source: utils.QuerySource | None = None,
) -> Engine:
    """获取SQLAlchemy引擎上下文管理器"""
    
    try:
        # 构建连接URL
        sqlalchemy_url = self.get_url_for_impersonation(
            url=make_url_safe(self.sqlalchemy_uri_decrypted),
            impersonate_user=self.impersonate_user,
            username=effective_username,
        )
        
        # 连接参数配置
        params: dict[str, Any] = {
            "poolclass": NullPool if nullpool else StaticPool,
            "pool_pre_ping": self.pool_pre_ping,
            "pool_recycle": self.pool_recycle,
            "echo": self.db_engine_spec.echo,
        }
        
        # 连接参数处理
        connect_args = self.get_extra().get("engine_params", {}).get("connect_args", {})
        if connect_args:
            params["connect_args"] = connect_args
        
        # 更新加密参数
        self.update_params_from_encrypted_extra(params)
        
        # 连接变异器处理
        if DB_CONNECTION_MUTATOR:
            if not source and request and request.referrer:
                if "/superset/dashboard/" in request.referrer:
                    source = utils.QuerySource.DASHBOARD
                elif "/explore/" in request.referrer:
                    source = utils.QuerySource.CHART
                elif "/sqllab/" in request.referrer:
                    source = utils.QuerySource.SQL_LAB
            
            sqlalchemy_url, params = DB_CONNECTION_MUTATOR(
                sqlalchemy_url,
                params,
                effective_username,
                security_manager,
                source,
            )
        
        # 创建引擎
        engine = create_engine(sqlalchemy_url, **params)
        
        # 引擎配置调整
        sqlalchemy_url, connect_args = self.db_engine_spec.adjust_engine_params(
            uri=sqlalchemy_url,
            connect_args=params.get("connect_args", {}),
            catalog=catalog,
            schema=schema,
        )
        
        engine = create_engine(sqlalchemy_url, **params)
        yield engine
        
    except Exception as ex:
        raise self.db_engine_spec.get_dbapi_mapped_exception(ex) from ex
    finally:
        if engine:
            engine.dispose()
```

## 2. SQL解析与查询构建

### 2.1 SQL解析器架构

#### SQLGlot 集成实现
```python
# superset/sql_parse.py
class ParsedQuery:
    """SQL解析结果类"""
    
    def __init__(
        self,
        sql: str,
        engine: str | None = None,
        schema: str | None = None,
    ) -> None:
        self.sql = sql
        self.engine = engine
        self.schema = schema
        self._parsed = None
        self._tables = None
    
    @property
    def parsed(self) -> list[Statement]:
        """解析后的SQL语句列表"""
        if self._parsed is None:
            try:
                self._parsed = sqlparse.parse(self.sql)
            except Exception as ex:
                logger.warning("SQL parsing error: %s", str(ex))
                self._parsed = []
        return self._parsed
    
    @property
    def tables(self) -> set[Table]:
        """提取SQL中的表名"""
        if self._tables is None:
            self._tables = set()
            
            for statement in self.parsed:
                try:
                    # 使用SQLGlot解析表名
                    parsed = sqlglot.parse_one(str(statement), dialect=self.engine)
                    for table in parsed.find_all(sqlglot.exp.Table):
                        table_name = table.name
                        schema_name = table.db or self.schema
                        catalog_name = table.catalog
                        
                        self._tables.add(Table(
                            table=table_name,
                            schema=schema_name,
                            catalog=catalog_name,
                        ))
                except Exception as ex:
                    logger.warning("Table extraction error: %s", str(ex))
        
        return self._tables
    
    def is_select(self) -> bool:
        """判断是否为SELECT语句"""
        if not self.parsed:
            return False
        
        first_token = self.parsed[0].token_first(skip_ws=True, skip_cm=True)
        return first_token and first_token.ttype is sqlparse.tokens.DML and \
               first_token.value.upper() == "SELECT"
    
    def is_explain(self) -> bool:
        """判断是否为EXPLAIN语句"""
        if not self.parsed:
            return False
        
        first_token = self.parsed[0].token_first(skip_ws=True, skip_cm=True)
        return first_token and first_token.value.upper() == "EXPLAIN"
    
    def get_query_limit(self) -> int | None:
        """获取查询LIMIT值"""
        for statement in self.parsed:
            limit_match = re.search(r'\bLIMIT\s+(\d+)\b', str(statement), re.IGNORECASE)
            if limit_match:
                return int(limit_match.group(1))
        return None
```

### 2.2 查询对象构建系统

#### QueryObject 到 SQL 转换
```python
# superset/connectors/sqla/models.py - SqlaTable类
def get_sqla_query(
    self,
    columns: list[Column] = None,
    filter: list[QueryObjectDict] = None,
    from_dttm: datetime | None = None,
    to_dttm: datetime | None = None,
    groupby: list[Column] = None,
    metrics: list[Metric] = None,
    granularity: Column | None = None,
    timeseries_limit: int = 15,
    timeseries_limit_metric: Metric | None = None,
    row_limit: int | None = None,
    row_offset: int | None = None,
    order_desc: bool = True,
    extras: dict[str, Any] | None = None,
    **kwargs,
) -> Query:
    """构建SQLAlchemy查询对象"""
    
    # 基础查询构建
    qry = select()
    
    # 选择列处理
    if columns:
        for col in columns:
            col_obj = self.get_column(col.column_name)
            if col_obj:
                qry = qry.add_columns(col_obj.get_sqla_col())
    
    # 指标处理
    if metrics:
        for metric in metrics:
            metric_obj = self.get_metric(metric.metric_name) if hasattr(metric, 'metric_name') else metric
            if metric_obj:
                qry = qry.add_columns(metric_obj.get_sqla_col().label(metric_obj.metric_name))
    
    # FROM子句
    if self.sql:
        # 自定义SQL作为子查询
        qry = qry.select_from(text(f"({self.sql}) AS query"))
    else:
        # 表名
        table_obj = table(self.table_name, schema=self.schema)
        qry = qry.select_from(table_obj)
    
    # 时间范围过滤
    if granularity and (from_dttm or to_dttm):
        dttm_col = self.get_column(granularity)
        if dttm_col:
            if from_dttm:
                qry = qry.where(dttm_col.get_sqla_col() >= from_dttm)
            if to_dttm:
                qry = qry.where(dttm_col.get_sqla_col() <= to_dttm)
    
    # WHERE条件过滤
    if filter:
        for flt in filter:
            filter_clause = self._get_filter_clause(flt)
            if filter_clause is not None:
                qry = qry.where(filter_clause)
    
    # GROUP BY子句
    if groupby:
        group_by_columns = []
        for col in groupby:
            col_obj = self.get_column(col.column_name)
            if col_obj:
                group_by_columns.append(col_obj.get_sqla_col())
        
        if group_by_columns:
            qry = qry.group_by(*group_by_columns)
    
    # ORDER BY子句
    if order_desc and metrics:
        # 按第一个指标降序排列
        first_metric = metrics[0]
        if hasattr(first_metric, 'metric_name'):
            qry = qry.order_by(desc(first_metric.metric_name))
    
    # LIMIT子句
    if row_limit:
        qry = qry.limit(row_limit)
    
    # OFFSET子句
    if row_offset:
        qry = qry.offset(row_offset)
    
    return qry

def _get_filter_clause(self, flt: dict[str, Any]) -> ClauseElement | None:
    """构建过滤条件子句"""
    col_name = flt.get("col")
    op = flt.get("op")
    val = flt.get("val")
    
    if not col_name or not op:
        return None
    
    col_obj = self.get_column(col_name)
    if not col_obj:
        return None
    
    sqla_col = col_obj.get_sqla_col()
    
    # 操作符处理
    if op == "==":
        return sqla_col == val
    elif op == "!=":
        return sqla_col != val
    elif op == ">":
        return sqla_col > val
    elif op == "<":
        return sqla_col < val
    elif op == ">=":
        return sqla_col >= val
    elif op == "<=":
        return sqla_col <= val
    elif op == "in":
        if isinstance(val, (list, tuple)):
            return sqla_col.in_(val)
    elif op == "not in":
        if isinstance(val, (list, tuple)):
            return ~sqla_col.in_(val)
    elif op == "LIKE":
        return sqla_col.like(val)
    elif op == "ILIKE":
        return sqla_col.ilike(val)
    elif op == "IS NULL":
        return sqla_col.is_(None)
    elif op == "IS NOT NULL":
        return sqla_col.isnot(None)
    
    return None
```

### 2.3 查询执行引擎

#### SQL执行器架构
```python
# superset/sqllab/sql_json_executer.py
class SqlJsonExecutor:
    """SQL查询执行器基类"""
    
    def __init__(self, database: Database, schema: str | None = None) -> None:
        self._database = database
        self._schema = schema
    
    def execute(
        self,
        sql: str,
        query: Query,
        log_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """执行SQL查询"""
        raise NotImplementedError("Subclasses must implement execute method")

class SynchronousSqlJsonExecutor(SqlJsonExecutor):
    """同步SQL执行器"""
    
    def execute(
        self,
        sql: str,
        query: Query,
        log_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """同步执行SQL查询"""
        try:
            with self._database.get_sqla_engine(schema=self._schema) as engine:
                # 预编译SQL
                compiled_sql = sqlalchemy.text(sql)
                
                # 执行查询
                result = engine.execute(compiled_sql)
                
                # 处理结果
                if result.returns_rows:
                    df = pd.read_sql(compiled_sql, engine)
                    data = df.to_dict(orient="records")
                    columns = [{"name": col, "type": str(df[col].dtype)} for col in df.columns]
                else:
                    data = []
                    columns = []
                
                return {
                    "data": data,
                    "columns": columns,
                    "query": {
                        "changedOn": datetime.now().isoformat(),
                        "state": "success",
                        "executedSql": sql,
                    },
                }
                
        except Exception as ex:
            logger.exception("Query execution failed")
            return {
                "error": str(ex),
                "query": {
                    "changedOn": datetime.now().isoformat(),
                    "state": "failed",
                    "executedSql": sql,
                    "errorMessage": str(ex),
                },
            }

class ASynchronousSqlJsonExecutor(SqlJsonExecutor):
    """异步SQL执行器"""
    
    def execute(
        self,
        sql: str,
        query: Query,
        log_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """异步执行SQL查询"""
        
        # 提交Celery任务
        task = sql_lab.get_sql_results.apply_async(
            args=[
                query.id,
                rendered_query,
                return_results,
                store_results,
                user_name,
                start_time,
                expand_data,
                log_params,
            ],
            soft_time_limit=SQLLAB_TIMEOUT,
        )
        
        return {
            "query": {
                "changedOn": datetime.now().isoformat(),
                "state": "running",
                "executedSql": sql,
                "queryId": query.id,
                "taskId": task.id,
            },
        }
```

## 3. 数据库安全管理

### 3.1 连接安全验证

#### URI安全检查机制
```python
# superset/security/analytics_db_safety.py
import re
from flask_babel import lazy_gettext as _
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import NoSuchModuleError

# 不安全的SQLAlchemy方言黑名单
BLOCKLIST = {
    # SQLite创建本地DB，允许映射服务器文件系统
    re.compile(r"sqlite(?:\+[^\s]*)?$"),
    # shillelagh允许打开本地文件（如'SELECT * FROM "csv:///etc/passwd"'）
    re.compile(r"shillelagh$"),
    re.compile(r"shillelagh\+apsw$"),
}

def check_sqlalchemy_uri(uri: URL) -> None:
    """检查SQLAlchemy URI的安全性"""
    if not feature_flag_manager.is_feature_enabled("ENABLE_SUPERSET_META_DB"):
        BLOCKLIST.add(re.compile(r"superset$"))
    
    for blocklist_regex in BLOCKLIST:
        if not re.match(blocklist_regex, uri.drivername):
            continue
            
        try:
            dialect = uri.get_dialect().__name__
        except (NoSuchModuleError, ValueError):
            dialect = uri.drivername
        
        raise SupersetSecurityException(
            SupersetError(
                error_type=SupersetErrorType.DATABASE_SECURITY_ACCESS_ERROR,
                message=_(
                    "%(dialect)s cannot be used as a data source for security reasons.",
                    dialect=dialect,
                ),
                level=ErrorLevel.ERROR,
            )
        )
```

### 3.2 权限控制系统

#### 数据库访问权限检查
```python
# superset/security/manager.py - SupersetSecurityManager类
def can_access_database(self, database: Database) -> bool:
    """检查数据库访问权限"""
    return (
        self.can_access_all_databases()
        or self.can_access("database_access", database.perm)
        or database.id in self.user_view_menu_names("database_access")
    )

def can_access_schema(self, datasource: BaseDatasource) -> bool:
    """检查schema访问权限"""
    if not datasource or not datasource.schema:
        return True
        
    return (
        self.can_access_all_datasources()
        or self.can_access("schema_access", datasource.schema_perm)
        or datasource.schema in self.user_view_menu_names("schema_access")
    )

def raise_for_access(
    self,
    database: Database | None = None,
    datasource: BaseDatasource | None = None,
    query: Query | None = None,
    query_context: QueryContext | None = None,
    viz: BaseViz | None = None,
    **kwargs: Any,
) -> None:
    """检查访问权限并在无权限时抛出异常"""
    
    # 数据库权限检查
    if database and not self.can_access_database(database):
        raise SupersetSecurityException(
            SupersetError(
                error_type=SupersetErrorType.DATABASE_SECURITY_ACCESS_ERROR,
                message=__("You need access to the following database to run this query: %(database)s", 
                          database=database.database_name),
                level=ErrorLevel.ERROR,
            )
        )
    
    # 数据源权限检查
    if datasource and not self.can_access_datasource(datasource):
        raise SupersetSecurityException(
            SupersetError(
                error_type=SupersetErrorType.DATASOURCE_SECURITY_ACCESS_ERROR,
                message=__("You need access to the following datasource to run this query: %(datasource)s",
                          datasource=datasource.name),
                level=ErrorLevel.ERROR,
            )
        )
    
    # SQL查询权限检查
    if query and not self.can_access_query(query):
        raise SupersetSecurityException(
            SupersetError(
                error_type=SupersetErrorType.QUERY_SECURITY_ACCESS_ERROR,
                message=__("You need access to the following query to run it: %(query)s",
                          query=query.sql),
                level=ErrorLevel.ERROR,
            )
        )
```

### 3.3 SQL注入防护

#### 参数化查询实现
```python
# superset/sqllab/query_render.py
class SqlQueryRenderImpl:
    """SQL查询渲染实现类"""
    
    def __init__(self, database: Database, query: Query) -> None:
        self._database = database
        self._query = query
    
    def render(self, sql: str, **kwargs) -> str:
        """渲染SQL模板"""
        
        # Jinja2模板渲染
        template_env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            undefined=jinja2.StrictUndefined,
        )
        
        # 添加安全函数
        template_env.globals.update({
            "filter_values": self._filter_values,
            "url_param": self._url_param,
            "time_grain_to_seconds": utils.time_grain_to_seconds,
            "dataset": self._get_dataset_function(),
        })
        
        try:
            template = template_env.from_string(sql)
            rendered_sql = template.render(
                filter_values=self._filter_values,
                url_param=self._url_param,
                **kwargs
            )
            
            # SQL注入检查
            self._validate_sql_injection(rendered_sql)
            
            return rendered_sql
            
        except jinja2.TemplateError as ex:
            logger.exception("Template rendering failed")
            raise QueryTemplateError(str(ex)) from ex
    
    def _validate_sql_injection(self, sql: str) -> None:
        """SQL注入检查"""
        
        # 检查危险关键字
        dangerous_patterns = [
            r'\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|TRUNCATE)\s+',
            r';\s*(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|TRUNCATE)',
            r'--\s*[^\r\n]*',  # SQL注释
            r'/\*.*?\*/',       # 多行注释
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE | re.DOTALL):
                logger.warning("Potential SQL injection detected: %s", sql[:100])
                
        # 使用SQLGlot解析验证
        try:
            parsed = sqlglot.parse_one(sql, dialect=self._database.backend)
            if not isinstance(parsed, sqlglot.exp.Select):
                if not self._database.allow_dml:
                    raise SecurityException("DML statements are not allowed")
        except sqlglot.ParseError as ex:
            logger.warning("SQL parsing failed during injection check: %s", str(ex))
    
    def _filter_values(self, column: str, default: Any = None) -> Any:
        """安全的过滤值获取"""
        # 从当前过滤器中获取值
        # 确保只返回当前用户有权限的数据
        pass
```

## 4. 多数据库支持架构

### 4.1 数据库驱动注册系统

#### 引擎规范注册机制
```python
# superset/db_engine_specs/__init__.py
import importlib
import pkgutil
from typing import Dict, Type

from .base import BaseEngineSpec

# 引擎规范注册表
engines: Dict[str, Type[BaseEngineSpec]] = {}

def load_engine_specs() -> None:
    """动态加载所有引擎规范"""
    for module_info in pkgutil.iter_modules(__path__, prefix=__name__ + "."):
        module = importlib.import_module(module_info.name)
        
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseEngineSpec)
                and attr != BaseEngineSpec
                and hasattr(attr, "engine")
            ):
                engines[attr.engine] = attr

def get_engine_spec(engine: str) -> Type[BaseEngineSpec]:
    """获取引擎规范"""
    if engine not in engines:
        load_engine_specs()
    
    return engines.get(engine, BaseEngineSpec)

# 自动加载
load_engine_specs()
```

### 4.2 多数据库连接池管理

#### 连接池配置与管理
```python
# superset/utils/database.py
from sqlalchemy.pool import QueuePool, NullPool, StaticPool

class DatabaseConnectionManager:
    """数据库连接管理器"""
    
    def __init__(self) -> None:
        self._engines: dict[str, Engine] = {}
        self._pools: dict[str, Pool] = {}
    
    def get_engine(
        self,
        database: Database,
        source: utils.QuerySource | None = None,
        **kwargs
    ) -> Engine:
        """获取数据库引擎"""
        
        cache_key = f"{database.id}_{source or 'default'}"
        
        if cache_key not in self._engines:
            self._engines[cache_key] = self._create_engine(database, source, **kwargs)
        
        return self._engines[cache_key]
    
    def _create_engine(
        self,
        database: Database,
        source: utils.QuerySource | None = None,
        **kwargs
    ) -> Engine:
        """创建数据库引擎"""
        
        # 连接池配置
        pool_config = self._get_pool_config(database, source)
        
        # 创建引擎
        with database.get_sqla_engine(**pool_config) as engine:
            return engine
    
    def _get_pool_config(
        self,
        database: Database,
        source: utils.QuerySource | None = None,
    ) -> dict[str, Any]:
        """获取连接池配置"""
        
        config = {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 3600,
        }
        
        # 根据来源调整配置
        if source == utils.QuerySource.SQL_LAB:
            config.update({
                "pool_size": 5,
                "max_overflow": 10,
                "poolclass": QueuePool,
            })
        elif source == utils.QuerySource.DASHBOARD:
            config.update({
                "pool_size": 15,
                "max_overflow": 30,
                "poolclass": QueuePool,
            })
        else:
            config.update({
                "poolclass": NullPool,  # 默认使用NullPool
            })
        
        return config
    
    def close_all_connections(self) -> None:
        """关闭所有连接"""
        for engine in self._engines.values():
            engine.dispose()
        
        self._engines.clear()
        self._pools.clear()
```

## 5. 查询执行流程时序图

### 5.1 同步查询执行流程

```mermaid
sequenceDiagram
    participant User as 用户/API
    participant SQLLab as SQL Lab视图
    participant Executor as SQL执行器
    participant Database as 数据库连接
    participant Engine as SQLAlchemy引擎
    participant DB as 目标数据库

    User->>SQLLab: 提交SQL查询
    SQLLab->>SQLLab: 解析SQL语句
    SQLLab->>SQLLab: 权限验证
    
    SQLLab->>Executor: 创建SQL执行器
    Executor->>Database: 获取数据库连接
    Database->>Engine: 创建SQLAlchemy引擎
    
    Engine->>DB: 建立数据库连接
    DB-->>Engine: 连接成功
    
    Executor->>Engine: 执行SQL查询
    Engine->>DB: 发送SQL语句
    DB-->>Engine: 返回查询结果
    
    Engine-->>Executor: 结果集
    Executor->>Executor: 数据格式化
    Executor-->>SQLLab: 返回JSON结果
    SQLLab-->>User: 显示查询结果
```

### 5.2 异步查询执行流程

```mermaid
sequenceDiagram
    participant User as 用户界面
    participant API as 查询API
    participant Celery as Celery任务队列
    participant Worker as Celery Worker
    participant Cache as Redis缓存
    participant DB as 数据库

    User->>API: 提交异步查询请求
    API->>API: 创建Query记录
    API->>Celery: 提交异步任务
    API-->>User: 返回任务ID和状态

    User->>User: 开始轮询查询状态
    
    par 异步执行
        Celery->>Worker: 分配任务到Worker
        Worker->>DB: 执行SQL查询
        DB-->>Worker: 返回查询结果
        Worker->>Cache: 缓存查询结果
        Worker->>Worker: 更新Query状态
    end
    
    loop 状态检查
        User->>API: 查询执行状态
        API->>Cache: 检查任务状态
        Cache-->>API: 返回当前状态
        API-->>User: 返回执行进度
    end
    
    User->>API: 获取最终结果
    API->>Cache: 获取缓存结果
    Cache-->>API: 返回查询数据
    API-->>User: 返回完整结果
```

## 6. 数据库架构图

### 6.1 数据库连接架构

```mermaid
flowchart TD
    A[Superset应用] --> B[DatabaseManager]
    B --> C[Database模型]
    C --> D[EngineSpec工厂]
    
    D --> E[PostgresEngineSpec]
    D --> F[MySQLEngineSpec]
    D --> G[RedshiftEngineSpec]
    D --> H[BigQueryEngineSpec]
    
    E --> I[PostgreSQL驱动]
    F --> J[MySQL驱动]
    G --> K[Redshift驱动]
    H --> L[BigQuery驱动]
    
    I --> M[PostgreSQL数据库]
    J --> N[MySQL数据库]
    K --> O[Amazon Redshift]
    L --> P[Google BigQuery]
    
    B --> Q[连接池管理]
    Q --> R[QueuePool]
    Q --> S[NullPool]
    Q --> T[StaticPool]
```

### 6.2 SQL解析与执行架构

```mermaid
flowchart LR
    A[原始SQL] --> B[SQLGlot解析器]
    B --> C[解析树]
    C --> D[安全验证]
    D --> E[权限检查]
    E --> F[SQL渲染器]
    F --> G[参数化SQL]
    
    G --> H{执行方式}
    H -->|同步| I[同步执行器]
    H -->|异步| J[异步执行器]
    
    I --> K[SQLAlchemy引擎]
    J --> L[Celery任务]
    L --> M[Worker进程]
    M --> K
    
    K --> N[数据库连接]
    N --> O[查询结果]
    O --> P[数据后处理]
    P --> Q[JSON响应]
```

## 7. 重点难点分析

### 7.1 技术挑战

1. **多数据库兼容性**：不同数据库的SQL方言差异处理
2. **连接池管理**：高并发场景下的连接复用和释放
3. **安全控制**：SQL注入防护和权限隔离
4. **性能优化**：大查询的内存管理和超时控制

### 7.2 架构设计要点

1. **插件化设计**：通过EngineSpec实现数据库支持的扩展
2. **分层架构**：清晰的数据访问层和业务逻辑层分离
3. **异步处理**：长时间查询的异步执行机制
4. **缓存策略**：查询结果的多级缓存优化

### 7.3 安全考虑

1. **URI安全检查**：阻止不安全的数据库连接
2. **SQL注入防护**：多层次的SQL安全验证
3. **权限细粒度控制**：数据库、schema、表级别的访问控制
4. **审计日志**：完整的查询执行记录

这个源码分析深入展示了Superset数据库连接系统的完整架构，从连接管理到查询执行，从安全控制到多数据库支持，体现了企业级数据平台在数据访问层的设计精髓。 