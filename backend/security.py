"""
Security utilities for Biomech AI - Phase 2.1-2.3 Security Hardening

Implements API key management, security headers, request validation,
and encryption utilities.
"""

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import jwt

logger = logging.getLogger(__name__)

# ==================== API KEY MANAGEMENT (Phase 2.1) ====================


class APIKeyManager:
    """Manage API keys with rotation and revocation support"""

    # In-memory key store (for demo - use database + Secret Manager in production)
    _keys: Dict[str, Dict] = {}
    _key_mappings: Dict[str, str] = {}  # token -> key_id mapping

    @classmethod
    def generate_key(cls, name: str, permissions: list = None) -> Tuple[str, str]:
        """Generate a new API key"""
        key_id = f"key_{secrets.token_hex(8)}"
        key_token = secrets.token_urlsafe(32)

        # Hash the key token for storage
        key_hash = hashlib.sha256(key_token.encode()).hexdigest()

        key_data = {
            "id": key_id,
            "name": name,
            "hash": key_hash,
            "permissions": permissions or ["read", "write"],
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "revoked": False,
        }

        cls._keys[key_id] = key_data
        cls._key_mappings[key_token] = key_id

        logger.info(f"✅ API key generated: {name} ({key_id})")
        return key_id, key_token  # Return token only once!

    @classmethod
    def validate_key(cls, key_token: str) -> Optional[Dict]:
        """Validate API key and return associated data"""
        try:
            key_hash = hashlib.sha256(key_token.encode()).hexdigest()

            for key_id, key_data in cls._keys.items():
                if hmac.compare_digest(key_data["hash"], key_hash) and not key_data["revoked"]:
                    # Update last used time
                    key_data["last_used"] = datetime.now().isoformat()
                    logger.debug(f"API key validated: {key_id}")
                    return key_data

            logger.warning("Invalid or revoked API key used")
            return None
        except Exception as e:
            logger.error(f"Key validation error: {e}")
            return None

    @classmethod
    def revoke_key(cls, key_id: str) -> bool:
        """Revoke an API key"""
        if key_id in cls._keys:
            cls._keys[key_id]["revoked"] = True
            logger.warning(f"API key revoked: {key_id}")
            return True
        return False

    @classmethod
    def rotate_key(cls, key_id: str, name: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """Rotate an API key (revoke old, generate new)"""
        if key_id not in cls._keys:
            return None

        old_key = cls._keys[key_id]
        cls.revoke_key(key_id)

        new_name = name or f"{old_key['name']}_rotated"
        new_id, new_token = cls.generate_key(new_name, old_key.get("permissions"))

        logger.info(f"API key rotated: {key_id} -> {new_id}")
        return new_id, new_token

    @classmethod
    def list_keys(cls) -> list:
        """List all non-revoked API keys (without tokens)"""
        return [
            {
                "id": key_id,
                "name": data["name"],
                "permissions": data["permissions"],
                "created_at": data["created_at"],
                "last_used": data["last_used"],
                "revoked": data["revoked"],
            }
            for key_id, data in cls._keys.items()
        ]


# ==================== SECURITY HEADERS (Phase 2.3) ====================


def get_security_headers() -> Dict[str, str]:
    """Return recommended security headers"""
    return {
        # Prevent clickjacking
        "X-Frame-Options": "DENY",
        # Prevent MIME type sniffing
        "X-Content-Type-Options": "nosniff",
        # Enable XSS protection
        "X-XSS-Protection": "1; mode=block",
        # Referrer policy
        "Referrer-Policy": "strict-origin-when-cross-origin",
        # HSTS (HTTP Strict Transport Security) - 1 year
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        # Content Security Policy - allowed domains for dependencies
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://www.gstatic.com https://accounts.google.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "connect-src 'self' https://*.gemini.com https://*.supabase.co https://*.googleapis.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "media-src 'self' blob:; "
            "worker-src 'self' blob:;"
        ),
        # Permissions-Policy - Enable Camera for pose analysis
        "Permissions-Policy": (
            "geolocation=(), "
            "microphone=(), "
            "camera=(self), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        ),
        # Additional security headers
        "X-Permitted-Cross-Domain-Policies": "none",
    }


# ==================== REQUEST VALIDATION (Phase 2.2) ====================


class RequestValidator:
    """Validate incoming requests for security"""

    # Maximum allowed request size (10 MB)
    MAX_REQUEST_SIZE = 10 * 1024 * 1024

    # Maximum content length for specific endpoints
    ENDPOINT_SIZE_LIMITS = {
        "/generate-feedback": 5 * 1024 * 1024,  # 5MB
        "/sync-session": 2 * 1024 * 1024,  # 2MB
        "/sync-profile": 1 * 1024 * 1024,  # 1MB
    }

    @classmethod
    def validate_request_size(cls, endpoint: str, content_length: int) -> Tuple[bool, Optional[str]]:
        """Validate request size against limits"""
        limit = cls.ENDPOINT_SIZE_LIMITS.get(endpoint, cls.MAX_REQUEST_SIZE)

        if content_length > limit:
            error = f"Request size ({content_length} bytes) exceeds limit ({limit} bytes)"
            logger.warning(f"Request size validation failed: {error}")
            return False, error

        return True, None

    @classmethod
    def validate_json_payload(cls, data: Dict) -> Tuple[bool, Optional[str]]:
        """Validate JSON payload structure"""
        # Check for suspicious keys
        suspicious_patterns = ["__", "eval", "exec", "syscall"]
        for key in data.keys():
            for pattern in suspicious_patterns:
                if pattern in key.lower():
                    error = f"Suspicious key detected: {key}"
                    logger.warning(f"Payload validation failed: {error}")
                    return False, error

        return True, None

    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """Sanitize a string value"""
        if not isinstance(value, str):
            return str(value)

        # Remove null bytes
        value = value.replace("\x00", "")

        # Limit length
        MAX_STRING_LENGTH = 10000
        if len(value) > MAX_STRING_LENGTH:
            value = value[:MAX_STRING_LENGTH]

        return value


# ==================== JWT TOKEN MANAGEMENT ====================


class TokenManager:
    """JWT token generation and validation for authentication"""

    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable must be set")
    ALGORITHM = "HS256"
    TOKEN_EXPIRY_HOURS = 24

    @classmethod
    def generate_token(cls, user_id: str, permissions: list = None) -> str:
        """Generate JWT token for user"""
        expires = datetime.utcnow() + timedelta(hours=cls.TOKEN_EXPIRY_HOURS)

        payload = {
            "user_id": user_id,
            "permissions": permissions or ["read"],
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": expires.isoformat(),
        }

        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        logger.debug(f"JWT token generated for user: {user_id}")
        return token

    @classmethod
    def validate_token(cls, token: str) -> Optional[Dict]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])

            # Check expiration
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if expires_at < datetime.utcnow():
                logger.warning("Token expired")
                return None

            logger.debug(f"JWT token validated for user: {payload['user_id']}")
            return payload
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None


# ==================== ENCRYPTION UTILITIES ====================


def hash_password(password: str) -> str:
    """Hash password using PBKDF2"""
    import hashlib
    import os

    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}${pwdhash.hex()}"


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify password against stored hash"""
    import hashlib

    try:
        salt_hex, pwdhash_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        stored_pwdhash = bytes.fromhex(pwdhash_hex)

        pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(pwdhash, stored_pwdhash)
    except (ValueError, AttributeError):
        return False


logger.info("✅ Security utilities initialized")
