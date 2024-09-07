import logging
from datetime import datetime

from elasticsearch import Elasticsearch

from azin.settings import ES_HOST, ES_PORT
from storage.es_mappings import AUDIT_LOG_MAPPING, ERROR_LOG_MAPPING


class AuditLogElasticsearchHandler(logging.Handler):
    def __init__(
            self,
            hosts=f'http://{ES_HOST}:{ES_PORT}',
            index_name='audit-logs',
            mapping=AUDIT_LOG_MAPPING
    ):
        logging.Handler.__init__(self)
        self.client = Elasticsearch(hosts=hosts)
        self.index_name = index_name
        self.mapping = mapping
        self.ensure_index()

    def ensure_index(self):
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(index=self.index_name, body={"mappings": self.mapping})

    def emit(self, record):
        log_entry = self.format(record)
        doc = {
            "timestamp": datetime.now().timestamp(),
            "user": getattr(record, "user", None),
            "action": getattr(record, "action", None),
            "resource": getattr(record, "resource", None),
            "message": record.getMessage(),
            "details": getattr(record, "details", None)
        }
        self.client.index(index=self.index_name, body=doc)


class ErrorLogElasticsearchHandler(logging.Handler):
    def __init__(
            self,
            hosts=f'http://{ES_HOST}:{ES_PORT}',
            index_name='error-logs',
            mapping=ERROR_LOG_MAPPING
    ):
        logging.Handler.__init__(self)
        self.client = Elasticsearch(hosts=hosts)
        self.index_name = index_name
        self.mapping = mapping
        self.ensure_index()

    def ensure_index(self):
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(index=self.index_name, body={"mappings": self.mapping})

    def emit(self, record):
        log_entry = self.format(record)
        doc = {
            "timestamp": datetime.now().timestamp(),
            "level": record.levelname,
            "message": record.getMessage(),
            "exception": getattr(record, "exception", None),
            "stack_trace": getattr(record, "stack_trace", None),
            "context": getattr(record, "context", None)
        }
        self.client.index(index=self.index_name, body=doc)
