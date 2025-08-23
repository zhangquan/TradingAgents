# Polygon.io 集成使用说明

## 概述

本项目已集成 Polygon.io API 来替代 YFIN 数据功能，提供更可靠和实时的股票市场数据。

## 安装依赖

使用 uv 包管理器安装新的依赖：

```bash
uv sync
```

## 环境配置

在环境变量中设置 Polygon.io API 密钥：

```bash
export POLYGON_API_KEY="your_polygon_api_key_here"
```

或者在 `.env` 文件中添加：

```
POLYGON_API_KEY=your_polygon_api_key_here
```

## 获取 API 密钥

1. 访问 [Polygon.io](https://polygon.io/)
2. 注册账户并选择适合的计划
3. 在控制台中获取 API 密钥

## 使用方法

### 1. 使用 PolygonToolkit

```python
from tradingagents.agents.utils.agent_polygon_util import PolygonToolkit

# 创建工具包实例
toolkit = PolygonToolkit()

# 获取股票数据
data = toolkit.get_polygon_data("AAPL", "2024-01-01", "2024-01-31")

# 获取公司信息
info = toolkit.get_polygon_company_info("AAPL")

# 获取股息信息
dividends = toolkit.get_polygon_dividends("AAPL")

# 获取股票分割信息
splits = toolkit.get_polygon_splits("AAPL")
```

### 2. 直接使用接口函数

```python
from tradingagents.dataflows.polygon_interface import (
    get_polygon_data,
    get_polygon_company_info,
    get_polygon_dividends,
    get_polygon_splits
)

# 获取股票数据
data = get_polygon_data("AAPL", "2024-01-01", "2024-01-31")

# 获取公司信息
info = get_polygon_company_info("AAPL")
```

### 3. 使用 PolygonUtils 类

```python
from tradingagents.dataflows.polygon_utils import PolygonUtils

# 创建工具实例
polygon_utils = PolygonUtils()

# 获取股票数据
df = polygon_utils.get_stock_data("AAPL", "2024-01-01", "2024-01-31")

# 获取公司信息
info = polygon_utils.get_stock_info("AAPL")
```

## 功能对比

| 功能 | YFIN (原) | Polygon.io (新) |
|------|-----------|-----------------|
| 股票价格数据 | ✅ | ✅ |
| 公司信息 | ✅ | ✅ |
| 股息数据 | ✅ | ✅ |
| 股票分割 | ✅ | ✅ |
| 实时数据 | ❌ | ✅ |
| 数据可靠性 | 中等 | 高 |
| API 限制 | 宽松 | 按计划 |

## 数据格式

### 股票价格数据

返回的数据包含以下列：
- `Date`: 日期
- `Open`: 开盘价
- `High`: 最高价
- `Low`: 最低价
- `Close`: 收盘价
- `Volume`: 成交量
- `VWAP`: 成交量加权平均价
- `Transactions`: 交易笔数

### 公司信息

返回的数据包含：
- `Company Name`: 公司名称
- `Industry`: 行业
- `Sector`: 板块
- `Country`: 国家
- `Website`: 网站
- `Market Cap`: 市值
- `Employees`: 员工数
- `Description`: 公司描述

## 错误处理

所有函数都包含错误处理，如果 API 调用失败，会返回相应的错误信息而不是抛出异常。

## 注意事项

1. **API 限制**: 根据您的 Polygon.io 计划，可能有 API 调用次数限制
2. **数据延迟**: 实时数据可能有几秒到几分钟的延迟
3. **市场时间**: 数据仅在市场开放时间可用
4. **时区**: 所有时间戳都使用 UTC 时区

## 故障排除

### 常见问题

1. **API 密钥错误**
   - 确保环境变量 `POLYGON_API_KEY` 已正确设置
   - 检查 API 密钥是否有效

2. **无数据返回**
   - 检查股票代码是否正确
   - 确认日期范围是否有效
   - 验证是否为交易日

3. **API 限制错误**
   - 检查您的 Polygon.io 计划限制
   - 考虑升级计划或减少调用频率

### 调试

启用详细日志记录：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 迁移指南

如果您正在从 YFIN 迁移到 Polygon.io：

1. 将 `get_YFin_data` 替换为 `get_polygon_data`
2. 将 `get_YFin_data_online` 替换为 `get_polygon_data`
3. 更新任何直接使用 YFinance 的代码

示例：

```python
# 旧代码
from tradingagents.agents.utils.agent_utils import Toolkit
data = Toolkit.get_YFin_data("AAPL", "2024-01-01", "2024-01-31")

# 新代码
from tradingagents.agents.utils.agent_polygon_util import PolygonToolkit
data = PolygonToolkit.get_polygon_data("AAPL", "2024-01-01", "2024-01-31")
``` 