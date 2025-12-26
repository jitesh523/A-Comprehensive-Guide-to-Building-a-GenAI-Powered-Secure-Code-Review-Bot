"""
LLM Response Caching System

This module implements semantic caching for LLM responses to reduce costs
and improve response times.
"""
import hashlib
import json
from typing import Any
from datetime import datetime, timedelta
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class LLMCache:
    """
    Semantic cache for LLM responses using Redis.
    """
    
    def __init__(self, redis_client: Any | None = None):
        """
        Initialize LLM cache.
        
        Args:
            redis_client: Redis client instance (optional)
        """
        self.redis_client = redis_client
        self.ttl = settings.CACHE_TTL_LLM  # 24 hours by default
        self.enabled = settings.ENABLE_CACHING
    
    def _get_cache_key(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float
    ) -> str:
        """
        Generate cache key from messages and parameters.
        
        Args:
            messages: List of message dicts
            model: Model name
            temperature: Temperature parameter
            
        Returns:
            Cache key string
        """
        # Create deterministic string from inputs
        cache_input = {
            "messages": messages,
            "model": model,
            "temperature": round(temperature, 2)  # Round to avoid float precision issues
        }
        
        # Hash the input
        input_str = json.dumps(cache_input, sort_keys=True)
        cache_hash = hashlib.sha256(input_str.encode()).hexdigest()
        
        return f"llm_cache:{model}:{cache_hash}"
    
    async def get(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float
    ) -> dict[str, Any] | None:
        """
        Get cached response if available.
        
        Args:
            messages: List of message dicts
            model: Model name
            temperature: Temperature parameter
            
        Returns:
            Cached response dict or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(messages, model, temperature)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for key: {cache_key[:16]}...")
                return json.loads(cached_data)
            
            logger.debug(f"Cache miss for key: {cache_key[:16]}...")
            return None
        
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        response: dict[str, Any]
    ):
        """
        Cache an LLM response.
        
        Args:
            messages: List of message dicts
            model: Model name
            temperature: Temperature parameter
            response: Response dict to cache
        """
        if not self.enabled or not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(messages, model, temperature)
            
            # Add metadata
            cache_data = {
                **response,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_key": cache_key
            }
            
            # Store in Redis with TTL
            await self.redis_client.setex(
                cache_key,
                self.ttl,
                json.dumps(cache_data)
            )
            
            logger.info(f"Cached response for key: {cache_key[:16]}...")
        
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    async def invalidate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float
    ):
        """
        Invalidate a cached response.
        
        Args:
            messages: List of message dicts
            model: Model name
            temperature: Temperature parameter
        """
        if not self.enabled or not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(messages, model, temperature)
            await self.redis_client.delete(cache_key)
            logger.info(f"Invalidated cache for key: {cache_key[:16]}...")
        
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
    
    async def clear_all(self):
        """Clear all LLM cache entries."""
        if not self.enabled or not self.redis_client:
            return
        
        try:
            # Find all llm_cache keys
            keys = []
            async for key in self.redis_client.scan_iter(match="llm_cache:*"):
                keys.append(key)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
        
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
    
    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            # Count cache entries
            count = 0
            async for _ in self.redis_client.scan_iter(match="llm_cache:*"):
                count += 1
            
            return {
                "enabled": True,
                "total_entries": count,
                "ttl_seconds": self.ttl
            }
        
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {"enabled": True, "error": str(e)}


# Global cache instance
_cache_instance: LLMCache | None = None


def get_llm_cache(redis_client: Any | None = None) -> LLMCache:
    """
    Get or create global LLM cache instance.
    
    Args:
        redis_client: Redis client instance
        
    Returns:
        LLMCache instance
    """
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = LLMCache(redis_client)
    
    return _cache_instance
