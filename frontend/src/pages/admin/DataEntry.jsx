import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Loader2, ClipboardList, Download, Search, RefreshCcw } from 'lucide-react';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function AdminDataEntry() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [todayCount, setTodayCount] = useState(0);
  const [workers, setWorkers] = useState([]);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [workerFilter, setWorkerFilter] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.append('search', searchQuery.trim());
      if (workerFilter !== 'all') params.append('worker_id', workerFilter);
      if (dateFrom) params.append('date_from', new Date(dateFrom).toISOString());
      if (dateTo) params.append('date_to', new Date(dateTo + 'T23:59:59').toISOString());
      
      const res = await fetch(`${API_URL}/api/admin/data-entry?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setEntries(data.entries || []);
        setTotal(data.total || 0);
        setTodayCount(data.today_count || 0);
        if (data.workers) setWorkers(data.workers);
      } else {
        toast.error('Failed to load data entries');
      }
    } catch {
      toast.error('Failed to load data entries');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, workerFilter, dateFrom, dateTo]);

  useEffect(() => {
    const debounce = setTimeout(() => fetchEntries(), 300);
    return () => clearTimeout(debounce);
  }, [fetchEntries]);

  const handleExportExcel = () => {
    if (entries.length === 0) {
      toast.error('No data to export');
      return;
    }
    
    const exportData = entries.map(e => ({
      'Customer Name': e.customer_name || '',
      'Mobile Number': e.mobile_number || '',
      'City': e.city || '',
      'Notes': e.notes || '',
      'Created At': e.created_at ? new Date(e.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : '',
      'Worker Name': e.worker_name || '',
    }));
    
    const ws = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Data Entries');
    XLSX.writeFile(wb, `FieldFlow_DataEntries_${new Date().toISOString().slice(0,10)}.xlsx`);
    toast.success(`Exported ${exportData.length} records`);
  };

  const formatDate = (d) => {
    if (!d) return '-';
    return new Date(d).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <Layout>
      <div className="space-y-4" data-testid="admin-data-entry-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 flex items-center gap-2">
              <ClipboardList className="h-6 w-6" style={{ color: '#ED1C24' }} />
              Worker Data Entries
            </h1>
            <p className="text-sm text-zinc-500 mt-1">
              Total entries: {total}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-green-50 border border-green-200 px-4 py-2 rounded-lg text-center" data-testid="today-entry-count">
              <p className="text-xl font-bold text-green-700">{todayCount}</p>
              <p className="text-[10px] text-green-600 font-medium">Today's Entries</p>
            </div>
            <Button variant="outline" size="sm" onClick={fetchEntries} data-testid="refresh-data-entry-btn">
              <RefreshCcw className="h-4 w-4 mr-1" /> Refresh
            </Button>
            <Button 
              size="sm" 
              className="bg-green-600 hover:bg-green-700 text-white"
              onClick={handleExportExcel}
              data-testid="export-data-entry-excel-btn"
            >
              <Download className="h-4 w-4 mr-1" /> Download Excel
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                <Input
                  placeholder="Search name, mobile, city..."
                  className="pl-10"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  data-testid="search-data-entry"
                />
              </div>
              <Select value={workerFilter} onValueChange={setWorkerFilter}>
                <SelectTrigger className="w-44" data-testid="worker-filter">
                  <SelectValue placeholder="Filter by Worker" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Workers</SelectItem>
                  {workers.map(w => (
                    <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-36"
                placeholder="From"
                data-testid="date-from-filter"
              />
              <Input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-36"
                placeholder="To"
                data-testid="date-to-filter"
              />
            </div>
          </CardContent>
        </Card>

        {/* Table */}
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-zinc-50">
                    <TableHead>Customer Name</TableHead>
                    <TableHead>Mobile Number</TableHead>
                    <TableHead>City</TableHead>
                    <TableHead>Notes</TableHead>
                    <TableHead>Created At</TableHead>
                    <TableHead>Worker Name</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-12">
                        <Loader2 className="h-6 w-6 animate-spin mx-auto text-zinc-400" />
                      </TableCell>
                    </TableRow>
                  ) : entries.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-12 text-zinc-400">
                        No data entries found
                      </TableCell>
                    </TableRow>
                  ) : (
                    entries.map((entry) => (
                      <TableRow key={entry.id} className="hover:bg-zinc-50">
                        <TableCell className="font-medium">{entry.customer_name}</TableCell>
                        <TableCell className="font-mono text-sm">{entry.mobile_number}</TableCell>
                        <TableCell>{entry.city}</TableCell>
                        <TableCell className="text-sm text-zinc-500 max-w-[200px] truncate" title={entry.notes}>
                          {entry.notes || '-'}
                        </TableCell>
                        <TableCell className="text-xs text-zinc-500">{formatDate(entry.created_at)}</TableCell>
                        <TableCell className="text-sm font-medium">{entry.worker_name || '-'}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
