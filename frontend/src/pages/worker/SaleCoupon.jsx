import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Alert, AlertDescription } from '../../components/ui/alert';
import PaymentQR from '../../components/PaymentQR';
import {
  Ticket, User, Phone, Building2,
  Loader2, CheckCircle, Search,
  RefreshCcw, History, ChevronRight, ChevronLeft,
  QrCode, CreditCard, IndianRupee
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const THEME_COLOR = '#ED1C24';

export default function SaleCouponPage() {
  const [activeTab, setActiveTab] = useState('sale');

  // 4-step sale process (Photo/OCR step removed)
  const [step, setStep] = useState(1);

  // Step 1: Coupon Code
  const [couponCode, setCouponCode] = useState('');
  const [validating, setValidating] = useState(false);
  const [validatedCoupon, setValidatedCoupon] = useState(null);

  // Step 2: Customer Details
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');

  // Step 3: Branch + Payment Mode
  const [selectedBranch, setSelectedBranch] = useState('');
  const [branches, setBranches] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  // Payment
  const [paymentMode, setPaymentMode] = useState('cash'); // 'cash' or 'upi'
  const [cashAllowed, setCashAllowed] = useState(true);

  // GPS Location (OPTIONAL — collected silently in background, NEVER blocks the sale)
  const [location, setLocation] = useState(null);

  // My Sales state
  const [mySales, setMySales] = useState([]);
  const [salesLoading, setSalesLoading] = useState(false);

  useEffect(() => {
    fetchBranches();
    fetchUserInfo();
    // Silently attempt GPS — failure is OK
    collectLocationSilently();
  }, []);

  const collectLocationSilently = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy
        });
      },
      () => {
        // Silent failure — GPS is optional, sale proceeds without it
      },
      { enableHighAccuracy: false, timeout: 5000, maximumAge: 60000 }
    );
  };

  const fetchUserInfo = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const userData = await response.json();
        setCashAllowed(userData.cash_allowed !== false);
        if (userData.cash_allowed === false) {
          setPaymentMode('upi');
        }
      }
    } catch (error) {
      console.error('Failed to fetch user info');
    }
  };

  const fetchBranches = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/branches`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setBranches(data.filter(b => b.is_active !== false));
      }
    } catch (error) {
      console.error('Failed to fetch branches');
    }
  };

  const validateCouponCode = async () => {
    if (!couponCode.trim()) {
      toast.error('Please enter a coupon code');
      return;
    }
    setValidating(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/campaigns/validate-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ coupon_code: couponCode.trim().toUpperCase() })
      });
      const data = await response.json();
      if (response.ok && (data.valid || data.is_valid)) {
        setValidatedCoupon(data);
        toast.success(`Valid coupon: ${data.campaign_name} - ₹${data.campaign_price || data.price}`);
        setStep(2);
      } else {
        toast.error(data.detail || data.message || 'Invalid coupon code');
        setValidatedCoupon(null);
      }
    } catch (error) {
      toast.error('Failed to validate coupon');
    } finally {
      setValidating(false);
    }
  };

  const submitSale = async () => {
    // Validations — NO GPS REQUIRED
    if (!validatedCoupon) {
      toast.error('Please validate coupon code first');
      return;
    }
    if (!customerName.trim()) {
      toast.error('Customer name is required');
      return;
    }
    if (!customerPhone.trim() || customerPhone.length < 10) {
      toast.error('Valid phone number is required (10 digits)');
      return;
    }
    if (!selectedBranch) {
      toast.error('Please select a branch');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');

      const payload = {
        coupon_code: couponCode.trim().toUpperCase(),
        customer_name: customerName.trim(),
        customer_phone: customerPhone.trim(),
        branch_id: selectedBranch,
        // GPS is OPTIONAL — send null if unavailable, NEVER block the sale
        latitude: location ? location.latitude : null,
        longitude: location ? location.longitude : null,
        gps_accuracy: location ? location.accuracy : null,
        // Backend expects "CASH" or "QR" (UPI is the user-facing label for QR)
        payment_mode: paymentMode === 'upi' ? 'QR' : 'CASH'
      };

      const response = await fetch(`${API_URL}/api/campaigns/worker-sale`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(data.message || 'Coupon sold successfully!');
        resetSale();
      } else {
        // data.detail may be a string (HTTPException) or an array (Pydantic 422)
        let errMsg = 'Failed to complete sale';
        if (typeof data.detail === 'string') {
          errMsg = data.detail;
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          errMsg = data.detail.map(d => `${d.loc?.slice(-1)[0] || 'field'}: ${d.msg}`).join('; ');
        }
        toast.error(errMsg);
      }
    } catch (error) {
      toast.error('Failed to submit sale');
    } finally {
      setSubmitting(false);
    }
  };

  const resetSale = () => {
    setStep(1);
    setCouponCode('');
    setValidatedCoupon(null);
    setCustomerName('');
    setCustomerPhone('');
    setSelectedBranch('');
    setPaymentMode('cash');
    // Refresh location silently for next sale
    collectLocationSilently();
  };

  const fetchMySales = async () => {
    setSalesLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/campaigns/worker/my-sales`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        setMySales(await response.json());
      }
    } catch (error) {
      toast.error('Failed to load sales');
    } finally {
      setSalesLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') {
      fetchMySales();
    }
  }, [activeTab]);

  const formatDate = (date) => {
    if (!date) return '-';
    return new Date(date).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStepTitle = () => {
    switch (step) {
      case 1: return 'Step 1: Enter Coupon Code';
      case 2: return 'Step 2: Customer Details';
      case 3: return 'Step 3: Branch & Payment';
      case 4: return 'Step 4: Payment';
      default: return '';
    }
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="worker-sale-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight" style={{ color: THEME_COLOR }}>
              Sale Coupon
            </h1>
            <p className="text-zinc-500 mt-1">Record customer coupon sales</p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="sale" className="data-[state=active]:text-[#ED1C24]">
              <Ticket className="h-4 w-4 mr-2" />
              New Sale
            </TabsTrigger>
            <TabsTrigger value="history" className="data-[state=active]:text-[#ED1C24]">
              <History className="h-4 w-4 mr-2" />
              My Sales
            </TabsTrigger>
          </TabsList>

          {/* New Sale Tab */}
          <TabsContent value="sale" className="mt-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Ticket className="h-5 w-5" style={{ color: THEME_COLOR }} />
                    {getStepTitle()}
                  </CardTitle>
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4].map(s => (
                      <div
                        key={s}
                        className={`w-6 h-2 rounded-full transition-colors ${
                          s <= step ? 'bg-[#ED1C24]' : 'bg-zinc-200'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">

                {/* ===== STEP 1: Coupon Code ===== */}
                {step === 1 && (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label className="text-base font-semibold">Coupon Code *</Label>
                      <div className="flex gap-2">
                        <Input
                          placeholder="e.g., UT100"
                          value={couponCode}
                          onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                          className="font-mono text-lg h-12"
                          data-testid="coupon-code-input"
                        />
                        <Button
                          onClick={validateCouponCode}
                          disabled={validating || !couponCode.trim()}
                          className="h-12 px-6"
                          style={{ backgroundColor: THEME_COLOR }}
                          data-testid="validate-coupon-btn"
                        >
                          {validating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4 mr-2" />}
                          {validating ? 'Validating...' : 'Validate'}
                        </Button>
                      </div>
                      <p className="text-sm text-zinc-500">Enter the coupon code printed on the coupon</p>
                    </div>
                  </div>
                )}

                {/* ===== STEP 2: Customer Details ===== */}
                {step === 2 && (
                  <div className="space-y-4">
                    <Alert className="border-green-500 bg-green-50">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-800">
                        <strong>{validatedCoupon?.campaign_name}</strong> - ₹{validatedCoupon?.campaign_price || validatedCoupon?.price}
                        <span className="ml-2 font-mono">({couponCode})</span>
                      </AlertDescription>
                    </Alert>

                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label className="text-base font-semibold flex items-center gap-2">
                          <User className="h-4 w-4" />
                          Customer Name *
                        </Label>
                        <Input
                          placeholder="Enter customer full name"
                          value={customerName}
                          onChange={(e) => setCustomerName(e.target.value)}
                          className="h-12"
                          data-testid="customer-name-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-base font-semibold flex items-center gap-2">
                          <Phone className="h-4 w-4" />
                          Mobile Number *
                        </Label>
                        <Input
                          type="tel"
                          placeholder="10-digit mobile number"
                          value={customerPhone}
                          onChange={(e) => setCustomerPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                          maxLength={10}
                          className="h-12 font-mono"
                          data-testid="customer-phone-input"
                        />
                      </div>
                    </div>

                    <div className="flex gap-2 pt-4">
                      <Button variant="outline" onClick={() => setStep(1)}>
                        <ChevronLeft className="h-4 w-4 mr-1" /> Back
                      </Button>
                      <Button
                        onClick={() => setStep(3)}
                        disabled={!customerName.trim() || customerPhone.length < 10}
                        className="flex-1"
                        style={{ backgroundColor: THEME_COLOR }}
                        data-testid="customer-continue-btn"
                      >
                        Continue <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </div>
                  </div>
                )}

                {/* ===== STEP 3: Branch + Payment Mode + Submit ===== */}
                {step === 3 && (
                  <div className="space-y-4">
                    {/* Summary */}
                    <div className="p-4 bg-zinc-50 rounded-lg space-y-2">
                      <h3 className="font-semibold text-sm text-zinc-500 uppercase">Sale Summary</h3>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div><span className="text-zinc-500">Coupon:</span> <strong className="font-mono">{couponCode}</strong></div>
                        <div><span className="text-zinc-500">Amount:</span> <strong className="text-green-600">₹{validatedCoupon?.campaign_price || validatedCoupon?.price}</strong></div>
                        <div><span className="text-zinc-500">Customer:</span> <strong>{customerName}</strong></div>
                        <div><span className="text-zinc-500">Phone:</span> <strong>{customerPhone}</strong></div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-base font-semibold flex items-center gap-2">
                        <Building2 className="h-4 w-4" />
                        Select Branch *
                      </Label>
                      <select
                        className="w-full h-12 px-3 border rounded-md text-base"
                        value={selectedBranch}
                        onChange={(e) => setSelectedBranch(e.target.value)}
                        data-testid="branch-select"
                      >
                        <option value="">-- Select Branch --</option>
                        {branches.map(branch => (
                          <option key={branch.id} value={branch.id}>{branch.name}</option>
                        ))}
                      </select>
                    </div>

                    {/* Payment Mode Selection */}
                    <div className="space-y-2">
                      <Label className="text-base font-semibold flex items-center gap-2">
                        <CreditCard className="h-4 w-4" />
                        Payment Mode *
                      </Label>
                      <div className={`grid ${cashAllowed ? 'grid-cols-2' : 'grid-cols-1'} gap-3`}>
                        {cashAllowed && (
                          <button
                            type="button"
                            onClick={() => setPaymentMode('cash')}
                            className={`p-4 rounded-lg border-2 transition-all flex flex-col items-center gap-2 ${
                              paymentMode === 'cash'
                                ? 'border-[#ED1C24] bg-red-50'
                                : 'border-zinc-200 hover:border-zinc-300'
                            }`}
                            data-testid="payment-cash-btn"
                          >
                            <IndianRupee className={`h-6 w-6 ${paymentMode === 'cash' ? 'text-[#ED1C24]' : 'text-zinc-500'}`} />
                            <span className={`font-medium ${paymentMode === 'cash' ? 'text-[#ED1C24]' : 'text-zinc-700'}`}>
                              Cash
                            </span>
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => setPaymentMode('upi')}
                          className={`p-4 rounded-lg border-2 transition-all flex flex-col items-center gap-2 ${
                            paymentMode === 'upi'
                              ? 'border-[#ED1C24] bg-red-50'
                              : 'border-zinc-200 hover:border-zinc-300'
                          }`}
                          data-testid="payment-upi-btn"
                        >
                          <QrCode className={`h-6 w-6 ${paymentMode === 'upi' ? 'text-[#ED1C24]' : 'text-zinc-500'}`} />
                          <span className={`font-medium ${paymentMode === 'upi' ? 'text-[#ED1C24]' : 'text-zinc-700'}`}>
                            UPI / QR
                          </span>
                        </button>
                      </div>
                      {!cashAllowed && (
                        <p className="text-sm text-amber-600 mt-2">
                          Cash payments are disabled for your account. Please use QR/UPI only.
                        </p>
                      )}
                    </div>

                    {/* Navigation & Submit */}
                    <div className="flex gap-2 pt-4">
                      <Button variant="outline" onClick={() => setStep(2)}>
                        <ChevronLeft className="h-4 w-4 mr-1" /> Back
                      </Button>
                      {paymentMode === 'cash' ? (
                        <Button
                          onClick={submitSale}
                          disabled={submitting || !selectedBranch}
                          className="flex-1 h-12 text-lg"
                          style={{ backgroundColor: '#16a34a' }}
                          data-testid="submit-sale-btn"
                        >
                          {submitting ? (
                            <Loader2 className="h-5 w-5 animate-spin mr-2" />
                          ) : (
                            <CheckCircle className="h-5 w-5 mr-2" />
                          )}
                          Complete Sale (Cash ₹{validatedCoupon?.campaign_price || validatedCoupon?.price})
                        </Button>
                      ) : (
                        <Button
                          onClick={() => setStep(4)}
                          disabled={!selectedBranch}
                          className="flex-1 h-12 text-lg"
                          style={{ backgroundColor: THEME_COLOR }}
                          data-testid="generate-qr-btn"
                        >
                          <QrCode className="h-5 w-5 mr-2" />
                          Generate Payment QR
                          <ChevronRight className="h-4 w-4 ml-1" />
                        </Button>
                      )}
                    </div>

                    <Button variant="link" onClick={resetSale} className="w-full text-zinc-500">
                      Cancel & Start Over
                    </Button>
                  </div>
                )}

                {/* ===== STEP 4: UPI Payment with QR ===== */}
                {step === 4 && (
                  <div className="space-y-4">
                    <PaymentQR
                      ticketId={validatedCoupon?.coupon_id || couponCode}
                      amount={validatedCoupon?.campaign_price || validatedCoupon?.price}
                      customerName={customerName}
                      customerPhone={customerPhone}
                      onPaymentSuccess={() => {
                        toast.success('Payment received! Completing sale...');
                        submitSale();
                      }}
                      onPaymentFailed={() => {
                        toast.error('Payment failed. You can retry or switch to cash.');
                      }}
                      onCancel={() => {
                        setStep(3);
                        setPaymentMode('cash');
                      }}
                    />

                    <div className="flex gap-2 pt-2">
                      <Button variant="outline" onClick={() => setStep(3)} className="flex-1">
                        <ChevronLeft className="h-4 w-4 mr-1" /> Back to Options
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* My Sales History Tab */}
          <TabsContent value="history" className="mt-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5" style={{ color: THEME_COLOR }} />
                  My Sales History
                </CardTitle>
                <Button variant="outline" size="sm" onClick={fetchMySales}>
                  <RefreshCcw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
              </CardHeader>
              <CardContent>
                {salesLoading ? (
                  <div className="flex items-center justify-center h-40">
                    <Loader2 className="h-8 w-8 animate-spin" style={{ color: THEME_COLOR }} />
                  </div>
                ) : mySales.length === 0 ? (
                  <div className="text-center py-8 text-zinc-500">
                    <Ticket className="h-12 w-12 mx-auto mb-4 text-zinc-300" />
                    <p>No sales recorded yet</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Coupon</TableHead>
                          <TableHead>Customer</TableHead>
                          <TableHead>Worker</TableHead>
                          <TableHead>Branch</TableHead>
                          <TableHead>Campaign</TableHead>
                          <TableHead>Amount</TableHead>
                          <TableHead>Date</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {mySales.map((sale) => (
                          <TableRow key={sale.coupon_id}>
                            <TableCell>
                              <code className="px-2 py-1 bg-zinc-100 rounded text-sm">
                                {sale.coupon_code}
                              </code>
                            </TableCell>
                            <TableCell>
                              <div>
                                <p className="font-medium">{sale.customer_name}</p>
                                <p className="text-xs text-zinc-500">****{sale.customer_phone_last4}</p>
                              </div>
                            </TableCell>
                            <TableCell className="font-medium">{sale.worker_name || '-'}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
                                <Building2 className="h-3 w-3 text-zinc-400" />
                                {sale.branch_name || '-'}
                              </div>
                            </TableCell>
                            <TableCell>{sale.campaign_name}</TableCell>
                            <TableCell className="font-bold text-green-600">
                              ₹{sale.campaign_price}
                            </TableCell>
                            <TableCell className="text-sm text-zinc-500">
                              {formatDate(sale.sold_at)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
