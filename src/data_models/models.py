from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Literal, Optional


ALLOWED_SENTIMENTS = Literal["Positive", "Negative", "Neutral"]
ALLOWED_SOURCE_TYPES = Literal[
    "Guideline", "Label", "Phase 4 CT", "Phase 3 CT", "Phase 2 CT",
    "Phase 1 CT", "PubMed", "Preclinical", "Review", "Conference Abstract", "Other" # Added more examples
]
ALLOWED_DOMINANT_SENTIMENTS = Literal["Positive", "Negative", "Neutral", "Mixed"]

# --- Input Models ---

class MentionItem(BaseModel):
    """ Defines the structure for a single relationship mention. """
    source_type: ALLOWED_SOURCE_TYPES = Field(..., description="Type of the source document")
    year: int = Field(..., gt=1900, lt=2100, description="Year the mention was recorded/published (within reasonable range)")
    sentiment: ALLOWED_SENTIMENTS = Field(..., description="Pre-calculated sentiment")
    mention_id: Optional[str] = Field(None, description="Optional source-specific identifier for traceability", examples=["pmid:12345678", "NCT00001234"])

    model_config = ConfigDict(extra='forbid') 

class EntityMetadata(BaseModel):
    """ Defines the structure for metadata associated with each entity. """
    id: str = Field(..., min_length=1, description="Unique identifier for the entity")
    overall_prominence: float = Field(..., ge=0.0, description="Pre-calculated prominence score (e.g., weighted frequency) for normalization")

    model_config = ConfigDict(extra='forbid') 

class ScorerInputData(BaseModel):
    """ Pydantic model for validating the entire input dictionary to RelationshipScorer. """
    relationship_mentions: List[MentionItem] = Field(..., min_length=1, description="List of mentions for the relationship (at least one required)")
    entity_a_metadata: EntityMetadata = Field(..., description="Metadata for Entity A")
    entity_b_metadata: EntityMetadata = Field(..., description="Metadata for Entity B")

    model_config = ConfigDict(extra='forbid') 

class SentimentScoresOutput(BaseModel):
    """ Defines the structure for the detailed sentiment score output. """
    positive_score: float = Field(..., ge=0.0, description="Weighted score sum for positive mentions")
    negative_score: float = Field(..., ge=0.0, description="Weighted score sum for negative mentions")
    neutral_score: float = Field(..., ge=0.0, description="Weighted score sum for neutral mentions")
    net_score: float = Field(..., description="Calculated net score (e.g., positive - negative)")
    dominant_sentiment: ALLOWED_DOMINANT_SENTIMENTS = Field(..., description="Overall dominant sentiment category")

    model_config = ConfigDict(extra='forbid')

class ScorerOutputData(BaseModel):
    """ Pydantic model for validating the final output dictionary from get_all_scores. """
    evidence_strength: float = Field(..., description="Calculated normalized, weighted evidence score")
    sentiment_scores: SentimentScoresOutput = Field(..., description="Detailed sentiment breakdown")
    trend_score: float = Field(..., description="Calculated score reflecting dynamics")

    model_config = ConfigDict(extra='forbid') 

