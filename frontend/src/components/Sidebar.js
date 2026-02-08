import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  LayoutDashboard, 
  Users, 
  Container, 
  FileText, 
  Wallet, 
  LogOut,
  TrendingUp,
  TrendingDown,
  Wrench
} from 'lucide-react';

export const Sidebar = () => {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/clients', icon: Users, label: 'Clientes' },
    { path: '/dumpsters', icon: Container, label: 'Caçambas' },
    { path: '/orders', icon: FileText, label: 'Pedidos' },
    { path: '/finance/cash', icon: Wallet, label: 'Caixa' },
    { path: '/finance/receivable', icon: TrendingUp, label: 'Contas a Receber' },
    { path: '/finance/payable', icon: TrendingDown, label: 'Contas a Pagar' },
  ];

  return (
    <div className="w-64 bg-slate-900 min-h-screen flex flex-col" data-testid="sidebar">
      <div className="p-6 border-b border-slate-800">
        <h1 className="text-2xl font-heading font-black text-white tracking-tight" data-testid="app-title">
          FOX
        </h1>
        <p className="text-xs text-slate-400 mt-1">Locações</p>
      </div>

      <nav className="flex-1 p-4 space-y-1" data-testid="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-sm transition-colors duration-200 ${
                isActive
                  ? 'bg-orange-500 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <item.icon className="w-5 h-5" strokeWidth={1.5} />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800" data-testid="user-section">
        <div className="px-4 py-2">
          <p className="text-sm font-medium text-white" data-testid="user-name">{user?.full_name}</p>
          <p className="text-xs text-slate-400" data-testid="user-email">{user?.email}</p>
        </div>
        <button
          onClick={handleLogout}
          data-testid="logout-button"
          className="flex items-center gap-3 px-4 py-3 rounded-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors duration-200 w-full mt-2"
        >
          <LogOut className="w-5 h-5" strokeWidth={1.5} />
          <span className="font-medium">Sair</span>
        </button>
      </div>
    </div>
  );
};