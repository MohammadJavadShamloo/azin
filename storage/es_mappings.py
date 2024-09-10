AUDIT_LOG_MAPPING = {
    "properties": {
        "timestamp": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
        "user": {"type": "keyword"},
        "action": {"type": "keyword"},
        "resource": {"type": "keyword"},
        "message": {"type": "text"},
        "details": {"type": "object"}
    }
}

ERROR_LOG_MAPPING = {
    "properties": {
        "timestamp": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
        "level": {"type": "keyword"},
        "message": {"type": "text"},
        "exception": {"type": "text"},
        "stack_trace": {"type": "text"},
        "context": {"type": "object"}
    }
}

HASH_INDEX_MAPPING = {
    "properties": {
        "hash": {"type": "keyword", "index": True},
        "original_key": {"type": "text", "index": True},
        "user_id": {"type": "text", "index": True},
        "filename": {"type": "keyword", "index": True},
        "folder_path": {"type": "text"},
        "creation_date": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
        "size": {"type": "long"},
        "file_type": {"type": "keyword"}
    }
}

USER_USAGE_INDEX_MAPPING = {
    "properties": {
        "user_id": {"type": "keyword", "index": True},
        "bucket_name": {"type": "keyword", "index": True},
        "total_size": {"type": "long"},
        "file_count": {"type": "long"},
        "upload_count": {"type": "long"},
        "delete_count": {"type": "long"},
        "last_activity_date": {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
        "storage_limit": {"type": "long"}
    }
}

ES_SETTINGS = {
    "number_of_shards": 3,
    "number_of_replicas": 0
}
