import { useState, useEffect } from 'react';
import { wipAPI } from '../../services/api';
import { formatWeight, formatDateTime, statusColor } from '../../utils/formatters';

export default function WIPTracker() {
    const [wipItems, setWipItems] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const res = await wipAPI.list();
            setWipItems(res.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const statusCounts = {
        in_process: wipItems.filter(w => w.status === 'in_process').length,
        completed: wipItems.filter(w => w.status === 'completed').length,
        rejected: wipItems.filter(w => w.status === 'rejected').length,
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Work In Progress</h1>
                    <p className="page-subtitle">Track material currently in production</p>
                </div>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon blue">🔄</div>
                    <div className="stat-info">
                        <div className="stat-label">In Process</div>
                        <div className="stat-value">{statusCounts.in_process}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon green">✓</div>
                    <div className="stat-info">
                        <div className="stat-label">Completed</div>
                        <div className="stat-value">{statusCounts.completed}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon red">✗</div>
                    <div className="stat-info">
                        <div className="stat-label">Rejected</div>
                        <div className="stat-value">{statusCounts.rejected}</div>
                    </div>
                </div>
            </div>

            <div className="card">
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Batch #</th>
                                <th>Product</th>
                                <th>Quantity</th>
                                <th>Status</th>
                                <th>Updated</th>
                                <th>Created</th>
                            </tr>
                        </thead>
                        <tbody>
                            {wipItems.map((w) => (
                                <tr key={w.id}>
                                    <td className="font-bold font-mono">{w.batch_number}</td>
                                    <td>{w.product_name}</td>
                                    <td className="font-mono">{formatWeight(w.quantity, 'units')}</td>
                                    <td><span className={`badge ${statusColor(w.status)}`}>{w.status.replace('_', ' ')}</span></td>
                                    <td>{formatDateTime(w.updated_at)}</td>
                                    <td>{formatDateTime(w.created_at)}</td>
                                </tr>
                            ))}
                            {wipItems.length === 0 && !loading && (
                                <tr><td colSpan={6} className="empty-state"><p>No WIP items found.</p></td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
