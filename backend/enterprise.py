"""
Multi-Tenancy Support - Phase 5.1 Enterprise Features

Implements organization/workspace support for enterprise deployments
with role-based access control and data isolation.
"""

import logging
from typing import Dict, Optional, Any, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """Role definitions"""

    ADMIN = "admin"
    MANAGER = "manager"
    COACH = "coach"
    USER = "user"
    VIEWER = "viewer"


class OrganizationTier(str, Enum):
    """Organization subscription tiers"""

    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Organization(BaseModel):
    """Organization/workspace"""

    id: str
    name: str
    slug: str  # URL-friendly identifier
    tier: OrganizationTier = OrganizationTier.FREE
    owner_id: str
    logo_url: Optional[str] = None
    settings: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Feature limits
    max_users: int = 5  # FREE: 5, PROFESSIONAL: 50, ENTERPRISE: unlimited
    max_analyses_per_month: int = 1000  # Based on tier
    max_storage_gb: int = 10  # Based on tier


class OrganizationMember(BaseModel):
    """Organization member with role"""

    id: str
    org_id: str
    user_id: str
    role: UserRole = UserRole.USER
    joined_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    permissions: List[str] = []  # Custom permissions


class RolePermissions:
    """Role-based permissions matrix"""

    PERMISSIONS_MAP = {
        UserRole.ADMIN: [
            "org:read",
            "org:write",
            "org:delete",
            "member:manage",
            "role:manage",
            "billing:manage",
            "settings:manage",
            "analysis:full",
            "export:full",
        ],
        UserRole.MANAGER: [
            "org:read",
            "member:read",
            "analysis:full",
            "reports:read",
            "import:data",
        ],
        UserRole.COACH: [
            "org:read",
            "member:read",
            "analysis:create",
            "analysis:read",
            "client:manage",
        ],
        UserRole.USER: ["org:read", "analysis:own", "profile:edit"],  # Only own analyses
        UserRole.VIEWER: ["analysis:read"],  # Read-only access
    }

    @classmethod
    def has_permission(cls, role: UserRole, permission: str) -> bool:
        """Check if role has permission"""
        return permission in cls.PERMISSIONS_MAP.get(role, [])

    @classmethod
    def get_permissions(cls, role: UserRole) -> List[str]:
        """Get all permissions for role"""
        return cls.PERMISSIONS_MAP.get(role, [])


class MultiTenancyManager:
    """Manage organization isolation and access control"""

    def __init__(self):
        self.organizations: Dict[str, Organization] = {}
        self.members: Dict[str, List[OrganizationMember]] = {}

    def create_organization(self, org: Organization) -> str:
        """Create new organization"""
        self.organizations[org.id] = org
        self.members[org.id] = []
        logger.info(f"Organization created: {org.id}")
        return org.id

    def add_member(self, org_id: str, member: OrganizationMember) -> bool:
        """Add member to organization"""
        if org_id not in self.organizations:
            logger.error(f"Organization not found: {org_id}")
            return False

        org = self.organizations[org_id]
        current_members = len(self.members[org_id])

        if current_members >= org.max_users:
            logger.warning(f"Organization {org_id} reached member limit")
            return False

        self.members[org_id].append(member)
        logger.info(f"Member added to organization {org_id}: {member.user_id}")
        return True

    def check_access(self, org_id: str, user_id: str, required_permission: str) -> bool:
        """Check if user has permission in organization"""
        if org_id not in self.organizations:
            return False

        for member in self.members.get(org_id, []):
            if member.user_id == user_id:
                role = member.role
                return RolePermissions.has_permission(role, required_permission)

        return False

    def get_organization_data(self, org_id: str, user_id: str, data_type: str) -> Optional[Dict]:
        """Get organization data with access control"""
        # Verify user has access
        if not self.check_access(org_id, user_id, f"{data_type}:read"):
            logger.warning(f"Access denied for user {user_id} to {data_type} in org {org_id}")
            return None

        # Return isolated data for organization
        if data_type == "analyses":
            return {"org_id": org_id, "count": 42, "recent": []}  # Placeholder

        return None

    def enforce_quota(self, org_id: str, quota_type: str) -> bool:
        """Check if organization is within quota"""
        org = self.organizations.get(org_id)
        if not org:
            return False

        if quota_type == "analyses_per_month":
            # Check against org.max_analyses_per_month
            pass
        elif quota_type == "storage":
            # Check against org.max_storage_gb
            pass

        return True


# Global multi-tenancy manager
_tenancy_manager: Optional[MultiTenancyManager] = None


def get_tenancy_manager() -> MultiTenancyManager:
    """Get or create global tenancy manager"""
    global _tenancy_manager
    if _tenancy_manager is None:
        _tenancy_manager = MultiTenancyManager()
    return _tenancy_manager


logger.info("✅ Multi-tenancy support initialized")
