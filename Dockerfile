FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pyproject.toml main.py ./
COPY src ./src
COPY build/synthetic-data ./build/synthetic-data
ENV PYTHONPATH=/app/src
EXPOSE 8080
CMD ["python", "main.py"]
