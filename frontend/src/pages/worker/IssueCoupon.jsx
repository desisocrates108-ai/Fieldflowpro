import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createWorker } from 'tesseract.js';
import Layout from '../../components/Layout';
import { uploadAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Progress } from '../../components/ui/progress';
import { 
  Camera, 
  Loader2, 
  CheckCircle,
  MapPin,
  AlertCircle,
  RotateCcw,
  Send
} from 'lucide-react';
import { getCurrentPosition } from '../../lib/utils';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function IssueCouponPage() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  
  const [step, setStep] = useState('ready'); // ready, capturing, processing, review, success
  const [cameraActive, setCameraActive] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [location, setLocation] = useState(null);
  const [extractedData, setExtractedData] = useState({ name: '', mobile: '', confidence: 0 });
  const [ocrProgress, setOcrProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [generatedCoupon, setGeneratedCoupon] = useState(null);

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });
      
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
      setStep('capturing');
      
      // Get location in parallel
      try {
        const pos = await getCurrentPosition();
        setLocation(pos);
      } catch (e) {
        toast.error('Could not get GPS location');
      }
    } catch (error) {
      console.error('Camera error:', error);
      toast.error('Could not access camera. Please allow camera permissions.');
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  // Capture photo
  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    setCapturedImage(imageData);
    stopCamera();
    setStep('processing');
    
    // Run OCR
    runOCR(imageData);
  };

  // Run OCR using Tesseract.js
  const runOCR = async (imageData) => {
    setOcrProgress(0);
    
    try {
      const worker = await createWorker('eng', 1, {
        logger: progress => {
          if (progress.status === 'recognizing text') {
            setOcrProgress(Math.round(progress.progress * 100));
          }
        }
      });
      
      const { data } = await worker.recognize(imageData);
      await worker.terminate();
      
      // Extract name and mobile from OCR result
      const extracted = parseOCRResult(data.text);
      setExtractedData({
        name: extracted.name,
        mobile: extracted.mobile,
        confidence: data.confidence / 100
      });
      
      setStep('review');
      
      if (!extracted.name || !extracted.mobile) {
        toast.warning('Could not fully extract data. Please verify and correct if needed.');
      }
    } catch (error) {
      console.error('OCR error:', error);
      toast.error('Failed to process image. Please try again.');
      setStep('ready');
    }
  };

  // Parse OCR result to extract name and mobile
  const parseOCRResult = (text) => {
    const lines = text.split('\n').map(line => line.trim()).filter(Boolean);
    
    let name = '';
    let mobile = '';
    
    // Find mobile number (10+ digits)
    const mobileRegex = /[\d\s-]{10,}/g;
    for (const line of lines) {
      const matches = line.match(mobileRegex);
      if (matches) {
        // Clean and get first valid mobile
        for (const match of matches) {
          const cleaned = match.replace(/[\s-]/g, '');
          if (cleaned.length >= 10) {
            mobile = cleaned.slice(-10); // Take last 10 digits
            break;
          }
        }
        if (mobile) break;
      }
    }
    
    // Find name (assume it's a line with mostly letters, not the mobile line)
    for (const line of lines) {
      // Skip if line contains too many numbers
      const numbers = (line.match(/\d/g) || []).length;
      const letters = (line.match(/[a-zA-Z]/g) || []).length;
      
      if (letters > numbers && letters >= 3 && !line.includes(mobile)) {
        // Clean the name
        name = line.replace(/[^a-zA-Z\s.]/g, '').trim();
        if (name.length >= 2) break;
      }
    }
    
    return { name, mobile };
  };

  // Submit coupon
  const submitCoupon = async () => {
    if (!extractedData.name || !extractedData.mobile) {
      toast.error('Name and mobile number are required');
      return;
    }
    
    if (!location) {
      toast.error('GPS location is required');
      return;
    }
    
    setLoading(true);
    
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${BACKEND_URL}/api/coupons/issue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          image_base64: capturedImage,
          extracted_name: extractedData.name,
          extracted_mobile: extractedData.mobile,
          location: {
            lat: location.latitude,
            lng: location.longitude
          },
          ocr_confidence: extractedData.confidence
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to issue coupon');
      }
      
      setGeneratedCoupon(data);
      setStep('success');
      toast.success('Coupon issued successfully!');
    } catch (error) {
      console.error('Submit error:', error);
      toast.error(error.message || 'Failed to issue coupon');
    } finally {
      setLoading(false);
    }
  };

  // Reset flow
  const resetFlow = () => {
    setCapturedImage(null);
    setExtractedData({ name: '', mobile: '', confidence: 0 });
    setGeneratedCoupon(null);
    setStep('ready');
    setOcrProgress(0);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => stopCamera();
  }, []);

  // Success Screen
  if (step === 'success' && generatedCoupon) {
    return (
      <Layout>
        <div className="max-w-md mx-auto space-y-6" data-testid="coupon-success">
          <div className="text-center py-8">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-10 w-10 text-green-600" />
            </div>
            <h1 className="text-2xl font-bold font-['Barlow_Condensed']">Coupon Issued!</h1>
            <p className="text-zinc-500 mt-2">Pending CRE verification</p>
          </div>

          <Card className="coupon-card border-2 border-blue-200">
            <CardContent className="p-6 text-center">
              <p className="text-sm text-zinc-500 mb-2">Coupon Code</p>
              <p className="text-3xl font-bold font-mono tracking-wider text-blue-600" data-testid="coupon-code">
                {generatedCoupon.code}
              </p>
              <div className="mt-4 pt-4 border-t border-dashed">
                <p className="text-sm"><strong>Customer:</strong> {generatedCoupon.customer_name}</p>
                <p className="text-xs text-yellow-600 mt-2">Status: {generatedCoupon.status}</p>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button variant="outline" className="flex-1" onClick={resetFlow}>
              <Camera className="h-4 w-4 mr-2" />
              Issue Another
            </Button>
            <Button className="flex-1" onClick={() => navigate('/worker/my-coupons')}>
              View All Coupons
            </Button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-md mx-auto space-y-6" data-testid="issue-coupon-page">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
            Issue Coupon
          </h1>
          <p className="text-zinc-500 mt-1">
            Capture photo to extract customer details
          </p>
        </div>

        {/* Ready State - Single Button */}
        {step === 'ready' && (
          <Card className="border-2 border-dashed border-blue-300 bg-blue-50/50">
            <CardContent className="py-16 flex flex-col items-center justify-center">
              <div className="w-24 h-24 rounded-full bg-blue-600 flex items-center justify-center mb-6 shadow-lg">
                <Camera className="h-12 w-12 text-white" />
              </div>
              <Button 
                size="lg"
                className="h-14 px-8 text-lg"
                onClick={startCamera}
                data-testid="click-photo-btn"
              >
                <Camera className="h-5 w-5 mr-2" />
                Click Photo
              </Button>
              <p className="text-sm text-zinc-500 mt-4 text-center">
                Take a photo of the coupon form to auto-extract<br />customer name and mobile number
              </p>
            </CardContent>
          </Card>
        )}

        {/* Camera View */}
        {step === 'capturing' && (
          <Card>
            <CardContent className="p-0 relative">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full rounded-lg"
              />
              <canvas ref={canvasRef} className="hidden" />
              
              {/* Camera overlay */}
              <div className="absolute inset-0 pointer-events-none">
                <div className="absolute inset-4 border-2 border-white/50 rounded-lg" />
              </div>
              
              {/* Location indicator */}
              {location && (
                <div className="absolute top-4 left-4 bg-green-500 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  GPS Ready
                </div>
              )}
              
              {/* Capture button */}
              <div className="absolute bottom-4 left-0 right-0 flex justify-center">
                <button
                  onClick={capturePhoto}
                  className="w-16 h-16 rounded-full bg-white border-4 border-blue-600 flex items-center justify-center shadow-lg hover:scale-105 transition-transform"
                  data-testid="capture-btn"
                >
                  <div className="w-12 h-12 rounded-full bg-blue-600" />
                </button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Processing State */}
        {step === 'processing' && (
          <Card>
            <CardContent className="py-12 flex flex-col items-center justify-center">
              <div className="w-20 h-20 rounded-full bg-blue-100 flex items-center justify-center mb-6">
                <Loader2 className="h-10 w-10 text-blue-600 animate-spin" />
              </div>
              <h3 className="text-lg font-semibold mb-4">Processing Image...</h3>
              <div className="w-full max-w-xs">
                <Progress value={ocrProgress} className="h-2" />
                <p className="text-sm text-zinc-500 text-center mt-2">
                  Extracting text: {ocrProgress}%
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Review State */}
        {step === 'review' && (
          <>
            {/* Preview Image */}
            {capturedImage && (
              <Card>
                <CardContent className="p-2">
                  <img 
                    src={capturedImage} 
                    alt="Captured" 
                    className="w-full rounded-lg"
                  />
                </CardContent>
              </Card>
            )}

            {/* Extracted Data */}
            <Card>
              <CardHeader>
                <CardTitle className="font-['Barlow_Condensed'] text-lg flex items-center gap-2">
                  Extracted Details
                  <span className="text-xs font-normal text-zinc-500">
                    ({Math.round(extractedData.confidence * 100)}% confidence)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-zinc-700">Customer Name</label>
                  <input
                    type="text"
                    value={extractedData.name}
                    onChange={(e) => setExtractedData({ ...extractedData, name: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Enter customer name"
                    data-testid="extracted-name-input"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-zinc-700">Mobile Number</label>
                  <input
                    type="tel"
                    value={extractedData.mobile}
                    onChange={(e) => setExtractedData({ ...extractedData, mobile: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="Enter mobile number"
                    data-testid="extracted-mobile-input"
                  />
                </div>
                
                {/* Location */}
                <div className="flex items-center gap-2 p-3 bg-zinc-50 rounded-lg">
                  <MapPin className={`h-5 w-5 ${location ? 'text-green-600' : 'text-red-500'}`} />
                  <div>
                    <p className="text-sm font-medium">
                      {location ? 'Location Captured' : 'Location Not Available'}
                    </p>
                    {location && (
                      <p className="text-xs text-zinc-500">
                        {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
                      </p>
                    )}
                  </div>
                </div>

                {/* Warning if low confidence */}
                {extractedData.confidence < 0.7 && (
                  <div className="flex items-start gap-2 p-3 bg-yellow-50 rounded-lg">
                    <AlertCircle className="h-5 w-5 text-yellow-600 shrink-0 mt-0.5" />
                    <p className="text-sm text-yellow-800">
                      Low OCR confidence. Please verify the extracted data is correct.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex gap-3">
              <Button variant="outline" onClick={resetFlow} className="flex-1">
                <RotateCcw className="h-4 w-4 mr-2" />
                Retake
              </Button>
              <Button 
                onClick={submitCoupon} 
                disabled={loading || !extractedData.name || !extractedData.mobile || !location}
                className="flex-1"
                data-testid="submit-coupon-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Issuing...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Issue Coupon
                  </>
                )}
              </Button>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
