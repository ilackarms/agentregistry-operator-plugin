---
name: agentregistry-operator
description: Use when asked to inspect or explain AgentRegistry resources, harness-compatible agents, plugin source pins, deployment readiness, runtime status, unresolved refs, or AgentCore harness health.
allowed-tools: Bash
---

# AgentRegistry Operator

Use this skill to inspect AgentRegistry resources from a Claude Code harness.
Stay read-only.

## Credential Contract

Use `ARCTL_API_BASE_URL` for the API URL.

The helper uses a bearer token from `ARCTL_BEARER_TOKEN`,
`AGENTREGISTRY_BEARER_TOKEN`, or `AGENTREGISTRY_TOKEN`. If none is set, it uses
dev OIDC env: `AGENTREGISTRY_OIDC_ISSUER`,
`AGENTREGISTRY_OIDC_CLIENT_ID`, `AGENTREGISTRY_USERNAME`,
`AGENTREGISTRY_PASSWORD`.

Never print token values.

## Standard Inspection Flow

Run:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/agentregistry-summary.sh"
```

Use the JSON output to answer:

- Which harness-compatible Agents exist.
- Which Deployments are ready or failed.
- Which Plugins have resolved source commits.
- Which Prompts and Runtimes are present.

## Response Style

Lead with `AGENTREGISTRY_OPERATOR_PLUGIN_OK` for demo smoke prompts. Prefer
exact names, Ready condition reasons, and resolved commits. Mention the installed
plugin path from `CLAUDE_PLUGIN_ROOT`.
