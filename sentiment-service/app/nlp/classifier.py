"""
Sentiment classification using Hugging Face transformers.

Uses fine-tuned DistilBERT model for efficient sentiment classification.
Supports VADER for financial sentiment analysis.
"""
import logging
from typing import List, Tuple, Dict, Optional
from enum import Enum
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

logger = logging.getLogger(__name__)


class SentimentLabel(str, Enum):
    """Sentiment classification labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SentimentScore:
    """Structured sentiment score result."""
    
    def __init__(
        self,
        label: SentimentLabel,
        score: float,
        positive_pct: float,
        negative_pct: float,
        neutral_pct: float
    ):
        """Initialize sentiment score.
        
        Args:
            label: Primary sentiment label
            score: Normalized score from -1 (very negative) to +1 (very positive)
            positive_pct: Percentage positive (0-100)
            negative_pct: Percentage negative (0-100)
            neutral_pct: Percentage neutral (0-100)
        """
        self.label = label
        self.score = score  # -1 to +1
        self.positive_pct = positive_pct
        self.negative_pct = negative_pct
        self.neutral_pct = neutral_pct
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "label": self.label.value,
            "score": round(self.score, 4),
            "positive_pct": round(self.positive_pct, 2),
            "negative_pct": round(self.negative_pct, 2),
            "neutral_pct": round(self.neutral_pct, 2)
        }


class SentimentClassifier:
    """Sentiment classifier using fine-tuned DistilBERT."""
    
    def __init__(
        self,
        model_name: str = "distilbert-base-uncased-finetuned-sst-2-english",
        device: str = "cpu"
    ):
        """Initialize sentiment classifier.
        
        Args:
            model_name: Hugging Face model identifier
            device: Compute device ('cuda' or 'cpu')
        """
        self.model_name = model_name
        self.device = device
        self.classifier = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the model and tokenizer."""
        try:
            logger.info(f"Loading sentiment model: {self.model_name}")
            
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                device=0 if self.device == "cuda" and torch.cuda.is_available() else -1
            )
            
            logger.info(f"Sentiment model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Failed to initialize sentiment classifier: {e}")
            raise
    
    def classify(self, text: str, return_probabilities: bool = False) -> SentimentScore:
        """Classify sentiment of a text.
        
        Args:
            text: Text to analyze
            return_probabilities: Whether to include raw model probabilities
        
        Returns:
            SentimentScore object
        """
        if not text or not text.strip():
            # Neutral for empty text
            return SentimentScore(
                label=SentimentLabel.NEUTRAL,
                score=0.0,
                positive_pct=0.0,
                negative_pct=0.0,
                neutral_pct=100.0
            )
        
        try:
            # Truncate text to model max length (512 tokens)
            text = text[:512]
            
            result = self.classifier(text, top_k=None)
            
            # Process results - distilbert returns [{'label': 'POSITIVE/NEGATIVE', 'score': 0.95}]
            sentiments = {}
            for item in result:
                label = item["label"].lower()
                score = item["score"]
                sentiments[label] = score
            
            # Calculate percentages
            positive_pct = sentiments.get("positive", 0.0) * 100
            negative_pct = sentiments.get("negative", 0.0) * 100
            neutral_pct = sentiments.get("neutral", 0.0) * 100
            
            # Determine primary label
            if positive_pct > negative_pct and positive_pct > neutral_pct:
                label = SentimentLabel.POSITIVE
            elif negative_pct > positive_pct and negative_pct > neutral_pct:
                label = SentimentLabel.NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL
            
            # Convert to -1 to +1 scale
            score = (positive_pct - negative_pct) / 100.0
            
            return SentimentScore(
                label=label,
                score=score,
                positive_pct=positive_pct,
                negative_pct=negative_pct,
                neutral_pct=neutral_pct
            )
        
        except Exception as e:
            logger.error(f"Error classifying sentiment: {e}")
            # Return neutral on error
            return SentimentScore(
                label=SentimentLabel.NEUTRAL,
                score=0.0,
                positive_pct=0.0,
                negative_pct=0.0,
                neutral_pct=100.0
            )
    
    def classify_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[SentimentScore]:
        """Classify sentiment for multiple texts efficiently.
        
        Args:
            texts: List of texts to analyze
            batch_size: Batch size for processing
        
        Returns:
            List of SentimentScore objects
        """
        results = []
        
        # Process in batches for efficiency
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = self.classifier(batch, top_k=None)
            
            for text, sentiment_results in zip(batch, batch_results):
                sentiments = {}
                for item in sentiment_results:
                    label = item["label"].lower()
                    score = item["score"]
                    sentiments[label] = score
                
                positive_pct = sentiments.get("positive", 0.0) * 100
                negative_pct = sentiments.get("negative", 0.0) * 100
                neutral_pct = sentiments.get("neutral", 0.0) * 100
                
                if positive_pct > negative_pct and positive_pct > neutral_pct:
                    label = SentimentLabel.POSITIVE
                elif negative_pct > positive_pct and negative_pct > neutral_pct:
                    label = SentimentLabel.NEGATIVE
                else:
                    label = SentimentLabel.NEUTRAL
                
                score_value = (positive_pct - negative_pct) / 100.0
                
                results.append(SentimentScore(
                    label=label,
                    score=score_value,
                    positive_pct=positive_pct,
                    negative_pct=negative_pct,
                    neutral_pct=neutral_pct
                ))
        
        return results


class FinancialSentimentAnalyzer:
    """Specialized sentiment analyzer for financial/crypto text using VADER."""
    
    def __init__(self):
        """Initialize VADER sentiment analyzer."""
        try:
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            import nltk
            
            # Download VADER lexicon if needed
            try:
                nltk.data.find('sentiment/vader_lexicon')
            except LookupError:
                nltk.download('vader_lexicon')
            
            self.vader = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized")
        except ImportError:
            logger.warning("NLTK not available, financial sentiment analysis disabled")
            self.vader = None
    
    def analyze(self, text: str) -> SentimentScore:
        """Analyze financial sentiment using VADER.
        
        Args:
            text: Text to analyze
        
        Returns:
            SentimentScore object
        """
        if not self.vader:
            logger.warning("VADER not initialized, returning neutral")
            return SentimentScore(
                label=SentimentLabel.NEUTRAL,
                score=0.0,
                positive_pct=0.0,
                negative_pct=0.0,
                neutral_pct=100.0
            )
        
        try:
            scores = self.vader.polarity_scores(text)
            
            # Extract compound score (normalized -1 to +1)
            compound = scores["compound"]
            positive = scores["pos"] * 100
            negative = scores["neg"] * 100
            neutral = scores["neu"] * 100
            
            # Determine label
            if compound >= 0.05:
                label = SentimentLabel.POSITIVE
            elif compound <= -0.05:
                label = SentimentLabel.NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL
            
            return SentimentScore(
                label=label,
                score=compound,
                positive_pct=positive,
                negative_pct=negative,
                neutral_pct=neutral
            )
        
        except Exception as e:
            logger.error(f"Error in VADER sentiment analysis: {e}")
            return SentimentScore(
                label=SentimentLabel.NEUTRAL,
                score=0.0,
                positive_pct=0.0,
                negative_pct=0.0,
                neutral_pct=100.0
            )


class EnsembleSentimentAnalyzer:
    """Ensemble sentiment analyzer combining multiple models."""
    
    def __init__(self, use_vader: bool = True):
        """Initialize ensemble analyzer.
        
        Args:
            use_vader: Whether to include VADER in ensemble
        """
        self.distilbert = SentimentClassifier()
        self.vader = FinancialSentimentAnalyzer() if use_vader else None
    
    def analyze(self, text: str) -> SentimentScore:
        """Analyze sentiment using ensemble approach.
        
        Args:
            text: Text to analyze
        
        Returns:
            Averaged SentimentScore from all models
        """
        results = []
        
        # Get DistilBERT prediction
        results.append(self.distilbert.classify(text))
        
        # Get VADER prediction if available
        if self.vader:
            results.append(self.vader.analyze(text))
        
        # Average results
        avg_score = sum(r.score for r in results) / len(results)
        avg_positive = sum(r.positive_pct for r in results) / len(results)
        avg_negative = sum(r.negative_pct for r in results) / len(results)
        avg_neutral = sum(r.neutral_pct for r in results) / len(results)
        
        # Determine label from average scores
        if avg_positive > avg_negative and avg_positive > avg_neutral:
            label = SentimentLabel.POSITIVE
        elif avg_negative > avg_positive and avg_negative > avg_neutral:
            label = SentimentLabel.NEGATIVE
        else:
            label = SentimentLabel.NEUTRAL
        
        return SentimentScore(
            label=label,
            score=avg_score,
            positive_pct=avg_positive,
            negative_pct=avg_negative,
            neutral_pct=avg_neutral
        )
