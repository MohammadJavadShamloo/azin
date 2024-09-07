from elasticsearch import Elasticsearch, ApiError
from django.conf import settings


class ReportFacade:
    def __init__(self):
        self.client = Elasticsearch(hosts=[f'http://{settings.ES_HOST}:{settings.ES_PORT}'])
        self.audit_log_index = settings.ES_AUDIT_LOG_INDEX
        self.error_log_index = settings.ES_ERROR_LOG_INDEX
        self.user_usage_index = settings.ES_USER_USAGE_INDEX

    def get_audit_logs(self, size=100, from_index=0):
        """
        Retrieve the latest audit logs from Elasticsearch.
        :param size: Number of log entries to retrieve.
        :param from_index: Start index for pagination.
        :return: List of audit log entries.
        """
        try:
            query = {
                "query": {
                    "match_all": {}
                },
                "sort": [
                    {"timestamp": {"order": "desc"}}
                ],
                "from": from_index,
                "size": size
            }
            response = self.client.search(index=self.audit_log_index, body=query)
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            raise Exception(f"Error retrieving audit logs: {str(e)}")

    def get_error_logs(self, size=100, from_index=0):
        """
        Retrieve the latest error logs from Elasticsearch.
        :param size: Number of log entries to retrieve.
        :param from_index: Start index for pagination.
        :return: List of error log entries.
        """
        try:
            query = {
                "query": {
                    "match_all": {}
                },
                "sort": [
                    {"timestamp": {"order": "desc"}}
                ],
                "from": from_index,
                "size": size
            }
            response = self.client.search(index=self.error_log_index, body=query)
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            raise Exception(f"Error retrieving error logs: {str(e)}")

    def search_audit_logs(self, search_term, size=100, from_index=0):
        """
        Search audit logs by a specific term.
        :param search_term: Term to search in the logs.
        :param size: Number of log entries to retrieve.
        :param from_index: Start index for pagination.
        :return: List of matching audit log entries.
        """
        try:
            query = {
                "query": {
                    "multi_match": {
                        "query": search_term,
                        "fields": ["user", "action", "resource", "message", "details"]
                    }
                },
                "sort": [
                    {"timestamp": {"order": "desc"}}
                ],
                "from": from_index,
                "size": size
            }
            response = self.client.search(index=self.audit_log_index, body=query)
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            raise Exception(f"Error searching audit logs: {str(e)}")

    def search_error_logs(self, search_term, size=100, from_index=0):
        """
        Search error logs by a specific term.
        :param search_term: Term to search in the logs.
        :param size: Number of log entries to retrieve.
        :param from_index: Start index for pagination.
        :return: List of matching error log entries.
        """
        try:
            query = {
                "query": {
                    "multi_match": {
                        "query": search_term,
                        "fields": ["level", "message", "exception", "stack_trace", "context"]
                    }
                },
                "sort": [
                    {"timestamp": {"order": "desc"}}
                ],
                "from": from_index,
                "size": size
            }
            response = self.client.search(index=self.error_log_index, body=query)
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            raise Exception(f"Error searching error logs: {str(e)}")

    def get_user_usage(self, user_id):
        """Retrieve storage usage details for a specific user."""
        try:
            return self.client.get(index=self.user_usage_index, id=user_id)['_source']
        except ApiError as e:
            raise Exception(f"Error retrieving usage data for user {user_id}: {str(e)}")

    def get_all_users_usage(self):
        """Retrieve storage usage details for all users."""
        try:
            es_query = {
                "query": {
                    "match_all": {}
                }
            }
            response = self.client.search(index=self.user_usage_index, body=es_query)
            return [hit['_source'] for hit in response['hits']['hits']]
        except ApiError as e:
            raise Exception(f"Error retrieving usage data for all users: {str(e)}")