import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import Layout from '../../components/Layout';
import { couponAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import ForceDeleteModal from '../../components/ForceDeleteModal';
import { 
  Loader2, Search, Ticket, Phone, User, 
  CheckCircle, XCircle, Eye, MapPin, Clock,
  Camera, AlertCircle, RefreshCcw, Trash2
} from 'lucide-react';
import { formatDateTime, getStatusColor } from '../../lib/utils';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function CouponsPage() {
  const { user } = useAuth();
  const [coupons, setCoupons] = useState([]);
  const [pendingCoupons, setPendingCoupons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedCoupon, setSelectedCoupon] = useState(null);
  const [verifyDialogOpen, setVerifyDialogOpen] = useState(false);
  const [verificationNotes, setVerificationNotes] = useState('');
  const [correctedName, setCorrectedName] = useState('');
  const [correctedMobile, setCorrectedMobile] = useState('');
  const [processing, setProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('pending');
  
  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [couponToDelete, setCouponToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const isCRE = user?.role === 'cre' || user?.role === 'admin';

  const fetchCoupons = async () => {
    try {
      const [allRes, pendingRes] = await Promise.all([
        couponAPI.getAll(statusFilter === 'all' ? null : statusFilter),
        isCRE ? couponAPI.getAll(null, true) : Promise.resolve({ data: [] })
      ]);
      setCoupons(allRes.data);
      setPendingCoupons(pendingRes.data || []);
    } catch (error) {
      console.error('Failed to fetch coupons:', error);
      toast.error('Failed to load coupons');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCoupons();
  }, [statusFilter]);

  const handleVerify = async (verified) => {
    if (!selectedCoupon) return;
    
    setProcessing(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${BACKEND_URL}/api/coupons/${selectedCoupon.id}/verify`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          verified,
          notes: verificationNotes,
          corrected_name: correctedName || null,
          corrected_mobile: correctedMobile || null
        })
      });

      if (!response.ok) {
        throw new Error('Verification failed');
      }

      toast.success(verified ? 'Coupon verified successfully!' : 'Coupon cancelled');
      setVerifyDialogOpen(false);
      setSelectedCoupon(null);
      setVerificationNotes('');
      setCorrectedName('');
      setCorrectedMobile('');
      fetchCoupons();
    } catch (error) {
      toast.error('Failed to verify coupon');
    } finally {
      setProcessing(false);
    }
  };

  const openVerifyDialog = (coupon) => {
    setSelectedCoupon(coupon);
    setCorrectedName(coupon.customer_name);
    setCorrectedMobile(coupon.customer_phone);
    setVerifyDialogOpen(true);
  };

  const handleDeleteCoupon = async (coupon) => {
    // Only allow deletion of AVAILABLE or PENDING coupons
    const allowedStatuses = ['AVAILABLE', 'PENDING'];
    if (!allowedStatuses.includes(coupon.status)) {
      toast.error(`Coupon is ${coupon.status}. Only AVAILABLE/PENDING coupons can be deleted.`);
      return;
    }
    
    if (!window.confirm(
      `⚠️ DELETE COUPON\n\n` +
      `Code: ${coupon.code || coupon.coupon_code}\n\n` +
      `This will permanently delete this coupon. Continue?`
    )) {
      return;
    }
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${BACKEND_URL}/api/campaigns/coupons/${coupon.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(data.message || 'Coupon deleted');
        fetchCoupons();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete coupon');
      }
    } catch (error) {
      toast.error('Failed to delete coupon');
    }
  };

  const filteredCoupons = coupons.filter(coupon => 
    coupon.code?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    coupon.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (coupon.customer_phone || coupon.mobile_last4 || '').includes(searchQuery)
  );

  return (
    <Layout>
      <div className="space-y-6" data-testid="coupons-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              Coupons
            </h1>
            <p className="text-zinc-500 mt-1">
              {isCRE ? 'View and verify coupons' : 'View and manage all issued coupons'}
            </p>
          </div>
          <Button variant="outline" onClick={() => { setLoading(true); fetchCoupons(); }}>
            <RefreshCcw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* CRE Tabs View */}
        {isCRE ? (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="pending" className="relative">
                Pending Verification
                {pendingCoupons.length > 0 && (
                  <Badge className="ml-2 bg-red-500 text-white">{pendingCoupons.length}</Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="all">All Coupons</TabsTrigger>
            </TabsList>

            {/* Pending Coupons Tab */}
            <TabsContent value="pending" className="mt-6">
              {loading ? (
                <Card>
                  <CardContent className="flex items-center justify-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                  </CardContent>
                </Card>
              ) : pendingCoupons.length === 0 ? (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center h-64 text-center">
                    <CheckCircle className="h-12 w-12 text-green-300 mb-4" />
                    <p className="text-zinc-500">No pending coupons</p>
                    <p className="text-sm text-zinc-400">All coupons have been verified</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {pendingCoupons.map((coupon) => (
                    <Card key={coupon.id} className="border-yellow-200 bg-yellow-50/50" data-testid={`pending-coupon-${coupon.id}`}>
                      <CardContent className="p-6">
                        <div className="flex flex-col md:flex-row gap-6">
                          {/* Photo Preview */}
                          {coupon.photo_url && (
                            <div className="w-full md:w-48 h-36 bg-zinc-100 rounded-lg overflow-hidden flex-shrink-0">
                              <img 
                                src={`${BACKEND_URL}${coupon.photo_url}`} 
                                alt="Coupon photo"
                                className="w-full h-full object-cover"
                              />
                            </div>
                          )}
                          
                          {/* Coupon Details */}
                          <div className="flex-1 space-y-3">
                            <div className="flex items-center justify-between">
                              <code className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded font-mono text-lg">
                                {coupon.code}
                              </code>
                              <Badge className={getStatusColor(coupon.status)}>
                                {coupon.status}
                              </Badge>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="flex items-center gap-2">
                                <User className="h-4 w-4 text-zinc-400" />
                                <span className="font-medium">{coupon.customer_name}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Phone className="h-4 w-4 text-zinc-400" />
                                <span>{coupon.customer_phone}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4 text-zinc-400" />
                                <span className="text-sm text-zinc-600">{formatDateTime(coupon.issued_at)}</span>
                              </div>
                              {coupon.latitude && coupon.longitude && (
                                <div className="flex items-center gap-2">
                                  <MapPin className="h-4 w-4 text-zinc-400" />
                                  <span className="text-sm text-zinc-600">
                                    {coupon.latitude.toFixed(4)}, {coupon.longitude.toFixed(4)}
                                  </span>
                                </div>
                              )}
                            </div>
                            
                            {/* OCR Confidence */}
                            {coupon.ocr_confidence !== undefined && (
                              <div className="flex items-center gap-2">
                                <Camera className="h-4 w-4 text-zinc-400" />
                                <span className="text-sm">
                                  OCR Confidence: 
                                  <span className={`ml-1 font-medium ${
                                    coupon.ocr_confidence >= 0.8 ? 'text-green-600' : 
                                    coupon.ocr_confidence >= 0.6 ? 'text-yellow-600' : 'text-red-600'
                                  }`}>
                                    {(coupon.ocr_confidence * 100).toFixed(0)}%
                                  </span>
                                </span>
                                {coupon.ocr_confidence < 0.7 && (
                                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                                )}
                              </div>
                            )}
                          </div>
                          
                          {/* Action Buttons */}
                          <div className="flex flex-col gap-2 md:w-40">
                            <Button 
                              onClick={() => openVerifyDialog(coupon)}
                              className="bg-green-600 hover:bg-green-700"
                              data-testid={`verify-btn-${coupon.id}`}
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              Review
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* All Coupons Tab */}
            <TabsContent value="all" className="mt-6">
              {renderAllCouponsView()}
            </TabsContent>
          </Tabs>
        ) : (
          renderAllCouponsView()
        )}

        {/* Verify Dialog */}
        <Dialog open={verifyDialogOpen} onOpenChange={setVerifyDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="font-['Barlow_Condensed'] text-2xl">
                Verify Coupon - {selectedCoupon?.code}
              </DialogTitle>
            </DialogHeader>
            
            {selectedCoupon && (
              <div className="space-y-6">
                {/* Photo */}
                {selectedCoupon.photo_url && (
                  <div className="w-full h-64 bg-zinc-100 rounded-lg overflow-hidden">
                    <img 
                      src={`${BACKEND_URL}${selectedCoupon.photo_url}`} 
                      alt="Coupon photo"
                      className="w-full h-full object-contain"
                    />
                  </div>
                )}
                
                {/* Editable Fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Customer Name</label>
                    <Input
                      value={correctedName}
                      onChange={(e) => setCorrectedName(e.target.value)}
                      placeholder="Enter customer name"
                      data-testid="verify-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Mobile Number</label>
                    <Input
                      value={correctedMobile}
                      onChange={(e) => setCorrectedMobile(e.target.value)}
                      placeholder="Enter mobile number"
                      data-testid="verify-mobile-input"
                    />
                  </div>
                </div>
                
                {/* Location Info */}
                {selectedCoupon.latitude && selectedCoupon.longitude && (
                  <div className="p-3 bg-zinc-50 rounded-lg">
                    <div className="flex items-center gap-2 text-sm">
                      <MapPin className="h-4 w-4 text-zinc-400" />
                      <span>Location: {selectedCoupon.latitude.toFixed(6)}, {selectedCoupon.longitude.toFixed(6)}</span>
                    </div>
                  </div>
                )}
                
                {/* Notes */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Verification Notes (Optional)</label>
                  <Textarea
                    value={verificationNotes}
                    onChange={(e) => setVerificationNotes(e.target.value)}
                    placeholder="Add any notes about this verification..."
                    rows={3}
                    data-testid="verify-notes-input"
                  />
                </div>
              </div>
            )}
            
            <DialogFooter className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setVerifyDialogOpen(false)}
                disabled={processing}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => handleVerify(false)}
                disabled={processing}
                data-testid="reject-coupon-btn"
              >
                {processing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <XCircle className="h-4 w-4 mr-2" />}
                Reject
              </Button>
              <Button
                className="bg-green-600 hover:bg-green-700"
                onClick={() => handleVerify(true)}
                disabled={processing}
                data-testid="approve-coupon-btn"
              >
                {processing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                Approve & Activate
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );

  function renderAllCouponsView() {
    return (
      <>
        {/* Filters */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <Input
              placeholder="Search by code, name, or phone..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
              data-testid="search-coupons-input"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40" data-testid="status-filter-select">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="PENDING">Pending</SelectItem>
              <SelectItem value="ACTIVE">Active</SelectItem>
              <SelectItem value="VERIFIED">Verified</SelectItem>
              <SelectItem value="REDEEMED">Redeemed</SelectItem>
              <SelectItem value="UTILIZED">Utilized</SelectItem>
              <SelectItem value="EXPIRED">Expired</SelectItem>
              <SelectItem value="CANCELLED">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Coupons Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : filteredCoupons.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <Ticket className="h-12 w-12 text-zinc-300 mb-4" />
                <p className="text-zinc-500">No coupons found</p>
                <p className="text-sm text-zinc-400">Coupons will appear here once issued</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Issued At</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCoupons.map((coupon) => (
                    <TableRow key={coupon.id} className="table-row-hover">
                      <TableCell>
                        <code className="px-2 py-1 bg-zinc-100 rounded text-sm font-mono">
                          {coupon.code}
                        </code>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-zinc-400" />
                          {coupon.customer_name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-zinc-600">
                          <Phone className="h-4 w-4" />
                          {coupon.customer_phone || coupon.mobile_last4 || '-'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(coupon.status)}>
                          {coupon.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-zinc-600">
                        {formatDateTime(coupon.issued_at)}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          {coupon.status === 'PENDING' && isCRE && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openVerifyDialog(coupon)}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              Review
                            </Button>
                          )}
                          {user?.role === 'admin' && (
                            <Button
                              size="sm"
                              variant="outline"
                              className={['AVAILABLE', 'PENDING'].includes(coupon.status)
                                ? "text-red-600 hover:bg-red-50" 
                                : "text-zinc-400 cursor-not-allowed"
                              }
                              onClick={() => handleDeleteCoupon(coupon)}
                              disabled={!['AVAILABLE', 'PENDING'].includes(coupon.status)}
                              title={['AVAILABLE', 'PENDING'].includes(coupon.status)
                                ? "Delete coupon" 
                                : `Cannot delete ${coupon.status} coupon`
                              }
                              data-testid={`delete-coupon-${coupon.id}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </>
    );
  }
}
