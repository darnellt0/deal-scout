"""Full-text search utilities for listings and items."""

import logging
from typing import List, Optional
from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session

from app.core.models import Listing, ListingScore

logger = logging.getLogger(__name__)


class ListingSearch:
    """Full-text search for listings using PostgreSQL."""

    @staticmethod
    def search_listings(
        session: Session,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_score: Optional[float] = None,
        condition: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[tuple[Listing, float]], int]:
        """
        Full-text search for listings with optional filters.

        Args:
            session: Database session
            query: Search query string
            category: Optional category filter
            min_price: Optional minimum price filter
            max_price: Optional maximum price filter
            min_score: Optional minimum deal score filter
            condition: Optional condition filter
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            Tuple of (results list, total count)
        """
        # Base query with join to ListingScore for deal scoring
        base_query = session.query(Listing, ListingScore.value).join(
            ListingScore, and_(
                Listing.id == ListingScore.listing_id,
                ListingScore.metric == "deal_score"
            )
        )

        # Apply search query - uses PostgreSQL full-text search
        if query and query.strip():
            # Create a search vector from title, description, and category
            search_query = f"%{query.lower()}%"

            base_query = base_query.filter(
                or_(
                    func.lower(Listing.title).ilike(search_query),
                    func.lower(Listing.description).ilike(search_query),
                    func.lower(Listing.category).ilike(search_query),
                )
            )

        # Apply optional filters
        if category:
            base_query = base_query.filter(
                func.lower(Listing.category).ilike(f"%{category.lower()}%")
            )

        if min_price is not None:
            base_query = base_query.filter(Listing.price >= min_price)

        if max_price is not None:
            base_query = base_query.filter(Listing.price <= max_price)

        if min_score is not None:
            base_query = base_query.filter(ListingScore.value >= min_score)

        if condition:
            base_query = base_query.filter(Listing.condition == condition)

        # Get total count before pagination
        count_query = base_query.with_entities(func.count(Listing.id)).scalar() or 0

        # Order by deal score and apply pagination
        results = (
            base_query.order_by(ListingScore.value.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return results, count_query

    @staticmethod
    def search_listings_advanced(
        session: Session,
        keywords: List[str],
        exclude_keywords: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_score: Optional[float] = None,
        categories: Optional[List[str]] = None,
        condition: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[tuple[Listing, float]], int]:
        """
        Advanced search with multiple keywords and exclusions.

        Args:
            session: Database session
            keywords: List of keywords that must be present (AND logic)
            exclude_keywords: List of keywords to exclude (NOT logic)
            min_price: Optional minimum price filter
            max_price: Optional maximum price filter
            min_score: Optional minimum deal score filter
            categories: Optional list of categories to search in
            condition: Optional condition filter
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            Tuple of (results list, total count)
        """
        # Base query with join to ListingScore
        base_query = session.query(Listing, ListingScore.value).join(
            ListingScore, and_(
                Listing.id == ListingScore.listing_id,
                ListingScore.metric == "deal_score"
            )
        )

        # Apply inclusion filters (AND logic)
        for keyword in keywords:
            if keyword.strip():
                keyword_lower = f"%{keyword.lower()}%"
                base_query = base_query.filter(
                    or_(
                        func.lower(Listing.title).ilike(keyword_lower),
                        func.lower(Listing.description).ilike(keyword_lower),
                        func.lower(Listing.category).ilike(keyword_lower),
                    )
                )

        # Apply exclusion filters (NOT logic)
        if exclude_keywords:
            for keyword in exclude_keywords:
                if keyword.strip():
                    keyword_lower = f"%{keyword.lower()}%"
                    base_query = base_query.filter(
                        ~or_(
                            func.lower(Listing.title).ilike(keyword_lower),
                            func.lower(Listing.description).ilike(keyword_lower),
                            func.lower(Listing.category).ilike(keyword_lower),
                        )
                    )

        # Apply price range filter
        if min_price is not None:
            base_query = base_query.filter(Listing.price >= min_price)

        if max_price is not None:
            base_query = base_query.filter(Listing.price <= max_price)

        # Apply deal score filter
        if min_score is not None:
            base_query = base_query.filter(ListingScore.value >= min_score)

        # Apply category filter
        if categories:
            category_filters = [
                func.lower(Listing.category).ilike(f"%{cat.lower()}%")
                for cat in categories
            ]
            base_query = base_query.filter(or_(*category_filters))

        # Apply condition filter
        if condition:
            base_query = base_query.filter(Listing.condition == condition)

        # Get total count before pagination
        count_query = base_query.with_entities(func.count(Listing.id)).scalar() or 0

        # Order by deal score and apply pagination
        results = (
            base_query.order_by(ListingScore.value.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return results, count_query

    @staticmethod
    def get_suggestions(session: Session, partial_query: str, limit: int = 10) -> List[str]:
        """
        Get autocomplete suggestions for search queries.

        Args:
            session: Database session
            partial_query: Partial search query
            limit: Maximum suggestions to return

        Returns:
            List of suggested search terms
        """
        if not partial_query or len(partial_query) < 2:
            return []

        search_term = f"{partial_query.lower()}%"

        # Get unique categories that match
        categories = (
            session.query(func.distinct(Listing.category))
            .filter(func.lower(Listing.category).ilike(search_term))
            .limit(limit // 2)
            .all()
        )

        # Get unique titles that match
        titles = (
            session.query(func.distinct(Listing.title))
            .filter(func.lower(Listing.title).ilike(search_term))
            .limit(limit // 2)
            .all()
        )

        suggestions = []
        for cat in categories:
            if cat[0]:
                suggestions.append(cat[0])
        for title in titles:
            if title[0]:
                suggestions.append(title[0])

        return suggestions[:limit]
