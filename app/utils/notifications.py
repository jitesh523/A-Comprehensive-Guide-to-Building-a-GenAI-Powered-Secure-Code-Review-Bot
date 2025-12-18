"""
Notification utilities for Slack and Discord
"""
import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings
import asyncio

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications to Slack and Discord"""
    
    @staticmethod
    async def send_slack_notification(
        finding: Dict[str, Any],
        pr_url: str,
        max_retries: int = 3
    ) -> bool:
        """
        Send notification to Slack.
        
        Args:
            finding: Security finding details
            pr_url: URL to the pull request
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        if not settings.ENABLE_SLACK_NOTIFICATIONS or not settings.SLACK_WEBHOOK_URL:
            logger.debug("Slack notifications disabled")
            return False
        
        # Check severity filter
        if not NotificationService._should_notify(finding.get("severity")):
            logger.debug(f"Skipping notification for severity: {finding.get('severity')}")
            return False
        
        # Format Slack message
        severity_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        
        emoji = severity_emoji.get(finding.get("severity", "MEDIUM"), "⚠️")
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Security Issue Found"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{finding.get('severity')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Tool:*\n{finding.get('tool')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*File:*\n{finding.get('file')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Line:*\n{finding.get('line')}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{finding.get('description')}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{pr_url}|View Pull Request>"
                    }
                }
            ]
        }
        
        # Send with retry logic
        return await NotificationService._send_with_retry(
            settings.SLACK_WEBHOOK_URL,
            message,
            max_retries
        )
    
    @staticmethod
    async def send_discord_notification(
        finding: Dict[str, Any],
        pr_url: str,
        max_retries: int = 3
    ) -> bool:
        """
        Send notification to Discord.
        
        Args:
            finding: Security finding details
            pr_url: URL to the pull request
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        if not settings.ENABLE_DISCORD_NOTIFICATIONS or not settings.DISCORD_WEBHOOK_URL:
            logger.debug("Discord notifications disabled")
            return False
        
        # Check severity filter
        if not NotificationService._should_notify(finding.get("severity")):
            logger.debug(f"Skipping notification for severity: {finding.get('severity')}")
            return False
        
        # Format Discord message
        severity_colors = {
            "CRITICAL": 0xFF0000,  # Red
            "HIGH": 0xFF6600,      # Orange
            "MEDIUM": 0xFFFF00,    # Yellow
            "LOW": 0x00FF00        # Green
        }
        
        color = severity_colors.get(finding.get("severity", "MEDIUM"), 0xFFFF00)
        
        message = {
            "embeds": [
                {
                    "title": "🔒 Security Issue Found",
                    "color": color,
                    "fields": [
                        {
                            "name": "Severity",
                            "value": finding.get("severity"),
                            "inline": True
                        },
                        {
                            "name": "Tool",
                            "value": finding.get("tool"),
                            "inline": True
                        },
                        {
                            "name": "File",
                            "value": finding.get("file"),
                            "inline": False
                        },
                        {
                            "name": "Line",
                            "value": str(finding.get("line")),
                            "inline": True
                        },
                        {
                            "name": "Description",
                            "value": finding.get("description", "No description"),
                            "inline": False
                        }
                    ],
                    "url": pr_url
                }
            ]
        }
        
        # Send with retry logic
        return await NotificationService._send_with_retry(
            settings.DISCORD_WEBHOOK_URL,
            message,
            max_retries
        )
    
    @staticmethod
    def _should_notify(severity: str) -> bool:
        """Check if severity meets notification threshold"""
        severity_levels = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4
        }
        
        min_level = severity_levels.get(settings.NOTIFICATION_MIN_SEVERITY, 3)
        current_level = severity_levels.get(severity, 2)
        
        return current_level >= min_level
    
    @staticmethod
    async def _send_with_retry(
        webhook_url: str,
        payload: Dict[str, Any],
        max_retries: int
    ) -> bool:
        """
        Send webhook with exponential backoff retry.
        
        Args:
            webhook_url: Webhook URL
            payload: Message payload
            max_retries: Maximum retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries):
                try:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        timeout=10.0
                    )
                    
                    if response.status_code in [200, 204]:
                        logger.info(f"Notification sent successfully on attempt {attempt + 1}")
                        return True
                    else:
                        logger.warning(f"Notification failed with status {response.status_code}")
                
                except Exception as e:
                    logger.error(f"Notification attempt {attempt + 1} failed: {str(e)}")
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to send notification after {max_retries} attempts")
        return False
