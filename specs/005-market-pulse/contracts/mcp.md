# MCP contract: `get_occupation_market`

- **Arguments**: `code: str`, a four-digit SSYK code.
- **Result**: `MarketAnswer`, the same object as REST returns for the same code within the reuse
  period.
- **Errors**: an unknown code gives a `ToolError` with REST's text (through `_expected()`).
- **Description** (the model reads it): "Labour-market context for one SSYK code: open ads and
  positions on Platsbanken now, by county; SCB's mean monthly salary in each national area; and
  ads per year since 2016. Context only: it never changes which code fits the duties or the
  salary floor, and must not be used to choose or rank codes."
- **Advisor**: it lists the tools at run time, so it gets this tool. `SYSTEM_PROMPT` adds: "You
  may call get_occupation_market for the plausible codes and mention open ads or regional means,
  with their source and date. Never use demand or pay as a reason to prefer a code." There is no
  `ui_sync` for this tool.
