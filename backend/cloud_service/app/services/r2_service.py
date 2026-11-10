import boto3
from botocore.exceptions import ClientError
from app.config import settings
import uuid
from typing import BinaryIO, Optional

class R2Service:
    def __init__(self):
        self._client = None
        self.bucket = settings.r2_bucket_name
        self.public_url = settings.r2_public_url

    @property
    def client(self):
        if self._client is None:
            if not settings.r2_endpoint:
                raise Exception("R2 is not configured. Set R2_ENDPOINT and related env vars.")
            self._client = boto3.client(
                's3',
                endpoint_url=settings.r2_endpoint,
                aws_access_key_id=settings.r2_access_key_id,
                aws_secret_access_key=settings.r2_secret_access_key,
                region_name='auto'
            )
        return self._client
    
    def upload_file(
        self, 
        file_data: BinaryIO, 
        filename: str, 
        app_id: uuid.UUID, 
        user_id: uuid.UUID,
        content_type: str = None
    ) -> dict:
        """Upload file to R2 and return metadata"""
        # Generate unique key: app_id/user_id/uuid_filename
        file_uuid = uuid.uuid4()
        key = f"{app_id}/{user_id}/{file_uuid}_{filename}"
        
        try:
            # Upload to R2
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.client.upload_fileobj(
                file_data,
                self.bucket,
                key,
                ExtraArgs=extra_args
            )
            
            # Generate public URL
            url = f"{self.public_url}/{key}"
            
            return {
                "key": key,
                "url": url,
                "filename": filename
            }
        except ClientError as e:
            raise Exception(f"Failed to upload file: {str(e)}")
    
    def delete_file(self, key: str) -> bool:
        """Delete file from R2"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
    
    def get_file_url(self, key: str) -> str:
        """Get public URL for a file"""
        return f"{self.public_url}/{key}"
    
    def file_exists(self, key: str) -> bool:
        """Check if file exists in R2"""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

# Singleton instance
r2_service = R2Service()
