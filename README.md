# AgentRegistry Operator Toolkit

Read-only Claude Code plugin for inspecting an AgentRegistry environment from a
harness Agent.

The plugin is intentionally small for the first demo:

- `commands/agentregistry-status.md` asks Claude to inspect the registry.
- `skills/agentregistry-operator/SKILL.md` teaches the read-only operating flow.
- `scripts/agentregistry-summary.sh` calls the AgentRegistry API and returns a
  compact JSON summary.

## Credentials

Set:

```sh
export ARCTL_API_BASE_URL=https://example.are.soloio.dev
export ARCTL_BEARER_TOKEN=...
```

The helper also accepts `AGENTREGISTRY_BEARER_TOKEN`, `AGENTREGISTRY_TOKEN`, or
Claude plugin user config values. It never prints token values.

## Local Smoke

```sh
CLAUDE_PLUGIN_ROOT="$PWD" ./scripts/agentregistry-summary.sh
```

The response includes `AGENTREGISTRY_OPERATOR_PLUGIN_OK` when API access works.
