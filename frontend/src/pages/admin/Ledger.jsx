import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { 
  IndianRupee, Users, Search, Loader2, RefreshCcw,
  User, Ticket, Receipt, Eye, Phone, MessageSquare,
  Building2, Clock, Image
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

  const formatDate = (date) => {
    return new Date(date).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
            <p className="text-zinc-500 mt-1">Worker ledgers, CRE remarks, branch encashments</p>
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

        {/* Expenses Dialog */}
        <Dialog open={expensesDialogOpen} onOpenChange={setExpensesDialogOpen}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
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
              <div className="space-y-4">
                {expenses.map((expense) => (
                  <Card key={expense.id}>
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <Badge className={
                              expense.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                              expense.status === 'REJECTED' ? 'bg-red-100 text-red-800' :
                              'bg-yellow-100 text-yellow-800'
                            }>
                              {expense.status}
                            </Badge>
                            <span className="font-medium">{expense.type}</span>
                          </div>
                          <p className="text-sm text-zinc-500">{expense.description || 'No description'}</p>
                          <p className="text-xs text-zinc-400">
                            <Clock className="h-3 w-3 inline mr-1" />
                            {formatDate(expense.created_at)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xl font-bold">₹{expense.amount}</p>
                          {expense.bill_photo_url && (
                            <a
                              href={`${API_URL}${expense.bill_photo_url}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-blue-600 flex items-center gap-1 justify-end mt-1"
                            >
                              <Image className="h-3 w-3" />
                              View Bill
                            </a>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
