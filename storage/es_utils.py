import logging
from django.conf import settings
from elasticsearch import Elasticsearch, helpers, ApiError
from storage.es_mappings import ES_SETTINGS
from datetime import datetime

audit_logger = logging.getLogger('audit_logger')
error_logger = logging.getLogger('error_logger')


class ESFacade:
    def __init__(self):
        audit_logger.info({
            "timestamp": int(datetime.now().timestamp() * 1000),
            "user": "system",
            "action": "init",
            "resource": "ESFacade",
            "message": "Initializing Elasticsearch client",
            "details": {}
        })
        self.es_client = Elasticsearch(hosts=f"http://{settings.ES_HOST}:{settings.ES_PORT}")

    def create_index(self, index_name, es_mappings=None, es_settings=ES_SETTINGS):
        """Creates an Elasticsearch index with optional mappings and settings."""
        try:
            if not self.es_client.indices.exists(index=index_name):
                self.es_client.indices.create(index=index_name, body={
                    'mappings': es_mappings or {},
                    'settings': es_settings
                })
                audit_logger.info({
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "user": "system",
                    "action": "create_index",
                    "resource": index_name,
                    "message": f"Index {index_name} created successfully.",
                    "details": es_mappings
                })
            else:
                audit_logger.info({
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "user": "system",
                    "action": "create_index",
                    "resource": index_name,
                    "message": f"Index {index_name} already exists.",
                    "details": {}
                })
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error creating index {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name}
            })
            raise

    def delete_index(self, index_name):
        """Deletes an Elasticsearch index."""
        try:
            if self.es_client.indices.exists(index=index_name):
                self.es_client.indices.delete(index=index_name)
                audit_logger.info({
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "user": "system",
                    "action": "delete_index",
                    "resource": index_name,
                    "message": f"Index {index_name} deleted successfully.",
                    "details": {}
                })
            else:
                audit_logger.info({
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "user": "system",
                    "action": "delete_index",
                    "resource": index_name,
                    "message": f"Index {index_name} does not exist.",
                    "details": {}
                })
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error deleting index {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name}
            })
            raise

    def index_document(self, index_name, doc_id, document):
        """Indexes a single document into the specified index."""
        try:
            self.es_client.index(index=index_name, id=doc_id, body=document)
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "index_document",
                "resource": index_name,
                "message": f"Document {doc_id} indexed successfully.",
                "details": {"doc_id": doc_id}
            })
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error indexing document in {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name, "doc_id": doc_id}
            })
            raise

    def get_document(self, index_name, doc_id):
        """Retrieves a document by ID from the specified index."""
        try:
            response = self.es_client.get(index=index_name, id=doc_id)
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "get_document",
                "resource": index_name,
                "message": f"Document {doc_id} retrieved successfully.",
                "details": {"doc_id": doc_id}
            })
            return response['_source']
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error retrieving document {doc_id} from {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name, "doc_id": doc_id}
            })
            raise

    def search_documents(self, index_name, user_id, search_term, fields=None):
        """Searches documents in the specified Elasticsearch index using the provided search term."""
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "user_id": user_id
                                }
                            },
                            {
                                "bool": {
                                    "should": [
                                        {
                                            "wildcard": {
                                                "filename": {
                                                    "value": f"*{search_term}*"
                                                }
                                            }
                                        },
                                        {
                                            "wildcard": {
                                                "file_type": {
                                                    "value": f"*{search_term}*"
                                                }
                                            }
                                        },
                                        {
                                            "wildcard": {
                                                "hash": {
                                                    "value": f"*{search_term}*"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
            response = self.es_client.search(index=index_name, body=query)
            query["size"] = response['hits']['total']['value']
            response = self.es_client.search(index=index_name, body=query)
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "search_documents",
                "resource": index_name,
                "message": f"Search executed on index {index_name} with term '{search_term}'.",
                "details": {"query": query}
            })
            return response['hits']['hits']
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error searching documents in {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name, "search_term": search_term}
            })
            raise

    def update_document(self, index_name, doc_id, update_fields):
        """Updates specific fields of a document in the specified index."""
        try:
            self.es_client.update(index=index_name, id=doc_id, body={'doc': update_fields})
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "update_document",
                "resource": index_name,
                "message": f"Document {doc_id} updated successfully.",
                "details": {"doc_id": doc_id, "update_fields": update_fields}
            })
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error updating document {doc_id} in {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name, "doc_id": doc_id}
            })
            raise

    def delete_document(self, index_name, doc_id):
        """Deletes a document by ID from the specified index."""
        try:
            self.es_client.delete(index=index_name, id=doc_id)
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "delete_document",
                "resource": index_name,
                "message": f"Document {doc_id} deleted successfully.",
                "details": {"doc_id": doc_id}
            })
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error deleting document {doc_id} from {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name, "doc_id": doc_id}
            })
            raise

    def bulk_index_documents(self, index_name, documents):
        """Performs a bulk index operation for multiple documents."""
        try:
            actions = [
                {
                    '_op_type': 'index',
                    '_index': index_name,
                    '_id': doc['id'],
                    '_source': doc['body']
                } for doc in documents
            ]
            helpers.bulk(self.es_client, actions)
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "bulk_index_documents",
                "resource": index_name,
                "message": f"Bulk index operation completed successfully for {index_name}.",
                "details": {"documents_count": len(documents)}
            })
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error performing bulk index operation in {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name}
            })
            raise

    def bulk_update_documents(self, index_name, documents):
        """Performs a bulk update operation for multiple documents."""
        try:
            actions = [
                {
                    '_op_type': 'update',
                    '_index': index_name,
                    '_id': doc['id'],
                    'doc': doc['body']
                } for doc in documents
            ]
            helpers.bulk(self.es_client, actions)
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "bulk_update_documents",
                "resource": index_name,
                "message": f"Bulk update operation completed successfully for {index_name}.",
                "details": {"documents_count": len(documents)}
            })
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error performing bulk update operation in {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name}
            })
            raise

    def bulk_delete_documents(self, index_name, doc_ids):
        """Performs a bulk delete operation for multiple documents."""
        try:
            actions = [
                {
                    '_op_type': 'delete',
                    '_index': index_name,
                    '_id': doc_id
                } for doc_id in doc_ids
            ]
            helpers.bulk(self.es_client, actions)
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "bulk_delete_documents",
                "resource": index_name,
                "message": f"Bulk delete operation completed successfully for {index_name}.",
                "details": {"documents_count": len(doc_ids)}
            })
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error performing bulk delete operation in {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name}
            })
            raise

    def refresh_index(self, index_name):
        """Refreshes an Elasticsearch index to make recent changes searchable."""
        try:
            self.es_client.indices.refresh(index=index_name)
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "refresh_index",
                "resource": index_name,
                "message": f"Index {index_name} refreshed successfully.",
                "details": {}
            })
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error refreshing index {index_name}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"index_name": index_name}
            })
            raise
