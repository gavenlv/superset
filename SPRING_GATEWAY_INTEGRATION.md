# Spring Gateway 与 Superset 集成指南

## 概述

本指南介绍如何使用 Spring Cloud Gateway 与 Apache Superset 进行集成，实现：

1. **公共 Swagger UI 访问** - 无需登录即可查看 API 文档
2. **安全的 API 调用** - 通过 JWT token 进行身份验证
3. **OpenAPI 规范暴露** - 为 API Gateway 提供服务发现

## Superset 配置更改

### 1. 公共角色和权限

```python
# superset_config.py

# 启用公共角色
AUTH_ROLE_PUBLIC = 'Public'

# 为 Swagger UI 配置公共权限
PUBLIC_SWAGGER_PERMISSIONS = [
    ("can_show", "SwaggerView"),
    ("menu_access", "OpenApi"), 
    ("can_get", "OpenApi"),
    ("can_get", "Api"),
    ("can_list", "Api"),
]
```

### 2. CORS 配置

```python
# 启用 CORS 以支持 API Gateway
ENABLE_CORS = True
CORS_OPTIONS = {
    "origins": ["*"],  # 生产环境中应限制为具体的 Gateway 域名
    "supports_credentials": True,
    "allow_headers": [
        "Content-Type",
        "Authorization", 
        "X-Requested-With",
        "X-API-Key",
        "X-Gateway-Authorization",
        "Accept",
        "Origin"
    ],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    "expose_headers": [
        "Content-Type",
        "Authorization",
        "X-Total-Count"
    ]
}
```

### 3. JWT 认证配置

```python
# JWT 配置
JWT_SECRET_KEY = "your-secure-jwt-secret-key"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时
JWT_REFRESH_TOKEN_EXPIRES = 30 * 24 * 3600  # 30天
ENABLE_JWT_AUTHENTICATION = True
```

## Spring Gateway 配置

### 1. application.yml 配置

```yaml
spring:
  cloud:
    gateway:
      routes:
        # Superset OpenAPI 规范路由（公共访问）
        - id: superset-openapi
          uri: http://superset:8088
          predicates:
            - Path=/superset/openapi/**
          filters:
            - RewritePath=/superset/openapi/(?<segment>.*), /openapi/$\{segment}
            - AddResponseHeader=Access-Control-Allow-Origin, *
            
        # Superset Swagger UI 路由（公共访问）
        - id: superset-swagger
          uri: http://superset:8088
          predicates:
            - Path=/superset/swagger/**
          filters:
            - RewritePath=/superset/swagger/(?<segment>.*), /swagger/$\{segment}
            
        # Superset API 路由（需要认证）
        - id: superset-api
          uri: http://superset:8088
          predicates:
            - Path=/superset/api/**
          filters:
            - RewritePath=/superset/api/(?<segment>.*), /api/$\{segment}
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
                
        # Superset 认证路由
        - id: superset-auth
          uri: http://superset:8088
          predicates:
            - Path=/superset/auth/**
          filters:
            - RewritePath=/superset/auth/(?<segment>.*), /api/v1/security/$\{segment}
            
      globalcors:
        corsConfigurations:
          '[/**]':
            allowedOrigins: ["*"]
            allowedMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            allowedHeaders: ["*"]
            allowCredentials: true
```

### 2. JWT 认证过滤器

```java
@Component
public class JwtAuthenticationFilter implements GatewayFilter, Ordered {
    
    private final JwtUtils jwtUtils;
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        
        // 跳过公共端点
        if (isPublicEndpoint(request.getPath().toString())) {
            return chain.filter(exchange);
        }
        
        // 检查 JWT token
        String token = extractToken(request);
        if (token != null && jwtUtils.validateToken(token)) {
            // 添加用户信息到请求头
            ServerHttpRequest modifiedRequest = request.mutate()
                .header("X-User-Id", jwtUtils.getUserIdFromToken(token))
                .header("X-User-Roles", jwtUtils.getRolesFromToken(token))
                .build();
                
            return chain.filter(exchange.mutate().request(modifiedRequest).build());
        }
        
        // 未认证，返回 401
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(HttpStatus.UNAUTHORIZED);
        return response.setComplete();
    }
    
    private boolean isPublicEndpoint(String path) {
        return path.startsWith("/superset/openapi/") ||
               path.startsWith("/superset/swagger/") ||
               path.startsWith("/superset/auth/login");
    }
    
    private String extractToken(ServerHttpRequest request) {
        String bearerToken = request.getHeaders().getFirst("Authorization");
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
    
    @Override
    public int getOrder() {
        return -1;
    }
}
```

### 3. Gateway 过滤器配置

```java
@Configuration
public class GatewayConfig {
    
    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            .route("superset-api", r -> r.path("/superset/api/**")
                .filters(f -> f
                    .rewritePath("/superset/api/(?<segment>.*)", "/api/${segment}")
                    .filter(new JwtAuthenticationFilter())
                    .retry(3))
                .uri("http://superset:8088"))
            .build();
    }
}
```

## 使用示例

### 1. 获取 OpenAPI 规范

```bash
# 通过 API Gateway 获取 Superset OpenAPI 规范
curl -X GET "http://gateway:8080/superset/openapi/spec" \
  -H "Accept: application/json"
```

### 2. 用户认证流程

```bash
# 1. 通过 Gateway 登录获取 JWT token
curl -X POST "http://gateway:8080/superset/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# 返回: {"access_token": "eyJ...", "refresh_token": "eyJ..."}

# 2. 使用 JWT token 调用 API
curl -X GET "http://gateway:8080/superset/api/v1/chart/" \
  -H "Authorization: Bearer eyJ..."
```

### 3. Swagger UI 访问

```bash
# 直接访问 Swagger UI（无需认证）
curl -X GET "http://gateway:8080/superset/swagger/v1"
```

## 部署步骤

### 1. 更新 Superset 配置

```bash
# 1. 应用新的配置
cp superset_config.py /path/to/superset/
cd /path/to/superset
superset init

# 2. 重启 Superset
systemctl restart superset
```

### 2. 部署 Spring Gateway

```bash
# 1. 构建 Gateway 应用
mvn clean package -DskipTests

# 2. 部署到容器
docker build -t superset-gateway .
docker run -d --name superset-gateway \
  -p 8080:8080 \
  -e SUPERSET_URL=http://superset:8088 \
  superset-gateway
```

### 3. 验证集成

```bash
# 运行测试脚本
python test_api_gateway_access.py http://gateway:8080
```

## 安全注意事项

### 1. 生产环境配置

```python
# 生产环境中的安全配置
CORS_OPTIONS = {
    "origins": ["https://your-gateway-domain.com"],  # 限制特定域名
    "supports_credentials": True,
}

# 使用强密钥
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")  # 从环境变量读取
```

### 2. API 速率限制

```yaml
# Gateway 中配置速率限制
filters:
  - name: RequestRateLimiter
    args:
      redis-rate-limiter.replenishRate: 10
      redis-rate-limiter.burstCapacity: 20
```

### 3. 日志和监控

```java
@Component
public class ApiLoggingFilter implements GatewayFilter {
    private static final Logger logger = LoggerFactory.getLogger(ApiLoggingFilter.class);
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        
        logger.info("API Request: {} {}", request.getMethod(), request.getURI());
        
        return chain.filter(exchange).then(
            Mono.fromRunnable(() -> {
                ServerHttpResponse response = exchange.getResponse();
                logger.info("API Response: {}", response.getStatusCode());
            })
        );
    }
}
```

## 故障排除

### 1. CORS 问题

```bash
# 检查 CORS 头
curl -I -X OPTIONS "http://gateway:8080/superset/openapi/spec" \
  -H "Origin: http://localhost:3000"
```

### 2. JWT 认证问题

```bash
# 验证 JWT token
curl -X GET "http://gateway:8080/superset/api/v1/chart/" \
  -H "Authorization: Bearer <token>" \
  -v
```

### 3. 网关路由问题

```bash
# 查看 Gateway 路由配置
curl -X GET "http://gateway:8080/actuator/gateway/routes"
```

## 总结

这个集成方案实现了：

- ✅ **Swagger UI 公共访问** - 开发者可以无需登录查看 API 文档
- ✅ **安全的 API 调用** - 所有 API 调用都需要有效的 JWT token
- ✅ **OpenAPI 规范暴露** - API Gateway 可以获取完整的 API 规范
- ✅ **CORS 支持** - 支持跨域请求
- ✅ **速率限制** - 防止 API 滥用
- ✅ **监控和日志** - 完整的请求追踪 