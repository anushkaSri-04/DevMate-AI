
FROM python:3.11-slim

# Keep Python output visible and avoid unnecessary cache files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install project metadata and source code
COPY pyproject.toml ./
COPY src ./src

# Install DevMate AI and its dependencies
RUN pip install --no-cache-dir .

# Create the persistent ChromaDB directory
RUN mkdir -p /app/data/chroma

# FastAPI listens on port 8000
EXPOSE 8000

# Start the API server
CMD ["uvicorn", "devmate.api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
