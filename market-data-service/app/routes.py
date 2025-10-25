"""
Market Data Service routes.
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from datetime import datetime
from typing import List, Set
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["market"])

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "market-data-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """WebSocket endpoint for real-time price updates."""
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        while True:
            # Receive subscription message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "subscribe":
                coins = message.get("coins", [])
                logger.info(f"Client subscribed to coins: {coins}")
                
                # Send confirmation
                await websocket.send_json({
                    "type": "subscribed",
                    "coins": coins
                })
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("Client disconnected from price stream")
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        active_connections.discard(websocket)


async def broadcast_price_update(price_data: dict):
    """Broadcast price update to all connected clients."""
    disconnected = set()
    
    for connection in active_connections:
        try:
            await connection.send_json({
                "type": "price_update",
                "data": price_data
            })
        except Exception:
            disconnected.add(connection)
    
    # Clean up disconnected clients
    for connection in disconnected:
        active_connections.discard(connection)
