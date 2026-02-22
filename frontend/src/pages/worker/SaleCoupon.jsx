import React, { useState, useEffect, useRef } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Alert, AlertDescription } from '../../components/ui/alert';
import Webcam from 'react-webcam';
import { 
  Ticket, User, Phone, Camera, MapPin, Building2,
  Loader2, CheckCircle, AlertTriangle, Search,
  RefreshCcw, History
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function SaleCouponPage() {
  const [activeTab, setActiveTab] = useState('sale');
  
  // Sale form state
  const [step, setStep] = useState(1);
  const [couponCode, setCouponCode] = useState('');
  const [validating, setValidating] = useState(false);
  const [validatedCoupon, setValidatedCoupon] = useState(null);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [selectedBranch, setSelectedBranch] = useState('');
  const [branches, setBranches] = useState([]);
  const [photo, setPhoto] = useState(null);
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  // My Sales state
  const [mySales, setMySales] = useState([]);
  const [salesLoading, setSalesLoading] = useState(false);
  
  const webcamRef = useRef(null);

  useEffect(() => {
    fetchBranches();
    getCurrentLocation();
  }, []);

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

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          });
          if (position.coords.accuracy > 100) {
            setLocationError('GPS accuracy is low. Please try moving to an open area.');
          } else {
            setLocationError('');
          }
        },
        (error) => {
          setLocationError('Failed to get GPS location. Please enable location services.');
          toast.error('GPS location required for sale');
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    } else {
      setLocationError('Geolocation not supported by this browser');
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
        body: JSON.stringify({ code: couponCode.trim().toUpperCase() })
      });

      const data = await response.json();
      
      if (response.ok && data.is_valid) {
        setValidatedCoupon(data);
        toast.success(`Valid coupon: ${data.campaign_name} - ₹${data.price}`);
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

  const capturePhoto = () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      setPhoto(imageSrc);
      toast.success('Photo captured');
    }
  };

  const submitSale = async () => {
    // Validations
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
    if (!location) {
      toast.error('GPS location is required');
      getCurrentLocation();
      return;
    }
    if (location.accuracy > 100) {
      toast.error('GPS accuracy too low. Please try again in an open area.');
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
        latitude: location.latitude,
        longitude: location.longitude,
        gps_accuracy: location.accuracy
      };
      
      // Add photo if captured (optional)
      if (photo) {
        payload.image_base64 = photo;
      }

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
        // Reset form
        setStep(1);
        setCouponCode('');
        setValidatedCoupon(null);
        setCustomerName('');
        setCustomerPhone('');
        setSelectedBranch('');
        setPhoto(null);
        // Refresh location
        getCurrentLocation();
      } else {
        toast.error(data.detail || 'Failed to complete sale');
      }
    } catch (error) {
      toast.error('Failed to submit sale');
    } finally {
      setSubmitting(false);
    }
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

  const resetSale = () => {
    setStep(1);
    setCouponCode('');
    setValidatedCoupon(null);
    setCustomerName('');
    setCustomerPhone('');
    setSelectedBranch('');
    setPhoto(null);
    getCurrentLocation();
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="worker-sale-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              Sale Coupon
            </h1>
            <p className="text-zinc-500 mt-1">Record customer coupon sales</p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="sale">
              <Ticket className="h-4 w-4 mr-2" />
              New Sale
            </TabsTrigger>
            <TabsTrigger value="history">
              <History className="h-4 w-4 mr-2" />
              My Sales
            </TabsTrigger>
          </TabsList>

          {/* New Sale Tab */}
          <TabsContent value="sale" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Ticket className="h-5 w-5 text-blue-600" />
                  {step === 1 ? 'Step 1: Enter Coupon Code' : 
                   step === 2 ? 'Step 2: Customer Details' : 
                   'Step 3: Review & Submit'}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Step 1: Coupon Code */}
                {step === 1 && (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Coupon Code</Label>
                      <div className="flex gap-2">
                        <Input
                          placeholder="e.g., UT100"
                          value={couponCode}
                          onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                          className="font-mono text-lg"
                          data-testid="coupon-code-input"
                        />
                        <Button 
                          onClick={validateCouponCode}
                          disabled={validating || !couponCode.trim()}
                          data-testid="validate-coupon-btn"
                        >
                          {validating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                          Validate
                        </Button>
                      </div>
                    </div>

                    {/* Camera for optional photo capture */}
                    <div className="space-y-2">
                      <Label>Photo (Optional)</Label>
                      <div className="border rounded-lg overflow-hidden bg-zinc-100">
                        {!photo ? (
                          <div className="relative">
                            <Webcam
                              ref={webcamRef}
                              screenshotFormat="image/jpeg"
                              className="w-full h-48 object-cover"
                              videoConstraints={{
                                facingMode: 'environment',
                                width: 640,
                                height: 480
                              }}
                            />
                            <Button 
                              className="absolute bottom-2 left-1/2 -translate-x-1/2"
                              onClick={capturePhoto}
                            >
                              <Camera className="h-4 w-4 mr-2" />
                              Capture
                            </Button>
                          </div>
                        ) : (
                          <div className="relative">
                            <img src={photo} alt="Captured" className="w-full h-48 object-cover" />
                            <Button 
                              className="absolute bottom-2 left-1/2 -translate-x-1/2"
                              variant="secondary"
                              onClick={() => setPhoto(null)}
                            >
                              Retake
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* GPS Status */}
                    <div className="flex items-center gap-2 p-3 bg-zinc-50 rounded-lg">
                      <MapPin className={`h-4 w-4 ${location ? 'text-green-600' : 'text-zinc-400'}`} />
                      {location ? (
                        <span className="text-sm">
                          GPS: {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)} 
                          <span className={`ml-2 ${location.accuracy <= 100 ? 'text-green-600' : 'text-yellow-600'}`}>
                            (±{Math.round(location.accuracy)}m)
                          </span>
                        </span>
                      ) : (
                        <span className="text-sm text-zinc-500">Getting GPS location...</span>
                      )}
                      <Button size="sm" variant="ghost" onClick={getCurrentLocation}>
                        <RefreshCcw className="h-3 w-3" />
                      </Button>
                    </div>
                    
                    {locationError && (
                      <Alert className="border-yellow-500 bg-yellow-50">
                        <AlertTriangle className="h-4 w-4 text-yellow-600" />
                        <AlertDescription className="text-yellow-800">{locationError}</AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}

                {/* Step 2: Customer Details */}
                {step === 2 && validatedCoupon && (
                  <div className="space-y-4">
                    {/* Validated Coupon Info */}
                    <Alert className="border-green-500 bg-green-50">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-800">
                        <strong>{validatedCoupon.campaign_name}</strong> - ₹{validatedCoupon.price}
                        <span className="ml-2 font-mono">({couponCode})</span>
                      </AlertDescription>
                    </Alert>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Customer Name *</Label>
                        <Input
                          placeholder="Enter customer name"
                          value={customerName}
                          onChange={(e) => setCustomerName(e.target.value)}
                          data-testid="customer-name-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Mobile Number *</Label>
                        <Input
                          type="tel"
                          placeholder="10-digit mobile"
                          value={customerPhone}
                          onChange={(e) => setCustomerPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                          maxLength={10}
                          data-testid="customer-phone-input"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Select Branch *</Label>
                      <select
                        className="w-full h-10 px-3 border rounded-md"
                        value={selectedBranch}
                        onChange={(e) => setSelectedBranch(e.target.value)}
                        data-testid="branch-select"
                      >
                        <option value="">Select Branch</option>
                        {branches.map(branch => (
                          <option key={branch.id} value={branch.id}>{branch.name}</option>
                        ))}
                      </select>
                    </div>

                    {photo && (
                      <div className="space-y-2">
                        <Label>Captured Photo</Label>
                        <img src={photo} alt="Coupon" className="w-full max-w-md rounded-lg border" />
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button variant="outline" onClick={resetSale}>
                        Start Over
                      </Button>
                      <Button 
                        onClick={submitSale}
                        disabled={submitting || !customerName || !customerPhone || !selectedBranch}
                        className="flex-1"
                        data-testid="submit-sale-btn"
                      >
                        {submitting ? (
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        ) : (
                          <CheckCircle className="h-4 w-4 mr-2" />
                        )}
                        Complete Sale (₹{validatedCoupon.price})
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
                  <History className="h-5 w-5 text-blue-600" />
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
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
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
                            <TableCell className="font-medium">{sale.worker_name}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
                                <Building2 className="h-3 w-3 text-zinc-400" />
                                {sale.branch_name}
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
