"""
Tests for sentiment classifier.
"""
import pytest
from sentiment_service.app.nlp.classifier import (
    SentimentClassifier,
    SentimentLabel,
    FinancialSentimentAnalyzer,
    EnsembleSentimentAnalyzer,
    SentimentScore
)


class TestSentimentClassifier:
    """Tests for DistilBERT-based sentiment classifier."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        return SentimentClassifier(device="cpu")
    
    def test_classifier_initialization(self, classifier):
        """Test classifier initializes correctly."""
        assert classifier is not None
        assert classifier.classifier is not None
        assert classifier.device == "cpu"
    
    def test_classify_positive_text(self, classifier):
        """Test classification of positive text."""
        text = "Bitcoin is amazing! The project team is incredible and the community is fantastic!"
        result = classifier.classify(text)
        
        assert isinstance(result, SentimentScore)
        assert result.label == SentimentLabel.POSITIVE
        assert result.score > 0
        assert result.positive_pct > result.negative_pct
    
    def test_classify_negative_text(self, classifier):
        """Test classification of negative text."""
        text = "This cryptocurrency is a complete scam. The developers are dishonest and the project is terrible."
        result = classifier.classify(text)
        
        assert isinstance(result, SentimentScore)
        assert result.label == SentimentLabel.NEGATIVE
        assert result.score < 0
        assert result.negative_pct > result.positive_pct
    
    def test_classify_neutral_text(self, classifier):
        """Test classification of neutral text."""
        text = "The blockchain was created in 2009. It uses proof of work consensus mechanism."
        result = classifier.classify(text)
        
        assert isinstance(result, SentimentScore)
        assert result.label == SentimentLabel.NEUTRAL
    
    def test_classify_empty_text(self, classifier):
        """Test classification of empty text."""
        result = classifier.classify("")
        
        assert result.label == SentimentLabel.NEUTRAL
        assert result.score == 0.0
        assert result.neutral_pct == 100.0
    
    def test_classify_very_long_text(self, classifier):
        """Test classification truncates very long text."""
        long_text = "positive " * 1000  # Create very long text
        result = classifier.classify(long_text)
        
        # Should not raise error and should truncate
        assert isinstance(result, SentimentScore)
    
    def test_sentiment_score_to_dict(self):
        """Test SentimentScore conversion to dict."""
        score = SentimentScore(
            label=SentimentLabel.POSITIVE,
            score=0.85,
            positive_pct=85.0,
            negative_pct=10.0,
            neutral_pct=5.0
        )
        
        result = score.to_dict()
        assert result["label"] == "positive"
        assert result["score"] == 0.85
        assert result["positive_pct"] == 85.0
    
    @pytest.mark.asyncio
    async def test_classify_batch(self, classifier):
        """Test batch classification."""
        texts = [
            "Bitcoin is great!",
            "Ethereum is horrible!",
            "Cardano is okay."
        ]
        
        results = classifier.classify_batch(texts)
        
        assert len(results) == 3
        assert all(isinstance(r, SentimentScore) for r in results)
        assert results[0].label == SentimentLabel.POSITIVE
        assert results[1].label == SentimentLabel.NEGATIVE
        assert results[2].label == SentimentLabel.NEUTRAL


class TestFinancialSentimentAnalyzer:
    """Tests for VADER financial sentiment analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return FinancialSentimentAnalyzer()
    
    def test_vader_initialization(self, analyzer):
        """Test VADER initializes correctly."""
        assert analyzer is not None
    
    def test_vader_positive_sentiment(self, analyzer):
        """Test VADER detects positive sentiment."""
        text = "The bull market is incredible! Prices are skyrocketing!"
        result = analyzer.analyze(text)
        
        assert result.label == SentimentLabel.POSITIVE
        assert result.score > 0
    
    def test_vader_negative_sentiment(self, analyzer):
        """Test VADER detects negative sentiment."""
        text = "The market crashed! Losses are devastating!"
        result = analyzer.analyze(text)
        
        assert result.label == SentimentLabel.NEGATIVE
        assert result.score < 0
    
    def test_vader_neutral_sentiment(self, analyzer):
        """Test VADER detects neutral sentiment."""
        text = "Trading volume increased by 10 percent."
        result = analyzer.analyze(text)
        
        assert result.label == SentimentLabel.NEUTRAL


class TestEnsembleSentimentAnalyzer:
    """Tests for ensemble sentiment analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create ensemble analyzer."""
        return EnsembleSentimentAnalyzer(use_vader=True)
    
    def test_ensemble_initialization(self, analyzer):
        """Test ensemble initializes correctly."""
        assert analyzer.distilbert is not None
        assert analyzer.vader is not None
    
    def test_ensemble_analysis(self, analyzer):
        """Test ensemble analysis combines multiple models."""
        text = "Bitcoin is absolutely wonderful and fantastic!"
        result = analyzer.analyze(text)
        
        assert isinstance(result, SentimentScore)
        assert result.label == SentimentLabel.POSITIVE
        assert result.score > 0
    
    def test_ensemble_conservative_neutral(self, analyzer):
        """Test ensemble can be more conservative with neutrality."""
        text = "The price went up."
        result = analyzer.analyze(text)
        
        # Mixed models may be more neutral
        assert isinstance(result, SentimentScore)
        assert -0.5 < result.score < 0.5


class TestSentimentScoreIntegration:
    """Integration tests for sentiment scoring."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier."""
        return SentimentClassifier(device="cpu")
    
    def test_score_range(self, classifier):
        """Test sentiment scores are in valid range."""
        texts = [
            "Excellent! Amazing! Wonderful!",
            "Terrible! Horrible! Awful!",
            "The price is stable.",
        ]
        
        for text in texts:
            result = classifier.classify(text)
            assert -1 <= result.score <= 1
            assert 0 <= result.positive_pct <= 100
            assert 0 <= result.negative_pct <= 100
            assert 0 <= result.neutral_pct <= 100
    
    def test_percentages_sum_to_100(self, classifier):
        """Test sentiment percentages sum to approximately 100."""
        texts = [
            "Great news!",
            "Bad news!",
            "News.",
        ]
        
        for text in texts:
            result = classifier.classify(text)
            total = result.positive_pct + result.negative_pct + result.neutral_pct
            assert 95 <= total <= 105  # Allow small rounding differences
