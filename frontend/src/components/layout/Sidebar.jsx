import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    HiOutlineViewGrid, HiOutlineCube, HiOutlineOfficeBuilding,
    HiOutlineDocumentText, HiOutlineCog, HiOutlineClipboardList,
    HiOutlineChartBar, HiOutlineCurrencyDollar, HiOutlineCalculator,
    HiOutlineShoppingCart, HiOutlineLogout,
} from 'react-icons/hi';

export default function Sidebar() {
    const { user, logout } = useAuth();

    const navSections = [
        {
            title: 'Overview',
            items: [
                { path: '/', icon: HiOutlineViewGrid, label: 'Dashboard' },
            ],
        },
        {
            title: 'Inventory',
            items: [
                { path: '/items', icon: HiOutlineCube, label: 'Items' },
                { path: '/warehouses', icon: HiOutlineOfficeBuilding, label: 'Warehouses' },
                { path: '/stock-ledger', icon: HiOutlineDocumentText, label: 'Stock Ledger' },
            ],
        },
        {
            title: 'Manufacturing',
            items: [
                { path: '/bom', icon: HiOutlineClipboardList, label: 'Bill of Materials' },
                { path: '/production', icon: HiOutlineCog, label: 'Production Orders' },
            ],
        },
        {
            title: 'Sales & Finance',
            items: [
                { path: '/sales', icon: HiOutlineShoppingCart, label: 'Sales Orders' },
                { path: '/accounting', icon: HiOutlineCalculator, label: 'Accounting' },
            ],
        },
        {
            title: 'Analytics',
            items: [
                { path: '/reports', icon: HiOutlineChartBar, label: 'Reports' },
            ],
        },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-logo">SI</div>
                <div className="sidebar-brand">
                    <h1>Silver Inventory</h1>
                    <span>Manufacturing ERP</span>
                </div>
            </div>

            <nav className="sidebar-nav">
                {navSections.map((section) => (
                    <div key={section.title} className="nav-section">
                        <div className="nav-section-title">{section.title}</div>
                        {section.items.map((item) => (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                className={({ isActive }) =>
                                    `nav-link ${isActive ? 'active' : ''}`
                                }
                                end={item.path === '/'}
                            >
                                <item.icon />
                                {item.label}
                            </NavLink>
                        ))}
                    </div>
                ))}
            </nav>

            <div className="sidebar-footer">
                <div className="sidebar-user">
                    <div className="sidebar-avatar">
                        {user?.username?.charAt(0)?.toUpperCase() || 'U'}
                    </div>
                    <div className="sidebar-user-info">
                        <div className="sidebar-user-name">{user?.username || 'User'}</div>
                        <div className="sidebar-user-role">{user?.role?.replace('_', ' ') || 'Guest'}</div>
                    </div>
                    <button
                        onClick={logout}
                        className="nav-link"
                        style={{ width: 'auto', padding: '4px' }}
                        title="Logout"
                    >
                        <HiOutlineLogout />
                    </button>
                </div>
            </div>
        </aside>
    );
}
