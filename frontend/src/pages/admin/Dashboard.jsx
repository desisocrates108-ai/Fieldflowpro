import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { dashboardAPI, couponAPI, attendanceAPI } from '../../lib/api';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { 
  Users, 
  Ticket, 
  TrendingUp, 
  Clock, 
  ClipboardList, 
  Building2, 
  CheckCircle,
  Loader2,
  RefreshCcw
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = async () => {
    try {
      const response = await dashboardAPI.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      toast.error('Failed to load dashboard statistics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchStats();
  };

  const statCards = stats ? [
    {
      title: 'Total Workers',
      value: stats.total_workers,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      accent: 'stats-card-primary',
    },
    {
      title: 'Active Today',
      value: stats.active_workers,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      accent: 'stats-card-success',
    },
    {
      title: 'Coupons Today',
      value: stats.total_coupons_today,
      icon: Ticket,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      accent: 'stats-card-primary',
    },
    {
      title: 'Redemption Rate',
      value: `${stats.redemption_rate}%`,
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      accent: 'stats-card-warning',
    },
    {
      title: 'Attendance Rate',
      value: `${stats.attendance_rate}%`,
      icon: Clock,
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-50',
      accent: 'stats-card-primary',
    },
    {
      title: 'Pending Bookings',
      value: stats.pending_bookings,
      icon: ClipboardList,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      accent: 'stats-card-warning',
    },
    {
      title: 'Completed',
      value: stats.completed_bookings,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      accent: 'stats-card-success',
    },
    {
      title: 'Total Branches',
      value: stats.total_branches,
      icon: Building2,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      accent: 'stats-card-primary',
    },
  ] : [];

  return (
    <Layout>
      <div className="space-y-6" data-testid="admin-dashboard">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              Dashboard
            </h1>
            <p className="text-zinc-500 mt-1">
              Welcome back, {user?.name}
            </p>
          </div>
          <Button 
            variant="outline" 
            onClick={handleRefresh}
            disabled={refreshing}
            data-testid="refresh-stats-btn"
          >
            <RefreshCcw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Stats Grid */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {statCards.map((stat, index) => (
              <Card 
                key={index} 
                className={`stats-card ${stat.accent}`}
                data-testid={`stat-card-${stat.title.toLowerCase().replace(/\s/g, '-')}`}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-zinc-500">{stat.title}</p>
                      <p className="text-3xl font-bold font-['Barlow_Condensed'] mt-2">
                        {stat.value}
                      </p>
                    </div>
                    <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                      <stat.icon className={`h-6 w-6 ${stat.color}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="font-['Barlow_Condensed']">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full justify-start" variant="outline" asChild>
                <a href="/admin/workers">
                  <Users className="h-4 w-4 mr-3" />
                  Manage Workers
                </a>
              </Button>
              <Button className="w-full justify-start" variant="outline" asChild>
                <a href="/admin/bookings">
                  <ClipboardList className="h-4 w-4 mr-3" />
                  View Bookings
                </a>
              </Button>
              <Button className="w-full justify-start" variant="outline" asChild>
                <a href="/admin/branches">
                  <Building2 className="h-4 w-4 mr-3" />
                  Manage Branches
                </a>
              </Button>
              <Button className="w-full justify-start" variant="outline" asChild>
                <a href="/admin/map">
                  <Clock className="h-4 w-4 mr-3" />
                  Live Map Tracking
                </a>
              </Button>
            </CardContent>
          </Card>

          {/* System Status */}
          <Card>
            <CardHeader>
              <CardTitle className="font-['Barlow_Condensed']">System Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full" />
                    <span className="text-sm font-medium">API Services</span>
                  </div>
                  <span className="text-xs text-green-600 font-medium">Operational</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full" />
                    <span className="text-sm font-medium">Database</span>
                  </div>
                  <span className="text-xs text-green-600 font-medium">Connected</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full" />
                    <span className="text-sm font-medium">GPS Services</span>
                  </div>
                  <span className="text-xs text-green-600 font-medium">Active</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
