import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { bookingAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Loader2, ClipboardList, Phone, MapPin, User, Truck, CheckCircle } from 'lucide-react';
import { formatDateTime, getStatusColor } from '../../lib/utils';
import { toast } from 'sonner';

export default function BranchBookings() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchBookings = async () => {
    try {
      const response = await bookingAPI.getAll();
      setBookings(response.data);
    } catch (error) {
      console.error('Failed to fetch bookings:', error);
      toast.error('Failed to load bookings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, []);

  const handleStatusUpdate = async (bookingId, newStatus) => {
    try {
      await bookingAPI.updateStatus(bookingId, { status: newStatus });
      toast.success('Booking status updated');
      fetchBookings();
    } catch (error) {
      console.error('Failed to update status:', error);
      toast.error('Failed to update status');
    }
  };

  const activeBookings = bookings.filter(b => 
    ['ASSIGNED', 'DISPATCHED', 'IN_PROGRESS'].includes(b.status)
  );
  const completedBookings = bookings.filter(b => b.status === 'COMPLETED');

  return (
    <Layout>
      <div className="space-y-6" data-testid="branch-bookings-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
            Assigned Bookings
          </h1>
          <p className="text-zinc-500 mt-1">
            {activeBookings.length} active, {completedBookings.length} completed
          </p>
        </div>

        {/* Bookings List */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : bookings.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-64 text-center">
              <ClipboardList className="h-12 w-12 text-zinc-300 mb-4" />
              <p className="text-zinc-500">No bookings assigned yet</p>
              <p className="text-sm text-zinc-400">Bookings will appear here when assigned by admin</p>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Active Bookings */}
            {activeBookings.length > 0 && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold font-['Barlow_Condensed']">
                  Active Bookings ({activeBookings.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {activeBookings.map((booking) => (
                    <Card key={booking.id} className="card-interactive">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <Badge className={getStatusColor(booking.status)}>
                            {booking.status}
                          </Badge>
                          <span className="text-xs text-zinc-500">
                            {formatDateTime(booking.created_at)}
                          </span>
                        </div>
                        
                        <h3 className="font-semibold mb-2">{booking.service_type}</h3>
                        
                        <div className="space-y-2 mb-4">
                          <div className="flex items-center gap-2 text-sm">
                            <User className="h-4 w-4 text-zinc-400" />
                            <span>{booking.customer_name}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-zinc-600">
                            <Phone className="h-4 w-4 text-zinc-400" />
                            <span>{booking.customer_phone}</span>
                          </div>
                          <div className="flex items-start gap-2 text-sm text-zinc-600">
                            <MapPin className="h-4 w-4 text-zinc-400 mt-0.5" />
                            <span>{booking.address}</span>
                          </div>
                        </div>

                        {/* Status Update */}
                        <div className="pt-3 border-t border-zinc-100">
                          <Select
                            value={booking.status}
                            onValueChange={(value) => handleStatusUpdate(booking.id, value)}
                          >
                            <SelectTrigger data-testid={`booking-status-${booking.id}`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="ASSIGNED">Assigned</SelectItem>
                              <SelectItem value="DISPATCHED">Dispatched</SelectItem>
                              <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                              <SelectItem value="COMPLETED">Completed</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Completed Bookings */}
            {completedBookings.length > 0 && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold font-['Barlow_Condensed'] text-zinc-600">
                  Completed ({completedBookings.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {completedBookings.map((booking) => (
                    <Card key={booking.id} className="bg-zinc-50">
                      <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-green-100 rounded-lg">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          </div>
                          <div>
                            <p className="font-medium">{booking.service_type}</p>
                            <p className="text-sm text-zinc-500">{booking.customer_name}</p>
                            <p className="text-xs text-zinc-400">
                              Completed: {formatDateTime(booking.completed_at)}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
