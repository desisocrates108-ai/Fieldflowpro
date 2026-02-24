import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { MapPin, Eye, EyeOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const THEME_COLOR = '#ED1C24';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }
    
    setLoading(true);
    
    try {
      const user = await login(email, password);
      toast.success(`Welcome back, ${user.name}!`);
      
      // Redirect based on role
      switch (user.role) {
        case 'admin':
          navigate('/admin');
          break;
        case 'cre':
          navigate('/cre');
          break;
        case 'worker':
          navigate('/worker');
          break;
        case 'branch':
          navigate('/branch');
          break;
        default:
          navigate('/customer');
      }
    } catch (error) {
      console.error('Login error:', error);
      toast.error(error.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Image */}
      <div className="hidden lg:flex lg:w-1/2 relative">
        <img 
          src="https://images.unsplash.com/photo-1648747640271-e0270e2dac1c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwxfHxmaWVsZCUyMHNlcnZpY2UlMjB0ZWNobmljaWFuJTIwdGFibGV0fGVufDB8fHx8MTc3MTMwMjg1NXww&ixlib=rb-4.1.0&q=85"
          alt="Field technician" 
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0" style={{ background: `linear-gradient(to right, rgba(0,0,0,0.7), ${THEME_COLOR}30)` }} />
        <div className="relative z-10 flex flex-col justify-end p-12 text-white">
          <h1 className="text-5xl font-bold font-['Barlow_Condensed'] mb-4" style={{ color: THEME_COLOR }}>
            FieldFlow Pro
          </h1>
          <p className="text-xl text-white/80 max-w-md">
            Pan-India Field Revenue Intelligence System for streamlined operations, GPS tracking, and workforce coordination.
          </p>
        </div>
      </div>
      
      {/* Right side - Login form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-zinc-50">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: THEME_COLOR }}>
              <MapPin className="h-7 w-7 text-white" />
            </div>
            <span className="text-3xl font-bold font-['Barlow_Condensed']" style={{ color: THEME_COLOR }}>FieldFlow Pro</span>
          </div>
          
          <Card className="border-0 shadow-lg">
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl font-['Barlow_Condensed']">Sign in</CardTitle>
              <CardDescription>
                Enter your credentials to access your account
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="name@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    data-testid="login-email-input"
                    className="h-11"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      data-testid="login-password-input"
                      className="h-11 pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-700"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>
                <Button 
                  type="submit" 
                  className="w-full h-11"
                  style={{ backgroundColor: THEME_COLOR }}
                  disabled={loading}
                  data-testid="login-submit-btn"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Signing in...
                    </>
                  ) : (
                    'Sign in'
                  )}
                </Button>
              </form>
              
              <div className="mt-6 text-center text-sm text-zinc-500">
                Contact your administrator if you need an account.
              </div>
            </CardContent>
          </Card>
          
          {/* Demo credentials - styled with theme color */}
          <div className="mt-6 p-4 rounded-lg" style={{ backgroundColor: `${THEME_COLOR}10`, border: `1px solid ${THEME_COLOR}30` }}>
            <p className="text-sm font-medium mb-2" style={{ color: THEME_COLOR }}>Demo Credentials:</p>
            <p className="text-xs text-zinc-600">Admin: testadmin@fieldflow.com / admin123</p>
            <p className="text-xs text-zinc-600">Worker: testworker@fieldflow.com / worker123</p>
            <p className="text-xs text-zinc-600">Branch: testbranch@fieldflow.com / branch123</p>
            <p className="text-xs text-zinc-600">CRE: testcre@fieldflow.com / cre123</p>
          </div>
        </div>
      </div>
    </div>
  );
}
