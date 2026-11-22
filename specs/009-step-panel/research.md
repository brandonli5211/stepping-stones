# Research: Call detail step panel

## Decision: Extend ViewCallDetail instead of a new use case

`GET /calls/{id}` already returns `steps` and `type_details`. The call page already loads that response and already has `selectStep` for the transcript highlight. A second use case would fetch the same call again. The mapper drops those two fields today (`callDetail/api.ts`). Filling that gap stays inside `ViewCallDetail`.

## Decision: The page does not compare accounts

`type_details.fields[].result` is already `match`, `mismatch` or `reversed`. The presenter turns that word into a label. It does not compare `caller_asked` with `logged`.

## Decision: Default selection lives in the presenter

The first missed or wrong step, else the first step, is chosen when the loaded call does not contain the currently selected key. The page does not scan statuses. Choosing a step still goes through `selectStep`, which the flags already use.

## Decision: The field table belongs to a failed step

The table is call-level data, but a completed step's panel is the positive case: evidence, no deduction, no coaching. The table is attached only when the selected step is missed or wrong and the call type is `transfer_money`. Other types carry no fields, so they draw nothing.

## Decision: "I did do this" is not wired

Issue #40 owns that action. The panel does not draw the button.

## Alternatives considered

A new endpoint for one step was rejected because the whole list arrives with the call. Computing the default step inside the React component was rejected because that is a rule, and rules belong in the presenter.
