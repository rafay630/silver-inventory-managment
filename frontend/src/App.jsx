import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import AppLayout from './components/layout/AppLayout';
import Login from './pages/auth/Login';
import Dashboard from './pages/Dashboard';
import RawMaterialList from './pages/raw-materials/RawMaterialList';
import ProductList from './pages/products/ProductList';
import SupplierList from './pages/suppliers/SupplierList';
import BatchList from './pages/production/BatchList';
import WIPTracker from './pages/wip/WIPTracker';
import FinishedGoodsList from './pages/finished-goods/FinishedGoodsList';
import Reports from './pages/reports/Reports';
import Transactions from './pages/transactions/Transactions';

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
                <Route path="/raw-materials" element={<RawMaterialList />} />
                <Route path="/products" element={<ProductList />} />
                <Route path="/suppliers" element={<SupplierList />} />
                <Route path="/production" element={<BatchList />} />
                <Route path="/wip" element={<WIPTracker />} />
                <Route path="/finished-goods" element={<FinishedGoodsList />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/transactions" element={<Transactions />} />
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
