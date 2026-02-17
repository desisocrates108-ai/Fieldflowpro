import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../../components/Layout';
import { couponAPI, uploadAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { 
  Ticket, 
  MapPin, 
  Camera, 
  Loader2, 
  CheckCircle,
  User,
  Phone,
  X
} from 'lucide-react';
import { getCurrentPosition } from '../../lib/utils';
import { toast } from 'sonner';

export default function IssueCouponPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_phone: '',
    area_id: ''
  });
  const [location, setLocation] = useState(null);
  const [photo, setPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [gettingLocation, setGettingLocation] = useState(false);
  const [generatedCoupon, setGeneratedCoupon] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const getLocation = async () => {
    setGettingLocation(true);
    try {
      const pos = await getCurrentPosition();
      setLocation(pos);
      toast.success('Location captured');
    } catch (error) {
      toast.error('Failed to get location');
    } finally {
      setGettingLocation(false);
    }
  };

  const handlePhotoChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setPhoto(file);
      const reader = new FileReader();
      reader.onload = (e) => setPhotoPreview(e.target?.result);
      reader.readAsDataURL(file);
    }
  };

  const removePhoto = () => {
    setPhoto(null);
    setPhotoPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.customer_name || !formData.customer_phone) {
      toast.error('Please fill in customer name and phone');
      return;
    }

    if (!location) {
      toast.error('Please capture your location first');
      return;
    }

    setLoading(true);

    try {
      let photo_url = null;

      // Upload photo if present
      if (photo) {
        const uploadRes = await uploadAPI.upload(photo);
        photo_url = uploadRes.data.url;
      }

      // Create coupon
      const response = await couponAPI.create({
        customer_name: formData.customer_name,
        customer_phone: formData.customer_phone,
        area_id: formData.area_id || 'DEF',
        latitude: location.latitude,
        longitude: location.longitude,
        photo_url
      });

      setGeneratedCoupon(response.data);
      toast.success('Coupon created successfully!');
    } catch (error) {
      console.error('Failed to create coupon:', error);
      toast.error(error.response?.data?.detail || 'Failed to create coupon');
    } finally {
      setLoading(false);
    }
  };

  if (generatedCoupon) {
    return (
      <Layout>
        <div className="max-w-md mx-auto space-y-6" data-testid="coupon-success">
          <div className="text-center py-8">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-10 w-10 text-green-600" />
            </div>
            <h1 className="text-2xl font-bold font-['Barlow_Condensed']">Coupon Created!</h1>
            <p className="text-zinc-500 mt-2">Share this code with the customer</p>
          </div>

          {/* Coupon Card */}
          <Card className="coupon-card border-2 border-blue-200">
            <CardContent className="p-6 text-center">
              <p className="text-sm text-zinc-500 mb-2">Coupon Code</p>
              <p className="text-3xl font-bold font-mono tracking-wider text-blue-600" data-testid="coupon-code">
                {generatedCoupon.code}
              </p>
              <div className="mt-4 pt-4 border-t border-dashed">
                <p className="text-sm"><strong>Customer:</strong> {generatedCoupon.customer_name}</p>
                <p className="text-sm text-zinc-500">{generatedCoupon.customer_phone}</p>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button 
              variant="outline" 
              className="flex-1"
              onClick={() => {
                setGeneratedCoupon(null);
                setFormData({ customer_name: '', customer_phone: '', area_id: '' });
                setPhoto(null);
                setPhotoPreview(null);
                setLocation(null);
              }}
            >
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
            Create a new coupon for a customer
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Customer Info */}
          <Card>
            <CardHeader>
              <CardTitle className="font-['Barlow_Condensed'] text-lg flex items-center gap-2">
                <User className="h-5 w-5" />
                Customer Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="customer_name">Customer Name *</Label>
                <Input
                  id="customer_name"
                  name="customer_name"
                  placeholder="John Doe"
                  value={formData.customer_name}
                  onChange={handleChange}
                  data-testid="customer-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="customer_phone">Phone Number *</Label>
                <Input
                  id="customer_phone"
                  name="customer_phone"
                  type="tel"
                  placeholder="+1 234 567 8900"
                  value={formData.customer_phone}
                  onChange={handleChange}
                  data-testid="customer-phone-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="area_id">Area ID (Optional)</Label>
                <Input
                  id="area_id"
                  name="area_id"
                  placeholder="e.g., NORTH, SOUTH"
                  value={formData.area_id}
                  onChange={handleChange}
                  data-testid="area-id-input"
                />
              </div>
            </CardContent>
          </Card>

          {/* Location */}
          <Card>
            <CardHeader>
              <CardTitle className="font-['Barlow_Condensed'] text-lg flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Location
              </CardTitle>
            </CardHeader>
            <CardContent>
              {location ? (
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="text-sm font-medium text-green-700">Location Captured</p>
                      <p className="text-xs text-green-600 font-mono">
                        {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
                      </p>
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={getLocation}
                  >
                    Update
                  </Button>
                </div>
              ) : (
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  onClick={getLocation}
                  disabled={gettingLocation}
                  data-testid="capture-location-btn"
                >
                  {gettingLocation ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Getting Location...
                    </>
                  ) : (
                    <>
                      <MapPin className="h-4 w-4 mr-2" />
                      Capture Location
                    </>
                  )}
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Photo */}
          <Card>
            <CardHeader>
              <CardTitle className="font-['Barlow_Condensed'] text-lg flex items-center gap-2">
                <Camera className="h-5 w-5" />
                Photo (Optional)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {photoPreview ? (
                <div className="relative">
                  <img 
                    src={photoPreview} 
                    alt="Preview" 
                    className="w-full h-48 object-cover rounded-lg"
                  />
                  <button
                    type="button"
                    onClick={removePhoto}
                    className="absolute top-2 right-2 p-1 bg-black/50 rounded-full text-white hover:bg-black/70"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    capture="environment"
                    onChange={handlePhotoChange}
                    className="hidden"
                    id="photo-input"
                  />
                  <label
                    htmlFor="photo-input"
                    className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-zinc-300 rounded-lg cursor-pointer hover:bg-zinc-50"
                  >
                    <Camera className="h-8 w-8 text-zinc-400 mb-2" />
                    <span className="text-sm text-zinc-500">Tap to capture or upload photo</span>
                  </label>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Submit */}
          <Button 
            type="submit" 
            className="w-full h-12" 
            disabled={loading}
            data-testid="create-coupon-btn"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating Coupon...
              </>
            ) : (
              <>
                <Ticket className="h-4 w-4 mr-2" />
                Create Coupon
              </>
            )}
          </Button>
        </form>
      </div>
    </Layout>
  );
}
