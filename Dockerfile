FROM python:3.10

# install chromium
RUN apt update && apt install -y --no-install-recommends chromium chromium-driver
RUN apt autoclean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application files
COPY . /app

WORKDIR /app

# Set the display for headless Chrome
ENV DISPLAY=:99
