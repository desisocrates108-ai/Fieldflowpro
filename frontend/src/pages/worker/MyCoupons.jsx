import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { couponAPI } from '../../lib/api';
import { Card, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Loader2, Ticket, Phone, User, Clock, MapPin } from 'lucide-react';
import { formatDateTime, getStatusColor } from '../../lib/utils';
import { toast } from 'sonner';

export default function MyCouponsPage() {
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchCoupons = async () => {
    try {
      const response = await couponAPI.getAll();
      setCoupons(response.data);
    } catch (error) {
      console.error('Failed to fetch coupons:', error);
      toast.error('Failed to load coupons');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCoupons();
  }, []);

  return (
    <Layout>
      <div className="space-y-6" data-testid="my-coupons-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
            My Coupons
          </h1>
          <p className="text-zinc-500 mt-1">
            Coupons you've issued ({coupons.length} total)
          </p>
        </div>

        {/* Coupons List */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : coupons.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-64 text-center">
              <Ticket className="h-12 w-12 text-zinc-300 mb-4" />
              <p className="text-zinc-500">No coupons issued yet</p>
              <p className="text-sm text-zinc-400">Issue your first coupon to see it here</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {coupons.map((coupon) => (
              <Card key={coupon.id} className="card-interactive">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <code className="text-lg font-bold font-mono text-blue-600">
                        {coupon.code}
                      </code>
                      <Badge className={`ml-2 ${getStatusColor(coupon.status)}`}>
                        {coupon.status}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <User className="h-4 w-4 text-zinc-400" />
                      <span>{coupon.customer_name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-zinc-600">
                      <Phone className="h-4 w-4 text-zinc-400" />
                      <span>{coupon.customer_phone}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-zinc-500">
                      <Clock className="h-4 w-4 text-zinc-400" />
                      <span>{formatDateTime(coupon.issued_at)}</span>
                    </div>
                    {coupon.latitude && coupon.longitude && (
                      <div className="flex items-center gap-2 text-xs text-zinc-400">
                        <MapPin className="h-3 w-3" />
                        <span className="font-mono">
                          {coupon.latitude.toFixed(4)}, {coupon.longitude.toFixed(4)}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {coupon.redeemed_at && (
                    <div className="mt-3 pt-3 border-t border-zinc-100">
                      <p className="text-xs text-green-600">
                        Redeemed: {formatDateTime(coupon.redeemed_at)}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
