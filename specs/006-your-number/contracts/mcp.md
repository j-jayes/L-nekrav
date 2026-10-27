# MCP contract changes: Your number

- **`get_occupation_salary(code, age_band=None, region=None, on=None)`**: gains `region`. Its
  description says the estimate is not an SCB figure, names both factors, and says a factor is left
  out when SCB does not publish its inputs.
- **`evaluate_permit_eligibility`**: the answer carries `market_position`. Its description says the
  position is a bracket between SCB's published percentiles, never an interpolated percentile, and
  that it does not affect eligibility.
- **`compare_occupations`**: accepts 1–5 codes.

The advisor reaches all three through `McpTools`, so it needs no separate change. The system prompt
gains one line: describe a number's position only with the bracket given, and call any estimate an
estimate.
