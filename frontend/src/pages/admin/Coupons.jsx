import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import ForceDeleteModal from '../../components/ForceDeleteModal';
import { 
  Loader2, Search, Ticket, Download, Eye, RefreshCcw, Trash2, Image, X
} from 'lucide-react';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const statusColors = {
  AVAILABLE: 'bg-green-100 text-green-700',
  SOLD: 'bg-blue-100 text-blue-700',
  REDEEMED: 'bg-purple-100 text-purple-700',
  ENCASHED: 'bg-amber-100 text-amber-700',
  CANCELLED: 'bg-red-100 text-red-700',
  UTILIZED: 'bg-gray-100 text-gray-700',
  PENDING: 'bg-yellow-100 text-yellow-700',
  ACTIVE: 'bg-cyan-100 text-cyan-700',
  VERIFIED: 'bg-teal-100 text-teal-700',
  EXPIRED: 'bg-orange-100 text-orange-700',
};

export default function CouponsPage() {
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [totals, setTotals] = useState({ total_campaign: 0, total_legacy: 0 });
  
  // Photo preview
  const [photoPreviewOpen, setPhotoPreviewOpen] = useState(false);
  const [previewPhotoUrl, setPreviewPhotoUrl] = useState('');
  
  // Delete
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [couponToDelete, setCouponToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchCoupons = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams();
      if (statusFilter !== 'all') params.append('status', statusFilter);
      if (sourceFilter !== 'all') params.append('source', sourceFilter);
      if (searchQuery.trim()) params.append('search', searchQuery.trim());
      
      const response = await fetch(
        `${BACKEND_URL}/api/admin/coupons?${params.toString()}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      if (response.ok) {
        const data = await response.json();
        setCoupons(data.coupons || []);
        setTotals({ total_campaign: data.total_campaign, total_legacy: data.total_legacy });
      } else {
        toast.error('Failed to load coupons');
      }
    } catch (error) {
      toast.error('Failed to load coupons');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, sourceFilter, searchQuery]);

  useEffect(() => {
    const debounce = setTimeout(() => fetchCoupons(), 300);
    return () => clearTimeout(debounce);
  }, [fetchCoupons]);

  const handleDeleteCoupon = async () => {
    if (!couponToDelete) return;
    setDeleting(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${BACKEND_URL}/api/admin/coupons/${couponToDelete.id}?force=true`,
        { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (response.ok) {
        const data = await response.json();
        toast.success(data.message || 'Coupon deleted');
        setCoupons(prev => prev.filter(c => c.id !== couponToDelete.id));
        setDeleteModalOpen(false);
        setCouponToDelete(null);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete');
      }
    } catch {
      toast.error('Failed to delete coupon');
    } finally {
      setDeleting(false);
    }
  };

  const handleExportExcel = () => {
    const soldCoupons = coupons.filter(c => c.customer_name);
    if (soldCoupons.length === 0) {
      toast.error('No data to export');
      return;
    }
    
    const exportData = soldCoupons.map(c => ({
      'Customer Name': c.customer_name || '',
      'Customer Mobile': c.customer_phone || '',
      'Coupon Code': c.code || '',
      'Campaign Name': c.campaign_name || '',
      'Worker Name': c.worker_name || '',
      'Branch Name': c.branch_name || '',
      'Sold Date & Time': c.sold_at ? new Date(c.sold_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : '',
      'Status': c.status || '',
      'Source': c.source === 'campaign' ? 'Campaign' : 'Legacy',
    }));
    
    const ws = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Coupons');
    XLSX.writeFile(wb, `FieldFlow_Coupons_${new Date().toISOString().slice(0,10)}.xlsx`);
    toast.success(`Exported ${exportData.length} records`);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('en-IN', { 
      timeZone: 'Asia/Kolkata',
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const openPhoto = (url) => {
    if (!url) return;
    const fullUrl = url.startsWith('http') ? url : `${BACKEND_URL}${url}`;
    setPreviewPhotoUrl(fullUrl);
    setPhotoPreviewOpen(true);
  };

  if (loading && coupons.length === 0) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-4" data-testid="admin-coupons-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 flex items-center gap-2">
              <Ticket className="h-6 w-6" style={{ color: '#ED1C24' }} />
              All Coupons
            </h1>
            <p className="text-sm text-zinc-500 mt-1">
              Campaign: {totals.total_campaign.toLocaleString()} | Legacy: {totals.total_legacy.toLocaleString()}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={fetchCoupons} data-testid="refresh-coupons-btn">
              <RefreshCcw className="h-4 w-4 mr-1" /> Refresh
            </Button>
            <Button 
              size="sm" 
              className="bg-green-600 hover:bg-green-700 text-white"
              onClick={handleExportExcel}
              data-testid="export-excel-btn"
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
                  placeholder="Search customer name, mobile, coupon code..."
                  className="pl-10"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  data-testid="search-coupons-input"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40" data-testid="status-filter">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="AVAILABLE">Available</SelectItem>
                  <SelectItem value="SOLD">Sold</SelectItem>
                  <SelectItem value="REDEEMED">Redeemed</SelectItem>
                  <SelectItem value="ENCASHED">Encashed</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                  <SelectItem value="UTILIZED">Utilized</SelectItem>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="VERIFIED">Verified</SelectItem>
                </SelectContent>
              </Select>
              <Select value={sourceFilter} onValueChange={setSourceFilter}>
                <SelectTrigger className="w-44" data-testid="source-filter">
                  <SelectValue placeholder="Source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sources</SelectItem>
                  <SelectItem value="campaign">Campaign Coupons</SelectItem>
                  <SelectItem value="legacy">Legacy Coupons</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Results count */}
        <p className="text-sm text-zinc-500">Showing {coupons.length} coupons</p>

        {/* Table */}
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-zinc-50">
                    <TableHead className="w-36">Customer</TableHead>
                    <TableHead className="w-28">Mobile</TableHead>
                    <TableHead className="w-32">Coupon Code</TableHead>
                    <TableHead className="w-32">Campaign</TableHead>
                    <TableHead className="w-24">Worker</TableHead>
                    <TableHead className="w-24">Branch</TableHead>
                    <TableHead className="w-36">Sold/Issued</TableHead>
                    <TableHead className="w-16">Photo</TableHead>
                    <TableHead className="w-24">Status</TableHead>
                    <TableHead className="w-20 text-center">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {coupons.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={10} className="text-center py-12 text-zinc-400">
                        No coupons found
                      </TableCell>
                    </TableRow>
                  ) : (
                    coupons.map((coupon) => (
                      <TableRow key={coupon.id} className="hover:bg-zinc-50">
                        <TableCell className="font-medium text-sm" data-testid={`coupon-customer-${coupon.id}`}>
                          {coupon.customer_name || <span className="text-zinc-300">-</span>}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {coupon.customer_phone || <span className="text-zinc-300">-</span>}
                        </TableCell>
                        <TableCell>
                          <code className="px-1.5 py-0.5 bg-zinc-100 rounded text-xs font-mono">
                            {coupon.code}
                          </code>
                        </TableCell>
                        <TableCell className="text-sm truncate max-w-[120px]" title={coupon.campaign_name}>
                          {coupon.campaign_name || '-'}
                        </TableCell>
                        <TableCell className="text-sm truncate max-w-[100px]">{coupon.worker_name || '-'}</TableCell>
                        <TableCell className="text-sm truncate max-w-[100px]">{coupon.branch_name || '-'}</TableCell>
                        <TableCell className="text-xs text-zinc-500">{formatDate(coupon.sold_at)}</TableCell>
                        <TableCell>
                          {coupon.photo_url ? (
                            <button
                              onClick={() => openPhoto(coupon.photo_url)}
                              className="w-8 h-8 rounded border overflow-hidden hover:ring-2 hover:ring-blue-400 transition-all"
                              title="View photo"
                              data-testid={`view-photo-${coupon.id}`}
                            >
                              <img 
                                src={coupon.photo_url.startsWith('http') ? coupon.photo_url : `${BACKEND_URL}${coupon.photo_url}`}
                                alt="Coupon" 
                                className="w-full h-full object-cover"
                                onError={(e) => { e.target.style.display = 'none'; }}
                              />
                            </button>
                          ) : (
                            <span className="text-zinc-300 text-xs">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge className={`text-[10px] ${statusColors[coupon.status] || 'bg-zinc-100 text-zinc-600'}`}>
                            {coupon.status}
                          </Badge>
                          {coupon.source === 'legacy' && (
                            <Badge className="text-[10px] bg-zinc-200 text-zinc-500 ml-1">Legacy</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-1">
                            {coupon.photo_url && (
                              <Button
                                size="sm" variant="ghost"
                                className="h-7 w-7 p-0 text-zinc-400 hover:text-blue-600"
                                onClick={() => openPhoto(coupon.photo_url)}
                              >
                                <Eye className="h-3.5 w-3.5" />
                              </Button>
                            )}
                            <Button
                              size="sm" variant="ghost"
                              className="h-7 w-7 p-0 text-zinc-400 hover:text-red-600 hover:bg-red-50"
                              onClick={() => { setCouponToDelete(coupon); setDeleteModalOpen(true); }}
                              data-testid={`delete-coupon-${coupon.id}`}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Photo Preview Modal */}
      <Dialog open={photoPreviewOpen} onOpenChange={setPhotoPreviewOpen}>
        <DialogContent className="max-w-2xl p-2">
          <DialogHeader className="p-2">
            <DialogTitle className="flex items-center gap-2 text-sm">
              <Image className="h-4 w-4" /> Coupon Photo
            </DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center bg-zinc-100 rounded-lg overflow-hidden min-h-[300px]">
            {previewPhotoUrl && (
              <img 
                src={previewPhotoUrl} 
                alt="Coupon Preview" 
                className="max-w-full max-h-[70vh] object-contain"
              />
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-red-700 flex items-center gap-2">
              <Trash2 className="h-5 w-5" /> Delete Coupon?
            </DialogTitle>
          </DialogHeader>
          {couponToDelete && (
            <div className="space-y-3">
              <div className="bg-zinc-50 rounded-lg p-3 text-sm space-y-1">
                <p><span className="font-medium">Code:</span> <code>{couponToDelete.code}</code></p>
                <p><span className="font-medium">Status:</span> {couponToDelete.status}</p>
                {couponToDelete.customer_name && <p><span className="font-medium">Customer:</span> {couponToDelete.customer_name}</p>}
              </div>
              <p className="text-sm text-red-600">This will permanently delete the coupon and cannot be undone.</p>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => { setDeleteModalOpen(false); setCouponToDelete(null); }}>
                  Cancel
                </Button>
                <Button 
                  className="bg-red-600 hover:bg-red-700 text-white"
                  onClick={handleDeleteCoupon}
                  disabled={deleting}
                  data-testid="confirm-delete-coupon-btn"
                >
                  {deleting ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Trash2 className="h-4 w-4 mr-1" />}
                  Delete
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
