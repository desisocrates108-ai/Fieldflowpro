import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { attendanceAPI, couponAPI, taskAPI } from '../../lib/api';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { 
  Clock, 
  Ticket, 
  ClipboardList, 
  MapPin, 
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { formatTime } from '../../lib/utils';
import { toast } from 'sonner';

export default function WorkerDashboard() {
  const { user } = useAuth();
  const [attendance, setAttendance] = useState(null);
  const [todayCoupons, setTodayCoupons] = useState(0);
  const [pendingTasks, setPendingTasks] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [attendanceRes, couponsRes, tasksRes] = await Promise.all([
        attendanceAPI.getToday(),
        couponAPI.getAll(),
        taskAPI.getAll()
      ]);
      
      const records = attendanceRes.data;
      const punchIn = records.find(r => r.type === 'PUNCH_IN');
      const punchOut = records.find(r => r.type === 'PUNCH_OUT');
      
      setAttendance({
        punchedIn: !!punchIn,
        punchedOut: !!punchOut,
        punchInTime: punchIn?.timestamp,
        punchOutTime: punchOut?.timestamp
      });
      
      // Count today's coupons
      const today = new Date().toISOString().split('T')[0];
      const todayCount = couponsRes.data.filter(c => 
        c.issued_at.split('T')[0] === today
      ).length;
      setTodayCoupons(todayCount);
      
      // Count pending tasks
      const pending = tasksRes.data.filter(t => 
        t.status === 'PENDING' || t.status === 'IN_PROGRESS'
      ).length;
      setPendingTasks(pending);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getAttendanceStatus = () => {
    if (!attendance) return null;
    
    if (attendance.punchedOut) {
      return {
        icon: CheckCircle,
        text: `Completed • Out at ${formatTime(attendance.punchOutTime)}`,
        color: 'text-green-600',
        bgColor: 'bg-green-50'
      };
    }
    
    if (attendance.punchedIn) {
      return {
        icon: Clock,
        text: `Working • In at ${formatTime(attendance.punchInTime)}`,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50'
      };
    }
    
    return {
      icon: AlertCircle,
      text: 'Not punched in',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50'
    };
  };

  const status = getAttendanceStatus();

  return (
    <Layout>
      <div className="space-y-6" data-testid="worker-dashboard">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
            Good {new Date().getHours() < 12 ? 'Morning' : new Date().getHours() < 18 ? 'Afternoon' : 'Evening'}, {user?.name?.split(' ')[0]}
          </h1>
          <p className="text-zinc-500 mt-1">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        {/* Attendance Status Card */}
        {loading ? (
          <Card className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-16 bg-zinc-100 rounded" />
            </CardContent>
          </Card>
        ) : status && (
          <Card className={status.bgColor}>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-full ${status.bgColor}`}>
                  <status.icon className={`h-8 w-8 ${status.color}`} />
                </div>
                <div>
                  <p className="text-sm text-zinc-600">Today's Attendance</p>
                  <p className={`text-lg font-semibold ${status.color}`}>{status.text}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-4">
          <Card className="card-interactive" data-testid="coupons-today-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500">Coupons Today</p>
                  <p className="text-3xl font-bold font-['Barlow_Condensed'] mt-1">
                    {loading ? '-' : todayCoupons}
                  </p>
                </div>
                <div className="p-3 bg-purple-100 rounded-lg">
                  <Ticket className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="card-interactive" data-testid="pending-tasks-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500">Pending Tasks</p>
                  <p className="text-3xl font-bold font-['Barlow_Condensed'] mt-1">
                    {loading ? '-' : pendingTasks}
                  </p>
                </div>
                <div className="p-3 bg-orange-100 rounded-lg">
                  <ClipboardList className="h-6 w-6 text-orange-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Barlow_Condensed']">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Button 
              className="h-auto py-4 justify-start" 
              variant={attendance?.punchedIn && !attendance?.punchedOut ? "default" : "outline"}
              asChild
            >
              <a href="/worker/attendance">
                <Clock className="h-5 w-5 mr-3" />
                <div className="text-left">
                  <p className="font-medium">
                    {!attendance?.punchedIn ? 'Punch In' : !attendance?.punchedOut ? 'Punch Out' : 'View Attendance'}
                  </p>
                  <p className="text-xs opacity-80">Record your attendance</p>
                </div>
              </a>
            </Button>

            <Button 
              className="h-auto py-4 justify-start" 
              variant="outline"
              disabled={!attendance?.punchedIn}
              asChild
            >
              <a href="/worker/coupons">
                <Ticket className="h-5 w-5 mr-3" />
                <div className="text-left">
                  <p className="font-medium">Issue Coupon</p>
                  <p className="text-xs text-zinc-500">Create new coupon</p>
                </div>
              </a>
            </Button>

            <Button className="h-auto py-4 justify-start" variant="outline" asChild>
              <a href="/worker/my-coupons">
                <Ticket className="h-5 w-5 mr-3" />
                <div className="text-left">
                  <p className="font-medium">My Coupons</p>
                  <p className="text-xs text-zinc-500">View issued coupons</p>
                </div>
              </a>
            </Button>

            <Button className="h-auto py-4 justify-start" variant="outline" asChild>
              <a href="/worker/tasks">
                <ClipboardList className="h-5 w-5 mr-3" />
                <div className="text-left">
                  <p className="font-medium">My Tasks</p>
                  <p className="text-xs text-zinc-500">View assigned tasks</p>
                </div>
              </a>
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
