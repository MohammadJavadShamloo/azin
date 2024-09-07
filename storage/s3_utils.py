import boto3
from botocore.exceptions import ClientError, BotoCoreError
import logging
from django.conf import settings

from storage.error_map import ERROR_MAP, DEFAULT_ERROR_MESSAGE

audit_logger = logging.getLogger('audit_logger')
error_logger = logging.getLogger('error_logger')


class S3Facade:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY
        )

    def generate_bucket_name(self, user_id):
        """Generates a bucket name based on the user_id. This can be customized further if needed."""
        return f"user-{user_id}-bucket"

    def _convert_error_code_to_message(self, error):
        """Converts an AWS error code to a user-friendly error message."""
        try:
            error_code = error.response.get('Error', {}).get('Code', '')
            return ERROR_MAP.get(error_code, DEFAULT_ERROR_MESSAGE)
        except Exception:
            return str(error)

    def create_bucket_for_user(self, user_id):
        """Creates a bucket for a specific user if it does not already exist."""
        bucket_name = self.generate_bucket_name(user_id)
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
            audit_logger.info(f"Bucket {bucket_name} created for user {user_id}")
        except (ClientError, BotoCoreError, Exception) as e:
            error_message = self._convert_error_code_to_message(e)
            error_logger.error(f"Error creating bucket {bucket_name} for user {user_id}: {error_message}")
            raise Exception(error_message)

    def upload_file(self, user_id, file_path, file_content, metadata=None):
        """Uploads a file to the user's bucket. Metadata can be included."""
        bucket_name = self.generate_bucket_name(user_id)
        try:
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=file_path,
                Body=file_content,
                Metadata=metadata or {}
            )
            audit_logger.info(f"File {file_path} uploaded to bucket {bucket_name} for user {user_id}")
        except (ClientError, BotoCoreError, Exception) as e:
            error_message = self._convert_error_code_to_message(e)
            error_logger.error(f"Error uploading file {file_path} for user {user_id}: {error_message}")
            raise Exception(error_message)

    def create_folder(self, user_id, folder_path):
        """Creates a folder in the user's bucket. S3 does not have folders, so this creates an empty object with a '/' suffix."""
        bucket_name = self.generate_bucket_name(user_id)
        try:
            if not folder_path.endswith('/'):
                folder_path += '/'
            self.s3_client.put_object(Bucket=bucket_name, Key=folder_path)
            audit_logger.info(f"Folder {folder_path} created in bucket {bucket_name} for user {user_id}")
        except (ClientError, BotoCoreError, Exception) as e:
            error_message = self._convert_error_code_to_message(e)
            error_logger.error(f"Error creating folder {folder_path} for user {user_id}: {error_message}")
            raise Exception(error_message)

    def delete_object(self, user_id, file_path):
        """Deletes a file or folder from the user's bucket."""
        bucket_name = self.generate_bucket_name(user_id)
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=file_path)
            audit_logger.info(f"Object {file_path} deleted from bucket {bucket_name} for user {user_id}")
        except (ClientError, BotoCoreError, Exception) as e:
            error_message = self._convert_error_code_to_message(e)
            error_logger.error(f"Error deleting object {file_path} for user {user_id}: {error_message}")
            raise Exception(error_message)

    def list_folder_contents(self, user_id, folder_path='', only_name=False):
        """Lists the contents of a folder in the user's bucket."""
        bucket_name = self.generate_bucket_name(user_id)
        if folder_path != '' and not folder_path.endswith('/'):
            folder_path += '/'
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_path, Delimiter='/')
            contents = []
            for item in response.get('Contents', []):
                key = item['Key']
                if key != folder_path:
                    if only_name:
                        contents.append(key[len(folder_path):])
                    else:
                        contents.append({
                            'name': key[len(folder_path):],
                            'type': 'file',
                            'size': item.get('Size', 0)
                        })
            for prefix in response.get('CommonPrefixes', []):
                folder_name = prefix['Prefix'][len(folder_path):].rstrip('/')
                if only_name:
                    contents.append(prefix['Prefix'][len(folder_path):])
                else:
                    contents.append({
                        'name': folder_name,
                        'type': 'folder',
                        'size': 0
                    })
            audit_logger.info(f"Listed contents of folder {folder_path} in bucket {bucket_name} for user {user_id}")
            return contents
        except ClientError as e:
            error_logger.error(f"Error listing contents of folder {folder_path} for user {user_id}: {str(e)}")
            raise

    def get_object(self, user_id, file_path):
        """Retrieves a file from the user's bucket."""
        bucket_name = self.generate_bucket_name(user_id)
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_path)
            audit_logger.info(f"Object {file_path} retrieved from bucket {bucket_name} for user {user_id}")
            return response['Body'].read(), response.get('Metadata', {})
        except (ClientError, BotoCoreError) as e:
            error_message = self._convert_error_code_to_message(e)
            error_logger.error(f"Error retrieving object {file_path} for user {user_id}: {error_message}")
            raise Exception(error_message)

    def generate_download_link(self, user_id, file_path, expiration=3600):
        """Generates a presigned URL for downloading a file, valid for a specified expiration time."""
        bucket_name = self.generate_bucket_name(user_id)
        try:
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': file_path},
                ExpiresIn=expiration
            )
            audit_logger.info(f"Generated download link for {file_path} in bucket {bucket_name} for user {user_id}")
            return download_url
        except (ClientError, BotoCoreError) as e:
            error_message = self._convert_error_code_to_message(e)
            error_logger.error(
                f"Error generating download link for {file_path} in bucket {bucket_name}: {error_message}")
            raise Exception(error_message)
