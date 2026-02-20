import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
    baseURL: API_BASE,
    headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle 401 globally — but don't redirect if already on login page
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && !window.location.pathname.includes('/login')) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// ─── Auth ───
export const authAPI = {
    login: (data) => api.post('/auth/login', data),
    register: (data) => api.post('/auth/register', data),
    me: () => api.get('/auth/me'),
};

// ─── Users ───
export const usersAPI = {
    list: () => api.get('/users/'),
    update: (id, data) => api.patch(`/users/${id}`, data),
    deactivate: (id) => api.delete(`/users/${id}`),
};

// ─── Suppliers ───
export const suppliersAPI = {
    list: () => api.get('/suppliers/'),
    create: (data) => api.post('/suppliers/', data),
    update: (id, data) => api.put(`/suppliers/${id}`, data),
    deactivate: (id) => api.delete(`/suppliers/${id}`),
};

// ─── Raw Materials ───
export const rawMaterialsAPI = {
    list: () => api.get('/raw-materials/'),
    create: (data) => api.post('/raw-materials/', data),
    purchase: (data) => api.post('/raw-materials/purchase', data),
    adjust: (data) => api.post('/raw-materials/adjust', data),
};

// ─── Products ───
export const productsAPI = {
    list: () => api.get('/products/'),
    create: (data) => api.post('/products/', data),
    update: (id, data) => api.put(`/products/${id}`, data),
    getBOM: (id) => api.get(`/products/${id}/bom`),
    addBOM: (id, data) => api.post(`/products/${id}/bom`, data),
    updateBOM: (productId, bomId, data) => api.put(`/products/${productId}/bom/${bomId}`, data),
};

// ─── Production ───
export const productionAPI = {
    listBatches: (status) => api.get('/production/batches', { params: { status } }),
    createBatch: (data) => api.post('/production/batches', data),
    getBatch: (id) => api.get(`/production/batches/${id}`),
    completeBatch: (id, data) => api.patch(`/production/batches/${id}/complete`, data),
    cancelBatch: (id) => api.patch(`/production/batches/${id}/cancel`),
};

// ─── WIP ───
export const wipAPI = {
    list: () => api.get('/wip'),
    getByBatch: (batchId) => api.get(`/wip/${batchId}`),
    updateStatus: (id, data) => api.patch(`/wip/${id}/status`, data),
};

// ─── Finished Goods ───
export const finishedGoodsAPI = {
    list: () => api.get('/finished-goods'),
};

// ─── Transactions ───
export const transactionsAPI = {
    list: (params) => api.get('/transactions', { params }),
};

// ─── Reports ───
export const reportsAPI = {
    stockReport: () => api.get('/reports/raw-material-stock'),
    wastageReport: () => api.get('/reports/wastage'),
    efficiencyReport: () => api.get('/reports/production-efficiency'),
    wipSummary: () => api.get('/reports/wip-summary'),
    batchHistory: () => api.get('/reports/batch-history'),
    consumptionVariance: () => api.get('/reports/consumption-variance'),
};

export default api;
