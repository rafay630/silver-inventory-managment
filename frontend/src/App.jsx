import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import AppLayout from './components/layout/AppLayout';
import Login from './pages/auth/Login';
import Dashboard from './pages/Dashboard';
import ItemList from './pages/inventory/ItemList';
import WarehouseList from './pages/inventory/WarehouseList';
import StockLedger from './pages/inventory/StockLedger';
import BOMList from './pages/manufacturing/BOMList';
import ProductionOrders from './pages/manufacturing/ProductionOrders';
import SalesOrders from './pages/sales/SalesOrders';
import Accounting from './pages/accounting/Accounting';
import Reports from './pages/reports/Reports';

function ProtectedRoute({ children }) {
    const { user, loading } = useAuth();
    if (loading) return <div className="empty-state"><p>Loading...</p></div>;
    if (!user) return <Navigate to="/login" replace />;
    return children;
}

function AppRoutes() {
    const { user } = useAuth();

    return (
        <Routes>
            <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />

            <Route
                element={
                    <ProtectedRoute>
                        <AppLayout />
                    </ProtectedRoute>
                }
            >
                <Route path="/" element={<Dashboard />} />
                <Route path="/items" element={<ItemList />} />
                <Route path="/warehouses" element={<WarehouseList />} />
                <Route path="/stock-ledger" element={<StockLedger />} />
                <Route path="/bom" element={<BOMList />} />
                <Route path="/production" element={<ProductionOrders />} />
                <Route path="/sales" element={<SalesOrders />} />
                <Route path="/accounting" element={<Accounting />} />
                <Route path="/reports" element={<Reports />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
}

export default function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <AppRoutes />
            </AuthProvider>
        </BrowserRouter>
    );
}
