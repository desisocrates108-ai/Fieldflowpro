import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "./context/AuthContext";
import "./App.css";

// Pages
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import RedeemCouponPage from "./pages/RedeemCoupon";

// Admin Pages
import AdminDashboard from "./pages/admin/Dashboard";
import WorkersPage from "./pages/admin/Workers";
import AdminCouponsPage from "./pages/admin/Coupons";
import AdminBookingsPage from "./pages/admin/Bookings";
import BranchesPage from "./pages/admin/Branches";
import LiveMapPage from "./pages/admin/LiveMap";
import CampaignsPage from "./pages/admin/Campaigns";

// Worker Pages
import WorkerDashboard from "./pages/worker/Dashboard";
import AttendancePage from "./pages/worker/Attendance";
import IssueCouponPage from "./pages/worker/IssueCoupon";
import SellCouponPage from "./pages/worker/SellCoupon";
import MyCouponsPage from "./pages/worker/MyCoupons";
import TasksPage from "./pages/worker/Tasks";
import ExpensesPage from "./pages/worker/Expenses";

// Branch Pages
import BranchBookings from "./pages/branch/Bookings";

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, loading, user } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    // Redirect to appropriate dashboard based on role
    switch (user?.role) {
      case 'admin':
        return <Navigate to="/admin" replace />;
      case 'cre':
        return <Navigate to="/cre" replace />;
      case 'worker':
        return <Navigate to="/worker" replace />;
      case 'branch':
        return <Navigate to="/branch" replace />;
      default:
        return <Navigate to="/login" replace />;
    }
  }

  return children;
};

// Root redirect based on user role
const RootRedirect = () => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  switch (user?.role) {
    case 'admin':
      return <Navigate to="/admin" replace />;
    case 'cre':
      return <Navigate to="/cre" replace />;
    case 'worker':
      return <Navigate to="/worker" replace />;
    case 'branch':
      return <Navigate to="/branch" replace />;
    default:
      return <Navigate to="/login" replace />;
  }
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/redeem" element={<RedeemCouponPage />} />
      
      {/* Root Redirect */}
      <Route path="/" element={<RootRedirect />} />

      {/* Admin Routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/workers"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <WorkersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/coupons"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminCouponsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/bookings"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminBookingsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/branches"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <BranchesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/map"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <LiveMapPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/campaigns"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <CampaignsPage />
          </ProtectedRoute>
        }
      />

      {/* Worker Routes */}
      <Route
        path="/worker"
        element={
          <ProtectedRoute allowedRoles={['worker']}>
            <WorkerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/worker/attendance"
        element={
          <ProtectedRoute allowedRoles={['worker']}>
            <AttendancePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/worker/coupons"
        element={
          <ProtectedRoute allowedRoles={['worker']}>
            <IssueCouponPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/worker/sell"
        element={
          <ProtectedRoute allowedRoles={['worker']}>
            <SellCouponPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/worker/expenses"
        element={
          <ProtectedRoute allowedRoles={['worker']}>
            <ExpensesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/worker/my-coupons"
        element={
          <ProtectedRoute allowedRoles={['worker']}>
            <MyCouponsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/worker/tasks"
        element={
          <ProtectedRoute allowedRoles={['worker']}>
            <TasksPage />
          </ProtectedRoute>
        }
      />

      {/* Branch Manager Routes */}
      <Route
        path="/branch"
        element={
          <ProtectedRoute allowedRoles={['branch']}>
            <BranchBookings />
          </ProtectedRoute>
        }
      />
      <Route
        path="/branch/bookings"
        element={
          <ProtectedRoute allowedRoles={['branch']}>
            <BranchBookings />
          </ProtectedRoute>
        }
      />

      {/* CRE Routes - Same dashboard as Admin but limited permissions */}
      <Route
        path="/cre"
        element={
          <ProtectedRoute allowedRoles={['cre']}>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cre/coupons"
        element={
          <ProtectedRoute allowedRoles={['cre']}>
            <AdminCouponsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cre/bookings"
        element={
          <ProtectedRoute allowedRoles={['cre']}>
            <AdminBookingsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cre/audit-logs"
        element={
          <ProtectedRoute allowedRoles={['cre']}>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />

      {/* Catch all - redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster 
          position="top-right" 
          richColors 
          closeButton
          toastOptions={{
            className: 'font-sans',
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
