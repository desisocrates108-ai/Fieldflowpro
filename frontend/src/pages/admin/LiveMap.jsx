import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { locationAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Loader2, RefreshCcw, Map as MapIcon, User, Clock } from 'lucide-react';
import { formatTime } from '../../lib/utils';
import { toast } from 'sonner';

export default function LiveMapPage() {
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchWorkerLocations = async () => {
    try {
      const response = await locationAPI.getWorkers();
      setWorkers(response.data);
    } catch (error) {
      console.error('Failed to fetch worker locations:', error);
      toast.error('Failed to load worker locations');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchWorkerLocations();
    // Auto refresh every 30 seconds
    const interval = setInterval(fetchWorkerLocations, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchWorkerLocations();
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="live-map-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
              Live Map
            </h1>
            <p className="text-zinc-500 mt-1">
              Real-time worker location tracking
            </p>
          </div>
          <Button 
            variant="outline" 
            onClick={handleRefresh}
            disabled={refreshing}
            data-testid="refresh-map-btn"
          >
            <RefreshCcw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Map Placeholder */}
          <Card className="lg:col-span-2">
            <CardContent className="p-0">
              <div className="h-[500px] bg-zinc-100 rounded-lg flex flex-col items-center justify-center">
                <div className="text-center p-8">
                  <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
                    <MapIcon className="h-8 w-8 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-semibold font-['Barlow_Condensed'] mb-2">
                    Map Integration Required
                  </h3>
                  <p className="text-zinc-500 text-sm mb-4 max-w-md">
                    To enable live map tracking, please configure your Mapbox API token.
                    This feature provides real-time visualization of worker locations.
                  </p>
                  <Badge variant="outline">Mapbox Token Required</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Worker List */}
          <Card>
            <CardHeader>
              <CardTitle className="font-['Barlow_Condensed'] text-lg">Active Workers</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-48">
                  <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                </div>
              ) : workers.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-48 text-center">
                  <User className="h-10 w-10 text-zinc-300 mb-3" />
                  <p className="text-zinc-500 text-sm">No active workers</p>
                  <p className="text-xs text-zinc-400">Workers will appear here when they update their location</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[400px] overflow-y-auto">
                  {workers.map((worker, index) => (
                    <div 
                      key={worker.worker_id || index}
                      className="flex items-center gap-3 p-3 bg-zinc-50 rounded-lg"
                    >
                      <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                        <User className="h-5 w-5 text-green-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{worker.name}</p>
                        <div className="flex items-center gap-2 text-xs text-zinc-500">
                          <Clock className="h-3 w-3" />
                          {formatTime(worker.timestamp)}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-mono text-zinc-500">
                          {worker.latitude?.toFixed(4)}, {worker.longitude?.toFixed(4)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Map Info */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <MapIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold font-['Barlow_Condensed'] mb-1">About Live Tracking</h3>
                <p className="text-sm text-zinc-600">
                  This feature displays real-time locations of field workers on an interactive map. 
                  Workers' positions are updated automatically when they use the mobile app. 
                  To enable full map functionality, a Mapbox API token is required.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
