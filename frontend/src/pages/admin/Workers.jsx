import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { 
  Plus, Users, Search, MoreVertical, Trash2, 
  Ban, CheckCircle, Key, IndianRupee, Loader2,
  RefreshCcw, User, Mail, Phone, MapPin
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function WorkersPage() {
  const [workers, setWorkers] = useState([]);
  const [ledgers, setLedgers] = useState({});
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [advanceDialogOpen, setAdvanceDialogOpen] = useState(false);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [selectedWorker, setSelectedWorker] = useState(null);
  
  // Form states
  const [creating, setCreating] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [newWorker, setNewWorker] = useState({
    email: '', password: '', name: '', phone: '', area_id: ''
  });
  const [advanceAmount, setAdvanceAmount] = useState('');
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      // Fetch workers
      const workersRes = await fetch(`${API_URL}/api/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (workersRes.ok) {
        const data = await workersRes.json();
        setWorkers(data.filter(u => u.role === 'worker'));
      }
      
      // Fetch areas
      const areasRes = await fetch(`${API_URL}/api/areas`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (areasRes.ok) {
        const data = await areasRes.json();
        setAreas(data);
      }
      
      // Fetch all ledgers
      const ledgersRes = await fetch(`${API_URL}/api/ledgers/all`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (ledgersRes.ok) {
        const data = await ledgersRes.json();
        const ledgerMap = {};
        data.forEach(l => { ledgerMap[l.worker_id] = l; });
        setLedgers(ledgerMap);
      }
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorker = async () => {
    if (!newWorker.email || !newWorker.password || !newWorker.name) {
      toast.error('Please fill all required fields');
      return;
    }

    setCreating(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/admin/workers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newWorker)
      });

      if (response.ok) {
        toast.success('Worker created successfully');
        setCreateDialogOpen(false);
        setNewWorker({ email: '', password: '', name: '', phone: '', area_id: '' });
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create worker');
      }
    } catch (error) {
      toast.error('Failed to create worker');
    } finally {
      setCreating(false);
    }
  };

  const toggleWorkerStatus = async (worker) => {
    setProcessing(true);
    try {
      const token = localStorage.getItem('access_token');
      const endpoint = worker.is_active ? 'disable' : 'enable';
      const response = await fetch(`${API_URL}/api/admin/workers/${worker.id}/${endpoint}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success(`Worker ${worker.is_active ? 'disabled' : 'enabled'}`);
        fetchData();
      }
    } catch (error) {
      toast.error('Failed to update worker');
    } finally {
      setProcessing(false);
    }
  };

  const handleAddAdvance = async () => {
    if (!advanceAmount || parseFloat(advanceAmount) <= 0) {
      toast.error('Please enter valid amount');
      return;
    }

    setProcessing(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/workers/${selectedWorker.id}/advance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          amount: parseFloat(advanceAmount),
          description: 'Advance payment'
        })
      });

      if (response.ok) {
        toast.success(`₹${advanceAmount} advance added`);
        setAdvanceDialogOpen(false);
        setAdvanceAmount('');
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to add advance');
      }
    } catch (error) {
      toast.error('Failed to add advance');
    } finally {
      setProcessing(false);
    }
  };

  const handleResetPassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setProcessing(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/admin/workers/${selectedWorker.id}/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ new_password: newPassword })
      });

      if (response.ok) {
        toast.success('Password reset successfully');
        setPasswordDialogOpen(false);
        setNewPassword('');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to reset password');
      }
    } catch (error) {
      toast.error('Failed to reset password');
    } finally {
      setProcessing(false);
    }
  };

  const handleDeleteWorker = async (worker) => {
    if (!confirm(`Are you sure you want to delete ${worker.name}?`)) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/admin/workers/${worker.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Worker deleted');
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete worker');
      }
    } catch (error) {
      toast.error('Failed to delete worker');
    }
  };

  const filteredWorkers = workers.filter(w =>
    w.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    w.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Stats
  const activeWorkers = workers.filter(w => w.is_active).length;
  const totalNetPayable = Object.values(ledgers).reduce((acc, l) => acc + (l.net_payable || 0), 0);

  return (
    <Layout>
      <div className="space-y-6" data-testid="workers-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              Worker Management
            </h1>
            <p className="text-zinc-500 mt-1">Create, manage, and control worker accounts</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => { setLoading(true); fetchData(); }}>
              <RefreshCcw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700" data-testid="create-worker-btn">
                  <Plus className="h-4 w-4 mr-2" />
                  Create Worker
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="font-['Barlow_Condensed'] text-2xl">Create New Worker</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Full Name *</Label>
                    <Input
                      placeholder="John Doe"
                      value={newWorker.name}
                      onChange={(e) => setNewWorker({ ...newWorker, name: e.target.value })}
                      data-testid="worker-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Email *</Label>
                    <Input
                      type="email"
                      placeholder="john@company.com"
                      value={newWorker.email}
                      onChange={(e) => setNewWorker({ ...newWorker, email: e.target.value })}
                      data-testid="worker-email-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Password *</Label>
                    <Input
                      type="password"
                      placeholder="Min 6 characters"
                      value={newWorker.password}
                      onChange={(e) => setNewWorker({ ...newWorker, password: e.target.value })}
                      data-testid="worker-password-input"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Phone</Label>
                      <Input
                        placeholder="9876543210"
                        value={newWorker.phone}
                        onChange={(e) => setNewWorker({ ...newWorker, phone: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Area</Label>
                      <Select
                        value={newWorker.area_id}
                        onValueChange={(v) => setNewWorker({ ...newWorker, area_id: v })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select area" />
                        </SelectTrigger>
                        <SelectContent>
                          {areas.map((area) => (
                            <SelectItem key={area.id} value={area.id}>
                              {area.name}, {area.city}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
                  <Button onClick={handleCreateWorker} disabled={creating} data-testid="confirm-create-worker-btn">
                    {creating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
                    Create Worker
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Users className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Total Workers</p>
                  <p className="text-2xl font-bold">{workers.length}</p>
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
                  <p className="text-sm text-zinc-500">Active</p>
                  <p className="text-2xl font-bold">{activeWorkers}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-100 rounded-lg">
                  <Ban className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Disabled</p>
                  <p className="text-2xl font-bold">{workers.length - activeWorkers}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <IndianRupee className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Net Payable</p>
                  <p className="text-2xl font-bold">₹{totalNetPayable.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input
            placeholder="Search workers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
            data-testid="search-workers-input"
          />
        </div>

        {/* Workers Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : filteredWorkers.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <Users className="h-12 w-12 text-zinc-300 mb-4" />
                <p className="text-zinc-500">No workers found</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Worker</TableHead>
                    <TableHead>Contact</TableHead>
                    <TableHead>Sales</TableHead>
                    <TableHead>Revenue</TableHead>
                    <TableHead>Net Payable</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredWorkers.map((worker) => {
                    const ledger = ledgers[worker.id] || {};
                    return (
                      <TableRow key={worker.id} className="table-row-hover">
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-zinc-100 rounded-full flex items-center justify-center">
                              <User className="h-5 w-5 text-zinc-400" />
                            </div>
                            <div>
                              <p className="font-medium">{worker.name}</p>
                              <p className="text-xs text-zinc-500">{worker.email}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-zinc-600">
                          {worker.phone || '-'}
                        </TableCell>
                        <TableCell className="font-medium">
                          {ledger.total_coupons_sold || 0}
                        </TableCell>
                        <TableCell>
                          ₹{(ledger.total_revenue || 0).toLocaleString()}
                        </TableCell>
                        <TableCell className={ledger.net_payable > 0 ? 'text-green-600 font-medium' : ''}>
                          ₹{(ledger.net_payable || 0).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Badge className={worker.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                            {worker.is_active ? 'Active' : 'Disabled'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedWorker(worker);
                                setAdvanceDialogOpen(true);
                              }}
                              title="Add Advance"
                            >
                              <IndianRupee className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedWorker(worker);
                                setPasswordDialogOpen(true);
                              }}
                              title="Reset Password"
                            >
                              <Key className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => toggleWorkerStatus(worker)}
                              disabled={processing}
                              title={worker.is_active ? 'Disable' : 'Enable'}
                            >
                              {worker.is_active ? <Ban className="h-4 w-4" /> : <CheckCircle className="h-4 w-4" />}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-red-600 hover:bg-red-50"
                              onClick={() => handleDeleteWorker(worker)}
                              title="Delete"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Add Advance Dialog */}
        <Dialog open={advanceDialogOpen} onOpenChange={setAdvanceDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Advance - {selectedWorker?.name}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Advance Amount (₹)</Label>
                <Input
                  type="number"
                  placeholder="Enter amount"
                  value={advanceAmount}
                  onChange={(e) => setAdvanceAmount(e.target.value)}
                  data-testid="advance-amount-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setAdvanceDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleAddAdvance} disabled={processing} data-testid="confirm-advance-btn">
                {processing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Add Advance
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Reset Password Dialog */}
        <Dialog open={passwordDialogOpen} onOpenChange={setPasswordDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Reset Password - {selectedWorker?.name}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>New Password</Label>
                <Input
                  type="password"
                  placeholder="Min 6 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  data-testid="new-password-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setPasswordDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleResetPassword} disabled={processing} data-testid="confirm-password-btn">
                {processing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Reset Password
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
