---
description: Inspect AgentRegistry resources, source pins, and deployment readiness with the AgentRegistry Operator Toolkit.
argument-hint: "[resource-name-or-question]"
allowed-tools: Bash
---

Use the AgentRegistry Operator Toolkit to inspect the current registry.

User focus:

```text
$ARGUMENTS
```

Run the bundled read-only summary helper first:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/agentregistry-summary.sh"
```

Then answer with:

1. `AGENTREGISTRY_OPERATOR_PLUGIN_OK`
2. Counts and readiness for Agents, Deployments, Plugins, Prompts, and Runtimes.
3. Any failed readiness or unresolved source pins.
4. The installed plugin path.

Do not print bearer tokens, keychain values, cookies, or other credentials.
