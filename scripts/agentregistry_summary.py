#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def env_first(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


BASE_URL = env_first("ARCTL_API_BASE_URL", "CLAUDE_PLUGIN_OPTION_API_BASE_URL").rstrip("/")
TOKEN = env_first(
    "ARCTL_BEARER_TOKEN",
    "AGENTREGISTRY_BEARER_TOKEN",
    "AGENTREGISTRY_TOKEN",
    "CLAUDE_PLUGIN_OPTION_API_TOKEN",
)
OIDC_ISSUER = env_first("AGENTREGISTRY_OIDC_ISSUER", "OIDC_ISSUER")
OIDC_CLIENT_ID = env_first("AGENTREGISTRY_OIDC_CLIENT_ID", "OIDC_CLIENT_ID")
OIDC_USERNAME = env_first("AGENTREGISTRY_USERNAME", "ARCTL_USERNAME")
OIDC_PASSWORD = env_first("AGENTREGISTRY_PASSWORD", "ARCTL_PASSWORD")


def fail(message: str, code: int = 2) -> None:
    print(json.dumps({"error": message}), file=sys.stderr)
    raise SystemExit(code)


if not BASE_URL:
    fail("missing ARCTL_API_BASE_URL")

def token_from_oidc_password_flow() -> str:
    if not (OIDC_ISSUER and OIDC_CLIENT_ID and OIDC_USERNAME and OIDC_PASSWORD):
        return ""

    token_url = f"{OIDC_ISSUER.rstrip('/')}/protocol/openid-connect/token"
    body = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": OIDC_CLIENT_ID,
            "username": OIDC_USERNAME,
            "password": OIDC_PASSWORD,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        token_url,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        fail(f"OIDC token endpoint returned HTTP {exc.code}: {body}", 1)
    except urllib.error.URLError as exc:
        fail(f"OIDC token request failed: {exc.reason}", 1)
    token = str(payload.get("access_token") or "").strip()
    if not token:
        fail("OIDC token response did not include an access_token", 1)
    return token


if not TOKEN:
    TOKEN = token_from_oidc_password_flow()

if not TOKEN:
    fail("missing AgentRegistry bearer token or OIDC password-flow credentials")


def api_get(path: str):
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        fail(f"AgentRegistry API returned HTTP {exc.code}: {body}", 1)
    except urllib.error.URLError as exc:
        fail(f"AgentRegistry API request failed: {exc.reason}", 1)


def list_items(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("items", "agents", "deployments", "plugins", "prompts", "skills", "mcpServers", "runtimes"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def condition_named(resource, condition_type: str):
    for condition in ((resource.get("status") or {}).get("conditions") or []):
        if condition.get("type") == condition_type:
            return condition
    return None


def summarize_resource(kind: str, resource):
    metadata = resource.get("metadata") or {}
    spec = resource.get("spec") or {}
    status = resource.get("status") or {}
    details = status.get("details") or {}
    return {
        "kind": resource.get("kind") or kind,
        "name": metadata.get("name") or resource.get("name") or "",
        "tag": metadata.get("tag"),
        "title": spec.get("title"),
        "harnesses": spec.get("compatibleHarnesses") or spec.get("harnesses"),
        "targetRef": spec.get("targetRef"),
        "runtimeRef": spec.get("runtimeRef"),
        "harness": spec.get("harness"),
        "resolvedSource": status.get("resolvedSource") or details.get("resolvedSource"),
        "conditions": status.get("conditions") or [],
        "ready": condition_named(resource, "Ready"),
        "inventory": status.get("inventory"),
        "manifest": status.get("manifest"),
    }


def summarize_list(kind: str, path: str):
    return [summarize_resource(kind, item) for item in list_items(api_get(path))]


def summarize_one(kind: str, collection: str, name: str):
    resource = api_get(f"/v0/{collection}/{name}")
    return {
        "kind": resource.get("kind") or kind,
        "name": (resource.get("metadata") or {}).get("name") or resource.get("name") or "",
        "tag": (resource.get("metadata") or {}).get("tag"),
        "spec": resource.get("spec"),
        "status": resource.get("status"),
    }


def print_json(value) -> None:
    print(json.dumps(value, separators=(",", ":"), sort_keys=True))


resource = sys.argv[1] if len(sys.argv) > 1 else "overview"
name = sys.argv[2] if len(sys.argv) > 2 else ""

kinds = {
    "agents": ("Agent", "agents"),
    "deployments": ("Deployment", "deployments"),
    "plugins": ("Plugin", "plugins"),
    "prompts": ("Prompt", "prompts"),
    "skills": ("Skill", "skills"),
    "mcpservers": ("MCPServer", "mcpservers"),
    "runtimes": ("Runtime", "runtimes"),
}

if resource == "overview":
    agents = summarize_list("Agent", "/v0/agents?limit=200")
    deployments = summarize_list("Deployment", "/v0/deployments?limit=200")
    plugins = summarize_list("Plugin", "/v0/plugins?limit=200")
    prompts = summarize_list("Prompt", "/v0/prompts?limit=200")
    skills = summarize_list("Skill", "/v0/skills?limit=200")
    mcpservers = summarize_list("MCPServer", "/v0/mcpservers?limit=200")
    runtimes = summarize_list("Runtime", "/v0/runtimes?limit=200")
    print_json(
        {
            "marker": "AGENTREGISTRY_OPERATOR_PLUGIN_OK",
            "apiBaseUrl": BASE_URL,
            "pluginRoot": os.environ.get("CLAUDE_PLUGIN_ROOT", ""),
            "counts": {
                "agents": len(agents),
                "deployments": len(deployments),
                "plugins": len(plugins),
                "prompts": len(prompts),
                "skills": len(skills),
                "mcpServers": len(mcpservers),
                "runtimes": len(runtimes),
            },
            "harnessCompatibleAgents": [agent for agent in agents if agent.get("harnesses")],
            "deployments": deployments,
            "plugins": plugins,
            "prompts": prompts,
            "skills": skills,
            "mcpServers": mcpservers,
            "runtimes": runtimes,
        }
    )
elif resource in kinds:
    kind, collection = kinds[resource]
    if name:
        print_json(summarize_one(kind, collection, name))
    else:
        print_json(summarize_list(kind, f"/v0/{collection}?limit=200"))
else:
    print(json.dumps({"error": "unknown resource kind", "resource": resource}), file=sys.stderr)
    raise SystemExit(2)
