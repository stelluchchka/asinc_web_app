# Start your image with a node base image
FROM python:3.8-slim

# The /app directory should act as the main application directory
WORKDIR /async_web_app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "server.py"]