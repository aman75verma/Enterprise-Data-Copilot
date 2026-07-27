import { Database, LayoutDashboard, Code, MessageSquare } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

interface Props {
  isDevMode: boolean;
  setIsDevMode: (val: boolean) => void;
}

export function TopNav({ isDevMode, setIsDevMode }: Props) {
  const location = useLocation();
  const navigate = useNavigate();
  const isAdmin = location.pathname === '/admin';
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const initials = user.name ? user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase() : 'DA';

  return (
    <div className="topbar glass">
      <Link to="/" className="topbar-brand">
        <div className="topbar-logo">
          <Database size={18} color="#080c14" strokeWidth={2.5} />
        </div>
        <span className="topbar-title">Supabase Support Copilot</span>
        <span className="topbar-badge">Internal</span>
      </Link>

      <div className="topbar-actions">
        <div className="model-indicator">
          <span className="pulse-dot" />
          Llama 3.3 · 70B
        </div>

        {!isAdmin && (
          <button className={`btn ${isDevMode ? 'btn-accent' : ''}`} onClick={() => setIsDevMode(!isDevMode)}>
            <Code size={13} />
            {isDevMode ? 'Dev: ON' : 'Dev'}
          </button>
        )}

        <Link to={isAdmin ? '/' : '/admin'} style={{ textDecoration: 'none' }}>
          <button className="btn">
            {isAdmin ? <><MessageSquare size={13} /> Chat</> : <><LayoutDashboard size={13} /> Admin</>}
          </button>
        </Link>

        <div
          className="avatar"
          onClick={() => { localStorage.removeItem('user'); navigate('/login'); }}
          title={`${user.name || 'Agent'} · Click to sign out`}
        >
          {initials}
        </div>
      </div>
    </div>
  );
}
