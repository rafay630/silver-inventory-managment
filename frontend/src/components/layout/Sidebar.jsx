import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    HiOutlineViewGrid, HiOutlineCube, HiOutlineBeaker,
    HiOutlineCog, HiOutlineClipboardList, HiOutlineChartBar,
    HiOutlineArchive, HiOutlineUsers, HiOutlineTruck,
    HiOutlineLogout, HiOutlineDocumentReport,
} from 'react-icons/hi';

export default function Sidebar() {
    const { user, logout } = useAuth();
    const location = useLocation();

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
                { path: '/raw-materials', icon: HiOutlineCube, label: 'Raw Materials' },
                { path: '/products', icon: HiOutlineBeaker, label: 'Products & BOM' },
                { path: '/suppliers', icon: HiOutlineTruck, label: 'Suppliers' },
            ],
        },
        {
            title: 'Production',
            items: [
                { path: '/production', icon: HiOutlineCog, label: 'Production Batches' },
                { path: '/wip', icon: HiOutlineClipboardList, label: 'Work In Progress' },
                { path: '/finished-goods', icon: HiOutlineArchive, label: 'Finished Goods' },
            ],
        },
        {
            title: 'Analytics',
            items: [
                { path: '/reports', icon: HiOutlineChartBar, label: 'Reports' },
                { path: '/transactions', icon: HiOutlineDocumentReport, label: 'Audit Trail' },
            ],
        },
    ];

    // Admin-only section
    if (user?.role === 'admin') {
        navSections.push({
            title: 'Admin',
            items: [
                { path: '/users', icon: HiOutlineUsers, label: 'User Management' },
            ],
        });
    }

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
