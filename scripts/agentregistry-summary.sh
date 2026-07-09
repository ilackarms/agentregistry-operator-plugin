#!/usr/bin/env sh
set -eu

base_url="${ARCTL_API_BASE_URL:-${CLAUDE_PLUGIN_OPTION_API_BASE_URL:-}}"
token="${ARCTL_BEARER_TOKEN:-${AGENTREGISTRY_BEARER_TOKEN:-${AGENTREGISTRY_TOKEN:-${CLAUDE_PLUGIN_OPTION_API_TOKEN:-}}}}"
resource="${1:-overview}"
name="${2:-}"

if [ -z "$base_url" ]; then
  printf '%s\n' '{"error":"missing ARCTL_API_BASE_URL"}' >&2
  exit 2
fi

if [ -z "$token" ]; then
  printf '%s\n' '{"error":"missing AgentRegistry bearer token"}' >&2
  exit 2
fi

base_url="${base_url%/}"

api_get() {
  path="$1"
  curl -fsS \
    -H "Authorization: Bearer ${token}" \
    -H "Accept: application/json" \
    "${base_url}${path}"
}

jq_required() {
  if ! command -v jq >/dev/null 2>&1; then
    printf '%s\n' '{"error":"jq is required by agentregistry-summary.sh"}' >&2
    exit 2
  fi
}

items_filter='
  def items:
    if type == "array" then .
    elif has("items") then .items
    elif has("agents") then .agents
    elif has("deployments") then .deployments
    elif has("plugins") then .plugins
    elif has("prompts") then .prompts
    elif has("skills") then .skills
    elif has("mcpServers") then .mcpServers
    elif has("runtimes") then .runtimes
    else []
    end;
'

summarize_list() {
  kind="$1"
  path="$2"
  api_get "$path" | jq -c --arg kind "$kind" "${items_filter}"'
    items
    | map({
        kind: (.kind // $kind),
        name: (.metadata.name // .name // ""),
        tag: (.metadata.tag // null),
        title: (.spec.title // null),
        harnesses: (.spec.compatibleHarnesses // .spec.harnesses // null),
        targetRef: (.spec.targetRef // null),
        runtimeRef: (.spec.runtimeRef // null),
        harness: (.spec.harness // null),
        resolvedSource: (.status.resolvedSource // .status.details.resolvedSource // null),
        conditions: (.status.conditions // []),
        ready: ((.status.conditions // []) | map(select(.type == "Ready")) | .[0] // null),
        inventory: (.status.inventory // null),
        manifest: (.status.manifest // null)
      })
  '
}

summarize_one() {
  kind="$1"
  collection="$2"
  item_name="$3"
  api_get "/v0/${collection}/${item_name}" | jq -c --arg kind "$kind" '{
    kind: (.kind // $kind),
    name: (.metadata.name // .name // ""),
    tag: (.metadata.tag // null),
    spec: .spec,
    status: .status
  }'
}

jq_required

case "$resource" in
  overview)
    agents="$(summarize_list Agent /v0/agents?limit=200)"
    deployments="$(summarize_list Deployment /v0/deployments?limit=200)"
    plugins="$(summarize_list Plugin /v0/plugins?limit=200)"
    prompts="$(summarize_list Prompt /v0/prompts?limit=200)"
    skills="$(summarize_list Skill /v0/skills?limit=200)"
    mcpservers="$(summarize_list MCPServer /v0/mcpservers?limit=200)"
    runtimes="$(summarize_list Runtime /v0/runtimes?limit=200)"

    jq -nc \
      --arg baseUrl "$base_url" \
      --arg pluginRoot "${CLAUDE_PLUGIN_ROOT:-}" \
      --argjson agents "$agents" \
      --argjson deployments "$deployments" \
      --argjson plugins "$plugins" \
      --argjson prompts "$prompts" \
      --argjson skills "$skills" \
      --argjson mcpServers "$mcpservers" \
      --argjson runtimes "$runtimes" \
      '{
        marker: "AGENTREGISTRY_OPERATOR_PLUGIN_OK",
        apiBaseUrl: $baseUrl,
        pluginRoot: $pluginRoot,
        counts: {
          agents: ($agents | length),
          deployments: ($deployments | length),
          plugins: ($plugins | length),
          prompts: ($prompts | length),
          skills: ($skills | length),
          mcpServers: ($mcpServers | length),
          runtimes: ($runtimes | length)
        },
        harnessCompatibleAgents: ($agents | map(select((.harnesses // []) | length > 0))),
        deployments: $deployments,
        plugins: $plugins,
        prompts: $prompts,
        skills: $skills,
        mcpServers: $mcpServers,
        runtimes: $runtimes
      }'
    ;;
  agents|deployments|plugins|prompts|skills|mcpservers|runtimes)
    if [ -n "$name" ]; then
      case "$resource" in
        agents) summarize_one Agent agents "$name" ;;
        deployments) summarize_one Deployment deployments "$name" ;;
        plugins) summarize_one Plugin plugins "$name" ;;
        prompts) summarize_one Prompt prompts "$name" ;;
        skills) summarize_one Skill skills "$name" ;;
        mcpservers) summarize_one MCPServer mcpservers "$name" ;;
        runtimes) summarize_one Runtime runtimes "$name" ;;
      esac
    else
      case "$resource" in
        agents) summarize_list Agent /v0/agents?limit=200 ;;
        deployments) summarize_list Deployment /v0/deployments?limit=200 ;;
        plugins) summarize_list Plugin /v0/plugins?limit=200 ;;
        prompts) summarize_list Prompt /v0/prompts?limit=200 ;;
        skills) summarize_list Skill /v0/skills?limit=200 ;;
        mcpservers) summarize_list MCPServer /v0/mcpservers?limit=200 ;;
        runtimes) summarize_list Runtime /v0/runtimes?limit=200 ;;
      esac
    fi
    ;;
  *)
    printf '{"error":"unknown resource kind","resource":"%s"}\n' "$resource" >&2
    exit 2
    ;;
esac
