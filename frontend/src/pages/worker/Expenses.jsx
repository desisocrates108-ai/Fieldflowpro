import React, { useState, useRef, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../../components/ui/dialog';
import Webcam from 'react-webcam';
import { 
  Plus, Receipt, Camera, MapPin, Loader2, CheckCircle, 
  XCircle, Clock, RefreshCcw, IndianRupee, ImageIcon
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const THEME_COLOR = '#ED1C24';

const EXPENSE_TYPES = [
  'Travel',
  'Food',
  'Equipment',
  'Communication',
  'Accommodation',
  'Other'
];

export default function ExpensesPage() {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    type: '',
    amount: '',
    description: ''
  });
  const [billPhoto, setBillPhoto] = useState(null);
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  
  const webcamRef = useRef(null);

  useEffect(() => {
    fetchExpenses();
    getLocation();
  }, []);

  const fetchExpenses = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/expenses`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setExpenses(data);
      }
    } catch (error) {
      toast.error('Failed to load expenses');
    } finally {
      setLoading(false);
    }
  };

  const getLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation not supported');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        });
        setLocationError(null);
      },
      () => setLocationError('Unable to get location'),
      { enableHighAccuracy: true }
    );
  };

  const capturePhoto = () => {
    if (!webcamRef.current) return;
    const imageSrc = webcamRef.current.getScreenshot();
    setBillPhoto(imageSrc);
    setShowCamera(false);
    toast.success('Photo captured');
  };

  const handleSubmit = async () => {
    // Validation
    if (!formData.type || !formData.amount) {
      toast.error('Please fill type and amount');
      return;
    }
    
    const amount = parseFloat(formData.amount);
    if (amount <= 0) {
      toast.error('Amount must be positive');
      return;
    }
    
    if (amount > 100 && !billPhoto) {
      toast.error('Bill photo is mandatory for expenses above ₹100');
      return;
    }
    
    if (!location) {
      toast.error('Location is required');
      getLocation();
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/expenses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          type: formData.type,
          amount: amount,
          description: formData.description || null,
          latitude: location.lat,
          longitude: location.lng,
          image_base64: billPhoto
        })
      });

      if (response.ok) {
        toast.success('Expense submitted successfully');
        setDialogOpen(false);
        resetForm();
        fetchExpenses();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to submit expense');
      }
    } catch (error) {
      toast.error('Failed to submit expense');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({ type: '', amount: '', description: '' });
    setBillPhoto(null);
    setShowCamera(false);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'APPROVED': return 'bg-green-100 text-green-800';
      case 'REJECTED': return 'bg-red-100 text-red-800';
      case 'PENDING': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'APPROVED': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'REJECTED': return <XCircle className="h-4 w-4 text-red-600" />;
      default: return <Clock className="h-4 w-4 text-yellow-600" />;
    }
  };

  // Stats
  const totalExpenses = expenses.reduce((acc, e) => e.status === 'APPROVED' ? acc + e.amount : acc, 0);
  const pendingCount = expenses.filter(e => e.status === 'PENDING').length;

  return (
    <Layout>
      <div className="space-y-6" data-testid="expenses-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              My Expenses
            </h1>
            <p className="text-zinc-500 mt-1">Submit and track your expense claims</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => { setLoading(true); fetchExpenses(); }}>
              <RefreshCcw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700" data-testid="add-expense-btn">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Expense
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle className="font-['Barlow_Condensed'] text-2xl">Submit Expense</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Expense Type</Label>
                      <Select
                        value={formData.type}
                        onValueChange={(v) => setFormData({ ...formData, type: v })}
                      >
                        <SelectTrigger data-testid="expense-type-select">
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          {EXPENSE_TYPES.map((type) => (
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Amount (₹)</Label>
                      <Input
                        type="number"
                        placeholder="0"
                        value={formData.amount}
                        onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                        data-testid="expense-amount-input"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Description (Optional)</Label>
                    <Textarea
                      placeholder="What was this expense for?"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={2}
                      data-testid="expense-description-input"
                    />
                  </div>

                  {/* Bill Photo */}
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <ImageIcon className="h-4 w-4" />
                      Bill Photo 
                      {parseFloat(formData.amount) > 100 && (
                        <span className="text-red-500 text-xs">(Required for ₹100+)</span>
                      )}
                    </Label>
                    
                    {showCamera ? (
                      <div className="space-y-2">
                        <div className="bg-black rounded-lg overflow-hidden aspect-video">
                          <Webcam
                            ref={webcamRef}
                            audio={false}
                            screenshotFormat="image/jpeg"
                            videoConstraints={{ facingMode: 'environment' }}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button onClick={capturePhoto} className="flex-1">
                            <Camera className="h-4 w-4 mr-2" />
                            Capture
                          </Button>
                          <Button variant="outline" onClick={() => setShowCamera(false)}>
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : billPhoto ? (
                      <div className="relative">
                        <img src={billPhoto} alt="Bill" className="w-full rounded-lg" />
                        <Button
                          variant="secondary"
                          size="sm"
                          className="absolute top-2 right-2"
                          onClick={() => setBillPhoto(null)}
                        >
                          <RefreshCcw className="h-4 w-4 mr-1" />
                          Retake
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="outline"
                        className="w-full h-24 border-dashed"
                        onClick={() => setShowCamera(true)}
                        data-testid="capture-bill-btn"
                      >
                        <Camera className="h-6 w-6 mr-2" />
                        Take Photo of Bill
                      </Button>
                    )}
                  </div>

                  {/* Location Status */}
                  <div className={`p-3 rounded-lg ${location ? 'bg-green-50' : 'bg-yellow-50'}`}>
                    <div className="flex items-center gap-2">
                      <MapPin className={`h-4 w-4 ${location ? 'text-green-600' : 'text-yellow-600'}`} />
                      {location ? (
                        <span className="text-sm text-green-700">Location captured</span>
                      ) : (
                        <>
                          <span className="text-sm text-yellow-700">{locationError || 'Getting location...'}</span>
                          <Button variant="link" size="sm" onClick={getLocation}>Retry</Button>
                        </>
                      )}
                    </div>
                  </div>

                  <Button
                    className="w-full bg-green-600 hover:bg-green-700"
                    onClick={handleSubmit}
                    disabled={submitting}
                    data-testid="submit-expense-btn"
                  >
                    {submitting ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <CheckCircle className="h-4 w-4 mr-2" />
                    )}
                    Submit Expense
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <IndianRupee className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Approved</p>
                  <p className="text-2xl font-bold">₹{totalExpenses.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <Clock className="h-5 w-5 text-yellow-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Pending</p>
                  <p className="text-2xl font-bold">{pendingCount}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Receipt className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Total Claims</p>
                  <p className="text-2xl font-bold">{expenses.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Expenses List */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Expenses</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : expenses.length === 0 ? (
              <div className="text-center py-8">
                <Receipt className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
                <p className="text-zinc-500">No expenses yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {expenses.map((expense) => (
                  <div
                    key={expense.id}
                    className="flex items-center justify-between p-4 bg-zinc-50 rounded-lg"
                  >
                    <div className="flex items-center gap-4">
                      {getStatusIcon(expense.status)}
                      <div>
                        <p className="font-medium">{expense.type}</p>
                        <p className="text-sm text-zinc-500">
                          {expense.description || 'No description'}
                        </p>
                        <p className="text-xs text-zinc-400">
                          {new Date(expense.created_at).toLocaleString()}
                        </p>
                        {expense.status === 'REJECTED' && expense.rejection_reason && (
                          <p className="text-xs text-red-600 mt-1 italic">
                            Rejection reason: {expense.rejection_reason}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold">₹{expense.amount}</p>
                      <Badge className={getStatusColor(expense.status)}>
                        {expense.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
