FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy app source files (excluding the database)
COPY requirements.txt .
COPY app.py .
COPY templates/ ./templates/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Environment variable:
# - DB_PATH: path to SQLite DB (mounted volume at runtime)
# - FLASK_SKIP_BROWSER: disables browser auto-launch inside container
ENV DB_PATH=/data/investments.sqlite3
ENV FLASK_SKIP_BROWSER=1

# Run the app
CMD ["python", "app.py"]
