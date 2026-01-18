"""
opinion_classifier.py

This module implements the OpinionClassifier class, responsible for:
1. Analyzing the sentiment of news articles using VADER.
2. Classifying stance as IN_FAVOR, AGAINST, or NEUTRAL based on conservative thresholds.
3. Augmenting article objects with 'sentiment_score' and 'stance'.

NOTE: valid Python code returned.
"""

from typing import List, Dict, Any

# Try to import vaderSentiment, handle if missing for hackathon safety
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    print("WARNING: vaderSentiment not installed. Sentiment analysis will be mocked/limited.")
    SentimentIntensityAnalyzer = None

class OpinionClassifier:
    """
    Classifies news articles into stances based on sentiment analysis.
    Uses VADER (Valence Aware Dictionary and sEntiment Reasoner).
    """

    def __init__(self):
        """
        Initialize the classifier.
        """
        if SentimentIntensityAnalyzer:
            self.analyzer = SentimentIntensityAnalyzer()
        else:
            self.analyzer = None

    def classify_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of articles and add sentiment metadata.
        
        Args:
            articles (List[Dict]): List of article dictionaries.
            
        Returns:
            List[Dict]: The same list, but with 'sentiment_score' and 'stance' keys.
        """
        for article in articles:
            # FORCE NEUTRAL STANCE FOR CENTER SOURCES
            # This ensures they appear in the "Neutral Coverage" column, 
            # regardless of the specific sentiment of the headline.
            if article.get('political_bucket') == 'center':
                article['sentiment_score'] = 0.0
                article['stance'] = 'NEUTRAL'
                continue

            # Analyze title and content combined for better context, 
            # but weigh title heavily if needed. For now, simple concatenation.
            text_to_analyze = f"{article.get('title', '')} {article.get('content', '')}"
            
            # Fallback if text is empty
            if not text_to_analyze.strip():
                score = 0.0
            else:
                score = self._analyze_sentiment(text_to_analyze)
            
            stance = self._determine_stance(score)
            
            article['sentiment_score'] = score
            article['stance'] = stance
            
        return articles

    def _analyze_sentiment(self, text: str) -> float:
        """
        Get the compound sentiment score for a given text.
        
        Args:
            text (str): The text to analyze.
            
        Returns:
            float: Compound score between -1.0 (most negative) and 1.0 (most positive).
        """
        if self.analyzer:
            scores = self.analyzer.polarity_scores(text)
            return scores['compound']
            
        # --- Fallback Logic for when VADER is missing (Hackathon Mode) ---
        text_lower = text.lower()
        score = 0.0
        
        # Simple weighted keywords for demo purposes
        # Ideally, we'd want 'support', 'good' -> positive
        # 'against', 'bad', 'crisis' -> negative
        
        positive_words = [
            "excellent", "good", "great", "support", "liberty", "freedom", 
            "save", "peace", "reforms", "modernization", "efficient", 
            "necessary", "revival", "essential", "working"
        ]
        
        negative_words = [
            "terrible", "bad", "worst", "hate", "fail", "crisis", "destroy", 
            "culprit", "blocked", "abuses", "cheats", "terror", "crushed", 
            "dictatorship", "threatening", "harm", "hurt", "kill"
        ]
        
        for word in positive_words:
            if word in text_lower:
                score += 0.3
                
        for word in negative_words:
            if word in text_lower:
                score -= 0.3
                
        # Clamp between -1.0 and 1.0
        return max(-1.0, min(1.0, score))

    def _determine_stance(self, score: float) -> str:
        """
        Map a sentiment score to a stance using conservative thresholds.
        
        Thresholds:
        - Score >= 0.15: IN_FAVOR
        - Score <= -0.15: AGAINST
        - Otherwise: NEUTRAL
        
        Args:
            score (float): The compound sentiment score.
            
        Returns:
            str: "IN_FAVOR", "AGAINST", or "NEUTRAL"
        """
        if score >= 0.15:
            return "IN_FAVOR"
        elif score <= -0.15:
            return "AGAINST"
        else:
            return "NEUTRAL"
