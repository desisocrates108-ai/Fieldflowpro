import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { 
  QrCode, Loader2, CheckCircle, XCircle, RefreshCcw,
  CreditCard, Smartphone, IndianRupee, Clock
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const THEME_COLOR = '#ED1C24';

/**
 * PaymentQR Component
 * Displays a QR code for UPI payment and handles payment verification
 * 
 * Props:
 * - ticketId: string - The ticket/coupon ID
 * - amount: number - Amount in INR
 * - customerName: string
 * - customerPhone: string
 * - onPaymentSuccess: (paymentData) => void
 * - onPaymentFailed: (error) => void
 * - onCancel: () => void
 */
export default function PaymentQR({
  ticketId,
  amount,
  customerName,
  customerPhone,
  customerEmail,
  onPaymentSuccess,
  onPaymentFailed,
  onCancel
}) {
  const [loading, setLoading] = useState(true);
  const [paymentOrder, setPaymentOrder] = useState(null);
  const [paymentStatus, setPaymentStatus] = useState('pending'); // pending, paid, failed
  const [error, setError] = useState(null);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [autoCheckEnabled, setAutoCheckEnabled] = useState(true);

  // Create payment order on mount
  useEffect(() => {
    createPaymentOrder();
  }, []);

  // Auto-check payment status every 5 seconds
  useEffect(() => {
    if (!paymentOrder || paymentStatus !== 'pending' || !autoCheckEnabled) return;

    const interval = setInterval(() => {
      checkPaymentStatus();
    }, 5000);

    return () => clearInterval(interval);
  }, [paymentOrder, paymentStatus, autoCheckEnabled]);

  const createPaymentOrder = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/payments/create-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ticket_id: ticketId,
          amount: amount,
          customer_name: customerName,
          customer_phone: customerPhone,
          customer_email: customerEmail || null,
          description: `Payment for ticket ${ticketId}`
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to create payment order');
      }

      const data = await response.json();
      setPaymentOrder(data);
      toast.success('QR Code generated. Scan to pay.');
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
      if (onPaymentFailed) onPaymentFailed(err);
    } finally {
      setLoading(false);
    }
  };

  const checkPaymentStatus = useCallback(async () => {
    if (!paymentOrder || checkingStatus) return;

    setCheckingStatus(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${API_URL}/api/payments/status/${paymentOrder.order_id}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (response.ok) {
        const data = await response.json();
        
        if (data.status === 'paid') {
          setPaymentStatus('paid');
          setAutoCheckEnabled(false);
          toast.success('Payment received successfully!');
          if (onPaymentSuccess) onPaymentSuccess(data);
        } else if (data.status === 'failed') {
          setPaymentStatus('failed');
          setAutoCheckEnabled(false);
          toast.error('Payment failed');
          if (onPaymentFailed) onPaymentFailed({ message: 'Payment failed' });
        }
      }
    } catch (err) {
      console.error('Error checking payment status:', err);
    } finally {
      setCheckingStatus(false);
    }
  }, [paymentOrder, checkingStatus, onPaymentSuccess, onPaymentFailed]);

  const handleManualCheck = () => {
    checkPaymentStatus();
  };

  const handleRetry = () => {
    setPaymentStatus('pending');
    setError(null);
    setAutoCheckEnabled(true);
    createPaymentOrder();
  };

  if (loading) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Loader2 className="h-12 w-12 animate-spin mb-4" style={{ color: THEME_COLOR }} />
          <p className="text-zinc-600">Generating Payment QR Code...</p>
        </CardContent>
      </Card>
    );
  }

  if (error && !paymentOrder) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <XCircle className="h-12 w-12 text-red-500 mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onCancel}>Cancel</Button>
            <Button onClick={handleRetry} style={{ backgroundColor: THEME_COLOR }}>
              <RefreshCcw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (paymentStatus === 'paid') {
    return (
      <Card className="w-full max-w-md mx-auto border-green-500">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mb-4">
            <CheckCircle className="h-12 w-12 text-green-600" />
          </div>
          <h3 className="text-xl font-bold text-green-600 mb-2">Payment Successful!</h3>
          <p className="text-zinc-600 mb-4">Amount: ₹{amount}</p>
          <Badge className="bg-green-100 text-green-800">
            Transaction Complete
          </Badge>
        </CardContent>
      </Card>
    );
  }

  if (paymentStatus === 'failed') {
    return (
      <Card className="w-full max-w-md mx-auto border-red-500">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center mb-4">
            <XCircle className="h-12 w-12 text-red-600" />
          </div>
          <h3 className="text-xl font-bold text-red-600 mb-2">Payment Failed</h3>
          <p className="text-zinc-600 mb-4">Please try again</p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onCancel}>Cancel</Button>
            <Button onClick={handleRetry} style={{ backgroundColor: THEME_COLOR }}>
              <RefreshCcw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto" data-testid="payment-qr-card">
      <CardHeader className="text-center pb-2">
        <CardTitle className="flex items-center justify-center gap-2">
          <QrCode className="h-5 w-5" style={{ color: THEME_COLOR }} />
          Scan & Pay
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Amount Display */}
        <div className="text-center p-4 rounded-lg" style={{ backgroundColor: `${THEME_COLOR}10` }}>
          <p className="text-sm text-zinc-500 mb-1">Amount to Pay</p>
          <p className="text-4xl font-bold" style={{ color: THEME_COLOR }}>
            ₹{amount}
          </p>
        </div>

        {/* QR Code */}
        {paymentOrder?.qr_code_base64 && (
          <div className="flex flex-col items-center">
            <div className="p-4 bg-white rounded-lg border-2 border-zinc-200">
              <img
                src={`data:image/png;base64,${paymentOrder.qr_code_base64}`}
                alt="Payment QR Code"
                className="w-48 h-48"
                data-testid="payment-qr-image"
              />
            </div>
            <p className="text-xs text-zinc-500 mt-2">
              Scan with any UPI app (GPay, PhonePe, Paytm, etc.)
            </p>
          </div>
        )}

        {/* Payment Info */}
        <div className="bg-zinc-50 rounded-lg p-3 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-zinc-500">Customer</span>
            <span className="font-medium">{customerName}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-zinc-500">Phone</span>
            <span className="font-medium">{customerPhone}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-zinc-500">Order ID</span>
            <span className="font-mono text-xs">{paymentOrder?.order_id?.slice(0, 8)}...</span>
          </div>
        </div>

        {/* Auto-check Status */}
        <Alert className="border-blue-200 bg-blue-50">
          <Clock className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-700 text-sm">
            {autoCheckEnabled ? (
              <>
                <span className="flex items-center gap-2">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Waiting for payment... Auto-checking every 5 seconds
                </span>
              </>
            ) : (
              'Auto-check paused'
            )}
          </AlertDescription>
        </Alert>

        {/* Manual Check Button */}
        <Button
          variant="outline"
          className="w-full"
          onClick={handleManualCheck}
          disabled={checkingStatus}
        >
          {checkingStatus ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <RefreshCcw className="h-4 w-4 mr-2" />
          )}
          Check Payment Status
        </Button>

        {/* Cancel Button */}
        <Button
          variant="ghost"
          className="w-full text-zinc-500"
          onClick={onCancel}
        >
          Cancel Payment
        </Button>

        {/* UPI Apps */}
        <div className="flex items-center justify-center gap-2 pt-2 border-t">
          <Smartphone className="h-4 w-4 text-zinc-400" />
          <span className="text-xs text-zinc-400">
            GPay • PhonePe • Paytm • BHIM • Any UPI
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
