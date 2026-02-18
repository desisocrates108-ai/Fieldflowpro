import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { 
  Ticket, User, Phone, CheckCircle, XCircle,
  Loader2, RefreshCcw, IndianRupee, Search, AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function BranchDashboard() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [encashDialogOpen, setEncashDialogOpen] = useState(false);
  const [encashCode, setEncashCode] = useState('');
  const [encashing, setEncashing] = useState(false);
  const [encashResult, setEncashResult] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/branch/customers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        setCustomers(await response.json());
      }
    } catch (error) {
      toast.error('Failed to load customers');
    } finally {
      setLoading(false);
    }
  };

  const handleEncash = async () => {
    if (!encashCode.trim()) {
      toast.error('Please enter coupon code');
      return;
    }

    setEncashing(true);
    setEncashResult(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/branch/encash`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ coupon_code: encashCode.trim().toUpperCase() })
      });

      const data = await response.json();

      if (response.ok) {
        setEncashResult({ success: true, data });
        toast.success(`Coupon encashed! ₹${data.campaign_price}`);
        fetchCustomers();
      } else {
        setEncashResult({ success: false, error: data.detail });
        toast.error(data.detail || 'Encashment failed');
      }
    } catch (error) {
      setEncashResult({ success: false, error: 'Failed to encash coupon' });
      toast.error('Failed to encash coupon');
    } finally {
      setEncashing(false);
    }
  };

  const resetEncashDialog = () => {
    setEncashDialogOpen(false);
    setEncashCode('');
    setEncashResult(null);
  };

  const filteredCustomers = customers.filter(c =>
    c.coupon_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.customer_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Stats
  const totalCustomers = customers.length;
  const soldCount = customers.filter(c => c.status === 'SOLD').length;
  const encashedCount = customers.filter(c => c.status === 'ENCASHED').length;

  const formatDate = (date) => {
    return new Date(date).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="branch-dashboard">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              Branch Dashboard
            </h1>
            <p className="text-zinc-500 mt-1">View assigned customers and encash coupons</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => { setLoading(true); fetchCustomers(); }}>
              <RefreshCcw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button 
              className="bg-green-600 hover:bg-green-700"
              onClick={() => setEncashDialogOpen(true)}
              data-testid="encash-btn"
            >
              <IndianRupee className="h-4 w-4 mr-2" />
              Encash Coupon
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Ticket className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Total Assigned</p>
                  <p className="text-2xl font-bold">{totalCustomers}</p>
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
                  <p className="text-sm text-zinc-500">Pending Encash</p>
                  <p className="text-2xl font-bold">{soldCount}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Encashed</p>
                  <p className="text-2xl font-bold">{encashedCount}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input
            placeholder="Search by code or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
            data-testid="search-input"
          />
        </div>

        {/* Customers Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : filteredCustomers.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <Ticket className="h-12 w-12 text-zinc-300 mb-4" />
                <p className="text-zinc-500">No customers assigned to your branch</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Mobile</TableHead>
                    <TableHead>Campaign</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCustomers.map((customer) => (
                    <TableRow key={customer.coupon_id}>
                      <TableCell>
                        <code className="px-2 py-1 bg-zinc-100 rounded text-sm font-mono">
                          {customer.coupon_code}
                        </code>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-zinc-400" />
                          {customer.customer_name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-zinc-600">
                          <Phone className="h-4 w-4" />
                          {customer.mobile_last4}
                        </div>
                      </TableCell>
                      <TableCell className="text-zinc-600">{customer.campaign_name}</TableCell>
                      <TableCell className="text-sm text-zinc-500">
                        {formatDate(customer.sold_at)}
                      </TableCell>
                      <TableCell>
                        <Badge className={
                          customer.status === 'ENCASHED' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }>
                          {customer.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Encash Dialog */}
        <Dialog open={encashDialogOpen} onOpenChange={setEncashDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <IndianRupee className="h-5 w-5 text-green-600" />
                Encash Coupon
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Enter Coupon Code</Label>
                <Input
                  placeholder="e.g., MUM001"
                  value={encashCode}
                  onChange={(e) => setEncashCode(e.target.value.toUpperCase())}
                  className="text-lg font-mono text-center tracking-wider"
                  data-testid="encash-code-input"
                />
              </div>

              {encashResult && (
                <div className={`p-4 rounded-lg ${encashResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  {encashResult.success ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-green-700">
                        <CheckCircle className="h-5 w-5" />
                        <span className="font-medium">Encashment Successful!</span>
                      </div>
                      <div className="text-sm text-green-700">
                        <p>Campaign: {encashResult.data.campaign_name}</p>
                        <p>Customer: {encashResult.data.customer_name}</p>
                        <p className="text-lg font-bold">Amount: ₹{encashResult.data.campaign_price}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-red-700">
                      <XCircle className="h-5 w-5" />
                      <span>{encashResult.error}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={resetEncashDialog}>Close</Button>
              {!encashResult?.success && (
                <Button 
                  onClick={handleEncash} 
                  disabled={encashing}
                  className="bg-green-600 hover:bg-green-700"
                  data-testid="confirm-encash-btn"
                >
                  {encashing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                  Encash
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
