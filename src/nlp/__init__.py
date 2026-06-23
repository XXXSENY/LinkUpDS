"""
Équipe 3 - NLP & Système de Recommandation
Modules d'analyse de texte et de traitement du langage naturel.
"""

from __future__ import annotations

from src.nlp.sentiment_analysis import analyze_sentiment, batch_analyze_sentiment
from src.nlp.topic_modeling import extract_topics, get_topic_distribution

__all__ = [
    "analyze_sentiment",
    "batch_analyze_sentiment",
    "extract_topics",
    "get_topic_distribution",
]
