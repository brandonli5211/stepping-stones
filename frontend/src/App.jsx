import { Sidebar } from "./components/Sidebar.jsx";
import { StoneSprite } from "./components/Stone.jsx";
import CallDetailPage from "./pages/CallDetailPage.jsx";
import MyCallsPage from "./pages/MyCallsPage.jsx";
import ProceduresPage from "./pages/ProceduresPage.jsx";
import ProgressPage from "./pages/ProgressPage.jsx";
import { RouteOutlet, RouterProvider, paths } from "./router.jsx";

// The app's only screens. `navKey` picks the highlighted menu item;
// routes without `navLabel` (call detail) have no menu item of their own.
const routes = [
  { path: paths.myCalls, component: MyCallsPage, navKey: "calls", navLabel: "My calls" },
  { path: paths.callDetail(), component: CallDetailPage, navKey: "calls" },
  { path: paths.progress, component: ProgressPage, navKey: "progress", navLabel: "Progress" },
  { path: paths.procedures, component: ProceduresPage, navKey: "procedures", navLabel: "Procedures" },
];

export default function App() {
  return (
    <RouterProvider routes={routes}>
      <StoneSprite />
      <div className="shell">
        <Sidebar items={routes.filter((r) => r.navLabel)} />
        <main className="main">
          <RouteOutlet />
        </main>
      </div>
    </RouterProvider>
  );
}
