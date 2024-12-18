FROM python:3.9-slim-bullseye

# Install Chromium and dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Verify installations
RUN python3 --version && chromium --version
# Verify Chrome installation
RUN chromium --version

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 27017

CMD ["python", "app.py"]
