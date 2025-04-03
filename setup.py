# setup.py
# Setup script for the relationship_scorer_package

import setuptools
import os

def get_long_description():
    """Reads the README.md file for the long description."""
    # Ensure the path is correct relative to setup.py
    readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
    try:
        with open(readme_path, "r", encoding="utf-8") as fh:
            long_description = fh.read()
        return long_description
    except FileNotFoundError:
        print("Warning: README.md not found. Long description will be empty.")
        return ""


def get_requirements():
    """Reads the requirements.txt file for package dependencies."""
    req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    try:
        with open(req_path, "r", encoding="utf-8") as f:
            requirements = f.read().splitlines()
            # Filter out comments and empty lines
            requirements = [req for req in requirements if req and not req.startswith('#')]
        return requirements
    except FileNotFoundError:
        print("Warning: requirements.txt not found. Dependencies will be empty.")
        return []

# Package metadata
PACKAGE_NAME = "relationship_scorer" # How the package will be named on PyPI/install
VERSION = "0.1.0" # Initial version - consider tools like setuptools_scm for auto-versioning
AUTHOR = "Your Name / Organization" # Replace with actual author
EMAIL = "your.email@example.com" # Replace with actual email
DESCRIPTION = "A Python package to calculate ensemble scores for entity relationships."
URL = "https://github.com/your_username/relationship_scorer_package" # Replace with actual URL

setuptools.setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION,
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url=URL,
    project_urls={ # Optional: Add relevant links
        "Bug Tracker": f"{URL}/issues",
        "Source Code": URL,
    },
    # Specify where the actual Python package code is located
    package_dir={"": "src"}, # Tells setuptools that packages are under the 'src' directory
    # Automatically find packages under the 'src' directory
    packages=setuptools.find_packages(where="src"),

    # Include non-code files found in the package directories
    # Using include_package_data=True relies on MANIFEST.in for files outside package dirs
    # or for fine-grained control.
    include_package_data=True,
    # If config files were *inside* src/relationship_scorer/, you could use package_data:
    # package_data={
    #     'relationship_scorer': ['config/*.yaml'],
    # },
    # For config files outside 'src', MANIFEST.in is the standard way.
    # Create a MANIFEST.in file in the root with:
    # recursive-include config *.yaml

    # Define dependencies
    install_requires=get_requirements(),
    # Classifiers help users find your project
    classifiers=[
        "Development Status :: 3 - Alpha", # Change as appropriate (3 - Alpha, 4 - Beta, 5 - Production/Stable)
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License", # Choose your license (e.g., Apache Software License, BSD License)
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Typing :: Typed", # Indicate that the package uses type hints
    ],
    python_requires='>=3.8', # Specify minimum Python version compatible with your code
    # Entry points for command-line scripts (if any)
    # entry_points={
    #     'console_scripts': [
    #         'score-relationship=relationship_scorer.cli:main', # Example if you add a CLI module
    #     ],
    # },
)
