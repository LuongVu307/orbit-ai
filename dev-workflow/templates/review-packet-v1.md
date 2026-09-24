# Review Packet v1

Review the final diff independently. Do not rely on or request the implementer's reasoning transcript.

## Required inputs

- Task spec:
- Approved implementation plan:
- Diff base:
- Final diff:
- Validation results:

## Bug review

Check acceptance criteria, correctness, regressions, architecture boundaries, error handling, unnecessary complexity, and missing tests. Report only actionable findings with severity and `file:line` locations.

## Security review

When relevant, check secrets, external input validation, approval-boundary bypasses, unsafe external actions, database isolation, dependency changes, and destructive operations. Report only actionable findings with severity and `file:line` locations.

## Outcome

Record `passed`, `findings`, or `not applicable`. Objective findings return to implementation and require the affected validation scopes to be rerun. Product ambiguity returns to the user.
