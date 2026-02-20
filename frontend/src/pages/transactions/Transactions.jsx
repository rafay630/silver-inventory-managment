import { useState, useEffect } from 'react';
import { transactionsAPI } from '../../services/api';
import { formatWeight, formatDateTime } from '../../utils/formatters';

export default function Transactions() {
    const [txns, setTxns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [typeFilter, setTypeFilter] = useState('');

    useEffect(() => { loadData(); }, [typeFilter]);

    const loadData = async () => {
        try {
            const res = await transactionsAPI.list({ limit: 100, transaction_type: typeFilter || undefined });
            setTxns(res.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const typeColors = {
        PURCHASE: 'badge-green',
        ISSUE_TO_PROD: 'badge-blue',
        WIP_IN: 'badge-blue',
        WIP_OUT: 'badge-purple',
        FG_IN: 'badge-green',
        ADJUSTMENT: 'badge-amber',
        RETURN_FROM_PROD: 'badge-silver',
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Audit Trail</h1>
                    <p className="page-subtitle">Complete inventory movement log</p>
                </div>
            </div>

            <div className="filter-bar">
                <select className="form-select" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
                    <option value="">All Types</option>
                    <option value="PURCHASE">Purchase</option>
                    <option value="ISSUE_TO_PROD">Issue to Production</option>
                    <option value="WIP_IN">WIP In</option>
                    <option value="WIP_OUT">WIP Out</option>
                    <option value="FG_IN">Finished Goods In</option>
                    <option value="ADJUSTMENT">Adjustment</option>
                    <option value="RETURN_FROM_PROD">Return from Production</option>
                </select>
            </div>

            <div className="card">
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Type</th>
                                <th>Material / Product</th>
                                <th>Quantity</th>
                                <th>Reference</th>
                                <th>Notes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {txns.map(t => (
                                <tr key={t.id}>
                                    <td className="font-mono" style={{ fontSize: 'var(--font-xs)' }}>{formatDateTime(t.created_at)}</td>
                                    <td><span className={`badge ${typeColors[t.transaction_type] || 'badge-silver'}`}>{t.transaction_type.replace(/_/g, ' ')}</span></td>
                                    <td>{t.raw_material_name || t.product_name || '—'}</td>
                                    <td className="font-mono font-bold">{formatWeight(t.quantity, t.unit || 'g')}</td>
                                    <td className="font-mono">{t.reference_number || '—'}</td>
                                    <td className="text-muted" style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.notes || '—'}</td>
                                </tr>
                            ))}
                            {txns.length === 0 && !loading && (
                                <tr><td colSpan={6} className="empty-state"><p>No transactions found.</p></td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
