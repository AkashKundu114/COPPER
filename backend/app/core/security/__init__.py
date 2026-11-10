"""COPPER Zero-Trust Security & Identity Subsystem."""

from app.core.security.access_control import (
    ABACContext,
    AccessController,
    Permission,
    Role,
    access_controller,
)
from app.core.security.agent_token import (
    AgentTokenPayload,
    AgentTokenService,
    agent_token_service,
)
from app.core.security.auth import (
    KeyManager,
    Principal,
    PrincipalType,
    authenticate_request,
    key_manager,
)
from app.core.security.network_policy import (
    NetworkSecurityPolicy,
    SSRFViolationError,
    network_security_policy,
)
from app.core.security.prompt_injection import (
    sanitize_untrusted_text,
    scan_for_indirect_injection,
    wrap_untrusted_observation,
)
from app.core.security.rate_limiter import (
    RateLimitConfig,
    RateLimiterMiddleware,
    SlidingWindowRateLimiter,
    rate_limiter,
)
from app.core.security.secret_vault import (
    SecretItem,
    SecretVault,
    secret_vault,
)
from app.core.security.tool_policy import (
    ToolAuthorizationPolicy,
    get_required_tool_permission,
    tool_authorization_policy,
)

__all__ = [
    "ABACContext",
    "AccessController",
    "AgentTokenPayload",
    "AgentTokenService",
    "KeyManager",
    "NetworkSecurityPolicy",
    "Permission",
    "Principal",
    "PrincipalType",
    "RateLimitConfig",
    "RateLimiterMiddleware",
    "Role",
    "SSRFViolationError",
    "SecretItem",
    "SecretVault",
    "SlidingWindowRateLimiter",
    "ToolAuthorizationPolicy",
    "access_controller",
    "agent_token_service",
    "authenticate_request",
    "get_required_tool_permission",
    "key_manager",
    "network_security_policy",
    "rate_limiter",
    "sanitize_untrusted_text",
    "scan_for_indirect_injection",
    "secret_vault",
    "tool_authorization_policy",
    "wrap_untrusted_observation",
]
