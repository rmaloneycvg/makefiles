#!/usr/bin/env python3
"""
Generate APIM XML policies and write them to a file suitable for az apim api policy set.

Policies supported:
    oauth        — validate JWT (audience + any of given roles)
    oauth-role   — validate JWT with a single required role (per-operation)
    cors         — CORS + JWT (combines both)
    rate-limit   — rate limit calls per renewal period

Usage:
    apim_policy.py oauth --tenant-id <id> --audience <client-id> --roles API.Read API.Write API.Admin --out policy.xml
    apim_policy.py oauth-role --tenant-id <id> --audience <client-id> --role API.Read --out policy.xml
    apim_policy.py cors --origin https://app.example.com --tenant-id <id> --audience <client-id> --roles API.Read API.Write API.Admin --out policy.xml
    apim_policy.py rate-limit --calls 100 --period 60 --out policy.xml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def _validate_jwt(tenant_id: str, audience: str, roles: list[str], http_code: int = 401) -> ET.Element:
    openid_url = f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration"
    jwt = ET.Element("validate-jwt", {
        "header-name": "Authorization",
        "failed-validation-httpcode": str(http_code),
    })
    ET.SubElement(jwt, "openid-config", {"url": openid_url})
    required = ET.SubElement(jwt, "required-claims")
    aud_claim = ET.SubElement(required, "claim", {"name": "aud"})
    ET.SubElement(aud_claim, "value").text = audience
    if roles:
        role_claim = ET.SubElement(required, "claim", {"name": "roles", "match": "any"})
        for role in roles:
            ET.SubElement(role_claim, "value").text = role
    return jwt


def _policies_skeleton() -> tuple[ET.Element, ET.Element, ET.Element, ET.Element]:
    policies = ET.Element("policies")
    inbound = ET.SubElement(policies, "inbound")
    backend = ET.SubElement(policies, "backend")
    ET.SubElement(backend, "base")
    outbound = ET.SubElement(policies, "outbound")
    ET.SubElement(outbound, "base")
    return policies, inbound, backend, outbound


def build_oauth(tenant_id: str, audience: str, roles: list[str]) -> str:
    policies, inbound, *_ = _policies_skeleton()
    inbound.append(_validate_jwt(tenant_id, audience, roles, http_code=401))
    return ET.tostring(policies, encoding="unicode")


def build_oauth_role(tenant_id: str, audience: str, role: str) -> str:
    policies, inbound, *_ = _policies_skeleton()
    inbound.append(_validate_jwt(tenant_id, audience, [role], http_code=403))
    return ET.tostring(policies, encoding="unicode")


def build_cors(origin: str, tenant_id: str, audience: str, roles: list[str]) -> str:
    policies, inbound, *_ = _policies_skeleton()
    cors = ET.SubElement(inbound, "cors", {"allow-credentials": "true"})
    allowed_origins = ET.SubElement(cors, "allowed-origins")
    ET.SubElement(allowed_origins, "origin").text = origin
    allowed_methods = ET.SubElement(cors, "allowed-methods")
    for method in ("GET", "POST", "PUT", "DELETE", "OPTIONS"):
        ET.SubElement(allowed_methods, "method").text = method
    allowed_headers = ET.SubElement(cors, "allowed-headers")
    for header in ("Authorization", "Content-Type"):
        ET.SubElement(allowed_headers, "header").text = header
    inbound.append(_validate_jwt(tenant_id, audience, roles, http_code=401))
    return ET.tostring(policies, encoding="unicode")


def build_rate_limit(calls: int, period: int) -> str:
    policies, inbound, *_ = _policies_skeleton()
    ET.SubElement(inbound, "rate-limit", {"calls": str(calls), "renewal-period": str(period)})
    ET.SubElement(inbound, "base")
    return ET.tostring(policies, encoding="unicode")


def _write(xml: str, out: str | None) -> None:
    if out:
        Path(out).write_text(xml)
    else:
        sys.stdout.write(xml)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_oauth = sub.add_parser("oauth", help="Validate JWT with any of the given roles")
    p_oauth.add_argument("--tenant-id", required=True)
    p_oauth.add_argument("--audience", required=True, help="App registration client ID")
    p_oauth.add_argument("--roles", nargs="+", required=True)
    p_oauth.add_argument("--out")

    p_role = sub.add_parser("oauth-role", help="Validate JWT requiring a specific role")
    p_role.add_argument("--tenant-id", required=True)
    p_role.add_argument("--audience", required=True)
    p_role.add_argument("--role", required=True)
    p_role.add_argument("--out")

    p_cors = sub.add_parser("cors", help="CORS + JWT validation")
    p_cors.add_argument("--origin", required=True)
    p_cors.add_argument("--tenant-id", required=True)
    p_cors.add_argument("--audience", required=True)
    p_cors.add_argument("--roles", nargs="+", required=True)
    p_cors.add_argument("--out")

    p_rl = sub.add_parser("rate-limit", help="Rate limit policy")
    p_rl.add_argument("--calls", type=int, required=True)
    p_rl.add_argument("--period", type=int, required=True)
    p_rl.add_argument("--out")

    args = parser.parse_args()

    if args.cmd == "oauth":
        xml = build_oauth(args.tenant_id, args.audience, args.roles)
    elif args.cmd == "oauth-role":
        xml = build_oauth_role(args.tenant_id, args.audience, args.role)
    elif args.cmd == "cors":
        xml = build_cors(args.origin, args.tenant_id, args.audience, args.roles)
    elif args.cmd == "rate-limit":
        xml = build_rate_limit(args.calls, args.period)
    else:
        parser.error(f"Unknown command: {args.cmd}")
        return 2

    _write(xml, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
