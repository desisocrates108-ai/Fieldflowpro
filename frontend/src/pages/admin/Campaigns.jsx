import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from '../../components/ui/dialog';
import { Alert, AlertDescription } from '../../components/ui/alert';
import ForceDeleteModal from '../../components/ForceDeleteModal';
import { 
  Plus, Ticket, Package, IndianRupee, Hash, 
  Loader2, Search, Eye, Trash2, Pause,
  RefreshCcw, CheckCircle, XCircle, AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [campaignCoupons, setCampaignCoupons] = useState([]);
  const [couponsLoading, setCouponsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [creating, setCreating] = useState(false);
  
  // Delete Modal State
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [campaignToDelete, setCampaignToDelete] = useState(null);
  const [campaignDependencies, setCampaignDependencies] = useState({});
  const [deleting, setDeleting] = useState(false);

  // Form state - new range-based logic
  const [formData, setFormData] = useState({
    name: '',
    price: '',
    start_code: '',
    end_code: ''
  });

  // Validation state
  const [validation, setValidation] = useState({
    valid: false,
    message: '',
    totalCoupons: 0,
    prefix: ''
  });

  const parseCode = (code) => {
    const match = code.trim().toUpperCase().match(/^([A-Z]+)(\d+)$/);
    if (match) {
      return { prefix: match[1], number: parseInt(match[2]) };
    }
    return null;
  };

  // Validate coupon range whenever start/end codes change
  useEffect(() => {
    const startCode = formData.start_code.trim().toUpperCase();
    const endCode = formData.end_code.trim().toUpperCase();

    if (!startCode || !endCode) {
      setValidation({ valid: false, message: '', totalCoupons: 0, prefix: '' });
      return;
    }

    const startParsed = parseCode(startCode);
    const endParsed = parseCode(endCode);

    if (!startParsed) {
      setValidation({ valid: false, message: 'Invalid start code format. Use format like "UT100"', totalCoupons: 0, prefix: '' });
      return;
    }

    if (!endParsed) {
      setValidation({ valid: false, message: 'Invalid end code format. Use format like "UT400"', totalCoupons: 0, prefix: '' });
      return;
    }

    if (startParsed.prefix !== endParsed.prefix) {
      setValidation({ 
        valid: false, 
        message: `Prefix mismatch: "${startParsed.prefix}" vs "${endParsed.prefix}". Both codes must have the same prefix.`, 
        totalCoupons: 0, 
        prefix: '' 
      });
      return;
    }

    if (endParsed.number <= startParsed.number) {
      setValidation({ 
        valid: false, 
        message: `End number (${endParsed.number}) must be greater than start number (${startParsed.number})`, 
        totalCoupons: 0, 
        prefix: startParsed.prefix 
      });
      return;
    }

    const total = endParsed.number - startParsed.number;
    setValidation({ 
      valid: true, 
      message: `Will create ${total} coupons: ${startCode} to ${startParsed.prefix}${endParsed.number - 1}`, 
      totalCoupons: total,
      prefix: startParsed.prefix
    });
  }, [formData.start_code, formData.end_code]);

  const fetchCampaigns = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/campaigns`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCampaigns(data);
      }
    } catch (error) {
      toast.error('Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const handleCreate = async () => {
    if (!formData.name || !formData.price || !validation.valid) {
      toast.error('Please fill all fields correctly');
      return;
    }

    setCreating(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/campaigns`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: formData.name,
          price: parseFloat(formData.price),
          start_code: formData.start_code.toUpperCase(),
          end_code: formData.end_code.toUpperCase()
        })
      });

      if (response.ok) {
        toast.success(`Campaign created with ${validation.totalCoupons} coupons!`);
        setCreateDialogOpen(false);
        setFormData({ name: '', price: '', start_code: '', end_code: '' });
        fetchCampaigns();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create campaign');
      }
    } catch (error) {
      toast.error('Failed to create campaign');
    } finally {
      setCreating(false);
    }
  };

  const viewCampaignCoupons = async (campaign) => {
    setSelectedCampaign(campaign);
    setViewDialogOpen(true);
    setCouponsLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/campaigns/${campaign.id}/coupons?limit=50`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCampaignCoupons(data);
      }
    } catch (error) {
      toast.error('Failed to load coupons');
    } finally {
      setCouponsLoading(false);
    }
  };

  const updateCampaignStatus = async (campaignId, status) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/campaigns/${campaignId}?status=${status}`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        toast.success(`Campaign ${status.toLowerCase()}`);
        fetchCampaigns();
      }
    } catch (error) {
      toast.error('Failed to update campaign');
    }
  };

  const openDeleteModal = async (campaign) => {
    setCampaignToDelete(campaign);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/campaigns/${campaign.id}/dependencies`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCampaignDependencies(data.dependencies || {});
      }
    } catch (error) {
      setCampaignDependencies({
        total_coupons: campaign.total_coupons || 0,
        sold: campaign.sold_count || 0
      });
    }
    setDeleteModalOpen(true);
  };

  const handleDeleteCampaign = async (forceDelete) => {
    if (!campaignToDelete) return;
    
    setDeleting(true);
    try {
      const token = localStorage.getItem('access_token');
      const url = `${API_URL}/api/campaigns/${campaignToDelete.id}${forceDelete ? '?force=true' : ''}`;
      const response = await fetch(url, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(data.message || 'Campaign deleted');
        fetchCampaigns();
        setDeleteModalOpen(false);
        setCampaignToDelete(null);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete campaign');
      }
    } catch (error) {
      toast.error('Failed to delete campaign');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeactivateCampaign = async (campaign) => {
    if (campaign.status === 'INACTIVE') {
      toast.info('Campaign is already inactive');
      return;
    }
    
    if (!window.confirm(`Deactivate campaign "${campaign.name}"? It will no longer be available for new sales.`)) {
      return;
    }
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/campaigns/${campaign.id}/deactivate`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        toast.success('Campaign deactivated');
        fetchCampaigns();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to deactivate campaign');
      }
    } catch (error) {
      toast.error('Failed to deactivate campaign');
    }
  };

  const filteredCampaigns = campaigns.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.prefix.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusColor = (status) => {
    switch (status) {
      case 'ACTIVE': return 'bg-green-100 text-green-800';
      case 'INACTIVE': return 'bg-gray-100 text-gray-800';
      case 'COMPLETED': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Calculate stats
  const totalRevenue = campaigns.reduce((acc, c) => acc + (c.sold_count * c.price), 0);
  const totalSold = campaigns.reduce((acc, c) => acc + c.sold_count, 0);
  const totalAvailable = campaigns.reduce((acc, c) => acc + c.available_count, 0);

  return (
    <Layout>
      <div className="space-y-6" data-testid="campaigns-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              Campaign Management
            </h1>
            <p className="text-zinc-500 mt-1">Create and manage coupon campaigns</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => { setLoading(true); fetchCampaigns(); }}>
              <RefreshCcw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700" data-testid="create-campaign-btn">
                  <Plus className="h-4 w-4 mr-2" />
                  Create Campaign
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle className="font-['Barlow_Condensed'] text-2xl">Create New Campaign</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Campaign Name</Label>
                    <Input
                      placeholder="e.g., Mumbai Diwali Sale"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      data-testid="campaign-name-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Price (₹)</Label>
                    <Input
                      type="number"
                      placeholder="149"
                      value={formData.price}
                      onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                      data-testid="campaign-price-input"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Start Coupon Code</Label>
                      <Input
                        placeholder="e.g., UT100"
                        value={formData.start_code}
                        onChange={(e) => setFormData({ ...formData, start_code: e.target.value.toUpperCase() })}
                        data-testid="campaign-start-code-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>End Coupon Code</Label>
                      <Input
                        placeholder="e.g., UT400"
                        value={formData.end_code}
                        onChange={(e) => setFormData({ ...formData, end_code: e.target.value.toUpperCase() })}
                        data-testid="campaign-end-code-input"
                      />
                    </div>
                  </div>
                  
                  {/* Validation Alert */}
                  {(formData.start_code || formData.end_code) && (
                    <Alert className={validation.valid ? 'border-green-500 bg-green-50' : 'border-amber-500 bg-amber-50'}>
                      <AlertDescription className="flex items-center gap-2">
                        {validation.valid ? (
                          <>
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            <span className="text-green-800">{validation.message}</span>
                          </>
                        ) : (
                          <>
                            <AlertTriangle className="h-4 w-4 text-amber-600" />
                            <span className="text-amber-800">{validation.message || 'Enter both start and end codes'}</span>
                          </>
                        )}
                      </AlertDescription>
                    </Alert>
                  )}
                  
                  {validation.valid && (
                    <div className="p-4 bg-zinc-50 rounded-lg border">
                      <h4 className="font-medium text-sm text-zinc-700 mb-2">Preview</h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="text-zinc-500">Prefix:</div>
                        <div className="font-mono font-medium">{validation.prefix}</div>
                        <div className="text-zinc-500">Total Coupons:</div>
                        <div className="font-bold text-blue-600">{validation.totalCoupons}</div>
                        <div className="text-zinc-500">First Code:</div>
                        <div className="font-mono">{formData.start_code.toUpperCase()}</div>
                        <div className="text-zinc-500">Last Code:</div>
                        <div className="font-mono">{validation.prefix}{parseInt(formData.end_code.match(/\d+/)?.[0] || 0) - 1}</div>
                      </div>
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
                  <Button 
                    onClick={handleCreate} 
                    disabled={creating || !validation.valid || !formData.name || !formData.price} 
                    data-testid="confirm-create-btn"
                  >
                    {creating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
                    Create {validation.totalCoupons > 0 ? `(${validation.totalCoupons} coupons)` : 'Campaign'}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Package className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Active Campaigns</p>
                  <p className="text-2xl font-bold">{campaigns.filter(c => c.status === 'ACTIVE').length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Ticket className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Coupons Sold</p>
                  <p className="text-2xl font-bold">{totalSold}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <Hash className="h-5 w-5 text-yellow-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Available</p>
                  <p className="text-2xl font-bold">{totalAvailable}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <IndianRupee className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">Total Revenue</p>
                  <p className="text-2xl font-bold">₹{totalRevenue.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input
            placeholder="Search campaigns..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
            data-testid="search-campaigns-input"
          />
        </div>

        {/* Campaigns Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : filteredCampaigns.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <Package className="h-12 w-12 text-zinc-300 mb-4" />
                <p className="text-zinc-500">No campaigns found</p>
                <p className="text-sm text-zinc-400">Create your first campaign to get started</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Campaign</TableHead>
                    <TableHead>Prefix</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Sold / Total</TableHead>
                    <TableHead>Revenue</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCampaigns.map((campaign) => (
                    <TableRow key={campaign.id} className="table-row-hover">
                      <TableCell className="font-medium">{campaign.name}</TableCell>
                      <TableCell>
                        <code className="px-2 py-1 bg-zinc-100 rounded text-sm">{campaign.prefix}</code>
                      </TableCell>
                      <TableCell>₹{campaign.price}</TableCell>
                      <TableCell>
                        <span className="font-medium text-green-600">{campaign.sold_count}</span>
                        <span className="text-zinc-400"> / {campaign.total_count}</span>
                      </TableCell>
                      <TableCell className="font-medium">
                        ₹{(campaign.sold_count * campaign.price).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(campaign.status)}>{campaign.status}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => viewCampaignCoupons(campaign)}
                            data-testid={`view-campaign-${campaign.id}`}
                            title="View Coupons"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {campaign.status === 'ACTIVE' ? (
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-orange-600 hover:bg-orange-50"
                              onClick={() => handleDeactivateCampaign(campaign)}
                              title="Deactivate (soft delete)"
                              data-testid={`deactivate-campaign-${campaign.id}`}
                            >
                              <Pause className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => updateCampaignStatus(campaign.id, 'ACTIVE')}
                              title="Activate"
                            >
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-red-600 hover:bg-red-50"
                            onClick={() => openDeleteModal(campaign)}
                            title="Delete campaign"
                            data-testid={`delete-campaign-${campaign.id}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Force Delete Modal */}
        <ForceDeleteModal
          open={deleteModalOpen}
          onClose={() => {
            setDeleteModalOpen(false);
            setCampaignToDelete(null);
          }}
          onConfirm={handleDeleteCampaign}
          title="Delete Campaign"
          itemName={campaignToDelete?.name || ''}
          dependencies={campaignDependencies}
          loading={deleting}
        />

        {/* View Campaign Coupons Dialog */}
        <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-['Barlow_Condensed'] text-2xl">
                {selectedCampaign?.name} - Coupons
              </DialogTitle>
            </DialogHeader>
            {couponsLoading ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : (
              <div className="max-h-96 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Sold At</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {campaignCoupons.map((coupon) => (
                      <TableRow key={coupon.id}>
                        <TableCell>
                          <code className="px-2 py-1 bg-zinc-100 rounded text-sm font-mono">
                            {coupon.code}
                          </code>
                        </TableCell>
                        <TableCell>
                          <Badge className={
                            coupon.status === 'AVAILABLE' ? 'bg-green-100 text-green-800' :
                            coupon.status === 'SOLD' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }>
                            {coupon.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{coupon.customer_name || '-'}</TableCell>
                        <TableCell className="text-sm text-zinc-500">
                          {coupon.sold_at ? new Date(coupon.sold_at).toLocaleString() : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
