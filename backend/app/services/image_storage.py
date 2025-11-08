"""
Image Storage Service

Handles uploading images to S3 (or local fallback) and generating public URLs.
Used by snap jobs and cross-posting to provide image URLs for marketplace APIs.
"""
from __future__ import annotations

import base64
import logging
import uuid
from pathlib import Path
from typing import Optional, List
from io import BytesIO

from app.config import get_settings

logger = logging.getLogger(__name__)


class ImageStorageService:
    """
    Unified image storage service supporting:
    - S3 (preferred for production)
    - Local filesystem (fallback for development)
    """

    def __init__(self):
        self.settings = get_settings()
        self.use_s3 = self.settings.has_s3_config()

        if self.use_s3:
            try:
                import boto3
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.settings.aws_region,
                    aws_access_key_id=self.settings.aws_access_key_id,
                    aws_secret_access_key=self.settings.aws_secret_access_key,
                )
                logger.info("ImageStorageService initialized with S3 backend")
            except ImportError:
                logger.warning("boto3 not installed, falling back to local storage")
                self.use_s3 = False
        else:
            logger.info("S3 not configured, using local storage")

        # Local storage directory
        self.local_storage_dir = Path("/app/backend/static/uploads")
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)

    def upload_image(
        self,
        image_data: bytes | str,
        filename: Optional[str] = None,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload image and return public URL.

        Args:
            image_data: Raw bytes or base64-encoded string
            filename: Optional filename (generates UUID if not provided)
            content_type: MIME type (default: image/jpeg)

        Returns:
            Public URL to the uploaded image
        """
        # Decode base64 if needed
        if isinstance(image_data, str):
            try:
                image_data = base64.b64decode(image_data)
            except Exception as e:
                logger.error(f"Failed to decode base64 image: {e}")
                raise ValueError("Invalid base64 image data")

        # Generate filename if not provided
        if not filename:
            ext = content_type.split('/')[-1]
            filename = f"{uuid.uuid4()}.{ext}"

        if self.use_s3:
            return self._upload_to_s3(image_data, filename, content_type)
        else:
            return self._upload_local(image_data, filename)

    def _upload_to_s3(self, image_data: bytes, filename: str, content_type: str) -> str:
        """Upload to S3 and return public URL."""
        try:
            key = f"{self.settings.s3_image_prefix}{filename}"
            self.s3_client.put_object(
                Bucket=self.settings.s3_bucket,
                Key=key,
                Body=image_data,
                ContentType=content_type,
                ACL='public-read',  # Make publicly accessible
            )

            # Generate public URL
            url = f"https://{self.settings.s3_bucket}.s3.{self.settings.aws_region}.amazonaws.com/{key}"
            logger.info(f"Uploaded image to S3: {url}")
            return url
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            # Fall back to local storage
            logger.warning("Falling back to local storage")
            return self._upload_local(image_data, filename)

    def _upload_local(self, image_data: bytes, filename: str) -> str:
        """Upload to local filesystem and return URL."""
        try:
            file_path = self.local_storage_dir / filename
            with open(file_path, 'wb') as f:
                f.write(image_data)

            # Generate URL (assumes /static is mounted in FastAPI)
            url = f"/static/uploads/{filename}"
            logger.info(f"Uploaded image locally: {url}")
            return url
        except Exception as e:
            logger.error(f"Failed to upload locally: {e}")
            raise

    def upload_multiple(
        self,
        images: List[bytes | str],
        content_type: str = "image/jpeg"
    ) -> List[str]:
        """
        Upload multiple images and return list of URLs.

        Args:
            images: List of image data (bytes or base64)
            content_type: MIME type for all images

        Returns:
            List of public URLs
        """
        urls = []
        for idx, image_data in enumerate(images):
            try:
                url = self.upload_image(image_data, content_type=content_type)
                urls.append(url)
            except Exception as e:
                logger.error(f"Failed to upload image {idx}: {e}")
                # Continue with other images
                continue
        return urls

    def delete_image(self, url: str) -> bool:
        """
        Delete image by URL.

        Args:
            url: Public URL of the image

        Returns:
            True if deleted successfully, False otherwise
        """
        if self.use_s3 and url.startswith('https://'):
            # Extract S3 key from URL
            try:
                key = url.split('.com/')[-1]
                self.s3_client.delete_object(
                    Bucket=self.settings.s3_bucket,
                    Key=key
                )
                logger.info(f"Deleted S3 image: {key}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete S3 image: {e}")
                return False
        elif url.startswith('/static/'):
            # Local file
            try:
                filename = url.split('/')[-1]
                file_path = self.local_storage_dir / filename
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted local image: {filename}")
                    return True
            except Exception as e:
                logger.error(f"Failed to delete local image: {e}")
                return False
        return False


# Singleton instance
_storage_service: Optional[ImageStorageService] = None


def get_image_storage() -> ImageStorageService:
    """Get singleton image storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = ImageStorageService()
    return _storage_service
