// Page layout + routes. Each <Route> is one page from the UI outline (docs/UI_OUTLINE.md).
import { Link, Route, Routes } from 'react-router-dom';

import CallListPage from './pages/CallListPage.jsx';
import CallDetailPage from './pages/CallDetailPage.jsx';

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="brand">Stepping Stones</Link>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<CallListPage />} />
          <Route path="/calls/:callId" element={<CallDetailPage />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
    </div>
  );
}
