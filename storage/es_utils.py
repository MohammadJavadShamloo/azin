import logging
from elasticsearch import Elasticsearch, NotFoundError, ApiError
from django.conf import settings
from es_mappings import ES_SETTINGS

audit_logger = logging.getLogger('audit')
error_logger = logging.getLogger('error_logger')


class ElasticsearchFacade:
    def __init__(self):
        try:
            self.es_client = Elasticsearch(hosts=settings.ES_HOST)
            audit_logger.info("Initialized Elasticsearch client.")
        except ApiError as e:
            error_logger.error(f"Failed to initialize Elasticsearch client: {str(e)}")
            raise

    def create_index(self, index_name, es_settings=ES_SETTINGS, es_mappings=None):
        """Create an index in Elasticsearch."""
        try:
            body = {'settings': es_settings}
            if es_mappings:
                body['mappings'] = es_mappings

            response = self.es_client.indices.create(index=index_name, body=body)
            audit_logger.info(f"Index '{index_name}' created with settings: {es_settings}, mappings: {es_mappings}")
            return response
        except ApiError as e:
            error_logger.error(f"Failed to create index '{index_name}': {str(e)}")
            raise

    def index_document(self, index_name, document, doc_id=None):
        """Index a document in Elasticsearch."""
        try:
            response = self.es_client.index(index=index_name, id=doc_id, body=document)
            audit_logger.info(f"Document indexed in '{index_name}' with ID: {doc_id}")
            return response
        except ApiError as e:
            error_logger.error(f"Failed to index document in '{index_name}' with ID {doc_id}: {str(e)}")
            raise

    def get_document(self, index_name, doc_id):
        """Retrieve a document from Elasticsearch by ID."""
        try:
            response = self.es_client.get(index=index_name, id=doc_id)
            audit_logger.info(f"Document retrieved from '{index_name}' with ID: {doc_id}")
            return response
        except NotFoundError:
            error_logger.error(f"Document not found in '{index_name}' with ID: {doc_id}")
            return None
        except ApiError as e:
            error_logger.error(f"Failed to retrieve document from '{index_name}' with ID {doc_id}: {str(e)}")
            raise

    def search(self, index_name, query, size=10):
        """Search for documents in an index."""
        try:
            response = self.es_client.search(index=index_name, body=query, size=size)
            audit_logger.info(f"Search performed on index '{index_name}' with query: {query}")
            return response
        except ApiError as e:
            error_logger.error(f"Failed to perform search on index '{index_name}': {str(e)}")
            raise

    def delete_document(self, index_name, doc_id):
        """Delete a document from Elasticsearch by ID."""
        try:
            response = self.es_client.delete(index=index_name, id=doc_id)
            audit_logger.info(f"Document with ID {doc_id} deleted from index '{index_name}'")
            return response
        except NotFoundError:
            error_logger.error(f"Document not found in '{index_name}' with ID: {doc_id}")
            return None
        except ApiError as e:
            error_logger.error(f"Failed to delete document from '{index_name}' with ID {doc_id}: {str(e)}")
            raise

    def delete_index(self, index_name):
        """Delete an index from Elasticsearch."""
        try:
            response = self.es_client.indices.delete(index=index_name, ignore=[400, 404])
            audit_logger.info(f"Index '{index_name}' deleted.")
            return response
        except ApiError as e:
            error_logger.error(f"Failed to delete index '{index_name}': {str(e)}")
            raise

    def update_document(self, index_name, doc_id, update_body):
        """Update a document in Elasticsearch."""
        try:
            response = self.es_client.update(index=index_name, id=doc_id, body={"doc": update_body})
            audit_logger.info(f"Document with ID {doc_id} updated in index '{index_name}'")
            return response
        except ApiError as e:
            error_logger.error(f"Failed to update document in '{index_name}' with ID {doc_id}: {str(e)}")
            raise

    def bulk_index(self, index_name, documents):
        """Bulk index multiple documents into Elasticsearch."""
        try:
            actions = []
            for document in documents:
                action = {
                    "_op_type": "index",
                    "_index": index_name,
                    "_id": document.get('_id'),
                    "_source": document.get('doc')
                }
                actions.append(action)
            response = self.es_client.bulk(body=actions)
            audit_logger.info(f"Bulk indexed documents into index '{index_name}'")
            return response
        except ApiError as e:
            error_logger.error(f"Failed to bulk index documents into '{index_name}': {str(e)}")
            raise

    def refresh_index(self, index_name):
        """Refresh an index in Elasticsearch."""
        try:
            response = self.es_client.indices.refresh(index=index_name)
            audit_logger.info(f"Index '{index_name}' refreshed.")
            return response
        except ApiError as e:
            error_logger.error(f"Failed to refresh index '{index_name}': {str(e)}")
            raise
