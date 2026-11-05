import CallsPage from "./CallsPage.jsx";
import "./styles.css";

const NAV = ["My calls", "Progress", "Procedures"];

export default function App() {
  return (
    <div className="shell">
      <nav className="sidebar">
        <div className="brand">Stepping<br />Stones</div>
        <ul>
          {NAV.map((item) => <li key={item} className={item === "My calls" ? "active" : ""}>{item}</li>)}
        </ul>
        <div className="user">Agent</div>
      </nav>
      <main className="content"><CallsPage /></main>
    </div>
  );
}
