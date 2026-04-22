import React, { useState, useEffect, useCallback, useRef } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { QRCodeSVG } from 'qrcode.react';
import {
  QrCode, Search, Loader2, RefreshCcw, Download,
  Users, CalendarDays, Phone, MapPin
} from 'lucide-react';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const THEME_COLOR = '#ED1C24';

export default function AdminQRLeads() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [todayCount, setTodayCount] = useState(0);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // QR Dialog
  const [qrDialogOpen, setQrDialogOpen] = useState(false);
  const qrRef = useRef(null);

  const qrUrl = `${API_URL}/qr-lead-form`;

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.append('search', searchQuery.trim());
      if (dateFrom) params.append('date_from', new Date(dateFrom).toISOString());
      if (dateTo) params.append('date_to', new Date(dateTo + 'T23:59:59').toISOString());

      const res = await fetch(`${API_URL}/api/admin/qr-leads?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setLeads(data.leads || []);
        setTotal(data.total || 0);
        setTodayCount(data.today_count || 0);
      } else {
        toast.error('Failed to load QR leads');
      }
    } catch {
      toast.error('Failed to load QR leads');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, dateFrom, dateTo]);

  useEffect(() => {
    const debounce = setTimeout(() => fetchLeads(), 300);
    return () => clearTimeout(debounce);
  }, [fetchLeads]);

  const handleExportExcel = () => {
    if (leads.length === 0) {
      toast.error('No data to export');
      return;
    }
    const exportData = leads.map(l => ({
      'Name': l.name,
      'Mobile': l.mobile,
      'City': l.city,
      'State': l.state,
      'Vehicle Type': l.vehicle_type,
      'Date': l.created_at ? new Date(l.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : '',
    }));
    const ws = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'QR Leads');
    XLSX.writeFile(wb, `QR_Leads_${new Date().toISOString().slice(0, 10)}.xlsx`);
    toast.success(`Exported ${exportData.length} leads`);
  };

  const handleDownloadQR = () => {
    const svg = qrRef.current?.querySelector('svg');
    if (!svg) return;
    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      canvas.width = 600;
      canvas.height = 700;
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, 600, 700);
      // Draw QR
      ctx.drawImage(img, 50, 50, 500, 500);
      // Draw text
      ctx.fillStyle = '#ED1C24';
      ctx.font = 'bold 28px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('FieldFlow Pro', 300, 600);
      ctx.fillStyle = '#666666';
      ctx.font = '16px sans-serif';
      ctx.fillText('Scan to Register', 300, 640);
      // Download
      const link = document.createElement('a');
      link.download = 'FieldFlow_QR_Code.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
    toast.success('QR Code downloaded');
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
      <div className="space-y-6" data-testid="admin-qr-leads-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight flex items-center gap-2">
              <QrCode className="h-7 w-7" style={{ color: THEME_COLOR }} />
              QR Leads
            </h1>
            <p className="text-zinc-500 mt-1">Customer leads captured via QR code scan</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button
              onClick={() => setQrDialogOpen(true)}
              style={{ backgroundColor: THEME_COLOR }}
              className="hover:opacity-90"
              data-testid="show-qr-btn"
            >
              <QrCode className="h-4 w-4 mr-2" />
              Show QR Code
            </Button>
            <Button variant="outline" onClick={fetchLeads} disabled={loading} data-testid="refresh-qr-leads">
              <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline" onClick={handleExportExcel} data-testid="export-qr-leads">
              <Download className="h-4 w-4 mr-2" />
              Excel
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold" style={{ color: THEME_COLOR }} data-testid="qr-total-leads">{total}</p>
              <p className="text-xs text-zinc-500">Total Leads</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-green-600" data-testid="qr-today-leads">{todayCount}</p>
              <p className="text-xs text-zinc-500">Today's Leads</p>
            </CardContent>
          </Card>
          <Card className="hidden md:block">
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-blue-600">QR</p>
              <p className="text-xs text-zinc-500">Source</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                <Input
                  placeholder="Search name, mobile, city..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                  data-testid="search-qr-leads"
                />
              </div>
              <Input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-40"
                data-testid="qr-date-from"
              />
              <Input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-40"
                data-testid="qr-date-to"
              />
            </div>
          </CardContent>
        </Card>

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </div>
        ) : leads.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center text-zinc-500">
              <QrCode className="h-12 w-12 mx-auto mb-4 text-zinc-300" />
              <p className="text-lg font-medium">No leads yet</p>
              <p className="text-sm mt-1">Share your QR code to start collecting leads</p>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-zinc-50">
                      <TableHead>Name</TableHead>
                      <TableHead>Mobile</TableHead>
                      <TableHead>City</TableHead>
                      <TableHead>State</TableHead>
                      <TableHead>Vehicle Type</TableHead>
                      <TableHead>Date & Time</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leads.map((lead) => (
                      <TableRow key={lead.id} data-testid={`qr-lead-row-${lead.id}`}>
                        <TableCell className="font-medium">{lead.name}</TableCell>
                        <TableCell>
                          <span className="flex items-center gap-1 text-sm">
                            <Phone className="h-3 w-3 text-zinc-400" />{lead.mobile}
                          </span>
                        </TableCell>
                        <TableCell className="text-sm">{lead.city}</TableCell>
                        <TableCell className="text-sm">{lead.state}</TableCell>
                        <TableCell className="text-sm font-medium">{lead.vehicle_type}</TableCell>
                        <TableCell className="text-xs text-zinc-500 whitespace-nowrap">
                          {formatDate(lead.created_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* QR Code Dialog */}
        <Dialog open={qrDialogOpen} onOpenChange={setQrDialogOpen}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <QrCode className="h-5 w-5" style={{ color: THEME_COLOR }} />
                QR Code for Lead Capture
              </DialogTitle>
            </DialogHeader>
            <div className="flex flex-col items-center gap-4 py-4" ref={qrRef}>
              <div className="p-4 bg-white rounded-xl border-2 border-zinc-200">
                <QRCodeSVG
                  value={qrUrl}
                  size={256}
                  level="H"
                  fgColor="#000000"
                  bgColor="#ffffff"
                  includeMargin={true}
                />
              </div>
              <div className="text-center">
                <p className="font-bold" style={{ color: THEME_COLOR }}>FieldFlow Pro</p>
                <p className="text-sm text-zinc-500">Scan to register</p>
              </div>
              <p className="text-xs text-zinc-400 text-center break-all px-4">{qrUrl}</p>
            </div>
            <Button
              onClick={handleDownloadQR}
              className="w-full"
              style={{ backgroundColor: THEME_COLOR }}
              data-testid="download-qr-btn"
            >
              <Download className="h-4 w-4 mr-2" />
              Download QR Code
            </Button>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
