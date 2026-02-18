import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { 
  Phone, User, Ticket, Building2, Clock, 
  Loader2, RefreshCcw, CheckCircle, MessageSquare,
  Users, PhoneCall, AlertCircle
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
  const [filter, setFilter] = useState('all'); // all, pending, called

  useEffect(() => {
    fetchData();
  }, []);

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
      
      // Fetch customers
      const customersRes = await fetch(`${API_URL}/api/cre/customers`, {
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

  const filteredCustomers = customers.filter(c => {
    if (filter === 'pending') return c.call_status === 'PENDING';
    if (filter === 'called') return c.call_status !== 'PENDING';
    return true;
  });

  const formatDate = (date) => {
    if (!date) return '-';
    return new Date(date).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="cre-dashboard">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              CRE Dashboard
            </h1>
            <p className="text-zinc-500 mt-1">Customer calls and follow-ups</p>
          </div>
          <Button variant="outline" onClick={() => { setLoading(true); fetchData(); }}>
            <RefreshCcw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
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

        {/* Filter */}
        <div className="flex gap-2">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            All
          </Button>
          <Button
            variant={filter === 'pending' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('pending')}
          >
            Pending
          </Button>
          <Button
            variant={filter === 'called' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('called')}
          >
            Called
          </Button>
        </div>

        {/* Customer Cards */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : filteredCustomers.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-64 text-center">
              <Users className="h-12 w-12 text-zinc-300 mb-4" />
              <p className="text-zinc-500">No customers found</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCustomers.map((customer) => (
              <Card key={customer.coupon_id} className={`${customer.call_status === 'PENDING' ? 'border-yellow-200 bg-yellow-50/30' : ''}`}>
                <CardContent className="p-4 space-y-3">
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <Badge className={customer.call_status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}>
                      {customer.call_status}
                    </Badge>
                    <code className="text-xs bg-zinc-100 px-2 py-1 rounded">{customer.coupon_code}</code>
                  </div>

                  {/* Customer Info */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-zinc-400" />
                      <span className="font-medium">{customer.customer_name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Phone className="h-4 w-4 text-zinc-400" />
                      <span className="font-mono">{customer.customer_phone}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Ticket className="h-4 w-4 text-zinc-400" />
                      <span className="text-sm text-zinc-600">{customer.campaign_name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-zinc-400" />
                      <span className="text-sm text-zinc-600">{customer.branch_name}</span>
                    </div>
                  </div>

                  {/* Last Call Info */}
                  {customer.last_call_timestamp && (
                    <div className="text-xs text-zinc-500 border-t pt-2">
                      <p><Clock className="h-3 w-3 inline mr-1" />Last call: {formatDate(customer.last_call_timestamp)}</p>
                      {customer.last_remarks && (
                        <p className="mt-1 italic">"{customer.last_remarks}"</p>
                      )}
                    </div>
                  )}

                  {/* Call Button */}
                  <Button
                    className="w-full bg-green-600 hover:bg-green-700"
                    onClick={() => handleCall(customer)}
                    data-testid={`call-btn-${customer.coupon_id}`}
                  >
                    <Phone className="h-4 w-4 mr-2" />
                    Call Customer
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

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
