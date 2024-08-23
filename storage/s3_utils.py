import logging

from botocore.exceptions import BotoCoreError, ClientError

from storage import boto_client
from storage.error_map import ERROR_MAP, DEFAULT_ERROR_MESSAGE

audit_logger = logging.getLogger('audit')
error_logger = logging.getLogger('error_logger')


class S3Facade:
    def __init__(self):
        try:
            self.s3_client = boto_client
            audit_logger.info(f"Initialized S3 client")
        except BotoCoreError as e:
            error_logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise

    @staticmethod
    def get_error_message(error_code):
        """Retrieve error message from error map based on the error code."""
        return ERROR_MAP.get(error_code, DEFAULT_ERROR_MESSAGE)

    def upload_file(self, bucket_name, file_name, object_name=None):
        """Upload a file to the bucket."""
        try:
            if object_name is None:
                object_name = file_name
            self.s3_client.upload_file(file_name, bucket_name, object_name)
            audit_logger.info(f"File uploaded to {bucket_name}/{object_name}")
            return f"{bucket_name}/{object_name}"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = S3Facade.get_error_message(error_code)
            error_logger.error(f"Failed to upload file {file_name} to bucket {bucket_name}: {error_message} "
                               f"(Error Code: {error_code})")
            raise Exception(f"Failed to upload file '{file_name}' to S3. {error_message}")
        except BotoCoreError as e:
            error_logger.error(f"Failed to upload file {file_name} to bucket {bucket_name}: {str(e)}")
            raise

    def download_file(self, bucket_name, object_name, file_name=None):
        """Download a file from the bucket."""
        try:
            if file_name is None:
                file_name = object_name
            self.s3_client.download_file(bucket_name, object_name, file_name)
            audit_logger.info(f"File downloaded from {bucket_name}/{object_name}")
            return file_name
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = S3Facade.get_error_message(error_code)
            error_logger.error(f"Failed to download file {object_name} from bucket {bucket_name}: {error_message} "
                               f"(Error Code: {error_code})")
            raise Exception(f"Failed to download file '{object_name}' from S3. {error_message}")
        except BotoCoreError as e:
            error_logger.error(f"Failed to download file {object_name} from bucket {bucket_name}: {str(e)}")
            raise

    def list_files(self, bucket_name, prefix=None):
        """List files in the bucket."""
        try:
            kwargs = {'Bucket': bucket_name}
            if prefix:
                kwargs['Prefix'] = prefix

            response = self.s3_client.list_objects_v2(**kwargs)
            file_list = [item['Key'] for item in response.get('Contents', [])]
            audit_logger.info(f"Files listed in bucket {bucket_name} with prefix {prefix}: {file_list}")
            return file_list
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = S3Facade.get_error_message(error_code)
            error_logger.error(
                f"Failed to list files in bucket {bucket_name} with prefix {prefix}: {error_message} "
                f"(Error Code: {error_code})")
            raise Exception(f"Failed to list files in S3 with prefix '{prefix}'. {error_message}")
        except BotoCoreError as e:
            error_logger.error(f"Failed to list files in bucket {bucket_name} with prefix {prefix}: {str(e)}")
            raise

    def delete_file(self, bucket_name, object_name):
        """Delete a file from the bucket."""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)
            audit_logger.info(f"File {object_name} deleted from bucket {bucket_name}")
            return f"{object_name} deleted."
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = S3Facade.get_error_message(error_code)
            error_logger.error(f"Failed to delete file {object_name} from bucket {bucket_name}: {error_message} "
                               f"(Error Code: {error_code})")
            raise Exception(f"Failed to delete file '{object_name}' from S3. {error_message}")
        except BotoCoreError as e:
            error_logger.error(f"Failed to delete file {object_name} from bucket {bucket_name}: {str(e)}")
            raise

    def generate_presigned_url(self, bucket_name, object_name, expiration=3600):
        """Generate a presigned URL to share an S3 object."""
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            audit_logger.info(f"Presigned URL generated for file {object_name} in bucket {bucket_name}")
            return presigned_url
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = S3Facade.get_error_message(error_code)
            error_logger.error(
                f"Failed to generate presigned URL for {object_name} in bucket {bucket_name}: {error_message} "
                f"(Error Code: {error_code})")
            raise Exception(f"Failed to generate presigned URL for '{object_name}'. {error_message}")
        except BotoCoreError as e:
            error_logger.error(
                f"Failed to generate presigned URL for {object_name} in bucket {bucket_name}: {str(e)}")
            raise
