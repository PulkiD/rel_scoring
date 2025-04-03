# src/scoring/sentiment.py
# Calculates the detailed Sentiment Scores for the relationship.

from typing import List, Dict, Any
from ..data_models.models import MentionItem, SentimentScoresOutput # Import Pydantic models
from ..utils.logger import get_logger
from ..exceptions import CalculationError, ConfigurationError

logger = get_logger()

def calculate(mentions: List[MentionItem], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates detailed sentiment scores based on mentions and source weights.

    Implements the "NetScoreDetailed" aggregation method, providing scores
    for positive, negative, and neutral mentions, a net score, and a
    dominant sentiment category.

    Args:
        mentions: List of MentionItem objects for the relationship.
        config: The loaded configuration dictionary.

    Returns:
        A dictionary containing the calculated sentiment scores, conforming
        to the SentimentScoresOutput Pydantic model structure.

    Raises:
        CalculationError: If calculation fails.
        ConfigurationError: If config is invalid or missing required keys.
    """
    logger.info("Calculating Sentiment scores...")
    if not mentions:
        logger.warning("No mentions provided for sentiment calculation. Returning zero scores.")
        # Return default structure expected by SentimentScoresOutput
        return SentimentScoresOutput(
            positive_score=0.0,
            negative_score=0.0,
            neutral_score=0.0,
            net_score=0.0,
            dominant_sentiment="Neutral" # Or perhaps "Mixed"? Defaulting to Neutral.
        ).model_dump() # Return as dict

    try:
        # --- Get relevant config sections ---
        weights = config.get('source_weights')
        sentiment_config = config.get('sentiment', {})
        aggregation_method = sentiment_config.get('aggregation_method', 'NetScoreDetailed') # Default if not specified

        if not weights:
            raise ConfigurationError("Missing 'source_weights' in configuration.")
        # Ensure the configured method is the one we are implementing here
        if aggregation_method != "NetScoreDetailed":
             logger.warning(f"Sentiment aggregation method '{aggregation_method}' configured, but only 'NetScoreDetailed' is implemented in this function. Proceeding with NetScoreDetailed.")
             # Or raise ConfigurationError? For now, proceed with warning.

        # --- Calculate weighted sums for each sentiment category ---
        positive_score = 0.0
        negative_score = 0.0
        neutral_score = 0.0

        for mention in mentions:
            try:
                weight = weights[mention.source_type]
            except KeyError:
                logger.warning(f"Source type '{mention.source_type}' not found in configured weights for sentiment calculation. Mention skipped.")
                continue # Skip mentions with unconfigured source types

            if mention.sentiment == "Positive":
                positive_score += weight
            elif mention.sentiment == "Negative":
                negative_score += weight
            elif mention.sentiment == "Neutral":
                neutral_score += weight
            # else: # Should not happen if input validation is working
            #     logger.warning(f"Unknown sentiment '{mention.sentiment}' found for mention '{mention.mention_id}'. Skipping.")

        # --- Calculate Net Score ---
        net_score = positive_score - negative_score

        # --- Determine Dominant Sentiment ---
        # Simple logic: Compare positive and negative scores. If close, consider neutral count or declare Mixed.
        # More sophisticated logic could use thresholds from config if defined.
        dominant_sentiment = "Neutral" # Default
        if positive_score > negative_score and positive_score > neutral_score:
             dominant_sentiment = "Positive"
        elif negative_score > positive_score and negative_score > neutral_score:
             dominant_sentiment = "Negative"
        elif neutral_score >= positive_score and neutral_score >= negative_score:
             # If neutral is highest or equal to highest, call it Neutral (unless pos/neg are both significant?)
             dominant_sentiment = "Neutral"

        # Check for 'Mixed' cases - e.g., if positive and negative are both significant and outweigh neutral
        # This threshold logic can be refined based on requirements.
        total_score = positive_score + negative_score + neutral_score
        if total_score > 0: # Avoid division by zero
             # Example threshold: if both positive and negative contribute > 25% of non-neutral score
             non_neutral_score = positive_score + negative_score
             if non_neutral_score > 0:
                  pos_ratio = positive_score / non_neutral_score
                  neg_ratio = negative_score / non_neutral_score
                  # If neither strongly dominates the other (e.g., both between 30% and 70%)
                  if 0.3 < pos_ratio < 0.7:
                       # And if the combined non-neutral score is significant compared to neutral
                       if non_neutral_score > neutral_score: # Example condition
                            dominant_sentiment = "Mixed"

        # If all scores are zero (e.g., only mentions with unknown source types)
        if positive_score == 0 and negative_score == 0 and neutral_score == 0:
             dominant_sentiment = "Neutral" # Or "Mixed"? Consistent default needed.


        # --- Prepare Output ---
        result = SentimentScoresOutput(
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score,
            net_score=net_score,
            dominant_sentiment=dominant_sentiment
        )

        logger.info(f"Sentiment score calculation complete. Dominant: {dominant_sentiment}, Net: {net_score:.2f}")
        # Return as dictionary to match expected output format of main scorer
        return result.model_dump()

    except ConfigurationError as e:
        logger.error(f"Configuration error during sentiment calculation: {e}", exc_info=True)
        raise # Re-raise specific config errors
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"An unexpected error occurred during sentiment calculation: {e}", exc_info=True)
        raise CalculationError(f"Unexpected error in sentiment calculation: {e}")

