"""
Modular Notification Forwarders

This module provides a plugin-based system for forwarding notifications
to external providers like ntfy.sh, email, SMS, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import httpx
import logging

logger = logging.getLogger(__name__)


class NotificationPriority(str, Enum):
    MIN = "min"
    LOW = "low"
    DEFAULT = "default"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationPayload:
    """Standardized notification payload structure."""
    target: str  # e.g., topic name, email address, phone number
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.DEFAULT
    tags: Optional[list] = None
    click_url: Optional[str] = None
    attach_url: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


@dataclass
class ForwardResult:
    """Result of a forwarding attempt."""
    success: bool
    provider: str
    target: str
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class BaseForwarder(ABC):
    """Abstract base class for all notification forwarders."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass

    @abstractmethod
    async def forward(self, payload: NotificationPayload, config: Dict[str, Any]) -> ForwardResult:
        """
        Forward a notification to the external provider.

        Args:
            payload: The notification payload to send
            config: Provider-specific configuration (e.g., base URLs, API keys)

        Returns:
            ForwardResult indicating success or failure
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the provider configuration."""
        pass


class NtfyForwarder(BaseForwarder):
    """Forwarder for ntfy.sh notifications."""

    DEFAULT_BASE_URL = "https://ntfy.sh"

    @property
    def provider_name(self) -> str:
        return "ntfy"

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate ntfy configuration."""
        # base_url is optional (defaults to ntfy.sh)
        return True

    async def forward(self, payload: NotificationPayload, config: Dict[str, Any]) -> ForwardResult:
        """Forward notification to ntfy server."""
        base_url = config.get("base_url", self.DEFAULT_BASE_URL).rstrip("/")
        topic = payload.target
        url = f"{base_url}/{topic}"

        # Build headers for ntfy
        headers = {
            "Title": payload.title,
            "Priority": self._map_priority(payload.priority),
        }

        if payload.tags:
            headers["Tags"] = ",".join(payload.tags)

        if payload.click_url:
            headers["Click"] = payload.click_url

        if payload.attach_url:
            headers["Attach"] = payload.attach_url

        # Add auth token if provided
        auth_token = config.get("auth_token")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    content=payload.message,
                    headers=headers
                )

                success = response.status_code in (200, 201)
                response_data = None
                try:
                    response_data = response.json()
                except:
                    response_data = {"raw": response.text}

                return ForwardResult(
                    success=success,
                    provider=self.provider_name,
                    target=topic,
                    status_code=response.status_code,
                    response_data=response_data,
                    error_message=None if success else f"HTTP {response.status_code}"
                )

        except httpx.TimeoutException:
            logger.error(f"Timeout forwarding to ntfy: {url}")
            return ForwardResult(
                success=False,
                provider=self.provider_name,
                target=topic,
                error_message="Request timeout"
            )
        except Exception as e:
            logger.error(f"Error forwarding to ntfy: {e}")
            return ForwardResult(
                success=False,
                provider=self.provider_name,
                target=topic,
                error_message=str(e)
            )

    def _map_priority(self, priority: NotificationPriority) -> str:
        """Map our priority enum to ntfy priority values."""
        priority_map = {
            NotificationPriority.MIN: "1",
            NotificationPriority.LOW: "2",
            NotificationPriority.DEFAULT: "3",
            NotificationPriority.HIGH: "4",
            NotificationPriority.URGENT: "5",
        }
        return priority_map.get(priority, "3")


class EmailForwarder(BaseForwarder):
    """Placeholder forwarder for email notifications (future implementation)."""

    @property
    def provider_name(self) -> str:
        return "email"

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate email configuration."""
        required = ["smtp_host", "smtp_port", "sender_email"]
        return all(key in config for key in required)

    async def forward(self, payload: NotificationPayload, config: Dict[str, Any]) -> ForwardResult:
        """Forward notification via email."""
        # TODO: Implement actual email sending
        logger.warning("Email forwarder not yet implemented")
        return ForwardResult(
            success=False,
            provider=self.provider_name,
            target=payload.target,
            error_message="Email forwarder not yet implemented"
        )


class SMSForwarder(BaseForwarder):
    """Placeholder forwarder for SMS notifications (future implementation)."""

    @property
    def provider_name(self) -> str:
        return "sms"

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate SMS configuration."""
        required = ["api_key", "sender_number"]
        return all(key in config for key in required)

    async def forward(self, payload: NotificationPayload, config: Dict[str, Any]) -> ForwardResult:
        """Forward notification via SMS."""
        # TODO: Implement actual SMS sending (e.g., via Twilio)
        logger.warning("SMS forwarder not yet implemented")
        return ForwardResult(
            success=False,
            provider=self.provider_name,
            target=payload.target,
            error_message="SMS forwarder not yet implemented"
        )


class NotificationRouter:
    """
    Routes notifications to the appropriate forwarder based on provider type.
    """

    def __init__(self):
        self._forwarders: Dict[str, BaseForwarder] = {}
        self._register_default_forwarders()

    def _register_default_forwarders(self):
        """Register built-in forwarders."""
        self.register_forwarder(NtfyForwarder())
        self.register_forwarder(EmailForwarder())
        self.register_forwarder(SMSForwarder())

    def register_forwarder(self, forwarder: BaseForwarder):
        """Register a new forwarder."""
        self._forwarders[forwarder.provider_name] = forwarder
        logger.info(f"Registered forwarder: {forwarder.provider_name}")

    def get_forwarder(self, provider: str) -> Optional[BaseForwarder]:
        """Get a forwarder by provider name."""
        return self._forwarders.get(provider)

    def list_providers(self) -> list:
        """List all registered provider names."""
        return list(self._forwarders.keys())

    async def route(
        self,
        provider: str,
        payload: NotificationPayload,
        config: Dict[str, Any]
    ) -> ForwardResult:
        """
        Route a notification to the appropriate forwarder.

        Args:
            provider: The provider name (e.g., "ntfy", "email")
            payload: The notification payload
            config: Provider-specific configuration

        Returns:
            ForwardResult indicating success or failure
        """
        forwarder = self.get_forwarder(provider)

        if not forwarder:
            logger.error(f"Unknown notification provider: {provider}")
            return ForwardResult(
                success=False,
                provider=provider,
                target=payload.target,
                error_message=f"Unknown provider: {provider}"
            )

        if not forwarder.validate_config(config):
            logger.error(f"Invalid configuration for provider: {provider}")
            return ForwardResult(
                success=False,
                provider=provider,
                target=payload.target,
                error_message=f"Invalid configuration for {provider}"
            )

        return await forwarder.forward(payload, config)


# Global router instance
notification_router = NotificationRouter()

