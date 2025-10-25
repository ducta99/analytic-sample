"""
Kafka producer for publishing sentiment scores.
"""
import json
import logging
from typing import Optional, List
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class SentimentProducer:
    """Kafka producer for sentiment scores."""
    
    TOPIC = "sentiment_updates"
    
    def __init__(
        self,
        bootstrap_servers: List[str],
        client_id: str = "sentiment-producer"
    ):
        """Initialize sentiment producer.
        
        Args:
            bootstrap_servers: List of Kafka broker addresses
            client_id: Producer client ID
        """
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.producer: Optional[KafkaProducer] = None
        self._connect()
    
    def _connect(self):
        """Connect to Kafka."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=5,
                compression_type='snappy'  # Compress messages
            )
            logger.info(f"Connected to Kafka: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def publish_sentiment(
        self,
        coin_id: str,
        sentiment_score: float,
        positive_pct: float,
        negative_pct: float,
        neutral_pct: float,
        label: str,
        source: str = "news",
        article_count: int = 0
    ) -> bool:
        """Publish sentiment score to Kafka.
        
        Args:
            coin_id: Cryptocurrency ID
            sentiment_score: Score from -1 to +1
            positive_pct: Positive percentage
            negative_pct: Negative percentage
            neutral_pct: Neutral percentage
            label: Sentiment label (positive, negative, neutral)
            source: Data source (news, twitter, etc)
            article_count: Number of articles analyzed
        
        Returns:
            True if successful, False otherwise
        """
        if not self.producer:
            logger.error("Producer not connected")
            return False
        
        try:
            message = {
                "coin_id": coin_id,
                "sentiment_score": sentiment_score,
                "positive_pct": positive_pct,
                "negative_pct": negative_pct,
                "neutral_pct": neutral_pct,
                "label": label,
                "source": source,
                "article_count": article_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Use coin_id as partition key for ordering
            future = self.producer.send(
                self.TOPIC,
                value=message,
                key=coin_id.encode("utf-8")
            )
            
            # Wait for send confirmation with timeout
            record_metadata = future.get(timeout=5)
            
            logger.debug(
                f"Sentiment published - Coin: {coin_id}, "
                f"Score: {sentiment_score}, Topic: {record_metadata.topic}, "
                f"Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}"
            )
            
            return True
        
        except KafkaError as e:
            logger.error(f"Kafka error publishing sentiment: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing sentiment: {e}")
            return False
    
    def publish_batch_sentiments(
        self,
        sentiments: List[dict]
    ) -> int:
        """Publish multiple sentiment scores.
        
        Args:
            sentiments: List of sentiment dicts with keys:
                - coin_id, sentiment_score, positive_pct, negative_pct,
                  neutral_pct, label, source
        
        Returns:
            Number of successfully published messages
        """
        if not self.producer:
            logger.error("Producer not connected")
            return 0
        
        success_count = 0
        futures = []
        
        try:
            for sentiment in sentiments:
                message = {
                    "coin_id": sentiment["coin_id"],
                    "sentiment_score": sentiment["sentiment_score"],
                    "positive_pct": sentiment["positive_pct"],
                    "negative_pct": sentiment["negative_pct"],
                    "neutral_pct": sentiment["neutral_pct"],
                    "label": sentiment["label"],
                    "source": sentiment.get("source", "news"),
                    "article_count": sentiment.get("article_count", 0),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                future = self.producer.send(
                    self.TOPIC,
                    value=message,
                    key=sentiment["coin_id"].encode("utf-8")
                )
                futures.append(future)
            
            # Wait for all sends with timeout
            for future in futures:
                try:
                    future.get(timeout=5)
                    success_count += 1
                except KafkaError as e:
                    logger.error(f"Failed to send sentiment: {e}")
            
            logger.info(f"Published {success_count}/{len(sentiments)} sentiments")
            return success_count
        
        except Exception as e:
            logger.error(f"Error in batch publish: {e}")
            return success_count
    
    def close(self):
        """Close Kafka connection."""
        if self.producer:
            try:
                self.producer.flush(timeout_ms=5000)
                self.producer.close()
                logger.info("Sentiment producer closed")
            except Exception as e:
                logger.error(f"Error closing producer: {e}")
