import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { 
  Ticket, Search, Loader2, RefreshCcw, Download, 
  Camera, User, Building2, CalendarDays, Phone,
  IndianRupee, X, ZoomIn
} from 'lucide-react';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function SoldCouponsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [workerFilter, setWorkerFilter] = useState('all');
  const [campaignFilter, setCampaignFilter] = useState('all');
  const [branchFilter, setBranchFilter] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [todayOnly, setTodayOnly] = useState(false);

  // Image viewer
  const [imageViewerOpen, setImageViewerOpen] = useState(false);
  const [viewingImageUrl, setViewingImageUrl] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.append('search', searchQuery.trim());
      if (workerFilter !== 'all') params.append('worker_id', workerFilter);
      if (campaignFilter !== 'all') params.append('campaign_id', campaignFilter);
      if (branchFilter !== 'all') params.append('branch_id', branchFilter);

      if (todayOnly) {
        const todayStr = new Date().toISOString().slice(0, 10);
        params.append('date_from', new Date(todayStr + 'T00:00:00+05:30').toISOString());
      } else {
        if (dateFrom) params.append('date_from', new Date(dateFrom).toISOString());
        if (dateTo) params.append('date_to', new Date(dateTo + 'T23:59:59').toISOString());
      }

      const res = await fetch(`${API_URL}/api/admin/sold-coupons?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        setData(await res.json());
      } else {
        toast.error('Failed to load sold coupons');
      }
    } catch {
      toast.error('Failed to load sold coupons');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, workerFilter, campaignFilter, branchFilter, dateFrom, dateTo, todayOnly]);

  useEffect(() => {
    const debounce = setTimeout(() => fetchData(), 300);
    return () => clearTimeout(debounce);
  }, [fetchData]);

  const openImageViewer = (url) => {
    let fullUrl = url;
    if (!url.startsWith('http')) {
      if (url.startsWith('/uploads/')) {
        fullUrl = `${API_URL}/api/uploads/${url.replace('/uploads/', '')}`;
      } else {
        fullUrl = `${API_URL}${url}`;
      }
    }
    setViewingImageUrl(fullUrl);
    setImageViewerOpen(true);
  };

  const handleExportExcel = () => {
    if (!data?.coupons?.length) {
      toast.error('No data to export');
      return;
    }
    const exportData = data.coupons.map(c => ({
      'Coupon Code': c.code,
      'Customer Name': c.customer_name,
      'Customer Phone': c.customer_phone,
      'Executive': c.worker_name,
      'Branch': c.branch_name,
      'Campaign': c.campaign_name,
      'Price': c.campaign_price,
      'Payment Mode': c.payment_mode,
      'City': c.city,
      'Sold At': c.sold_at ? new Date(c.sold_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : '',
    }));
    const ws = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Sold Coupons');
    XLSX.writeFile(wb, `SoldCoupons_${new Date().toISOString().slice(0, 10)}.xlsx`);
    toast.success(`Exported ${exportData.length} records`);
  };

  const formatDate = (date) => {
    if (!date) return '-';
    return new Date(date).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const getPhotoUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    if (url.startsWith('/uploads/')) return `${API_URL}/api/uploads/${url.replace('/uploads/', '')}`;
    return `${API_URL}${url}`;
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="sold-coupons-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight flex items-center gap-2">
              <Ticket className="h-7 w-7 text-[#ED1C24]" />
              Sold Coupons
            </h1>
            <p className="text-zinc-500 mt-1">
              Complete sold coupon history with executive details
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={fetchData} disabled={loading} data-testid="refresh-sold-coupons">
              <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" onClick={handleExportExcel} data-testid="export-sold-coupons">
              <Download className="h-4 w-4 mr-2" />
              Excel
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        {data && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-[#ED1C24]" data-testid="total-sold">{data.total}</p>
                <p className="text-xs text-zinc-500">Total Sold</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-green-600" data-testid="today-sold">{data.today_sold}</p>
                <p className="text-xs text-zinc-500">Sold Today</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-blue-600">{data.worker_summary?.length || 0}</p>
                <p className="text-xs text-zinc-500">Active Executives</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-purple-600">
                  {data.coupons?.reduce((s, c) => s + (c.campaign_price || 0), 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })}
                </p>
                <p className="text-xs text-zinc-500">Filtered Revenue</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Worker Summary */}
        {data?.worker_summary?.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Executive Sales Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {data.worker_summary.map(ws => (
                  <Badge
                    key={ws.worker_id}
                    variant="outline"
                    className="py-1.5 px-3 cursor-pointer hover:bg-zinc-100 transition-colors"
                    onClick={() => setWorkerFilter(ws.worker_id)}
                    data-testid={`worker-summary-${ws.worker_id}`}
                  >
                    <User className="h-3 w-3 mr-1" />
                    {ws.worker_name}: <span className="font-bold ml-1">{ws.sold_count}</span>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                <Input
                  placeholder="Search code/name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                  data-testid="search-sold-coupons"
                />
              </div>

              <Select value={workerFilter} onValueChange={setWorkerFilter}>
                <SelectTrigger data-testid="filter-worker">
                  <SelectValue placeholder="All Workers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Workers</SelectItem>
                  {data?.filters?.workers?.map(w => (
                    <SelectItem key={w.id} value={w.id}>{w.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={campaignFilter} onValueChange={setCampaignFilter}>
                <SelectTrigger data-testid="filter-campaign">
                  <SelectValue placeholder="All Campaigns" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Campaigns</SelectItem>
                  {data?.filters?.campaigns?.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={branchFilter} onValueChange={setBranchFilter}>
                <SelectTrigger data-testid="filter-branch">
                  <SelectValue placeholder="All Branches" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Branches</SelectItem>
                  {data?.filters?.branches?.map(b => (
                    <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Input
                type="date"
                value={dateFrom}
                onChange={(e) => { setDateFrom(e.target.value); setTodayOnly(false); }}
                placeholder="From"
                data-testid="date-from"
              />

              <div className="flex gap-1">
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => { setDateTo(e.target.value); setTodayOnly(false); }}
                  placeholder="To"
                  data-testid="date-to"
                  className="flex-1"
                />
                <Button
                  variant={todayOnly ? "default" : "outline"}
                  size="sm"
                  onClick={() => { setTodayOnly(!todayOnly); setDateFrom(''); setDateTo(''); }}
                  className={`whitespace-nowrap ${todayOnly ? 'bg-[#ED1C24] hover:bg-[#d01920]' : ''}`}
                  data-testid="today-filter-btn"
                >
                  Today
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </div>
        ) : !data?.coupons?.length ? (
          <Card>
            <CardContent className="p-12 text-center text-zinc-500">
              <Ticket className="h-12 w-12 mx-auto mb-4 text-zinc-300" />
              <p className="text-lg font-medium">No sold coupons found</p>
              <p className="text-sm mt-1">Adjust your filters or check back later</p>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-zinc-50">
                      <TableHead>Photo</TableHead>
                      <TableHead>Coupon Code</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Executive</TableHead>
                      <TableHead>Branch</TableHead>
                      <TableHead>Campaign</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Payment</TableHead>
                      <TableHead>Sold At</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.coupons.map((coupon) => (
                      <TableRow key={coupon.id} data-testid={`sold-coupon-row-${coupon.code}`}>
                        <TableCell>
                          {coupon.photo_url ? (
                            <img
                              src={getPhotoUrl(coupon.photo_url)}
                              alt="Coupon"
                              className="h-10 w-10 object-cover rounded cursor-pointer border hover:opacity-80 transition-opacity"
                              onClick={() => openImageViewer(coupon.photo_url)}
                              onError={(e) => { e.target.style.display = 'none'; }}
                              data-testid={`photo-thumb-${coupon.code}`}
                            />
                          ) : (
                            <div className="h-10 w-10 rounded bg-zinc-100 flex items-center justify-center">
                              <Camera className="h-4 w-4 text-zinc-300" />
                            </div>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="font-mono font-bold">{coupon.code}</Badge>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium text-sm">{coupon.customer_name || '-'}</p>
                            <p className="text-xs text-zinc-500 flex items-center gap-1">
                              <Phone className="h-3 w-3" />{coupon.customer_phone || '-'}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <User className="h-3 w-3 text-zinc-400" />
                            <span className="text-sm">{coupon.worker_name}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Building2 className="h-3 w-3 text-zinc-400" />
                            <span className="text-sm">{coupon.branch_name}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">{coupon.campaign_name}</TableCell>
                        <TableCell className="font-bold text-green-700">
                          <IndianRupee className="h-3 w-3 inline" />{coupon.campaign_price}
                        </TableCell>
                        <TableCell>
                          <Badge className={coupon.payment_mode === 'CASH' ? 'bg-orange-100 text-orange-800' : 'bg-blue-100 text-blue-800'}>
                            {coupon.payment_mode}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-zinc-500 whitespace-nowrap">
                          {formatDate(coupon.sold_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Image Viewer Modal */}
        <Dialog open={imageViewerOpen} onOpenChange={setImageViewerOpen}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle className="flex items-center justify-between">
                Coupon Photo
                <Button variant="ghost" size="sm" onClick={() => setImageViewerOpen(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </DialogTitle>
            </DialogHeader>
            <div className="flex items-center justify-center p-4 bg-zinc-100 rounded-lg min-h-[400px]">
              {viewingImageUrl ? (
                <img
                  src={viewingImageUrl}
                  alt="Coupon Photo"
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
