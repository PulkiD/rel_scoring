# src/utils/logger.py
# Singleton Logger implementation for consistent logging across the package.

import logging
import sys
import os
from .config_loader import load_config # Use config loader to get logging settings

# --- Singleton Metaclass ---
class SingletonType(type):
    """ Metaclass to ensure only one instance of the Logger exists. """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonType, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

# --- Logger Class ---
class Logger(metaclass=SingletonType):
    """
    Singleton Logger class.
    Configures logging based on settings in scoring_config.yaml.
    """
    _logger = None

    def __init__(self):
        """ Initializes the logger instance and configures it. """
        if self._logger is None: # Ensure setup runs only once
            try:
                # Load logging configuration specifically
                config = load_config().get('logging', {})
                log_level_str = config.get('level', 'INFO').upper()
                log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                log_file = config.get('log_file', None) # Path relative to project root or absolute

                # Get numeric log level
                log_level = getattr(logging, log_level_str, logging.INFO)

                # --- Basic Configuration ---
                # Use basicConfig initially to set the root logger level and format
                # If handlers are added later, they will inherit this level unless overridden
                logging.basicConfig(level=log_level, format=log_format)

                # --- Get Specific Logger ---
                # Get a logger instance specific to this package/module if desired
                # Using __name__ might result in multiple logger names (e.g., utils.logger, main_scorer)
                # Using a fixed name ensures consistency if preferred
                self._logger = logging.getLogger("RelationshipScorerPackage")
                self._logger.setLevel(log_level) # Ensure this specific logger respects the level

                # --- Prevent Duplicate Handlers ---
                # Check if handlers already exist to avoid duplication if init is called multiple times (though Singleton should prevent this)
                if not self._logger.handlers:
                    # --- Console Handler ---
                    # basicConfig adds a StreamHandler by default, but we might want more control
                    # Let's remove default handlers if any were added by basicConfig to the root logger
                    # and add our own controlled handler to our specific logger.
                    # Note: Modifying root logger handlers can affect other libraries if not careful.
                    # It might be safer to just configure *our* logger's handlers.
                    for handler in logging.root.handlers[:]:
                         logging.root.removeHandler(handler)

                    # Add a console handler to our specific logger
                    console_handler = logging.StreamHandler(sys.stdout)
                    console_handler.setLevel(log_level)
                    formatter = logging.Formatter(log_format)
                    console_handler.setFormatter(formatter)
                    self._logger.addHandler(console_handler)

                    # --- File Handler (Optional) ---
                    if log_file:
                        try:
                            # Ensure log directory exists if log_file path includes directories
                            log_dir = os.path.dirname(log_file)
                            if log_dir and not os.path.exists(log_dir):
                                os.makedirs(log_dir)

                            file_handler = logging.FileHandler(log_file, mode='a') # Append mode
                            file_handler.setLevel(log_level)
                            file_handler.setFormatter(formatter)
                            self._logger.addHandler(file_handler)
                            self._logger.info(f"Logging initialized. Level: {log_level_str}. Outputting to console and file: {log_file}")
                        except Exception as e:
                            self._logger.error(f"Failed to configure file handler for {log_file}: {e}", exc_info=True)
                            self._logger.info(f"Logging initialized. Level: {log_level_str}. Outputting to console only.")
                    else:
                         self._logger.info(f"Logging initialized. Level: {log_level_str}. Outputting to console only.")

                # --- Prevent Propagation (Optional) ---
                # Set propagate to False if you don't want messages handled by this logger
                # to be passed up to the root logger (e.g., if root is configured differently)
                self._logger.propagate = False

            except Exception as e:
                # Fallback basic configuration if config loading fails
                logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
                self._logger = logging.getLogger("RelationshipScorerPackage_Fallback")
                self._logger.error(f"Failed to configure logger from config file: {e}. Using basic INFO level logging to console.", exc_info=True)


    def get_logger(self):
        """ Returns the configured logger instance. """
        if self._logger is None:
             # This should ideally not happen due to Singleton logic, but as a safeguard:
             self.__init__() # Try to initialize if not already done
        return self._logger

# --- Global Access Function ---
def get_logger():
    """ Public function to access the singleton logger instance. """
    return Logger().get_logger()

