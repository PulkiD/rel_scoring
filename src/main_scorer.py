# src/main_scorer.py
# Contains the main RelationshipScorer class for calculating ensemble scores.

from pydantic import ValidationError

# Import package components using relative imports
from .utils.config_loader import load_config
from .utils.logger import get_logger
from .scoring import evidence, sentiment, trend
from .exceptions import (
    ScoringInitializationError,
    CalculationError,
    ConfigurationError,
    InputValidationError,
    OutputValidationError
)
from .data_models.models import (
    ScorerInputData,
    ScorerOutputData,
    MentionItem,
    EntityMetadata
)
from typing import Dict, Any, List

class RelationshipScorer:
    """
    Orchestrates the calculation of ensemble scores for a relationship.

    Initializes with relationship data, validates input using Pydantic,
    loads configuration, and provides methods to calculate individual scores
    or the complete ensemble.
    """
    # Class attributes for validated data and config
    mentions: List[MentionItem]
    entity_a: EntityMetadata
    entity_b: EntityMetadata
    config: Dict[str, Any]
    logger: Any # Type hint for logger if possible, depends on logger implementation details

    def __init__(self, input_data: Dict[str, Any]):
        """
        Initializes the scorer, validates input using Pydantic, and loads configuration.

        Args:
            input_data (dict): Dictionary containing keys 'relationship_mentions',
                               'entity_a_metadata', 'entity_b_metadata'. Must conform
                               to the ScorerInputData Pydantic model.

        Raises:
            ScoringInitializationError: If input data fails validation or config cannot be loaded.
        """
        self.logger = get_logger() # Initialize logger first
        self.logger.info(f"Initializing RelationshipScorer for entity pair: {input_data.get('entity_a_metadata',{}).get('id','N/A')} - {input_data.get('entity_b_metadata',{}).get('id','N/A')}")

        # 1. Validate input using Pydantic
        try:
            validated_input = ScorerInputData(**input_data)
            # Store validated components directly
            self.mentions = validated_input.relationship_mentions
            self.entity_a = validated_input.entity_a_metadata
            self.entity_b = validated_input.entity_b_metadata
            self.logger.debug("Input data validated successfully via Pydantic.")
        except ValidationError as e:
            self.logger.error(f"Input data validation failed: {e}", exc_info=True)
            # Wrap Pydantic error in our custom exception for consistency
            raise InputValidationError(e)
        except Exception as e: # Catch other potential errors during model instantiation
             self.logger.error(f"Unexpected error during input data processing: {e}", exc_info=True)
             raise ScoringInitializationError(f"Unexpected error processing input data: {e}")


        # 2. Load configuration
        try:
            self.config = load_config() # Reads from config/scoring_config.yaml (or configured path)
            self.logger.info("Configuration loaded successfully.")
            # Optional: Validate loaded config against a schema if needed
        except ConfigurationError as e:
             self.logger.error(f"Failed to load configuration: {e}", exc_info=True)
             raise ScoringInitializationError(f"Failed to load configuration: {e}") # Re-raise as init error
        except Exception as e:
            self.logger.error(f"Unexpected error loading configuration: {e}", exc_info=True)
            raise ScoringInitializationError(f"Unexpected error loading configuration: {e}")

        # 3. Pre-process data if necessary
        try:
            self._preprocess_data()
        except Exception as e:
            self.logger.error(f"Error during data preprocessing: {e}", exc_info=True)
            raise ScoringInitializationError(f"Error during data preprocessing: {e}")

        self.logger.info("RelationshipScorer initialized successfully.")

    def _preprocess_data(self):
        """
        Placeholder for any data preprocessing needed after validation and config loading.
        For example, sorting mentions by year, grouping, etc.
        """
        self.logger.debug("Running data preprocessing step (currently placeholder)...")
        # Example: Sort mentions by year if needed by some calculation
        # self.mentions.sort(key=lambda m: m.year)
        pass

    def get_evidence_strength(self) -> float:
        """Calculates the Evidence Strength score."""
        self.logger.debug(f"Calculating Evidence Strength for {self.entity_a.id} - {self.entity_b.id}...")
        try:
            # Pass necessary components from validated data
            score = evidence.calculate(
                self.mentions,
                self.entity_a.overall_prominence,
                self.entity_b.overall_prominence,
                self.config
            )
            self.logger.debug(f"Evidence Strength calculated: {score}")
            return score
        except (CalculationError, ConfigurationError) as e:
            # Log expected calculation/config errors and re-raise
            self.logger.error(f"Error calculating evidence strength: {e}", exc_info=True)
            raise
        except Exception as e:
            # Wrap unexpected errors in CalculationError
            self.logger.error(f"Unexpected error in evidence strength calculation: {e}", exc_info=True)
            raise CalculationError(f"Unexpected error in evidence strength: {e}")

    def get_sentiment_scores(self) -> Dict[str, Any]:
        """Calculates the Sentiment Scores (NetScore detailed approach)."""
        self.logger.debug(f"Calculating Sentiment Scores for {self.entity_a.id} - {self.entity_b.id}...")
        try:
            scores = sentiment.calculate(self.mentions, self.config)
            self.logger.debug(f"Sentiment Scores calculated: {scores}")
            return scores # Should already be a dict from sentiment.calculate
        except (CalculationError, ConfigurationError) as e:
            self.logger.error(f"Error calculating sentiment scores: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in sentiment score calculation: {e}", exc_info=True)
            raise CalculationError(f"Unexpected error in sentiment scores: {e}")

    def get_trend_score(self) -> float:
        """Calculates the Trend Score."""
        self.logger.debug(f"Calculating Trend Score for {self.entity_a.id} - {self.entity_b.id}...")
        try:
            score = trend.calculate(self.mentions, self.config)
            self.logger.debug(f"Trend Score calculated: {score}")
            return score
        except (CalculationError, ConfigurationError) as e:
            self.logger.error(f"Error calculating trend score: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in trend score calculation: {e}", exc_info=True)
            raise CalculationError(f"Unexpected error in trend score: {e}")

    def get_all_scores(self) -> Dict[str, Any]:
        """
        Calculates and returns all ensemble scores in a dictionary.

        Performs optional output validation using the ScorerOutputData model.

        Returns:
            dict: A dictionary containing 'evidence_strength', 'sentiment_scores', and 'trend_score'.

        Raises:
            CalculationError: If any underlying score calculation fails.
            OutputValidationError: If the final assembled output fails Pydantic validation.
        """
        self.logger.info(f"Calculating all ensemble scores for {self.entity_a.id} - {self.entity_b.id}...")
        try:
            # Calculate all individual scores
            evidence_score = self.get_evidence_strength()
            sentiment_score_dict = self.get_sentiment_scores()
            trend_score_val = self.get_trend_score()

            # Assemble raw results
            scores_raw = {
                "evidence_strength": evidence_score,
                "sentiment_scores": sentiment_score_dict,
                "trend_score": trend_score_val
            }

            # --- Optional but recommended: Validate final output ---
            try:
                validated_output = ScorerOutputData(**scores_raw)
                self.logger.info("Successfully calculated and validated all scores.")
                # Return the validated data as a standard dictionary
                return validated_output.model_dump()
            except ValidationError as e:
                self.logger.error(f"Output data validation failed: {e}. Returning raw data.", exc_info=True)
                # Decide behaviour: raise error or return raw data with warning?
                # Raising ensures consumers always get valid data if no error is raised.
                raise OutputValidationError(e)
                # Alternatively, return raw data:
                # return scores_raw

        except (CalculationError, ConfigurationError) as e:
             # Catch errors raised by individual getters
             self.logger.error(f"Failed to calculate all scores due to error in underlying calculation: {e}")
             # Re-raise the original error
             raise
        except Exception as e:
             # Catch unexpected errors during assembly
             self.logger.error(f"Unexpected error assembling final scores: {e}", exc_info=True)
             raise CalculationError(f"Unexpected error assembling final scores: {e}")

