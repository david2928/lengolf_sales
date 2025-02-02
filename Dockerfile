# Use Python 3.11 slim image
FROM python:3.11-slim

# Accept build arguments
ARG APP_LOGIN
ARG APP_PASSWORD
ARG GOOGLE_KEY

# Set environment variables
ENV APP_LOGIN=$APP_LOGIN
ENV APP_PASSWORD=$APP_PASSWORD
ENV GOOGLE_KEY=$GOOGLE_KEY

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-freefont-ttf \
    libxss1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY app/requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy the rest of the application
COPY . .

# Run the application
CMD ["python", "-m", "app.app"] 