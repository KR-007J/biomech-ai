"""
Integration APIs - Phase 5.3 Enterprise Features

Enables integration with third-party services and custom webhooks.
"""

import logging
import json
import asyncio
import hmac
import hashlib
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class IntegrationEventType(str, Enum):
    """Types of integration events"""
    ANALYSIS_COMPLETED = "analysis.completed"
    PROFILE_UPDATED = "profile.updated"
    SESSION_RECORDED = "session.recorded"
    ALERT_ISSUED = "alert.issued"
    EXPORT_READY = "export.ready"

class Integration:
    """Represents a third-party integration"""
    
    def __init__(self, id: str, name: str, provider: str, webhook_url: str, secret: str,
                 enabled: bool = True, events: list = None):
        self.id = id
        self.name = name
        self.provider = provider  # 'stripe', 'slack', 'zapier', 'custom', etc.
        self.webhook_url = webhook_url
        self.secret = secret
        self.enabled = enabled
        self.events = events or []
        self.created_at = datetime.now()
        self.last_triggered = None

class IntegrationManager:
    """Manage integrations and webhooks"""
    
    def __init__(self):
        self.integrations: Dict[str, Integration] = {}
        self.handlers: Dict[IntegrationEventType, list] = {}
    
    def register_integration(self, integration: Integration) -> str:
        """Register new integration"""
        self.integrations[integration.id] = integration
        logger.info(f"Integration registered: {integration.name}")
        return integration.id
    
    def trigger_event(self, event_type: IntegrationEventType, data: Dict[str, Any]):
        """Trigger event and notify all subscribed integrations"""
        asyncio.create_task(self._dispatch_event(event_type, data))
    
    async def _dispatch_event(self, event_type: IntegrationEventType, data: Dict[str, Any]):
        """Dispatch event to subscribed integrations"""
        tasks = []
        
        for integration in self.integrations.values():
            if not integration.enabled:
                continue
            
            if event_type.value not in integration.events:
                continue
            
            # Create webhook payload
            payload = {
                "event": event_type.value,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            # Sign payload
            signature = self._sign_payload(payload, integration.secret)
            
            # Send webhook
            task = self._send_webhook(
                integration.webhook_url,
                payload,
                signature
            )
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _sign_payload(self, payload: Dict[str, Any], secret: str) -> str:
        """Sign webhook payload with HMAC-SHA256"""
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _send_webhook(self, url: str, payload: Dict[str, Any], signature: str):
        """Send webhook to external service"""
        import aiohttp
        
        headers = {
            "Content-Type": "application/json",
            "X-Biomech-Signature": f"sha256={signature}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                    if resp.status >= 200 and resp.status < 300:
                        logger.debug(f"Webhook sent successfully to {url}")
                    else:
                        logger.warning(f"Webhook failed: {resp.status}")
        except asyncio.TimeoutError:
            logger.warning(f"Webhook timeout: {url}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
    
    def verify_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify incoming webhook signature"""
        expected_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, f"sha256={expected_signature}")

class StripeIntegration:
    """Stripe payment integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.info("Stripe integration initialized")
    
    def create_subscription(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Create Stripe subscription"""
        return {
            "subscription_id": "sub_xyz",
            "user_id": user_id,
            "plan": plan_id,
            "status": "active"
        }
    
    def handle_webhook(self, event: Dict[str, Any]) -> bool:
        """Handle Stripe webhook event"""
        event_type = event.get("type")
        
        if event_type == "customer.subscription.updated":
            logger.info("Subscription updated")
            return True
        elif event_type == "customer.subscription.deleted":
            logger.info("Subscription cancelled")
            return True
        elif event_type == "invoice.payment_succeeded":
            logger.info("Invoice paid")
            return True
        
        return False

class SlackIntegration:
    """Slack integration for notifications"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        logger.info("Slack integration initialized")
    
    async def send_notification(self, message: str, channel: str = "#general"):
        """Send Slack notification"""
        payload = {
            "channel": channel,
            "text": message,
            "username": "Biomech AI"
        }
        
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self.webhook_url, json=payload)
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")

class XlsxExporter:
    """Excel export integration"""
    
    @staticmethod
    def export_analyses(user_id: str, analyses: list) -> bytes:
        """Export analyses to Excel"""
        try:
            import openpyxl
            from openpyxl.utils import get_column_letter
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Analyses"
            
            # Headers
            headers = ["Date", "Exercise", "Performance", "Risk Level", "Notes"]
            ws.append(headers)
            
            # Data
            for i, analysis in enumerate(analyses, 2):
                summary = analysis.get("summary", {})
                risk = summary.get("risk", {})
                
                ws.append([
                    analysis.get("created_at", ""),
                    summary.get("exercise", ""),
                    summary.get("performance_score", ""),
                    risk.get("risk_level", ""),
                    analysis.get("notes", "")
                ])
            
            return wb.save
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return None

# Global integration manager
_integration_manager: Optional[IntegrationManager] = None

def get_integration_manager() -> IntegrationManager:
    """Get or create global integration manager"""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = IntegrationManager()
    return _integration_manager

logger.info("✅ Integration APIs initialized")
