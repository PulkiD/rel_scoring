# src/exceptions.py
# Custom exception classes for the relationship scorer package.

class RelationshipScorerError(Exception):
    """Base class for exceptions in this package."""
    pass

class ScoringInitializationError(RelationshipScorerError):
    """Exception raised for errors during RelationshipScorer initialization."""
    def __init__(self, message="Failed to initialize RelationshipScorer"):
        self.message = message
        super().__init__(self.message)

class ConfigurationError(RelationshipScorerError):
    """Exception raised for errors related to configuration loading or validation."""
    def __init__(self, message="Configuration error"):
        self.message = message
        super().__init__(self.message)

class CalculationError(RelationshipScorerError):
    """Exception raised for errors during score calculation."""
    def __init__(self, message="Error during score calculation"):
        self.message = message
        super().__init__(self.message)

class InputValidationError(ScoringInitializationError):
    """Specific exception for Pydantic input validation errors."""
    def __init__(self, pydantic_error):
        self.message = f"Input data validation failed: {pydantic_error}"
        self.details = pydantic_error.errors() # Store detailed Pydantic errors
        super().__init__(self.message)

class OutputValidationError(CalculationError):
    """Specific exception for Pydantic output validation errors."""
    def __init__(self, pydantic_error):
        self.message = f"Output data validation failed: {pydantic_error}"
        self.details = pydantic_error.errors() # Store detailed Pydantic errors
        super().__init__(self.message)

