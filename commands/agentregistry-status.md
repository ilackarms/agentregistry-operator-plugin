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
2. The AgentRegistry API base URL in use.
3. A concise readiness summary for Agents, Deployments, Plugins, Prompts, and Runtimes.
4. Any unresolved refs, failed conditions, missing source pins, or drift/readiness concerns.
5. The installed plugin path.

Do not print bearer tokens, keychain values, cookies, or other credentials.
