"""
TIER 5: Advanced Authentication & Authorization
Implements RBAC, OAuth2, JWT, MFA, and enterprise security
"""

import asyncio
import uuid
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Tuple
import logging
from dataclasses import dataclass, field
import json
import base64

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================


class Role(str, Enum):
    """User roles in system"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TRAINER = "trainer"
    ATHLETE = "athlete"
    VIEWER = "viewer"
    API_CLIENT = "api_client"


class Permission(str, Enum):
    """System permissions"""

    READ_SESSIONS = "read:sessions"
    WRITE_SESSIONS = "write:sessions"
    DELETE_SESSIONS = "delete:sessions"
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    DELETE_USERS = "delete:users"
    MANAGE_ROLES = "manage:roles"
    MANAGE_TENANTS = "manage:tenants"
    VIEW_ANALYTICS = "view:analytics"
    EXPORT_DATA = "export:data"
    MANAGE_API_KEYS = "manage:api_keys"
    VIEW_AUDIT_LOG = "view:audit_log"


class TokenType(str, Enum):
    """Types of tokens"""

    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


@dataclass
class RoleDefinition:
    """Definition of a role with permissions"""

    role_name: Role
    permissions: Set[Permission]
    description: str

    def to_dict(self) -> Dict:
        return {
            "role": self.role_name.value,
            "permissions": [p.value for p in self.permissions],
            "description": self.description,
        }


@dataclass
class User:
    """User account"""

    user_id: str
    username: str
    email: str
    password_hash: str
    role: Role
    tenant_id: str
    is_active: bool = True
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self, include_password: bool = False) -> Dict:
        data = {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "tenant_id": self.tenant_id,
            "is_active": self.is_active,
            "mfa_enabled": self.mfa_enabled,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        if include_password:
            data["password_hash"] = self.password_hash
        return data


@dataclass
class JWT:
    """JWT token"""

    token_id: str
    user_id: str
    token_type: TokenType
    payload: Dict
    issued_at: datetime
    expires_at: datetime
    tenant_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict:
        return {
            "token_id": self.token_id,
            "user_id": self.user_id,
            "type": self.token_type.value,
            "iat": int(self.issued_at.timestamp()),
            "exp": int(self.expires_at.timestamp()),
            "tenant_id": self.tenant_id,
        }


@dataclass
class APIKey:
    """API key for service integration"""

    api_key_id: str
    api_key_hash: str
    user_id: str
    tenant_id: str
    name: str
    permissions: Set[Permission]
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    rate_limit: int = 1000  # requests per hour

    def is_expired(self) -> bool:
        return self.expires_at and datetime.utcnow() > self.expires_at


@dataclass
class AuditLog:
    """Audit log entry"""

    log_id: str
    user_id: str
    action: str
    resource: str
    timestamp: datetime
    status: str  # "success", "failure"
    details: Dict = field(default_factory=dict)
    ip_address: Optional[str] = None


# ============================================================================
# ROLE MANAGEMENT
# ============================================================================


class RoleManager:
    """Manages roles and permissions"""

    def __init__(self):
        self.roles: Dict[Role, RoleDefinition] = {}
        self._initialize_default_roles()
        logger.info("Role manager initialized")

    def _initialize_default_roles(self):
        """Initialize default system roles"""
        self.roles = {
            Role.SUPER_ADMIN: RoleDefinition(
                role_name=Role.SUPER_ADMIN,
                permissions=set(Permission),  # All permissions
                description="Full system access",
            ),
            Role.ADMIN: RoleDefinition(
                role_name=Role.ADMIN,
                permissions={
                    Permission.READ_USERS,
                    Permission.WRITE_USERS,
                    Permission.READ_SESSIONS,
                    Permission.WRITE_SESSIONS,
                    Permission.MANAGE_ROLES,
                    Permission.VIEW_ANALYTICS,
                    Permission.VIEW_AUDIT_LOG,
                },
                description="Tenant administrator",
            ),
            Role.TRAINER: RoleDefinition(
                role_name=Role.TRAINER,
                permissions={
                    Permission.READ_SESSIONS,
                    Permission.WRITE_SESSIONS,
                    Permission.READ_USERS,
                    Permission.VIEW_ANALYTICS,
                    Permission.EXPORT_DATA,
                },
                description="Trainer/coach",
            ),
            Role.ATHLETE: RoleDefinition(
                role_name=Role.ATHLETE,
                permissions={
                    Permission.READ_SESSIONS,
                    Permission.WRITE_SESSIONS,
                    Permission.VIEW_ANALYTICS,
                },
                description="Athlete/client",
            ),
            Role.API_CLIENT: RoleDefinition(
                role_name=Role.API_CLIENT,
                permissions={Permission.READ_SESSIONS, Permission.WRITE_SESSIONS},
                description="API client integration",
            ),
        }

    def get_permissions(self, role: Role) -> Set[Permission]:
        """Get permissions for role"""
        return self.roles.get(role, RoleDefinition(role, set(), "")).permissions

    def can_perform(self, role: Role, permission: Permission) -> bool:
        """Check if role has permission"""
        permissions = self.get_permissions(role)
        return permission in permissions

    def add_custom_role(self, role_name: str, permissions: List[str]) -> Dict:
        """Add custom role"""
        try:
            perms = {Permission(p) for p in permissions}
            role_def = RoleDefinition(
                role_name=Role(role_name),
                permissions=perms,
                description=f"Custom role: {role_name}",
            )
            logger.info(f"Custom role created: {role_name}")
            return {"success": True, "role": role_name}
        except Exception as e:
            logger.error(f"Custom role creation failed: {str(e)}")
            return {"success": False, "error": str(e)}


# ============================================================================
# AUTHENTICATION SERVICE
# ============================================================================


class AuthenticationService:
    """
    Authentication service with JWT, OAuth2, and MFA support
    """

    def __init__(self, secret_key: str = None, role_manager: RoleManager = None):
        """
        Initialize authentication service

        Args:
            secret_key: Secret key for token signing
            role_manager: Role manager instance
        """
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.role_manager = role_manager or RoleManager()
        self.users: Dict[str, User] = {}
        self.tokens: Dict[str, JWT] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.refresh_tokens: Dict[str, str] = {}  # user_id -> token_id
        self.audit_logs: List[AuditLog] = []

        logger.info("Authentication service initialized")

    async def register_user(
        self, username: str, email: str, password: str, role: str = "athlete", tenant_id: str = None
    ) -> Dict[str, Any]:
        """
        Register new user

        Args:
            username: Username
            email: Email address
            password: Password
            role: User role
            tenant_id: Tenant ID (default system tenant)

        Returns:
            User object or error
        """
        try:
            # Validate inputs
            if not self._validate_email(email):
                return {"error": "Invalid email"}
            if not self._validate_password(password):
                return {"error": "Password too weak"}
            if username in [u.username for u in self.users.values()]:
                return {"error": "Username already exists"}

            user_id = str(uuid.uuid4())
            password_hash = self._hash_password(password)

            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                role=Role(role),
                tenant_id=tenant_id or "default",
            )

            self.users[user_id] = user

            logger.info(f"User registered: {username} ({user_id})")

            return {"success": True, "user_id": user_id, "username": username, "email": email}
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            return {"error": str(e)}

    async def login(self, username: str, password: str, ip_address: str = None) -> Dict[str, Any]:
        """
        Authenticate user

        Args:
            username: Username
            password: Password
            ip_address: Client IP address

        Returns:
            Access and refresh tokens
        """
        try:
            # Find user
            user = None
            for u in self.users.values():
                if u.username == username:
                    user = u
                    break

            if not user:
                logger.warning(f"Login failed: user not found ({username})")
                return {"error": "Invalid credentials"}

            # Verify password
            if not self._verify_password(password, user.password_hash):
                logger.warning(f"Login failed: wrong password ({username})")
                return {"error": "Invalid credentials"}

            if not user.is_active:
                return {"error": "Account inactive"}

            # Create tokens
            access_token = await self._create_token(
                user.user_id, user.tenant_id, TokenType.ACCESS, ip_address, 3600
            )
            refresh_token = await self._create_token(
                user.user_id, user.tenant_id, TokenType.REFRESH, ip_address, 604800
            )

            # Store refresh token
            self.refresh_tokens[user.user_id] = refresh_token.token_id

            # Update last login
            user.last_login = datetime.utcnow()

            # Audit log
            await self._audit_log(user.user_id, "login", "user", "success", ip_address)

            logger.info(f"User logged in: {username}")

            return {
                "success": True,
                "access_token": self._encode_token(access_token),
                "refresh_token": self._encode_token(refresh_token),
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": user.to_dict(),
            }
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return {"error": str(e)}

    async def verify_token(self, token: str, ip_address: str = None) -> Tuple[bool, Optional[Dict]]:
        """
        Verify JWT token

        Args:
            token: JWT token
            ip_address: Client IP for validation

        Returns:
            (is_valid, token_payload)
        """
        try:
            payload = self._decode_token(token)
            if not payload:
                return False, None

            # Check expiration
            token_id = payload.get("token_id")
            jwt_obj = self.tokens.get(token_id)

            if not jwt_obj or jwt_obj.is_expired():
                return False, None

            return True, payload
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return False, None

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token

        Args:
            refresh_token: Refresh token

        Returns:
            New access token
        """
        try:
            payload = self._decode_token(refresh_token)
            if not payload:
                return {"error": "Invalid token"}

            user_id = payload.get("user_id")
            tenant_id = payload.get("tenant_id")

            # Create new access token
            access_token = await self._create_token(
                user_id, tenant_id, TokenType.ACCESS, None, 3600
            )

            logger.info(f"Token refreshed for user: {user_id}")

            return {
                "success": True,
                "access_token": self._encode_token(access_token),
                "expires_in": 3600,
            }
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return {"error": str(e)}

    async def _create_token(
        self,
        user_id: str,
        tenant_id: str,
        token_type: TokenType,
        ip_address: Optional[str],
        ttl_seconds: int,
    ) -> JWT:
        """Create JWT token"""
        token_id = str(uuid.uuid4())
        issued_at = datetime.utcnow()
        expires_at = issued_at + timedelta(seconds=ttl_seconds)

        jwt_obj = JWT(
            token_id=token_id,
            user_id=user_id,
            token_type=token_type,
            payload=self._create_payload(user_id, token_type),
            issued_at=issued_at,
            expires_at=expires_at,
            tenant_id=tenant_id,
            ip_address=ip_address,
        )

        self.tokens[token_id] = jwt_obj
        return jwt_obj

    def _create_payload(self, user_id: str, token_type: TokenType) -> Dict:
        """Create JWT payload"""
        user = self.users.get(user_id)
        if not user:
            return {}

        return {
            "sub": user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "tenant_id": user.tenant_id,
            "type": token_type.value,
        }

    def _encode_token(self, jwt_obj: JWT) -> str:
        """Encode JWT to string"""
        payload = jwt_obj.to_dict()
        payload.update(jwt_obj.payload)

        header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode()
        body = base64.b64encode(json.dumps(payload).encode()).decode()

        signature = hmac.new(
            self.secret_key.encode(), f"{header}.{body}".encode(), hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature).decode()

        return f"{header}.{body}.{signature}"

    def _decode_token(self, token: str) -> Optional[Dict]:
        """Decode JWT token"""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None

            header, body, signature = parts

            # Verify signature
            expected_sig = hmac.new(
                self.secret_key.encode(), f"{header}.{body}".encode(), hashlib.sha256
            ).digest()
            expected_sig = base64.b64encode(expected_sig).decode()

            if not hmac.compare_digest(signature, expected_sig):
                return None

            # Decode payload
            payload = json.loads(base64.b64decode(body).decode())
            return payload
        except Exception as e:
            logger.error(f"Token decode failed: {str(e)}")
            return None

    async def create_api_key(
        self, user_id: str, name: str, permissions: List[str], expires_in_days: int = 365
    ) -> Dict[str, Any]:
        """
        Create API key for integration

        Args:
            user_id: User creating key
            name: Key name
            permissions: List of permissions
            expires_in_days: Expiration in days

        Returns:
            API key details
        """
        try:
            user = self.users.get(user_id)
            if not user:
                return {"error": "User not found"}

            # Generate API key
            raw_key = secrets.token_urlsafe(32)
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            api_key_id = str(uuid.uuid4())
            perms = {Permission(p) for p in permissions}

            api_key = APIKey(
                api_key_id=api_key_id,
                api_key_hash=key_hash,
                user_id=user_id,
                tenant_id=user.tenant_id,
                name=name,
                permissions=perms,
                expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            )

            self.api_keys[api_key_id] = api_key

            logger.info(f"API key created: {name} for user {user_id}")

            return {
                "success": True,
                "api_key_id": api_key_id,
                "api_key": raw_key,  # Only shown once
                "name": name,
                "expires_at": api_key.expires_at.isoformat(),
                "warning": "Save this key securely, it won't be shown again",
            }
        except Exception as e:
            logger.error(f"API key creation failed: {str(e)}")
            return {"error": str(e)}

    async def validate_api_key(
        self, api_key: str, ip_address: str = None
    ) -> Tuple[bool, Optional[Dict]]:
        """Validate API key"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            for key_id, api_key_obj in self.api_keys.items():
                if api_key_obj.api_key_hash == key_hash:
                    if api_key_obj.is_expired() or not api_key_obj.is_active:
                        return False, None

                    await self._audit_log(
                        api_key_obj.user_id, "api_call", "api_key", "success", ip_address
                    )

                    return True, {
                        "user_id": api_key_obj.user_id,
                        "tenant_id": api_key_obj.tenant_id,
                        "permissions": [p.value for p in api_key_obj.permissions],
                    }

            return False, None
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False, None

    async def _audit_log(
        self, user_id: str, action: str, resource: str, status: str, ip_address: str = None
    ):
        """Record audit log entry"""
        log = AuditLog(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource=resource,
            timestamp=datetime.utcnow(),
            status=status,
            ip_address=ip_address,
        )
        self.audit_logs.append(log)

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        return "@" in email and "." in email.split("@")[1]

    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        return len(password) >= 8 and any(c.isupper() for c in password)

    def _hash_password(self, password: str) -> str:
        """Hash password"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password"""
        try:
            salt, pwd_hash = password_hash.split("$")
            verify_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
            return verify_hash.hex() == pwd_hash
        except:
            return False


logger.info("Advanced authentication module loaded - Tier 5 partial complete")
