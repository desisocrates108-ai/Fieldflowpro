import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Textarea } from '../../components/ui/textarea';
import { Label } from '../../components/ui/label';
import { 
  IndianRupee, Users, Search, Loader2, RefreshCcw,
  User, Receipt, Eye, MessageSquare,
  Building2, Clock, Image, CheckCircle, XCircle,
  X, ZoomIn
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function AdminLedgerPage() {
  const [ledgers, setLedgers] = useState([]);
  const [creRemarks, setCreRemarks] = useState([]);
  const [encashments, setEncashments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('ledgers');
  const [selectedWorkerExpenses, setSelectedWorkerExpenses] = useState(null);
  const [expensesDialogOpen, setExpensesDialogOpen] = useState(false);
  const [expenses, setExpenses] = useState([]);
  const [expensesLoading, setExpensesLoading] = useState(false);
  
  // Image viewer
  const [imageViewerOpen, setImageViewerOpen] = useState(false);
  const [viewingImageUrl, setViewingImageUrl] = useState('');
  
  // Rejection dialog
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectingExpenseId, setRejectingExpenseId] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [processingAction, setProcessingAction] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      // Fetch ledgers
      const ledgersRes = await fetch(`${API_URL}/api/ledgers/all`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (ledgersRes.ok) {
        setLedgers(await ledgersRes.json());
      }
      
      // Fetch CRE remarks
      const remarksRes = await fetch(`${API_URL}/api/admin/cre-remarks`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (remarksRes.ok) {
        setCreRemarks(await remarksRes.json());
      }
      
      // Fetch encashments
      const encashRes = await fetch(`${API_URL}/api/admin/encashments`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (encashRes.ok) {
        setEncashments(await encashRes.json());
      }
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const viewWorkerExpenses = async (workerId, workerName) => {
    setSelectedWorkerExpenses({ id: workerId, name: workerName });
    setExpensesDialogOpen(true);
    setExpensesLoading(true);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/expenses?worker_id=${workerId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        setExpenses(await response.json());
      }
    } catch (error) {
      toast.error('Failed to load expenses');
    } finally {
      setExpensesLoading(false);
    }
  };

  const handleApproveExpense = async (expenseId) => {
    setProcessingAction(expenseId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/expenses/${expenseId}/approve`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ approved: true })
      });

      if (response.ok) {
        toast.success('Expense approved and added to ledger');
        // Refresh expenses
        if (selectedWorkerExpenses) {
          viewWorkerExpenses(selectedWorkerExpenses.id, selectedWorkerExpenses.name);
        }
        // Refresh ledgers
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to approve expense');
      }
    } catch (error) {
      toast.error('Failed to approve expense');
    } finally {
      setProcessingAction(null);
    }
  };

  const openRejectDialog = (expenseId) => {
    setRejectingExpenseId(expenseId);
    setRejectionReason('');
    setRejectDialogOpen(true);
  };

  const handleRejectExpense = async () => {
    if (!rejectionReason.trim()) {
      toast.error('Please provide a rejection reason');
      return;
    }

    setProcessingAction(rejectingExpenseId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/expenses/${rejectingExpenseId}/approve`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ approved: false, rejection_reason: rejectionReason })
      });

      if (response.ok) {
        toast.success('Expense rejected');
        setRejectDialogOpen(false);
        // Refresh expenses
        if (selectedWorkerExpenses) {
          viewWorkerExpenses(selectedWorkerExpenses.id, selectedWorkerExpenses.name);
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to reject expense');
      }
    } catch (error) {
      toast.error('Failed to reject expense');
    } finally {
      setProcessingAction(null);
    }
  };

  const openImageViewer = (url) => {
    // Handle both relative and absolute URLs
    // Backend stores paths like /uploads/filename.jpg
    // But the ingress routes /api/* to backend, so use /api/uploads/
    let fullUrl = url;
    if (!url.startsWith('http')) {
      // Convert /uploads/xxx to /api/uploads/xxx for proper routing through ingress
      if (url.startsWith('/uploads/')) {
        fullUrl = `${API_URL}/api/uploads/${url.replace('/uploads/', '')}`;
      } else {
        fullUrl = `${API_URL}${url}`;
      }
    }
    setViewingImageUrl(fullUrl);
    setImageViewerOpen(true);
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Approved</Badge>;
      case 'REJECTED':
        return <Badge className="bg-red-100 text-red-800"><XCircle className="h-3 w-3 mr-1" />Rejected</Badge>;
      default:
        return <Badge className="bg-yellow-100 text-yellow-800"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
    }
  };

  const filteredLedgers = ledgers.filter(l =>
    l.worker_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Stats
  const totalRevenue = ledgers.reduce((acc, l) => acc + l.total_revenue, 0);
  const totalPayable = ledgers.reduce((acc, l) => acc + l.net_payable, 0);
  const totalExpenses = ledgers.reduce((acc, l) => acc + l.total_expenses, 0);
  const totalAdvances = ledgers.reduce((acc, l) => acc + l.total_advances, 0);

  return (
    <Layout>
      <div className="space-y-6" data-testid="admin-ledger-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              Ledger & Operations
            </h1>
            <p className="text-zinc-500 mt-1">Worker ledgers, expenses, CRE remarks, branch encashments</p>
          </div>
          <Button variant="outline" onClick={() => { setLoading(true); fetchData(); }}>
            <RefreshCcw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <IndianRupee className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Total Revenue</p>
                  <p className="text-2xl font-bold">₹{totalRevenue.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <IndianRupee className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Total Advances</p>
                  <p className="text-2xl font-bold">₹{totalAdvances.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-red-100 rounded-lg">
                  <Receipt className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Total Expenses</p>
                  <p className="text-2xl font-bold">₹{totalExpenses.toLocaleString()}</p>
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
                  <p className="text-2xl font-bold">₹{totalPayable.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="ledgers">Worker Ledgers</TabsTrigger>
            <TabsTrigger value="remarks">
              CRE Remarks
              {creRemarks.length > 0 && <Badge className="ml-2">{creRemarks.length}</Badge>}
            </TabsTrigger>
            <TabsTrigger value="encashments">
              Encashments
              {encashments.length > 0 && <Badge className="ml-2">{encashments.length}</Badge>}
            </TabsTrigger>
          </TabsList>

          {/* Ledgers Tab */}
          <TabsContent value="ledgers" className="mt-6">
            <div className="relative max-w-md mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
              <Input
                placeholder="Search workers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            <Card>
              <CardContent className="p-0">
                {loading ? (
                  <div className="flex items-center justify-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Worker</TableHead>
                        <TableHead>Sales</TableHead>
                        <TableHead>Revenue</TableHead>
                        <TableHead>Advances</TableHead>
                        <TableHead>Expenses</TableHead>
                        <TableHead>Net Payable</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredLedgers.map((ledger) => (
                        <TableRow key={ledger.worker_id}>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-zinc-100 rounded-full flex items-center justify-center">
                                <User className="h-4 w-4 text-zinc-400" />
                              </div>
                              <span className="font-medium">{ledger.worker_name}</span>
                            </div>
                          </TableCell>
                          <TableCell className="font-medium">{ledger.total_coupons_sold}</TableCell>
                          <TableCell className="text-green-600">₹{ledger.total_revenue.toLocaleString()}</TableCell>
                          <TableCell className="text-blue-600">₹{ledger.total_advances.toLocaleString()}</TableCell>
                          <TableCell className="text-red-600">₹{ledger.total_expenses.toLocaleString()}</TableCell>
                          <TableCell className={`font-bold ${ledger.net_payable > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ₹{ledger.net_payable.toLocaleString()}
                          </TableCell>
                          <TableCell>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => viewWorkerExpenses(ledger.worker_id, ledger.worker_name)}
                              data-testid={`view-expenses-${ledger.worker_id}`}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              Expenses
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* CRE Remarks Tab */}
          <TabsContent value="remarks" className="mt-6">
            <Card>
              <CardContent className="p-0">
                {creRemarks.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <MessageSquare className="h-12 w-12 text-zinc-300 mb-4" />
                    <p className="text-zinc-500">No CRE remarks yet</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>CRE</TableHead>
                        <TableHead>Coupon</TableHead>
                        <TableHead>Customer</TableHead>
                        <TableHead>Phone</TableHead>
                        <TableHead>Call Time</TableHead>
                        <TableHead>Remarks</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {creRemarks.map((remark) => (
                        <TableRow key={remark.id}>
                          <TableCell className="font-medium">{remark.cre_name}</TableCell>
                          <TableCell>
                            <code className="px-2 py-1 bg-zinc-100 rounded text-sm">
                              {remark.coupon_code}
                            </code>
                          </TableCell>
                          <TableCell>{remark.customer_name}</TableCell>
                          <TableCell className="font-mono text-sm">{remark.customer_phone}</TableCell>
                          <TableCell className="text-sm text-zinc-500">
                            {formatDate(remark.call_timestamp)}
                          </TableCell>
                          <TableCell className="max-w-xs">
                            <p className="truncate text-sm italic">"{remark.remarks}"</p>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Encashments Tab */}
          <TabsContent value="encashments" className="mt-6">
            <Card>
              <CardContent className="p-0">
                {encashments.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <Building2 className="h-12 w-12 text-zinc-300 mb-4" />
                    <p className="text-zinc-500">No encashments yet</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Coupon</TableHead>
                        <TableHead>Campaign</TableHead>
                        <TableHead>Customer</TableHead>
                        <TableHead>Branch</TableHead>
                        <TableHead>Encashed By</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>Time</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {encashments.map((enc) => (
                        <TableRow key={enc.id}>
                          <TableCell>
                            <code className="px-2 py-1 bg-green-100 rounded text-sm text-green-800">
                              {enc.coupon_code}
                            </code>
                          </TableCell>
                          <TableCell>{enc.campaign_name}</TableCell>
                          <TableCell>{enc.customer_name}</TableCell>
                          <TableCell className="font-medium">{enc.branch_name}</TableCell>
                          <TableCell>{enc.encashed_by_name}</TableCell>
                          <TableCell className="font-bold text-green-600">
                            ₹{enc.campaign_price}
                          </TableCell>
                          <TableCell className="text-sm text-zinc-500">
                            {formatDate(enc.encashed_at)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Expenses Dialog with Approval System */}
        <Dialog open={expensesDialogOpen} onOpenChange={setExpensesDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-['Barlow_Condensed'] text-2xl">
                Expenses - {selectedWorkerExpenses?.name}
              </DialogTitle>
            </DialogHeader>
            {expensesLoading ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : expenses.length === 0 ? (
              <div className="text-center py-8">
                <Receipt className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
                <p className="text-zinc-500">No expenses found</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Bill</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {expenses.map((expense) => (
                    <TableRow key={expense.id}>
                      <TableCell className="font-medium">{expense.type}</TableCell>
                      <TableCell className="font-bold">₹{expense.amount}</TableCell>
                      <TableCell className="max-w-xs">
                        <p className="truncate text-sm">{expense.description || '-'}</p>
                      </TableCell>
                      <TableCell>{getStatusBadge(expense.status)}</TableCell>
                      <TableCell>
                        {expense.bill_photo_url ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openImageViewer(expense.bill_photo_url)}
                            data-testid={`view-bill-${expense.id}`}
                          >
                            <ZoomIn className="h-4 w-4 mr-1" />
                            View
                          </Button>
                        ) : (
                          <span className="text-zinc-400 text-sm">No bill</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-zinc-500">
                        {formatDate(expense.created_at)}
                      </TableCell>
                      <TableCell>
                        {expense.status === 'PENDING' ? (
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              className="bg-green-600 hover:bg-green-700 h-8 px-2"
                              onClick={() => handleApproveExpense(expense.id)}
                              disabled={processingAction === expense.id}
                              data-testid={`approve-expense-${expense.id}`}
                            >
                              {processingAction === expense.id ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <CheckCircle className="h-3 w-3" />
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-8 px-2 text-red-600 border-red-300 hover:bg-red-50"
                              onClick={() => openRejectDialog(expense.id)}
                              disabled={processingAction === expense.id}
                              data-testid={`reject-expense-${expense.id}`}
                            >
                              <XCircle className="h-3 w-3" />
                            </Button>
                          </div>
                        ) : expense.status === 'REJECTED' && expense.rejection_reason ? (
                          <span className="text-xs text-red-600 italic">
                            Reason: {expense.rejection_reason}
                          </span>
                        ) : (
                          <span className="text-xs text-zinc-400">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </DialogContent>
        </Dialog>

        {/* Reject Expense Dialog */}
        <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Reject Expense</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Rejection Reason (Required)</Label>
                <Textarea
                  placeholder="Enter reason for rejection..."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  rows={3}
                  data-testid="rejection-reason-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setRejectDialogOpen(false)}>Cancel</Button>
              <Button 
                variant="destructive" 
                onClick={handleRejectExpense}
                disabled={processingAction || !rejectionReason.trim()}
                data-testid="confirm-reject-btn"
              >
                {processingAction ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Reject Expense
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Image Viewer Modal */}
        <Dialog open={imageViewerOpen} onOpenChange={setImageViewerOpen}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle className="flex items-center justify-between">
                Bill Photo
                <Button variant="ghost" size="sm" onClick={() => setImageViewerOpen(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </DialogTitle>
            </DialogHeader>
            <div className="flex items-center justify-center p-4 bg-zinc-100 rounded-lg min-h-[400px]">
              {viewingImageUrl ? (
                <img 
                  src={viewingImageUrl} 
                  alt="Bill" 
                  className="max-w-full max-h-[60vh] object-contain rounded"
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect fill="%23f5f5f5" width="200" height="200"/><text fill="%23999" font-size="14" x="50%" y="50%" text-anchor="middle">Image not found</text></svg>';
                  }}
                />
              ) : (
                <div className="text-zinc-500">Loading image...</div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
