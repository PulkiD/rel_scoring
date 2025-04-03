# src/scoring/trend.py
# Calculates the Trend Score for the relationship.

import math
import datetime
from typing import List, Dict, Any, Optional
from ..data_models.models import MentionItem # Import Pydantic model
from ..utils.logger import get_logger
from ..exceptions import CalculationError, ConfigurationError
from datetime import timedelta

logger = get_logger()

def _calculate_recency_weighted_score(mentions: List[MentionItem], weights: Dict[str, float], decay_rate: float) -> float:
    """
    Calculates trend score based on recency, weighting recent mentions more heavily
    using exponential decay.
    """
    logger.debug(f"RecencyWeighted: Calculating trend score using RecencyWeighted method with decay rate: {decay_rate}")
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

    logger.debug(f"RecencyWeighted: Calculated recency-weighted trend score: {trend_score}")
    return trend_score

def _calculate_weighted_score_for_mentions(mentions: List[MentionItem], weights: Dict[str, float]) -> float:
    """Calculates the sum of weighted scores for a list of mentions,
    where the score for each mention is determined by its source_type weight from the config.
    """
    total_score = 0.0
    for mention in mentions:
        # Get weight based on source_type from the provided weights dictionary
        weight = weights.get(mention.source_type, 0.0) # Use 0 weight if source_type not in weights
        if weight == 0.0 and mention.source_type in weights:
             # Only warn if the source_type was explicitly configured but set to 0
             logger.warning(f"Mention from source '{mention.source_type}' in year {mention.year} has configured weight of 0.")
        elif mention.source_type not in weights:
             logger.warning(f"Mention source '{mention.source_type}' in year {mention.year} not found in source_weights config. Assigning weight 0.")

        # The score contribution of this mention is its configured weight
        total_score += weight
    return total_score

def _calculate_rate_of_change_score(mentions: List[MentionItem], weights: Dict[str, float], window_years: float) -> float:
    """
    Calculates trend score based on the change in weighted evidence strength
    between two consecutive time windows defined by years.

    Args:
        mentions: A list of MentionItem objects, each with a 'year' (int) and 'score' (float).
        weights: A dictionary mapping source_type to its weight.
        window_years: The duration of each time window in years (float, will be converted to int >= 1).

    Returns:
        The difference between the weighted score in the most recent window
        and the weighted score in the preceding window. Returns 0.0 if there are
        no mentions or if window_years is non-positive.
    """
    if not mentions:
        logger.warning("No mentions provided for RateOfChange trend calculation. Returning 0.")
        return 0.0

    # Ensure window size is at least 1 year
    window_size_years = max(1, int(window_years))
    if window_years <= 0:
         logger.warning(f"window_years ({window_years}) is non-positive. RateOfChange calculation requires positive window size. Returning 0.")
         return 0.0

    current_year = datetime.datetime.now().year

    # Define year boundaries for the windows
    # Current window: (current_year - window_size_years, current_year]
    # Previous window: (current_year - 2*window_size_years, current_year - window_size_years]
    current_window_end_year = current_year
    current_window_start_year_exclusive = current_year - window_size_years
    previous_window_end_year = current_window_start_year_exclusive
    previous_window_start_year_exclusive = current_year - (2 * window_size_years)

    logger.debug(f"RateOfChange: Current Year={current_year}, Window Size={window_size_years} years")
    logger.debug(f"RateOfChange: Current Window Year Range: ({current_window_start_year_exclusive}, {current_window_end_year}]")
    logger.debug(f"RateOfChange: Previous Window Year Range: ({previous_window_start_year_exclusive}, {previous_window_end_year}]")

    # Filter mentions into windows based on year
    current_window_mentions = []
    previous_window_mentions = []

    for mention in mentions:
        # Validate mention year
        if not isinstance(mention.year, int) or mention.year <= 0:
            logger.warning(f"Mention has invalid year '{mention.year}'. Skipping.")
            continue

        mention_year = mention.year
        # Check if the mention falls within the defined year windows
        if current_window_start_year_exclusive < mention_year <= current_window_end_year:
            current_window_mentions.append(mention)
        elif previous_window_start_year_exclusive < mention_year <= previous_window_end_year:
            previous_window_mentions.append(mention)

    # Calculate weighted scores for each window
    current_window_score = _calculate_weighted_score_for_mentions(current_window_mentions, weights)
    previous_window_score = _calculate_weighted_score_for_mentions(previous_window_mentions, weights)

    # Calculate the rate of change (difference)
    trend_score = current_window_score - previous_window_score

    logger.debug(f"RateOfChange Trend: Current Window ({current_window_start_year_exclusive+1}-{current_window_end_year}): Score={current_window_score:.2f} ({len(current_window_mentions)} mentions)")
    logger.debug(f"RateOfChange Trend: Previous Window ({previous_window_start_year_exclusive+1}-{previous_window_end_year}): Score={previous_window_score:.2f} ({len(previous_window_mentions)} mentions)")
    logger.debug(f"RateOfChange Trend: Calculated Score = {trend_score:.2f}")

    return trend_score

def _calculate_evidence_progression_score(mentions: List[MentionItem], weights: Dict[str, float], config: Dict[str, Any]) -> float:
    """
    Calculates trend score based on recent progression up the evidence hierarchy.

    Awards points if mentions with higher source weights appear within a recent
    time window compared to the maximum weight seen before that window.

    Args:
        mentions: List of MentionItem objects (each with 'year' and 'source_type').
        weights: Dictionary mapping source_type to its numerical weight.
        config: The 'evidence_progression' sub-dictionary from the main config,
                containing 'recent_years_threshold' and 'progression_points'.

    Returns:
        The calculated progression score (float). Returns 0.0 if config is
        missing, invalid, or no progression is detected.
    """
    if not mentions:
        logger.warning("No mentions provided for EvidenceProgression calculation. Returning 0.")
        return 0.0

    # --- Get config parameters ---
    try:
        recent_years_threshold = config.get('recent_years_threshold')
        progression_points = config.get('progression_points')

        if recent_years_threshold is None or not isinstance(recent_years_threshold, (int, float)) or recent_years_threshold <= 0:
             logger.error(f"Invalid or missing 'recent_years_threshold' ({recent_years_threshold}) in evidence_progression config.")
             return 0.0 # Cannot proceed without a valid threshold
        if progression_points is None or not isinstance(progression_points, dict):
             logger.error(f"Invalid or missing 'progression_points' in evidence_progression config.")
             return 0.0 # Cannot proceed without points mapping

    except Exception as e:
         logger.error(f"Error accessing evidence_progression config: {e}", exc_info=True)
         return 0.0

    # --- Determine time boundaries ---
    current_year = datetime.datetime.now().year
    # Year from which the 'recent' period starts (inclusive)
    recent_start_year = current_year - int(recent_years_threshold) + 1
    logger.debug(f"EvidenceProgression: Current Year={current_year}, Recent Threshold={recent_years_threshold} years -> Recent Start Year={recent_start_year}")

    # --- Find max historical weight and recent source types ---
    max_historical_weight = -1.0 # Initialize below any possible weight
    recent_source_types = set()

    for mention in mentions:
        if not isinstance(mention.year, int) or mention.year <= 0:
            # Skip mentions with invalid years
            continue

        mention_weight = weights.get(mention.source_type, -1.0) # Use -1 to handle unweighted types gracefully

        if mention.year < recent_start_year:
            # Mention is in the historical period
            if mention_weight > max_historical_weight:
                max_historical_weight = mention_weight
        else:
            # Mention is in the recent period
            if mention_weight > 0: # Only consider source types with positive weight
                 recent_source_types.add(mention.source_type)

    if max_historical_weight == -1.0:
        # No valid mentions found in the historical period, treat baseline as 0
        max_historical_weight = 0.0
        logger.debug("EvidenceProgression: No mentions found before recent period. Historical max weight set to 0.")
    else:
        logger.debug(f"EvidenceProgression: Max weight before {recent_start_year} = {max_historical_weight:.2f}")

    # --- Calculate progression score ---
    total_progression_score = 0.0
    progressed_tiers = []

    for source_type in recent_source_types:
        recent_weight = weights.get(source_type, -1.0)
        if recent_weight > max_historical_weight:
            # This source type represents a progression beyond the historical max
            points = progression_points.get(source_type)
            if points is not None and isinstance(points, (int, float)):
                total_progression_score += points
                progressed_tiers.append(f"{source_type} (Weight: {recent_weight:.2f}, Points: {points})")
                logger.debug(f"  - Progression detected: Reached '{source_type}' (Weight: {recent_weight:.2f} > {max_historical_weight:.2f}). Added {points} points.")
            else:
                 logger.warning(f"  - Progression detected for '{source_type}' (Weight: {recent_weight:.2f}), but no valid points found in progression_points config. Skipping.")

    if not progressed_tiers:
        logger.debug("EvidenceProgression: No progression detected in the recent period.")

    logger.info(f"EvidenceProgression calculation complete. Score: {total_progression_score:.2f}")
    return total_progression_score

def calculate(mentions: List[MentionItem], config: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates all Trend scores for the relationship using different methods.

    Args:
        mentions: List of MentionItem objects for the relationship.
        config: The loaded configuration dictionary.

    Returns:
        A dictionary containing all trend scores:
        {
            "recency_weighted": float,  # Score based on recency-weighted evidence
            "rate_of_change": float,    # Score based on rate of change between time windows
            "evidence_progression": float # Score based on progression in evidence hierarchy
        }

    Raises:
        CalculationError: If calculation fails.
        ConfigurationError: If config is invalid or missing required keys.
    """
    logger.info("Calculating all Trend scores...")
    if not mentions:
        logger.warning("No mentions provided for trend calculation. Returning all scores as 0.")
        return {
            "recency_weighted": 0.0,
            "rate_of_change": 0.0,
            "evidence_progression": 0.0
        }

    try:
        # --- Get relevant config sections ---
        trend_config = config.get('trend', {})
        weights = config.get('source_weights', {})
        if not trend_config or not weights:
             raise ConfigurationError("Missing 'trend' or 'source_weights' in configuration.")

        # --- Calculate all trend scores ---
        trend_scores = {}

        # 1. Recency Weighted Score
        recency_config = trend_config.get('recency_weighted', {})
        decay_rate = recency_config.get('decay_rate')
        if decay_rate is None:
             logger.warning("Missing 'decay_rate' in trend.recency_weighted config. Using default 0.15.")
             decay_rate = 0.15
        trend_scores['recency_weighted'] = _calculate_recency_weighted_score(mentions, weights, decay_rate)

        # 2. Rate of Change Score
        roc_config = trend_config.get('rate_of_change', {})
        window_years = roc_config.get('window_years')
        if window_years is None or window_years <= 0:
             logger.warning("Missing or invalid 'window_years' in trend.rate_of_change config. Using default 5.0.")
             window_years = 5.0
        trend_scores['rate_of_change'] = _calculate_rate_of_change_score(mentions, weights, window_years)

        # 3. Evidence Progression Score
        prog_config = trend_config.get('evidence_progression', {})
        trend_scores['evidence_progression'] = _calculate_evidence_progression_score(mentions, weights, prog_config)

        logger.info(f"All trend scores calculated: {trend_scores}")
        return trend_scores

    except ConfigurationError as e:
        logger.error(f"Configuration error during trend calculation: {e}", exc_info=True)
        raise # Re-raise specific config errors
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"An unexpected error occurred during trend calculation: {e}", exc_info=True)
        raise CalculationError(f"Unexpected error in trend calculation: {e}")
