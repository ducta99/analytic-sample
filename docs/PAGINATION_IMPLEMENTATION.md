# Pagination Implementation Guide

Comprehensive guide for implementing cursor-based pagination across API endpoints to handle large datasets efficiently.

**Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** January 2025

## Table of Contents

1. [Pagination Overview](#pagination-overview)
2. [Cursor-Based Pagination](#cursor-based-pagination)
3. [Backend Implementation](#backend-implementation)
4. [API Documentation](#api-documentation)
5. [Frontend Implementation](#frontend-implementation)
6. [Testing & Validation](#testing--validation)
7. [Performance Optimization](#performance-optimization)

---

## Pagination Overview

### 1. Pagination Types

| Type | Use Case | Pros | Cons |
|------|----------|------|------|
| **Offset-Limit** | Traditional pagination | Simple, easy to understand | OFFSET is slow on large datasets, inconsistent results on changes |
| **Cursor-Based** | Large datasets, real-time | Efficient, consistent, prevents duplicate rows | Requires ordering, less intuitive |
| **Keyset** | Timeline feeds | Very efficient | More complex, requires unique keys |
| **Search-Based** | Elasticsearch | Powerful filtering | Different implementation per backend |

### 2. Cursor-Based Pagination Pattern

```
Request 1: GET /api/market/prices?limit=10
Response:
{
  "data": [
    {"id": 1, "coin": "bitcoin", "price": 45000, ...},
    {"id": 2, "coin": "ethereum", "price": 2500, ...},
    ...
    {"id": 10, "coin": "solana", "price": 150, ...}
  ],
  "pagination": {
    "has_more": true,
    "next_cursor": "eyJpZCI6IDEwfQ=="  // Base64-encoded {"id": 10}
  }
}

Request 2: GET /api/market/prices?limit=10&cursor=eyJpZCI6IDEwfQ==
Response:
{
  "data": [
    {"id": 11, "coin": "cardano", "price": 0.5, ...},
    ...
    {"id": 20, "coin": "litecoin", "price": 200, ...}
  ],
  "pagination": {
    "has_more": true,
    "next_cursor": "eyJpZCI6IDIwfQ=="
  }
}
```

### 3. Cursor Format

```
Cursor: eyJpZCI6IDEwfQ==

Base64 decode → {"id": 10}
                 ↓
                 Last item ID from previous page
                 ↓
                 Used to fetch next batch
```

---

## Cursor-Based Pagination

### 1. Database Query Pattern

```sql
-- Traditional offset-limit (SLOW on large tables)
SELECT * FROM prices
LIMIT 10 OFFSET 100
-- SQL Server scans first 110 rows, returns last 10

-- Cursor-based pagination (FAST)
SELECT * FROM prices
WHERE id > 10  -- Previous cursor value
ORDER BY id
LIMIT 10
-- Database uses index, scans exactly 10 rows
```

### 2. Pros of Cursor-Based Pagination

✅ **Performance:** Uses database indexes, O(n) where n = page size (not n = offset)  
✅ **Consistency:** No duplicate rows if data changes during pagination  
✅ **Simplicity:** No need to calculate total pages or maintain OFFSET state  
✅ **Infinite scrolling:** Perfect for mobile apps and feeds  
✅ **Backwards compatibility:** Can go both forward and backward with cursors

### 3. Cons of Cursor-Based Pagination

⚠️ **Ordering:** Always requires consistent ordering  
⚠️ **Discoverability:** User can't jump to page 50 directly  
⚠️ **Complexity:** Slightly more complex than offset-limit for backend  
⚠️ **Sorting:** Dynamic sorting requires careful index planning  

---

## Backend Implementation

### 1. Pagination Models

**shared/schemas.py:**

```python
"""Pagination schemas for all API responses."""

from typing import TypeVar, Generic, List, Optional, Dict, Any
from pydantic import BaseModel, Field
import base64
import json

T = TypeVar('T')


class PaginationCursor(BaseModel):
    """Pagination cursor data."""
    id: int
    timestamp: Optional[str] = None  # For time-based sorting
    
    def encode(self) -> str:
        """Encode cursor to base64 string."""
        data = self.model_dump(exclude_none=True)
        json_str = json.dumps(data)
        return base64.b64encode(json_str.encode()).decode()
    
    @staticmethod
    def decode(cursor: str) -> 'PaginationCursor':
        """Decode cursor from base64 string."""
        try:
            json_str = base64.b64decode(cursor).decode()
            data = json.loads(json_str)
            return PaginationCursor(**data)
        except Exception as e:
            raise ValueError(f"Invalid cursor: {e}")


class PaginationInfo(BaseModel):
    """Pagination information."""
    has_more: bool = Field(..., description="Whether more items exist")
    next_cursor: Optional[str] = Field(
        None, 
        description="Cursor for next page (if has_more=true)"
    )
    prev_cursor: Optional[str] = Field(
        None,
        description="Cursor for previous page"
    )
    page_size: int = Field(..., description="Number of items returned")
    total_returned: int = Field(..., description="Actual items returned")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    data: List[T] = Field(..., description="Page items")
    pagination: PaginationInfo = Field(..., description="Pagination details")


# Example typed responses
class Price(BaseModel):
    id: int
    coin_id: str
    price: float
    timestamp: str


class PaginatedPrices(PaginatedResponse[Price]):
    """Paginated price response."""
    pass
```

### 2. FastAPI Pagination Dependencies

**shared/pagination.py:**

```python
"""Pagination utilities for FastAPI endpoints."""

from typing import Optional, List, TypeVar, Generic, Any
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.orm import AsyncSession
from .schemas import PaginationCursor, PaginationInfo, PaginatedResponse

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    cursor: Optional[str] = None
    limit: int = 10
    
    def __init__(self, cursor: Optional[str] = None, limit: int = 10, **kwargs):
        # Validate limit
        if limit < 1 or limit > 100:
            limit = min(max(limit, 1), 100)
        
        super().__init__(cursor=cursor, limit=limit, **kwargs)


async def paginate(
    session: AsyncSession,
    query,  # SQLAlchemy query object
    cursor: Optional[str] = None,
    limit: int = 10,
    cursor_field=None,  # Field to use for cursor (default: id)
):
    """
    Paginate a SQLAlchemy query using cursor-based pagination.
    
    Args:
        session: AsyncSession
        query: SQLAlchemy select() query
        cursor: Pagination cursor from previous request
        limit: Number of items per page (1-100)
        cursor_field: SQLAlchemy column to use for cursor
    
    Returns:
        dict with 'items', 'has_more', 'next_cursor', 'prev_cursor'
    """
    
    # Validate limit
    limit = min(max(limit, 1), 100)
    
    # Decode cursor if provided
    cursor_value = None
    if cursor:
        try:
            cursor_obj = PaginationCursor.decode(cursor)
            cursor_value = cursor_obj.id
        except ValueError:
            raise ValueError("Invalid cursor format")
    
    # If no cursor field specified, use 'id'
    if cursor_field is None:
        from sqlalchemy import inspect
        # This should be set by caller, but default to 'id'
        cursor_column_name = 'id'
    else:
        cursor_column_name = cursor_field.name if hasattr(cursor_field, 'name') else str(cursor_field)
    
    # Fetch limit+1 to determine if there are more items
    fetch_limit = limit + 1
    
    # Build filter condition if cursor provided
    if cursor_value is not None:
        # Assuming cursor is based on ID
        # Adjust this based on your ordering strategy
        query = query.where(cursor_field > cursor_value)
    
    # Order by cursor field
    if cursor_field is not None:
        query = query.order_by(cursor_field)
    
    # Execute query
    result = await session.execute(query.limit(fetch_limit))
    items = result.scalars().all()
    
    # Determine if there are more items
    has_more = len(items) > limit
    if has_more:
        items = items[:limit]  # Remove the extra item
    
    # Generate next cursor
    next_cursor = None
    if has_more and items:
        last_item = items[-1]
        # Extract ID from item (could be dict or ORM model)
        if hasattr(last_item, 'id'):
            last_id = last_item.id
        else:
            last_id = last_item.get('id')
        
        next_cursor = PaginationCursor(id=last_id).encode()
    
    # Generate prev cursor (optional - can be empty)
    prev_cursor = cursor  # Just return original cursor as prev
    
    return {
        'items': items,
        'has_more': has_more,
        'next_cursor': next_cursor,
        'prev_cursor': prev_cursor,
    }
```

### 3. Market Data Service Implementation

**market-data-service/app/routes.py:**

```python
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from shared.pagination import paginate, PaginationParams
from shared.schemas import PaginatedResponse, PaginationInfo
from .schemas import PriceResponse
from .models import Price as PriceModel
from .database import get_session

router = APIRouter(prefix="/api/market", tags=["Market Data"])


@router.get("/prices", response_model=PaginatedResponse)
async def get_prices(
    coins: str = Query(
        None,
        description="Comma-separated list of coin IDs",
        example="bitcoin,ethereum,cardano"
    ),
    cursor: str = Query(
        None,
        description="Pagination cursor from previous response",
        example="eyJpZCI6IDEwfQ=="
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Number of items per page (1-100)"
    ),
    session: AsyncSession = Depends(get_session),
):
    """
    Get cryptocurrency prices with pagination.
    
    Query Parameters:
    - coins: Comma-separated coin IDs (e.g., "bitcoin,ethereum")
    - cursor: Pagination cursor from previous response
    - limit: Items per page (default: 10, max: 100)
    
    Returns paginated list of prices.
    """
    
    # Build base query
    query = select(PriceModel).order_by(desc(PriceModel.id))
    
    # Filter by coins if provided
    if coins:
        coin_list = [c.strip().lower() for c in coins.split(",")]
        query = query.where(PriceModel.coin_id.in_(coin_list))
    
    # Paginate
    page_data = await paginate(
        session,
        query,
        cursor=cursor,
        limit=limit,
        cursor_field=PriceModel.id
    )
    
    # Build response
    prices = [PriceResponse.from_orm(item) for item in page_data['items']]
    
    pagination = PaginationInfo(
        has_more=page_data['has_more'],
        next_cursor=page_data['next_cursor'],
        prev_cursor=page_data['prev_cursor'],
        page_size=len(prices),
        total_returned=len(prices),
    )
    
    return PaginatedResponse(data=prices, pagination=pagination)


@router.get("/prices/by-coin/{coin_id}", response_model=PaginatedResponse)
async def get_prices_for_coin(
    coin_id: str = Query(..., description="Cryptocurrency ID"),
    days: int = Query(
        7,
        ge=1,
        le=365,
        description="Number of days of history"
    ),
    cursor: str = Query(None),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """
    Get price history for a specific coin.
    
    Supports time-range queries with cursor pagination.
    """
    from datetime import datetime, timedelta
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Build query with time range
    query = select(PriceModel).where(
        (PriceModel.coin_id == coin_id) &
        (PriceModel.timestamp >= start_date) &
        (PriceModel.timestamp <= end_date)
    ).order_by(desc(PriceModel.timestamp))
    
    # Paginate
    page_data = await paginate(
        session,
        query,
        cursor=cursor,
        limit=limit,
        cursor_field=PriceModel.id
    )
    
    prices = [PriceResponse.from_orm(item) for item in page_data['items']]
    pagination = PaginationInfo(
        has_more=page_data['has_more'],
        next_cursor=page_data['next_cursor'],
        prev_cursor=page_data['prev_cursor'],
        page_size=len(prices),
        total_returned=len(prices),
    )
    
    return PaginatedResponse(data=prices, pagination=pagination)
```

### 4. Portfolio Service Implementation

**portfolio-service/app/routes.py:**

```python
@router.get("/portfolio/{portfolio_id}/assets")
async def get_portfolio_assets(
    portfolio_id: int,
    cursor: str = Query(None),
    limit: int = Query(10, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Get assets in a portfolio with pagination.
    """
    
    # Verify portfolio ownership
    portfolio = await session.get(Portfolio, portfolio_id)
    if not portfolio or portfolio.user_id != user_id:
        raise HTTPException(status_code=404)
    
    # Build query
    query = select(Asset).where(
        Asset.portfolio_id == portfolio_id
    ).order_by(desc(Asset.id))
    
    # Paginate
    page_data = await paginate(
        session,
        query,
        cursor=cursor,
        limit=limit,
        cursor_field=Asset.id
    )
    
    assets = [AssetResponse.from_orm(item) for item in page_data['items']]
    pagination = PaginationInfo(
        has_more=page_data['has_more'],
        next_cursor=page_data['next_cursor'],
        prev_cursor=page_data['prev_cursor'],
        page_size=len(assets),
        total_returned=len(assets),
    )
    
    return PaginatedResponse(data=assets, pagination=pagination)
```

### 5. Sentiment Service Implementation

**sentiment-service/app/routes.py:**

```python
@router.get("/sentiment/news/{coin_id}")
async def get_news_articles(
    coin_id: str,
    cursor: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """
    Get news articles for a coin with pagination.
    """
    
    # Build query (ordered by most recent first)
    query = select(NewsArticle).where(
        NewsArticle.coin_id == coin_id
    ).order_by(desc(NewsArticle.published_at))
    
    # Paginate
    page_data = await paginate(
        session,
        query,
        cursor=cursor,
        limit=limit,
        cursor_field=NewsArticle.id
    )
    
    articles = [
        NewsArticleResponse.from_orm(item)
        for item in page_data['items']
    ]
    
    pagination = PaginationInfo(
        has_more=page_data['has_more'],
        next_cursor=page_data['next_cursor'],
        prev_cursor=page_data['prev_cursor'],
        page_size=len(articles),
        total_returned=len(articles),
    )
    
    return PaginatedResponse(data=articles, pagination=pagination)
```

---

## API Documentation

### 1. OpenAPI Schema Update

**Update docs/openapi.yaml:**

```yaml
components:
  schemas:
    # Pagination objects
    PaginationCursor:
      type: object
      properties:
        id:
          type: integer
          description: Cursor ID (base item ID)
        timestamp:
          type: string
          format: date-time
          nullable: true
          description: Optional timestamp for time-based cursors

    PaginationInfo:
      type: object
      required:
        - has_more
        - page_size
        - total_returned
      properties:
        has_more:
          type: boolean
          description: True if more items exist
        next_cursor:
          type: string
          nullable: true
          description: Cursor for next page (if has_more=true)
        prev_cursor:
          type: string
          nullable: true
          description: Cursor for previous page
        page_size:
          type: integer
          description: Number of items returned
        total_returned:
          type: integer
          description: Actual items returned

    PaginatedPrices:
      type: object
      required:
        - data
        - pagination
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Price'
          description: Array of prices
        pagination:
          $ref: '#/components/schemas/PaginationInfo'

    Price:
      type: object
      required:
        - id
        - coin_id
        - price
        - timestamp
      properties:
        id:
          type: integer
        coin_id:
          type: string
        price:
          type: number
          format: float
        price_change_24h:
          type: number
          format: float
        timestamp:
          type: string
          format: date-time

  # Pagination parameters
  parameters:
    CursorParam:
      name: cursor
      in: query
      description: Pagination cursor from previous response
      schema:
        type: string
        example: "eyJpZCI6IDEwfQ=="
      required: false

    LimitParam:
      name: limit
      in: query
      description: Number of items per page (1-100)
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 10
      required: false

paths:
  /api/market/prices:
    get:
      summary: Get cryptocurrency prices (paginated)
      tags:
        - Market Data
      parameters:
        - name: coins
          in: query
          description: Comma-separated coin IDs
          schema:
            type: string
            example: "bitcoin,ethereum,cardano"
        - $ref: '#/components/parameters/CursorParam'
        - $ref: '#/components/parameters/LimitParam'
      responses:
        '200':
          description: Paginated prices
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedPrices'
              example:
                data:
                  - id: 1
                    coin_id: "bitcoin"
                    price: 45000
                    price_change_24h: 2.5
                    timestamp: "2025-01-15T12:00:00Z"
                pagination:
                  has_more: true
                  next_cursor: "eyJpZCI6IDEwfQ=="
                  page_size: 10
                  total_returned: 10
```

---

## Frontend Implementation

### 1. React Query Hook

**frontend/src/hooks/usePagedData.ts:**

```typescript
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import { apiClient } from '../utils/api-client';

export interface PaginationInfo {
  has_more: boolean;
  next_cursor?: string;
  prev_cursor?: string;
  page_size: number;
  total_returned: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationInfo;
}

/**
 * Hook for paginated data fetching with cursor support
 */
export function usePagedData<T>(
  endpoint: string,
  params: Record<string, any> = {},
  limit: number = 10
): {
  data: T[];
  loading: boolean;
  error: Error | null;
  hasMore: boolean;
  fetchMore: () => void;
  reset: () => void;
} {
  const [allData, setAllData] = useState<T[]>([]);
  const [nextCursor, setNextCursor] = useState<string | undefined>(undefined);
  const [hasMore, setHasMore] = useState(true);

  const { isLoading, error, refetch } = useQuery(
    [endpoint, params, nextCursor],
    async () => {
      const response = await apiClient.request<PaginatedResponse<T>>(
        'GET',
        endpoint,
        undefined,
        {
          params: {
            ...params,
            cursor: nextCursor,
            limit,
          },
        }
      );

      // Append new items to existing data
      setAllData((prev) => [...prev, ...response.data]);

      // Update pagination state
      setHasMore(response.pagination.has_more);
      setNextCursor(response.pagination.next_cursor);

      return response;
    },
    {
      enabled: hasMore,
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const fetchMore = useCallback(() => {
    if (hasMore && !isLoading) {
      refetch();
    }
  }, [hasMore, isLoading, refetch]);

  const reset = useCallback(() => {
    setAllData([]);
    setNextCursor(undefined);
    setHasMore(true);
  }, []);

  return {
    data: allData,
    loading: isLoading,
    error: error as Error | null,
    hasMore,
    fetchMore,
    reset,
  };
}
```

### 2. Infinite Scroll Component

**frontend/src/components/PaginatedPriceList.tsx:**

```typescript
import React, { useEffect, useRef, useCallback } from 'react';
import { usePagedData } from '../hooks/usePagedData';
import InfiniteScroll from 'react-infinite-scroll-component';

interface PriceListProps {
  coins?: string;
  pageSize?: number;
}

export const PaginatedPriceList: React.FC<PriceListProps> = ({
  coins,
  pageSize = 20,
}) => {
  const { data, loading, error, hasMore, fetchMore } = usePagedData(
    '/api/market/prices',
    coins ? { coins } : {},
    pageSize
  );

  return (
    <InfiniteScroll
      dataLength={data.length}
      next={fetchMore}
      hasMore={hasMore}
      loader={<div className="p-4">Loading more prices...</div>}
      endMessage={<div className="p-4">No more prices to load</div>}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((price, index) => (
          <div key={`${price.coin_id}-${index}`} className="card">
            <div className="card-body">
              <h3 className="text-lg font-bold">{price.coin_id}</h3>
              <p>${price.price.toFixed(2)}</p>
              <p className={price.price_change_24h >= 0 ? 'text-green-600' : 'text-red-600'}>
                {price.price_change_24h > 0 ? '+' : ''}{price.price_change_24h.toFixed(2)}%
              </p>
            </div>
          </div>
        ))}
      </div>

      {error && (
        <div className="alert alert-error mt-4">
          <p>Error loading prices: {error.message}</p>
        </div>
      )}
    </InfiniteScroll>
  );
};
```

### 3. Pagination Controls Component

**frontend/src/components/PaginationControls.tsx:**

```typescript
import React from 'react';

interface PaginationControlsProps {
  currentPage: number;
  pageSize: number;
  hasMore: boolean;
  loading: boolean;
  onNext: () => void;
  onPrev: () => void;
  onPageSizeChange: (size: number) => void;
}

export const PaginationControls: React.FC<PaginationControlsProps> = ({
  currentPage,
  pageSize,
  hasMore,
  loading,
  onNext,
  onPrev,
  onPageSizeChange,
}) => {
  return (
    <div className="flex items-center justify-between p-4">
      <div className="flex items-center gap-2">
        <label htmlFor="pageSize">Items per page:</label>
        <select
          id="pageSize"
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="select select-bordered"
        >
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onPrev}
          disabled={currentPage === 1 || loading}
          className="btn btn-sm"
        >
          Previous
        </button>

        <span className="px-4">Page {currentPage}</span>

        <button
          onClick={onNext}
          disabled={!hasMore || loading}
          className="btn btn-sm"
        >
          {loading ? 'Loading...' : 'Next'}
        </button>
      </div>
    </div>
  );
};
```

---

## Testing & Validation

### 1. Backend Pagination Tests

**tests/test_pagination.py:**

```python
import pytest
from httpx import AsyncClient
import json
import base64


@pytest.mark.asyncio
async def test_pagination_first_page(client: AsyncClient):
    """Test first page of pagination."""
    response = await client.get("/api/market/prices?limit=5")
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) <= 5
    assert isinstance(data["pagination"]["has_more"], bool)


@pytest.mark.asyncio
async def test_pagination_cursor_encoding(client: AsyncClient):
    """Test cursor encoding/decoding."""
    # Get first page
    response = await client.get("/api/market/prices?limit=5")
    pagination = response.json()["pagination"]
    
    if pagination["has_more"]:
        cursor = pagination["next_cursor"]
        
        # Verify cursor is base64
        decoded = base64.b64decode(cursor).decode()
        cursor_data = json.loads(decoded)
        assert "id" in cursor_data


@pytest.mark.asyncio
async def test_pagination_with_cursor(client: AsyncClient):
    """Test pagination with cursor from previous page."""
    # Get first page
    response1 = await client.get("/api/market/prices?limit=5")
    page1_data = response1.json()
    
    if page1_data["pagination"]["has_more"]:
        next_cursor = page1_data["pagination"]["next_cursor"]
        
        # Get next page
        response2 = await client.get(
            f"/api/market/prices?limit=5&cursor={next_cursor}"
        )
        page2_data = response2.json()
        
        # Verify different data
        page1_ids = [item["id"] for item in page1_data["data"]]
        page2_ids = [item["id"] for item in page2_data["data"]]
        
        assert page1_ids != page2_ids
        assert len(page2_data["data"]) <= 5


@pytest.mark.asyncio
async def test_pagination_limit_enforcement(client: AsyncClient):
    """Test that limit is enforced."""
    response = await client.get("/api/market/prices?limit=200")  # Over max
    data = response.json()
    
    # Should be capped at 100
    assert len(data["data"]) <= 100
    assert data["pagination"]["page_size"] <= 100


@pytest.mark.asyncio
async def test_pagination_last_page(client: AsyncClient):
    """Test pagination on last page."""
    cursor = None
    has_more = True
    pages = 0
    
    while has_more and pages < 100:  # Safety limit
        params = {"limit": 5}
        if cursor:
            params["cursor"] = cursor
        
        response = await client.get("/api/market/prices", params=params)
        data = response.json()
        
        has_more = data["pagination"]["has_more"]
        cursor = data["pagination"]["next_cursor"]
        pages += 1
    
    # Last page should have has_more=False
    assert has_more is False
```

### 2. Frontend Pagination Tests

**frontend/__tests__/usePagedData.test.ts:**

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePagedData } from '../src/hooks/usePagedData';
import React from 'react';

describe('usePagedData', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient();
  });

  it('should fetch first page of data', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      React.createElement(QueryClientProvider, { client: queryClient }, children)
    );

    const { result } = renderHook(
      () => usePagedData('/api/market/prices', {}, 10),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.data.length).toBeGreaterThan(0);
    });
  });

  it('should fetch more data on demand', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      React.createElement(QueryClientProvider, { client: queryClient }, children)
    );

    const { result } = renderHook(
      () => usePagedData('/api/market/prices', {}, 10),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.data.length).toBeGreaterThan(0);
    });

    const firstPageLength = result.current.data.length;

    if (result.current.hasMore) {
      result.current.fetchMore();

      await waitFor(() => {
        expect(result.current.data.length).toBeGreaterThan(firstPageLength);
      });
    }
  });

  it('should reset data', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      React.createElement(QueryClientProvider, { client: queryClient }, children)
    );

    const { result } = renderHook(
      () => usePagedData('/api/market/prices', {}, 10),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.data.length).toBeGreaterThan(0);
    });

    result.current.reset();

    expect(result.current.data.length).toBe(0);
  });
});
```

### 3. Load Testing

```bash
#!/bin/bash
# scripts/load_test_pagination.sh

API_URL="${1:-http://localhost:8000}"

echo "Load testing pagination endpoints"

# Test sequential pagination (navigate through pages)
echo -e "\n[Test 1] Sequential pagination load test"
cursor=""
page_count=0
max_pages=50

for i in $(seq 1 $max_pages); do
  if [ -z "$cursor" ]; then
    response=$(curl -s "$API_URL/api/market/prices?limit=50")
  else
    response=$(curl -s "$API_URL/api/market/prices?limit=50&cursor=$cursor")
  fi
  
  cursor=$(echo "$response" | jq -r '.pagination.next_cursor')
  has_more=$(echo "$response" | jq -r '.pagination.has_more')
  
  echo "Page $i: $(echo "$response" | jq '.data | length') items"
  
  if [ "$has_more" = "false" ]; then
    echo "Reached last page at page $i"
    break
  fi
done

# Test concurrent pagination requests
echo -e "\n[Test 2] Concurrent pagination requests"
parallel -j 10 "curl -s '$API_URL/api/market/prices?limit=20&cursor={}'" \
  ::: $(seq 0 9)

echo -e "\nLoad test completed"
```

---

## Performance Optimization

### 1. Database Indexing

**migrations/001_initial_schema.sql:**

```sql
-- Create indexes for cursor-based pagination
CREATE INDEX idx_prices_id ON prices(id DESC);
CREATE INDEX idx_prices_coin_timestamp ON prices(coin_id, timestamp DESC);
CREATE INDEX idx_assets_portfolio_id ON assets(portfolio_id, id DESC);
CREATE INDEX idx_articles_coin_published ON news_articles(coin_id, published_at DESC);

-- Composite indexes for filtering + ordering
CREATE INDEX idx_prices_coin_date ON prices(coin_id, timestamp DESC)
  WHERE timestamp > NOW() - INTERVAL '1 year';
```

### 2. Query Optimization

```python
# Good: Uses index efficiently
query = select(Price).where(
    Price.coin_id.in_(coin_list)
).order_by(Price.id.desc()).limit(50)

# Bad: ORDER BY on calculated column
query = select(Price).order_by(
    (Price.price * Price.quantity).desc()
).limit(50)

# Better: Pre-calculate or use indexed column
query = select(Price).order_by(
    Price.id.desc()
).limit(50)
```

### 3. Caching Pagination Results

```python
from shared.cache import cache

@router.get("/api/market/prices")
async def get_prices(
    coins: str = Query(None),
    cursor: str = Query(None),
    limit: int = Query(10),
    session: AsyncSession = Depends(get_session),
):
    # Generate cache key
    cache_key = f"prices:{coins}:{cursor}:{limit}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Fetch from DB
    page_data = await paginate(...)
    response = PaginatedResponse(...)
    
    # Cache for 5 minutes
    cache.set(cache_key, response, ttl=300)
    
    return response
```

---

## Deployment Checklist

- [ ] Pagination schemas added to shared/schemas.py
- [ ] Pagination utility functions in shared/pagination.py
- [ ] All required endpoints updated with cursor pagination
- [ ] OpenAPI documentation updated with pagination schemas
- [ ] Database indexes created for pagination columns
- [ ] Frontend hooks implemented for pagination
- [ ] Infinite scroll component tested
- [ ] Load tests for pagination endpoints pass
- [ ] Caching strategy for pagination results implemented
- [ ] E2E tests for pagination workflows added
- [ ] Documentation updated with pagination examples

---

**Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** January 2025
