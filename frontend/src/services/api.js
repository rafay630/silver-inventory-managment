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
    me: () => api.get('/auth/me'),
};

// ─── Items (Raw Materials + Finished Goods) ───
export const itemsAPI = {
    list: (itemType) => api.get('/items', { params: { item_type: itemType || undefined } }),
    get: (id) => api.get(`/items/${id}`),
    create: (data) => api.post('/items', data),
    update: (id, data) => api.put(`/items/${id}`, data),
    getByBarcode: (barcode) => api.get(`/items/barcode/${barcode}`),
};

// ─── Categories ───
export const categoriesAPI = {
    list: () => api.get('/categories'),
    create: (data) => api.post('/categories', data),
};

// ─── UOMs ───
export const uomAPI = {
    list: () => api.get('/uom'),
    create: (data) => api.post('/uom', data),
    listConversions: () => api.get('/uom/conversions'),
    createConversion: (data) => api.post('/uom/conversions', data),
};

// ─── Warehouses ───
export const warehousesAPI = {
    list: () => api.get('/warehouses'),
    create: (data) => api.post('/warehouses', data),
    update: (id, data) => api.put(`/warehouses/${id}`, data),
    getStock: (id) => api.get(`/warehouses/${id}/stock`),
};

// ─── Stock Ledger ───
export const stockLedgerAPI = {
    entries: (params) => api.get('/stock-ledger/entries', { params }),
    balance: (itemId, warehouseId) => api.get('/stock-ledger/balance', { params: { item_id: itemId, warehouse_id: warehouseId || undefined } }),
    balances: (itemType, warehouseId) => api.get('/stock-ledger/balances', { params: { item_type: itemType || undefined, warehouse_id: warehouseId || undefined } }),
};

// ─── Bill of Materials ───
export const bomAPI = {
    list: (productId) => api.get('/bom/', { params: { product_id: productId || undefined } }),
    get: (id) => api.get(`/bom/${id}`),
    create: (data) => api.post('/bom/', data),
    requirements: (bomId, orderQty) => api.get(`/bom/${bomId}/requirements`, { params: { order_qty: orderQty } }),
};

// ─── Production Orders ───
export const productionAPI = {
    list: (status) => api.get('/production-orders/', { params: { status: status || undefined } }),
    get: (id) => api.get(`/production-orders/${id}`),
    create: (data) => api.post('/production-orders/', data),
    start: (id) => api.post(`/production-orders/${id}/start`),
    cancel: (id) => api.post(`/production-orders/${id}/cancel`),
    issueWIP: (orderId, data) => api.post(`/production-orders/${orderId}/wip-issues`, data),
    recordExpense: (orderId, data) => api.post(`/production-orders/${orderId}/expenses`, data),
    complete: (orderId, data) => api.post(`/production-orders/${orderId}/complete`, data),
};

// ─── Sales ───
export const salesAPI = {
    list: (status) => api.get('/sales/', { params: { status: status || undefined } }),
    get: (id) => api.get(`/sales/${id}`),
    create: (data) => api.post('/sales/', data),
};

// ─── Accounting ───
export const accountingAPI = {
    // Chart of Accounts
    listAccounts: (accountType) => api.get('/accounting/accounts', { params: { account_type: accountType || undefined } }),
    createAccount: (data) => api.post('/accounting/accounts', data),
    // Journal Entries
    listJournalEntries: (params) => api.get('/accounting/journal-entries', { params }),
    getJournalEntry: (id) => api.get(`/accounting/journal-entries/${id}`),
    createJournalEntry: (data) => api.post('/accounting/journal-entries', data),
    // Financial Reports
    trialBalance: (asOfDate) => api.get('/accounting/trial-balance', { params: { as_of_date: asOfDate || undefined } }),
    profitAndLoss: (fromDate, toDate) => api.get('/accounting/profit-and-loss', { params: { from_date: fromDate, to_date: toDate } }),
    balanceSheet: (asOfDate) => api.get('/accounting/balance-sheet', { params: { as_of_date: asOfDate || undefined } }),
};

// ─── Pricing / Sales Catalog ───
export const pricingAPI = {
    getCatalog: () => api.get('/pricing/catalog'),
    setPricing: (data) => api.post('/pricing', data),
    publish: (id) => api.post(`/pricing/${id}/publish`),
    unpublish: (id) => api.post(`/pricing/${id}/unpublish`),
    getListed: () => api.get('/pricing/listed'),
};

// ─── Reports ───
export const reportsAPI = {
    stockLedger: (params) => api.get('/reports/stock-ledger', { params }),
    inventoryValuation: (warehouseId) => api.get('/reports/inventory-valuation', { params: { warehouse_id: warehouseId || undefined } }),
    productionCostSheet: (orderId) => api.get(`/reports/production-cost-sheet/${orderId}`),
    wipSummary: () => api.get('/reports/wip-summary'),
    materialConsumption: (fromDate, toDate) => api.get('/reports/material-consumption', { params: { from_date: fromDate || undefined, to_date: toDate || undefined } }),
    trialBalance: (asOfDate) => api.get('/reports/trial-balance', { params: { as_of_date: asOfDate || undefined } }),
    profitAndLoss: (fromDate, toDate) => api.get('/reports/profit-and-loss', { params: { from_date: fromDate, to_date: toDate } }),
    balanceSheet: (asOfDate) => api.get('/reports/balance-sheet', { params: { as_of_date: asOfDate || undefined } }),
};

export default api;
