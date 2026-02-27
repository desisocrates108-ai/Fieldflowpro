import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { attendanceAPI } from '../../lib/api';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { 
  Clock, 
  Ticket, 
  ClipboardList, 
  Loader2,
  CheckCircle,
  AlertCircle,
  Camera,
  Package,
  Edit2
} from 'lucide-react';
import { formatTime } from '../../lib/utils';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const THEME_COLOR = '#ED1C24';

export default function WorkerDashboard() {
  const { user } = useAuth();
  const [attendance, setAttendance] = useState(null);
  const [couponSummary, setCouponSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
  const [newPossessionCount, setNewPossessionCount] = useState('');
  const [updating, setUpdating] = useState(false);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      // Fetch attendance - new API returns single object
      const attendanceRes = await attendanceAPI.getToday();
      const data = attendanceRes.data;
      
      setAttendance({
        punchedIn: !!data.punch_in_time,
        punchedOut: !!data.punch_out_time,
        punchInTime: data.punch_in_time,
        punchOutTime: data.punch_out_time,
        status: data.status,
        durationFormatted: data.duration_formatted
      });
      
      // Fetch coupon summary
      const summaryRes = await fetch(`${BACKEND_URL}/api/coupons/summary`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (summaryRes.ok) {
        const summary = await summaryRes.json();
        setCouponSummary(summary);
        setNewPossessionCount(summary.coupon_possession_count.toString());
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUpdatePossession = async () => {
    const count = parseInt(newPossessionCount);
    if (isNaN(count) || count < 0) {
      toast.error('Please enter a valid number');
      return;
    }

    setUpdating(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${BACKEND_URL}/api/workers/${user.id}/coupons`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ coupon_possession_count: count })
      });

      if (!res.ok) {
        throw new Error('Failed to update');
      }

      toast.success('Possession count updated');
      setUpdateDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error('Failed to update possession count');
    } finally {
      setUpdating(false);
    }
  };

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

        {/* MY COUPONS Section */}
        <Card className="border-2" style={{ borderColor: `${THEME_COLOR}40` }}>
          <CardHeader className="pb-2">
            <CardTitle className="font-['Barlow_Condensed'] text-xl flex items-center gap-2">
              <Package className="h-5 w-5" style={{ color: THEME_COLOR }} />
              MY COUPONS
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="animate-pulse space-y-3">
                <div className="h-12 bg-zinc-100 rounded" />
                <div className="h-12 bg-zinc-100 rounded" />
              </div>
            ) : (
              <div className="space-y-4">
                {/* Possession Count */}
                <div className="flex items-center justify-between p-4 rounded-lg" style={{ backgroundColor: `${THEME_COLOR}10` }}>
                  <div>
                    <p className="text-sm text-zinc-600">Coupons In Possession</p>
                    <p className="text-3xl font-bold font-['Barlow_Condensed']" style={{ color: THEME_COLOR }}>
                      {couponSummary?.coupon_possession_count || 0}
                    </p>
                  </div>
                  <Dialog open={updateDialogOpen} onOpenChange={setUpdateDialogOpen}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" data-testid="update-possession-btn">
                        <Edit2 className="h-4 w-4 mr-1" />
                        Update
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle className="font-['Barlow_Condensed']">Update Coupon Count</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <p className="text-sm text-zinc-600">
                          Enter the number of physical coupons you currently have.
                        </p>
                        <Input
                          type="number"
                          min="0"
                          value={newPossessionCount}
                          onChange={(e) => setNewPossessionCount(e.target.value)}
                          placeholder="Enter count"
                          data-testid="possession-count-input"
                        />
                        <Button 
                          onClick={handleUpdatePossession}
                          className="w-full"
                          style={{ backgroundColor: THEME_COLOR }}
                          disabled={updating}
                          data-testid="confirm-update-btn"
                        >
                          {updating ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Updating...
                            </>
                          ) : (
                            'Confirm Update'
                          )}
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>

                {/* Issued Count */}
                <div className="flex items-center justify-between p-4 bg-zinc-50 rounded-lg">
                  <div>
                    <p className="text-sm text-zinc-600">Coupons Issued</p>
                    <p className="text-2xl font-bold font-['Barlow_Condensed']">
                      {couponSummary?.coupons_issued || 0}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-zinc-500">Pending: {couponSummary?.coupons_pending || 0}</p>
                    <p className="text-xs text-green-600">Verified: {couponSummary?.coupons_verified || 0}</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Warning if no coupons in possession */}
        {couponSummary && couponSummary.coupon_possession_count === 0 && (
          <Card className="border-yellow-200 bg-yellow-50">
            <CardContent className="p-4 flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-600" />
              <div>
                <p className="font-medium text-yellow-800">No coupons in possession</p>
                <p className="text-sm text-yellow-700">Update your coupon count to start issuing coupons.</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
