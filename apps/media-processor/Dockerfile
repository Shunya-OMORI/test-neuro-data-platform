# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install poetry for dependency management
RUN pip install poetry

# Copy only the dependency definition files to leverage Docker's build cache
COPY pyproject.toml poetry.lock* ./

# Install project dependencies into the system's site-packages
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

# Copy the application's source code into the container
COPY ./src ./src

# The command to run when the container starts
CMD ["python", "src/main.py"]
