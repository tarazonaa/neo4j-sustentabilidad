FROM python:3.12-bullseye

ADD requirements.txt .
RUN pip install -r requirements.txt

ADD app /app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]