import logging

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
        if not isinstance(record.msg, dict):
            return
        self.client.index(index=self.index_name, body=record.msg)


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
        if not isinstance(record.msg, dict):
            return
        self.client.index(index=self.index_name, body=record.msg)
