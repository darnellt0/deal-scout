"""
Cross-Posting Orchestrator Service

Handles publishing items to multiple marketplaces with:
- Retry logic for failed posts
- Platform-specific error handling
- Status tracking and sync
- Image URL preparation
"""
from __future__ import annotations

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.models import MyItem, CrossPost, MarketplaceAccount
from app.services.image_storage import get_image_storage
from app.market.ebay_client import EbayClient
from app.market.facebook_client import FacebookClient
from app.market.offerup_client import OfferUpClient

logger = logging.getLogger(__name__)


class CrossPostingOrchestrator:
    """
    Orchestrates cross-posting to multiple marketplaces.

    Features:
    - Prepares images (uploads to S3/storage)
    - Posts to selected platforms (eBay, Facebook, OfferUp)
    - Creates CrossPost tracking records
    - Handles platform-specific errors
    - Returns detailed results per platform
    """

    def __init__(self, session: Session):
        self.session = session
        self.image_storage = get_image_storage()

    def publish_item(
        self,
        item: MyItem,
        platforms: List[str],
        user_id: int,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish item to multiple marketplaces.

        Args:
            item: MyItem to publish
            platforms: List of platform names (e.g., ['ebay', 'facebook', 'offerup'])
            user_id: User ID for OAuth credentials
            notes: Optional notes for the listing

        Returns:
            {
                'success': bool,
                'results': {
                    'ebay': {'status': 'live', 'external_id': '...', 'url': '...'},
                    'facebook': {'status': 'pending', 'error': '...'},
                    ...
                }
            }
        """
        results = {}
        all_success = True

        # Prepare image URLs (upload if needed)
        image_urls = self._prepare_image_urls(item)
        if not image_urls:
            logger.warning(f"No images available for item {item.id}")
            # Continue anyway - some platforms may allow listings without images

        for platform in platforms:
            try:
                result = self._post_to_platform(
                    platform=platform,
                    item=item,
                    user_id=user_id,
                    image_urls=image_urls,
                    notes=notes
                )
                results[platform] = result

                # Create CrossPost record
                self._create_cross_post_record(
                    item_id=item.id,
                    platform=platform,
                    result=result,
                    user_id=user_id,
                    notes=notes
                )

                if result.get('status') != 'live':
                    all_success = False

            except Exception as e:
                logger.error(f"Failed to post to {platform}: {e}")
                results[platform] = {
                    'status': 'failed',
                    'error': str(e)
                }
                all_success = False

                # Still create CrossPost record to track the failure
                self._create_cross_post_record(
                    item_id=item.id,
                    platform=platform,
                    result={'status': 'failed', 'error': str(e)},
                    user_id=user_id,
                    notes=notes
                )

        self.session.commit()

        return {
            'success': all_success,
            'results': results
        }

    def _prepare_image_urls(self, item: MyItem) -> List[str]:
        """
        Prepare image URLs for marketplace posting.

        If item has base64 images, upload them to storage and return public URLs.
        If item already has image URLs, return them as-is.

        Args:
            item: MyItem with images

        Returns:
            List of public image URLs
        """
        # TODO: Check if item has image_urls field (may need migration)
        # For now, assume images are base64 in processed_images or similar field
        # This will need to be integrated with snap job processing

        image_urls = []

        # Check if item has existing URLs
        if hasattr(item, 'image_urls') and item.image_urls:
            return item.image_urls

        # If images are base64, upload them
        # Note: This assumes snap job has stored base64 images somewhere
        # Actual implementation depends on MyItem model structure

        logger.info(f"Prepared {len(image_urls)} image URLs for item {item.id}")
        return image_urls

    def _post_to_platform(
        self,
        platform: str,
        item: MyItem,
        user_id: int,
        image_urls: List[str],
        notes: Optional[str]
    ) -> Dict[str, Any]:
        """
        Post to a specific platform.

        Args:
            platform: Platform name (ebay, facebook, offerup)
            item: MyItem to post
            user_id: User ID for credentials
            image_urls: List of image URLs
            notes: Optional notes

        Returns:
            {
                'status': 'live' | 'pending' | 'failed' | 'not_configured',
                'external_id': str (if successful),
                'url': str (if available),
                'error': str (if failed)
            }
        """
        # Get marketplace account
        account = (
            self.session.query(MarketplaceAccount)
            .filter_by(user_id=user_id, platform=platform)
            .first()
        )

        if not account or not account.access_token:
            logger.warning(f"No credentials for {platform} (user {user_id})")
            return {
                'status': 'not_configured',
                'error': f'{platform.capitalize()} account not connected'
            }

        # Prepare listing data
        listing_data = {
            'title': item.title or 'Untitled Item',
            'description': item.description or '',
            'price': float(item.price) if item.price else 0.0,
            'category': item.category or 'Other',
            'condition': item.condition or 'used',
            'images': image_urls,
            'location': item.location or {},
            'notes': notes,
        }

        # Call platform-specific client
        if platform == 'ebay':
            return self._post_to_ebay(account, listing_data)
        elif platform == 'facebook':
            return self._post_to_facebook(account, listing_data)
        elif platform == 'offerup':
            return self._post_to_offerup(account, listing_data)
        else:
            return {
                'status': 'failed',
                'error': f'Unsupported platform: {platform}'
            }

    def _post_to_ebay(self, account: MarketplaceAccount, data: Dict) -> Dict[str, Any]:
        """Post to eBay via Inventory API."""
        try:
            client = EbayClient(
                access_token=account.access_token,
                refresh_token=account.refresh_token
            )

            # eBay posting logic (simplified - actual implementation in ebay_client)
            # This is a stub - real implementation calls eBay Inventory API
            result = client.create_listing(data)

            return {
                'status': 'live',
                'external_id': result.get('listing_id'),
                'url': result.get('url'),
            }
        except Exception as e:
            logger.error(f"eBay posting failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _post_to_facebook(self, account: MarketplaceAccount, data: Dict) -> Dict[str, Any]:
        """Post to Facebook Marketplace via Graph API."""
        try:
            client = FacebookClient(access_token=account.access_token)

            # Facebook posting logic
            result = client.post_item(data)

            return {
                'status': 'live',
                'external_id': result.get('post_id'),
                'url': result.get('url'),
            }
        except Exception as e:
            logger.error(f"Facebook posting failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _post_to_offerup(self, account: MarketplaceAccount, data: Dict) -> Dict[str, Any]:
        """Post to OfferUp via API."""
        try:
            client = OfferUpClient(access_token=account.access_token)

            # OfferUp posting logic
            result = client.post_item(data)

            return {
                'status': 'live',
                'external_id': result.get('item_id'),
                'url': result.get('url'),
            }
        except Exception as e:
            logger.error(f"OfferUp posting failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _create_cross_post_record(
        self,
        item_id: int,
        platform: str,
        result: Dict[str, Any],
        user_id: int,
        notes: Optional[str]
    ):
        """Create CrossPost tracking record in database."""
        cross_post = CrossPost(
            item_id=item_id,
            user_id=user_id,
            platform=platform,
            status=result.get('status', 'pending'),
            external_id=result.get('external_id'),
            listing_url=result.get('url'),
            error_message=result.get('error'),
            notes=notes,
            posted_at=datetime.now(timezone.utc) if result.get('status') == 'live' else None,
        )
        self.session.add(cross_post)

    def retry_failed_posts(self, user_id: int, max_retries: int = 3) -> Dict[str, Any]:
        """
        Retry all failed cross-posts for a user.

        Args:
            user_id: User ID
            max_retries: Maximum retry attempts

        Returns:
            Summary of retry results
        """
        failed_posts = (
            self.session.query(CrossPost)
            .filter_by(user_id=user_id, status='failed')
            .filter(CrossPost.retry_count < max_retries)
            .all()
        )

        results = []
        for cross_post in failed_posts:
            item = self.session.query(MyItem).get(cross_post.item_id)
            if not item:
                continue

            logger.info(f"Retrying failed post {cross_post.id} (attempt {cross_post.retry_count + 1})")

            result = self._post_to_platform(
                platform=cross_post.platform,
                item=item,
                user_id=user_id,
                image_urls=[],  # TODO: Get from item
                notes=cross_post.notes
            )

            # Update cross-post record
            cross_post.retry_count += 1
            cross_post.status = result.get('status', 'failed')
            cross_post.external_id = result.get('external_id')
            cross_post.listing_url = result.get('url')
            cross_post.error_message = result.get('error')

            if result.get('status') == 'live':
                cross_post.posted_at = datetime.now(timezone.utc)

            results.append({
                'cross_post_id': cross_post.id,
                'platform': cross_post.platform,
                'new_status': cross_post.status,
            })

        self.session.commit()

        return {
            'retried': len(results),
            'results': results
        }


def get_cross_posting_orchestrator(session: Session) -> CrossPostingOrchestrator:
    """Factory function to get orchestrator instance."""
    return CrossPostingOrchestrator(session)
