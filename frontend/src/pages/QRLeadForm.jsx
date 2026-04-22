import React, { useState } from 'react';
import { MapPin, CheckCircle, Loader2 } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const THEME_COLOR = '#ED1C24';

const VEHICLE_TYPES = ['< 160cc', '≥ 160cc'];

export default function QRLeadForm() {
  const [name, setName] = useState('');
  const [mobile, setMobile] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [vehicleType, setVehicleType] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!name.trim() || !mobile.trim() || !city.trim() || !state.trim() || !vehicleType) {
      setError('All fields are required');
      return;
    }
    const cleanMobile = mobile.replace(/\D/g, '');
    if (cleanMobile.length < 10) {
      setError('Please enter a valid 10-digit mobile number');
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/qr-leads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim(), mobile: cleanMobile, city: city.trim(), state: state.trim(), vehicle_type: vehicleType }),
      });
      const data = await res.json();
      if (res.ok) {
        setSubmitted(true);
      } else {
        setError(data.detail || 'Submission failed. Please try again.');
      }
    } catch {
      setError('Network error. Please check your connection.');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md text-center space-y-6">
          <div className="mx-auto w-20 h-20 rounded-full bg-green-100 flex items-center justify-center">
            <CheckCircle className="h-10 w-10 text-green-600" />
          </div>
          <h1 className="text-2xl font-bold text-zinc-900">Thank You!</h1>
          <p className="text-zinc-600">Your details have been submitted successfully.</p>
          <p className="text-sm text-zinc-400">You may close this page now.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col" data-testid="qr-lead-form-page">
      {/* Header */}
      <div className="bg-white border-b border-zinc-200 px-4 py-4">
        <div className="max-w-md mx-auto flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: THEME_COLOR }}>
            <MapPin className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight" style={{ color: THEME_COLOR }}>FieldFlow Pro</h1>
            <p className="text-xs text-zinc-500">Customer Registration</p>
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="flex-1 flex items-start justify-center p-4 pt-6">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-xl shadow-sm border border-zinc-200 p-6">
            <h2 className="text-lg font-semibold text-zinc-900 mb-1">Fill Your Details</h2>
            <p className="text-sm text-zinc-500 mb-6">Please fill in the form below to register.</p>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700" data-testid="form-error">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your full name"
                  className="w-full px-3 py-2.5 border border-zinc-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400"
                  data-testid="qr-lead-name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Mobile Number *</label>
                <input
                  type="tel"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                  placeholder="Enter 10-digit mobile number"
                  maxLength={10}
                  className="w-full px-3 py-2.5 border border-zinc-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400"
                  data-testid="qr-lead-mobile"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">City *</label>
                <input
                  type="text"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Enter your city"
                  className="w-full px-3 py-2.5 border border-zinc-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400"
                  data-testid="qr-lead-city"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">State *</label>
                <input
                  type="text"
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  placeholder="Enter your state"
                  className="w-full px-3 py-2.5 border border-zinc-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400"
                  data-testid="qr-lead-state"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Vehicle Type *</label>
                <div className="grid grid-cols-2 gap-3">
                  {VEHICLE_TYPES.map((vt) => (
                    <button
                      key={vt}
                      type="button"
                      onClick={() => setVehicleType(vt)}
                      className={`px-4 py-2.5 rounded-lg border text-sm font-medium transition-all ${
                        vehicleType === vt
                          ? 'border-red-500 bg-red-50 text-red-700'
                          : 'border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50'
                      }`}
                      data-testid={`vehicle-type-${vt.replace(/[^a-z0-9]/gi, '')}`}
                    >
                      {vt}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 rounded-lg text-white font-semibold text-sm transition-colors disabled:opacity-60"
                style={{ backgroundColor: THEME_COLOR }}
                data-testid="qr-lead-submit"
              >
                {submitting ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" /> Submitting...
                  </span>
                ) : (
                  'Submit'
                )}
              </button>
            </form>
          </div>

          <p className="text-center text-xs text-zinc-400 mt-4">Powered by FieldFlow Pro</p>
        </div>
      </div>
    </div>
  );
}
