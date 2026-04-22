import React, { useState, useEffect, useCallback, useRef } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { QRCodeSVG } from 'qrcode.react';
import {
  QrCode, Search, Loader2, RefreshCcw, Download,
  Phone, Plus, Trash2, Tag, Copy, CalendarDays
} from 'lucide-react';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const THEME_COLOR = '#ED1C24';

export default function AdminQRLeads() {
  // Leads state
  const [leads, setLeads] = useState([]);
  const [leadsLoading, setLeadsLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [todayCount, setTodayCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [campaignFilter, setCampaignFilter] = useState('all');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [availableCampaignCodes, setAvailableCampaignCodes] = useState([]);

  // Campaigns state
  const [campaigns, setCampaigns] = useState([]);
  const [campaignsLoading, setCampaignsLoading] = useState(true);
  const [newCampaignName, setNewCampaignName] = useState('');
  const [newCampaignDesc, setNewCampaignDesc] = useState('');
  const [creating, setCreating] = useState(false);

  // QR Dialogs
  const [generalQrOpen, setGeneralQrOpen] = useState(false);
  const [campaignQrOpen, setCampaignQrOpen] = useState(null); // campaign object or null
  const generalQrRef = useRef(null);
  const campaignQrRef = useRef(null);

  const generalQrUrl = `${API_URL}/qr-lead-form`;
  const token = localStorage.getItem('access_token');
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  // ========== Fetch Leads ==========
  const fetchLeads = useCallback(async () => {
    setLeadsLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.append('search', searchQuery.trim());
      if (dateFrom) params.append('date_from', new Date(dateFrom).toISOString());
      if (dateTo) params.append('date_to', new Date(dateTo + 'T23:59:59').toISOString());
      if (campaignFilter !== 'all') params.append('campaign_code', campaignFilter);
      if (sourceFilter !== 'all') params.append('source_filter', sourceFilter);

      const res = await fetch(`${API_URL}/api/admin/qr-leads?${params}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setLeads(data.leads || []);
        setTotal(data.total || 0);
        setTodayCount(data.today_count || 0);
        setAvailableCampaignCodes(data.campaign_codes || []);
      } else toast.error('Failed to load leads');
    } catch { toast.error('Failed to load leads'); }
    finally { setLeadsLoading(false); }
  }, [searchQuery, dateFrom, dateTo, campaignFilter, sourceFilter]);

  useEffect(() => {
    const t = setTimeout(() => fetchLeads(), 300);
    return () => clearTimeout(t);
  }, [fetchLeads]);

  // ========== Fetch Campaigns ==========
  const fetchCampaigns = useCallback(async () => {
    setCampaignsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/qr-campaigns`, { headers });
      if (res.ok) {
        const data = await res.json();
        setCampaigns(data.campaigns || []);
      }
    } catch { /* silent */ }
    finally { setCampaignsLoading(false); }
  }, []);

  useEffect(() => { fetchCampaigns(); }, [fetchCampaigns]);

  // ========== Create Campaign ==========
  const handleCreateCampaign = async () => {
    if (!newCampaignName.trim()) { toast.error('Campaign name is required'); return; }
    setCreating(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/qr-campaigns`, {
        method: 'POST', headers,
        body: JSON.stringify({ name: newCampaignName.trim(), description: newCampaignDesc.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Campaign "${data.campaign.code}" created`);
        setNewCampaignName(''); setNewCampaignDesc('');
        fetchCampaigns();
      } else toast.error(data.detail || 'Failed to create campaign');
    } catch { toast.error('Failed to create campaign'); }
    finally { setCreating(false); }
  };

  // ========== Delete Campaign ==========
  const handleDeleteCampaign = async (id, name) => {
    if (!window.confirm(`Delete campaign "${name}"? Existing leads will NOT be deleted.`)) return;
    try {
      const res = await fetch(`${API_URL}/api/admin/qr-campaigns/${id}`, { method: 'DELETE', headers });
      if (res.ok) { toast.success('Campaign deleted'); fetchCampaigns(); }
      else toast.error('Failed to delete');
    } catch { toast.error('Failed to delete'); }
  };

  // ========== QR Download Helper ==========
  const downloadQR = (ref, filename, subtitle) => {
    const svg = ref.current?.querySelector('svg');
    if (!svg) return;
    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      canvas.width = 600; canvas.height = 720;
      ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, 600, 720);
      ctx.drawImage(img, 50, 50, 500, 500);
      ctx.fillStyle = '#ED1C24'; ctx.font = 'bold 28px sans-serif'; ctx.textAlign = 'center';
      ctx.fillText('FieldFlow Pro', 300, 610);
      ctx.fillStyle = '#666666'; ctx.font = '18px sans-serif';
      ctx.fillText(subtitle, 300, 650);
      const link = document.createElement('a');
      link.download = filename; link.href = canvas.toDataURL('image/png'); link.click();
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
    toast.success('QR Code downloaded');
  };

  // ========== Excel Export ==========
  const handleExportExcel = () => {
    if (!leads.length) { toast.error('No data to export'); return; }
    const rows = leads.map(l => ({
      'Name': l.name, 'Mobile': l.mobile, 'City': l.city, 'State': l.state,
      'Vehicle Type': l.vehicle_type, 'Campaign': l.campaign_name || l.campaign_code || 'GENERAL',
      'Source': l.source || 'QR',
      'Date': l.created_at ? new Date(l.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : '',
    }));
    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'QR Leads');
    XLSX.writeFile(wb, `QR_Leads_${new Date().toISOString().slice(0, 10)}.xlsx`);
    toast.success(`Exported ${rows.length} leads`);
  };

  const fmt = (d) => d ? new Date(d).toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  }) : '-';

  const copyUrl = (url) => { navigator.clipboard.writeText(url); toast.success('URL copied'); };

  return (
    <Layout>
      <div className="space-y-6" data-testid="admin-qr-leads-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight flex items-center gap-2">
              <QrCode className="h-7 w-7" style={{ color: THEME_COLOR }} /> QR Leads
            </h1>
            <p className="text-zinc-500 mt-1">Manage campaign QR codes & view all captured leads</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button onClick={() => setGeneralQrOpen(true)} style={{ backgroundColor: THEME_COLOR }} className="hover:opacity-90" data-testid="show-general-qr-btn">
              <QrCode className="h-4 w-4 mr-2" /> General QR
            </Button>
            <Button variant="outline" onClick={() => { fetchLeads(); fetchCampaigns(); }} disabled={leadsLoading} data-testid="refresh-qr-leads">
              <RefreshCcw className={`h-4 w-4 mr-2 ${leadsLoading ? 'animate-spin' : ''}`} /> Refresh
            </Button>
            <Button variant="outline" onClick={handleExportExcel} data-testid="export-qr-leads">
              <Download className="h-4 w-4 mr-2" /> Excel
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card><CardContent className="p-4 text-center">
            <p className="text-2xl font-bold" style={{ color: THEME_COLOR }} data-testid="qr-total-leads">{total}</p>
            <p className="text-xs text-zinc-500">Total Leads</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-green-600" data-testid="qr-today-leads">{todayCount}</p>
            <p className="text-xs text-zinc-500">Today's Leads</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-600">{campaigns.length}</p>
            <p className="text-xs text-zinc-500">Campaigns</p>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-purple-600">{campaigns.reduce((s, c) => s + (c.lead_count || 0), 0)}</p>
            <p className="text-xs text-zinc-500">Campaign Leads</p>
          </CardContent></Card>
        </div>

        {/* Tabs: Campaigns | Leads */}
        <Tabs defaultValue="campaigns" className="space-y-4">
          <TabsList className="bg-zinc-100">
            <TabsTrigger value="campaigns" data-testid="tab-campaigns">Campaign QR Management</TabsTrigger>
            <TabsTrigger value="leads" data-testid="tab-leads">Leads Data</TabsTrigger>
          </TabsList>

          {/* ========== CAMPAIGNS TAB ========== */}
          <TabsContent value="campaigns" className="space-y-4">
            {/* Create Campaign */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2"><Plus className="h-4 w-4" /> Create Campaign QR</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row gap-3">
                  <Input placeholder="Campaign Name (e.g. BI6)" value={newCampaignName}
                    onChange={(e) => setNewCampaignName(e.target.value)} className="flex-1" data-testid="campaign-name-input" />
                  <Input placeholder="Description (optional)" value={newCampaignDesc}
                    onChange={(e) => setNewCampaignDesc(e.target.value)} className="flex-1" data-testid="campaign-desc-input" />
                  <Button onClick={handleCreateCampaign} disabled={creating} style={{ backgroundColor: THEME_COLOR }}
                    className="hover:opacity-90 whitespace-nowrap" data-testid="create-campaign-btn">
                    {creating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
                    Create
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Campaign List */}
            {campaignsLoading ? (
              <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-zinc-400" /></div>
            ) : campaigns.length === 0 ? (
              <Card><CardContent className="p-12 text-center text-zinc-500">
                <Tag className="h-12 w-12 mx-auto mb-4 text-zinc-300" />
                <p className="text-lg font-medium">No campaigns yet</p>
                <p className="text-sm mt-1">Create your first campaign QR code above</p>
              </CardContent></Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {campaigns.map(c => {
                  const url = `${API_URL}/qr-lead-form?campaign=${c.code}`;
                  return (
                    <Card key={c.id} className="hover:shadow-md transition-shadow" data-testid={`campaign-card-${c.code}`}>
                      <CardContent className="p-5">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <Badge className="bg-blue-100 text-blue-800 font-mono font-bold mb-1">{c.code}</Badge>
                            <p className="font-semibold text-sm">{c.name}</p>
                            {c.description && <p className="text-xs text-zinc-500 mt-0.5">{c.description}</p>}
                          </div>
                          <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700 hover:bg-red-50 h-8 w-8 p-0"
                            onClick={() => handleDeleteCampaign(c.id, c.name)} data-testid={`delete-campaign-${c.code}`}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                        <div className="flex items-center justify-between text-xs text-zinc-500 mb-3">
                          <span className="flex items-center gap-1"><CalendarDays className="h-3 w-3" />{fmt(c.created_at)}</span>
                          <Badge variant="outline" className="font-bold">{c.lead_count} leads</Badge>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" className="flex-1" onClick={() => setCampaignQrOpen(c)} data-testid={`view-qr-${c.code}`}>
                            <QrCode className="h-3.5 w-3.5 mr-1" /> View QR
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => copyUrl(url)} data-testid={`copy-url-${c.code}`}>
                            <Copy className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>

          {/* ========== LEADS TAB ========== */}
          <TabsContent value="leads" className="space-y-4">
            {/* Filters */}
            <Card><CardContent className="p-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
                <div className="relative md:col-span-2">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                  <Input placeholder="Search name, mobile, city..." value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" data-testid="search-qr-leads" />
                </div>
                <Select value={campaignFilter} onValueChange={setCampaignFilter}>
                  <SelectTrigger data-testid="filter-campaign-code"><SelectValue placeholder="All Campaigns" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Campaigns</SelectItem>
                    {availableCampaignCodes.map(cc => <SelectItem key={cc} value={cc}>{cc}</SelectItem>)}
                  </SelectContent>
                </Select>
                <Select value={sourceFilter} onValueChange={setSourceFilter}>
                  <SelectTrigger data-testid="filter-source"><SelectValue placeholder="All Sources" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Sources</SelectItem>
                    <SelectItem value="general">General QR</SelectItem>
                    <SelectItem value="campaign">Campaign QR</SelectItem>
                  </SelectContent>
                </Select>
                <div className="flex gap-2">
                  <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="flex-1" data-testid="qr-date-from" />
                  <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="flex-1" data-testid="qr-date-to" />
                </div>
              </div>
            </CardContent></Card>

            {/* Table */}
            {leadsLoading ? (
              <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-zinc-400" /></div>
            ) : leads.length === 0 ? (
              <Card><CardContent className="p-12 text-center text-zinc-500">
                <QrCode className="h-12 w-12 mx-auto mb-4 text-zinc-300" />
                <p className="text-lg font-medium">No leads found</p>
                <p className="text-sm mt-1">Share your QR codes to start collecting leads</p>
              </CardContent></Card>
            ) : (
              <Card><CardContent className="p-0">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader><TableRow className="bg-zinc-50">
                      <TableHead>Name</TableHead>
                      <TableHead>Mobile</TableHead>
                      <TableHead>City</TableHead>
                      <TableHead>State</TableHead>
                      <TableHead>Vehicle Type</TableHead>
                      <TableHead>Campaign</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Date & Time</TableHead>
                    </TableRow></TableHeader>
                    <TableBody>
                      {leads.map(lead => (
                        <TableRow key={lead.id} data-testid={`qr-lead-row-${lead.id}`}>
                          <TableCell className="font-medium">{lead.name}</TableCell>
                          <TableCell><span className="flex items-center gap-1 text-sm"><Phone className="h-3 w-3 text-zinc-400" />{lead.mobile}</span></TableCell>
                          <TableCell className="text-sm">{lead.city}</TableCell>
                          <TableCell className="text-sm">{lead.state}</TableCell>
                          <TableCell className="text-sm font-medium">{lead.vehicle_type}</TableCell>
                          <TableCell>
                            {lead.campaign_code ? (
                              <Badge className="bg-blue-100 text-blue-800 font-mono text-xs">{lead.campaign_name || lead.campaign_code}</Badge>
                            ) : (
                              <span className="text-xs text-zinc-400">GENERAL</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={`text-xs ${lead.source === 'CAMPAIGN_QR' ? 'border-blue-300 text-blue-700' : 'border-zinc-300 text-zinc-600'}`}>
                              {lead.source === 'CAMPAIGN_QR' ? 'Campaign' : 'General'}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs text-zinc-500 whitespace-nowrap">{fmt(lead.created_at)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent></Card>
            )}
          </TabsContent>
        </Tabs>

        {/* ========== General QR Dialog ========== */}
        <Dialog open={generalQrOpen} onOpenChange={setGeneralQrOpen}>
          <DialogContent className="max-w-sm">
            <DialogHeader><DialogTitle className="flex items-center gap-2">
              <QrCode className="h-5 w-5" style={{ color: THEME_COLOR }} /> General QR Code
            </DialogTitle></DialogHeader>
            <div className="flex flex-col items-center gap-4 py-4" ref={generalQrRef}>
              <div className="p-4 bg-white rounded-xl border-2 border-zinc-200">
                <QRCodeSVG value={generalQrUrl} size={256} level="H" fgColor="#000000" bgColor="#ffffff" includeMargin />
              </div>
              <div className="text-center">
                <p className="font-bold" style={{ color: THEME_COLOR }}>FieldFlow Pro</p>
                <p className="text-sm text-zinc-500">General Registration</p>
              </div>
              <p className="text-xs text-zinc-400 text-center break-all px-4">{generalQrUrl}</p>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => downloadQR(generalQrRef, 'FieldFlow_General_QR.png', 'Scan to Register')}
                className="flex-1" style={{ backgroundColor: THEME_COLOR }} data-testid="download-general-qr">
                <Download className="h-4 w-4 mr-2" /> Download
              </Button>
              <Button variant="outline" onClick={() => copyUrl(generalQrUrl)} data-testid="copy-general-url">
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* ========== Campaign QR Dialog ========== */}
        <Dialog open={!!campaignQrOpen} onOpenChange={(v) => !v && setCampaignQrOpen(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader><DialogTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5 text-blue-600" /> {campaignQrOpen?.code} QR Code
            </DialogTitle></DialogHeader>
            {campaignQrOpen && (() => {
              const url = `${API_URL}/qr-lead-form?campaign=${campaignQrOpen.code}`;
              return (
                <>
                  <div className="flex flex-col items-center gap-4 py-4" ref={campaignQrRef}>
                    <div className="p-4 bg-white rounded-xl border-2 border-blue-200">
                      <QRCodeSVG value={url} size={256} level="H" fgColor="#000000" bgColor="#ffffff" includeMargin />
                    </div>
                    <div className="text-center">
                      <p className="font-bold" style={{ color: THEME_COLOR }}>FieldFlow Pro</p>
                      <Badge className="bg-blue-100 text-blue-800 font-mono mt-1">{campaignQrOpen.code}</Badge>
                    </div>
                    <p className="text-xs text-zinc-400 text-center break-all px-4">{url}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={() => downloadQR(campaignQrRef, `FieldFlow_${campaignQrOpen.code}_QR.png`, `Campaign: ${campaignQrOpen.code}`)}
                      className="flex-1" style={{ backgroundColor: THEME_COLOR }} data-testid="download-campaign-qr">
                      <Download className="h-4 w-4 mr-2" /> Download
                    </Button>
                    <Button variant="outline" onClick={() => copyUrl(url)} data-testid="copy-campaign-url">
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </>
              );
            })()}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
