# src/scoring/trend.py
# Calculates the Trend Score for the relationship.

import math
import datetime
from typing import List, Dict, Any
from ..data_models.models import MentionItem # Import Pydantic model
from ..utils.logger import get_logger
from ..exceptions import CalculationError, ConfigurationError

logger = get_logger()

def _calculate_recency_weighted_score(mentions: List[MentionItem], weights: Dict[str, float], decay_rate: float) -> float:
    """
    Calculates trend score based on recency, weighting recent mentions more heavily
    using exponential decay.
    """
    logger.debug(f"Calculating trend score using RecencyWeighted method with decay rate: {decay_rate}")
    trend_score = 0.0
    current_year = datetime.datetime.now().year

    if decay_rate < 0:
        logger.warning("Decay rate is negative, which is unusual. Ensure this is intended.")

    for mention in mentions:
        try:
            weight = weights[mention.source_type]
        except KeyError:
            logger.warning(f"Source type '{mention.source_type}' not found in configured weights for trend calculation. Mention skipped.")
            continue

        # Calculate age (ensure it's non-negative)
        age = max(0, current_year - mention.year)

        # Apply exponential decay: score = weight * exp(-lambda * age)
        try:
             decay_factor = math.exp(-decay_rate * age)
             trend_score += weight * decay_factor
        except OverflowError:
             logger.error(f"OverflowError calculating decay factor for mention year {mention.year} with age {age} and decay rate {decay_rate}. Skipping mention.")
             continue # Skip this mention if calculation overflows

    logger.debug(f"Calculated recency-weighted trend score: {trend_score}")
    return trend_score

def _calculate_rate_of_change_score(mentions: List[MentionItem], weights: Dict[str, float], window_years: float) -> float:
    """
    Placeholder for calculating trend score based on the change in evidence
    strength over defined time windows.
    """
    logger.warning("RateOfChange trend calculation method is not implemented. Returning placeholder value 0.0.")
    # Implementation would require:
    # 1. Grouping mentions by time windows (e.g., last X years, previous X years).
    # 2. Calculating a raw weighted score (similar to evidence.py) for each window.
    # 3. Calculating the difference or ratio between recent and past window scores.
    # Example:
    # current_window_score = calculate_score_for_window(mentions, weights, current_window)
    # previous_window_score = calculate_score_for_window(mentions, weights, previous_window)
    # trend_score = current_window_score - previous_window_score # Or ratio, or log ratio etc.
    return 0.0 # Placeholder

def _calculate_evidence_progression_score(mentions: List[MentionItem], weights: Dict[str, float], config: Dict[str, Any]) -> float:
    """
    Placeholder for calculating trend score based on recent progression
    up the evidence hierarchy.
    """
    logger.warning("EvidenceProgression trend calculation method is not implemented. Returning placeholder value 0.0.")
    # Implementation would require:
    # 1. Tracking the highest evidence tier (max weight) achieved per year or over time.
    # 2. Identifying recent advancements to higher tiers based on config thresholds (e.g., points for reaching 'Guideline' in last 2 years).
    # 3. Summing points for recent progressions.
    return 0.0 # Placeholder


def calculate(mentions: List[MentionItem], config: Dict[str, Any]) -> float:
    """
    Calculates the Trend score for the relationship based on the configured method.

    Args:
        mentions: List of MentionItem objects for the relationship.
        config: The loaded configuration dictionary.

    Returns:
        The final Trend Score (float).

    Raises:
        CalculationError: If calculation fails.
        ConfigurationError: If config is invalid or missing required keys.
    """
    logger.info("Calculating Trend score...")
    if not mentions:
        logger.warning("No mentions provided for trend calculation. Returning 0.")
        return 0.0

    try:
        # --- Get relevant config sections ---
        trend_config = config.get('trend', {})
        weights = config.get('source_weights', {})
        if not trend_config or not weights:
             raise ConfigurationError("Missing 'trend' or 'source_weights' in configuration.")

        method = trend_config.get('method')
        if not method:
             raise ConfigurationError("Missing 'method' in trend configuration.")

        # --- Dispatch to appropriate calculation function ---
        trend_score = 0.0
        if method == "RecencyWeighted":
            recency_config = trend_config.get('recency_weighted', {})
            decay_rate = recency_config.get('decay_rate')
            if decay_rate is None: # Check for None specifically, as 0 is a valid rate
                 raise ConfigurationError("Missing 'decay_rate' in trend.recency_weighted config.")
            trend_score = _calculate_recency_weighted_score(mentions, weights, decay_rate)

        elif method == "RateOfChange":
            roc_config = trend_config.get('rate_of_change', {})
            window_years = roc_config.get('window_years')
            if window_years is None or window_years <= 0:
                 raise ConfigurationError("Missing or invalid 'window_years' in trend.rate_of_change config.")
            trend_score = _calculate_rate_of_change_score(mentions, weights, window_years) # Placeholder call

        elif method == "EvidenceProgression":
            prog_config = trend_config.get('evidence_progression', {})
            # Pass relevant sub-config if needed by the implementation
            trend_score = _calculate_evidence_progression_score(mentions, weights, prog_config) # Placeholder call

        else:
            raise ConfigurationError(f"Invalid trend calculation method specified: {method}")

        logger.info(f"Trend score calculation complete using method '{method}'. Score: {trend_score}")
        return trend_score

    except ConfigurationError as e:
        logger.error(f"Configuration error during trend calculation: {e}", exc_info=True)
        raise # Re-raise specific config errors
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"An unexpected error occurred during trend calculation: {e}", exc_info=True)
        raise CalculationError(f"Unexpected error in trend calculation: {e}")
