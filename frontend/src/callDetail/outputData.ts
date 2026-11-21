import type { CallDetail } from "./entities";

// Output Data for ViewCallDetail.
export class ViewCallDetailOutputData {
  constructor(readonly detail: CallDetail) {}
}
