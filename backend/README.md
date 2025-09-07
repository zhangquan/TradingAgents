# TradingAgents Backend API

A comprehensive backend API for the TradingAgents platform, providing real-time market data, trading analysis, and user administration.

## Features

### Core Trading Analysis
- **Real Analysis Engine**: Integrated with TradingAgentsGraph for actual market analysis
- **Multiple Analysts**: Market, News, Social Media, Fundamentals analysts
- **Task Management**: Background processing with real-time progress tracking
- **Report Generation**: Comprehensive trading reports and decisions

### User Management
- **User Profiles**: Create and manage user accounts
- **Personalization**: User-specific preferences and configurations
- **Authentication**: JWT-based security (simplified for demo)



### Real-Time Data
- **Stock Prices**: Real-time and historical price data
- **Market News**: Latest news from multiple sources
- **Company Fundamentals**: Financial metrics and company information
- **Market Indices**: Major market indicators (S&P 500, NASDAQ, etc.)
- **Stock Search**: Find stocks by symbol or company name

### Storage & Caching
- **Local File Storage**: JSON-based storage for all data
- **Smart Caching**: Automatic caching with TTL for performance
- **Data Management**: Backup, cleanup, and maintenance utilities

### Notifications & Events
- **Real-time Notifications**: Analysis completion, market alerts
- **System Events**: Comprehensive logging and monitoring
- **WebSocket Updates**: Live updates for connected clients

## API Endpoints

### Authentication & Configuration
```
GET  /health                    - Health check
GET  /config                    - Get current configuration
POST /config                    - Update API keys and settings
```

### User Management
```
POST /users                     - Create new user
GET  /users/me                  - Get current user info
PUT  /users/me                  - Update user profile
```

### Trading Analysis
```
POST /analysis/start            - Start new analysis task
GET  /analysis/tasks            - List user's tasks
GET  /analysis/task/{id}        - Get task status

DELETE /analysis/task/{id}      - Cancel running task
GET  /analysis/history          - Get analysis history
GET  /analysis/{id}             - Get specific analysis
```



### Real-Time Market Data
```
GET  /data/price/{symbol}       - Get real-time stock price
GET  /data/news/{symbol}        - Get latest stock news
GET  /data/fundamentals/{symbol} - Get company fundamentals
GET  /data/market               - Get market overview
GET  /data/trending             - Get trending stocks
GET  /data/search?q={query}     - Search stocks
POST /data/batch                - Get data for multiple symbols
```

### Reports & History
```
GET  /reports                   - List available reports
GET  /reports/{ticker}/{date}   - Get specific report
```

### Notifications
```
GET  /notifications             - Get user notifications
POST /notifications             - Create notification
PUT  /notifications/{id}/read   - Mark as read
```

### System Management
```
GET  /system/stats              - Get system statistics
GET  /system/logs               - Get system logs
POST /system/cleanup            - Clean up old data
GET  /data/cache/stats          - Get cache statistics
POST /data/cache/refresh        - Refresh data cache
```

### WebSocket
```
WS   /ws                        - System status updates
```

### Available Models
```
GET  /models                    - Get available LLM models
GET  /analysts                  - Get available analyst types
```

## Configuration

The system is configured through environment variables for security. All API keys and system settings must be set via environment variables.

### Environment Variables Setup

Create a `.env` file in the project root with your API keys:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
ALIYUN_API_KEY=your_aliyun_api_key_here
FINNHUB_API_KEY=your_finnhub_api_key_here
POLYGON_API_KEY=your_polygon_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here

# System Configuration
LLM_PROVIDER=aliyun
DEEP_THINK_LLM=qwen3-235b-a22b-instruct-2507
QUICK_THINK_LLM=qwen-plus
LLM_BACKEND_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Analysis Settings
MAX_DEBATE_ROUNDS=1
MAX_RISK_DISCUSS_ROUNDS=1
ONLINE_TOOLS=true

# Data Storage
TRADINGAGENTS_RESULTS_DIR=./results
TRADINGAGENTS_DATA_DIR=./data
```

### API Keys Required
- **OpenAI**: For GPT models (gpt-4o, gpt-4o-mini, etc.)
- **Google**: For Gemini models (gemini-2.0-flash, etc.)
- **Aliyun**: For Qwen models (qwen-max, qwen-plus, etc.)
- **Finnhub**: For financial data and news
- **Polygon**: For market data and price feeds
- **Reddit**: For social sentiment analysis

**⚠️ Security Note**: API keys are loaded from environment variables only. The system does not accept API keys through HTTP endpoints for security reasons.

### LLM Providers
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo
- **Google**: Gemini-2.0-flash, Gemini-1.5-pro, Gemini-1.5-flash
- **Aliyun**: Qwen-max, Qwen-plus, Qwen-turbo

### Analyst Types
- **Market Analyst**: Technical analysis and price patterns
- **News Analyst**: News sentiment and impact analysis
- **Social Media Analyst**: Social sentiment from Reddit/Twitter
- **Fundamentals Analyst**: Financial metrics and company analysis

## Storage Structure

The system uses local file storage organized as:

```
data/
├── users/              # User profiles and configs

├── analysis/           # Analysis results by user/ticker
├── config/             # System configurations
├── cache/              # Cached market data
├── notifications/      # User notifications
└── logs/              # System event logs
```

## Usage Examples

### Start Trading Analysis
```python
import requests

# Note: API keys are configured via environment variables
# Make sure your .env file is properly set up before starting

# Start analysis directly
analysis_request = {
    "ticker": "AAPL",
    "analysis_date": "2024-01-15",
    "analysts": ["market", "news", "fundamentals"],
    "research_depth": 2,
    "llm_provider": "openai",
    "shallow_thinker": "gpt-4o-mini",
    "deep_thinker": "gpt-4o"
}
response = requests.post("http://localhost:8000/analysis/start", json=analysis_request)
task_id = response.json()["task_id"]

# Monitor progress
import time
while True:
    status = requests.get(f"http://localhost:8000/analysis/task/{task_id}")
    if status.json()["status"] == "completed":
        break
    time.sleep(5)
```

### Get Real-Time Data
```python
# Get stock price
price = requests.get("http://localhost:8000/data/price/AAPL")
print(f"AAPL: ${price.json()['price']}")

# Get latest news
news = requests.get("http://localhost:8000/data/news/AAPL?limit=5")
for article in news.json()["news"]:
    print(f"- {article['title']}")

# Search stocks
search = requests.get("http://localhost:8000/data/search?q=apple")
for result in search.json()["results"]:
    print(f"{result['symbol']}: {result['name']}")
```

## Development

### Requirements
- Python 3.10+
- FastAPI
- uvicorn
- TradingAgents core modules

### Installation
```bash
# Install dependencies
uv pip install -r requirements.txt

# Run development server
python backend/main.py
```

### Environment Variables
```bash
export OPENAI_API_KEY=your_key
export FINNHUB_API_KEY=your_key
export POLYGON_API_KEY=your_key
export GOOGLE_API_KEY=your_key
export ALIYUN_API_KEY=your_key
export REDDIT_CLIENT_ID=your_id
export REDDIT_CLIENT_SECRET=your_secret
```

## Performance & Scaling

### Caching Strategy
- **Price Data**: 1-minute TTL
- **News Data**: 5-minute TTL  
- **Fundamentals**: 1-hour TTL
- **Analysis Results**: Permanent storage

### Rate Limiting
- Data APIs have built-in rate limiting
- Background tasks prevent API overload
- Caching reduces external API calls

### Monitoring
- System logs track all operations
- Performance metrics available via `/system/stats`
- Cache statistics via `/data/cache/stats`

## Security

### Authentication
- JWT-based authentication (simplified for demo)
- User isolation for all data access
- API key management per user

### Data Protection
- Local file storage (no external database)
- User data isolation
- Secure API key handling

## Support

For issues and feature requests, please refer to the main TradingAgents repository.
