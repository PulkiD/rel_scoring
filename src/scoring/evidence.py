# src/scoring/evidence.py
# Calculates the Evidence Strength score.

import math
from typing import List, Dict, Any
from ..data_models.models import MentionItem # Import the Pydantic model for type hinting
from ..utils.logger import get_logger
from ..exceptions import CalculationError, ConfigurationError

logger = get_logger()

def _calculate_raw_weighted_frequency(mentions: List[MentionItem], weights: Dict[str, float], aggregation_method: str) -> float:
    """
    Calculates the raw score based on mention counts and source weights,
    before normalization.

    Args:
        mentions: List of MentionItem objects for the relationship.
        weights: Dictionary mapping source_type to its weight.
        aggregation_method: Method to use ('Logarithmic' or 'SimpleSum').

    Returns:
        The raw weighted frequency score.

    Raises:
        ConfigurationError: If an invalid aggregation method is specified.
        KeyError: If a mention's source_type is not found in weights.
    """
    logger.debug(f"Calculating raw weighted frequency using method: {aggregation_method}")
    raw_score = 0.0

    if aggregation_method == "SimpleSum":
        for mention in mentions:
            try:
                raw_score += weights[mention.source_type]
            except KeyError:
                logger.warning(f"Source type '{mention.source_type}' not found in configured weights. Mention skipped.")
                # Or raise ConfigurationError("Missing weight for source type...") ? Decide on strictness.

    elif aggregation_method == "Logarithmic":
        # Group mentions by source type first
        mentions_by_type = {}
        for mention in mentions:
            source_type = mention.source_type
            if source_type not in weights:
                 logger.warning(f"Source type '{source_type}' not found in configured weights. Mention skipped.")
                 continue # Skip mentions with unconfigured source types

            if source_type not in mentions_by_type:
                mentions_by_type[source_type] = 0
            mentions_by_type[source_type] += 1

        # Apply logarithmic aggregation: weight * log(1 + count)
        for source_type, count in mentions_by_type.items():
            weight = weights[source_type]
            raw_score += weight * math.log1p(count) # log1p(x) calculates log(1 + x) accurately

    else:
        raise ConfigurationError(f"Invalid frequency aggregation method specified: {aggregation_method}")

    logger.debug(f"Calculated raw weighted frequency: {raw_score}")
    return raw_score

def calculate_pmi(raw_score: float, entity_a_prominence: float, entity_b_prominence: float, total_count_or_scale: float = 1e6) -> float:
    """
    Calculates the Pointwise Mutual Information (PMI) score, clipped at 0.

    Args:
        raw_score: Score representing the co-occurrence of A and B (proportional to Count(A,B)).
        entity_a_prominence: Score representing the occurrence of A (proportional to Count(A)).
        entity_b_prominence: Score representing the occurrence of B (proportional to Count(B)).
        total_count_or_scale: Represents the total number of events/documents (N) or a scaling factor
                              in the PMI formula: log [ (Count(A,B) * N) / (Count(A) * Count(B)) ].
                              Defaults to 1e6 based on the previous placeholder. This might need tuning.

    Returns:
        The calculated PMI score, or 0.0 if inputs are invalid or PMI is negative.
    """
    # Avoid log(0) or division by zero
    if raw_score <= 0 or entity_a_prominence <= 0 or entity_b_prominence <= 0:
        return 0.0 # Return 0 for non-positive inputs, as PMI is undefined or meaningless

    try:
        # Calculate PMI based on the simplified formula: log [ (Count(A,B) * N) / (Count(A) * Count(B)) ]
        # Assuming inputs are proportional to counts and total_count_or_scale represents N * proportionality_constants
        pmi_value = math.log((raw_score * total_count_or_scale) / (entity_a_prominence * entity_b_prominence))
        # PMI measures how much more likely the co-occurrence is than expected by chance.
        # Negative PMI means co-occurrence is less likely than expected.
        # Often, only positive associations are of interest, so clip at 0.
        return max(0.0, pmi_value)
    except (ValueError, OverflowError) as e:
        # Catch potential math errors like log of a non-positive number (though ideally prevented by the initial check)
        logger.error(f"Error calculating PMI for scores ({raw_score}, {entity_a_prominence}, {entity_b_prominence}): {e}")
        return 0.0

def _apply_normalization(raw_score: float, entity_a_prominence: float, entity_b_prominence: float, total_mentions: int, method: str) -> float:
    """
    Applies normalization to the raw score to mitigate entity prominence bias.

    Args:
        raw_score: The raw weighted frequency score.
        entity_a_prominence: Overall prominence score for entity A.
        entity_b_prominence: Overall prominence score for entity B.
        total_mentions: Total number of mentions for this specific relationship.
        method: Normalization method ('PMI-like', 'RelativeFrequency', 'None').

    Returns:
        The normalized evidence strength score.

    Raises:
        ConfigurationError: If an invalid normalization method is specified.
        CalculationError: For potential issues like division by zero if inputs are invalid.
    """
    logger.debug(f"Applying normalization method: {method}")

    # Ensure prominence scores are valid for calculations
    if entity_a_prominence <= 0 or entity_b_prominence <= 0:
         # How to handle this depends on the method. For PMI/RelativeFreq, it's problematic.
         # Option 1: Return a default low score or 0
         # Option 2: Log a warning and proceed cautiously or switch to 'None'
         # Option 3: Raise an error
         logger.warning(f"Entity prominence scores must be positive for normalization (A: {entity_a_prominence}, B: {entity_b_prominence}). Normalization might be inaccurate or skipped.")
         # For now, let's default to skipping normalization if prominence is invalid
         if method in ["PMI-like", "RelativeFrequency"]:
              method = "None"


    if method == "None":
        normalized_score = raw_score
    elif method == "RelativeFrequency":
        # Example: Normalize by the average prominence of the two entities.
        # Variants: Normalize by min(A, B), max(A, B), or just A or B. Configurable?
        # Need to prevent division by zero.
        avg_prominence = (entity_a_prominence + entity_b_prominence) / 2.0
        if avg_prominence == 0:
             logger.error("Cannot normalize using RelativeFrequency with zero average entity prominence.")
             # Fallback to raw score or raise error? Let's return raw score with warning.
             logger.warning("Falling back to un-normalized score due to zero average prominence.")
             normalized_score = raw_score
        else:
             # Simple ratio - might need scaling or logarithmic adjustments depending on score distribution
             normalized_score = raw_score / avg_prominence
             # Placeholder: Add scaling/log if needed, e.g., math.log1p(raw_score / avg_prominence)

    elif method == "PMI-like":
        # Calculate Pointwise Mutual Information-like score.
        # This measures how much more likely the co-occurrence (raw_score) is
        # than would be expected if occurrences (prominence scores) were independent.
        # Note: The interpretation requires understanding how raw_score and prominence
        # relate to counts and probabilities in the corpus.
        # The default scaling factor in calculate_pmi might need adjustment.
        normalized_score = calculate_pmi(raw_score, entity_a_prominence, entity_b_prominence)

    else:
        raise ConfigurationError(f"Invalid normalization method specified: {method}")

    logger.debug(f"Calculated normalized score: {normalized_score}")
    # Consider adding clamping or scaling if scores vary wildly
    # e.g., return max(0, min(100, normalized_score)) # If scores should be within a range
    return normalized_score

def calculate(mentions: List[MentionItem], entity_a_prominence: float, entity_b_prominence: float, config: Dict[str, Any]) -> float:
    """
    Calculates the Evidence Strength score for the relationship.

    Orchestrates the calculation of raw weighted frequency and applies normalization.

    Args:
        mentions: List of MentionItem objects for the relationship.
        entity_a_prominence: Overall prominence score for entity A.
        entity_b_prominence: Overall prominence score for entity B.
        config: The loaded configuration dictionary.

    Returns:
        The final Evidence Strength score (float).

    Raises:
        CalculationError: If calculation fails.
        ConfigurationError: If config is invalid or missing required keys.
    """
    logger.info("Calculating Evidence Strength score...")
    if not mentions:
        logger.warning("No mentions provided for evidence strength calculation. Returning 0.")
        return 0.0

    try:
        # --- Get relevant config sections ---
        evidence_config = config.get('evidence_strength', {})
        weights = config.get('source_weights', {})
        if not evidence_config or not weights:
             raise ConfigurationError("Missing 'evidence_strength' or 'source_weights' in configuration.")

        aggregation_method = evidence_config.get('frequency_aggregation')
        normalization_method = evidence_config.get('normalization_method')
        if not aggregation_method or not normalization_method:
             raise ConfigurationError("Missing 'frequency_aggregation' or 'normalization_method' in evidence_strength config.")

        # --- Calculate Raw Score ---
        raw_score = _calculate_raw_weighted_frequency(mentions, weights, aggregation_method)

        # --- Apply Normalization ---
        normalized_score = _apply_normalization(
            raw_score,
            entity_a_prominence,
            entity_b_prominence,
            len(mentions), # Pass total mentions count if needed by normalization
            normalization_method
        )

        logger.info(f"Evidence Strength calculation complete. Score: {normalized_score}")
        return normalized_score

    except (ConfigurationError, KeyError, ValueError, ZeroDivisionError) as e:
        logger.error(f"Error during evidence strength calculation: {e}", exc_info=True)
        # Re-raise as CalculationError for the main scorer to catch
        raise CalculationError(f"Failed to calculate evidence strength: {e}")
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"An unexpected error occurred during evidence strength calculation: {e}", exc_info=True)
        raise CalculationError(f"Unexpected error in evidence strength calculation: {e}")

