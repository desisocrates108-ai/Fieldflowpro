import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { branchAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../../components/ui/dialog';
import { Alert, AlertDescription } from '../../components/ui/alert';
import ForceDeleteModal from '../../components/ForceDeleteModal';
import { Loader2, Building2, Plus, MapPin, Phone, Trash2, Power, AlertTriangle, CheckCircle } from 'lucide-react';
import { formatDateTime } from '../../lib/utils';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function BranchesPage() {
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    latitude: '',
    longitude: '',
    contact_phone: ''
  });
  const [submitting, setSubmitting] = useState(false);
  
  // Delete/Deactivate dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [branchToDelete, setBranchToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [branchDependencies, setBranchDependencies] = useState({});

  const fetchBranches = async () => {
    try {
      const response = await branchAPI.getAll();
      setBranches(response.data);
    } catch (error) {
      console.error('Failed to fetch branches:', error);
      toast.error('Failed to load branches');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBranches();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.address || !formData.latitude || !formData.longitude) {
      toast.error('Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    try {
      await branchAPI.create({
        name: formData.name,
        address: formData.address,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
        contact_phone: formData.contact_phone || null
      });
      toast.success('Branch created successfully');
      setDialogOpen(false);
      setFormData({ name: '', address: '', latitude: '', longitude: '', contact_phone: '' });
      fetchBranches();
    } catch (error) {
      console.error('Failed to create branch:', error);
      toast.error('Failed to create branch');
    } finally {
      setSubmitting(false);
    }
  };

  const handleGetLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData({
            ...formData,
            latitude: position.coords.latitude.toFixed(6),
            longitude: position.coords.longitude.toFixed(6)
          });
          toast.success('Location captured');
        },
        (error) => {
          toast.error('Failed to get location');
        }
      );
    } else {
      toast.error('Geolocation not supported');
    }
  };

  const openDeleteDialog = (branch) => {
    setBranchToDelete(branch);
    setDeleteResult(null);
    setDeleteDialogOpen(true);
  };

  const handleDeleteBranch = async () => {
    if (!branchToDelete) return;
    
    setDeleting(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/branches/${branchToDelete.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const result = await response.json();
      
      if (response.ok) {
        setDeleteResult(result);
        toast.success(result.message);
        fetchBranches();
        
        // Close dialog after short delay if successful
        setTimeout(() => {
          setDeleteDialogOpen(false);
          setBranchToDelete(null);
        }, 1500);
      } else {
        toast.error(result.detail || 'Failed to remove branch');
      }
    } catch (error) {
      toast.error('Failed to remove branch');
    } finally {
      setDeleting(false);
    }
  };

  const handleActivateBranch = async (branchId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/branches/${branchId}/activate`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        toast.success('Branch activated');
        fetchBranches();
      } else {
        toast.error('Failed to activate branch');
      }
    } catch (error) {
      toast.error('Failed to activate branch');
    }
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="branches-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              Branches
            </h1>
            <p className="text-zinc-500 mt-1">
              Manage service branches
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button data-testid="add-branch-btn">
                <Plus className="h-4 w-4 mr-2" />
                Add Branch
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="font-['Barlow_Condensed']">Add New Branch</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Branch Name *</Label>
                  <Input
                    id="name"
                    placeholder="Main Branch"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    data-testid="branch-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address">Address *</Label>
                  <Input
                    id="address"
                    placeholder="123 Main Street"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    data-testid="branch-address-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="latitude">Latitude *</Label>
                    <Input
                      id="latitude"
                      type="number"
                      step="any"
                      placeholder="37.7749"
                      value={formData.latitude}
                      onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                      data-testid="branch-lat-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="longitude">Longitude *</Label>
                    <Input
                      id="longitude"
                      type="number"
                      step="any"
                      placeholder="-122.4194"
                      value={formData.longitude}
                      onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                      data-testid="branch-lng-input"
                    />
                  </div>
                </div>
                <Button type="button" variant="outline" onClick={handleGetLocation} className="w-full">
                  <MapPin className="h-4 w-4 mr-2" />
                  Use Current Location
                </Button>
                <div className="space-y-2">
                  <Label htmlFor="contact_phone">Contact Phone</Label>
                  <Input
                    id="contact_phone"
                    type="tel"
                    placeholder="+1 234 567 8900"
                    value={formData.contact_phone}
                    onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                    data-testid="branch-phone-input"
                  />
                </div>
                <Button type="submit" className="w-full" disabled={submitting} data-testid="submit-branch-btn">
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Branch'
                  )}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Branches Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : branches.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <Building2 className="h-12 w-12 text-zinc-300 mb-4" />
                <p className="text-zinc-500">No branches found</p>
                <p className="text-sm text-zinc-400">Add your first branch to get started</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Address</TableHead>
                    <TableHead>Coordinates</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {branches.map((branch) => (
                    <TableRow key={branch.id} className="table-row-hover">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                            <Building2 className="h-4 w-4 text-indigo-600" />
                          </div>
                          <span className="font-medium">{branch.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-zinc-600 max-w-48 truncate">
                          <MapPin className="h-4 w-4 shrink-0" />
                          {branch.address}
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-xs bg-zinc-100 px-2 py-1 rounded">
                          {branch.latitude.toFixed(4)}, {branch.longitude.toFixed(4)}
                        </code>
                      </TableCell>
                      <TableCell>
                        {branch.contact_phone ? (
                          <div className="flex items-center gap-2 text-zinc-600">
                            <Phone className="h-4 w-4" />
                            {branch.contact_phone}
                          </div>
                        ) : (
                          <span className="text-zinc-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={branch.is_active ? 'default' : 'secondary'}>
                          {branch.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-zinc-600">
                        {formatDateTime(branch.created_at)}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {!branch.is_active && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-8 px-2 text-green-600 border-green-300 hover:bg-green-50"
                              onClick={() => handleActivateBranch(branch.id)}
                              data-testid={`activate-branch-${branch.id}`}
                            >
                              <Power className="h-3 w-3" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 px-2 text-red-600 border-red-300 hover:bg-red-50"
                            onClick={() => openDeleteDialog(branch)}
                            data-testid={`delete-branch-${branch.id}`}
                          >
                            <Trash2 className="h-3 w-3" />
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

        {/* Delete/Deactivate Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                Remove Branch
              </DialogTitle>
            </DialogHeader>
            
            {deleteResult ? (
              <Alert className={deleteResult.action === 'DELETED' ? 'border-green-500 bg-green-50' : 'border-amber-500 bg-amber-50'}>
                <AlertDescription className="flex items-center gap-2">
                  {deleteResult.action === 'DELETED' ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-green-800">{deleteResult.message}</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-4 w-4 text-amber-600" />
                      <div className="text-amber-800">
                        <p className="font-medium">{deleteResult.message}</p>
                        {deleteResult.dependencies && (
                          <ul className="mt-2 text-sm">
                            <li>Workers assigned: {deleteResult.dependencies.assigned_workers}</li>
                            <li>Coupons sold: {deleteResult.dependencies.sold_coupons}</li>
                            <li>Encashments: {deleteResult.dependencies.encashments}</li>
                          </ul>
                        )}
                      </div>
                    </>
                  )}
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-4 py-4">
                <p className="text-zinc-600">
                  Are you sure you want to remove <strong>{branchToDelete?.name}</strong>?
                </p>
                <Alert className="border-amber-500 bg-amber-50">
                  <AlertDescription className="text-amber-800 text-sm">
                    <strong>Note:</strong> If this branch has assigned workers, sold coupons, or encashment history, 
                    it will be <strong>deactivated</strong> instead of permanently deleted.
                  </AlertDescription>
                </Alert>
              </div>
            )}
            
            {!deleteResult && (
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                  Cancel
                </Button>
                <Button 
                  variant="destructive" 
                  onClick={handleDeleteBranch}
                  disabled={deleting}
                  data-testid="confirm-delete-branch-btn"
                >
                  {deleting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Remove Branch
                </Button>
              </DialogFooter>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
