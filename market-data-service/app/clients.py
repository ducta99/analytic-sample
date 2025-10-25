"""
Market Data Service - Real-time price streaming from exchanges.
"""
import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import websockets
from kafka import KafkaProducer
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PriceUpdate(BaseModel):
    """Price update model."""
    coin_id: str
    price: float
    volume: Optional[float] = None
    timestamp: datetime


class BinanceWebSocketClient:
    """Binance WebSocket client for real-time price updates."""
    
    def __init__(self, coins: List[str]):
        self.coins = coins
        self.ws_url = "wss://stream.binance.com:9443/ws"
        self.reconnect_delay = 1
        self.max_reconnect_delay = 30
        self.running = False
    
    def _get_stream_name(self, coin: str) -> str:
        """Get Binance stream name for a coin."""
        return f"{coin.lower()}usdt@ticker"
    
    async def connect(self):
        """Connect to Binance WebSocket."""
        self.running = True
        streams = "/".join([self._get_stream_name(coin) for coin in self.coins])
        url = f"{self.ws_url}/stream?streams={streams}"
        
        reconnect_delay = self.reconnect_delay
        
        while self.running:
            try:
                async with websockets.connect(url) as websocket:
                    logger.info(f"Connected to Binance WebSocket for {len(self.coins)} coins")
                    reconnect_delay = self.reconnect_delay
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            yield self._parse_message(data)
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse Binance message")
                        except Exception as e:
                            logger.error(f"Error processing message: {str(e)}")
            
            except websockets.exceptions.WebSocketException as e:
                logger.error(f"WebSocket error: {str(e)}")
                if self.running:
                    logger.info(f"Reconnecting in {reconnect_delay}s...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, self.max_reconnect_delay)
            
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                if self.running:
                    await asyncio.sleep(reconnect_delay)
    
    def _parse_message(self, data: Dict) -> PriceUpdate:
        """Parse Binance ticker message."""
        ticker = data.get("data", {})
        symbol = ticker.get("s", "").replace("USDT", "").lower()
        
        return PriceUpdate(
            coin_id=symbol,
            price=float(ticker.get("c", 0)),
            volume=float(ticker.get("v", 0)),
            timestamp=datetime.utcnow()
        )
    
    async def close(self):
        """Close the connection."""
        self.running = False


class CoinbaseWebSocketClient:
    """Coinbase WebSocket client for real-time price updates."""
    
    def __init__(self, coins: List[str]):
        self.coins = coins
        self.ws_url = "wss://ws-feed.exchange.coinbase.com"
        self.reconnect_delay = 1
        self.max_reconnect_delay = 30
        self.running = False
    
    async def connect(self):
        """Connect to Coinbase WebSocket."""
        self.running = True
        
        # Subscribe to product IDs
        product_ids = [f"{coin.upper()}-USD" for coin in self.coins]
        subscribe_message = {
            "type": "subscribe",
            "product_ids": product_ids,
            "channels": ["ticker"]
        }
        
        reconnect_delay = self.reconnect_delay
        
        while self.running:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    logger.info(f"Connected to Coinbase WebSocket for {len(self.coins)} coins")
                    await websocket.send(json.dumps(subscribe_message))
                    reconnect_delay = self.reconnect_delay
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            if data.get("type") == "ticker":
                                yield self._parse_message(data)
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse Coinbase message")
                        except Exception as e:
                            logger.error(f"Error processing message: {str(e)}")
            
            except websockets.exceptions.WebSocketException as e:
                logger.error(f"WebSocket error: {str(e)}")
                if self.running:
                    logger.info(f"Reconnecting in {reconnect_delay}s...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, self.max_reconnect_delay)
            
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                if self.running:
                    await asyncio.sleep(reconnect_delay)
    
    def _parse_message(self, data: Dict) -> PriceUpdate:
        """Parse Coinbase ticker message."""
        product_id = data.get("product_id", "").split("-")[0].lower()
        
        return PriceUpdate(
            coin_id=product_id,
            price=float(data.get("price", 0)),
            volume=float(data.get("last_size", 0)) if data.get("last_size") else None,
            timestamp=datetime.utcnow()
        )
    
    async def close(self):
        """Close the connection."""
        self.running = False


class KafkaProducerClient:
    """Kafka producer for publishing price updates."""
    
    def __init__(self, brokers: str):
        self.brokers = brokers.split(",")
        self.producer = None
    
    def connect(self):
        """Connect to Kafka."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.brokers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retries=3
            )
            logger.info(f"Connected to Kafka brokers: {self.brokers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            raise
    
    async def publish(self, topic: str, message: PriceUpdate):
        """Publish message to Kafka topic."""
        if not self.producer:
            raise RuntimeError("Kafka producer not connected")
        
        try:
            self.producer.send(
                topic,
                value=message.model_dump(mode='json')
            )
        except Exception as e:
            logger.error(f"Failed to publish message to Kafka: {str(e)}")
    
    def close(self):
        """Close Kafka connection."""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")
