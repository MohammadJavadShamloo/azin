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
def create_bucket_and_usage_record_for_new_user(sender, instance, **kwargs):
    s3_facade = S3Facade()
    report_facade = ReportFacade()
    bucket_name = f"{instance.username}"

    try:
        s3_facade.create_bucket_for_user(bucket_name)
        audit_logger.info(f"Bucket {bucket_name} created for user {instance.username}")

        document = {
            "user_id": instance.username,
            "email": instance.email,
            "date_joined": instance.date_joined.isoformat(),
            "total_size": 0,
            "file_count": 0,
            "last_login": instance.last_login.isoformat() if instance.last_login else None,
            "last_updated": datetime.now().isoformat(),
            "bucket_name": bucket_name
        }

        report_facade.client.index(
            index=report_facade.user_usage_index,
            id=instance.username,
            document=document
        )
        audit_logger.info(f"Usage record created for user {instance.username} in Elasticsearch with document: {document}")
    except Exception as e:
        error_logger.error(f"Failed to complete setup for user {instance.username}: {str(e)}")
