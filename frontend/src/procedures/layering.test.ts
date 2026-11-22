const sources = import.meta.glob("./*.{ts,tsx}", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const importsOf = (file: string) => [...sources[`./${file}`].matchAll(/from\s+"([^"]+)"/g)].map((match) => match[1]);
const APPLICATION = ["entities", "inputData", "inputBoundary", "outputData", "outputBoundary", "dataAccess", "interactor"];
const ADAPTERS = ["controller", "presenter", "viewModel", "api"];

test("imports point inward", () => {
  for (const name of [...APPLICATION, ...ADAPTERS]) for (const path of importsOf(`${name}.ts`)) {
    expect(path.startsWith("react")).toBe(false);
    expect(path.includes("components")).toBe(false);
  }
  for (const name of APPLICATION) for (const path of importsOf(`${name}.ts`)) expect(APPLICATION.map((item) => `./${item}`)).toContain(path);
  for (const file of ["ProceduresPage.tsx"]) for (const path of importsOf(file)) expect(["./api", "../gateway", "./interactor", "./compose"]).not.toContain(path);
});
