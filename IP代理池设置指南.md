# IP 代理池设置指南

## 1. 概述

IP 代理轮换功能允许您在爬虫任务中使用多个代理 IP，以避免被目标网站封锁。系统支持两种代理池配置方式：环境变量和 API 接口。

## 2. 配置方式

### 2.1 通过环境变量设置

在 `.env` 文件中添加以下配置：

```env
# 启用代理轮换
PROXY_ROTATION_ENABLED=true

# 代理轮换模式：per_task（每个任务使用一个代理）或 on_failure（失败时轮换）
PROXY_ROTATION_MODE=per_task

# 代理池：逗号分隔的代理列表
PROXY_POOL=http://proxy1:port,http://proxy2:port,http://proxy3:port

# 重试次数
PROXY_ROTATION_RETRY_LIMIT=2

# 代理黑名单时间（秒）
PROXY_BLACKLIST_TTL=300
```

### 2.2 通过 API 接口设置

使用 PUT 请求更新代理设置：

**请求 URL**：`/api/settings/rotation`

**请求方法**：PUT

**请求体**：
```json
{
  "PROXY_ROTATION_ENABLED": true,
  "PROXY_ROTATION_MODE": "per_task",
  "PROXY_POOL": "http://proxy1:port,http://proxy2:port,http://proxy3:port",
  "PROXY_ROTATION_RETRY_LIMIT": 2,
  "PROXY_BLACKLIST_TTL": 300
}
```

**响应**：
```json
{"message": "轮换设置已成功更新"}
```

## 3. 代理池格式

代理池使用逗号分隔的代理列表，支持 HTTP 和 HTTPS 代理：

```
# 基本格式
http://proxy1:port,http://proxy2:port,http://proxy3:port

# 带认证的代理
http://username:password@proxy1:port,http://username:password@proxy2:port

# 混合格式
http://proxy1:port,https://proxy2:port,http://username:password@proxy3:port
```

## 4. 代理轮换模式

系统支持两种代理轮换模式：

### 4.1 per_task（默认）

- 每个任务使用一个代理完成整个爬取过程
- 适用于需要会话保持的场景

### 4.2 on_failure

- 正常情况下使用同一代理
- 当请求失败时自动切换到下一个代理
- 适用于频繁遇到IP封锁的场景

## 5. 代理管理机制

### 5.1 黑名单机制

- 当代理请求失败时，该代理会被加入黑名单
- 黑名单时间由 `PROXY_BLACKLIST_TTL` 配置（默认300秒）
- 超过黑名单时间后，代理会自动恢复可用

### 5.2 随机选择

- 系统从可用代理池中随机选择一个代理
- 确保代理使用的均衡性

## 6. 示例配置

### 6.1 基本配置

```env
PROXY_ROTATION_ENABLED=true
PROXY_ROTATION_MODE=per_task
PROXY_POOL=http://192.168.1.100:8080,http://192.168.1.101:8080,http://192.168.1.102:8080
```

### 6.2 高级配置

```env
PROXY_ROTATION_ENABLED=true
PROXY_ROTATION_MODE=on_failure
PROXY_POOL=http://user:pass@proxy1:3128,http://user:pass@proxy2:3128,http://user:pass@proxy3:3128
PROXY_ROTATION_RETRY_LIMIT=3
PROXY_BLACKLIST_TTL=600
```

## 7. 验证配置

您可以通过以下方式验证代理配置是否生效：

1. **查看日志**：任务执行时会显示使用的代理信息
   ```
   IP 轮换：使用代理 http://proxy1:port
   ```

2. **API 查询**：调用 `/api/settings/rotation` 获取当前配置

3. **测试任务**：创建一个简单的测试任务，观察是否使用了代理

## 8. 注意事项

1. **代理可用性**：确保提供的代理都是可用的，无效代理会影响爬取效率
2. **代理质量**：选择高质量的代理服务，避免使用公共代理
3. **认证信息**：如果代理需要认证，请确保用户名和密码正确
4. **协议一致性**：使用与目标网站相同的协议（HTTP/HTTPS）
5. **性能影响**：过多的代理可能会增加系统负担，建议根据实际需求配置合适数量的代理

## 9. 常见问题

### 9.1 代理不生效

- 检查 `PROXY_ROTATION_ENABLED` 是否设置为 `true`
- 确认代理格式是否正确
- 测试代理是否可以正常访问目标网站

### 9.2 代理轮换不工作

- 检查 `PROXY_ROTATION_MODE` 配置是否正确
- 查看日志确认是否有代理被加入黑名单
- 确保代理池中有多个可用代理

### 9.3 任务失败频繁

- 增加 `PROXY_ROTATION_RETRY_LIMIT` 的值
- 延长 `PROXY_BLACKLIST_TTL` 时间
- 更换质量更好的代理服务

## 10. 代码实现

IP 代理轮换功能主要由以下文件实现：

- `src/rotation.py`：代理池管理类 `RotationPool`
- `src/scraper.py`：代理轮换配置和使用逻辑
- `src/api/routes/settings.py`：代理配置 API 接口

如需了解更多实现细节，请查看相关代码文件。