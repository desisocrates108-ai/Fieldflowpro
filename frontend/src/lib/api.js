import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE}/auth/refresh`, null, {
            params: { refresh_token: refreshToken }
          });
          
          const { access_token, refresh_token: newRefreshToken } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  refresh: (refreshToken) => api.post('/auth/refresh', null, { params: { refresh_token: refreshToken } }),
  me: () => api.get('/auth/me'),
};

// Attendance APIs
export const attendanceAPI = {
  punchIn: (data) => api.post('/attendance/punch-in', data),
  punchOut: (data) => api.post('/attendance/punch-out', data),
  getToday: () => api.get('/attendance/today'),
};

// Coupon APIs
export const couponAPI = {
  create: (data) => api.post('/coupons/create', data),
  issue: (data) => api.post('/coupons/issue', data),
  getAll: (status, pendingOnly) => api.get('/coupons', { params: { status, pending_only: pendingOnly } }),
  getById: (id) => api.get(`/coupons/${id}`),
  getSummary: () => api.get('/coupons/summary'),
  verify: (id, data) => api.patch(`/coupons/${id}/verify`, data),
  requestOTP: (couponCode, phone) => api.post('/coupons/request-otp', { coupon_code: couponCode, phone }),
  verifyOTP: (couponCode, phone, otp) => api.post('/coupons/verify-otp', { coupon_code: couponCode, phone, otp }),
};

// Booking APIs
export const bookingAPI = {
  create: (data) => api.post('/bookings', data),
  getAll: (status, branchId) => api.get('/bookings', { params: { status, branch_id: branchId } }),
  getById: (id) => api.get(`/bookings/${id}`),
  updateStatus: (id, data) => api.patch(`/bookings/${id}/status`, data),
  assignBranch: (id, branchId) => api.patch(`/bookings/${id}/assign`, { branch_id: branchId }),
};

// Branch APIs
export const branchAPI = {
  create: (data) => api.post('/branches', data),
  getAll: () => api.get('/branches'),
  getNearest: (latitude, longitude) => api.get('/branches/nearest', { params: { latitude, longitude } }),
};

// Task APIs
export const taskAPI = {
  create: (data) => api.post('/tasks', data),
  getAll: () => api.get('/tasks'),
  update: (id, data) => api.patch(`/tasks/${id}`, data),
};

// Location APIs
export const locationAPI = {
  update: (data) => api.post('/location/update', data),
  getWorkers: () => api.get('/location/workers'),
};

// Dashboard APIs
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getAdminStats: () => api.get('/admin/dashboard/stats'),
};

// Intelligence APIs (Elite v4.0)
export const intelligenceAPI = {
  // Real-time metrics
  getRealtimeMetrics: () => api.get('/intelligence/realtime-metrics'),
  
  // Fraud Detection
  getFraudAlerts: (status = 'ACTIVE') => api.get('/intelligence/fraud-alerts', { params: { status } }),
  resolveFraudAlert: (id, notes) => api.patch(`/intelligence/fraud-alerts/${id}/resolve`, null, { params: { notes } }),
  dismissFraudAlert: (id, notes) => api.patch(`/intelligence/fraud-alerts/${id}/dismiss`, null, { params: { notes } }),
  runFraudScan: () => api.post('/intelligence/scan-fraud'),
  
  // Worker Performance
  getWorkerScores: () => api.get('/intelligence/worker-scores'),
  getWorkerScore: (id) => api.get(`/intelligence/worker-scores/${id}`),
  
  // Inactive Workers
  getInactiveWorkers: () => api.get('/intelligence/inactive-workers'),
  
  // Area Intelligence
  getAreaIntelligence: () => api.get('/intelligence/area-intelligence'),
};

// Admin APIs
export const adminAPI = {
  getDashboardStats: () => api.get('/admin/dashboard/stats'),
  getInactivityAlerts: (status) => api.get('/admin/inactivity-alerts', { params: { status } }),
  resolveInactivityAlert: (id, notes) => api.patch(`/admin/inactivity-alerts/${id}/resolve`, null, { params: { notes } }),
  dismissInactivityAlert: (id, notes) => api.patch(`/admin/inactivity-alerts/${id}/dismiss`, null, { params: { notes } }),
  getSpoofingAlerts: () => api.get('/admin/spoofing-alerts'),
  
  // Worker management
  createWorker: (data) => api.post('/admin/workers', data),
  updateWorker: (id, data) => api.patch(`/admin/workers/${id}`, data),
  disableWorker: (id) => api.post(`/admin/workers/${id}/disable`),
  enableWorker: (id) => api.post(`/admin/workers/${id}/enable`),
  deleteWorker: (id) => api.delete(`/admin/workers/${id}`),
  resetWorkerPassword: (id, password) => api.post(`/admin/workers/${id}/reset-password`, { new_password: password }),
  addWorkerAdvance: (id, data) => api.post(`/workers/${id}/advance`, data),
  
  // CRE & Encashments
  getCRERemarks: () => api.get('/admin/cre-remarks'),
  getEncashments: () => api.get('/admin/encashments'),
};

// Worker APIs
export const workerAPI = {
  getAll: () => api.get('/workers'),
  getById: (id) => api.get(`/workers/${id}`),
  update: (id, data) => api.patch(`/workers/${id}`, { params: data }),
  updatePossession: (id, count) => api.patch(`/workers/${id}/coupons`, { coupon_possession_count: count }),
};

// File Upload
export const uploadAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export default api;
