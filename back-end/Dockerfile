FROM python:3-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt

COPY output.csv .
COPY api.py .
COPY main.py .

EXPOSE 5000

CMD ["python", "api.py"]
