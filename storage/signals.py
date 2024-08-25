import logging

from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from storage.s3_utils import S3Facade

audit_logger = logging.getLogger('audit')
error_logger = logging.getLogger('error_logger')


@receiver(user_signed_up)
def create_bucket_for_new_user(request, user, **kwargs):
    s3_facade = S3Facade()
    bucket_name = f"{user.username}"

    try:
        s3_facade.s3_client.create_bucket(Bucket=bucket_name)
        audit_logger.info(f"Bucket {bucket_name} created for user {user.username}")
    except Exception as e:
        error_logger.error(f"Failed to create bucket {bucket_name} for user {user.username}: {str(e)}")
