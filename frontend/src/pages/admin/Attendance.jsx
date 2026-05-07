import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { 
  Users, Clock, UserCheck, UserX, RefreshCcw, Search, Download,
  Calendar, Loader2, AlertCircle, CheckCircle
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function AdminAttendancePage() {
  const [stats, setStats] = useState(null);
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchData();
  }, [selectedDate]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      
      // Fetch stats
      const statsRes = await fetch(`${API_URL}/api/attendance/admin/stats?date=${selectedDate}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
      
      // Fetch workers attendance
      const workersRes = await fetch(`${API_URL}/api/attendance/admin/workers?date=${selectedDate}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (workersRes.ok) {
        setWorkers(await workersRes.json());
      }
    } catch (error) {
      console.error('Failed to load attendance data:', error);
      toast.error('Failed to load attendance data');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const token = localStorage.getItem('access_token');
      // Export last 30 days
      const endDate = selectedDate;
      const startDate = new Date(selectedDate);
      startDate.setDate(startDate.getDate() - 30);
      
      const response = await fetch(
        `${API_URL}/api/attendance/admin/export?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate}&format=csv`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      if (response.ok) {
        const data = await response.json();
        // Download CSV
        const blob = new Blob([data.csv_data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        toast.success('Attendance data exported');
      } else {
        toast.error('Failed to export data');
      }
    } catch (error) {
      toast.error('Export failed');
    } finally {
      setExporting(false);
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PRESENT':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Present</Badge>;
      case 'IN_PROGRESS':
        return <Badge className="bg-blue-100 text-blue-800"><Clock className="h-3 w-3 mr-1" />Working</Badge>;
      case 'ABSENT':
      default:
        return <Badge className="bg-red-100 text-red-800"><UserX className="h-3 w-3 mr-1" />Absent</Badge>;
    }
  };

  const filteredWorkers = workers.filter(w => {
    const matchesSearch = w.worker_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          w.worker_email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || w.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const isToday = selectedDate === new Date().toISOString().split('T')[0];

  return (
    <Layout>
      <div className="space-y-6" data-testid="admin-attendance-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              Attendance Dashboard
            </h1>
            <p className="text-zinc-500 mt-1">Track worker punch-in/out and working hours</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-36"
              data-testid="attendance-date-picker"
            />
            <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
              <RefreshCcw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport} disabled={exporting}>
              <Download className={`h-4 w-4 mr-1 ${exporting ? 'animate-spin' : ''}`} />
              Export
            </Button>
          </div>
        </div>

        {/* Date indicator */}
        {!isToday && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-yellow-600" />
            <span className="text-yellow-800">
              Viewing attendance for <strong>{new Date(selectedDate).toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</strong>
            </span>
          </div>
        )}

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Users className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-zinc-500">Total Workers</p>
                    <p className="text-2xl font-bold">{stats.total_workers}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <UserCheck className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-zinc-500">Present</p>
                    <p className="text-2xl font-bold text-green-600">{stats.present_today}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Clock className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-zinc-500">Working</p>
                    <p className="text-2xl font-bold text-blue-600">{stats.in_progress}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <UserX className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm text-zinc-500">Absent</p>
                    <p className="text-2xl font-bold text-red-600">{stats.absent_today}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Clock className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-zinc-500">Total Hours</p>
                    <p className="text-2xl font-bold">{stats.total_hours_today}h</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <Input
              placeholder="Search workers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
              data-testid="attendance-search"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40" data-testid="attendance-status-filter">
              <SelectValue placeholder="Filter status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="PRESENT">Present</SelectItem>
              <SelectItem value="IN_PROGRESS">Working</SelectItem>
              <SelectItem value="ABSENT">Absent</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Workers Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-[#ED1C24]" />
              </div>
            ) : filteredWorkers.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-zinc-500">
                <AlertCircle className="h-12 w-12 mb-2" />
                <p>No workers found</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Worker</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Punch In</TableHead>
                    <TableHead>Punch Out</TableHead>
                    <TableHead>Working Hours</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredWorkers.map((worker) => (
                    <TableRow key={worker.worker_id} data-testid={`worker-row-${worker.worker_id}`}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{worker.worker_name}</p>
                          <p className="text-sm text-zinc-500">{worker.worker_email}</p>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(worker.status)}</TableCell>
                      <TableCell>
                        {worker.punch_in_time ? (
                          <span className="font-mono text-green-600">{formatTime(worker.punch_in_time)}</span>
                        ) : (
                          <span className="text-zinc-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {worker.punch_out_time ? (
                          <span className="font-mono text-red-600">{formatTime(worker.punch_out_time)}</span>
                        ) : worker.status === 'IN_PROGRESS' ? (
                          <Badge variant="outline" className="text-blue-600 border-blue-300">Working...</Badge>
                        ) : (
                          <span className="text-zinc-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {worker.duration_formatted ? (
                          <span className="font-medium">{worker.duration_formatted}</span>
                        ) : worker.status === 'IN_PROGRESS' && worker.duration_minutes ? (
                          <span className="text-blue-600">{worker.duration_formatted || `${Math.floor(worker.duration_minutes / 60)}h ${worker.duration_minutes % 60}m`} (ongoing)</span>
                        ) : (
                          <span className="text-zinc-400">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
