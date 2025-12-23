"""
Sentiment Analyzer Module
Analyzes financial news sentiment using FinBERT model.
"""

import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List


class SentimentEngine:
    """Analyzes sentiment of financial headlines using FinBERT."""
    
    def __init__(self):
        """Initialize and load the FinBERT model."""
        self.model_name = "ProsusAI/finbert"
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the FinBERT model and tokenizer from Hugging Face."""
        try:
            print("Loading FinBERT model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.eval()
            print("FinBERT model loaded successfully.")
        except Exception as e:
            print(f"Error loading FinBERT model: {e}")
            raise
    
    def analyze(self, headlines: List[str]) -> pd.DataFrame:
        """
        Analyze sentiment of headlines.
        
        Args:
            headlines: List of headline strings
            
        Returns:
            DataFrame with columns: ['headline', 'sentiment_score', 'sentiment_label']
            sentiment_score: Float between -1 (Negative) and 1 (Positive)
            sentiment_label: String ('Positive', 'Negative', or 'Neutral')
        """
        if not headlines:
            return pd.DataFrame(columns=['headline', 'sentiment_score', 'sentiment_label'])
        
        results = []
        
        for headline in headlines:
            try:
                sentiment_score, sentiment_label = self._analyze_single(headline)
                results.append({
                    'headline': headline,
                    'sentiment_score': sentiment_score,
                    'sentiment_label': sentiment_label
                })
            except Exception as e:
                print(f"Error analyzing headline '{headline[:50]}...': {e}")
                results.append({
                    'headline': headline,
                    'sentiment_score': 0.0,
                    'sentiment_label': 'Neutral'
                })
        
        return pd.DataFrame(results)
    
    def _analyze_single(self, headline: str) -> tuple:
        """
        Analyze sentiment of a single headline.
        
        Args:
            headline: Headline string
            
        Returns:
            Tuple of (sentiment_score, sentiment_label)
            sentiment_score: Float between -1 (Negative) and 1 (Positive)
        """
        inputs = self.tokenizer(headline, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        positive_prob = predictions[0][0].item()
        negative_prob = predictions[0][1].item()
        neutral_prob = predictions[0][2].item()
        
        if positive_prob > negative_prob and positive_prob > neutral_prob:
            label = 'Positive'
            sentiment_score = positive_prob
        elif negative_prob > positive_prob and negative_prob > neutral_prob:
            label = 'Negative'
            sentiment_score = -negative_prob
        else:
            label = 'Neutral'
            sentiment_score = 0.0
        
        return sentiment_score, label

