import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function AppLayout() {
    return (
        <div className="app-layout">
            <Sidebar />
            <div className="main-content" style={{ marginLeft: 'var(--sidebar-width)' }}>
                <div className="page-content">
                    <Outlet />
                </div>
            </div>
        </div>
    );
}
