import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from storage.report_utils import ReportFacade
from storage.s3_utils import S3Facade

audit_logger = logging.getLogger('audit_logger')
error_logger = logging.getLogger('error_logger')


@receiver(post_save, sender=User)
def create_bucket_and_usage_record_for_new_user(sender, instance, created, **kwargs):
    if created:
        s3_facade = S3Facade()
        report_facade = ReportFacade()
        bucket_name = f"user-{instance.username}-bucket"
        method_name = 'create_bucket_and_usage_record_for_new_user'

        try:
            # Create S3 bucket for user
            s3_facade.create_bucket_for_user(instance.username)
            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": instance.username,
                "action": "create_bucket",
                "resource": bucket_name,
                "message": f"Bucket {bucket_name} created successfully for user {instance.username}.",
                "details": {"bucket_name": bucket_name}
            })

            # Create Elasticsearch document for tracking user storage usage
            document = {
                "user_id": instance.username,
                "date_joined": instance.date_joined.isoformat(),
                "total_size": 0,
                "file_count": 0,
                "upload_count": 0,
                "delete_count": 0,
                "last_updated": int(datetime.now().timestamp() * 1000),
                "bucket_name": bucket_name,
            }

            report_facade.client.index(
                index=report_facade.user_usage_index,
                id=instance.username,
                document=document
            )

            audit_logger.info({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "user": instance.username,
                "action": "create_usage_record",
                "resource": report_facade.user_usage_index,
                "message": f"Usage record created for user {instance.username}.",
                "details": {"bucket_name": bucket_name}
            })

        except Exception as e:
            error_logger.error({
                "timestamp": int(datetime.now().timestamp() * 1000),
                "level": "ERROR",
                "message": f"Failed to complete setup for user {instance.username}: {str(e)}",
                "exception": str(e),
                "context": {
                    "user_id": instance.username,
                    "bucket_name": bucket_name,
                    "method": method_name
                }
            })
            raise
