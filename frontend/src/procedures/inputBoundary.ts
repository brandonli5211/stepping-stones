import type { ViewProceduresInputData } from "./inputData";

export interface ViewProceduresInputBoundary {
  execute(input: ViewProceduresInputData): Promise<void>;
}
