import { useState, useEffect } from 'react';
import { finishedGoodsAPI } from '../../services/api';
import { formatWeight, formatDateTime } from '../../utils/formatters';

export default function FinishedGoodsList() {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        finishedGoodsAPI.list()
            .then(res => setItems(res.data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, []);

    // Group by product
    const grouped = items.reduce((acc, fg) => {
        const key = fg.product_name || 'Unknown';
        if (!acc[key]) acc[key] = { total: 0, items: [] };
        acc[key].total += parseFloat(fg.quantity);
        acc[key].items.push(fg);
        return acc;
    }, {});

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Finished Goods</h1>
                    <p className="page-subtitle">Completed products in stock</p>
                </div>
            </div>

            <div className="stats-grid">
                {Object.entries(grouped).map(([name, data]) => (
                    <div key={name} className="stat-card">
                        <div className="stat-icon green">📦</div>
                        <div className="stat-info">
                            <div className="stat-label">{name}</div>
                            <div className="stat-value">{data.total.toFixed(0)}</div>
                            <div className="stat-change" style={{ color: 'var(--text-muted)' }}>{data.items.length} batches</div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="card">
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th>Batch #</th>
                                <th>Quantity</th>
                                <th>Location</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((fg) => (
                                <tr key={fg.id}>
                                    <td className="font-bold">{fg.product_name}</td>
                                    <td className="font-mono">{fg.batch_number || '—'}</td>
                                    <td className="font-mono">{formatWeight(fg.quantity, 'units')}</td>
                                    <td>{fg.location}</td>
                                    <td>{formatDateTime(fg.created_at)}</td>
                                </tr>
                            ))}
                            {items.length === 0 && !loading && (
                                <tr><td colSpan={5} className="empty-state"><p>No finished goods yet.</p></td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
