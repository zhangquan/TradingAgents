"""
股票数据 API 路由器
基于 backend/services/data_services.py 提供股票数据和技术指标服务
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional, Union
import logging
from datetime import datetime
from pydantic import BaseModel

from backend.services.data_services import DataServices
from backend.storage import LocalStorage

# 配置日志
logger = logging.getLogger(__name__)

# 初始化路由器和数据服务
router = APIRouter(prefix="/api/stock", tags=["stock-data"])
data_service = DataServices(require_api_key=False)  # 仅使用缓存数据
storage = LocalStorage()  # 本地存储服务

# Pydantic 模型
class StockDataRequest(BaseModel):
    symbol: str
    curr_date: str
    look_back_days: int = 30

class MultipleIndicatorsRequest(BaseModel):
    symbol: str
    indicators: List[str]
    curr_date: str
    look_back_days: int = 100

class MarketOverviewRequest(BaseModel):
    symbols: Optional[List[str]] = None
    curr_date: Optional[str] = None

class WatchlistRequest(BaseModel):
    symbol: str

class WatchlistUpdateRequest(BaseModel):
    symbols: List[str]

# API 端点
@router.get("/available-stocks")
async def get_available_stocks(user_id: str = Query("demo_user", description="用户ID")):
    """获取用户关注的股票列表，如果用户没有关注的股票则返回缓存中所有可用的股票"""
    try:
        # 获取用户关注的股票
        watchlist = storage.get_user_watchlist(user_id)
        
        if watchlist:
            # 如果用户有关注的股票，验证这些股票在缓存中是否可用
            all_available_stocks = data_service.get_available_stocks()
            available_watchlist = [stock for stock in watchlist if stock in all_available_stocks]
            
            return {
                "stocks": available_watchlist,
                "count": len(available_watchlist),
                "source": "user_watchlist",
                "user_id": user_id,
                "unavailable_stocks": [stock for stock in watchlist if stock not in all_available_stocks],
                "generated_at": datetime.now().isoformat()
            }
        else:
            # 如果用户没有关注的股票，返回所有可用股票
            stocks = data_service.get_available_stocks()
            return {
                "stocks": stocks,
                "count": len(stocks),
                "source": "all_available",
                "user_id": user_id,
                "generated_at": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"获取可用股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/{symbol}")
async def get_stock_data(
    symbol: str,
    curr_date: str = Query(..., description="当前日期 YYYY-MM-DD"),
    look_back_days: int = Query(30, description="回看天数")
):
    """获取指定窗口期的股票数据"""
    try:
        # 验证日期格式
        if not data_service.validate_date(curr_date):
            raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD 格式")
        
        data = data_service.get_stock_data_window(symbol.upper(), curr_date, look_back_days)
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票 {symbol.upper()} 的数据")
        
        # 转换 DataFrame 为 JSON 格式
        data_dict = data.reset_index().to_dict('records')
        
        return {
            "symbol": symbol.upper(),
            "period": f"{look_back_days} days",
            "data": data_dict,
            "count": len(data_dict),
            "generated_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票数据失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{symbol}")
async def get_stock_summary(
    symbol: str,
    curr_date: str = Query(..., description="当前日期 YYYY-MM-DD"),
    look_back_days: int = Query(30, description="回看天数")
):
    """获取股票数据摘要"""
    try:
        if not data_service.validate_date(curr_date):
            raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD 格式")
        
        summary = data_service.get_stock_summary(symbol.upper(), curr_date, look_back_days)
        
        if "error" in summary:
            # Return the full error information instead of just the error message
            raise HTTPException(status_code=404, detail=summary)
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票摘要失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indicator/{symbol}")
async def get_technical_indicator(
    symbol: str,
    indicator: str = Query(..., description="技术指标名称"),
    curr_date: str = Query(..., description="当前日期 YYYY-MM-DD"),
    look_back_days: int = Query(100, description="回看天数")
):
    """计算单个技术指标"""
    try:
        if not data_service.validate_date(curr_date):
            raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD 格式")
        
        # 检查指标是否支持
        supported_indicators = data_service.get_supported_indicators()
        if indicator not in supported_indicators:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的指标: {indicator}。支持的指标: {list(supported_indicators.keys())}"
            )
        
        result = data_service.calculate_technical_indicator(
            symbol.upper(), indicator, curr_date, look_back_days
        )
        
        if result.empty:
            raise HTTPException(status_code=404, detail=f"无法计算指标 {indicator} for {symbol.upper()}")
        
        # 转换 DataFrame 为 JSON 格式
        data_dict = result.reset_index().to_dict('records')
        
        return {
            "symbol": symbol.upper(),
            "indicator": indicator,
            "description": supported_indicators[indicator],
            "period": f"{look_back_days} days",
            "data": data_dict,
            "count": len(data_dict),
            "generated_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算技术指标失败 {symbol} {indicator}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/indicators/multiple")
async def get_multiple_indicators(request: MultipleIndicatorsRequest):
    """计算多个技术指标"""
    try:
        if not data_service.validate_date(request.curr_date):
            raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD 格式")
        
        # 验证所有指标都是支持的
        supported_indicators = data_service.get_supported_indicators()
        invalid_indicators = [ind for ind in request.indicators if ind not in supported_indicators]
        if invalid_indicators:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的指标: {invalid_indicators}。支持的指标: {list(supported_indicators.keys())}"
            )
        
        results = data_service.get_multiple_indicators(
            request.symbol.upper(),
            request.indicators,
            request.curr_date,
            request.look_back_days
        )
        
        # 转换结果格式
        formatted_results = {}
        for indicator, data in results.items():
            if not data.empty:
                formatted_results[indicator] = {
                    "description": supported_indicators[indicator],
                    "data": data.reset_index().to_dict('records'),
                    "count": len(data)
                }
            else:
                formatted_results[indicator] = {
                    "description": supported_indicators[indicator],
                    "error": "无数据"
                }
        
        return {
            "symbol": request.symbol.upper(),
            "indicators": formatted_results,
            "period": f"{request.look_back_days} days",
            "generated_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算多个技术指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-indicators")
async def get_supported_indicators():
    """获取支持的技术指标列表"""
    try:
        indicators = data_service.get_supported_indicators()
        return {
            "indicators": indicators,
            "count": len(indicators),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取支持的指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/market-overview")
async def get_market_overview(request: MarketOverviewRequest):
    """获取市场概览"""
    try:
        curr_date = request.curr_date or datetime.now().strftime("%Y-%m-%d")
        
        if not data_service.validate_date(curr_date):
            raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD 格式")
        
        overview = data_service.get_market_overview(request.symbols, curr_date)
        
        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])
        
        return overview
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-overview")
async def get_market_overview_simple(
    symbols: Optional[str] = Query(None, description="逗号分隔的股票代码列表"),
    curr_date: Optional[str] = Query(None, description="当前日期 YYYY-MM-DD")
):
    """获取市场概览 (GET 方法)"""
    try:
        symbol_list = symbols.split(',') if symbols else None
        curr_date = curr_date or datetime.now().strftime("%Y-%m-%d")
        
        if not data_service.validate_date(curr_date):
            raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD 格式")
        
        overview = data_service.get_market_overview(symbol_list, curr_date)
        
        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])
        
        return overview
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 关注股票管理API
@router.get("/watchlist")
async def get_watchlist(user_id: str = Query("demo_user", description="用户ID")):
    """获取用户关注的股票列表"""
    try:
        watchlist = storage.get_user_watchlist(user_id)
        all_available_stocks = data_service.get_available_stocks()
        
        # 分离可用和不可用的股票
        available_watchlist = [stock for stock in watchlist if stock in all_available_stocks]
        unavailable_watchlist = [stock for stock in watchlist if stock not in all_available_stocks]
        
        return {
            "user_id": user_id,
            "watchlist": watchlist,
            "available_stocks": available_watchlist,
            "unavailable_stocks": unavailable_watchlist,
            "total_count": len(watchlist),
            "available_count": len(available_watchlist),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取用户关注列表失败 {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/watchlist/add")
async def add_to_watchlist(
    request: WatchlistRequest,
    user_id: str = Query("demo_user", description="用户ID")
):
    """添加股票到用户关注列表"""
    try:
        symbol = request.symbol.upper()
        
        # 检查股票是否在可用列表中
        available_stocks = data_service.get_available_stocks()
        if symbol not in available_stocks:
            raise HTTPException(
                status_code=400, 
                detail=f"股票 {symbol} 不在可用股票列表中"
            )
        
        success = storage.add_to_watchlist(user_id, symbol)
        if success:
            return {
                "message": f"股票 {symbol} 已添加到关注列表",
                "user_id": user_id,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"股票 {symbol} 已在关注列表中"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加股票到关注列表失败 {user_id} {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/watchlist/remove")
async def remove_from_watchlist(
    symbol: str = Query(..., description="股票代码"),
    user_id: str = Query("demo_user", description="用户ID")
):
    """从用户关注列表中移除股票"""
    try:
        symbol = symbol.upper()
        success = storage.remove_from_watchlist(user_id, symbol)
        
        if success:
            return {
                "message": f"股票 {symbol} 已从关注列表中移除",
                "user_id": user_id,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"股票 {symbol} 不在关注列表中"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从关注列表移除股票失败 {user_id} {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/watchlist")
async def update_watchlist(
    request: WatchlistUpdateRequest,
    user_id: str = Query("demo_user", description="用户ID")
):
    """更新用户关注股票列表（完全替换）"""
    try:
        symbols = [symbol.upper() for symbol in request.symbols]
        
        # 验证所有股票都在可用列表中
        available_stocks = data_service.get_available_stocks()
        invalid_symbols = [symbol for symbol in symbols if symbol not in available_stocks]
        
        if invalid_symbols:
            raise HTTPException(
                status_code=400,
                detail=f"以下股票不在可用股票列表中: {', '.join(invalid_symbols)}"
            )
        
        success = storage.update_watchlist(user_id, symbols)
        
        if success:
            return {
                "message": "关注列表已更新",
                "user_id": user_id,
                "watchlist": symbols,
                "count": len(symbols),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="更新关注列表失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新关注列表失败 {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/watchlist/check/{symbol}")
async def check_watchlist_status(
    symbol: str,
    user_id: str = Query("demo_user", description="用户ID")
):
    """检查股票是否在用户关注列表中"""
    try:
        symbol = symbol.upper()
        is_watched = storage.is_symbol_in_watchlist(user_id, symbol)
        
        return {
            "user_id": user_id,
            "symbol": symbol,
            "is_watched": is_watched,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"检查关注状态失败 {user_id} {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 健康检查端点
@router.get("/health")
async def health_check():
    """股票数据服务健康检查"""
    try:
        available_stocks = data_service.get_available_stocks()
        data_source_status = data_service.get_data_source_status()
        return {
            "status": "healthy",
            "available_stocks_count": len(available_stocks),
            "data_source": data_source_status,
            "timestamp": datetime.now().isoformat(),
            "service": "stock-data"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@router.get("/data-source-status")
async def get_data_source_status():
    """获取数据源状态信息"""
    try:
        status = data_service.get_data_source_status()
        return {
            "data_source_status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取数据源状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
