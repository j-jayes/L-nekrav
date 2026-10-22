# Protocol Parity and Honest-Fit Checklist: Lönekrav over MCP and A2A

**Purpose**: Unit tests for the requirements in spec.md, plan.md and contracts/. They cover
MCP/REST parity, the A2A event contract, behaviour with no key, the honest-fit memo guard, and
privacy and logging.
**Created**: 2026-10-22
**Feature**: [spec.md](../spec.md)
**Audience**: the PR reviewer. Standard depth.

Ownership: these items belong to the reviewer. A `[x]` means the reviewer judged that the
*requirement* is well written. It does not mean the work is done. `/speckit-implement` reads the
markers and never changes them.

## Requirement Completeness

- [ ] CHK001 - Is every one of the five tools mapped to exactly one REST route, with the argument mapping stated (nested request model or flat arguments)? [Completeness, Spec §FR-006, contracts/mcp.md]
- [ ] CHK002 - Does the spec list every rule that moves out of the REST adapter, so that a reviewer can tell when the move is complete? [Completeness, Spec §FR-002]
- [ ] CHK003 - Is the content of a `ui_sync` item fully defined (kind, tool, arguments, result), and is it stated whether failed tool calls produce one? [Completeness, Spec §FR-012, contracts/a2a.md]
- [ ] CHK004 - Are all the terminal states (completed, failed, rejected, canceled) listed, each with the condition that triggers it and its message text? [Completeness, contracts/a2a.md]
- [ ] CHK005 - Is the content of the agent card fully specified, including the disclosure text and the absolute endpoint URL? [Completeness, Spec §FR-010]
- [ ] CHK006 - Are the limits on the advisor's input fields (ad length, background length) stated, and are they consistent with the REST ad limit? [Completeness, data-model.md]
- [ ] CHK007 - Does the spec say how the model's tool list is derived, so the advisor's tools cannot drift from the MCP tools? [Completeness, Spec §FR-013, research R6]

## Requirement Clarity

- [ ] CHK008 - Is "the same data model the REST API returns" defined precisely enough to compare: equal JSON, or equal after parsing? [Clarity, Spec §FR-003, SC-001]
- [ ] CHK009 - Is "a cheap, fast model" pinned to a named default, with the date it was checked and the measurements behind the choice? [Clarity, Spec §FR-014, research R9]
- [ ] CHK010 - Is the bounded number of tool rounds given as a number, and is the per-call model time limit given in seconds? [Clarity, Spec §FR-015]
- [ ] CHK011 - Is "the memo does not mention the duties requirement" defined as a check that can be decided mechanically (for example, the exact `HONEST_FIT` text is absent)? [Clarity, Spec §FR-016, data-model.md]
- [ ] CHK012 - Is "promptly", used for the no-key reply, given a number? [Clarity, Spec §FR-017, SC-005]
- [ ] CHK013 - When a message carries both a data part and text parts, is it clear which one is used? [Clarity, Spec §FR-011, contracts/a2a.md]

## Requirement Consistency

- [ ] CHK014 - Does the spec's "agent unavailable … instead of failing" agree with the contract's use of the `rejected` state rather than `failed`? [Consistency, Spec US3, research R8]
- [ ] CHK015 - Does the handoff's `message/stream` agree with the A2A v1.0 method name `SendStreamingMessage` in the contract and the quickstart? [Consistency, Spec §FR-021, research R7]
- [ ] CHK016 - Is the error text for an unknown code the same in REST (404 detail), MCP (tool error) and the agent (the tool message passed to the model)? [Consistency, Spec §FR-009]
- [ ] CHK017 - Do the compare tool's arguments match the REST compare request (codes plus an optional offer, with no age band)? [Consistency, Spec §FR-006]
- [ ] CHK018 - Is the third-party disclosure worded the same in the card, the memo footer and the clarification? [Consistency, Spec Clarifications, §FR-016]

## Acceptance Criteria Quality

- [ ] CHK019 - Can SC-001 (100 % parity) be verified with a defined set of inputs for each tool and resource? [Measurability, Spec SC-001]
- [ ] CHK020 - Is SC-004 ("never recommends a code for a lower threshold") testable without judging the model's prose, for instance through the guard and the scripted fake model? [Measurability, Spec SC-004]
- [ ] CHK021 - Are the transcripts' required contents (the command run, the events, the timings) stated, so a reviewer can tell when the evidence is complete? [Measurability, Spec §FR-021, SC-006]

## Scenario Coverage

- [ ] CHK022 - Are requirements stated for a run where the model answers without calling any tool? [Coverage, Spec Edge Cases, §FR-016]
- [ ] CHK023 - Are requirements stated for a full-mode search that falls back to fast mode, when it is called through MCP and through the agent? [Coverage, Spec Edge Cases]
- [ ] CHK024 - Are client cancellation requirements defined, including what happens to a model call that is already in flight? [Coverage, Spec Edge Cases, Gap]
- [ ] CHK025 - Are requirements defined for concurrent advisor runs that share the model client and the MCP server? [Coverage, Spec §FR-018]
- [ ] CHK026 - Is the behaviour defined when the model sends arguments that are not valid JSON? [Edge Case, Gap]

## Non-Functional: Privacy and Logging

- [ ] CHK027 - Does the logging requirement name every new source of log output (the MCP server, the A2A SDK, the agent loop, model client errors)? [Completeness, Spec §FR-005]
- [ ] CHK028 - Is it stated that failure messages (failed-state text, tool errors) must not echo request content such as ad text or salary? [Gap, Spec §FR-005]
- [ ] CHK029 - Is it stated that the key must never appear in the card, the artifacts, the errors or the logs? [Completeness, Spec §FR-014]
- [ ] CHK030 - Is the decision to have no authentication on /mcp and /a2a recorded as an assumption, with the deployment it is limited to? [Assumption, Spec Assumptions]

## Honest Fit and Legal Data

- [ ] CHK031 - Do the requirements forbid legal figures in the system prompt, and say how that is enforced (the existing literal scan covers Python files only)? [Completeness, Spec §FR-004, research R10]
- [ ] CHK032 - Is it specified that memo figures must come from tool results in the same run, and is it stated how that is checked when the model is real and not the fake? [Measurability, Spec US2-5, Gap]
- [ ] CHK033 - Must the memo show the Swedish SSYK titles next to the English ones, as the rest of the product does? [Consistency, Spec Assumptions]

## Notes

- Items marked `[Gap]` may be closed by recording a deliberate exclusion. They do not all need a
  new requirement.
