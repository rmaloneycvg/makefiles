#!/usr/bin/env python3
"""Generate API Gateway authorizer and route configurations.

Subcommands:
    jwt-authorizer     Generate JWT authorizer JSON for Cognito
    route-config       Generate route with authorization scopes
    cors-config        Generate CORS configuration JSON
    throttle-config    Generate throttling configuration JSON

All output is JSON suitable for aws apigatewayv2 CLI commands.
"""
import json
import sys
import argparse


def jwt_authorizer(args):
    """Generate JWT authorizer creation parameters."""
    config = {
        "Name": args.name,
        "AuthorizerType": "JWT",
        "IdentitySource": "$request.header.Authorization",
        "JwtConfiguration": {
            "Audience": [args.client_id],
            "Issuer": f"https://cognito-idp.{args.region}.amazonaws.com/{args.user_pool_id}"
        }
    }
    print(json.dumps(config, indent=2))


def route_config(args):
    """Generate route configuration with authorization scopes."""
    config = {
        "RouteKey": f"{args.method} {args.path}",
        "AuthorizationType": "JWT",
        "AuthorizationScopes": args.scopes.split(",") if args.scopes else []
    }
    print(json.dumps(config, indent=2))


def cors_config(args):
    """Generate CORS configuration."""
    config = {
        "AllowOrigins": args.origins.split(","),
        "AllowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "AllowHeaders": [
            "Content-Type",
            "Authorization",
            "X-Amz-Date",
            "X-Api-Key",
            "X-Amz-Security-Token"
        ],
        "ExposeHeaders": ["X-Request-Id"],
        "MaxAge": 86400,
        "AllowCredentials": True if args.credentials else False
    }
    print(json.dumps(config, indent=2))


def throttle_config(args):
    """Generate throttling/rate-limit configuration."""
    config = {
        "ThrottlingBurstLimit": args.burst,
        "ThrottlingRateLimit": float(args.rate)
    }
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")

    # jwt-authorizer
    p_jwt = sub.add_parser("jwt-authorizer", help="Generate JWT authorizer config")
    p_jwt.add_argument("--name", default="CognitoAuthorizer")
    p_jwt.add_argument("--client-id", required=True)
    p_jwt.add_argument("--user-pool-id", required=True)
    p_jwt.add_argument("--region", required=True)

    # route-config
    p_route = sub.add_parser("route-config", help="Generate route config")
    p_route.add_argument("--method", default="GET")
    p_route.add_argument("--path", required=True)
    p_route.add_argument("--scopes", default="", help="Comma-separated OAuth2 scopes")

    # cors-config
    p_cors = sub.add_parser("cors-config", help="Generate CORS config")
    p_cors.add_argument("--origins", required=True, help="Comma-separated origins")
    p_cors.add_argument("--credentials", action="store_true")

    # throttle-config
    p_throttle = sub.add_parser("throttle-config", help="Generate throttle config")
    p_throttle.add_argument("--rate", required=True, type=int, help="Requests per second")
    p_throttle.add_argument("--burst", required=True, type=int, help="Burst limit")

    args = parser.parse_args()
    if args.command == "jwt-authorizer":
        jwt_authorizer(args)
    elif args.command == "route-config":
        route_config(args)
    elif args.command == "cors-config":
        cors_config(args)
    elif args.command == "throttle-config":
        throttle_config(args)
    else:
        parser.print_help()
        sys.exit(1)
