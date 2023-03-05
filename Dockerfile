FROM python:3.11-alpine
RUN apk add build-base
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY hydra_engine hydra_engine
CMD python -m hydra_engine
