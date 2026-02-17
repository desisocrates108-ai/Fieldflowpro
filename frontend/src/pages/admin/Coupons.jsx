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
import { 
  Loader2, Search, Ticket, Phone, User, 
  CheckCircle, XCircle, Eye, MapPin, Clock,
  Camera, AlertCircle, RefreshCcw
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

  const filteredCoupons = coupons.filter(coupon => 
    coupon.code?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    coupon.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (coupon.customer_phone || coupon.mobile_last4 || '').includes(searchQuery)
  );

  return (
    <Layout>
      <div className="space-y-6" data-testid="coupons-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
            Coupons
          </h1>
          <p className="text-zinc-500 mt-1">
            View and manage all issued coupons
          </p>
        </div>

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
              <SelectItem value="ISSUED">Issued</SelectItem>
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
                    <TableHead>Redeemed At</TableHead>
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
                          {coupon.customer_phone}
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
                      <TableCell className="text-zinc-600">
                        {coupon.redeemed_at ? formatDateTime(coupon.redeemed_at) : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
