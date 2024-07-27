FROM python:3.9-slim

WORKDIR /async_web_app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["/async_web_app/entrypoint.sh"]
CMD ["python", "src/server.py"]
