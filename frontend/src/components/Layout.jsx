import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  Ticket, 
  MapPin, 
  ClipboardList, 
  Users, 
  Building2, 
  Clock, 
  Menu, 
  X, 
  LogOut, 
  ChevronRight,
  Map,
  FileText,
  Settings,
  User,
  Package,
  Receipt,
  UserCog,
  Key,
  ShoppingBag
} from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '../lib/utils';
import NetworkStatus from './NetworkStatus';

// Theme color
const THEME_COLOR = '#ED1C24';

// Navigation items for different roles
const getNavItems = (role) => {
  const items = {
    admin: [
      { path: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
      { path: '/admin/login-management', icon: UserCog, label: 'Login Management' },
      { path: '/admin/workers', icon: Users, label: 'Workers' },
      { path: '/admin/attendance', icon: Clock, label: 'Attendance' },
      { path: '/admin/campaigns', icon: Package, label: 'Campaigns' },
      { path: '/admin/ledger', icon: Receipt, label: 'Ledger' },
      { path: '/admin/coupons', icon: Ticket, label: 'Coupons' },
      { path: '/admin/sold-coupons', icon: ShoppingBag, label: 'Sold Coupons' },
      { path: '/admin/data-entry', icon: ClipboardList, label: 'Data Entry' },
      { path: '/admin/branches', icon: Building2, label: 'Branches' },
      { path: '/admin/api-keys', icon: Key, label: 'API Keys' },
      { path: '/admin/audit-logs', icon: FileText, label: 'Audit Logs' },
    ],
    cre: [
      { path: '/cre', icon: LayoutDashboard, label: 'Customers' },
    ],
    worker: [
      { path: '/worker', icon: LayoutDashboard, label: 'Dashboard' },
      { path: '/worker/attendance', icon: Clock, label: 'Attendance' },
      { path: '/worker/sell', icon: Ticket, label: 'Sale Coupon' },
      { path: '/worker/expenses', icon: Receipt, label: 'Expenses' },
      { path: '/worker/data-entry', icon: ClipboardList, label: 'Data Entry' },
    ],
    branch: [
      { path: '/branch', icon: LayoutDashboard, label: 'Dashboard' },
    ],
  };
  return items[role] || [];
};

export const Layout = ({ children }) => {
  const { user, logout, hasRole } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const navItems = getNavItems(user?.role);
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-zinc-50">
      <NetworkStatus />
      
      {/* Sidebar - Desktop */}
      <aside className={cn(
        "fixed left-0 top-0 h-full w-64 bg-white border-r border-zinc-200 z-40 transition-transform duration-300",
        sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
      )}>
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-zinc-200">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: THEME_COLOR }}>
              <MapPin className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight font-['Barlow_Condensed']" style={{ color: THEME_COLOR }}>
              FieldFlow Pro
            </span>
          </Link>
          <button 
            onClick={() => setSidebarOpen(false)}
            className="md:hidden p-1 hover:bg-zinc-100 rounded"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Navigation - scrollable area between header and user section */}
        <nav className="p-4 space-y-1 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 64px - 100px)' }}>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "nav-link",
                  isActive && "nav-link-active"
                )}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.label}</span>
                {isActive && <ChevronRight className="h-4 w-4 ml-auto" />}
              </Link>
            );
          })}
        </nav>
        
        {/* User section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-zinc-200 bg-white">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-zinc-200 flex items-center justify-center">
              <User className="h-5 w-5 text-zinc-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm truncate">{user?.name}</p>
              <p className="text-xs text-zinc-500 capitalize">{user?.role?.replace('_', ' ')}</p>
            </div>
          </div>
          <Button 
            variant="outline" 
            className="w-full justify-start"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </aside>
      
      {/* Main content */}
      <main className={cn(
        "min-h-screen transition-all duration-300",
        "md:ml-64"
      )}>
        {/* Top bar - Mobile */}
        <header className="sticky top-0 z-30 h-16 bg-white/80 backdrop-blur-md border-b border-zinc-200 md:hidden">
          <div className="h-full flex items-center justify-between px-4">
            <button 
              onClick={() => setSidebarOpen(true)}
              className="p-2 hover:bg-zinc-100 rounded-lg"
            >
              <Menu className="h-5 w-5" />
            </button>
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: THEME_COLOR }}>
                <MapPin className="h-5 w-5 text-white" />
              </div>
              <span className="font-bold text-lg tracking-tight font-['Barlow_Condensed']" style={{ color: THEME_COLOR }}>
                FieldFlow Pro
              </span>
            </Link>
            <div className="w-10" /> {/* Spacer */}
          </div>
        </header>
        
        {/* Page content */}
        <div className="p-4 md:p-6 lg:p-8">
          {children}
        </div>
      </main>
      
      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default Layout;
