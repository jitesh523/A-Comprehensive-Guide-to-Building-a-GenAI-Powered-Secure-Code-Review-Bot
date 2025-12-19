"""
Cache manager for LLM responses and scan results
"""
import redis
import json
import hashlib
from typing import Optional, Any, Dict
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache for LLM responses and scan results"""
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("Cache manager initialized successfully")
        except Exception as e:
            logger.warning(f"Redis not available, caching disabled: {str(e)}")
            self.redis_client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, data: str) -> str:
        """Generate cache key from data hash"""
        data_hash = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"{prefix}:{data_hash}"
    
    def get_llm_response(self, code_snippet: str, finding_context: Dict) -> Optional[Dict]:
        """
        Get cached LLM response for code snippet.
        
        Args:
            code_snippet: Code to verify
            finding_context: Finding metadata
            
        Returns:
            Cached LLM response or None
        """
        if not self.enabled:
            return None
        
        try:
            # Create cache key from code + rule_id
            cache_data = f"{code_snippet}:{finding_context.get('rule_id', '')}"
            key = self._generate_key("llm", cache_data)
            
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"Cache HIT for LLM response: {key}")
                return json.loads(cached)
            
            logger.debug(f"Cache MISS for LLM response: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set_llm_response(
        self,
        code_snippet: str,
        finding_context: Dict,
        llm_response: Dict,
        ttl: int = 86400  # 24 hours
    ):
        """
        Cache LLM response.
        
        Args:
            code_snippet: Code that was verified
            finding_context: Finding metadata
            llm_response: LLM verification result
            ttl: Time to live in seconds (default: 24 hours)
        """
        if not self.enabled:
            return
        
        try:
            cache_data = f"{code_snippet}:{finding_context.get('rule_id', '')}"
            key = self._generate_key("llm", cache_data)
            
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(llm_response)
            )
            logger.debug(f"Cached LLM response: {key}")
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    def get_scan_results(self, file_path: str, file_hash: str) -> Optional[list]:
        """
        Get cached scan results for a file.
        
        Args:
            file_path: Path to file
            file_hash: SHA256 hash of file content
            
        Returns:
            Cached scan results or None
        """
        if not self.enabled:
            return None
        
        try:
            key = self._generate_key("scan", f"{file_path}:{file_hash}")
            cached = self.redis_client.get(key)
            
            if cached:
                logger.info(f"Cache HIT for scan results: {file_path}")
                return json.loads(cached)
            
            logger.debug(f"Cache MISS for scan results: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set_scan_results(
        self,
        file_path: str,
        file_hash: str,
        scan_results: list,
        ttl: int = 3600  # 1 hour
    ):
        """
        Cache scan results for a file.
        
        Args:
            file_path: Path to file
            file_hash: SHA256 hash of file content
            scan_results: SAST scan results
            ttl: Time to live in seconds (default: 1 hour)
        """
        if not self.enabled:
            return
        
        try:
            key = self._generate_key("scan", f"{file_path}:{file_hash}")
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(scan_results)
            )
            logger.debug(f"Cached scan results: {file_path}")
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    def invalidate_file(self, file_path: str):
        """
        Invalidate all cache entries for a file.
        
        Args:
            file_path: Path to file
        """
        if not self.enabled:
            return
        
        try:
            # Find all keys matching the file path
            pattern = f"scan:*{file_path}*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for {file_path}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
    
    def clear_all(self):
        """Clear all cache entries (use with caution!)"""
        if not self.enabled:
            return
        
        try:
            self.redis_client.flushdb()
            logger.warning("Cleared all cache entries")
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "total_keys": self.redis_client.dbsize(),
                "memory_used": info.get("used_memory_human", "unknown"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {"enabled": True, "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)


# Global cache instance
cache_manager = CacheManager()
