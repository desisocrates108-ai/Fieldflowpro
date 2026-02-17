import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { couponAPI, bookingAPI } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { InputOTP, InputOTPGroup, InputOTPSlot } from '../components/ui/input-otp';
import { MapPin, Ticket, Loader2, CheckCircle, Phone, Shield } from 'lucide-react';
import { toast } from 'sonner';

export default function RedeemCouponPage() {
  const [searchParams] = useSearchParams();
  const initialCode = searchParams.get('code') || '';
  
  const [step, setStep] = useState(1); // 1: Enter code, 2: Enter OTP, 3: Create booking, 4: Success
  const [couponCode, setCouponCode] = useState(initialCode);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [mockOtp, setMockOtp] = useState('');
  const [couponId, setCouponId] = useState('');
  const [bookingData, setBookingData] = useState({
    service_type: '',
    address: ''
  });
  const [loading, setLoading] = useState(false);
  const [booking, setBooking] = useState(null);

  const handleRequestOTP = async (e) => {
    e.preventDefault();
    
    if (!couponCode || !phone) {
      toast.error('Please enter coupon code and phone number');
      return;
    }

    setLoading(true);
    try {
      const response = await couponAPI.requestOTP(couponCode, phone);
      setMockOtp(response.data.mock_otp); // For MVP demo
      toast.success('OTP sent to your phone');
      setStep(2);
    } catch (error) {
      console.error('Failed to request OTP:', error);
      toast.error(error.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (otp.length !== 6) {
      toast.error('Please enter complete OTP');
      return;
    }

    setLoading(true);
    try {
      const response = await couponAPI.verifyOTP(couponCode, phone, otp);
      setCouponId(response.data.coupon_id);
      toast.success('Coupon redeemed successfully!');
      setStep(3);
    } catch (error) {
      console.error('Failed to verify OTP:', error);
      toast.error(error.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBooking = async (e) => {
    e.preventDefault();
    
    if (!bookingData.service_type || !bookingData.address) {
      toast.error('Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const response = await bookingAPI.create({
        coupon_id: couponId,
        service_type: bookingData.service_type,
        address: bookingData.address
      });
      setBooking(response.data);
      toast.success('Booking created successfully!');
      setStep(4);
    } catch (error) {
      console.error('Failed to create booking:', error);
      toast.error(error.response?.data?.detail || 'Failed to create booking');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-xl bg-blue-600 flex items-center justify-center mx-auto mb-4">
            <MapPin className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold font-['Barlow_Condensed']">FieldFlow Pro</h1>
          <p className="text-zinc-500">Redeem your coupon</p>
        </div>

        {/* Step 1: Enter Coupon Code */}
        {step === 1 && (
          <Card data-testid="redeem-step-1">
            <CardHeader>
              <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                <Ticket className="h-5 w-5" />
                Enter Coupon Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRequestOTP} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="couponCode">Coupon Code</Label>
                  <Input
                    id="couponCode"
                    placeholder="SVL-XXX-XXX-XXXXXX"
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                    className="font-mono text-center text-lg tracking-wider"
                    data-testid="coupon-code-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="Enter your phone number"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    data-testid="phone-input"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full" 
                  disabled={loading}
                  data-testid="request-otp-btn"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Sending OTP...
                    </>
                  ) : (
                    <>
                      <Phone className="h-4 w-4 mr-2" />
                      Get OTP
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Enter OTP */}
        {step === 2 && (
          <Card data-testid="redeem-step-2">
            <CardHeader>
              <CardTitle className="font-['Barlow_Condensed'] flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Verify OTP
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <p className="text-sm text-zinc-600 text-center">
                Enter the 6-digit code sent to <span className="font-medium">{phone}</span>
              </p>
              
              {/* Demo OTP Display */}
              {mockOtp && (
                <div className="p-3 bg-blue-50 rounded-lg text-center">
                  <p className="text-xs text-blue-600 mb-1">Demo OTP (for testing)</p>
                  <p className="text-2xl font-bold font-mono text-blue-700">{mockOtp}</p>
                </div>
              )}
              
              <div className="flex justify-center">
                <InputOTP
                  maxLength={6}
                  value={otp}
                  onChange={setOtp}
                  data-testid="otp-input"
                >
                  <InputOTPGroup>
                    <InputOTPSlot index={0} />
                    <InputOTPSlot index={1} />
                    <InputOTPSlot index={2} />
                    <InputOTPSlot index={3} />
                    <InputOTPSlot index={4} />
                    <InputOTPSlot index={5} />
                  </InputOTPGroup>
                </InputOTP>
              </div>
              
              <Button 
                onClick={handleVerifyOTP}
                className="w-full" 
                disabled={loading || otp.length !== 6}
                data-testid="verify-otp-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  'Verify & Redeem'
                )}
              </Button>
              
              <Button
                variant="ghost"
                className="w-full"
                onClick={() => setStep(1)}
              >
                Back
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Create Booking */}
        {step === 3 && (
          <Card data-testid="redeem-step-3">
            <CardHeader>
              <CardTitle className="font-['Barlow_Condensed']">
                <CheckCircle className="h-5 w-5 text-green-600 inline mr-2" />
                Create Booking
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-3 bg-green-50 rounded-lg mb-6 text-center">
                <p className="text-green-700 font-medium">Coupon Redeemed Successfully!</p>
              </div>
              
              <form onSubmit={handleCreateBooking} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="service_type">Service Type</Label>
                  <Input
                    id="service_type"
                    placeholder="e.g., AC Repair, Plumbing"
                    value={bookingData.service_type}
                    onChange={(e) => setBookingData({ ...bookingData, service_type: e.target.value })}
                    data-testid="service-type-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address">Service Address</Label>
                  <Input
                    id="address"
                    placeholder="Enter your address"
                    value={bookingData.address}
                    onChange={(e) => setBookingData({ ...bookingData, address: e.target.value })}
                    data-testid="address-input"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full" 
                  disabled={loading}
                  data-testid="create-booking-btn"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Booking'
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Step 4: Success */}
        {step === 4 && booking && (
          <Card data-testid="redeem-step-4">
            <CardContent className="py-8 text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold font-['Barlow_Condensed'] mb-2">Booking Confirmed!</h2>
              <p className="text-zinc-500 mb-6">Your service request has been submitted</p>
              
              <div className="bg-zinc-50 rounded-lg p-4 text-left space-y-2">
                <p><strong>Service:</strong> {booking.service_type}</p>
                <p><strong>Address:</strong> {booking.address}</p>
                <p><strong>Status:</strong> <span className="text-yellow-600">Pending Assignment</span></p>
              </div>
              
              <p className="text-sm text-zinc-500 mt-6">
                You will receive updates when your service is assigned and dispatched.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
