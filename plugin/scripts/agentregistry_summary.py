#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request


def env(*ks):
    return next((v.strip() for k in ks if (v := os.environ.get(k, "")).strip()), "")


base = env("ARCTL_API_BASE_URL").rstrip("/")
tok = env("ARCTL_BEARER_TOKEN", "AGENTREGISTRY_BEARER_TOKEN", "AGENTREGISTRY_TOKEN")
if not base:
    raise SystemExit("missing ARCTL_API_BASE_URL")
if not tok:
    body = urllib.parse.urlencode({"grant_type": "password", "client_id": env("AGENTREGISTRY_OIDC_CLIENT_ID", "OIDC_CLIENT_ID"), "username": env("AGENTREGISTRY_USERNAME", "ARCTL_USERNAME"), "password": env("AGENTREGISTRY_PASSWORD", "ARCTL_PASSWORD")}).encode()
    req = urllib.request.Request(f'{env("AGENTREGISTRY_OIDC_ISSUER","OIDC_ISSUER").rstrip("/")}/protocol/openid-connect/token', data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    tok = json.loads(urllib.request.urlopen(req, timeout=30).read())["access_token"]


def get(path):
    req = urllib.request.Request(f"{base}{path}")
    req.add_header("Authorization", f"Bearer {tok}")
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())


def rows(payload, key):
    return payload if isinstance(payload, list) else payload.get("items") or payload.get(key) or []


def slim(kind, item):
    m, s, st = item.get("metadata") or {}, item.get("spec") or {}, item.get("status") or {}
    r = next((c for c in st.get("conditions") or [] if c.get("type") == "Ready"), {})
    return {
        "kind": item.get("kind") or kind,
        "name": m.get("name") or item.get("name"),
        "ready": {"status": r.get("status"), "reason": r.get("reason")} if r else None,
        "harnesses": s.get("compatibleHarnesses") or s.get("harnesses"),
        "harness": s.get("harness"),
        "resolvedSource": st.get("resolvedSource") or ((st.get("details") or {}).get("resolvedSource")),
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
    "pluginRoot": os.environ.get("CLAUDE_PLUGIN_ROOT", ""),
    "counts": {k: len(v) for k, v in data.items()},
    "harnessCompatibleAgents": [a for a in data["agents"] if a.get("harnesses")],
    **data,
}, separators=(",", ":")))
