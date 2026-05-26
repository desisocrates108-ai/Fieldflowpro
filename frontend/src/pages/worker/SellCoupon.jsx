import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import {
  CheckCircle, XCircle, Loader2,
  Ticket, User, Phone,
  ArrowRight, Search
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function SellCouponPage() {
  // Steps: 1=Code Entry, 2=Customer Details, 3=Confirm, 4=Success
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Step 1: Code validation
  const [couponCode, setCouponCode] = useState('');
  const [validationResult, setValidationResult] = useState(null);
  const [validating, setValidating] = useState(false);

  // Step 2: Customer details
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');

  // Location (collected silently in background — NEVER required)
  const [location, setLocation] = useState(null);
  const [gpsAccuracy, setGpsAccuracy] = useState(null);

  // Areas
  const [areas, setAreas] = useState([]);
  const [selectedArea, setSelectedArea] = useState('');

  // Result
  const [saleResult, setSaleResult] = useState(null);

  useEffect(() => {
    fetchAreas();
    collectLocationSilently();
  }, []);

  const fetchAreas = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/areas`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setAreas(data);
      }
    } catch (error) {
      console.error('Failed to fetch areas');
    }
  };

  const collectLocationSilently = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        });
        setGpsAccuracy(position.coords.accuracy);
      },
      () => {
        // Silent failure — GPS is optional, sale proceeds without it
      },
      { enableHighAccuracy: false, timeout: 5000, maximumAge: 60000 }
    );
  };

  // Step 1: Validate coupon code
  const validateCode = async () => {
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
      setValidationResult(data);

      if (data.valid) {
        toast.success(`Coupon valid! ${data.campaign_name} - ₹${data.campaign_price}`);
        setStep(2);
      } else {
        toast.error(data.message);
      }
    } catch (error) {
      toast.error('Failed to validate coupon');
    } finally {
      setValidating(false);
    }
  };

  // Step 2 → Step 3: Review and confirm (NO GPS REQUIREMENT)
  const proceedToConfirm = () => {
    if (!customerName.trim()) {
      toast.error('Please enter customer name');
      return;
    }
    if (!customerPhone.trim() || customerPhone.length !== 10) {
      toast.error('Please enter valid 10-digit mobile number');
      return;
    }
    setStep(3);
  };

  // Step 3 → Step 4: Complete sale
  const completeSale = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/campaigns/sell`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          coupon_code: couponCode.trim().toUpperCase(),
          customer_name: customerName.trim(),
          customer_phone: customerPhone.trim(),
          // GPS is OPTIONAL — send null when not available
          latitude: location ? location.lat : null,
          longitude: location ? location.lng : null,
          gps_accuracy: gpsAccuracy,
          area_id: selectedArea || null
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSaleResult(data);
        setStep(4);
        toast.success(`Sale complete! ₹${data.campaign_price} added to ledger`);
      } else {
        toast.error(data.detail || 'Sale failed');
      }
    } catch (error) {
      toast.error('Failed to complete sale');
    } finally {
      setLoading(false);
    }
  };

  // Reset for new sale
  const resetForm = () => {
    setStep(1);
    setCouponCode('');
    setValidationResult(null);
    setCustomerName('');
    setCustomerPhone('');
    setSaleResult(null);
    setSelectedArea('');
    collectLocationSilently();
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto space-y-6" data-testid="sell-coupon-page">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
            Sell Coupon
          </h1>
          <p className="text-zinc-500 mt-1">
            Enter code, confirm details, complete sale
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-2">
          {[1, 2, 3, 4].map((s) => (
            <React.Fragment key={s}>
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                ${step >= s ? 'bg-blue-600 text-white' : 'bg-zinc-200 text-zinc-500'}
              `}>
                {step > s ? <CheckCircle className="h-4 w-4" /> : s}
              </div>
              {s < 4 && <div className={`w-12 h-1 ${step > s ? 'bg-blue-600' : 'bg-zinc-200'}`} />}
            </React.Fragment>
          ))}
        </div>

        {/* Step 1: Code Entry */}
        {step === 1 && (
          <Card data-testid="step-1-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Ticket className="h-5 w-5 text-blue-600" />
                Enter Coupon Code
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Coupon Code</Label>
                <Input
                  placeholder="e.g., MUM001, SA025"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                  className="text-lg font-mono text-center tracking-wider"
                  data-testid="coupon-code-input"
                />
              </div>

              {validationResult && !validationResult.valid && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2 text-red-700">
                    <XCircle className="h-4 w-4" />
                    <span>{validationResult.message}</span>
                  </div>
                </div>
              )}

              <Button
                className="w-full bg-blue-600 hover:bg-blue-700"
                onClick={validateCode}
                disabled={validating}
                data-testid="validate-code-btn"
              >
                {validating ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Search className="h-4 w-4 mr-2" />
                )}
                Validate Code
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Customer Details (camera/OCR step removed) */}
        {step === 2 && (
          <Card data-testid="step-2-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-blue-600" />
                Customer Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Campaign Info */}
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-green-800">{validationResult?.campaign_name}</p>
                    <code className="text-sm text-green-600">{couponCode}</code>
                  </div>
                  <Badge className="bg-green-600 text-white text-lg px-3">
                    ₹{validationResult?.campaign_price}
                  </Badge>
                </div>
              </div>

              {/* Customer Details */}
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <User className="h-4 w-4" />
                    Customer Name
                  </Label>
                  <Input
                    placeholder="Enter customer name"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    data-testid="customer-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    Mobile Number
                  </Label>
                  <Input
                    placeholder="10-digit mobile"
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                    data-testid="customer-phone-input"
                  />
                </div>
              </div>

              {/* Area Selection */}
              <div className="space-y-2">
                <Label>Area (Optional)</Label>
                <Select value={selectedArea} onValueChange={setSelectedArea}>
                  <SelectTrigger data-testid="area-select">
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

              <Button
                className="w-full bg-blue-600 hover:bg-blue-700"
                onClick={proceedToConfirm}
                disabled={!customerName || !customerPhone}
                data-testid="proceed-confirm-btn"
              >
                Review & Confirm
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Confirm */}
        {step === 3 && (
          <Card data-testid="step-3-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                Confirm Sale
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Summary */}
              <div className="space-y-3 p-4 bg-zinc-50 rounded-lg">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Campaign</span>
                  <span className="font-medium">{validationResult?.campaign_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Coupon Code</span>
                  <code className="font-mono">{couponCode}</code>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Price</span>
                  <span className="font-bold text-green-600">₹{validationResult?.campaign_price}</span>
                </div>
                <hr />
                <div className="flex justify-between">
                  <span className="text-zinc-500">Customer</span>
                  <span className="font-medium">{customerName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Mobile</span>
                  <span>{customerPhone}</span>
                </div>
                {selectedArea && (
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Area</span>
                    <span>{areas.find(a => a.id === selectedArea)?.name}</span>
                  </div>
                )}
              </div>

              <div className="flex gap-3">
                <Button variant="outline" className="flex-1" onClick={() => setStep(2)}>
                  Back to Edit
                </Button>
                <Button
                  className="flex-1 bg-green-600 hover:bg-green-700"
                  onClick={completeSale}
                  disabled={loading}
                  data-testid="confirm-sale-btn"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <CheckCircle className="h-4 w-4 mr-2" />
                  )}
                  Confirm Sale
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 4: Success */}
        {step === 4 && (
          <Card data-testid="step-4-card">
            <CardContent className="py-8 text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-green-700">Sale Complete!</h2>
              <div className="space-y-2 text-zinc-600">
                <p>Coupon <code className="font-mono bg-zinc-100 px-2 py-1 rounded">{saleResult?.coupon_code}</code> sold successfully</p>
                <p className="text-xl font-bold text-green-600">
                  ₹{saleResult?.campaign_price} added to your ledger
                </p>
              </div>
              <Button
                className="bg-blue-600 hover:bg-blue-700"
                onClick={resetForm}
                data-testid="new-sale-btn"
              >
                <Ticket className="h-4 w-4 mr-2" />
                New Sale
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
