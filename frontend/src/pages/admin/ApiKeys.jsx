import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from '../../components/ui/dialog';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { 
  Key, Plus, Loader2, RefreshCcw, Copy, Check,
  Eye, EyeOff, Trash2, Shield, AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const THEME_COLOR = '#ED1C24';

export default function ApiKeysPage() {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newKeyData, setNewKeyData] = useState({ service_name: '', description: '' });
  const [generatedKey, setGeneratedKey] = useState(null);
  const [copiedKey, setCopiedKey] = useState(false);

  const fetchApiKeys = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/admin/api-keys`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setApiKeys(data);
      }
    } catch (error) {
      console.error('Failed to fetch API keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const createApiKey = async () => {
    if (!newKeyData.service_name.trim()) {
      toast.error('Service name is required');
      return;
    }

    setCreating(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/admin/api-keys`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          service_name: newKeyData.service_name.trim(),
          description: newKeyData.description.trim() || null
        })
      });

      if (response.ok) {
        const data = await response.json();
        setGeneratedKey(data.api_key);
        toast.success('API key generated successfully');
        fetchApiKeys();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create API key');
      }
    } catch (error) {
      toast.error('Failed to create API key');
    } finally {
      setCreating(false);
    }
  };

  const toggleKeyStatus = async (keyId, currentStatus) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/admin/api-keys/${keyId}/toggle`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success(currentStatus ? 'API key deactivated' : 'API key activated');
        fetchApiKeys();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to update API key');
      }
    } catch (error) {
      toast.error('Failed to update API key status');
    }
  };

  const deleteApiKey = async (keyId) => {
    if (!window.confirm('Are you sure you want to permanently delete this API key? This cannot be undone.')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/admin/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('API key deleted');
        fetchApiKeys();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete API key');
      }
    } catch (error) {
      toast.error('Failed to delete API key');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    toast.success('API key copied to clipboard');
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const resetForm = () => {
    setNewKeyData({ service_name: '', description: '' });
    setGeneratedKey(null);
    setCopiedKey(false);
  };

  const formatDate = (date) => {
    if (!date) return '-';
    return new Date(date).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="api-keys-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold font-['Barlow_Condensed'] tracking-tight" style={{ color: THEME_COLOR }}>
              API Key Management
            </h1>
            <p className="text-zinc-500 text-sm mt-1">Manage API keys for external integrations</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button variant="outline" size="sm" onClick={() => { setLoading(true); fetchApiKeys(); }}>
              <RefreshCcw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
            <Dialog 
              open={createDialogOpen} 
              onOpenChange={(open) => { 
                setCreateDialogOpen(open); 
                if (!open) resetForm(); 
              }}
            >
              <DialogTrigger asChild>
                <Button style={{ backgroundColor: THEME_COLOR }} data-testid="create-api-key-btn">
                  <Plus className="h-4 w-4 mr-2" />
                  Generate New Key
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle className="font-['Barlow_Condensed'] text-2xl flex items-center gap-2">
                    <Key className="h-5 w-5" />
                    Generate API Key
                  </DialogTitle>
                </DialogHeader>
                
                {!generatedKey ? (
                  <>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label>Service Name *</Label>
                        <Input
                          placeholder="e.g., Mobile App, External CRM"
                          value={newKeyData.service_name}
                          onChange={(e) => setNewKeyData({ ...newKeyData, service_name: e.target.value })}
                          data-testid="api-key-service-name"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Description (Optional)</Label>
                        <Input
                          placeholder="Brief description of what this key is for"
                          value={newKeyData.description}
                          onChange={(e) => setNewKeyData({ ...newKeyData, description: e.target.value })}
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
                      <Button 
                        onClick={createApiKey} 
                        disabled={creating || !newKeyData.service_name.trim()}
                        style={{ backgroundColor: THEME_COLOR }}
                        data-testid="confirm-generate-key-btn"
                      >
                        {creating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Key className="h-4 w-4 mr-2" />}
                        Generate Key
                      </Button>
                    </DialogFooter>
                  </>
                ) : (
                  <div className="space-y-4 py-4">
                    <Alert className="border-green-500 bg-green-50">
                      <Shield className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-800">
                        <strong>API Key Generated!</strong> Copy it now. You won't be able to see it again.
                      </AlertDescription>
                    </Alert>
                    
                    <div className="space-y-2">
                      <Label>Your API Key</Label>
                      <div className="flex gap-2">
                        <Input
                          value={generatedKey}
                          readOnly
                          className="font-mono text-sm"
                        />
                        <Button
                          variant="outline"
                          onClick={() => copyToClipboard(generatedKey)}
                        >
                          {copiedKey ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>
                    
                    <Alert className="border-yellow-500 bg-yellow-50">
                      <AlertTriangle className="h-4 w-4 text-yellow-600" />
                      <AlertDescription className="text-yellow-800 text-sm">
                        Store this key securely. It will be hashed and cannot be retrieved later.
                      </AlertDescription>
                    </Alert>
                    
                    <Button 
                      className="w-full" 
                      onClick={() => { setCreateDialogOpen(false); resetForm(); }}
                    >
                      Done
                    </Button>
                  </div>
                )}
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Info Card */}
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-blue-900">API Key Security</h3>
                <p className="text-sm text-blue-700">
                  API keys are hashed and stored securely. You can only see the key once when it's generated.
                  Use these keys for external system integrations like mobile apps or third-party services.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Keys Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              Active API Keys
            </CardTitle>
            <CardDescription>
              {apiKeys.length} key(s) configured
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="h-8 w-8 animate-spin" style={{ color: THEME_COLOR }} />
              </div>
            ) : apiKeys.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 text-center">
                <Key className="h-12 w-12 text-zinc-300 mb-4" />
                <p className="text-zinc-500">No API keys configured</p>
                <p className="text-sm text-zinc-400">Generate your first API key to get started</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Service</TableHead>
                    <TableHead>Key Preview</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Last Used</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {apiKeys.map((key) => (
                    <TableRow key={key.id}>
                      <TableCell className="font-medium">{key.service_name}</TableCell>
                      <TableCell>
                        <code className="px-2 py-1 bg-zinc-100 rounded text-xs">
                          {key.key_prefix}...
                        </code>
                      </TableCell>
                      <TableCell className="text-zinc-600 text-sm max-w-xs truncate">
                        {key.description || '-'}
                      </TableCell>
                      <TableCell>
                        {key.is_active ? (
                          <Badge className="bg-green-100 text-green-800">Active</Badge>
                        ) : (
                          <Badge className="bg-zinc-100 text-zinc-600">Inactive</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-zinc-500">
                        {formatDate(key.created_at)}
                      </TableCell>
                      <TableCell className="text-sm text-zinc-500">
                        {key.last_used_at ? formatDate(key.last_used_at) : 'Never'}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => toggleKeyStatus(key.id, key.is_active)}
                            title={key.is_active ? 'Deactivate' : 'Activate'}
                          >
                            {key.is_active ? (
                              <EyeOff className="h-4 w-4 text-yellow-600" />
                            ) : (
                              <Eye className="h-4 w-4 text-green-600" />
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => deleteApiKey(key.id)}
                            title="Delete Key"
                            className="hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
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
      </div>
    </Layout>
  );
}
