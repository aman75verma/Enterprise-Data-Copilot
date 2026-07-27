import { useNavigate } from 'react-router-dom';
import { Database, Zap } from 'lucide-react';

export function Login() {
  const navigate = useNavigate();

  const handleDemoLogin = () => {
    localStorage.setItem('user', JSON.stringify({ name: 'Demo Agent', email: 'agent@supabase.io' }));
    navigate('/');
  };

  const handleGoogleLogin = () => {
    // In production, this would redirect to Google OAuth.
    // For this portfolio demo, we simulate it.
    localStorage.setItem('user', JSON.stringify({ name: 'Google User', email: 'user@gmail.com' }));
    navigate('/');
  };

  return (
    <div className="login-container">
      <div className="login-card glass-panel">
        <div className="welcome-logo" style={{ margin: '0 auto 24px' }}>
          <Database size={32} color="#0b0f19" />
        </div>
        
        <h1>Supabase Support Copilot</h1>
        <p>AI-powered internal tool for support agents. Query customer data, search docs, and track live issues.</p>

        <button className="google-btn" onClick={handleGoogleLogin}>
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Continue with Google
        </button>

        <div className="login-divider">or</div>

        <button className="demo-btn" onClick={handleDemoLogin}>
          <Zap size={16} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: 6 }} />
          Enter as Demo Agent
        </button>

        <div className="login-footer">
          Built for portfolio demonstration purposes.<br />
          Powered by Groq (Llama 3.3 70B) &amp; MCP Protocol.
        </div>
      </div>
    </div>
  );
}
