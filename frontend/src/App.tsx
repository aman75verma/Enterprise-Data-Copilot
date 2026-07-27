import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Chat } from './pages/Chat';
import { AdminDashboard } from './pages/AdminDashboard';
import { Login } from './pages/Login';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const user = localStorage.getItem('user');
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<RequireAuth><Chat /></RequireAuth>} />
        <Route path="/admin" element={<RequireAuth><AdminDashboard /></RequireAuth>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
