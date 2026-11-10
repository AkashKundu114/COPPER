"""Network Security Policy & Server-Side Request Forgery (SSRF) Defense.

Enforces strict network perimeter boundaries and egress restrictions outside LLM control.
"""

from __future__ import annotations

import ipaddress
import socket
import urllib.parse
from typing import Any

from app.core.config import NetworkMode, settings
from app.core.logger import logger


class SSRFViolationError(RuntimeError):
    """Raised when an outbound network request attempts to probe private subnets or cloud metadata."""
    pass


BLOCKED_METADATA_HOSTS = {
    "169.254.169.254",  # AWS/GCP/Azure/OpenStack metadata IP
    "metadata.google.internal",
    "metadata.packet.net",
    "instance-data",
}


def is_private_or_restricted_ip(ip_str: str) -> bool:
    """Checks whether an IP address belongs to private, loopback, link-local, or multicast subnets."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return True


class NetworkSecurityPolicy:
    """Enforces network egress restrictions based on NetworkMode and SSRF prevention rules."""

    def validate_url(self, target_url: str, allow_loopback: bool | None = None) -> str:
        """Validates that a URL conforms to current network egress mode and SSRF rules.
        
        Returns the sanitized URL string, or raises SSRFViolationError.
        """
        clean_url = target_url.strip()
        parsed = urllib.parse.urlparse(clean_url)

        if parsed.scheme.lower() not in {"http", "https"}:
            raise SSRFViolationError(f"Prohibited protocol scheme: '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

        hostname = (parsed.hostname or "").lower().strip()
        if not hostname:
            raise SSRFViolationError("Invalid URL: missing target hostname.")

        # Check explicit cloud metadata hosts
        if hostname in BLOCKED_METADATA_HOSTS:
            raise SSRFViolationError(f"Access denied: Prohibited cloud metadata endpoint '{hostname}'.")

        mode = getattr(settings, "NETWORK_MODE", NetworkMode.USER_AUTHORIZED_EGRESS)
        if isinstance(mode, str):
            try:
                mode = NetworkMode(mode.lower())
            except ValueError:
                mode = NetworkMode.USER_AUTHORIZED_EGRESS

        # Mode 1: OFFLINE_AIRGAP
        if mode == NetworkMode.OFFLINE_AIRGAP:
            raise SSRFViolationError("Outbound network egress is prohibited under OFFLINE_AIRGAP mode.")

        # Resolve hostname to verify IP address
        try:
            # We resolve IPv4 first
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            resolved_ips = [info[4][0] for info in addr_info]
        except socket.gaierror as e:
            raise SSRFViolationError(f"DNS resolution failure for host '{hostname}': {e}")

        # Check if loopback is permitted
        loopback_allowed = (
            allow_loopback
            if allow_loopback is not None
            else (mode == NetworkMode.LOCAL_SERVICES)
        )

        for ip_str in resolved_ips:
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue

            # Check cloud metadata IP range
            if ip in ipaddress.ip_network("169.254.0.0/16"):
                raise SSRFViolationError(f"Access denied: Target IP '{ip_str}' is within protected link-local metadata space.")

            # Mode 2: LOCAL_SERVICES (strictly loopback services only, e.g. SearXNG on 127.0.0.1)
            if mode == NetworkMode.LOCAL_SERVICES:
                if not ip.is_loopback:
                    raise SSRFViolationError(
                        f"Outbound WAN request to '{hostname}' ({ip_str}) is blocked under LOCAL_SERVICES mode. Only local loopback endpoints are permitted."
                    )
            # Mode 3: USER_AUTHORIZED_EGRESS (WAN allowed, but internal RFC 1918 subnets blocked unless loopback allowed)
            elif mode == NetworkMode.USER_AUTHORIZED_EGRESS:
                if ip.is_loopback:
                    if not loopback_allowed:
                        raise SSRFViolationError(f"Access denied: Loopback connection to '{hostname}' ({ip_str}) blocked in standard egress mode.")
                elif ip.is_private:
                    raise SSRFViolationError(
                        f"SSRF Protection: Outbound connection to private intranet IP '{ip_str}' ({hostname}) is blocked."
                    )

        return clean_url


network_security_policy = NetworkSecurityPolicy()
