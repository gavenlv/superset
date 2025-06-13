#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day 8 自定义数据库驱动演示：数据库引擎扩展机制
=============================================

本脚本演示如何扩展 Superset 的数据库引擎规范：
- 自定义数据库驱动
- OAuth2集成
- 参数化配置
- 函数映射
"""

import json
import time
import uuid
import requests
from typing import Dict, List, Any, Optional, Union, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import urlencode, urljoin
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError


@dataclass
class OAuth2ClientConfig:
    """OAuth2客户端配置"""
    id: str
    secret: str
    scope: str
    redirect_uri: str
    authorization_request_uri: str
    token_request_uri: str


@dataclass
class OAuth2State:
    """OAuth2状态"""
    database_id: int
    user_id: int
    default_redirect_uri: str
    tab_id: str


@dataclass
class OAuth2TokenResponse:
    """OAuth2令牌响应"""
    access_token: str
    refresh_token: Optional[str]
    expires_in: int
    token_type: str = "Bearer"


class DatabaseEngineSpec(ABC):
    """数据库引擎规范基类"""
    
    # 引擎标识
    engine_name: str = "Base Engine"
    engine: str = "base"
    engine_aliases: set[str] = set()
    drivers: Dict[str, str] = {}
    default_driver: Optional[str] = None
    
    # SQLAlchemy URI模板
    sqlalchemy_uri_placeholder: str = "engine+driver://user:password@host:port/dbname"
    
    # 功能支持
    allows_joins: bool = True
    allows_subqueries: bool = True
    allows_sql_comments: bool = True
    supports_file_upload: bool = False
    
    # OAuth2支持
    oauth2_scope: str = ""
    oauth2_authorization_request_uri: str = ""
    oauth2_token_request_uri: str = ""
    oauth2_exception: Type[Exception] = Exception
    
    # 时间粒度表达式
    _time_grain_expressions: Dict[str, str] = {}
    
    @classmethod
    def supports_backend(cls, backend: str, driver: Optional[str] = None) -> bool:
        """检查是否支持给定的后端/驱动"""
        if backend != cls.engine and backend not in cls.engine_aliases:
            return False
        
        if not cls.drivers or driver is None:
            return True
        
        return driver in cls.drivers
    
    @classmethod
    def get_function_names(cls, database: 'MockDatabase') -> List[str]:
        """获取数据库支持的函数列表"""
        return []
    
    @classmethod
    def get_datatype(cls, type_code: Any) -> Optional[str]:
        """获取数据类型映射"""
        return str(type_code) if type_code else None
    
    @classmethod
    def execute(cls, cursor: Any, query: str, database: 'MockDatabase', **kwargs: Any) -> None:
        """执行SQL查询"""
        try:
            cursor.execute(query)
        except Exception as ex:
            if database.is_oauth2_enabled() and cls.needs_oauth2(ex):
                cls.start_oauth2_dance(database)
            raise ex
    
    @classmethod
    def needs_oauth2(cls, ex: Exception) -> bool:
        """检查异常是否表示需要OAuth2"""
        return isinstance(ex, cls.oauth2_exception)
    
    @classmethod
    def start_oauth2_dance(cls, database: 'MockDatabase') -> None:
        """启动OAuth2认证流程"""
        tab_id = str(uuid.uuid4())
        
        state = OAuth2State(
            database_id=database.id,
            user_id=1,  # 模拟用户ID
            default_redirect_uri="http://localhost:8088/oauth2",
            tab_id=tab_id,
        )
        
        oauth2_config = database.get_oauth2_config()
        if not oauth2_config:
            raise Exception("No OAuth2 configuration found")
        
        oauth_url = cls.get_oauth2_authorization_uri(oauth2_config, state)
        print(f"🔐 OAuth2认证URL: {oauth_url}")
        
        # 在实际实现中，这里会抛出OAuth2RedirectError
        # raise OAuth2RedirectError(oauth_url, tab_id, state.default_redirect_uri)
    
    @classmethod
    def get_oauth2_authorization_uri(cls, config: OAuth2ClientConfig, state: OAuth2State) -> str:
        """构建OAuth2授权URI"""
        params = {
            "scope": config.scope,
            "access_type": "offline",
            "response_type": "code",
            "state": cls._encode_oauth2_state(state),
            "redirect_uri": config.redirect_uri,
            "client_id": config.id,
            "prompt": "consent",
        }
        return f"{config.authorization_request_uri}?{urlencode(params)}"
    
    @classmethod
    def get_oauth2_token(cls, config: OAuth2ClientConfig, code: str) -> OAuth2TokenResponse:
        """交换授权码获取访问令牌"""
        response = requests.post(
            config.token_request_uri,
            json={
                "code": code,
                "client_id": config.id,
                "client_secret": config.secret,
                "redirect_uri": config.redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=30,
        )
        
        token_data = response.json()
        return OAuth2TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data["expires_in"],
            token_type=token_data.get("token_type", "Bearer"),
        )
    
    @classmethod
    def _encode_oauth2_state(cls, state: OAuth2State) -> str:
        """编码OAuth2状态"""
        # 简化实现，实际应使用JWT
        return json.dumps(state.__dict__)


class BasicParametersMixin:
    """基础参数混入类"""
    
    # 推荐驱动
    default_driver: str = ""
    
    # 加密参数
    encryption_parameters: Dict[str, str] = {}
    
    @classmethod
    def build_sqlalchemy_uri(cls, parameters: Dict[str, Any]) -> str:
        """构建SQLAlchemy URI"""
        query = parameters.get("query", {}).copy()
        
        if parameters.get("encryption"):
            if not cls.encryption_parameters:
                raise Exception("Unable to build a URL with encryption enabled")
            query.update(cls.encryption_parameters)
        
        return str(
            URL.create(
                f"{cls.engine}+{cls.default_driver}".rstrip("+"),
                username=parameters.get("username"),
                password=parameters.get("password"),
                host=parameters["host"],
                port=parameters["port"],
                database=parameters["database"],
                query=query,
            )
        )
    
    @classmethod
    def get_parameters_from_uri(cls, uri: str) -> Dict[str, Any]:
        """从URI提取参数"""
        url = URL.create(uri)
        query = dict(url.query)
        
        # 移除加密参数
        for key in cls.encryption_parameters:
            query.pop(key, None)
        
        return {
            "username": url.username,
            "password": url.password,
            "host": url.host,
            "port": url.port,
            "database": url.database,
            "query": query,
            "encryption": bool(cls.encryption_parameters),
        }


class CustomCloudDBEngineSpec(BasicParametersMixin, DatabaseEngineSpec):
    """自定义云数据库引擎规范"""
    
    engine_name = "Custom Cloud DB"
    engine = "customclouddb"
    engine_aliases = {"clouddb", "customdb"}
    drivers = {
        "rest": "REST API driver",
        "native": "Native driver",
    }
    default_driver = "rest"
    
    sqlalchemy_uri_placeholder = (
        "customclouddb+rest://token:secret@api.example.com:443/database"
    )
    
    # OAuth2配置
    oauth2_scope = "read write"
    oauth2_authorization_request_uri = "https://auth.example.com/oauth2/authorize"
    oauth2_token_request_uri = "https://auth.example.com/oauth2/token"
    oauth2_exception = ConnectionError
    
    # 加密参数
    encryption_parameters = {"ssl": "true", "sslmode": "require"}
    
    # 时间粒度表达式
    _time_grain_expressions = {
        None: "{col}",
        "PT1S": "DATE_TRUNC('second', {col})",
        "PT1M": "DATE_TRUNC('minute', {col})",
        "PT1H": "DATE_TRUNC('hour', {col})",
        "P1D": "DATE_TRUNC('day', {col})",
        "P1W": "DATE_TRUNC('week', {col})",
        "P1M": "DATE_TRUNC('month', {col})",
        "P1Y": "DATE_TRUNC('year', {col})",
    }
    
    @classmethod
    def get_function_names(cls, database: 'MockDatabase') -> List[str]:
        """获取支持的函数列表"""
        return [
            # 聚合函数
            "COUNT", "SUM", "AVG", "MIN", "MAX",
            "STDDEV", "VARIANCE",
            
            # 字符串函数
            "CONCAT", "SUBSTRING", "LENGTH", "UPPER", "LOWER",
            "TRIM", "LTRIM", "RTRIM",
            
            # 日期函数
            "NOW", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP",
            "DATE_TRUNC", "DATE_PART", "EXTRACT",
            
            # 数学函数
            "ABS", "CEIL", "FLOOR", "ROUND", "SQRT", "POWER",
            "SIN", "COS", "TAN", "LOG", "EXP",
            
            # 条件函数
            "CASE", "COALESCE", "NULLIF", "GREATEST", "LEAST",
            
            # 窗口函数
            "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD",
            "FIRST_VALUE", "LAST_VALUE",
        ]
    
    @classmethod
    def get_datatype(cls, type_code: Any) -> Optional[str]:
        """获取数据类型映射"""
        type_mapping = {
            "int": "INTEGER",
            "float": "FLOAT",
            "str": "VARCHAR",
            "bool": "BOOLEAN",
            "datetime": "TIMESTAMP",
            "date": "DATE",
            "time": "TIME",
            "decimal": "DECIMAL",
            "json": "JSON",
            "array": "ARRAY",
        }
        return type_mapping.get(str(type_code).lower(), "VARCHAR")
    
    @classmethod
    def epoch_to_dttm(cls) -> str:
        """Unix时间戳转换为日期时间"""
        return "TO_TIMESTAMP({col})"
    
    @classmethod
    def convert_dttm(cls, target_type: str, dttm: Any) -> Optional[str]:
        """转换日期时间格式"""
        if target_type.upper() == "DATE":
            return f"DATE('{dttm.date().isoformat()}')"
        elif target_type.upper() == "TIMESTAMP":
            return f"TIMESTAMP('{dttm.isoformat()}')"
        elif target_type.upper() == "DATETIME":
            return f"DATETIME('{dttm.isoformat()}')"
        return None
    
    @classmethod
    def get_cancel_query_id(cls, cursor: Any, query: Any) -> Optional[str]:
        """获取查询取消ID"""
        # 返回模拟的查询ID
        return f"query_{int(time.time())}"
    
    @classmethod
    def cancel_query(cls, cursor: Any, query: Any, cancel_query_id: str) -> bool:
        """取消查询"""
        print(f"🚫 取消查询: {cancel_query_id}")
        return True


class TimeSeriesDBEngineSpec(BasicParametersMixin, DatabaseEngineSpec):
    """时序数据库引擎规范"""
    
    engine_name = "Time Series DB"
    engine = "tsdb"
    engine_aliases = {"timeseries", "influx"}
    drivers = {
        "influxdb": "InfluxDB driver",
        "prometheus": "Prometheus driver",
    }
    default_driver = "influxdb"
    
    sqlalchemy_uri_placeholder = "tsdb+influxdb://user:password@host:8086/database"
    
    # 时序数据库特性
    supports_file_upload = False
    allows_joins = False  # 时序数据库通常不支持复杂JOIN
    
    # 时间粒度表达式（时序数据库特有）
    _time_grain_expressions = {
        None: "time",
        "PT1S": "time(1s)",
        "PT5S": "time(5s)",
        "PT30S": "time(30s)",
        "PT1M": "time(1m)",
        "PT5M": "time(5m)",
        "PT10M": "time(10m)",
        "PT15M": "time(15m)",
        "PT30M": "time(30m)",
        "PT1H": "time(1h)",
        "PT6H": "time(6h)",
        "PT12H": "time(12h)",
        "P1D": "time(1d)",
        "P1W": "time(1w)",
    }
    
    @classmethod
    def get_function_names(cls, database: 'MockDatabase') -> List[str]:
        """获取时序数据库函数"""
        return [
            # 聚合函数
            "MEAN", "MEDIAN", "MODE", "SUM", "COUNT",
            "MIN", "MAX", "FIRST", "LAST",
            "STDDEV", "SPREAD", "PERCENTILE",
            
            # 时间函数
            "NOW", "TIME", "DURATION",
            
            # 选择函数
            "TOP", "BOTTOM", "SAMPLE",
            
            # 变换函数
            "DERIVATIVE", "DIFFERENCE", "MOVING_AVERAGE",
            "CUMULATIVE_SUM", "RATE",
            
            # 预测函数
            "HOLT_WINTERS", "LINEAR_REGRESSION",
        ]
    
    @classmethod
    def get_datatype(cls, type_code: Any) -> Optional[str]:
        """时序数据库类型映射"""
        type_mapping = {
            "field": "FIELD",
            "tag": "TAG",
            "time": "TIME",
            "float": "FLOAT",
            "integer": "INTEGER",
            "string": "STRING",
            "boolean": "BOOLEAN",
        }
        return type_mapping.get(str(type_code).lower(), "FIELD")


class GraphDBEngineSpec(DatabaseEngineSpec):
    """图数据库引擎规范"""
    
    engine_name = "Graph DB"
    engine = "graphdb"
    engine_aliases = {"neo4j", "graph"}
    drivers = {
        "bolt": "Bolt protocol driver",
        "http": "HTTP driver",
    }
    default_driver = "bolt"
    
    sqlalchemy_uri_placeholder = "graphdb+bolt://user:password@host:7687/database"
    
    # 图数据库特性
    allows_joins = False  # 图数据库使用不同的查询语言
    allows_subqueries = False
    
    @classmethod
    def get_function_names(cls, database: 'MockDatabase') -> List[str]:
        """获取图数据库函数（Cypher）"""
        return [
            # 节点和关系函数
            "NODES", "RELATIONSHIPS", "ID", "TYPE", "LABELS",
            "PROPERTIES", "KEYS",
            
            # 路径函数
            "LENGTH", "NODES", "RELATIONSHIPS", "EXTRACT",
            "FILTER", "REDUCE",
            
            # 聚合函数
            "COUNT", "SUM", "AVG", "MIN", "MAX",
            "COLLECT", "DISTINCT",
            
            # 字符串函数
            "SUBSTRING", "LEFT", "RIGHT", "TRIM", "LTRIM", "RTRIM",
            "UPPER", "LOWER", "REPLACE", "SPLIT",
            
            # 数学函数
            "ABS", "CEIL", "FLOOR", "ROUND", "SQRT",
            "SIN", "COS", "TAN", "LOG", "EXP",
            
            # 列表函数
            "HEAD", "TAIL", "SIZE", "REVERSE", "SORT",
            
            # 图算法函数
            "SHORTEST_PATH", "ALL_SHORTEST_PATHS",
        ]


class MockDatabase:
    """模拟数据库类"""
    
    def __init__(self, id: int, engine_spec: Type[DatabaseEngineSpec]):
        self.id = id
        self.engine_spec = engine_spec
        self.oauth2_config: Optional[OAuth2ClientConfig] = None
        
    def is_oauth2_enabled(self) -> bool:
        """检查是否启用OAuth2"""
        return self.oauth2_config is not None
    
    def get_oauth2_config(self) -> Optional[OAuth2ClientConfig]:
        """获取OAuth2配置"""
        return self.oauth2_config
    
    def set_oauth2_config(self, config: OAuth2ClientConfig) -> None:
        """设置OAuth2配置"""
        self.oauth2_config = config


class DatabaseEngineRegistry:
    """数据库引擎注册表"""
    
    def __init__(self):
        self.engines: Dict[str, Type[DatabaseEngineSpec]] = {}
        
    def register_engine(self, engine_spec: Type[DatabaseEngineSpec]) -> None:
        """注册引擎"""
        self.engines[engine_spec.engine] = engine_spec
        
        # 注册别名
        for alias in engine_spec.engine_aliases:
            self.engines[alias] = engine_spec
        
        print(f"✓ 注册数据库引擎: {engine_spec.engine} - {engine_spec.engine_name}")
    
    def get_engine_spec(self, backend: str, driver: Optional[str] = None) -> Optional[Type[DatabaseEngineSpec]]:
        """获取引擎规范"""
        engine_spec = self.engines.get(backend)
        if engine_spec and engine_spec.supports_backend(backend, driver):
            return engine_spec
        return None
    
    def list_engines(self) -> List[str]:
        """列出所有引擎"""
        return list(set(spec.engine for spec in self.engines.values()))
    
    def get_available_drivers(self) -> Dict[str, List[str]]:
        """获取可用驱动"""
        drivers = {}
        for engine, spec in self.engines.items():
            if engine == spec.engine:  # 避免重复别名
                drivers[engine] = list(spec.drivers.keys())
        return drivers


def demo_custom_database_engines():
    """演示自定义数据库引擎"""
    print("🗄️ 自定义数据库引擎演示")
    print("=" * 60)
    
    # 创建注册表
    registry = DatabaseEngineRegistry()
    
    # 注册自定义引擎
    registry.register_engine(CustomCloudDBEngineSpec)
    registry.register_engine(TimeSeriesDBEngineSpec)
    registry.register_engine(GraphDBEngineSpec)
    
    print(f"\n📊 已注册引擎: {registry.list_engines()}")
    print(f"🔧 可用驱动: {json.dumps(registry.get_available_drivers(), indent=2)}")
    
    # 演示云数据库引擎
    print("\n☁️ 演示云数据库引擎:")
    cloud_spec = registry.get_engine_spec("customclouddb", "rest")
    if cloud_spec:
        print(f"   引擎名称: {cloud_spec.engine_name}")
        print(f"   支持的函数: {len(cloud_spec.get_function_names(None))} 个")
        print(f"   URI模板: {cloud_spec.sqlalchemy_uri_placeholder}")
        
        # 演示参数构建
        params = {
            "username": "api_user",
            "password": "api_secret",
            "host": "api.example.com",
            "port": 443,
            "database": "analytics",
            "encryption": True,
        }
        uri = cloud_spec.build_sqlalchemy_uri(params)
        print(f"   构建的URI: {uri}")
    
    # 演示时序数据库引擎
    print("\n📈 演示时序数据库引擎:")
    ts_spec = registry.get_engine_spec("tsdb", "influxdb")
    if ts_spec:
        print(f"   引擎名称: {ts_spec.engine_name}")
        print(f"   时间粒度: {list(ts_spec._time_grain_expressions.keys())}")
        print(f"   支持JOIN: {ts_spec.allows_joins}")
        
        # 演示函数列表
        functions = ts_spec.get_function_names(None)
        print(f"   时序函数: {functions[:10]}...")  # 显示前10个
    
    # 演示图数据库引擎
    print("\n🕸️ 演示图数据库引擎:")
    graph_spec = registry.get_engine_spec("graphdb", "bolt")
    if graph_spec:
        print(f"   引擎名称: {graph_spec.engine_name}")
        print(f"   查询语言: Cypher")
        print(f"   支持子查询: {graph_spec.allows_subqueries}")
        
        # 演示Cypher函数
        cypher_functions = graph_spec.get_function_names(None)
        print(f"   Cypher函数: {cypher_functions[:8]}...")  # 显示前8个
    
    return registry


def demo_oauth2_integration():
    """演示OAuth2集成"""
    print("\n🔐 OAuth2集成演示")
    print("=" * 60)
    
    # 创建OAuth2配置
    oauth2_config = OAuth2ClientConfig(
        id="superset_client_id",
        secret="superset_client_secret",
        scope="read write admin",
        redirect_uri="http://localhost:8088/oauth2",
        authorization_request_uri="https://auth.example.com/oauth2/authorize",
        token_request_uri="https://auth.example.com/oauth2/token",
    )
    
    # 创建数据库实例
    database = MockDatabase(1, CustomCloudDBEngineSpec)
    database.set_oauth2_config(oauth2_config)
    
    print(f"✓ OAuth2配置: {oauth2_config.id}")
    print(f"✓ 授权范围: {oauth2_config.scope}")
    
    # 模拟OAuth2流程
    try:
        print("\n🚀 启动OAuth2认证流程:")
        CustomCloudDBEngineSpec.start_oauth2_dance(database)
    except Exception as e:
        print(f"   OAuth2流程: {str(e)}")
    
    # 演示令牌交换（模拟）
    print("\n🔄 模拟令牌交换:")
    mock_token_response = OAuth2TokenResponse(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        refresh_token="refresh_token_example",
        expires_in=3600,
        token_type="Bearer"
    )
    print(f"   访问令牌: {mock_token_response.access_token[:50]}...")
    print(f"   过期时间: {mock_token_response.expires_in} 秒")
    print(f"   刷新令牌: {'是' if mock_token_response.refresh_token else '否'}")


def demo_parameter_configuration():
    """演示参数化配置"""
    print("\n⚙️ 参数化配置演示")
    print("=" * 60)
    
    # 演示基础参数配置
    print("1. 基础参数配置:")
    params = {
        "username": "db_user",
        "password": "db_password",
        "host": "database.example.com",
        "port": 5432,
        "database": "analytics",
        "query": {
            "sslmode": "require",
            "application_name": "superset",
        },
        "encryption": True,
    }
    
    # 使用云数据库引擎构建URI
    uri = CustomCloudDBEngineSpec.build_sqlalchemy_uri(params)
    print(f"   构建的URI: {uri}")
    
    # 从URI提取参数
    extracted_params = CustomCloudDBEngineSpec.get_parameters_from_uri(uri)
    print(f"   提取的参数: {json.dumps(extracted_params, indent=2)}")
    
    # 演示时序数据库参数
    print("\n2. 时序数据库参数:")
    ts_params = {
        "username": "ts_user",
        "password": "ts_password",
        "host": "influxdb.example.com",
        "port": 8086,
        "database": "metrics",
        "query": {
            "precision": "ms",
            "chunked": "true",
        },
    }
    
    ts_uri = TimeSeriesDBEngineSpec.build_sqlalchemy_uri(ts_params)
    print(f"   时序DB URI: {ts_uri}")


def demo_function_mapping():
    """演示函数映射"""
    print("\n🔧 函数映射演示")
    print("=" * 60)
    
    # 创建模拟数据库
    mock_db = MockDatabase(1, CustomCloudDBEngineSpec)
    
    # 获取不同引擎的函数
    engines = [
        ("云数据库", CustomCloudDBEngineSpec),
        ("时序数据库", TimeSeriesDBEngineSpec),
        ("图数据库", GraphDBEngineSpec),
    ]
    
    for name, engine_spec in engines:
        functions = engine_spec.get_function_names(mock_db)
        print(f"\n{name}函数 ({len(functions)} 个):")
        
        # 按类别分组显示
        if name == "云数据库":
            categories = {
                "聚合": ["COUNT", "SUM", "AVG", "MIN", "MAX"],
                "字符串": ["CONCAT", "SUBSTRING", "LENGTH", "UPPER", "LOWER"],
                "日期": ["NOW", "CURRENT_DATE", "DATE_TRUNC"],
                "数学": ["ABS", "CEIL", "FLOOR", "ROUND", "SQRT"],
                "窗口": ["ROW_NUMBER", "RANK", "LAG", "LEAD"],
            }
        elif name == "时序数据库":
            categories = {
                "聚合": ["MEAN", "MEDIAN", "SUM", "COUNT", "MIN", "MAX"],
                "时间": ["NOW", "TIME", "DURATION"],
                "变换": ["DERIVATIVE", "DIFFERENCE", "MOVING_AVERAGE"],
                "预测": ["HOLT_WINTERS", "LINEAR_REGRESSION"],
            }
        else:  # 图数据库
            categories = {
                "节点": ["NODES", "ID", "TYPE", "LABELS"],
                "路径": ["LENGTH", "SHORTEST_PATH"],
                "聚合": ["COUNT", "SUM", "COLLECT"],
                "字符串": ["SUBSTRING", "UPPER", "LOWER"],
            }
        
        for category, funcs in categories.items():
            available = [f for f in funcs if f in functions]
            if available:
                print(f"   {category}: {', '.join(available)}")


def main():
    """主演示函数"""
    print("🗄️ Day 8 自定义数据库驱动演示")
    print("=" * 60)
    
    try:
        # 演示自定义数据库引擎
        registry = demo_custom_database_engines()
        
        # 演示OAuth2集成
        demo_oauth2_integration()
        
        # 演示参数化配置
        demo_parameter_configuration()
        
        # 演示函数映射
        demo_function_mapping()
        
        print("\n" + "="*60)
        print("✅ 自定义数据库驱动演示完成！")
        print("\n📚 数据库扩展要点总结:")
        print("- 引擎规范：定义数据库特性和能力")
        print("- 参数化配置：灵活的连接参数管理")
        print("- OAuth2集成：现代化的认证机制")
        print("- 函数映射：数据库特定的函数支持")
        print("- 类型映射：标准化的数据类型处理")
        print("- 驱动支持：多种连接方式的支持")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 