"""
LLM Verifier using OpenAI with Structured Outputs
"""
from openai import OpenAI
from app.llm.models import VerificationResult, VerificationRequest
from app.llm.prompts import VerificationPrompts
from app.config import settings
from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class LLMVerifier:
    """
    Verifies SAST findings using OpenAI with structured outputs.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM verifier.
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        
        logger.info(f"Initialized LLM Verifier with model: {self.model}")
    
    async def verify_finding(
        self,
        finding: Dict[str, Any],
        include_few_shot: bool = True
    ) -> VerificationResult:
        """
        Verify a single SAST finding using LLM.
        
        Args:
            finding: Finding dictionary with context
            include_few_shot: Include few-shot examples in prompt
            
        Returns:
            VerificationResult with decision and reasoning
        """
        try:
            # Extract context
            context = finding.get('context', {})
            
            # Create verification request
            request = VerificationRequest(
                sast_tool=finding.get('tool', 'unknown'),
                rule_id=finding.get('rule_id', 'unknown'),
                severity=finding.get('severity', 'unknown'),
                description=finding.get('description', ''),
                code_context=context.get('context_code', finding.get('code', '')),
                function_name=context.get('function_name'),
                class_name=context.get('class_name'),
                file_path=finding.get('file', ''),
                line_number=finding.get('line', 0)
            )
            
            # Create prompt
            user_prompt = VerificationPrompts.create_verification_prompt(
                sast_tool=request.sast_tool,
                rule_id=request.rule_id,
                severity=request.severity,
                description=request.description,
                code_context=request.code_context,
                function_name=request.function_name,
                class_name=request.class_name,
                file_path=request.file_path,
                line_number=request.line_number
            )
            
            # Add few-shot examples if requested
            if include_few_shot:
                few_shot = VerificationPrompts.create_few_shot_examples()
                user_prompt = few_shot + "\n\n---\n\n" + user_prompt
            
            # Call OpenAI with structured outputs
            logger.info(f"Verifying finding: {request.rule_id} at {request.file_path}:{request.line_number}")
            
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": VerificationPrompts.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                response_format=VerificationResult,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract structured result
            result = response.choices[0].message.parsed
            
            logger.info(
                f"Verification complete: {result.decision} "
                f"(confidence: {result.confidence:.2f})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"LLM verification failed: {str(e)}")
            # Return uncertain result on error
            return VerificationResult(
                decision="uncertain",
                confidence=0.0,
                reasoning=f"Verification failed due to error: {str(e)}"
            )
    
    async def verify_batch(
        self,
        findings: list,
        max_concurrent: int = 5
    ) -> list:
        """
        Verify multiple findings concurrently.
        
        Args:
            findings: List of findings to verify
            max_concurrent: Maximum concurrent API calls
            
        Returns:
            List of VerificationResults
        """
        import asyncio
        
        # Create tasks
        tasks = []
        for finding in findings:
            task = self.verify_finding(finding)
            tasks.append(task)
        
        # Execute with concurrency limit
        results = []
        for i in range(0, len(tasks), max_concurrent):
            batch = tasks[i:i + max_concurrent]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
        
        return results
    
    def get_token_count(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4
    
    def validate_api_key(self) -> bool:
        """
        Validate that API key is working.
        
        Returns:
            True if API key is valid
        """
        try:
            # Make a minimal API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False
