import React from 'react';
import { Database, LayoutDashboard, Code, Shield } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

interface Props {
  isDevMode: boolean;
  setIsDevMode: (val: boolean) => void;
}

export function TopNav({ isDevMode, setIsDevMode }: Props) {
  const location = useLocation();
  const isAdmin = location.pathname === '/admin';

  return (
    <div className="top-nav glass-panel">
      <Link to="/" style={{textDecoration: 'none', color: 'inherit'}}>
        <div className="brand">
          <Database className="brand-icon" size={24} />
          Enterprise Data Copilot
        </div>
      </Link>

      <div style={{ display: 'flex', gap: 16 }}>
        {!isAdmin && (
          <button 
            className={`glass-button ${isDevMode ? 'primary' : ''}`}
            onClick={() => setIsDevMode(!isDevMode)}
          >
            <Code size={16} />
            {isDevMode ? 'Dev Mode: ON' : 'Dev Mode: OFF'}
          </button>
        )}
        
        <Link to={isAdmin ? "/" : "/admin"} style={{textDecoration: 'none'}}>
          <button className="glass-button">
            {isAdmin ? (
              <><Shield size={16} /> Copilot Chat</>
            ) : (
              <><LayoutDashboard size={16} /> Admin Dashboard</>
            )}
          </button>
        </Link>
      </div>
    </div>
  );
}
