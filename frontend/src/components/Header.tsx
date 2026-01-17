import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../services/store';
import { LogOut } from 'lucide-react';

export default function Header() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-dark-surface border-b border-dark-border sticky top-0 z-50">
      <div className="container mx-auto px-4 max-w-5xl">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <img src="/logo.png" alt="Note²" className="h-10 w-10 rounded-lg" />
            <span className="text-xl font-bold text-dark-text-primary">
              Note<sup className="text-brand text-sm">2</sup>
            </span>
          </Link>

          {/* User Menu */}
          <div className="flex items-center gap-4">
            <span className="text-dark-text-secondary text-sm hidden sm:block">
              {user?.email}
            </span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-bg rounded-lg transition-colors"
            >
              <LogOut size={18} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
