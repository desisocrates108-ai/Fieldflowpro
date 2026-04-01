import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { branchAPI } from '../../lib/api';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../../components/ui/dialog';
import ForceDeleteModal from '../../components/ForceDeleteModal';
import { Loader2, Building2, Plus, MapPin, Phone, Trash2, Power, Pencil } from 'lucide-react';
import { formatDateTime } from '../../lib/utils';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const emptyForm = { name: '', address: '', latitude: '', longitude: '', contact_phone: '' };

export default function BranchesPage() {
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ ...emptyForm });
  const [submitting, setSubmitting] = useState(false);
  
  // Edit state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editData, setEditData] = useState({ ...emptyForm });
  const [editBranchId, setEditBranchId] = useState(null);
  const [saving, setSaving] = useState(false);
  
  // Delete
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [branchToDelete, setBranchToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [branchDependencies, setBranchDependencies] = useState({});

  const fetchBranches = async () => {
    try {
      const response = await branchAPI.getAll();
      setBranches(response.data);
    } catch (error) {
      toast.error('Failed to load branches');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchBranches(); }, []);

  const handleCreate = async (e) => {
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
      setFormData({ ...emptyForm });
      fetchBranches();
    } catch {
      toast.error('Failed to create branch');
    } finally {
      setSubmitting(false);
    }
  };

  const openEditDialog = (branch) => {
    setEditBranchId(branch.id);
    setEditData({
      name: branch.name || '',
      address: branch.address || '',
      latitude: branch.latitude?.toString() || '',
      longitude: branch.longitude?.toString() || '',
      contact_phone: branch.contact_phone || ''
    });
    setEditDialogOpen(true);
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!editData.name || !editData.address) {
      toast.error('Branch Name and Address are required');
      return;
    }
    setSaving(true);
    try {
      const token = localStorage.getItem('access_token');
      const payload = {
        name: editData.name,
        address: editData.address,
        contact_phone: editData.contact_phone || null,
      };
      if (editData.latitude) payload.latitude = parseFloat(editData.latitude);
      if (editData.longitude) payload.longitude = parseFloat(editData.longitude);

      const res = await fetch(`${API_URL}/api/branches/${editBranchId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        toast.success('Branch updated successfully');
        setEditDialogOpen(false);
        fetchBranches();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to update branch');
      }
    } catch {
      toast.error('Failed to update branch');
    } finally {
      setSaving(false);
    }
  };

  const handleGetLocation = (target) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude.toFixed(6);
          const lng = position.coords.longitude.toFixed(6);
          if (target === 'create') {
            setFormData(f => ({ ...f, latitude: lat, longitude: lng }));
          } else {
            setEditData(f => ({ ...f, latitude: lat, longitude: lng }));
          }
          toast.success('Location captured');
        },
        () => toast.error('Failed to get location')
      );
    } else {
      toast.error('Geolocation not supported');
    }
  };

  const openDeleteDialog = async (branch) => {
    setBranchToDelete(branch);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/branches/${branch.id}/dependencies`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setBranchDependencies(data.dependencies || {});
      }
    } catch {
      setBranchDependencies({});
    }
    setDeleteDialogOpen(true);
  };

  const handleDeleteBranch = async (forceDelete) => {
    if (!branchToDelete) return;
    setDeleting(true);
    try {
      const token = localStorage.getItem('access_token');
      const url = `${API_URL}/api/branches/${branchToDelete.id}${forceDelete ? '?force=true' : ''}`;
      const response = await fetch(url, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const result = await response.json();
      if (response.ok) {
        toast.success(result.message);
        fetchBranches();
        setDeleteDialogOpen(false);
        setBranchToDelete(null);
      } else {
        toast.error(result.detail || 'Failed to remove branch');
      }
    } catch {
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
    } catch {
      toast.error('Failed to activate branch');
    }
  };

  const BranchForm = ({ data, onChange, onSubmit, onGetLocation, submitLabel, loading: isLoading, locationTarget }) => (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label>Branch Name *</Label>
        <Input
          placeholder="Main Branch"
          value={data.name}
          onChange={(e) => onChange({ ...data, name: e.target.value })}
          data-testid="branch-name-input"
        />
      </div>
      <div className="space-y-2">
        <Label>Address *</Label>
        <Input
          placeholder="123 Main Street"
          value={data.address}
          onChange={(e) => onChange({ ...data, address: e.target.value })}
          data-testid="branch-address-input"
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Latitude</Label>
          <Input
            type="number" step="any" placeholder="28.6139"
            value={data.latitude}
            onChange={(e) => onChange({ ...data, latitude: e.target.value })}
            data-testid="branch-lat-input"
          />
        </div>
        <div className="space-y-2">
          <Label>Longitude</Label>
          <Input
            type="number" step="any" placeholder="77.2090"
            value={data.longitude}
            onChange={(e) => onChange({ ...data, longitude: e.target.value })}
            data-testid="branch-lng-input"
          />
        </div>
      </div>
      <Button type="button" variant="outline" onClick={() => onGetLocation(locationTarget)} className="w-full">
        <MapPin className="h-4 w-4 mr-2" /> Use Current Location
      </Button>
      <div className="space-y-2">
        <Label>Contact Phone</Label>
        <Input
          type="tel" placeholder="+91 98765 43210"
          value={data.contact_phone}
          onChange={(e) => onChange({ ...data, contact_phone: e.target.value })}
          data-testid="branch-phone-input"
        />
      </div>
      <Button type="submit" className="w-full" disabled={isLoading} data-testid="submit-branch-btn">
        {isLoading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Saving...</> : submitLabel}
      </Button>
    </form>
  );

  return (
    <Layout>
      <div className="space-y-6" data-testid="branches-page">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">Branches</h1>
            <p className="text-zinc-500 mt-1">Manage service branches</p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button data-testid="add-branch-btn">
                <Plus className="h-4 w-4 mr-2" /> Add Branch
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Branch</DialogTitle>
              </DialogHeader>
              <BranchForm
                data={formData}
                onChange={setFormData}
                onSubmit={handleCreate}
                onGetLocation={handleGetLocation}
                submitLabel="Create Branch"
                loading={submitting}
                locationTarget="create"
              />
            </DialogContent>
          </Dialog>
        </div>

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
                    <TableHead className="w-28">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {branches.map((branch) => (
                    <TableRow key={branch.id}>
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
                          {branch.latitude?.toFixed(4)}, {branch.longitude?.toFixed(4)}
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
                      <TableCell className="text-zinc-600 text-sm">
                        {formatDateTime(branch.created_at)}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 px-2 text-blue-600 border-blue-300 hover:bg-blue-50"
                            onClick={() => openEditDialog(branch)}
                            data-testid={`edit-branch-${branch.id}`}
                          >
                            <Pencil className="h-3 w-3" />
                          </Button>
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

        {/* Edit Branch Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Pencil className="h-4 w-4" /> Edit Branch
              </DialogTitle>
            </DialogHeader>
            <BranchForm
              data={editData}
              onChange={setEditData}
              onSubmit={handleUpdate}
              onGetLocation={handleGetLocation}
              submitLabel="Save Changes"
              loading={saving}
              locationTarget="edit"
            />
          </DialogContent>
        </Dialog>

        {/* Force Delete Modal */}
        <ForceDeleteModal
          open={deleteDialogOpen}
          onClose={() => { setDeleteDialogOpen(false); setBranchToDelete(null); }}
          onConfirm={handleDeleteBranch}
          title="Delete Branch"
          itemName={branchToDelete?.name || ''}
          dependencies={branchDependencies}
          loading={deleting}
        />
      </div>
    </Layout>
  );
}
