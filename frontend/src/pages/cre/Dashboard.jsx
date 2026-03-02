import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { 
  Phone, User, Ticket, Building2, Clock, Calendar,
  Loader2, RefreshCcw, CheckCircle, MessageSquare,
  Users, PhoneCall, AlertCircle, Search, Download,
  Filter, ArrowUpDown, ArrowUp, ArrowDown, Trash2
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function CREDashboard() {
  const [customers, setCustomers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [remarksDialogOpen, setRemarksDialogOpen] = useState(false);
  const [selectedCallLog, setSelectedCallLog] = useState(null);
  const [remarks, setRemarks] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  // Filters
  const [filter, setFilter] = useState('all'); // all, pending, called
  const [searchQuery, setSearchQuery] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [selectedCampaign, setSelectedCampaign] = useState('all');
  const [selectedBranch, setSelectedBranch] = useState('all');
  
  // Sorting
  const [sortColumn, setSortColumn] = useState('sold_at');
  const [sortDirection, setSortDirection] = useState('desc');
  
  // Tab
  const [activeTab, setActiveTab] = useState('table');
  
  // Unique campaigns and branches for filters
  const [campaigns, setCampaigns] = useState([]);
  const [branches, setBranches] = useState([]);

  useEffect(() => {
    fetchData();
    // Set default date range to today
    const today = new Date().toISOString().split('T')[0];
    setFromDate(today);
    setToDate(today);
  }, []);

  useEffect(() => {
    // Extract unique campaigns and branches
    const uniqueCampaigns = [...new Set(customers.map(c => c.campaign_name).filter(Boolean))];
    const uniqueBranches = [...new Set(customers.map(c => c.branch_name).filter(Boolean))];
    setCampaigns(uniqueCampaigns);
    setBranches(uniqueBranches);
  }, [customers]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      // Fetch stats
      const statsRes = await fetch(`${API_URL}/api/cre/dashboard/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
      
      // Fetch customers with date filter
      let url = `${API_URL}/api/cre/customers`;
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      if (params.toString()) url += `?${params.toString()}`;
      
      const customersRes = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (customersRes.ok) {
        setCustomers(await customersRes.json());
      }
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCall = async (customer) => {
    try {
      const token = localStorage.getItem('access_token');
      
      // Log the call
      const response = await fetch(`${API_URL}/api/cre/calls/${customer.coupon_id}/log`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedCallLog(data.call_log_id);
        
        // Open phone dialer
        window.location.href = `tel:${customer.customer_phone}`;
        
        // After a short delay, open remarks dialog
        setTimeout(() => {
          setRemarksDialogOpen(true);
        }, 1000);
      }
    } catch (error) {
      toast.error('Failed to log call');
    }
  };

  const submitRemarks = async () => {
    if (!remarks.trim() || remarks.trim().length < 3) {
      toast.error('Remarks are mandatory (minimum 3 characters)');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/cre/calls/${selectedCallLog}/remarks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ remarks: remarks.trim() })
      });

      if (response.ok) {
        toast.success('Remarks saved successfully');
        setRemarksDialogOpen(false);
        setRemarks('');
        setSelectedCallLog(null);
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to save remarks');
      }
    } catch (error) {
      toast.error('Failed to save remarks');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteCallLog = async (logId, customerName) => {
    if (!window.confirm(`Delete remark for "${customerName}"? This action cannot be undone.`)) return;
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/cre/call-log/${logId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        toast.success('Call log deleted');
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete');
      }
    } catch (error) {
      toast.error('Failed to delete call log');
    }
  };

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };

  const getSortIcon = (column) => {
    if (sortColumn !== column) return <ArrowUpDown className="h-3 w-3 ml-1 text-zinc-400" />;
    return sortDirection === 'asc' 
      ? <ArrowUp className="h-3 w-3 ml-1 text-blue-600" /> 
      : <ArrowDown className="h-3 w-3 ml-1 text-blue-600" />;
  };

  // Filter and sort customers
  const filteredCustomers = customers
    .filter(c => {
      // Status filter
      if (filter === 'pending' && c.call_status !== 'PENDING') return false;
      if (filter === 'called' && c.call_status === 'PENDING') return false;
      
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchName = c.customer_name?.toLowerCase().includes(query);
        const matchPhone = c.customer_phone?.includes(query);
        const matchCoupon = c.coupon_code?.toLowerCase().includes(query);
        if (!matchName && !matchPhone && !matchCoupon) return false;
      }
      
      // Campaign filter
      if (selectedCampaign !== 'all' && c.campaign_name !== selectedCampaign) return false;
      
      // Branch filter
      if (selectedBranch !== 'all' && c.branch_name !== selectedBranch) return false;
      
      // Date filter
      if (fromDate || toDate) {
        const saleDate = new Date(c.sold_at).toISOString().split('T')[0];
        if (fromDate && saleDate < fromDate) return false;
        if (toDate && saleDate > toDate) return false;
      }
      
      return true;
    })
    .sort((a, b) => {
      let aVal = a[sortColumn];
      let bVal = b[sortColumn];
      
      if (sortColumn === 'sold_at') {
        aVal = new Date(aVal || 0).getTime();
        bVal = new Date(bVal || 0).getTime();
      }
      
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

  const formatDate = (date) => {
    if (!date) return '-';
    return new Date(date).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDateShort = (date) => {
    if (!date) return '-';
    return new Date(date).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const exportToCSV = () => {
    const headers = ['Date', 'Customer Name', 'Mobile', 'Coupon Code', 'Campaign', 'Branch', 'Worker', 'Status', 'Remarks'];
    const rows = filteredCustomers.map(c => [
      formatDateShort(c.sold_at),
      c.customer_name,
      c.customer_phone,
      c.coupon_code,
      c.campaign_name,
      c.branch_name,
      c.worker_name || 'N/A',
      c.call_status,
      c.last_remarks || ''
    ]);
    
    const csv = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cre_customers_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Export complete');
  };

  const setQuickDateFilter = (type) => {
    const today = new Date();
    
    switch (type) {
      case 'today':
        const todayStr = today.toISOString().split('T')[0];
        setFromDate(todayStr);
        setToDate(todayStr);
        break;
      case 'yesterday':
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];
        setFromDate(yesterdayStr);
        setToDate(yesterdayStr);
        break;
      case 'week':
        const weekAgo = new Date(today);
        weekAgo.setDate(weekAgo.getDate() - 7);
        setFromDate(weekAgo.toISOString().split('T')[0]);
        setToDate(today.toISOString().split('T')[0]);
        break;
      case 'month':
        const monthAgo = new Date(today);
        monthAgo.setDate(monthAgo.getDate() - 30);
        setFromDate(monthAgo.toISOString().split('T')[0]);
        setToDate(today.toISOString().split('T')[0]);
        break;
      default:
        setFromDate('');
        setToDate('');
    }
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="cre-dashboard">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              CRE Dashboard
            </h1>
            <p className="text-zinc-500 mt-1">Customer calls and follow-ups</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={exportToCSV} data-testid="export-csv-btn">
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            <Button variant="outline" onClick={() => { setLoading(true); fetchData(); }}>
              <RefreshCcw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Users className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Today's Customers</p>
                  <p className="text-2xl font-bold">{stats?.today_total_customers || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <PhoneCall className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Calls Made Today</p>
                  <p className="text-2xl font-bold">{stats?.today_calls_made || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <AlertCircle className="h-5 w-5 text-yellow-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Pending Calls</p>
                  <p className="text-2xl font-bold">{stats?.pending_calls || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="table">Excel Table View</TabsTrigger>
            <TabsTrigger value="quick">Quick Call</TabsTrigger>
          </TabsList>

          {/* Excel Table View */}
          <TabsContent value="table" className="mt-4">
            {/* Filters */}
            <Card className="mb-4">
              <CardContent className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
                  {/* Search */}
                  <div className="lg:col-span-2">
                    <Label className="text-xs text-zinc-500">Search</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                      <Input
                        placeholder="Name, phone, coupon..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                        data-testid="search-input"
                      />
                    </div>
                  </div>

                  {/* Quick Date Buttons */}
                  <div>
                    <Label className="text-xs text-zinc-500">Quick Filter</Label>
                    <div className="flex gap-1">
                      <Button size="sm" variant={fromDate === new Date().toISOString().split('T')[0] && fromDate === toDate ? 'default' : 'outline'} onClick={() => setQuickDateFilter('today')}>Today</Button>
                      <Button size="sm" variant="outline" onClick={() => setQuickDateFilter('yesterday')}>Yesterday</Button>
                      <Button size="sm" variant="outline" onClick={() => setQuickDateFilter('week')}>7D</Button>
                    </div>
                  </div>

                  {/* From Date */}
                  <div>
                    <Label className="text-xs text-zinc-500">From Date</Label>
                    <Input
                      type="date"
                      value={fromDate}
                      onChange={(e) => setFromDate(e.target.value)}
                      data-testid="from-date-input"
                    />
                  </div>

                  {/* To Date */}
                  <div>
                    <Label className="text-xs text-zinc-500">To Date</Label>
                    <Input
                      type="date"
                      value={toDate}
                      onChange={(e) => setToDate(e.target.value)}
                      data-testid="to-date-input"
                    />
                  </div>

                  {/* Campaign Filter */}
                  <div>
                    <Label className="text-xs text-zinc-500">Campaign</Label>
                    <select
                      className="w-full h-10 px-3 border rounded-md text-sm"
                      value={selectedCampaign}
                      onChange={(e) => setSelectedCampaign(e.target.value)}
                    >
                      <option value="all">All Campaigns</option>
                      {campaigns.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>

                {/* Status Filter */}
                <div className="flex gap-2 mt-4">
                  <Button size="sm" variant={filter === 'all' ? 'default' : 'outline'} onClick={() => setFilter('all')}>
                    All ({customers.length})
                  </Button>
                  <Button size="sm" variant={filter === 'pending' ? 'default' : 'outline'} onClick={() => setFilter('pending')}>
                    Pending ({customers.filter(c => c.call_status === 'PENDING').length})
                  </Button>
                  <Button size="sm" variant={filter === 'called' ? 'default' : 'outline'} onClick={() => setFilter('called')}>
                    Called ({customers.filter(c => c.call_status !== 'PENDING').length})
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Excel-style Table */}
            <Card>
              <CardContent className="p-0">
                {loading ? (
                  <div className="flex items-center justify-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                  </div>
                ) : filteredCustomers.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <Users className="h-12 w-12 text-zinc-300 mb-4" />
                    <p className="text-zinc-500">No customers found</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader className="bg-zinc-50 sticky top-0">
                        <TableRow>
                          <TableHead 
                            className="cursor-pointer hover:bg-zinc-100 whitespace-nowrap"
                            onClick={() => handleSort('sold_at')}
                          >
                            Date {getSortIcon('sold_at')}
                          </TableHead>
                          <TableHead 
                            className="cursor-pointer hover:bg-zinc-100 whitespace-nowrap"
                            onClick={() => handleSort('customer_name')}
                          >
                            Customer {getSortIcon('customer_name')}
                          </TableHead>
                          <TableHead className="whitespace-nowrap">Mobile</TableHead>
                          <TableHead className="whitespace-nowrap">Coupon</TableHead>
                          <TableHead 
                            className="cursor-pointer hover:bg-zinc-100 whitespace-nowrap"
                            onClick={() => handleSort('campaign_name')}
                          >
                            Campaign {getSortIcon('campaign_name')}
                          </TableHead>
                          <TableHead className="whitespace-nowrap">Branch</TableHead>
                          <TableHead className="whitespace-nowrap">Worker</TableHead>
                          <TableHead className="whitespace-nowrap">Status</TableHead>
                          <TableHead className="whitespace-nowrap">Remarks</TableHead>
                          <TableHead className="whitespace-nowrap text-center">Call</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredCustomers.map((customer) => (
                          <TableRow 
                            key={customer.coupon_id} 
                            className={customer.call_status === 'PENDING' ? 'bg-yellow-50/50' : ''}
                          >
                            <TableCell className="whitespace-nowrap text-sm">
                              {formatDateShort(customer.sold_at)}
                            </TableCell>
                            <TableCell className="font-medium whitespace-nowrap">
                              {customer.customer_name}
                            </TableCell>
                            <TableCell className="font-mono text-sm whitespace-nowrap">
                              {customer.customer_phone}
                            </TableCell>
                            <TableCell>
                              <code className="px-2 py-1 bg-zinc-100 rounded text-xs">
                                {customer.coupon_code}
                              </code>
                            </TableCell>
                            <TableCell className="text-sm whitespace-nowrap">
                              {customer.campaign_name}
                            </TableCell>
                            <TableCell className="text-sm whitespace-nowrap">
                              {customer.branch_name}
                            </TableCell>
                            <TableCell className="text-sm whitespace-nowrap">
                              {customer.worker_name || '-'}
                            </TableCell>
                            <TableCell>
                              <Badge className={
                                customer.call_status === 'PENDING' 
                                  ? 'bg-yellow-100 text-yellow-800' 
                                  : 'bg-green-100 text-green-800'
                              }>
                                {customer.call_status}
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-32 truncate text-xs text-zinc-500" title={customer.last_remarks}>
                              <div className="flex items-center gap-1">
                                <span className="truncate">{customer.last_remarks || '-'}</span>
                                {customer.last_call_log_id && (
                                  <button
                                    onClick={() => handleDeleteCallLog(customer.last_call_log_id, customer.customer_name)}
                                    className="flex-shrink-0 p-1 hover:bg-red-50 rounded text-zinc-400 hover:text-red-500 transition-colors"
                                    title="Delete remark"
                                    data-testid={`delete-remark-${customer.coupon_id}`}
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </button>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="text-center">
                              <Button
                                size="sm"
                                className="bg-green-600 hover:bg-green-700 h-8"
                                onClick={() => handleCall(customer)}
                                data-testid={`call-btn-${customer.coupon_id}`}
                              >
                                <Phone className="h-3 w-3" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
            
            {/* Table Footer */}
            <div className="flex items-center justify-between mt-2 text-sm text-zinc-500">
              <span>Showing {filteredCustomers.length} of {customers.length} customers</span>
            </div>
          </TabsContent>

          {/* Quick Call View */}
          <TabsContent value="quick" className="mt-4">
            {/* Search Bar */}
            <div className="mb-4">
              <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                <Input
                  placeholder="Search by name or phone..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                  data-testid="quick-search-input"
                />
              </div>
            </div>

            {/* Contact List */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PhoneCall className="h-5 w-5 text-green-600" />
                  Quick Dial Contacts ({filteredCustomers.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center h-40">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                  </div>
                ) : filteredCustomers.length === 0 ? (
                  <div className="text-center py-8 text-zinc-500">
                    No contacts found
                  </div>
                ) : (
                  <div className="max-h-[60vh] overflow-y-auto space-y-2">
                    {filteredCustomers.map((customer) => (
                      <div 
                        key={customer.coupon_id}
                        className={`flex items-center justify-between p-3 rounded-lg border ${
                          customer.call_status === 'PENDING' ? 'bg-yellow-50 border-yellow-200' : 'bg-zinc-50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            customer.call_status === 'PENDING' ? 'bg-yellow-100' : 'bg-green-100'
                          }`}>
                            <User className={`h-5 w-5 ${customer.call_status === 'PENDING' ? 'text-yellow-600' : 'text-green-600'}`} />
                          </div>
                          <div>
                            <p className="font-medium">{customer.customer_name}</p>
                            <p className="text-sm text-zinc-500 font-mono">{customer.customer_phone}</p>
                          </div>
                        </div>
                        <a
                          href={`tel:${customer.customer_phone}`}
                          onClick={() => handleCall(customer)}
                          className="p-3 bg-green-600 hover:bg-green-700 text-white rounded-full transition-colors"
                          data-testid={`quick-call-${customer.coupon_id}`}
                        >
                          <Phone className="h-5 w-5" />
                        </a>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Remarks Dialog */}
        <Dialog open={remarksDialogOpen} onOpenChange={(open) => {
          if (!open && !remarks.trim()) {
            toast.warning('Remarks are mandatory after call');
            return;
          }
          setRemarksDialogOpen(open);
        }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-blue-600" />
                Add Call Remarks (Mandatory)
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <Textarea
                placeholder="Enter your remarks about the call..."
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                rows={4}
                data-testid="remarks-input"
              />
              <p className="text-xs text-zinc-500">
                Remarks are mandatory before closing this dialog.
              </p>
            </div>
            <DialogFooter>
              <Button
                onClick={submitRemarks}
                disabled={submitting || !remarks.trim()}
                data-testid="submit-remarks-btn"
              >
                {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                Save Remarks
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
