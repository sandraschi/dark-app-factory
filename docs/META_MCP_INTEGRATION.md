# Meta-MCP Integration

**Cross-utilization with [meta-mcp](https://github.com/sandraschi/meta-mcp)**

Dark App Factory phases (Foreman, Worker, Judge) are long-running agents. meta-mcp will add agent lifecycle tools: start, poll status, get report. Natural fit for cross-utilization.

## How meta-mcp can use Dark App Factory

| Use Case | meta-mcp Tool | Dark App Factory |
|----------|---------------|------------------|
| Run full factory | `start_agent(agent_type="dark_factory", vibe_path=..., output_dir=...)` | Spawns `factory.py run` as background task |
| Run Foreman only | `start_agent(agent_type="foreman", vibe_path=...)` | Runs `foreman.py plan` |
| Run Worker only | `start_agent(agent_type="worker", specs_path=...)` | Runs `worker.py build` |
| Run Judge only | `start_agent(agent_type="judge", scenarios_path=...)` | Runs `judge.py judge` |

Client waits (non-blocking) via `get_agent_status`, then fetches `get_agent_report` when complete.

## How Dark App Factory can use meta-mcp

| Use Case | Mechanism |
|----------|-----------|
| Worker pattern lookup | Worker calls meta-mcp `execute_server_tool(advanced-memory, adn_search, query=...)` before generating code |
| Knowledge-augmented build | Worker writes research notes via `adn_content("write", ...)` during build |
| DTU as MCP server | Expose DTU mocks as MCP tools; meta-mcp starts DTU, Worker/Judge call via tool execution |

## Implementation Notes

- Dark App Factory scripts (`foreman.py`, `worker.py`, `judge.py`) are subprocess-invokable. meta-mcp AgentService can wrap them.
- DTU (`dtu/main.py`) is FastAPI; could add FastMCP wrapper for MCP protocol exposure.
- Worker would need MCP client to call meta-mcp; or run in context where meta-mcp tools are available to the orchestrator.

## Reference

- meta-mcp Agent Plan: `path/to/meta_mcp/docs/AGENT_LIFECYCLE_IMPLEMENTATION_PLAN.md`
- ANTIPATTERN (tool returns): `path/to/mcp-central-docs/docs/patterns/ANTIPATTERN_DIALOGIC_TOOL_FLUFF.md`
