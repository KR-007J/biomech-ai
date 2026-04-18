"""
TIER 5: Multi-Tenancy System
Provides tenant isolation, resource quotas, and billing integration
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class PlanType(str, Enum):
    """Subscription plan types"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    INACTIVE = "inactive"


@dataclass
class PlanQuota:
    """Resource quotas for a plan"""
    max_users: int
    max_storage_gb: int
    max_api_calls_monthly: int
    max_concurrent_sessions: int
    max_persons_per_session: int
    features: List[str]
    support_tier: str
    
    def to_dict(self) -> Dict:
        return {
            "max_users": self.max_users,
            "max_storage_gb": self.max_storage_gb,
            "max_api_calls_monthly": self.max_api_calls_monthly,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "max_persons_per_session": self.max_persons_per_session,
            "features": self.features,
            "support_tier": self.support_tier
        }


@dataclass
class Tenant:
    """Tenant (organization) in the system"""
    tenant_id: str
    name: str
    owner_id: str
    plan: PlanType
    status: TenantStatus
    created_at: datetime
    subscription_expires_at: datetime
    settings: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def is_trial_expired(self) -> bool:
        return self.plan == PlanType.FREE and datetime.utcnow() > self.subscription_expires_at
    
    def to_dict(self) -> Dict:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "owner_id": self.owner_id,
            "plan": self.plan.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "subscription_expires_at": self.subscription_expires_at.isoformat()
        }


@dataclass
class TenantUsage:
    """Track tenant resource usage"""
    tenant_id: str
    current_users: int
    storage_used_gb: float
    api_calls_this_month: int
    concurrent_sessions: int
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "tenant_id": self.tenant_id,
            "current_users": self.current_users,
            "storage_used_gb": self.storage_used_gb,
            "api_calls_this_month": self.api_calls_this_month,
            "concurrent_sessions": self.concurrent_sessions,
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class BillingRecord:
    """Billing record for tenant"""
    record_id: str
    tenant_id: str
    billing_period_start: datetime
    billing_period_end: datetime
    amount_cents: int
    status: str  # "pending", "paid", "overdue"
    invoice_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# PLAN DEFINITIONS
# ============================================================================

PLAN_QUOTAS = {
    PlanType.FREE: PlanQuota(
        max_users=1,
        max_storage_gb=10,
        max_api_calls_monthly=1000,
        max_concurrent_sessions=1,
        max_persons_per_session=1,
        features=["basic_analysis", "mobile_app"],
        support_tier="community"
    ),
    PlanType.STARTER: PlanQuota(
        max_users=5,
        max_storage_gb=100,
        max_api_calls_monthly=50000,
        max_concurrent_sessions=5,
        max_persons_per_session=3,
        features=["basic_analysis", "mobile_app", "multi_person", "reports"],
        support_tier="email"
    ),
    PlanType.PROFESSIONAL: PlanQuota(
        max_users=50,
        max_storage_gb=1000,
        max_api_calls_monthly=500000,
        max_concurrent_sessions=20,
        max_persons_per_session=10,
        features=["all", "ar_vr", "advanced_analytics", "api_access", "custom_workflows"],
        support_tier="priority"
    ),
    PlanType.ENTERPRISE: PlanQuota(
        max_users=10000,
        max_storage_gb=100000,
        max_api_calls_monthly=50000000,
        max_concurrent_sessions=1000,
        max_persons_per_session=100,
        features=["all", "sso", "multi_tenancy", "custom_integration", "dedicated_support"],
        support_tier="dedicated"
    )
}


# ============================================================================
# MULTI-TENANCY MANAGER
# ============================================================================

class MultiTenancyManager:
    """
    Manages multi-tenant system with isolation and quotas
    """
    
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.usage: Dict[str, TenantUsage] = {}
        self.billing_records: Dict[str, List[BillingRecord]] = {}
        self.tenant_data: Dict[str, Dict] = {}  # Isolated data per tenant
        logger.info("Multi-tenancy manager initialized")
    
    async def create_tenant(self, owner_id: str, name: str, plan: str = "free") -> Dict[str, Any]:
        """
        Create new tenant
        
        Args:
            owner_id: Tenant owner user ID
            name: Tenant name
            plan: Plan type
            
        Returns:
            Tenant details
        """
        try:
            tenant_id = str(uuid.uuid4())
            plan_type = PlanType(plan)
            
            # Calculate subscription expiration
            if plan_type == PlanType.FREE:
                subscription_expires = datetime.utcnow() + timedelta(days=30)  # 30-day trial
            else:
                subscription_expires = datetime.utcnow() + timedelta(days=365)  # 1 year
            
            tenant = Tenant(
                tenant_id=tenant_id,
                name=name,
                owner_id=owner_id,
                plan=plan_type,
                status=TenantStatus.TRIAL if plan_type == PlanType.FREE else TenantStatus.ACTIVE,
                created_at=datetime.utcnow(),
                subscription_expires_at=subscription_expires
            )
            
            self.tenants[tenant_id] = tenant
            self.usage[tenant_id] = TenantUsage(tenant_id=tenant_id)
            self.tenant_data[tenant_id] = {}
            
            logger.info(f"Tenant created: {tenant_id} ({name})")
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "tenant": tenant.to_dict(),
                "quota": PLAN_QUOTAS[plan_type].to_dict()
            }
        except Exception as e:
            logger.error(f"Tenant creation failed: {str(e)}")
            return {"error": str(e)}
    
    async def upgrade_plan(self, tenant_id: str, new_plan: str) -> Dict[str, Any]:
        """
        Upgrade tenant plan
        
        Args:
            tenant_id: Tenant ID
            new_plan: New plan type
            
        Returns:
            Updated tenant details
        """
        try:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return {"error": "Tenant not found"}
            
            old_plan = tenant.plan
            tenant.plan = PlanType(new_plan)
            tenant.subscription_expires_at = datetime.utcnow() + timedelta(days=365)
            
            logger.info(f"Tenant upgraded: {tenant_id} ({old_plan.value} -> {new_plan})")
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "old_plan": old_plan.value,
                "new_plan": new_plan,
                "new_quota": PLAN_QUOTAS[tenant.plan].to_dict()
            }
        except Exception as e:
            logger.error(f"Plan upgrade failed: {str(e)}")
            return {"error": str(e)}
    
    async def check_quota(self, tenant_id: str, resource: str, amount: int = 1) -> Tuple[bool, str]:
        """
        Check if tenant has quota for resource
        
        Args:
            tenant_id: Tenant ID
            resource: Resource type (users, storage, api_calls, etc.)
            amount: Amount needed
            
        Returns:
            (can_proceed, message)
        """
        try:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False, "Tenant not found"
            
            quota = PLAN_QUOTAS.get(tenant.plan)
            usage = self.usage.get(tenant_id)
            
            if not quota or not usage:
                return False, "Invalid configuration"
            
            # Check specific quota
            if resource == "users":
                if usage.current_users + amount > quota.max_users:
                    return False, f"User limit ({quota.max_users}) reached"
            elif resource == "storage":
                if usage.storage_used_gb + amount > quota.max_storage_gb:
                    return False, f"Storage limit ({quota.max_storage_gb}GB) reached"
            elif resource == "api_calls":
                if usage.api_calls_this_month + amount > quota.max_api_calls_monthly:
                    return False, f"API call limit reached"
            elif resource == "concurrent_sessions":
                if usage.concurrent_sessions + amount > quota.max_concurrent_sessions:
                    return False, f"Concurrent session limit ({quota.max_concurrent_sessions}) reached"
            
            return True, "Quota available"
        except Exception as e:
            logger.error(f"Quota check failed: {str(e)}")
            return False, str(e)
    
    async def record_usage(self, tenant_id: str, resource: str, amount: int = 1):
        """Record resource usage"""
        try:
            usage = self.usage.get(tenant_id)
            if not usage:
                return
            
            if resource == "users":
                usage.current_users += amount
            elif resource == "storage":
                usage.storage_used_gb += amount
            elif resource == "api_calls":
                usage.api_calls_this_month += amount
            elif resource == "concurrent_sessions":
                usage.concurrent_sessions += amount
            
            usage.last_updated = datetime.utcnow()
        except Exception as e:
            logger.error(f"Usage recording failed: {str(e)}")
    
    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get current usage for tenant"""
        try:
            tenant = self.tenants.get(tenant_id)
            usage = self.usage.get(tenant_id)
            quota = PLAN_QUOTAS.get(tenant.plan)
            
            if not all([tenant, usage, quota]):
                return {"error": "Tenant not found"}
            
            # Calculate usage percentages
            usage_percent = {
                "users": (usage.current_users / quota.max_users * 100) if quota.max_users > 0 else 0,
                "storage": (usage.storage_used_gb / quota.max_storage_gb * 100) if quota.max_storage_gb > 0 else 0,
                "api_calls": (usage.api_calls_this_month / quota.max_api_calls_monthly * 100) if quota.max_api_calls_monthly > 0 else 0
            }
            
            return {
                "tenant_id": tenant_id,
                "plan": tenant.plan.value,
                "usage": usage.to_dict(),
                "quota": quota.to_dict(),
                "usage_percent": usage_percent
            }
        except Exception as e:
            logger.error(f"Usage fetch failed: {str(e)}")
            return {"error": str(e)}
    
    async def get_isolated_data(self, tenant_id: str, resource_path: str) -> Optional[Dict]:
        """
        Get tenant-isolated data
        
        Args:
            tenant_id: Tenant ID
            resource_path: Data path (e.g., "sessions/123")
            
        Returns:
            Tenant-isolated data
        """
        try:
            tenant_data = self.tenant_data.get(tenant_id, {})
            
            # Navigate to resource
            parts = resource_path.split("/")
            current = tenant_data
            
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            
            return current
        except Exception as e:
            logger.error(f"Data retrieval failed: {str(e)}")
            return None
    
    async def store_isolated_data(self, tenant_id: str, resource_path: str, data: Any):
        """Store tenant-isolated data"""
        try:
            if tenant_id not in self.tenant_data:
                self.tenant_data[tenant_id] = {}
            
            parts = resource_path.split("/")
            current = self.tenant_data[tenant_id]
            
            # Navigate/create path
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Store data
            current[parts[-1]] = data
        except Exception as e:
            logger.error(f"Data storage failed: {str(e)}")
    
    async def generate_billing_invoice(self, tenant_id: str, period_start: datetime, 
                                       period_end: datetime) -> Dict[str, Any]:
        """
        Generate billing invoice
        
        Args:
            tenant_id: Tenant ID
            period_start: Billing period start
            period_end: Billing period end
            
        Returns:
            Invoice details
        """
        try:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return {"error": "Tenant not found"}
            
            # Calculate amount (simplified)
            plan_pricing = {
                PlanType.FREE: 0,
                PlanType.STARTER: 2900,  # $29/month in cents
                PlanType.PROFESSIONAL: 9900,  # $99/month
                PlanType.ENTERPRISE: 0  # Contact sales
            }
            
            amount = plan_pricing.get(tenant.plan, 0)
            
            record_id = str(uuid.uuid4())
            record = BillingRecord(
                record_id=record_id,
                tenant_id=tenant_id,
                billing_period_start=period_start,
                billing_period_end=period_end,
                amount_cents=amount,
                status="pending"
            )
            
            if tenant_id not in self.billing_records:
                self.billing_records[tenant_id] = []
            
            self.billing_records[tenant_id].append(record)
            
            logger.info(f"Invoice generated: {record_id} for tenant {tenant_id}")
            
            return {
                "invoice_id": record_id,
                "tenant_id": tenant_id,
                "amount_cents": amount,
                "currency": "USD",
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "status": "pending"
            }
        except Exception as e:
            logger.error(f"Invoice generation failed: {str(e)}")
            return {"error": str(e)}
    
    async def suspend_tenant(self, tenant_id: str, reason: str) -> Dict[str, bool]:
        """Suspend tenant account"""
        try:
            tenant = self.tenants.get(tenant_id)
            if tenant:
                tenant.status = TenantStatus.SUSPENDED
                tenant.metadata["suspension_reason"] = reason
                logger.info(f"Tenant suspended: {tenant_id} ({reason})")
                return {"success": True}
            return {"success": False}
        except Exception as e:
            logger.error(f"Suspension failed: {str(e)}")
            return {"success": False}


# ============================================================================
# DATA ISOLATION MIDDLEWARE
# ============================================================================

class TenantIsolationMiddleware:
    """Ensures data isolation between tenants"""
    
    def __init__(self, multi_tenancy_manager: MultiTenancyManager):
        self.manager = multi_tenancy_manager
    
    async def validate_tenant_access(self, user_id: str, tenant_id: str) -> bool:
        """Validate user access to tenant"""
        # In production, check user's tenant assignments
        return True
    
    async def inject_tenant_context(self, user_id: str) -> Optional[str]:
        """Inject tenant context for user"""
        # In production, look up user's primary tenant
        return "default"


logger.info("Multi-tenancy system module loaded - Tier 5 partial complete")
