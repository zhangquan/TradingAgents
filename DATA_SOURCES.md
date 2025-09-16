# 多数据源支持

本项目支持多种股票数据源，可以根据环境自动选择合适的数据源：

- **开发环境**: 使用 Polygon API
- **正式环境**: 使用 Yahoo Finance

## 环境配置

### 环境变量

通过设置以下环境变量来控制数据源选择：

```bash
# 环境设置
ENVIRONMENT=development  # 或 production

# 数据源设置（可选，留空则根据环境自动选择）
DATA_SOURCE=yahoo_finance  # 或 polygon

# API 密钥（仅开发环境需要）
POLYGON_API_KEY=your_polygon_api_key_here
```

### 自动选择逻辑

1. **环境检测**:
   - 如果 `ENVIRONMENT=production` 或 `NODE_ENV=production`，则使用 Yahoo Finance
   - 否则使用 Polygon API

2. **手动覆盖**:
   - 如果设置了 `DATA_SOURCE` 环境变量，则使用指定的数据源
   - 支持的值: `yahoo_finance`, `polygon`

## 使用方法

### 1. 开发环境（使用 Polygon API）

```bash
# 设置环境变量
export ENVIRONMENT=development
export POLYGON_API_KEY=your_polygon_api_key_here

# 启动服务
uv run python backend/main.py
```

### 2. 正式环境（使用 Yahoo Finance）

```bash
# 设置环境变量
export ENVIRONMENT=production

# 启动服务
uv run python backend/main.py
```

### 3. 强制使用特定数据源

```bash
# 强制使用 Yahoo Finance
export DATA_SOURCE=yahoo_finance

# 强制使用 Polygon API
export DATA_SOURCE=polygon
```

## API 端点

### 获取数据源状态

```http
GET /api/stock/data-source-status
```

响应示例：
```json
{
  "data_source_status": {
    "current_data_source": "yahoo_finance",
    "environment": "production",
    "is_production": true,
    "is_development": false,
    "polygon_available": false,
    "yahoo_finance_available": true,
    "config": {
      "environment": "production",
      "data_source": "yahoo_finance",
      "is_production": true,
      "is_development": false,
      "use_yahoo_finance": true,
      "use_polygon": false
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 健康检查

```http
GET /api/stock/health
```

响应示例：
```json
{
  "status": "healthy",
  "available_stocks_count": 4,
  "data_source": {
    "current_data_source": "yahoo_finance",
    "environment": "production",
    "is_production": true,
    "is_development": false,
    "polygon_available": false,
    "yahoo_finance_available": true
  },
  "timestamp": "2024-01-15T10:30:00.000Z",
  "service": "stock-data"
}
```

## 数据源特性对比

| 特性 | Yahoo Finance | Polygon API |
|------|---------------|-------------|
| API 密钥 | 不需要 | 需要 |
| 数据质量 | 高 | 高 |
| 更新频率 | 实时 | 实时 |
| 历史数据 | 丰富 | 丰富 |
| 免费额度 | 无限制 | 有限制 |
| 稳定性 | 高 | 高 |
| 缓存支持 | ✅ | ✅ |

## 测试

运行测试脚本验证多数据源功能：

```bash
# 测试所有数据源功能
uv run python test_data_sources.py
```

## 故障排除

### 1. Polygon API 密钥问题

如果使用 Polygon API 时遇到认证问题：

```bash
# 检查 API 密钥是否正确设置
echo $POLYGON_API_KEY

# 重新设置 API 密钥
export POLYGON_API_KEY=your_correct_api_key_here
```

### 2. 数据源切换问题

如果数据源没有按预期切换：

```bash
# 检查环境变量
echo "ENVIRONMENT: $ENVIRONMENT"
echo "DATA_SOURCE: $DATA_SOURCE"

# 强制使用特定数据源
export DATA_SOURCE=yahoo_finance  # 或 polygon
```

### 3. 缓存问题

如果遇到缓存相关的问题：

```python
# 清除特定股票的缓存
from tradingagents.dataflows.data_source_manager import DataSourceManager
manager = DataSourceManager()
manager.clear_cache("AAPL")  # 清除 AAPL 的缓存

# 清除所有缓存
manager.clear_cache()  # 清除所有缓存
```

## 开发说明

### 添加新的数据源

1. 在 `tradingagents/dataflows/` 目录下创建新的数据源工具类
2. 实现与 `PolygonUtils` 和 `YahooDataUtils` 相同的接口
3. 在 `DataSourceManager` 中添加新数据源的支持
4. 更新环境配置以支持新数据源

### 修改数据源选择逻辑

编辑 `tradingagents/dataflows/environment_config.py` 文件中的 `_get_data_source_for_environment` 方法。

## 注意事项

1. **API 限制**: Polygon API 有免费额度限制，建议在开发环境使用
2. **数据一致性**: 不同数据源的数据格式可能略有差异，但核心字段保持一致
3. **缓存策略**: 两种数据源都支持智能缓存，提高数据获取效率
4. **错误处理**: 如果主要数据源失败，系统会尝试回退到备用数据源