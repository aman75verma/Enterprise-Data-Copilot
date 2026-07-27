import { Database, LayoutDashboard, Code, Shield, Plus, LogOut } from 'lucide-react';
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
  const initials = user.name
    ? user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase()
    : 'DA';

  const handleLogout = () => {
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div className="top-nav glass-panel">
      <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
        <div className="brand">
          <Database className="brand-icon" size={22} />
          Supabase Support Copilot
          <span className="brand-sub">INTERNAL</span>
        </div>
      </Link>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span className="status-dot online" />
        <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginRight: 8 }}>
          Llama 3.3 70B
        </span>

        {!isAdmin && (
          <button
            className={`glass-button ${isDevMode ? 'primary' : ''}`}
            onClick={() => setIsDevMode(!isDevMode)}
          >
            <Code size={14} />
            {isDevMode ? 'Dev ON' : 'Dev'}
          </button>
        )}

        <Link to={isAdmin ? '/' : '/admin'} style={{ textDecoration: 'none' }}>
          <button className="glass-button">
            {isAdmin ? <><Shield size={14} /> Chat</> : <><LayoutDashboard size={14} /> Admin</>}
          </button>
        </Link>

        <div className="user-avatar" onClick={handleLogout} title={`${user.name || 'Agent'} — Click to logout`}>
          {initials}
        </div>
      </div>
    </div>
  );
}
