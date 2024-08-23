import hashlib
import logging
from s3_utils import S3Facade
from es_utils import ElasticsearchFacade
from storage.es_mappings import HASH_INDEX_MAPPING

audit_logger = logging.getLogger('audit')
error_logger = logging.getLogger('error_logger')


class StorageFacade:
    def __init__(self):
        try:
            self.s3_facade = S3Facade()
            self.es_facade = ElasticsearchFacade()
            self.index_name = 'files_index'
            audit_logger.info("Initialized StorageFacade with S3 and Elasticsearch facades.")

            if not self.es_facade.es_client.indices.exists(self.index_name):
                self.es_facade.create_index(self.index_name, es_mappings=HASH_INDEX_MAPPING)
        except Exception as e:
            error_logger.error(f"Failed to initialize StorageFacade: {str(e)}")
            raise

    @staticmethod
    def calculate_file_hash(file_path):
        """Calculate the SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            error_logger.error(f"Failed to calculate file hash for {file_path}: {str(e)}")
            raise

    def upload_file(self, file_path, bucket_name, object_name=None, metadata=None):
        """Upload a file to S3 and index it in Elasticsearch."""
        try:
            # Calculate the file's hash
            file_hash = self.calculate_file_hash(file_path)

            # Check if the file already exists in Elasticsearch
            query = {"query": {"term": {"file_hash": file_hash}}}
            existing_files = self.es_facade.search(self.index_name, query)

            if existing_files['hits']['total']['value'] > 0:
                # File with the same hash already exists, check if it's in the same bucket
                existing_file = existing_files['hits']['hits'][0]['_source']
                existing_bucket = existing_file['s3_object_name'].split('/')[0]

                if existing_bucket == bucket_name:
                    # Same bucket, create a metadata redirection link
                    link_object_name = f"{file_path.rsplit('/', 1)[-1]}_link"
                    self.s3_facade.create_link(bucket_name, existing_file['s3_object_name'], link_object_name)
                    audit_logger.info(
                        f"File '{file_path}' already exists in the same bucket as '{existing_file['s3_object_name']}'. "
                        f"Link created as '{link_object_name}'.")
                    return existing_file['s3_object_name'], link_object_name

                else:
                    audit_logger.info(
                        f"File '{file_path}' found in a different bucket '{existing_bucket}'. Uploading as a new object.")
                    # Proceed to upload as a new object

            # File doesn't exist in the same bucket or at all, upload it
            object_name = object_name or file_path.rsplit('/', 1)[-1]
            s3_object_name = self.s3_facade.upload_file(bucket_name, file_path, object_name)

            # Index the file metadata in Elasticsearch
            document = {
                "file_hash": file_hash,
                "s3_object_name": s3_object_name,
                "metadata": metadata or {}
            }
            self.es_facade.index_document(self.index_name, document)

            audit_logger.info(f"File '{file_path}' uploaded to S3 as '{s3_object_name}' and indexed in Elasticsearch.")

            return s3_object_name, None
        except Exception as e:
            error_logger.error(f"Failed to upload file '{file_path}': {str(e)}")
            raise

    def download_file(self, file_hash, file_name=None):
        """Download a file from S3 based on its hash."""
        try:
            # Find the file in Elasticsearch
            query = {"query": {"term": {"file_hash": file_hash}}}
            result = self.es_facade.search(self.index_name, query)

            if result['hits']['total']['value'] == 0:
                raise Exception(f"No file found with hash '{file_hash}'")

            s3_object_name = result['hits']['hits'][0]['_source']['s3_object_name']

            # Download the file from S3
            downloaded_file = self.s3_facade.download_file(s3_object_name, file_name)
            audit_logger.info(f"File with hash '{file_hash}' downloaded as '{downloaded_file}'.")

            return downloaded_file
        except Exception as e:
            error_logger.error(f"Failed to download file with hash '{file_hash}': {str(e)}")
            raise

    def list_files(self, prefix=None):
        """List files in the S3 bucket."""
        try:
            files = self.s3_facade.list_files(prefix)
            audit_logger.info(f"Files listed with prefix '{prefix}': {files}")
            return files
        except Exception as e:
            error_logger.error(f"Failed to list files with prefix '{prefix}': {str(e)}")
            raise

    def delete_file(self, file_hash, bucket_name):
        """Delete a file from S3 and Elasticsearch based on its hash."""
        try:
            # Find the file in Elasticsearch
            query = {"query": {"term": {"file_hash": file_hash}}}
            result = self.es_facade.search(self.index_name, query)

            if result['hits']['total']['value'] == 0:
                raise Exception(f"No file found with hash '{file_hash}'")

            s3_object_name = result['hits']['hits'][0]['_source']['s3_object_name']

            # If the object is a link, convert it to the full object before deletion
            metadata = self.s3_facade.get_object_metadata(bucket_name, s3_object_name)
            original_key = metadata.get('original-key')
            if original_key:
                # Download the original file and upload it to replace the link
                original_file_content = self.s3_facade.get_object_body(bucket_name, original_key)
                self.s3_facade.upload_object_body(bucket_name, s3_object_name, original_file_content)
                audit_logger.info(f"Link '{s3_object_name}' was converted to a full object before deletion.")

            # Delete the file from S3
            self.s3_facade.delete_file(bucket_name, s3_object_name)

            # Remove the document from Elasticsearch
            doc_id = result['hits']['hits'][0]['_id']
            self.es_facade.delete_document(self.index_name, doc_id)

            audit_logger.info(f"File with hash '{file_hash}' deleted from S3 and Elasticsearch.")

            return f"File '{s3_object_name}' deleted."
        except Exception as e:
            error_logger.error(f"Failed to delete file with hash '{file_hash}': {str(e)}")
            raise
