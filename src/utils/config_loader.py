# src/utils/config_loader.py
# Utility function to load configuration from the YAML file.

import yaml
import os
from ..exceptions import ConfigurationError # Use custom exception

# Define the expected path to the config file relative to this file's location
# Go up two levels (from utils -> src -> root) then into config/
_CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config'))
_DEFAULT_CONFIG_PATH = os.path.join(_CONFIG_DIR, 'scoring_config.yaml')

# --- Cached Configuration ---
# Cache the loaded configuration to avoid repeated file reads
_cached_config = None

def load_config(config_path: str = None) -> dict:
    """
    Loads the scoring configuration from a YAML file.

    Uses a cached version after the first load unless a specific path is provided.

    Args:
        config_path (str, optional): Absolute path to the configuration file.
                                     If None, uses the default path within the package.
                                     Defaults to None.

    Returns:
        dict: The loaded configuration dictionary.

    Raises:
        ConfigurationError: If the config file cannot be found or parsed.
    """
    global _cached_config

    # Use default path if none provided
    path_to_load = config_path if config_path else _DEFAULT_CONFIG_PATH

    # If a specific path is given, don't use cache for that call
    # If default path is used and cache exists, return cache
    if config_path is None and _cached_config is not None:
        return _cached_config

    # --- File Loading ---
    try:
        # Check if the determined path exists
        if not os.path.exists(path_to_load):
             # Try to provide a helpful error message about where it looked
             cwd = os.getcwd()
             raise ConfigurationError(f"Configuration file not found at '{path_to_load}'. Current working directory: '{cwd}'. Ensure the config file exists relative to the package structure or provide an absolute path.")

        # Open and parse the YAML file
        with open(path_to_load, 'r') as stream:
            config_data = yaml.safe_load(stream)
            if not isinstance(config_data, dict):
                 raise ConfigurationError(f"Configuration file '{path_to_load}' does not contain a valid YAML dictionary.")

            # --- Cache the result if default path was used ---
            if config_path is None:
                 _cached_config = config_data

            return config_data

    except yaml.YAMLError as e:
        raise ConfigurationError(f"Error parsing configuration file '{path_to_load}': {e}")
    except FileNotFoundError:
        # This might be redundant due to the os.path.exists check, but good practice
         raise ConfigurationError(f"Configuration file not found at '{path_to_load}'.")
    except Exception as e:
        # Catch other potential errors during file access or loading
        raise ConfigurationError(f"An unexpected error occurred while loading configuration from '{path_to_load}': {e}")

def get_config_value(key_path: str, default: any = None):
    """
    Retrieves a specific value from the loaded configuration using a dot-separated key path.

    Example: get_config_value("evidence_strength.normalization_method")

    Args:
        key_path (str): Dot-separated path to the desired key (e.g., "logging.level").
        default (any, optional): Default value to return if the key is not found. Defaults to None.

    Returns:
        any: The configuration value or the default value.

    Raises:
        ConfigurationError: If the configuration hasn't been loaded yet or is invalid.
    """
    config = load_config() # Ensures config is loaded (uses cache if available)
    if not config:
         raise ConfigurationError("Configuration could not be loaded.")

    keys = key_path.split('.')
    value = config
    try:
        for key in keys:
            if isinstance(value, dict):
                 value = value[key]
            else:
                 # If we encounter a non-dict structure while traversing, the path is invalid
                 return default
        return value
    except KeyError:
        # Key not found at some level of the path
        return default
    except Exception as e:
         # Handle unexpected errors during traversal
         logger = get_logger() # Assuming logger is available or can be imported safely here
         logger.warning(f"Error accessing config key '{key_path}': {e}. Returning default.")
         return default

