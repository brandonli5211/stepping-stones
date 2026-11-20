import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
import "./styles.css"; // still needed by the existing calls page

createRoot(document.getElementById("root")!).render(<App />);
