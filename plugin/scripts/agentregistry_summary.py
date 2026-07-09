#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request


def e(*ks):
    for k in ks:
        v = os.environ.get(k, "").strip()
        if v:
            return v
    return ""


base = e("ARCTL_API_BASE_URL").rstrip("/")
tok = e("ARCTL_BEARER_TOKEN", "AGENTREGISTRY_BEARER_TOKEN", "AGENTREGISTRY_TOKEN")
if not base:
    raise SystemExit("missing ARCTL_API_BASE_URL")
if not tok:
    issuer = e("AGENTREGISTRY_OIDC_ISSUER", "OIDC_ISSUER").rstrip("/")
    body = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": e("AGENTREGISTRY_OIDC_CLIENT_ID", "OIDC_CLIENT_ID"),
        "username": e("AGENTREGISTRY_USERNAME", "ARCTL_USERNAME"),
        "password": e("AGENTREGISTRY_PASSWORD", "ARCTL_PASSWORD"),
    }).encode()
    req = urllib.request.Request(f"{issuer}/protocol/openid-connect/token", data=body)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    tok = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())["access_token"]


def get(path):
    req = urllib.request.Request(f"{base}{path}")
    req.add_header("Authorization", f"Bearer {tok}")
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())


def rows(payload, key):
    return payload if isinstance(payload, list) else payload.get("items") or payload.get(key) or []


def ready(item):
    for c in (item.get("status") or {}).get("conditions") or []:
        if c.get("type") == "Ready":
            return {"status": c.get("status"), "reason": c.get("reason")}


def slim(kind, item):
    m, s, st = item.get("metadata") or {}, item.get("spec") or {}, item.get("status") or {}
    src = st.get("resolvedSource") or ((st.get("details") or {}).get("resolvedSource"))
    return {
        "kind": item.get("kind") or kind,
        "name": m.get("name") or item.get("name"),
        "ready": ready(item),
        "harnesses": s.get("compatibleHarnesses") or s.get("harnesses"),
        "targetRef": s.get("targetRef"),
        "runtimeRef": s.get("runtimeRef"),
        "harness": s.get("harness"),
        "resolvedSource": src,
    }


spec = {
    "agents": ("Agent", "/v0/agents?limit=200"),
    "deployments": ("Deployment", "/v0/deployments?limit=200"),
    "plugins": ("Plugin", "/v0/plugins?limit=200"),
    "prompts": ("Prompt", "/v0/prompts?limit=200"),
    "runtimes": ("Runtime", "/v0/runtimes?limit=200"),
}
data = {k: [slim(kind, x) for x in rows(get(path), k)] for k, (kind, path) in spec.items()}
print(json.dumps({
    "marker": "AGENTREGISTRY_OPERATOR_PLUGIN_OK",
    "apiBaseUrl": base,
    "pluginRoot": os.environ.get("CLAUDE_PLUGIN_ROOT", ""),
    "counts": {k: len(v) for k, v in data.items()},
    "harnessCompatibleAgents": [a for a in data["agents"] if a.get("harnesses")],
    **data,
}, separators=(",", ":"), sort_keys=True))
