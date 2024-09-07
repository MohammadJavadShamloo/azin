import logging

from django.conf import settings
from elasticsearch import Elasticsearch, helpers, ApiError

from storage.es_mappings import ES_SETTINGS

audit_logger = logging.getLogger('audit_logger')
error_logger = logging.getLogger('error_logger')


class ESFacade:
    def __init__(self):
        self.es_client = Elasticsearch(hosts=f"http://{settings.ES_HOST}:{settings.ES_PORT}")

    def create_index(self, index_name, es_mappings=None, es_settings=ES_SETTINGS):
        """Creates an Elasticsearch index with optional mappings and settings."""
        try:
            if not self.es_client.indices.exists(index=index_name):
                self.es_client.indices.create(index=index_name, body={
                    'mappings': es_mappings or {},
                    'settings': es_settings
                })
                audit_logger.info(f"Index {index_name} created successfully.")
            else:
                audit_logger.info(f"Index {index_name} already exists.")
        except ApiError as e:
            error_logger.error(f"Error creating index {index_name}: {str(e)}")
            raise

    def delete_index(self, index_name):
        """Deletes an Elasticsearch index."""
        try:
            if self.es_client.indices.exists(index=index_name):
                self.es_client.indices.delete(index=index_name)
                audit_logger.info(f"Index {index_name} deleted successfully.")
            else:
                audit_logger.info(f"Index {index_name} does not exist.")
        except ApiError as e:
            error_logger.error(f"Error deleting index {index_name}: {str(e)}")
            raise

    def index_document(self, index_name, doc_id, document):
        """Indexes a single document into the specified index."""
        try:
            self.es_client.index(index=index_name, id=doc_id, body=document)
            audit_logger.info(f"Document indexed in {index_name} successfully.")
        except ApiError as e:
            error_logger.error(f"Error indexing document in {index_name}: {str(e)}")
            raise

    def get_document(self, index_name, doc_id):
        """Retrieves a document by ID from the specified index."""
        try:
            response = self.es_client.get(index=index_name, id=doc_id)
            audit_logger.info(f"Document {doc_id} retrieved from {index_name} successfully.")
            return response['_source']
        except ApiError as e:
            error_logger.error(f"Error retrieving document {doc_id} from {index_name}: {str(e)}")
            raise

    def update_document(self, index_name, doc_id, update_fields):
        """Updates specific fields of a document in the specified index."""
        try:
            self.es_client.update(index=index_name, id=doc_id, body={'doc': update_fields})
            audit_logger.info(f"Document {doc_id} updated in {index_name} successfully.")
        except ApiError as e:
            error_logger.error(f"Error updating document {doc_id} in {index_name}: {str(e)}")
            raise

    def delete_document(self, index_name, doc_id):
        """Deletes a document by ID from the specified index."""
        try:
            self.es_client.delete(index=index_name, id=doc_id)
            audit_logger.info(f"Document {doc_id} deleted from {index_name} successfully.")
        except ApiError as e:
            error_logger.error(f"Error deleting document {doc_id} from {index_name}: {str(e)}")
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
            audit_logger.info(f"Bulk index operation completed successfully for index {index_name}.")
        except ApiError as e:
            error_logger.error(f"Error performing bulk index operation in {index_name}: {str(e)}")
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
            audit_logger.info(f"Bulk update operation completed successfully for index {index_name}.")
        except ApiError as e:
            error_logger.error(f"Error performing bulk update operation in {index_name}: {str(e)}")
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
            audit_logger.info(f"Bulk delete operation completed successfully for index {index_name}.")
        except ApiError as e:
            error_logger.error(f"Error performing bulk delete operation in {index_name}: {str(e)}")
            raise

    def refresh_index(self, index_name):
        """Refreshes an Elasticsearch index to make recent changes searchable."""
        try:
            self.es_client.indices.refresh(index=index_name)
            audit_logger.info(f"Index {index_name} refreshed successfully.")
        except ApiError as e:
            error_logger.error(f"Error refreshing index {index_name}: {str(e)}")
            raise
