# Configurable Data Provider System

This document explains the configurable stock data API system that allows switching between different data providers based on environment configuration through function arguments and toolkit configuration.

## Overview

The system supports multiple stock data providers through configurable toolkits:
- **Polygon.io** - Professional financial data API (requires API key)
- **Yahoo Finance** - Free stock data service
- **Finnhub** - Financial data API (placeholder for future implementation)

## Environment-Based Configuration

The system automatically selects the appropriate data provider based on the environment:

| Environment | Default Provider | Description |
|-------------|-----------------|-------------|
| `dev` | `polygon` | Development environment uses Polygon for detailed data |
| `pro` | `yahoo` | Production environment uses Yahoo Finance for reliability |
| `test` | `polygon` | Test environment uses Polygon for consistency |

## Configuration Methods

### 1. Automatic Selection (Recommended)

Set only the `ENVIRONMENT` variable:

```bash
# Development
export ENVIRONMENT=dev
# Automatically selects Polygon

# Production  
export ENVIRONMENT=pro
# Automatically selects Yahoo Finance
```

### 2. Explicit Provider Selection

Override the automatic selection:

```bash
export ENVIRONMENT=pro
export DATA_PROVIDER=polygon
# Forces Polygon even in production
```

### 3. Configuration Priority

The system follows this priority order:
1. Explicit `DATA_PROVIDER` environment variable
2. Environment-based mapping (`ENVIRONMENT` → provider)
3. Default fallback to `polygon`

## Startup Scripts

The startup scripts have been updated to set the appropriate environment variables:

### Development Environment
```bash
./start-dev.sh
# Sets: ENVIRONMENT=dev, DATA_PROVIDER=polygon
```

### Production Environment
```bash
./start-pro.sh
# Sets: ENVIRONMENT=pro, DATA_PROVIDER=yahoo
```

## API Endpoints

### Provider Information
```http
GET /api/stock/provider-info
```

Returns current data provider information:
```json
{
  "provider_name": "yahoo",
  "is_available": true,
  "require_api_key": false,
  "environment": "pro",
  "timestamp": "2025-01-16T..."
}
```

### Health Check
```http
GET /api/stock/health
```

Now includes data provider information:
```json
{
  "status": "healthy",
  "available_stocks_count": 9,
  "data_provider": {
    "provider_name": "yahoo",
    "is_available": true,
    "require_api_key": false,
    "environment": "pro"
  },
  "timestamp": "2025-01-16T...",
  "service": "stock-data"
}
```

## Code Structure

### Core Components

1. **`tradingagents/default_config.py`**
   - Contains environment-based provider mapping
   - `get_data_provider_for_environment()` function

2. **`tradingagents/agents/utils/configurable_data_toolkit.py`**
   - `ConfigurableDataToolkit` class that switches providers based on config
   - `create_data_toolkit()` factory function
   - Tools that automatically use the configured data provider

3. **Agent Functions (e.g., `market_analyst.py`, `news_analyst.py`)**
   - Updated to accept `data_toolkit` parameter instead of `polygon_toolkit`
   - Automatic fallback to default toolkit if none provided

### Toolkit Configuration

#### ConfigurableDataToolkit
- Automatically selects provider based on configuration
- Provides unified tool interface (`get_stock_data_window`, `get_stockstats_indicators_report_window`)
- Switches between Polygon and Yahoo Finance implementations
- Handles errors gracefully with informative messages

#### Provider Switching Logic
- **Polygon**: Uses existing `polygon_interface` functions
- **Yahoo Finance**: Uses `get_yfinance_data` function for price data
- **Fallback**: Defaults to Polygon if provider not recognized

## Usage Examples

### Agent Creation with Data Provider Configuration
```python
from tradingagents.agents.analysts.market_analyst import create_market_analyst
from tradingagents.agents.utils.configurable_data_toolkit import create_data_toolkit

# Create toolkit with specific provider
config = {"data_provider": "yahoo", "environment": "pro"}
data_toolkit = create_data_toolkit(config)

# Create market analyst with Yahoo Finance data
market_analyst = create_market_analyst(llm, toolkit, data_toolkit, config)
```

### Trading Graph Integration
```python
from tradingagents.graph.trading_graph import TradingAgentsGraph

# Set environment to use Yahoo Finance in production
config = {"environment": "pro", "data_provider": "yahoo"}
graph = TradingAgentsGraph(config=config)

# The graph will automatically create data toolkits with Yahoo Finance
```

### Direct Toolkit Usage
```python
from tradingagents.agents.utils.configurable_data_toolkit import create_data_toolkit

# Create toolkit for development (uses Polygon)
dev_toolkit = create_data_toolkit({"environment": "dev"})

# Create toolkit for production (uses Yahoo Finance)  
pro_toolkit = create_data_toolkit({"environment": "pro"})

# Get provider information
print(dev_toolkit.get_provider_info())  # {'provider': 'polygon', 'environment': 'dev'}
print(pro_toolkit.get_provider_info())  # {'provider': 'yahoo', 'environment': 'pro'}
```

## Benefits

1. **Function-Level Configuration** - Pass data provider config directly to agent functions
2. **Environment Flexibility** - Different providers for dev/prod environments
3. **Backward Compatibility** - Existing code continues to work with polygon_toolkit
4. **Simple Integration** - Just pass data_toolkit instead of polygon_toolkit
5. **Cost Optimization** - Use free providers in prod, detailed providers in dev
6. **Unified Tool Interface** - Same tool names regardless of underlying provider

## Testing

The configuration can be tested by setting environment variables and checking the selected provider:

```bash
# Test development config
export ENVIRONMENT=dev
# Should select Polygon

# Test production config  
export ENVIRONMENT=pro
# Should select Yahoo Finance

# Test explicit override
export ENVIRONMENT=pro
export DATA_PROVIDER=polygon
# Should use Polygon despite pro environment
```

## Migration Notes

- **Backward Compatibility**: Existing `polygon_toolkit` usage continues to work
- **Simple Migration**: Replace `polygon_toolkit` parameter with `data_toolkit` in agent functions
- **No Breaking Changes**: Existing APIs and tool names remain the same
- **Easy Extension**: New providers can be added to `ConfigurableDataToolkit`
- **Function-Level Control**: Each agent can use different data providers if needed

## Function Signature Changes

### Before (Polygon-only)
```python
def create_market_analyst(llm, toolkit, polygon_toolkit, config=None):
```

### After (Configurable)
```python  
def create_market_analyst(llm, toolkit, data_toolkit=None, config=None):
```

The new approach allows:
- Passing a configured `data_toolkit` that uses any provider
- Automatic fallback to polygon_toolkit for backward compatibility
- Environment-based provider selection through configuration