import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Request interceptor to add authorization token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const authService = {
  login: async (formData: FormData) => {
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  register: async (userData: any) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  forgotPassword: async (email: string) => {
    const response = await api.post('/auth/forgot-password', { email });
    return response.data;
  },
};

export const blueprintService = {
  upload: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/blueprints/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  list: async () => {
    const response = await api.get('/blueprints/');
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get(`/blueprints/${id}`);
    return response.data;
  },
  analyze: async (id: number) => {
    const response = await api.post(`/blueprints/${id}/analyze`);
    return response.data;
  },
  getImageUrl: (id: number) => {
    const token = localStorage.getItem('token');
    return `${API_BASE_URL}/blueprints/${id}/image?token=${token || ''}`;
  },
  getReportUrl: (id: number) => {
    return `${API_BASE_URL}/blueprints/${id}/report`;
  },
};

export const rulesService = {
  list: async () => {
    const response = await api.get('/rules/');
    return response.data;
  },
  update: async (key: string, value: number) => {
    const response = await api.put(`/rules/${key}`, { current_value: value });
    return response.data;
  },
};

export const analyticsService = {
  dashboard: async () => {
    const response = await api.get('/analytics/dashboard');
    return response.data;
  },
};

export default api;
