# Relationship Scorer Package

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A Python package designed to calculate an ensemble of scores for relationships between two entities. It analyzes co-occurrence mentions across various sources, considering source authority, sentiment, temporal dynamics, and entity prominence to provide nuanced relationship insights.

## Features

* **Ensemble Scoring:** Calculates three distinct scores:
    * **Evidence Strength:** A normalized score reflecting the quantity and quality (source authority) of evidence supporting the relationship, adjusted for entity prominence bias.
    * **Sentiment Scores:** A detailed breakdown including weighted scores for positive, negative, and neutral mentions, a net sentiment score, and an overall dominant sentiment category.
    * **Trend Score:** A score indicating the relationship's momentum, based on configurable methods like evidence recency (default), rate of change, or progression through evidence tiers.
* **Configurable:** Utilizes YAML configuration files (`config/scoring_config.yaml`) to easily adjust source weights, calculation methods (e.g., normalization, aggregation, trend type), decay rates, and logging settings without code changes.
* **Data Validation:** Employs Pydantic (`src/data_models/models.py`) for robust validation of input data structures and types, ensuring data integrity.
* **Modular Design:** Score calculation logic is separated into distinct, focused modules within the `src/scoring/` directory, promoting maintainability and extensibility.
* **Logging:** Includes a configurable Singleton logger (`src/utils/logger.py`) for consistent and informative logging throughout the package.
* **Production Ready Structure:** Follows standard Python packaging practices with a `src/` layout, clear separation of concerns, custom exceptions, and support for testing and containerization (`Dockerfile`).

## Package Structure

```
relationship_scorer_package/
├── config/
│   ├── scoring_config.yaml       # Calculation parameters
│   └── data_model_config.yaml    # Human-readable schema description/example
├── src/
│   ├── __init__.py
│   ├── main_scorer.py            # Main RelationshipScorer class
│   ├── scoring/                  # Scoring logic modules (evidence, sentiment, trend)
│   ├── utils/                    # Utility functions (config loader, logger)
│   ├── data_models/              # Pydantic models for validation
│   └── exceptions.py             # Custom exception classes
├── tests/                        # Unit tests (placeholder)
│   └── fixtures/                 # Test data (placeholder)
├── README.md                     # This file
├── requirements.txt              # Package dependencies
├── setup.py                      # Packaging script (using setuptools)
└── Dockerfile                    # Docker configuration for containerization
```

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your_username/relationship_scorer_package.git](https://github.com/your_username/relationship_scorer_package.git) # Replace with your repo URL
    cd relationship_scorer_package
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Linux/macOS:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install the package:**
    * For development (allows editing code without reinstalling):
        ```bash
        pip install -e .
        ```
    * For standard installation:
        ```bash
        pip install .
        ```

## Usage

Import the `RelationshipScorer` class, prepare your input data dictionary, and then call the scoring methods.

```python
# Example usage script

from relationship_scorer.main_scorer import RelationshipScorer
# Import specific exceptions for more granular error handling if needed
from relationship_scorer.exceptions import RelationshipScorerError, InputValidationError, ConfigurationError, CalculationError

# 1. Prepare your input data dictionary
# This structure MUST conform to the ScorerInputData Pydantic model.
# See config/data_model_config.yaml for a detailed example.
input_data = {
    "relationship_mentions": [
        {"source_type": "Guideline", "year": 2024, "sentiment": "Positive", "mention_id": "guideline-abc"},
        {"source_type": "Phase 3 CT", "year": 2023, "sentiment": "Positive", "mention_id": "NCT12345"},
        {"source_type": "PubMed", "year": 2022, "sentiment": "Neutral", "mention_id": "pmid:30000001"},
        {"source_type": "PubMed", "year": 2021, "sentiment": "Negative", "mention_id": "pmid:30000000"},
        {"source_type": "Review", "year": 2024, "sentiment": "Positive", "mention_id": "review-xyz"}
        # Add all relevant mentions for the specific entity pair
    ],
    "entity_a_metadata": {
        "id": "DRUG_X",
        # This score must be pre-calculated based on your entire dataset
        "overall_prominence": 250.5
    },
    "entity_b_metadata": {
        "id": "DISEASE_Y",
        # This score must be pre-calculated based on your entire dataset
        "overall_prominence": 180.0
    }
}

# 2. Initialize the scorer and calculate scores
try:
    # Initialization validates input using Pydantic and loads config from files
    print("Initializing scorer...")
    scorer = RelationshipScorer(input_data=input_data)
    print("Scorer initialized.")

    # Calculate all scores at once
    print("Calculating all scores...")
    all_scores = scorer.get_all_scores()
    print("\n--- All Scores ---")
    # Pretty print the dictionary
    import json
    print(json.dumps(all_scores, indent=2))
    print("-" * 20)

    # Alternatively, calculate individual scores if needed
    # print("\nCalculating individual scores...")
    # evidence = scorer.get_evidence_strength()
    # print(f"Evidence Strength: {evidence:.3f}")
    #
    # sentiment = scorer.get_sentiment_scores()
    # print("Sentiment Scores:", sentiment)
    #
    # trend = scorer.get_trend_score()
    # print(f"Trend Score: {trend:.3f}")

except InputValidationError as e:
    print(f"\nERROR: Input data is invalid.")
    print(f"Details: {e.details}") # Pydantic validation error details
except ConfigurationError as e:
    print(f"\nERROR: Configuration problem.")
    print(f"Details: {e}")
except CalculationError as e:
    print(f"\nERROR: Problem during score calculation.")
    print(f"Details: {e}")
except ScoringInitializationError as e:
    print(f"\nERROR: Failed to initialize the scorer.")
    print(f"Details: {e}")
except Exception as e:
    # Catch any other unexpected errors
    print(f"\nAn unexpected error occurred: {e}")

```

## Input Data Schema

The `RelationshipScorer` class requires an input dictionary conforming to the `ScorerInputData` Pydantic model (`src/data_models/models.py`). Refer to `config/data_model_config.yaml` for a human-readable description and example structure.

**Key Requirements:**

* `relationship_mentions`: A non-empty list of mention dictionaries. Each mention needs:
    * `source_type`: A string matching a key in `config/scoring_config.yaml` -> `source_weights`.
    * `year`: An integer representing the publication/record year.
    * `sentiment`: A string (`"Positive"`, `"Negative"`, or `"Neutral"`). **Sentiment analysis must be performed externally before using this package.**
    * `mention_id` (Optional): A string identifier for traceability.
* `entity_a_metadata` / `entity_b_metadata`: Dictionaries containing:
    * `id`: A unique string identifier for the entity.
    * `overall_prominence`: A non-negative float score. **This score, representing the entity's general importance or frequency in the dataset, must be pre-calculated externally** and is crucial for normalization methods.

## Output Data Schema

The `get_all_scores()` method returns a dictionary conforming to the `ScorerOutputData` Pydantic model (`src/data_models/models.py`). See `config/data_model_config.yaml` for details.

* `evidence_strength` (float)
* `sentiment_scores` (dict): Contains `positive_score`, `negative_score`, `neutral_score`, `net_score`, `dominant_sentiment`.
* `trend_score` (float)

## Configuration

The scoring behavior is controlled via `config/scoring_config.yaml`. Key sections include:

* `source_weights`: Define the numerical weight/authority for each source type.
* `evidence_strength`: Configure `frequency_aggregation` (`Logarithmic` or `SimpleSum`) and `normalization_method` (`PMI-like`, `RelativeFrequency`, or `None`).
* `sentiment`: Configure `aggregation_method` (`NetScoreDetailed` is currently implemented).
* `trend`: Configure the calculation `method` (`RecencyWeighted`, `RateOfChange`, `EvidenceProgression`) and method-specific parameters (e.g., `decay_rate`).
* `logging`: Set the logging `level`, `format`, and optional `log_file` path.

The package automatically loads this configuration file upon `RelationshipScorer` initialization. The expected location is `config/scoring_config.yaml` relative to the package root. You might need a `MANIFEST.in` file if installing the package via `pip install .` to ensure non-code files like YAML configs are included.

**Example MANIFEST.in:**
```
recursive-include config *.yaml
```

## Testing

Unit tests should be placed in the `tests/` directory. Run tests using `pytest`:

1.  Install testing dependencies:
    ```bash
    pip install pytest pytest-cov # Add to requirements-dev.txt if used
    ```
2.  Run pytest from the package root directory:
    ```bash
    pytest tests/
    # Or with coverage:
    # pytest --cov=src tests/
    ```
*(Note: Test files were not generated in this session as requested, but this section outlines how to run them once created).*

---