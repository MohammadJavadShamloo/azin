import hashlib
import os.path
from datetime import datetime

from django.conf import settings

from storage.es_mappings import USER_USAGE_INDEX_MAPPING, HASH_INDEX_MAPPING
from storage.s3_utils import S3Facade
from storage.es_utils import ESFacade
from botocore.exceptions import ClientError, BotoCoreError
import logging

audit_logger = logging.getLogger('audit_logger')
error_logger = logging.getLogger('error_logger')


class StorageFacade:
    def __init__(self):
        self.s3_facade = S3Facade()
        self.es_facade = ESFacade()
        self.user_usage_index = settings.ES_USER_USAGE_INDEX
        self.file_hash_index = settings.ES_FILE_HASH_INDEX

        self.create_indices()

    def create_indices(self):
        indices = [self.user_usage_index, self.file_hash_index]
        mappings = [USER_USAGE_INDEX_MAPPING, HASH_INDEX_MAPPING]

        for index, mapping in zip(indices, mappings):
            self.es_facade.create_index(index, mapping)

    @staticmethod
    def create_file_hash(file_content):
        """Creates a SHA-256 hash of the file content."""
        return hashlib.sha256(file_content).hexdigest()

    def create_object(self, user_id, file_path, file_content):
        """Creates an object in the user's S3 bucket, handling deduplication and usage updates."""
        file_hash = self.create_file_hash(file_content)
        bucket_name = self.s3_facade.generate_bucket_name(user_id)

        try:
            es_query = {"query": {"term": {"hash": file_hash}}}
            search_result = self.es_facade.es_client.search(index=self.file_hash_index, body=es_query)

            if search_result['hits']['total']['value'] > 0:
                original_doc = search_result['hits']['hits'][0]['_source']
                original_file_key = original_doc['original_key']

                metadata = {'original-key': original_file_key}
                self.s3_facade.upload_file(user_id, file_path, b'', metadata)

                self._update_user_usage(user_id, 0)
                self._index_file_hash(file_path, file_hash, user_id, file_size=0, original_key=original_file_key)

                audit_logger.info(f"File {file_path} linked to existing object with key {original_file_key}.")
                return f"File {file_path} linked to existing object with key {original_file_key}."
            else:
                self.s3_facade.upload_file(user_id, file_path, file_content)
                full_original_key = os.path.join(bucket_name, file_path)

                self._index_file_hash(file_path, file_hash, user_id, file_size=len(file_content),
                                      original_key=full_original_key)
                self._update_user_usage(user_id, len(file_content))

                audit_logger.info(f"File {file_path} uploaded successfully.")
                return f"File {file_path} uploaded successfully."
        except (ClientError, BotoCoreError) as e:
            error_logger.error(f"Error during object creation: {str(e)}")
            raise Exception(f"Error during object creation: {str(e)}")

    def create_folder(self, user_id, folder_path):
        """Creates a folder in the user's S3 bucket."""
        try:
            self.s3_facade.create_folder(user_id, folder_path)
            audit_logger.info(f"Folder {folder_path} created successfully for user {user_id}.")
            return f"Folder {folder_path} created successfully."
        except (ClientError, BotoCoreError) as e:
            error_logger.error(f"Error creating folder {folder_path} for user {user_id}: {str(e)}")
            raise Exception(f"Error creating folder {folder_path} for user {user_id}: {str(e)}")

    def read_object(self, user_id, file_path):
        """Retrieves an object or lists contents if it's a folder."""
        try:
            content, metadata = self.s3_facade.get_object(user_id, file_path)

            if 'original-key' in metadata:
                original_file_path = metadata['original-key']
                bucket_name, file_path = original_file_path.split('/', 1)
                source_user_id = bucket_name.split('-')[1]
                download_link = self.s3_facade.generate_download_link(source_user_id, file_path)
                audit_logger.info(f"Generated download link for {file_path} pointing to {original_file_path}.")
            else:
                download_link = self.s3_facade.generate_download_link(user_id, file_path)
                audit_logger.info(f"Generated download link for {file_path}.")

            return {
                'name': file_path,
                'type': 'file',
                'size': metadata.get('Content-Length', 0),
                'download_link': download_link
            }

        except (ClientError, BotoCoreError, Exception):
            try:
                folder_contents = self.s3_facade.list_folder_contents(user_id, file_path)
                audit_logger.info(f"Listed contents of folder {file_path} for user {user_id}.")
                return folder_contents
            except (ClientError, BotoCoreError) as inner_e:
                error_logger.error(f"Error reading object or folder {file_path} for user {user_id}: {str(inner_e)}")
                raise Exception(f"Error reading object or folder {file_path} for user {user_id}: {str(inner_e)}")

    def delete_object(self, user_id, file_path):
        """Deletes an object or a folder (recursively), and handles updating links if the main file is deleted."""
        try:
            content, metadata = self.s3_facade.get_object(user_id, file_path)

            if 'original-key' in metadata:
                self.s3_facade.delete_object(user_id, file_path)
                self.es_facade.delete_document(self.file_hash_index, f"{user_id}/{file_path}")
                self._update_user_usage(user_id, 0, decrement_file_count=True)
                audit_logger.info(f"Link {file_path} deleted successfully for user {user_id}.")
                return f"Link {file_path} deleted successfully."
            else:
                es_query = {
                    "query": {
                        "match": {
                            "original_key": f"{self.s3_facade.generate_bucket_name(user_id)}/{file_path}"}
                    }
                }
                search_result = self.es_facade.es_client.search(index=self.file_hash_index, body=es_query)

                if search_result['hits']['total']['value'] > 1:
                    new_content_holder = None
                    for hit in search_result['hits']['hits']:
                        potential_new_holder = hit['_id']
                        if potential_new_holder != f"{self.s3_facade.generate_bucket_name(user_id)}/{file_path}":
                            new_content_holder = potential_new_holder
                            break

                    if new_content_holder is None:
                        raise Exception(
                            f"No valid new content holder found for {file_path}. Cannot delete main object.")

                    new_content_holder_bucket_name, new_content_holder_file_path = new_content_holder.split('/', 1)
                    new_content_holder_user_id = new_content_holder_bucket_name.split('-')[1]
                    self.s3_facade.upload_file(new_content_holder_user_id, new_content_holder_file_path, content)

                    for hit in search_result['hits']['hits']:
                        doc_id = hit['_id']
                        if doc_id not in [new_content_holder,
                                          f"{self.s3_facade.generate_bucket_name(user_id)}/{file_path}"]:
                            self.es_facade.update_document(self.file_hash_index, doc_id,
                                                           {'original_key': new_content_holder})
                            linked_bucket_name, linked_file_path = doc_id.split("/", 1)
                            linked_user_id = linked_bucket_name.split('-')[1]
                            self.s3_facade.upload_file(linked_user_id, linked_file_path, b'',
                                                       {'original-key': new_content_holder})

                    self._index_file_hash(new_content_holder_file_path, self.create_file_hash(content),
                                          new_content_holder_user_id, file_size=len(content),
                                          original_key=new_content_holder)

                self.s3_facade.delete_object(user_id, file_path)
                self.es_facade.delete_document(self.file_hash_index,
                                               f"{self.s3_facade.generate_bucket_name(user_id)}/{file_path}")
                self._update_user_usage(user_id, -len(content), decrement_file_count=True)
                audit_logger.info(f"Original file {file_path} deleted successfully for user {user_id}.")
                return f"Original file {file_path} deleted successfully."
        except (ClientError, BotoCoreError, Exception) as e:
            try:
                folder_contents = self.s3_facade.list_folder_contents(user_id, file_path, only_name=True)
                for item in folder_contents:
                    item_name = os.path.join(file_path, item)
                    self.delete_object(user_id, item_name)
                self.s3_facade.delete_object(user_id, os.path.join(file_path, ''))
                audit_logger.info(f"Folder {file_path} and its contents deleted successfully for user {user_id}.")
                return f"Folder {file_path} and its contents deleted successfully."
            except (ClientError, BotoCoreError) as inner_e:
                error_logger.error(
                    f"Error deleting folder or its contents {file_path} for user {user_id}: {str(inner_e)}")
                raise Exception(f"Error deleting folder or its contents {file_path} for user {user_id}: {str(inner_e)}")

    def _index_file_hash(self, file_path, file_hash, user_id, file_size, original_key=None):
        """Indexes the file hash in Elasticsearch with full metadata according to the specified mapping."""
        folder_path, filename = os.path.split(file_path)
        file_type = filename.split('.')[-1] if '.' in filename else 'unknown'

        document = {
            "hash": file_hash,
            "original_key": original_key if original_key else file_path,
            "user_id": user_id,
            "filename": filename,
            "folder_path": folder_path,
            "creation_date": int(datetime.now().timestamp() * 1000),
            "size": file_size,
            "file_type": file_type,
        }

        try:
            doc_id = f"{self.s3_facade.generate_bucket_name(user_id)}/{file_path}"
            self.es_facade.index_document(self.file_hash_index, doc_id, document)
            audit_logger.info(f"Indexed file hash for {file_path} in Elasticsearch.")
        except (ClientError, BotoCoreError) as e:
            error_logger.error(f"Error indexing file hash for {file_path} in Elasticsearch: {str(e)}")
            raise Exception(f"Error indexing file hash for {file_path} in Elasticsearch: {str(e)}")

    def _update_user_usage(self, user_id, file_size_change, decrement_file_count=False):
        """Updates the user's storage usage in Elasticsearch."""
        try:
            current_usage = self.es_facade.get_document(self.user_usage_index, user_id)
            updated_size = current_usage['total_size'] + file_size_change
            updated_file_count = current_usage['file_count'] + (-1 if decrement_file_count else 1)
            self.es_facade.update_document(self.user_usage_index, user_id, {
                "total_size": updated_size,
                "file_count": updated_file_count
            })
            audit_logger.info(
                f"Updated storage usage for user {user_id}: size change {file_size_change}, file count updated.")
        except (ClientError, BotoCoreError) as e:
            error_logger.error(f"Error updating user usage for user {user_id}: {str(e)}")
            raise Exception(f"Failed to update user usage for user {user_id}: {str(e)}")
