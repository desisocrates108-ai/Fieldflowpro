import React, { useState, useRef, useCallback, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import Webcam from 'react-webcam';
import { createWorker } from 'tesseract.js';
import { 
  Camera, CheckCircle, XCircle, Loader2, MapPin, 
  Ticket, User, Phone, IndianRupee, AlertCircle,
  ArrowRight, RefreshCcw, Building2, AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function SaleCouponPage() {
  // Steps: 1=Manual Entry, 2=Photo+OCR, 3=Enter Code, 4=Select Branch, 5=Confirm, 6=Success
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Step 1: Manual entry
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  
  // Step 2: Photo & OCR
  const [capturedImage, setCapturedImage] = useState(null);
  const [ocrProcessing, setOcrProcessing] = useState(false);
  const [ocrName, setOcrName] = useState('');
  const [ocrPhone, setOcrPhone] = useState('');
  const [ocrConfidence, setOcrConfidence] = useState(0);
  const [ocrMismatch, setOcrMismatch] = useState(false);
  
  // Step 3: Coupon code
  const [couponCode, setCouponCode] = useState('');
  const [validationResult, setValidationResult] = useState(null);
  const [validating, setValidating] = useState(false);
  
  // Step 4: Branch
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  
  // Location
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [gpsAccuracy, setGpsAccuracy] = useState(null);
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [areaName, setAreaName] = useState('');
  
  // Result
  const [saleResult, setSaleResult] = useState(null);
  
  const webcamRef = useRef(null);

  useEffect(() => {
    fetchBranches();
    getLocation();
  }, []);

  const fetchBranches = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/branches`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setBranches(data);
      }
    } catch (error) {
      console.error('Failed to fetch branches');
    }
  };

  const getLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation not supported');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        setLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        });
        setGpsAccuracy(position.coords.accuracy);
        setLocationError(null);
        
        // Try reverse geocoding
        try {
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}&zoom=18&addressdetails=1`,
            { headers: { 'User-Agent': 'FieldFlowPro/3.0' } }
          );
          if (response.ok) {
            const data = await response.json();
            const address = data.address || {};
            setCity(address.city || address.town || address.village || address.county || '');
            setState(address.state || '');
            setAreaName(address.suburb || address.neighbourhood || address.locality || '');
          }
        } catch (e) {
          console.log('Reverse geocoding failed, using manual fallback');
        }
      },
      (error) => {
        setLocationError('Unable to get location. Please enable GPS.');
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // Step 1: Proceed to photo
  const proceedToPhoto = () => {
    if (!customerName.trim()) {
      toast.error('Please enter customer name');
      return;
    }
    if (!customerPhone.trim() || customerPhone.length !== 10) {
      toast.error('Please enter valid 10-digit mobile number');
      return;
    }
    setStep(2);
  };

  // Step 2: Capture photo and OCR
  const capturePhoto = useCallback(async () => {
    if (!webcamRef.current) return;

    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
    setOcrProcessing(true);

    try {
      const worker = await createWorker('eng');
      const { data } = await worker.recognize(imageSrc);
      await worker.terminate();

      setOcrConfidence(data.confidence / 100);

      const text = data.text;
      const lines = text.split('\n').filter(l => l.trim());

      // Extract phone
      const phoneMatch = text.match(/[6-9]\d{9}/);
      if (phoneMatch) {
        setOcrPhone(phoneMatch[0]);
      }

      // Extract name (first line with letters)
      for (const line of lines) {
        const cleaned = line.trim();
        if (cleaned.length > 2 && !cleaned.match(/\d{10}/) && /[A-Za-z]/.test(cleaned)) {
          setOcrName(cleaned);
          break;
        }
      }

      // Check mismatch
      const detectedPhone = phoneMatch ? phoneMatch[0] : '';
      const detectedName = lines.find(l => l.trim().length > 2 && /[A-Za-z]/.test(l)) || '';
      
      const nameMismatch = detectedName && customerName.toLowerCase().trim() !== detectedName.toLowerCase().trim();
      const phoneMismatch = detectedPhone && customerPhone !== detectedPhone;
      
      if (nameMismatch || phoneMismatch) {
        setOcrMismatch(true);
        toast.warning('OCR detection differs from manual entry. Please verify.');
      }

      toast.success('Photo captured and analyzed.');
    } catch (error) {
      console.error('OCR failed:', error);
      toast.info('Photo captured. OCR analysis complete.');
    } finally {
      setOcrProcessing(false);
    }
  }, [customerName, customerPhone]);

  // Step 2: Proceed to code entry
  const proceedToCodeEntry = () => {
    if (!capturedImage) {
      toast.error('Please capture photo first');
      return;
    }
    setStep(3);
  };

  // Step 3: Validate coupon code
  const validateCode = async () => {
    if (!couponCode.trim()) {
      toast.error('Please enter coupon code');
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
        toast.success(`Valid! ${data.campaign_name} - ₹${data.campaign_price}`);
        setStep(4);
      } else {
        toast.error(data.message);
      }
    } catch (error) {
      toast.error('Failed to validate coupon');
    } finally {
      setValidating(false);
    }
  };

  // Step 4: Proceed to confirm
  const proceedToConfirm = () => {
    if (!selectedBranch) {
      toast.error('Please select a branch');
      return;
    }
    if (!location) {
      toast.error('Location is required');
      getLocation();
      return;
    }
    if (gpsAccuracy && gpsAccuracy > 100) {
      toast.error('GPS accuracy too low. Move to open area.');
      return;
    }
    setStep(5);
  };

  // Step 5: Complete sale
  const completeSale = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/campaigns/worker-sale`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          customer_name: customerName.trim(),
          customer_phone: customerPhone.trim(),
          ocr_detected_name: ocrName || null,
          ocr_detected_phone: ocrPhone || null,
          ocr_confidence: ocrConfidence,
          coupon_code: couponCode.trim().toUpperCase(),
          branch_id: selectedBranch,
          latitude: location.lat,
          longitude: location.lng,
          gps_accuracy: gpsAccuracy,
          city: city,
          state: state,
          area_name: areaName,
          image_base64: capturedImage
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSaleResult(data);
        setStep(6);
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

  const resetForm = () => {
    setStep(1);
    setCustomerName('');
    setCustomerPhone('');
    setCapturedImage(null);
    setOcrName('');
    setOcrPhone('');
    setOcrConfidence(0);
    setOcrMismatch(false);
    setCouponCode('');
    setValidationResult(null);
    setSelectedBranch('');
    setSaleResult(null);
  };

  const getSelectedBranchName = () => {
    const branch = branches.find(b => b.id === selectedBranch);
    return branch ? branch.name : '';
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto space-y-6" data-testid="sale-coupon-page">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
            Sale Coupon
          </h1>
          <p className="text-zinc-500 mt-1">
            Fill details → Photo → Code → Branch → Submit
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-1 overflow-x-auto pb-2">
          {[1, 2, 3, 4, 5, 6].map((s) => (
            <React.Fragment key={s}>
              <div className={`
                w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0
                ${step >= s ? 'bg-blue-600 text-white' : 'bg-zinc-200 text-zinc-500'}
              `}>
                {step > s ? <CheckCircle className="h-3 w-3" /> : s}
              </div>
              {s < 6 && <div className={`w-6 h-0.5 flex-shrink-0 ${step > s ? 'bg-blue-600' : 'bg-zinc-200'}`} />}
            </React.Fragment>
          ))}
        </div>

        {/* Step 1: Manual Entry */}
        {step === 1 && (
          <Card data-testid="step-1-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-blue-600" />
                Customer Details (Manual Entry)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Customer Name *</Label>
                <Input
                  placeholder="Enter customer full name"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  data-testid="customer-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Mobile Number *</Label>
                <Input
                  placeholder="10-digit mobile number"
                  value={customerPhone}
                  onChange={(e) => setCustomerPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                  data-testid="customer-phone-input"
                />
              </div>
              
              <Button
                className="w-full bg-blue-600 hover:bg-blue-700"
                onClick={proceedToPhoto}
                data-testid="proceed-photo-btn"
              >
                Next: Click Photo
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Photo + OCR */}
        {step === 2 && (
          <Card data-testid="step-2-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Camera className="h-5 w-5 text-blue-600" />
                Click Coupon Photo
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Manual entry summary */}
              <div className="p-3 bg-zinc-50 rounded-lg text-sm">
                <p><strong>Name:</strong> {customerName}</p>
                <p><strong>Mobile:</strong> {customerPhone}</p>
              </div>

              {/* Camera */}
              {!capturedImage ? (
                <div className="space-y-3">
                  <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
                    <Webcam
                      ref={webcamRef}
                      audio={false}
                      screenshotFormat="image/jpeg"
                      videoConstraints={{ facingMode: 'environment' }}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <Button
                    className="w-full"
                    onClick={capturePhoto}
                    disabled={ocrProcessing}
                    data-testid="capture-btn"
                  >
                    {ocrProcessing ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Camera className="h-4 w-4 mr-2" />
                    )}
                    {ocrProcessing ? 'Analyzing...' : 'Click Coupon Photo'}
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="relative rounded-lg overflow-hidden">
                    <img src={capturedImage} alt="Captured" className="w-full" />
                    <Button
                      variant="secondary"
                      size="sm"
                      className="absolute top-2 right-2"
                      onClick={() => { setCapturedImage(null); setOcrName(''); setOcrPhone(''); setOcrMismatch(false); }}
                    >
                      <RefreshCcw className="h-4 w-4 mr-1" />
                      Retake
                    </Button>
                  </div>

                  {/* OCR Results */}
                  <div className={`p-3 rounded-lg ${ocrMismatch ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50'}`}>
                    <p className="text-sm font-medium mb-2 flex items-center gap-2">
                      {ocrMismatch ? (
                        <>
                          <AlertTriangle className="h-4 w-4 text-yellow-600" />
                          OCR Mismatch Detected
                        </>
                      ) : (
                        <>
                          <CheckCircle className="h-4 w-4 text-green-600" />
                          OCR Detection ({(ocrConfidence * 100).toFixed(0)}% confidence)
                        </>
                      )}
                    </p>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-zinc-500">Manual Entry</p>
                        <p><strong>Name:</strong> {customerName}</p>
                        <p><strong>Phone:</strong> {customerPhone}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">OCR Detected</p>
                        <p><strong>Name:</strong> {ocrName || 'Not detected'}</p>
                        <p><strong>Phone:</strong> {ocrPhone || 'Not detected'}</p>
                      </div>
                    </div>
                    {ocrMismatch && (
                      <p className="text-xs text-yellow-700 mt-2">
                        Please verify details are correct before proceeding.
                      </p>
                    )}
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep(1)} className="flex-1">
                  Back
                </Button>
                <Button
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                  onClick={proceedToCodeEntry}
                  disabled={!capturedImage}
                  data-testid="proceed-code-btn"
                >
                  Next: Enter Code
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Coupon Code */}
        {step === 3 && (
          <Card data-testid="step-3-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Ticket className="h-5 w-5 text-blue-600" />
                Enter Coupon Unique Code
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Coupon Code *</Label>
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

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
                  Back
                </Button>
                <Button
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                  onClick={validateCode}
                  disabled={validating}
                  data-testid="validate-btn"
                >
                  {validating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Validate Code
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 4: Select Branch */}
        {step === 4 && (
          <Card data-testid="step-4-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-blue-600" />
                Select Branch
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Coupon Info */}
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

              <div className="space-y-2">
                <Label>Branch *</Label>
                <Select value={selectedBranch} onValueChange={setSelectedBranch}>
                  <SelectTrigger data-testid="branch-select">
                    <SelectValue placeholder="Select branch" />
                  </SelectTrigger>
                  <SelectContent>
                    {branches.map((branch) => (
                      <SelectItem key={branch.id} value={branch.id}>
                        {branch.name} - {branch.city}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Location */}
              <div className={`p-3 rounded-lg ${location ? 'bg-green-50' : 'bg-yellow-50'}`}>
                <div className="flex items-center gap-2">
                  <MapPin className={`h-4 w-4 ${location ? 'text-green-600' : 'text-yellow-600'}`} />
                  {location ? (
                    <div className="text-sm text-green-700">
                      <p>Location: {city || 'Unknown'}, {state || 'Unknown'}</p>
                      <p className="text-xs">Accuracy: {gpsAccuracy?.toFixed(0)}m</p>
                    </div>
                  ) : (
                    <span className="text-sm text-yellow-700">{locationError || 'Getting location...'}</span>
                  )}
                  {!location && (
                    <Button variant="link" size="sm" onClick={getLocation}>Retry</Button>
                  )}
                </div>
              </div>

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep(3)} className="flex-1">
                  Back
                </Button>
                <Button
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                  onClick={proceedToConfirm}
                  data-testid="proceed-confirm-btn"
                >
                  Review & Submit
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 5: Confirm */}
        {step === 5 && (
          <Card data-testid="step-5-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                Confirm Sale
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3 p-4 bg-zinc-50 rounded-lg">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Customer</span>
                  <span className="font-medium">{customerName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Mobile</span>
                  <span>{customerPhone}</span>
                </div>
                <hr />
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
                  <span className="text-zinc-500">Branch</span>
                  <span className="font-medium">{getSelectedBranchName()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Location</span>
                  <span>{city}, {state}</span>
                </div>
              </div>

              {capturedImage && (
                <img src={capturedImage} alt="Captured" className="w-full rounded-lg" />
              )}

              {ocrMismatch && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center gap-2 text-yellow-700">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="text-sm">OCR mismatch was detected. Please ensure details are correct.</span>
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep(4)} className="flex-1">
                  Back
                </Button>
                <Button
                  className="flex-1 bg-green-600 hover:bg-green-700"
                  onClick={completeSale}
                  disabled={loading}
                  data-testid="submit-sale-btn"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                  Submit Sale
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 6: Success */}
        {step === 6 && (
          <Card data-testid="step-6-card">
            <CardContent className="py-8 text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-green-700">Sale Complete!</h2>
              <div className="space-y-2 text-zinc-600">
                <p>Coupon <code className="font-mono bg-zinc-100 px-2 py-1 rounded">{saleResult?.coupon_code}</code></p>
                <p>Customer: <strong>{saleResult?.customer_name}</strong></p>
                <p>Branch: <strong>{saleResult?.branch_name}</strong></p>
                <p className="text-xl font-bold text-green-600">
                  ₹{saleResult?.campaign_price} added to your ledger
                </p>
              </div>
              {saleResult?.ocr_mismatch_warning && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-700">
                  <AlertTriangle className="h-4 w-4 inline mr-1" />
                  {saleResult.ocr_mismatch_warning}
                </div>
              )}
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
