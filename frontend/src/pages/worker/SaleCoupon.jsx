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
import { createWorker } from 'tesseract.js';
import { 
  Ticket, User, Phone, Camera, MapPin, Building2,
  Loader2, CheckCircle, AlertTriangle, Search,
  RefreshCcw, History, Eye, ScanLine
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// OCR is optional - set to false to disable OCR completely
const USE_OCR = true;

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
  
  // OCR state (optional - non-blocking)
  const [ocrRunning, setOcrRunning] = useState(false);
  const [ocrResult, setOcrResult] = useState(null);
  const [ocrDetectedName, setOcrDetectedName] = useState('');
  const [ocrDetectedPhone, setOcrDetectedPhone] = useState('');
  const [ocrConfidence, setOcrConfidence] = useState(0);
  
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

  const capturePhoto = async () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      setPhoto(imageSrc);
      toast.success('Photo captured');
      
      // Run OCR in background (non-blocking)
      if (USE_OCR && imageSrc) {
        runOCR(imageSrc);
      }
    }
  };

  // OCR runs in background - does NOT block submission
  const runOCR = async (imageSrc) => {
    setOcrRunning(true);
    setOcrResult(null);
    
    try {
      const worker = await createWorker('eng');
      const { data } = await worker.recognize(imageSrc);
      await worker.terminate();
      
      setOcrResult(data.text);
      setOcrConfidence(data.confidence);
      
      // Try to extract name and phone from OCR text
      const lines = data.text.split('\n').filter(l => l.trim());
      
      // Simple extraction - look for patterns
      let detectedName = '';
      let detectedPhone = '';
      
      for (const line of lines) {
        // Phone pattern
        const phoneMatch = line.match(/(\d{10})/);
        if (phoneMatch && !detectedPhone) {
          detectedPhone = phoneMatch[1];
        }
        
        // Name pattern (lines with mostly letters)
        if (!detectedName && line.length > 3 && /^[a-zA-Z\s]+$/.test(line.trim())) {
          detectedName = line.trim();
        }
      }
      
      setOcrDetectedName(detectedName);
      setOcrDetectedPhone(detectedPhone);
      
      // Auto-fill if fields are empty (helpful, not required)
      if (detectedName && !customerName) {
        setCustomerName(detectedName);
      }
      if (detectedPhone && !customerPhone) {
        setCustomerPhone(detectedPhone);
      }
      
      if (detectedName || detectedPhone) {
        toast.info('OCR detected some data - please verify');
      }
    } catch (error) {
      console.error('OCR failed:', error);
      // OCR failure is NOT a blocker - sale can proceed
    } finally {
      setOcrRunning(false);
    }
  };

  const submitSale = async () => {
    // Validations - OCR is NOT required
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
        gps_accuracy: location.accuracy,
        // OCR data is optional - sent if available
        ocr_detected_name: ocrDetectedName || null,
        ocr_detected_phone: ocrDetectedPhone || null,
        ocr_confidence: ocrConfidence || null
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
        
        // Show OCR mismatch warning if any (informational only)
        if (data.ocr_mismatch_warning) {
          toast.warning(data.ocr_mismatch_warning, { duration: 5000 });
        }
        
        // Reset form
        resetSale();
      } else {
        toast.error(data.detail || 'Failed to complete sale');
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
    setPhoto(null);
    setOcrResult(null);
    setOcrDetectedName('');
    setOcrDetectedPhone('');
    setOcrConfidence(0);
    getCurrentLocation();
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
                  {step === 1 ? 'Step 1: Coupon Details' : 'Step 2: Customer Details & Submit'}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Step 1: Coupon Code + Photo */}
                {step === 1 && (
                  <div className="space-y-4">
                    {/* Coupon Code Input */}
                    <div className="space-y-2">
                      <Label>Coupon Code *</Label>
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

                    {/* Camera for Photo Capture */}
                    <div className="space-y-2">
                      <Label className="flex items-center gap-2">
                        <Camera className="h-4 w-4" />
                        Coupon Photo (Optional - enables OCR)
                      </Label>
                      <div className="border rounded-lg overflow-hidden bg-zinc-100">
                        {!photo ? (
                          <div className="relative">
                            <Webcam
                              ref={webcamRef}
                              screenshotFormat="image/jpeg"
                              className="w-full h-52 object-cover"
                              videoConstraints={{
                                facingMode: 'environment',
                                width: 640,
                                height: 480
                              }}
                            />
                            <Button 
                              className="absolute bottom-3 left-1/2 -translate-x-1/2"
                              onClick={capturePhoto}
                            >
                              <Camera className="h-4 w-4 mr-2" />
                              Capture Photo
                            </Button>
                          </div>
                        ) : (
                          <div className="relative">
                            <img src={photo} alt="Captured" className="w-full h-52 object-cover" />
                            <div className="absolute top-2 right-2">
                              {ocrRunning && (
                                <Badge className="bg-blue-600">
                                  <ScanLine className="h-3 w-3 mr-1 animate-pulse" />
                                  Scanning...
                                </Badge>
                              )}
                              {!ocrRunning && ocrResult && (
                                <Badge className="bg-green-600">
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                  OCR Done
                                </Badge>
                              )}
                            </div>
                            <Button 
                              className="absolute bottom-3 left-1/2 -translate-x-1/2"
                              variant="secondary"
                              onClick={() => {
                                setPhoto(null);
                                setOcrResult(null);
                                setOcrDetectedName('');
                                setOcrDetectedPhone('');
                              }}
                            >
                              Retake Photo
                            </Button>
                          </div>
                        )}
                      </div>
                      <p className="text-xs text-zinc-500">
                        Photo helps with OCR auto-fill but is not required for sale.
                      </p>
                    </div>

                    {/* OCR Results (if available) */}
                    {ocrResult && (ocrDetectedName || ocrDetectedPhone) && (
                      <Alert className="border-blue-500 bg-blue-50">
                        <Eye className="h-4 w-4 text-blue-600" />
                        <AlertDescription className="text-blue-800">
                          <strong>OCR Detected:</strong>
                          {ocrDetectedName && <span className="ml-2">Name: {ocrDetectedName}</span>}
                          {ocrDetectedPhone && <span className="ml-2">| Phone: {ocrDetectedPhone}</span>}
                          <span className="ml-2 text-xs">(Confidence: {ocrConfidence.toFixed(0)}%)</span>
                        </AlertDescription>
                      </Alert>
                    )}

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

                {/* Step 2: Customer Details & Submit */}
                {step === 2 && validatedCoupon && (
                  <div className="space-y-4">
                    {/* Validated Coupon Info */}
                    <Alert className="border-green-500 bg-green-50">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-800">
                        <strong>{validatedCoupon.campaign_name}</strong> - ₹{validatedCoupon.campaign_price || validatedCoupon.price}
                        <span className="ml-2 font-mono">({couponCode})</span>
                      </AlertDescription>
                    </Alert>

                    {/* Show captured photo if any */}
                    {photo && (
                      <div className="relative">
                        <img src={photo} alt="Coupon" className="w-full max-w-md rounded-lg border" />
                        {ocrRunning && (
                          <div className="absolute inset-0 bg-black/50 flex items-center justify-center rounded-lg">
                            <div className="text-white text-center">
                              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                              <p>Scanning with OCR...</p>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* OCR comparison (informational) */}
                    {ocrResult && (ocrDetectedName || ocrDetectedPhone) && (
                      <Alert className="border-blue-200 bg-blue-50">
                        <Eye className="h-4 w-4 text-blue-600" />
                        <AlertDescription className="text-blue-700 text-sm">
                          <strong>OCR Suggestion:</strong> 
                          {ocrDetectedName && <span className="ml-1">Name: "{ocrDetectedName}"</span>}
                          {ocrDetectedPhone && <span className="ml-1">| Phone: "{ocrDetectedPhone}"</span>}
                          <br />
                          <span className="text-xs">Please verify and correct if needed. OCR is not mandatory.</span>
                        </AlertDescription>
                      </Alert>
                    )}

                    {/* Customer Details Form */}
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

                    {/* Submit Buttons */}
                    <div className="flex gap-2 pt-4">
                      <Button variant="outline" onClick={resetSale}>
                        Start Over
                      </Button>
                      <Button 
                        onClick={submitSale}
                        disabled={submitting || !customerName || !customerPhone || !selectedBranch}
                        className="flex-1 bg-green-600 hover:bg-green-700"
                        data-testid="submit-sale-btn"
                      >
                        {submitting ? (
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        ) : (
                          <CheckCircle className="h-4 w-4 mr-2" />
                        )}
                        Complete Sale (₹{validatedCoupon.campaign_price || validatedCoupon.price})
                      </Button>
                    </div>

                    <p className="text-xs text-zinc-500 text-center">
                      OCR verification is optional. Sale will proceed with the details you entered.
                    </p>
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
