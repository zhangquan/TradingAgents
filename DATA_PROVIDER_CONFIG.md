# Data Provider Configuration System

This document explains the configurable stock data API system that allows switching between different data providers based on environment configuration.

## Overview

The system supports multiple stock data providers:
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

2. **`tradingagents/dataflows/data_provider_interface.py`**
   - `DataProviderInterface` protocol
   - Provider implementations (`PolygonDataProvider`, `YahooFinanceDataProvider`)
   - `DataProviderFactory` for creating provider instances

3. **`backend/services/data_services.py`**
   - Updated `DataServices` class to use configurable providers
   - Automatic fallback to Polygon if primary provider fails

### Provider Implementations

#### Polygon Provider
- Uses existing `PolygonUtils` 
- Supports caching and API key requirements
- Best for development with detailed market data

#### Yahoo Finance Provider
- Uses `yfinance` library
- No API key required
- Standardizes column names to match Polygon format
- Good for production with reliable free data

#### Finnhub Provider
- Placeholder for future implementation
- Requires API key configuration

## Usage Examples

### Backend Service Initialization
```python
from backend.services.data_services import DataServices

# Use default provider from config
service = DataServices(require_api_key=False)

# Override provider explicitly
service = DataServices(require_api_key=False, data_provider="yahoo")

# Get provider information
info = service.get_data_provider_info()
print(f"Using {info['provider_name']} provider")
```

### Trading Agents Integration
```python
from tradingagents.dataflows.data_provider_interface import DataProviderFactory

# Create provider based on config
provider = DataProviderFactory.create_provider(
    DEFAULT_CONFIG["data_provider"], 
    require_api_key=False
)

# Get stock data
data = provider.get_stock_data_window("AAPL", "2025-01-15", 30)
```

## Benefits

1. **Environment Flexibility** - Different providers for dev/prod
2. **Fallback Safety** - Automatic fallback to Polygon if primary fails
3. **API Compatibility** - Unified interface across providers
4. **Easy Configuration** - Simple environment variable setup
5. **Cost Optimization** - Use free providers in prod, detailed providers in dev

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

- Existing Polygon-based functionality continues to work
- No breaking changes to existing APIs
- Additional providers can be easily added to the factory
- Configuration is backward compatible