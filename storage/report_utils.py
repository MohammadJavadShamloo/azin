import logging
from elasticsearch import Elasticsearch, ApiError
from django.conf import settings
from datetime import datetime

audit_logger = logging.getLogger('audit_logger')
error_logger = logging.getLogger('error_logger')


class ReportFacade:
    def __init__(self):
        audit_logger.info({
            "timestamp": int(datetime.now().timestamp() * 1000),
            "user": "system",
            "action": "init",
            "resource": "ReportFacade",
            "message": "Initializing ReportFacade",
            "details": {}
        })
        self.client = Elasticsearch(hosts=[f'http://{settings.ES_HOST}:{settings.ES_PORT}'])
        self.audit_log_index = settings.ES_AUDIT_LOG_INDEX
        self.error_log_index = settings.ES_ERROR_LOG_INDEX
        self.user_usage_index = settings.ES_USER_USAGE_INDEX

    def get_audit_logs(self):
        try:
            query = {
                "query": {"match_all": {}},
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": True
            }
            response = self.client.search(index=self.audit_log_index, body=query)
            total_logs = response['hits']['total']['value']
            response = self.client.search(index=self.audit_log_index, body=query, size=total_logs)
            logs = [hit['_source'] for hit in response['hits']['hits']]

            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "get_audit_logs",
                "resource": self.audit_log_index,
                "message": f"Retrieved {len(logs)} audit logs.",
                "details": {"total_logs": total_logs}
            })
            return logs
        except Exception as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error retrieving audit logs: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {}
            })
            raise Exception(f"Error retrieving audit logs: {str(e)}")

    def get_error_logs(self):
        try:
            query = {
                "query": {"match_all": {}},
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": True
            }
            response = self.client.search(index=self.error_log_index, body=query)
            total_logs = response['hits']['total']['value']
            response = self.client.search(index=self.error_log_index, body=query, size=total_logs)
            logs = [hit['_source'] for hit in response['hits']['hits']]

            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "get_error_logs",
                "resource": self.error_log_index,
                "message": f"Retrieved {len(logs)} error logs.",
                "details": {"total_logs": total_logs}
            })
            return logs
        except Exception as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error retrieving error logs: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {}
            })
            raise Exception(f"Error retrieving error logs: {str(e)}")

    def search_audit_logs(self, search_term):
        try:
            query = {
                "query": {
                    "multi_match": {
                        "query": search_term,
                        "fields": ["user", "action", "resource", "message", "details"]
                    }
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": True
            }
            response = self.client.search(index=self.audit_log_index, body=query)
            total_logs = response['hits']['total']['value']
            response = self.client.search(index=self.audit_log_index, body=query, size=total_logs)
            logs = [hit['_source'] for hit in response['hits']['hits']]

            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "search_audit_logs",
                "resource": self.audit_log_index,
                "message": f"Search for term '{search_term}' returned {len(logs)} audit logs.",
                "details": {"total_logs": total_logs, "search_term": search_term}
            })
            return logs
        except Exception as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error searching audit logs: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"search_term": search_term}
            })
            raise Exception(f"Error searching audit logs: {str(e)}")

    def search_error_logs(self, search_term):
        try:
            query = {
                "query": {
                    "multi_match": {
                        "query": search_term,
                        "fields": ["level", "message", "exception", "stack_trace", "context"]
                    }
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "track_total_hits": True
            }
            response = self.client.search(index=self.error_log_index, body=query)
            total_logs = response['hits']['total']['value']
            response = self.client.search(index=self.error_log_index, body=query, size=total_logs)
            logs = [hit['_source'] for hit in response['hits']['hits']]

            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "search_error_logs",
                "resource": self.error_log_index,
                "message": f"Search for term '{search_term}' returned {len(logs)} error logs.",
                "details": {"total_logs": total_logs, "search_term": search_term}
            })
            return logs
        except Exception as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error searching error logs: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"search_term": search_term}
            })
            raise Exception(f"Error searching error logs: {str(e)}")

    def get_user_usage(self, user_id):
        try:
            usage_data = self.client.get(index=self.user_usage_index, id=user_id)['_source']
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "get_user_usage",
                "resource": self.user_usage_index,
                "message": f"Retrieved usage data for user {user_id}.",
                "details": {"user_id": user_id}
            })
            return usage_data
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error retrieving usage data for user {user_id}: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {"user_id": user_id}
            })
            raise Exception(f"Error retrieving usage data for user {user_id}: {str(e)}")

    def get_all_users_usage(self):
        try:
            query = {
                "query": {"match_all": {}},
                "track_total_hits": True
            }
            response = self.client.search(index=self.user_usage_index, body=query)
            total_records = response['hits']['total']['value']
            response = self.client.search(index=self.user_usage_index, body=query, size=total_records)
            usage_data = [hit['_source'] for hit in response['hits']['hits']]

            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": "system",
                "action": "get_all_users_usage",
                "resource": self.user_usage_index,
                "message": f"Retrieved usage data for all users.",
                "details": {"total_users": len(usage_data)}
            })
            return usage_data
        except ApiError as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Error retrieving usage data for all users: {str(e)}",
                "exception": str(e),
                "stack_trace": None,
                "context": {}
            })
            raise Exception(f"Error retrieving usage data for all users: {str(e)}")
