import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { intelligenceAPI, adminAPI } from '../../lib/api';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { 
  Users, 
  TrendingUp, 
  AlertTriangle, 
  MapPin, 
  DollarSign,
  Activity,
  ShieldAlert,
  Clock,
  RefreshCcw,
  Loader2,
  Award,
  BarChart3,
  Zap,
  UserX,
  CheckCircle,
  XCircle,
  Search,
  Building2,
  Ticket,
  CalendarDays,
  Briefcase
} from 'lucide-react';
import { toast } from 'sonner';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [workerScores, setWorkerScores] = useState([]);
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [inactiveWorkers, setInactiveWorkers] = useState({ total_inactive: 0, workers: [] });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [scanningFraud, setScanningFraud] = useState(false);

  const fetchAllData = useCallback(async () => {
    try {
      const [metricsRes, scoresRes, alertsRes, inactiveRes] = await Promise.all([
        adminAPI.getDashboardStats(),
        intelligenceAPI.getWorkerScores(),
        intelligenceAPI.getFraudAlerts('ACTIVE'),
        intelligenceAPI.getInactiveWorkers()
      ]);
      
      setMetrics(metricsRes.data);
      setWorkerScores(scoresRes.data.slice(0, 10)); // Top 10
      setFraudAlerts(alertsRes.data);
      setInactiveWorkers(inactiveRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to load dashboard data. Check network/API.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
    
    // Auto-refresh every 30 seconds for real-time metrics
    const interval = setInterval(() => {
      adminAPI.getDashboardStats().then(res => setMetrics(res.data)).catch(() => {});
    }, 30000);
    
    return () => clearInterval(interval);
  }, [fetchAllData]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAllData();
  };

  const handleFraudScan = async () => {
    setScanningFraud(true);
    try {
      const res = await intelligenceAPI.runFraudScan();
      toast.success(res.data.message);
      fetchAllData();
    } catch (error) {
      toast.error('Fraud scan failed');
    } finally {
      setScanningFraud(false);
    }
  };

  const handleResolveFraudAlert = async (alertId) => {
    try {
      await intelligenceAPI.resolveFraudAlert(alertId, 'Resolved from dashboard');
      toast.success('Alert resolved');
      fetchAllData();
    } catch (error) {
      toast.error('Failed to resolve alert');
    }
  };

  const handleDismissFraudAlert = async (alertId) => {
    try {
      await intelligenceAPI.dismissFraudAlert(alertId, 'Dismissed as false positive');
      toast.success('Alert dismissed');
      fetchAllData();
    } catch (error) {
      toast.error('Failed to dismiss alert');
    }
  };

  const handleResolveInactivity = async (alertId) => {
    try {
      await adminAPI.resolveInactivityAlert(alertId, 'Resolved from dashboard');
      toast.success('Inactivity alert resolved');
      fetchAllData();
    } catch (error) {
      toast.error('Failed to resolve alert');
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-blue-600 bg-blue-50';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL': return 'bg-red-600';
      case 'HIGH': return 'bg-orange-500';
      case 'MEDIUM': return 'bg-yellow-500';
      default: return 'bg-blue-500';
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="admin-command-center">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight flex items-center gap-2">
              <Zap className="h-8 w-8 text-yellow-500" />
              Command Center
            </h1>
            <p className="text-zinc-500 mt-1">
              Real-time Revenue Intelligence • Elite v4.0
              {metrics?.last_updated && (
                <span className="ml-2 text-xs text-zinc-400">
                  Last updated: {new Date(metrics.last_updated).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' })} IST
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={handleRefresh}
              disabled={refreshing}
              data-testid="refresh-btn"
            >
              <RefreshCcw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button 
              onClick={handleFraudScan}
              disabled={scanningFraud}
              className="bg-red-600 hover:bg-red-700"
              data-testid="fraud-scan-btn"
            >
              <ShieldAlert className={`h-4 w-4 mr-2 ${scanningFraud ? 'animate-pulse' : ''}`} />
              {scanningFraud ? 'Scanning...' : 'Run Fraud Scan'}
            </Button>
          </div>
        </div>

        {/* Real-Time Metrics */}
        {metrics && (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
              <CardContent className="p-4 text-center">
                <DollarSign className="h-6 w-6 mx-auto text-green-600 mb-1" />
                <p className="text-2xl font-bold text-green-700" data-testid="revenue-today">₹{(metrics.revenue_today || 0).toLocaleString()}</p>
                <p className="text-xs text-green-600">Revenue Today</p>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardContent className="p-4 text-center">
                <TrendingUp className="h-6 w-6 mx-auto text-blue-600 mb-1" />
                <p className="text-2xl font-bold text-blue-700" data-testid="sales-today">{metrics.sales_today || 0}</p>
                <p className="text-xs text-blue-600">Sales Today</p>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-cyan-50 to-cyan-100 border-cyan-200">
              <CardContent className="p-4 text-center">
                <Users className="h-6 w-6 mx-auto text-cyan-600 mb-1" />
                <p className="text-2xl font-bold text-cyan-700" data-testid="active-workers">{metrics.active_workers_now || 0}</p>
                <p className="text-xs text-cyan-600">Active Now</p>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
              <CardContent className="p-4 text-center">
                <Activity className="h-6 w-6 mx-auto text-purple-600 mb-1" />
                <p className="text-2xl font-bold text-purple-700" data-testid="punched-in">{metrics.total_punched_in_today || 0}</p>
                <p className="text-xs text-purple-600">Punched In</p>
              </CardContent>
            </Card>
            
            <Card className={`bg-gradient-to-br ${(metrics.inactive_alerts || 0) > 0 ? 'from-orange-50 to-orange-100 border-orange-300' : 'from-gray-50 to-gray-100 border-gray-200'}`}>
              <CardContent className="p-4 text-center">
                <UserX className={`h-6 w-6 mx-auto ${(metrics.inactive_alerts || 0) > 0 ? 'text-orange-600' : 'text-gray-400'} mb-1`} />
                <p className={`text-2xl font-bold ${(metrics.inactive_alerts || 0) > 0 ? 'text-orange-700' : 'text-gray-500'}`} data-testid="inactive-alerts">{metrics.inactive_alerts || 0}</p>
                <p className={`text-xs ${(metrics.inactive_alerts || 0) > 0 ? 'text-orange-600' : 'text-gray-500'}`}>Inactive Alerts</p>
              </CardContent>
            </Card>
            
            <Card className={`bg-gradient-to-br ${(metrics.fraud_alerts_active || 0) > 0 ? 'from-red-50 to-red-100 border-red-300' : 'from-gray-50 to-gray-100 border-gray-200'}`}>
              <CardContent className="p-4 text-center">
                <ShieldAlert className={`h-6 w-6 mx-auto ${(metrics.fraud_alerts_active || 0) > 0 ? 'text-red-600' : 'text-gray-400'} mb-1`} />
                <p className={`text-2xl font-bold ${(metrics.fraud_alerts_active || 0) > 0 ? 'text-red-700' : 'text-gray-500'}`} data-testid="fraud-alerts">{metrics.fraud_alerts_active || 0}</p>
                <p className={`text-xs ${(metrics.fraud_alerts_active || 0) > 0 ? 'text-red-600' : 'text-gray-500'}`}>Fraud Alerts</p>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
              <CardContent className="p-4 text-center">
                <Clock className="h-6 w-6 mx-auto text-amber-600 mb-1" />
                <p className="text-2xl font-bold text-amber-700" data-testid="pending-expenses">{metrics.pending_expenses || 0}</p>
                <p className="text-xs text-amber-600">Pending Expenses</p>
              </CardContent>
            </Card>
            
            <Card className="bg-gradient-to-br from-indigo-50 to-indigo-100 border-indigo-200">
              <CardContent className="p-4 text-center">
                <CheckCircle className="h-6 w-6 mx-auto text-indigo-600 mb-1" />
                <p className="text-2xl font-bold text-indigo-700" data-testid="encashments-today">{metrics.encashments_today || 0}</p>
                <p className="text-xs text-indigo-600">Encashments</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Extended Stats Row */}
        {metrics && (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            <Card className="border-zinc-200">
              <CardContent className="p-3 text-center">
                <DollarSign className="h-5 w-5 mx-auto text-green-500 mb-1" />
                <p className="text-lg font-bold text-zinc-800" data-testid="revenue-month">₹{(metrics.revenue_month || 0).toLocaleString()}</p>
                <p className="text-[10px] text-zinc-500">Revenue (Month)</p>
              </CardContent>
            </Card>
            <Card className="border-zinc-200">
              <CardContent className="p-3 text-center">
                <TrendingUp className="h-5 w-5 mx-auto text-blue-500 mb-1" />
                <p className="text-lg font-bold text-zinc-800" data-testid="sales-month">{metrics.sales_month || 0}</p>
                <p className="text-[10px] text-zinc-500">Sales (Month)</p>
              </CardContent>
            </Card>
            <Card className="border-zinc-200">
              <CardContent className="p-3 text-center">
                <Briefcase className="h-5 w-5 mx-auto text-teal-500 mb-1" />
                <p className="text-lg font-bold text-zinc-800" data-testid="active-campaigns">{metrics.active_campaigns || 0}</p>
                <p className="text-[10px] text-zinc-500">Active Campaigns</p>
              </CardContent>
            </Card>
            <Card className="border-zinc-200">
              <CardContent className="p-3 text-center">
                <Ticket className="h-5 w-5 mx-auto text-violet-500 mb-1" />
                <p className="text-lg font-bold text-zinc-800" data-testid="coupons-available">{(metrics.total_coupons_available || 0).toLocaleString()}</p>
                <p className="text-[10px] text-zinc-500">Coupons Available</p>
              </CardContent>
            </Card>
            <Card className="border-zinc-200">
              <CardContent className="p-3 text-center">
                <Users className="h-5 w-5 mx-auto text-sky-500 mb-1" />
                <p className="text-lg font-bold text-zinc-800" data-testid="total-workers">{metrics.total_workers || 0}</p>
                <p className="text-[10px] text-zinc-500">Total Workers</p>
              </CardContent>
            </Card>
            <Card className="border-zinc-200">
              <CardContent className="p-3 text-center">
                <Building2 className="h-5 w-5 mx-auto text-orange-500 mb-1" />
                <p className="text-lg font-bold text-zinc-800" data-testid="total-branches">{metrics.total_branches || 0}</p>
                <p className="text-[10px] text-zinc-500">Total Branches</p>
              </CardContent>
            </Card>
            <Card className="border-zinc-200">
              <CardContent className="p-3 text-center">
                <MapPin className="h-5 w-5 mx-auto text-rose-500 mb-1" />
                <p className="text-lg font-bold text-zinc-800" data-testid="total-areas">{metrics.total_areas || 0}</p>
                <p className="text-[10px] text-zinc-500">Total Areas</p>
              </CardContent>
            </Card>
            <Card className="border-zinc-200">
              <CardContent className="p-3 text-center">
                <CalendarDays className="h-5 w-5 mx-auto text-fuchsia-500 mb-1" />
                <p className="text-lg font-bold text-zinc-800" data-testid="expenses-month">₹{(metrics.expenses_month || 0).toLocaleString()}</p>
                <p className="text-[10px] text-zinc-500">Expenses (Month)</p>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Fraud Alerts Panel */}
          <Card className="border-red-200">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-red-700">
                <ShieldAlert className="h-5 w-5" />
                Fraud Alerts
                {fraudAlerts.length > 0 && (
                  <Badge variant="destructive" className="ml-2">{fraudAlerts.length}</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {fraudAlerts.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <ShieldAlert className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>No active fraud alerts</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {fraudAlerts.map((alert) => (
                    <div 
                      key={alert.id} 
                      className="p-3 bg-red-50 rounded-lg border border-red-200"
                      data-testid={`fraud-alert-${alert.id}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge className={getSeverityColor(alert.severity)}>
                              {alert.severity}
                            </Badge>
                            <span className="text-sm font-medium text-red-800">
                              {alert.alert_type.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <p className="text-sm text-red-700">{alert.worker_name}</p>
                          {alert.details && (
                            <p className="text-xs text-red-600 mt-1">
                              {alert.details.expense_ratio && `Expense Ratio: ${(alert.details.expense_ratio * 100).toFixed(0)}%`}
                              {alert.details.usage_count && `Mobile used ${alert.details.usage_count} times`}
                            </p>
                          )}
                        </div>
                        <div className="flex gap-1">
                          <Button 
                            size="sm" 
                            variant="outline"
                            className="h-7 px-2 text-green-600 border-green-300 hover:bg-green-50"
                            onClick={() => handleResolveFraudAlert(alert.id)}
                          >
                            <CheckCircle className="h-3 w-3" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline"
                            className="h-7 px-2 text-gray-600 border-gray-300 hover:bg-gray-50"
                            onClick={() => handleDismissFraudAlert(alert.id)}
                          >
                            <XCircle className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Inactive Workers Panel */}
          <Card className="border-orange-200">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-orange-700">
                <UserX className="h-5 w-5" />
                Inactive Workers
                {inactiveWorkers.total_inactive > 0 && (
                  <Badge className="ml-2 bg-orange-500">{inactiveWorkers.total_inactive}</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {inactiveWorkers.workers.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Users className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>All workers are active</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {inactiveWorkers.workers.map((worker) => (
                    <div 
                      key={worker.alert_id} 
                      className="p-3 bg-orange-50 rounded-lg border border-orange-200"
                      data-testid={`inactive-worker-${worker.worker_id}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <p className="font-medium text-orange-800">{worker.worker_name}</p>
                          <p className="text-sm text-orange-600">{worker.area_name}</p>
                          <div className="flex items-center gap-2 mt-1 text-xs text-orange-600">
                            <Clock className="h-3 w-3" />
                            <span>Inactive: {worker.hours_inactive}h</span>
                            {worker.current_latitude && (
                              <>
                                <MapPin className="h-3 w-3 ml-2" />
                                <span>{worker.current_latitude.toFixed(4)}, {worker.current_longitude.toFixed(4)}</span>
                              </>
                            )}
                          </div>
                        </div>
                        <Button 
                          size="sm" 
                          variant="outline"
                          className="h-7 px-2 text-green-600 border-green-300 hover:bg-green-50"
                          onClick={() => handleResolveInactivity(worker.alert_id)}
                        >
                          <CheckCircle className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Worker Performance Rankings */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5 text-yellow-500" />
              Worker Performance Rankings
              <Badge variant="outline" className="ml-2">Top 10</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-gray-500 border-b">
                    <th className="pb-3 font-medium">Rank</th>
                    <th className="pb-3 font-medium">Worker</th>
                    <th className="pb-3 font-medium text-center">Score</th>
                    <th className="pb-3 font-medium text-center">Grade</th>
                    <th className="pb-3 font-medium text-right">Sales (MTD)</th>
                    <th className="pb-3 font-medium text-right">Revenue (MTD)</th>
                    <th className="pb-3 font-medium text-right">Avg/Day</th>
                  </tr>
                </thead>
                <tbody>
                  {workerScores.map((score, index) => (
                    <tr 
                      key={score.worker_id} 
                      className="border-b last:border-0 hover:bg-gray-50"
                      data-testid={`worker-rank-${index + 1}`}
                    >
                      <td className="py-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                          index === 0 ? 'bg-yellow-100 text-yellow-700' :
                          index === 1 ? 'bg-gray-100 text-gray-700' :
                          index === 2 ? 'bg-orange-100 text-orange-700' :
                          'bg-gray-50 text-gray-500'
                        }`}>
                          {index + 1}
                        </div>
                      </td>
                      <td className="py-3 font-medium">{score.worker_name}</td>
                      <td className="py-3 text-center">
                        <span className={`px-3 py-1 rounded-full font-bold ${getScoreColor(score.final_score)}`}>
                          {score.final_score}
                        </span>
                      </td>
                      <td className="py-3 text-center">
                        <Badge variant={score.grade.startsWith('A') ? 'default' : score.grade === 'B' || score.grade === 'B+' ? 'secondary' : 'outline'}>
                          {score.grade}
                        </Badge>
                      </td>
                      <td className="py-3 text-right font-medium">{score.metrics.total_sales_month}</td>
                      <td className="py-3 text-right font-medium">₹{score.metrics.total_revenue_month.toLocaleString()}</td>
                      <td className="py-3 text-right text-gray-600">{score.metrics.avg_sales_per_day}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {workerScores.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <BarChart3 className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>No worker data available</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Links */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Button variant="outline" className="h-auto py-4 flex-col" asChild>
            <a href="/admin/campaigns">
              <BarChart3 className="h-6 w-6 mb-2" />
              <span>Campaigns</span>
            </a>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex-col" asChild>
            <a href="/admin/workers">
              <Users className="h-6 w-6 mb-2" />
              <span>Workers</span>
            </a>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex-col" asChild>
            <a href="/admin/ledger">
              <DollarSign className="h-6 w-6 mb-2" />
              <span>Ledger</span>
            </a>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex-col" asChild>
            <a href="/admin/branches">
              <MapPin className="h-6 w-6 mb-2" />
              <span>Branches</span>
            </a>
          </Button>
        </div>
      </div>
    </Layout>
  );
}
