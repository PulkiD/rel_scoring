# Dockerfile for the relationship_scorer_package

# Use an official Python runtime as a parent image
# Choose a version compatible with your dependencies (e.g., 3.8, 3.9, 3.10, 3.11)
FROM python:3.10-slim AS builder

# Set environment variables to prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install build dependencies if any of your Python packages have C extensions
# RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*

# --- Dependency Installation Stage ---
# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# Create a virtual environment within the builder stage (optional but good practice)
# RUN python -m venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies into the virtual environment or directly
# Using wheels speeds up installation in the final stage
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# --- Final Application Stage ---
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Set environment variables (repeat for final stage)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy installed wheels from builder stage
COPY --from=builder /app/wheels /wheels

# Install dependencies from wheels using the wheels directory
# --no-index prevents pip from looking online, ensuring only our wheels are used
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*

# Copy the application source code and necessary configuration
COPY setup.py .
COPY src/ src/
COPY config/ config/
# If using MANIFEST.in for package_data, copy it too
# COPY MANIFEST.in .

# Install the application package itself using the copied source
# Use -e for editable mode if useful for debugging inside the container,
# otherwise a standard install is fine.
RUN pip install --no-cache-dir -e .
# If not using editable mode: RUN pip install --no-cache-dir .

# --- Runtime ---
# Set the default command to execute when the container starts.
# This should be tailored to how your package is intended to be used.
# Example: If you create a command-line script entry point in setup.py:
# CMD ["score-relationship", "--input", "data.json"]
# Example: Run a specific Python script that uses the library:
# COPY your_script.py .
# CMD ["python", "your_script.py"]
# For now, just start an interactive Python session:
CMD ["python"]

# Expose any ports if your application runs a web service (unlikely for this library)
# EXPOSE 8000
