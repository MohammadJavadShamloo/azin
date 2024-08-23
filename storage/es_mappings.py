AUDIT_LOG_MAPPING = {
    "properties": {
        "timestamp": {"type": "date"},
        "user": {"type": "keyword"},
        "action": {"type": "keyword"},
        "resource": {"type": "keyword"},
        "message": {"type": "text"},
        "details": {"type": "object"}
    }
}

ERROR_LOG_MAPPING = {
    "properties": {
        "timestamp": {"type": "date"},
        "level": {"type": "keyword"},
        "message": {"type": "text"},
        "exception": {"type": "text"},
        "stack_trace": {"type": "text"},
        "context": {"type": "object"}
    }
}

HASH_INDEX_MAPPING = {
    "properties": {
        "file_hash": {"type": "keyword"},
        "s3_object_name": {"type": "keyword"},
        "metadata": {"type": "object"},
        "timestamp": {"type": "date"}
    }
}

ES_SETTINGS = {
    "number_of_shards": 5,
    "number_of_replicas": 0
}
