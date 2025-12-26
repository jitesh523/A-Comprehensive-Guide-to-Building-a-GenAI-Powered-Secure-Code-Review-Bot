"""
LLM Cost Tracking and Budgeting

This module tracks LLM API costs and enforces budget limits.
"""
from datetime import datetime, timedelta
from typing import Any
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CostEntry(BaseModel):
    """Single cost entry"""
    timestamp: datetime
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    scan_id: str | None = None
    finding_id: str | None = None


class CostTracker:
    """
    Track LLM API costs and enforce budgets.
    """
    
    def __init__(self, redis_client: Any | None = None):
        """
        Initialize cost tracker.
        
        Args:
            redis_client: Redis client for persistence
        """
        self.redis_client = redis_client
        self.monthly_budget_usd = 1000.0  # Default $1000/month
    
    async def record_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        scan_id: str | None = None,
        finding_id: str | None = None
    ):
        """
        Record a cost entry.
        
        Args:
            provider: LLM provider name
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Cost in USD
            scan_id: Optional scan ID
            finding_id: Optional finding ID
        """
        entry = CostEntry(
            timestamp=datetime.utcnow(),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            scan_id=scan_id,
            finding_id=finding_id
        )
        
        if self.redis_client:
            try:
                # Store in Redis sorted set by timestamp
                key = f"llm_costs:{entry.timestamp.strftime('%Y-%m')}"
                score = entry.timestamp.timestamp()
                value = entry.model_dump_json()
                
                await self.redis_client.zadd(key, {value: score})
                
                # Set expiry to 90 days
                await self.redis_client.expire(key, 90 * 24 * 3600)
                
                logger.info(
                    f"Recorded cost: ${cost_usd:.4f} for {provider}/{model} "
                    f"({input_tokens + output_tokens} tokens)"
                )
            
            except Exception as e:
                logger.error(f"Failed to record cost: {str(e)}")
    
    async def get_costs(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider: str | None = None
    ) -> list[CostEntry]:
        """
        Get cost entries within a date range.
        
        Args:
            start_date: Start date (default: beginning of current month)
            end_date: End date (default: now)
            provider: Optional provider filter
            
        Returns:
            List of CostEntry objects
        """
        if not self.redis_client:
            return []
        
        # Default to current month
        if not start_date:
            now = datetime.utcnow()
            start_date = datetime(now.year, now.month, 1)
        if not end_date:
            end_date = datetime.utcnow()
        
        try:
            entries = []
            
            # Get all months in range
            current = start_date.replace(day=1)
            while current <= end_date:
                key = f"llm_costs:{current.strftime('%Y-%m')}"
                
                # Get entries from Redis
                start_score = start_date.timestamp()
                end_score = end_date.timestamp()
                
                results = await self.redis_client.zrangebyscore(
                    key, start_score, end_score
                )
                
                for result in results:
                    entry = CostEntry.model_validate_json(result)
                    if not provider or entry.provider == provider:
                        entries.append(entry)
                
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            
            return entries
        
        except Exception as e:
            logger.error(f"Failed to get costs: {str(e)}")
            return []
    
    async def get_total_cost(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider: str | None = None
    ) -> float:
        """
        Get total cost within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            provider: Optional provider filter
            
        Returns:
            Total cost in USD
        """
        entries = await self.get_costs(start_date, end_date, provider)
        return sum(entry.cost_usd for entry in entries)
    
    async def get_monthly_cost(self, year: int | None = None, month: int | None = None) -> float:
        """
        Get total cost for a specific month.
        
        Args:
            year: Year (default: current year)
            month: Month (default: current month)
            
        Returns:
            Total cost in USD
        """
        now = datetime.utcnow()
        year = year or now.year
        month = month or now.month
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        return await self.get_total_cost(start_date, end_date)
    
    async def check_budget(self) -> tuple[bool, float, float]:
        """
        Check if current month's spending is within budget.
        
        Returns:
            Tuple of (within_budget, current_cost, budget_limit)
        """
        current_cost = await self.get_monthly_cost()
        within_budget = current_cost <= self.monthly_budget_usd
        
        if not within_budget:
            logger.warning(
                f"Budget exceeded: ${current_cost:.2f} / ${self.monthly_budget_usd:.2f}"
            )
        
        return within_budget, current_cost, self.monthly_budget_usd
    
    async def get_cost_breakdown(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Get detailed cost breakdown.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dict with cost breakdown by provider and model
        """
        entries = await self.get_costs(start_date, end_date)
        
        breakdown = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "by_provider": {},
            "by_model": {}
        }
        
        for entry in entries:
            # Total
            breakdown["total_cost"] += entry.cost_usd
            breakdown["total_tokens"] += entry.input_tokens + entry.output_tokens
            
            # By provider
            if entry.provider not in breakdown["by_provider"]:
                breakdown["by_provider"][entry.provider] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "requests": 0
                }
            breakdown["by_provider"][entry.provider]["cost"] += entry.cost_usd
            breakdown["by_provider"][entry.provider]["tokens"] += entry.input_tokens + entry.output_tokens
            breakdown["by_provider"][entry.provider]["requests"] += 1
            
            # By model
            if entry.model not in breakdown["by_model"]:
                breakdown["by_model"][entry.model] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "requests": 0
                }
            breakdown["by_model"][entry.model]["cost"] += entry.cost_usd
            breakdown["by_model"][entry.model]["tokens"] += entry.input_tokens + entry.output_tokens
            breakdown["by_model"][entry.model]["requests"] += 1
        
        return breakdown


# Global cost tracker instance
_cost_tracker_instance: CostTracker | None = None


def get_cost_tracker(redis_client: Any | None = None) -> CostTracker:
    """
    Get or create global cost tracker instance.
    
    Args:
        redis_client: Redis client instance
        
    Returns:
        CostTracker instance
    """
    global _cost_tracker_instance
    
    if _cost_tracker_instance is None:
        _cost_tracker_instance = CostTracker(redis_client)
    
    return _cost_tracker_instance
