import { NavLink, Outlet } from 'react-router-dom';

export default function App() {
  return (
    <div>
      <nav className="nav">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontWeight: 700 }}>VIA</span>
          <span className="tag blue">Demo</span>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
            Chat
          </NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active' : '')}>
            Dashboard
          </NavLink>
        </div>
      </nav>
      <Outlet />
    </div>
  );
}


