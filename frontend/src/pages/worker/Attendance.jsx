import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { attendanceAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { 
  Clock, 
  MapPin, 
  Loader2, 
  CheckCircle, 
  LogIn, 
  LogOut,
  AlertCircle
} from 'lucide-react';
import { formatTime, getCurrentPosition, getGPSAccuracyLabel } from '../../lib/utils';
import { toast } from 'sonner';

export default function AttendancePage() {
  const [attendance, setAttendance] = useState({ punchedIn: false, punchedOut: false });
  const [loading, setLoading] = useState(true);
  const [punching, setPunching] = useState(false);
  const [location, setLocation] = useState(null);
  const [gettingLocation, setGettingLocation] = useState(false);

  const fetchAttendance = async () => {
    try {
      const response = await attendanceAPI.getToday();
      const data = response.data;
      
      // New API returns a single object with status
      setAttendance({
        punchedIn: !!data.punch_in_time,
        punchedOut: !!data.punch_out_time,
        punchInTime: data.punch_in_time,
        punchOutTime: data.punch_out_time,
        status: data.status,
        durationMinutes: data.duration_minutes,
        durationFormatted: data.duration_formatted
      });
    } catch (error) {
      console.error('Failed to fetch attendance:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttendance();
  }, []);

  const getLocation = async () => {
    setGettingLocation(true);
    try {
      const pos = await getCurrentPosition();
      setLocation(pos);
      toast.success('Location captured successfully');
      return pos;
    } catch (error) {
      console.error('Failed to get location:', error);
      toast.error('Failed to get location. Please enable GPS.');
      return null;
    } finally {
      setGettingLocation(false);
    }
  };

  const handlePunchIn = async () => {
    const loc = location || await getLocation();
    if (!loc) return;

    setPunching(true);
    try {
      await attendanceAPI.punchIn({
        latitude: loc.latitude,
        longitude: loc.longitude,
        accuracy: loc.accuracy
      });
      toast.success('Punched in successfully!');
      fetchAttendance();
    } catch (error) {
      console.error('Failed to punch in:', error);
      toast.error(error.response?.data?.detail || 'Failed to punch in');
    } finally {
      setPunching(false);
    }
  };

  const handlePunchOut = async () => {
    const loc = location || await getLocation();
    if (!loc) return;

    setPunching(true);
    try {
      await attendanceAPI.punchOut({
        latitude: loc.latitude,
        longitude: loc.longitude,
        accuracy: loc.accuracy
      });
      toast.success('Punched out successfully!');
      fetchAttendance();
    } catch (error) {
      console.error('Failed to punch out:', error);
      toast.error(error.response?.data?.detail || 'Failed to punch out');
    } finally {
      setPunching(false);
    }
  };

  const accuracyInfo = location ? getGPSAccuracyLabel(location.accuracy) : null;

  return (
    <Layout>
      <div className="space-y-6 max-w-xl mx-auto" data-testid="attendance-page">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
            Attendance
          </h1>
          <p className="text-zinc-500 mt-1">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        {/* Status */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <>
            {/* Punch Button */}
            <div className="flex justify-center py-8">
              {!attendance.punchedIn ? (
                <button
                  onClick={handlePunchIn}
                  disabled={punching || gettingLocation}
                  className="punch-button punch-button-in"
                  data-testid="punch-in-btn"
                >
                  {punching ? (
                    <Loader2 className="h-8 w-8 animate-spin" />
                  ) : (
                    <>
                      <LogIn className="h-10 w-10 mb-2" />
                      <span className="text-lg">Punch In</span>
                    </>
                  )}
                </button>
              ) : !attendance.punchedOut ? (
                <button
                  onClick={handlePunchOut}
                  disabled={punching || gettingLocation}
                  className="punch-button punch-button-out"
                  data-testid="punch-out-btn"
                >
                  {punching ? (
                    <Loader2 className="h-8 w-8 animate-spin" />
                  ) : (
                    <>
                      <LogOut className="h-10 w-10 mb-2" />
                      <span className="text-lg">Punch Out</span>
                    </>
                  )}
                </button>
              ) : (
                <div className="w-32 h-32 rounded-full bg-green-100 flex flex-col items-center justify-center">
                  <CheckCircle className="h-10 w-10 text-green-600 mb-2" />
                  <span className="text-green-600 font-semibold">Complete</span>
                </div>
              )}
            </div>

            {/* Location Button */}
            {(!attendance.punchedIn || (attendance.punchedIn && !attendance.punchedOut)) && (
              <div className="flex justify-center">
                <Button
                  variant="outline"
                  onClick={getLocation}
                  disabled={gettingLocation}
                  data-testid="get-location-btn"
                >
                  {gettingLocation ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <MapPin className="h-4 w-4 mr-2" />
                  )}
                  {location ? 'Update Location' : 'Get Location'}
                </Button>
              </div>
            )}

            {/* Location Info */}
            {location && (
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <MapPin className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="text-sm font-medium">Current Location</p>
                        <p className="text-xs text-zinc-500 font-mono">
                          {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
                        </p>
                      </div>
                    </div>
                    {accuracyInfo && (
                      <div className={`text-right ${accuracyInfo.color}`}>
                        <p className="text-xs font-medium">{accuracyInfo.label} Accuracy</p>
                        <p className="text-xs">±{Math.round(location.accuracy)}m</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Today's Record */}
            <Card>
              <CardHeader>
                <CardTitle className="font-['Barlow_Condensed'] text-lg">Today's Record</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${attendance.punchedIn ? 'bg-green-100' : 'bg-zinc-200'}`}>
                      <LogIn className={`h-5 w-5 ${attendance.punchedIn ? 'text-green-600' : 'text-zinc-400'}`} />
                    </div>
                    <div>
                      <p className="font-medium">Punch In</p>
                      <p className="text-sm text-zinc-500">
                        {attendance.punchedIn ? formatTime(attendance.punchInTime) : 'Not recorded'}
                      </p>
                    </div>
                  </div>
                  {attendance.punchedIn && (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  )}
                </div>

                <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${attendance.punchedOut ? 'bg-green-100' : 'bg-zinc-200'}`}>
                      <LogOut className={`h-5 w-5 ${attendance.punchedOut ? 'text-green-600' : 'text-zinc-400'}`} />
                    </div>
                    <div>
                      <p className="font-medium">Punch Out</p>
                      <p className="text-sm text-zinc-500">
                        {attendance.punchedOut ? formatTime(attendance.punchOutTime) : 'Not recorded'}
                      </p>
                    </div>
                  </div>
                  {attendance.punchedOut && (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  )}
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
}
