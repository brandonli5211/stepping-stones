// the stuff the whole app agrees on. just types and constants, no react in here

// the statuses /calls sends back. "procedure" is only for drawing a step from a procedure
export type StepStatus = "completed" | "missed" | "wrong" | "under_review" | "procedure";

export const STATUS_LABELS: Record<StepStatus, string> = {
  completed: "Completed",
  missed: "Missed",
  wrong: "Wrong",
  under_review: "Under review",
  procedure: "Procedure step",
};

export type NavKey = "my-calls" | "progress" | "procedures";

export type Screen = {
  id: "my-calls" | "call-detail" | "progress" | "procedures";
  path: string;
  title: string;
  nav: NavKey;
};

// the only four screens. call detail lights up "my calls" in the menu
export const SCREENS: Screen[] = [
  { id: "my-calls", path: "/", title: "Your calls", nav: "my-calls" },
  { id: "call-detail", path: "/calls/:callId", title: "Call detail", nav: "my-calls" },
  { id: "progress", path: "/progress", title: "Your progress", nav: "progress" },
  { id: "procedures", path: "/procedures", title: "Procedures", nav: "procedures" },
];

export type MenuItem = { nav: NavKey; label: string; path: string };

export const MENU: MenuItem[] = [
  { nav: "my-calls", label: "My calls", path: "/" },
  { nav: "progress", label: "Progress", path: "/progress" },
  { nav: "procedures", label: "Procedures", path: "/procedures" },
];

export type AgentProfile = { name: string; role: string | null };
