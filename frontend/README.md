# TradingAgents Frontend

A modern, responsive web application for the TradingAgents trading analysis platform built with Next.js 15, React 19, and TypeScript.

## Features

### 🎯 **Complete Trading Platform**
- **Real-time Dashboard**: Market overview, system status, and quick actions
- **Trading Analysis**: AI-powered multi-agent analysis

- **Market Data**: Live stock prices, charts, and news feeds
- **Report Management**: View and manage analysis reports
- **System Settings**: Configuration and user preferences

### 🚀 **Modern Technologies**
- **Next.js 15**: Latest React framework with App Router
- **React 19**: Cutting-edge React features and performance
- **TypeScript**: Full type safety and developer experience
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible, unstyled UI components
- **Recharts**: Powerful charting library for data visualization
- **Lucide React**: Beautiful, customizable icons

### 🎨 **UI/UX Excellence**
- **Responsive Design**: Mobile-first approach, works on all devices
- **Modern Interface**: Clean, professional design language
- **Dark/Light Mode**: Theme switching (configurable)
- **Accessibility**: WCAG compliant components
- **Loading States**: Skeleton screens and progress indicators
- **Error Handling**: Graceful error boundaries and user feedback

### ⚡ **Real-time Features**
- **WebSocket Connection**: Live system status updates
- **Auto-refresh**: Smart data refreshing with caching
- **Push Notifications**: System alerts and notifications

### 📊 **Data Visualization**
- **Interactive Charts**: Stock price trends and market data visualization
- **Real-time Updates**: Live market data and price changes
- **Performance Metrics**: Market analytics and price tracking
- **Technical Indicators**: Advanced charting capabilities

## Architecture

### Component Structure
```
src/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Dashboard (/)
│   ├── analysis/          # Analysis management

│   ├── market/           # Market data and charts
│   ├── reports/          # Analysis reports
│   └── settings/         # System configuration
├── components/
│   ├── ui/               # Reusable UI components
│   ├── charts/           # Data visualization components
│   └── navigation.tsx    # Main navigation
├── hooks/                # Custom React hooks
│   ├── useWebSocket.ts   # Real-time connections
│   └── useNotifications.ts # Notification management
└── lib/
    ├── api.ts            # API client and types
    └── utils.ts          # Utility functions
```

### State Management
- **React State**: Local component state with hooks
- **Context API**: Global user and notification state
- **Real-time Updates**: WebSocket integration for system status
- **Caching**: Smart data caching with TTL

### API Integration
- **Type-safe Client**: Full TypeScript API client
- **Authentication**: JWT token management
- **Error Handling**: Centralized error processing
- **Request Interceptors**: Automatic auth headers
- **Response Formatting**: Consistent data structures

## Key Pages

### 🏠 **Dashboard** (`/`)
- System overview and statistics
- Real-time market indices and trending stocks
- Recent analysis tasks and system health
- Quick stock search and analysis shortcuts
- WebSocket connection status and notifications

### 📈 **Analysis** (`/analysis`)
- Create new trading analysis tasks
- Task management (start, stop, cancel)
- Multiple analyst types and LLM providers
- Historical analysis records



### 🌍 **Market** (`/market`)
- Live market data and stock prices
- Interactive price charts with 30-day history
- Stock search and watchlist management
- Latest news feeds for selected stocks
- Market indices and trending stocks

### 📋 **Reports** (`/reports`)
- Analysis report browser and viewer
- Filter by ticker, date, and analyst type
- Markdown report rendering
- Export and sharing capabilities
- Historical report archive

### ⚙️ **Settings** (`/settings`)
- API key configuration
- LLM provider settings
- User preferences and notifications
- System maintenance and cache management

## Custom Hooks

### `useWebSocket`
```typescript
const { data, isConnected, error } = useWebSocket(userId, enabled)
```
- Real-time connection management
- Automatic reconnection logic
- Connection status monitoring
- Data streaming and processing

### `useNotifications`
```typescript
const { notifications, unreadCount, markAsRead } = useNotifications()
```
- Notification state management
- Real-time notification updates
- Read/unread status tracking
- Toast integration



## Components

### Chart Components
- **StockChart**: Line/area charts for price data

- Responsive design with tooltips
- Customizable colors and themes
- Real-time data updates

### UI Components (Radix UI)
- **Card**: Content containers with headers
- **Button**: Various sizes and variants
- **Input**: Form inputs with validation
- **Select**: Dropdown selections
- **Dialog**: Modal dialogs and forms
- **Badge**: Status indicators
- **Progress**: Loading and progress bars
- **Tabs**: Tabbed interfaces

## Styling

### Tailwind CSS
- Utility-first CSS framework
- Responsive design utilities
- Custom color scheme
- Component variants
- Animation and transitions

### Design System
- Consistent spacing (4px grid)
- Typography scale (text-sm to text-3xl)
- Color palette (blue primary, semantic colors)
- Shadow system (subtle to pronounced)
- Border radius (rounded corners)

## Performance

### Optimization Strategies
- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js image component
- **Lazy Loading**: Component and data lazy loading
- **Caching**: API response caching with TTL
- **Debouncing**: Search input and API calls

### Bundle Analysis
- Tree shaking for optimal bundle size
- Dynamic imports for large components
- External library optimization
- Font optimization and preloading

## Development

### Getting Started
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Environment Variables
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000  # Backend API URL
```

### Scripts
- `dev`: Development server with hot reloading
- `build`: Production build optimization
- `start`: Production server
- `lint`: ESLint code quality checks
- `type-check`: TypeScript compilation check

## API Integration

### Backend Communication
- **Base URL**: Configurable API endpoint
- **Authentication**: Bearer token in headers
- **Error Handling**: Centralized error processing
- **Rate Limiting**: Built-in request throttling
- **Retry Logic**: Automatic retry for failed requests

### Real-time Features
- **WebSocket**: `/ws` for system status updates
- **Polling**: Manual refresh for task status updates

## Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile Browsers**: iOS Safari 14+, Chrome Mobile 90+
- **Features**: ES2020, WebSocket, SSE, Fetch API
- **Polyfills**: Automatic polyfill injection for older browsers

## Deployment

### Production Build
```bash
npm run build
npm start
```

### Docker Support
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Configuration
- Production API URLs
- CDN integration for static assets
- Performance monitoring
- Error tracking integration

## Testing

### Testing Strategy
- **Component Tests**: React Testing Library
- **Integration Tests**: End-to-end workflows
- **Type Safety**: TypeScript compilation
- **Linting**: ESLint and Prettier
- **Performance**: Lighthouse CI

### Quality Assurance
- Code review requirements
- Automated testing pipeline
- Performance benchmarks
- Accessibility audits
- Security scanning

## Future Enhancements

### Planned Features
- **Advanced Charts**: Candlestick and technical indicators
- **Real-time Trading**: Order placement and execution
- **Mobile App**: React Native companion app
- **AI Insights**: Enhanced analysis recommendations
- **Social Features**: Share analysis results

### Technical Improvements
- **PWA Support**: Offline functionality
- **GraphQL Integration**: More efficient data fetching
- **Micro-frontends**: Modular architecture
- **Advanced Caching**: Redis integration
- **Performance Monitoring**: Real-time metrics

This frontend provides a comprehensive, modern interface for the TradingAgents platform, combining powerful functionality with excellent user experience and real-time capabilities.