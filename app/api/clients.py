from elasticsearch import Elasticsearch
from faststream.rabbit import RabbitBroker
from minio import Minio

from app.core.config import settings

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS,
    secret_key=settings.MINIO_SECRET,
    secure=settings.MINIO_SECURE,
)

es_client = Elasticsearch(settings.ES_LINK)

broker = RabbitBroker(settings.RABBITMQ_URL)
