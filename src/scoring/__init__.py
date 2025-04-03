from . import evidence
from . import sentiment
from . import trend

from .evidence import calculate as evidence_calculate
from .sentiment import calculate as sentiment_calculate
from .trend import calculate as trend_calculate

__all__ = ['evidence_calculate', 'sentiment_calculate', 'trend_calculate']
