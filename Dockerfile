FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 8080
EXPOSE 8080

# Command to run the application
CMD streamlit run main.py --server.port=8080 --server.enableCORS=false --server.enableXsrfProtection=false --server.address=0.0.0.0