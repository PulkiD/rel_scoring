# tests/test_main_scorer.py
# Unit tests for the main RelationshipScorer class.

import pytest
from src.main_scorer import RelationshipScorer # Adjust import based on your final structure/installation
from src.exceptions import ScoringInitializationError, InputValidationError, CalculationError
# Import Pydantic models if needed for creating test data
from src.data_models.models import ScorerInputData, MentionItem, EntityMetadata

# --- Test Fixtures ---

@pytest.fixture
def valid_input_data():
    """ Provides a valid input data dictionary for testing. """
    return {
        "relationship_mentions": [
            {"source_type": "Guideline", "year": 2023, "sentiment": "Positive"},
            {"source_type": "Phase 3 CT", "year": 2022, "sentiment": "Positive"},
            {"source_type": "PubMed", "year": 2020, "sentiment": "Neutral"},
            {"source_type": "PubMed", "year": 2019, "sentiment": "Negative"} # Add more variety
        ],
        "entity_a_metadata": {
            "id": "ENTITY_A_TEST",
            "overall_prominence": 150.0
        },
        "entity_b_metadata": {
            "id": "ENTITY_B_TEST",
            "overall_prominence": 80.0
        }
    }

@pytest.fixture
def invalid_input_data_missing_key():
    """ Provides input data missing a required key. """
    return {
        # Missing "relationship_mentions"
        "entity_a_metadata": {
            "id": "ENTITY_A_TEST",
            "overall_prominence": 150.0
        },
        "entity_b_metadata": {
            "id": "ENTITY_B_TEST",
            "overall_prominence": 80.0
        }
    }

@pytest.fixture
def invalid_input_data_bad_type():
    """ Provides input data with incorrect types. """
    return {
        "relationship_mentions": [
            {"source_type": "Guideline", "year": "2023-invalid", "sentiment": "Positive"}, # Bad year type
        ],
        "entity_a_metadata": {
            "id": "ENTITY_A_TEST",
            "overall_prominence": "low" # Bad prominence type
        },
        "entity_b_metadata": {
            "id": "ENTITY_B_TEST",
            "overall_prominence": 80.0
        }
    }

# --- Test Cases ---

def test_scorer_initialization_success(valid_input_data):
    """ Test successful initialization of RelationshipScorer. """
    try:
        scorer = RelationshipScorer(input_data=valid_input_data)
        assert scorer is not None
        assert scorer.config is not None # Check config loaded
        assert len(scorer.mentions) == 4
        assert scorer.entity_a.id == "ENTITY_A_TEST"
    except ScoringInitializationError as e:
        pytest.fail(f"Initialization failed unexpectedly: {e}")

def test_scorer_initialization_invalid_input_missing_key(invalid_input_data_missing_key):
    """ Test initialization fails with missing keys due to Pydantic validation. """
    with pytest.raises(InputValidationError):
        RelationshipScorer(input_data=invalid_input_data_missing_key)

def test_scorer_initialization_invalid_input_bad_type(invalid_input_data_bad_type):
    """ Test initialization fails with incorrect types due to Pydantic validation. """
    with pytest.raises(InputValidationError):
        RelationshipScorer(input_data=invalid_input_data_bad_type)

# --- Placeholder tests for calculation methods ---
# These tests would need more specific assertions based on expected outputs
# given the placeholder logic or actual implemented logic.

def test_get_evidence_strength_runs(valid_input_data):
    """ Test that get_evidence_strength runs without critical errors. """
    scorer = RelationshipScorer(input_data=valid_input_data)
    try:
        score = scorer.get_evidence_strength()
        assert isinstance(score, float) # Basic type check
        # Add assertions for expected value range or specific value if logic is known
    except CalculationError as e:
        pytest.fail(f"get_evidence_strength failed unexpectedly: {e}")

def test_get_sentiment_scores_runs(valid_input_data):
    """ Test that get_sentiment_scores runs and returns expected structure. """
    scorer = RelationshipScorer(input_data=valid_input_data)
    try:
        scores = scorer.get_sentiment_scores()
        assert isinstance(scores, dict)
        assert "positive_score" in scores
        assert "negative_score" in scores
        assert "neutral_score" in scores
        assert "net_score" in scores
        assert "dominant_sentiment" in scores
        # Add assertions for expected values based on input and config
    except CalculationError as e:
        pytest.fail(f"get_sentiment_scores failed unexpectedly: {e}")

def test_get_trend_score_runs(valid_input_data):
    """ Test that get_trend_score runs without critical errors. """
    scorer = RelationshipScorer(input_data=valid_input_data)
    try:
        score = scorer.get_trend_score()
        assert isinstance(score, float)
        # Add assertions for expected value
    except CalculationError as e:
        pytest.fail(f"get_trend_score failed unexpectedly: {e}")

def test_get_all_scores_runs(valid_input_data):
    """ Test that get_all_scores runs and returns the combined dictionary. """
    scorer = RelationshipScorer(input_data=valid_input_data)
    try:
        all_scores = scorer.get_all_scores()
        assert isinstance(all_scores, dict)
        assert "evidence_strength" in all_scores
        assert "sentiment_scores" in all_scores
        assert "trend_score" in all_scores
        assert isinstance(all_scores["sentiment_scores"], dict) # Check nested structure
        # Add more specific assertions
    except CalculationError as e:
        pytest.fail(f"get_all_scores failed unexpectedly: {e}")

# TODO: Add more tests:
# - Test edge cases (empty mentions list - handled in init?, zero prominence)
# - Test different configuration options (normalization methods, trend methods)
# - Test specific calculation logic once implemented (e.g., assert specific scores for known inputs)
# - Test error handling within calculation functions (mocking dependencies if needed)
# - Test config loading errors (e.g., missing config file) - might need to mock os.path.exists

