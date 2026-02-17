import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { bookingAPI, branchAPI } from '../../lib/api';
import { Card, CardContent } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog';
import { Loader2, Search, ClipboardList, Building2, Phone, MapPin } from 'lucide-react';
import { formatDateTime, getStatusColor } from '../../lib/utils';
import { toast } from 'sonner';

export default function BookingsPage() {
  const [bookings, setBookings] = useState([]);
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState('');

  const fetchData = async () => {
    try {
      const [bookingsRes, branchesRes] = await Promise.all([
        bookingAPI.getAll(statusFilter === 'all' ? null : statusFilter),
        branchAPI.getAll()
      ]);
      setBookings(bookingsRes.data);
      setBranches(branchesRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to load bookings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const handleAssignBranch = async () => {
    if (!selectedBooking || !selectedBranch) return;

    try {
      await bookingAPI.assignBranch(selectedBooking.id, selectedBranch);
      toast.success('Branch assigned successfully');
      setAssignDialogOpen(false);
      setSelectedBooking(null);
      setSelectedBranch('');
      fetchData();
    } catch (error) {
      console.error('Failed to assign branch:', error);
      toast.error('Failed to assign branch');
    }
  };

  const handleUpdateStatus = async (bookingId, status) => {
    try {
      await bookingAPI.updateStatus(bookingId, { status });
      toast.success('Booking status updated');
      fetchData();
    } catch (error) {
      console.error('Failed to update status:', error);
      toast.error('Failed to update status');
    }
  };

  const filteredBookings = bookings.filter(booking => 
    booking.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    booking.customer_phone.includes(searchQuery) ||
    booking.address.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Layout>
      <div className="space-y-6" data-testid="bookings-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
            Bookings
          </h1>
          <p className="text-zinc-500 mt-1">
            Manage service bookings and assignments
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <Input
              placeholder="Search bookings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
              data-testid="search-bookings-input"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40" data-testid="status-filter-select">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="PENDING">Pending</SelectItem>
              <SelectItem value="ASSIGNED">Assigned</SelectItem>
              <SelectItem value="DISPATCHED">Dispatched</SelectItem>
              <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
              <SelectItem value="COMPLETED">Completed</SelectItem>
              <SelectItem value="CANCELLED">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Bookings Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : filteredBookings.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <ClipboardList className="h-12 w-12 text-zinc-300 mb-4" />
                <p className="text-zinc-500">No bookings found</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer</TableHead>
                    <TableHead>Service</TableHead>
                    <TableHead>Address</TableHead>
                    <TableHead>Branch</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredBookings.map((booking) => (
                    <TableRow key={booking.id} className="table-row-hover">
                      <TableCell>
                        <div>
                          <p className="font-medium">{booking.customer_name}</p>
                          <p className="text-sm text-zinc-500 flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {booking.customer_phone}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>{booking.service_type}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-zinc-600 max-w-48 truncate">
                          <MapPin className="h-4 w-4 shrink-0" />
                          {booking.address}
                        </div>
                      </TableCell>
                      <TableCell>
                        {booking.branch_id ? (
                          <div className="flex items-center gap-1">
                            <Building2 className="h-4 w-4 text-zinc-400" />
                            {branches.find(b => b.id === booking.branch_id)?.name || 'Unknown'}
                          </div>
                        ) : (
                          <span className="text-zinc-400">Unassigned</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(booking.status)}>
                          {booking.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-zinc-600">
                        {formatDateTime(booking.created_at)}
                      </TableCell>
                      <TableCell>
                        {booking.status === 'PENDING' && (
                          <Dialog open={assignDialogOpen && selectedBooking?.id === booking.id} onOpenChange={(open) => {
                            setAssignDialogOpen(open);
                            if (open) setSelectedBooking(booking);
                          }}>
                            <DialogTrigger asChild>
                              <Button size="sm" variant="outline" data-testid={`assign-branch-btn-${booking.id}`}>
                                Assign Branch
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle className="font-['Barlow_Condensed']">Assign Branch</DialogTitle>
                              </DialogHeader>
                              <div className="space-y-4">
                                <p className="text-sm text-zinc-600">
                                  Select a branch for this booking
                                </p>
                                <Select value={selectedBranch} onValueChange={setSelectedBranch}>
                                  <SelectTrigger data-testid="select-branch">
                                    <SelectValue placeholder="Select branch" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {branches.map((branch) => (
                                      <SelectItem key={branch.id} value={branch.id}>
                                        {branch.name}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                                <Button 
                                  onClick={handleAssignBranch}
                                  className="w-full"
                                  disabled={!selectedBranch}
                                  data-testid="confirm-assign-btn"
                                >
                                  Confirm Assignment
                                </Button>
                              </div>
                            </DialogContent>
                          </Dialog>
                        )}
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
