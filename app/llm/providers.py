"""
Multi-LLM Provider Support

This module provides a unified interface for multiple LLM providers:
- OpenAI (GPT-4, GPT-4o)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Google (Gemini Pro, Gemini 1.5 Pro)
"""
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Unified LLM response format"""
    content: str
    model: str
    provider: str
    tokens_used: int
    cost_usd: float


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.provider_name = self.__class__.__name__.replace("Provider", "").lower()
    
    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        response_format: type[BaseModel] | None = None
    ) -> LLMResponse:
        """
        Generate completion from messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Optional Pydantic model for structured output
            
        Returns:
            LLMResponse with content and metadata
        """
        pass
    
    @abstractmethod
    def get_cost_per_token(self) -> tuple[float, float]:
        """
        Get cost per token for this model.
        
        Returns:
            Tuple of (input_cost_per_1k, output_cost_per_1k)
        """
        pass
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD"""
        input_cost, output_cost = self.get_cost_per_token()
        return (input_tokens * input_cost / 1000) + (output_tokens * output_cost / 1000)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(api_key, model)
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        response_format: type[BaseModel] | None = None
    ) -> LLMResponse:
        """Generate completion using OpenAI"""
        try:
            if response_format:
                # Use structured outputs
                response = await self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format
                )
                content = response.choices[0].message.parsed.model_dump_json()
            else:
                # Regular completion
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content
            
            # Calculate cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self.calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider="openai",
                tokens_used=input_tokens + output_tokens,
                cost_usd=cost
            )
        
        except Exception as e:
            logger.error(f"OpenAI completion failed: {str(e)}")
            raise
    
    def get_cost_per_token(self) -> tuple[float, float]:
        """Get OpenAI pricing"""
        pricing = {
            "gpt-4o": (0.0025, 0.010),  # $2.50 / $10 per 1M tokens
            "gpt-4o-mini": (0.00015, 0.0006),  # $0.15 / $0.60 per 1M tokens
            "gpt-4-turbo": (0.010, 0.030),  # $10 / $30 per 1M tokens
            "gpt-4": (0.030, 0.060),  # $30 / $60 per 1M tokens
        }
        return pricing.get(self.model, (0.0025, 0.010))


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(api_key, model)
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        response_format: type[BaseModel] | None = None
    ) -> LLMResponse:
        """Generate completion using Anthropic Claude"""
        try:
            # Extract system message if present
            system_message = None
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg)
            
            # Call Anthropic API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message if system_message else "",
                messages=user_messages
            )
            
            content = response.content[0].text
            
            # If structured output requested, parse with Pydantic
            if response_format:
                import json
                try:
                    parsed = response_format.model_validate_json(content)
                    content = parsed.model_dump_json()
                except Exception as e:
                    logger.warning(f"Failed to parse structured output: {e}")
            
            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self.calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider="anthropic",
                tokens_used=input_tokens + output_tokens,
                cost_usd=cost
            )
        
        except Exception as e:
            logger.error(f"Anthropic completion failed: {str(e)}")
            raise
    
    def get_cost_per_token(self) -> tuple[float, float]:
        """Get Anthropic pricing"""
        pricing = {
            "claude-3-5-sonnet-20241022": (0.003, 0.015),  # $3 / $15 per 1M tokens
            "claude-3-opus-20240229": (0.015, 0.075),  # $15 / $75 per 1M tokens
            "claude-3-sonnet-20240229": (0.003, 0.015),  # $3 / $15 per 1M tokens
            "claude-3-haiku-20240307": (0.00025, 0.00125),  # $0.25 / $1.25 per 1M tokens
        }
        return pricing.get(self.model, (0.003, 0.015))


class GoogleProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        super().__init__(api_key, model)
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
    
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2000,
        response_format: type[BaseModel] | None = None
    ) -> LLMResponse:
        """Generate completion using Google Gemini"""
        try:
            # Convert messages to Gemini format
            # Gemini uses a simpler format: just the conversation history
            conversation = []
            for msg in messages:
                role = "user" if msg["role"] in ["user", "system"] else "model"
                conversation.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
            
            # Generate response
            response = await self.client.generate_content_async(
                conversation,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
            
            content = response.text
            
            # If structured output requested, parse with Pydantic
            if response_format:
                import json
                try:
                    parsed = response_format.model_validate_json(content)
                    content = parsed.model_dump_json()
                except Exception as e:
                    logger.warning(f"Failed to parse structured output: {e}")
            
            # Estimate tokens (Gemini doesn't always provide token counts)
            input_tokens = sum(len(msg["content"]) // 4 for msg in messages)
            output_tokens = len(content) // 4
            cost = self.calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider="google",
                tokens_used=input_tokens + output_tokens,
                cost_usd=cost
            )
        
        except Exception as e:
            logger.error(f"Google completion failed: {str(e)}")
            raise
    
    def get_cost_per_token(self) -> tuple[float, float]:
        """Get Google Gemini pricing"""
        pricing = {
            "gemini-1.5-pro": (0.00125, 0.005),  # $1.25 / $5 per 1M tokens
            "gemini-1.5-flash": (0.000075, 0.0003),  # $0.075 / $0.30 per 1M tokens
            "gemini-pro": (0.0005, 0.0015),  # $0.50 / $1.50 per 1M tokens
        }
        return pricing.get(self.model, (0.00125, 0.005))


class LLMProviderFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create_provider(
        provider: str,
        api_key: str,
        model: str | None = None
    ) -> LLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider: Provider name ('openai', 'anthropic', 'google')
            api_key: API key for the provider
            model: Optional model name (uses default if not specified)
            
        Returns:
            LLMProvider instance
        """
        providers = {
            "openai": (OpenAIProvider, "gpt-4o"),
            "anthropic": (AnthropicProvider, "claude-3-5-sonnet-20241022"),
            "google": (GoogleProvider, "gemini-1.5-pro"),
        }
        
        if provider not in providers:
            raise ValueError(f"Unknown provider: {provider}. Choose from: {list(providers.keys())}")
        
        provider_class, default_model = providers[provider]
        model = model or default_model
        
        return provider_class(api_key=api_key, model=model)
