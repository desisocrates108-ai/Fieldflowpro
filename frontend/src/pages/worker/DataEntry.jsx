import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Loader2, ClipboardList, Plus, RefreshCcw } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const THEME_COLOR = '#ED1C24';

export default function WorkerDataEntry() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  
  // Form state
  const [customerName, setCustomerName] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [city, setCity] = useState('');
  const [notes, setNotes] = useState('');

  const fetchEntries = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API_URL}/api/worker/data-entry/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setEntries(data.entries || []);
      }
    } catch {
      toast.error('Failed to load entries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchEntries(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!customerName.trim() || !mobileNumber.trim() || !city.trim()) {
      toast.error('Please fill Customer Name, Mobile Number, and City');
      return;
    }
    
    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API_URL}/api/worker/data-entry`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          customer_name: customerName.trim(),
          mobile_number: mobileNumber.trim(),
          city: city.trim(),
          notes: notes.trim(),
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success('Entry saved successfully');
        setEntries(prev => [data.entry, ...prev]);
        setCustomerName('');
        setMobileNumber('');
        setCity('');
        setNotes('');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to save entry');
      }
    } catch {
      toast.error('Failed to save entry');
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (d) => {
    if (!d) return '-';
    return new Date(d).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <Layout>
      <div className="space-y-5" data-testid="worker-data-entry-page">
        <h1 className="text-2xl font-bold text-zinc-900 flex items-center gap-2">
          <ClipboardList className="h-6 w-6" style={{ color: THEME_COLOR }} />
          Data Entry
        </h1>

        {/* Form */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Add Customer Details</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="customerName">Customer Name *</Label>
                  <Input
                    id="customerName"
                    placeholder="Enter customer name"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    data-testid="data-entry-name"
                  />
                </div>
                <div>
                  <Label htmlFor="mobileNumber">Mobile Number *</Label>
                  <Input
                    id="mobileNumber"
                    placeholder="Enter mobile number"
                    value={mobileNumber}
                    onChange={(e) => setMobileNumber(e.target.value)}
                    data-testid="data-entry-mobile"
                  />
                </div>
                <div>
                  <Label htmlFor="city">City *</Label>
                  <Input
                    id="city"
                    placeholder="Enter city"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    data-testid="data-entry-city"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="notes">Notes (optional)</Label>
                <Textarea
                  id="notes"
                  placeholder="Any additional notes..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  data-testid="data-entry-notes"
                />
              </div>
              <Button 
                type="submit" 
                disabled={submitting}
                style={{ backgroundColor: THEME_COLOR }}
                data-testid="data-entry-submit"
              >
                {submitting ? (
                  <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Saving...</>
                ) : (
                  <><Plus className="h-4 w-4 mr-2" /> Submit Entry</>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Records Table */}
        <Card>
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-base">My Entries ({entries.length})</CardTitle>
            <Button variant="ghost" size="sm" onClick={fetchEntries}>
              <RefreshCcw className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-zinc-50">
                    <TableHead>Customer Name</TableHead>
                    <TableHead>Mobile Number</TableHead>
                    <TableHead>City</TableHead>
                    <TableHead>Notes</TableHead>
                    <TableHead>Created At</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8">
                        <Loader2 className="h-5 w-5 animate-spin mx-auto text-zinc-400" />
                      </TableCell>
                    </TableRow>
                  ) : entries.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-zinc-400">
                        No entries yet. Add your first customer above.
                      </TableCell>
                    </TableRow>
                  ) : (
                    entries.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell className="font-medium">{entry.customer_name}</TableCell>
                        <TableCell className="font-mono text-sm">{entry.mobile_number}</TableCell>
                        <TableCell>{entry.city}</TableCell>
                        <TableCell className="text-sm text-zinc-500 max-w-[200px] truncate">{entry.notes || '-'}</TableCell>
                        <TableCell className="text-xs text-zinc-500">{formatDate(entry.created_at)}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
