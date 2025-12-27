"""
Rate Limiter for API endpoints

Implements token bucket algorithm for rate limiting.
"""
import time
from typing import Any
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: int, per: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            rate: Number of requests allowed
            per: Time period in seconds (default: 60)
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """
        Try to acquire a token.
        
        Returns:
            True if request is allowed, False if rate limited
        """
        async with self.lock:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current
            
            # Add tokens based on time passed
            self.allowance += time_passed * (self.rate / self.per)
            
            # Cap at maximum rate
            if self.allowance > self.rate:
                self.allowance = self.rate
            
            # Check if we have tokens
            if self.allowance < 1.0:
                return False
            else:
                self.allowance -= 1.0
                return True
    
    async def wait(self):
        """Wait until a token is available"""
        while not await self.acquire():
            await asyncio.sleep(0.1)


class RateLimitManager:
    """Manage multiple rate limiters"""
    
    def __init__(self):
        self.limiters: dict[str, RateLimiter] = {}
    
    def get_limiter(self, key: str, rate: int, per: int = 60) -> RateLimiter:
        """
        Get or create a rate limiter for a key.
        
        Args:
            key: Identifier for the limiter
            rate: Number of requests allowed
            per: Time period in seconds
            
        Returns:
            RateLimiter instance
        """
        if key not in self.limiters:
            self.limiters[key] = RateLimiter(rate, per)
        return self.limiters[key]
    
    async def check_limit(self, key: str, rate: int, per: int = 60) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Identifier for the limiter
            rate: Number of requests allowed
            per: Time period in seconds
            
        Returns:
            True if allowed, False if rate limited
        """
        limiter = self.get_limiter(key, rate, per)
        return await limiter.acquire()


# Global rate limit manager
rate_limit_manager = RateLimitManager()


def rate_limit(rate: int, per: int = 60, key_func: Any = None):
    """
    Decorator to add rate limiting to a function.
    
    Args:
        rate: Number of requests allowed
        per: Time period in seconds
        key_func: Function to generate rate limit key (default: function name)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = func.__name__
            
            # Check rate limit
            limiter = rate_limit_manager.get_limiter(key, rate, per)
            if not await limiter.acquire():
                raise Exception(f"Rate limit exceeded for {key}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
