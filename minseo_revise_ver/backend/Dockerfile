# 1. Base Image
FROM python:3.11-slim

# 2. Set Environment Variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set Work Directory
WORKDIR /app

# 4. Install uv
RUN pip install uv

# 5. Install Dependencies
COPY requirements.txt /app/
RUN uv pip install --no-cache-dir --system -r /app/requirements.txt

# 6. Copy Application Code
COPY . /app

# 7. Expose Port
EXPOSE 8000

# 8. Run Application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]