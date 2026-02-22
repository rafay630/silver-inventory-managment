import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { pricingAPI } from '../../services/api';
import { formatCurrency, formatNumber } from '../../utils/formatters';

export default function SalesCatalog() {
    const { user } = useAuth();
    const [catalog, setCatalog] = useState([]);
    const [loading, setLoading] = useState(true);
    const [margins, setMargins] = useState({});  // local margin edits
    const [saving, setSaving] = useState({});     // per-row saving state

    const isAdmin = user?.role === 'admin';

    useEffect(() => { loadCatalog(); }, []);

    const loadCatalog = async () => {
        try {
            const res = await pricingAPI.getCatalog();
            setCatalog(res.data);
            // Pre-fill local margins from existing data
            const m = {};
            res.data.forEach(item => {
                if (item.profit_margin_percent != null) {
                    m[item.item_id] = item.profit_margin_percent;
                }
            });
            setMargins(m);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const handleMarginChange = (itemId, value) => {
        setMargins({ ...margins, [itemId]: value });
    };

    const computePrice = (wac, margin) => {
        const m = parseFloat(margin) || 0;
        return wac * (1 + m / 100);
    };

    const handleSaveMargin = async (item) => {
        const margin = parseFloat(margins[item.item_id]);
        if (isNaN(margin) || margin < 0 || margin > 500) {
            alert('Margin must be between 0% and 500%');
            return;
        }
        setSaving({ ...saving, [item.item_id]: true });
        try {
            await pricingAPI.setPricing({
                item_id: item.item_id,
                profit_margin_percent: margin,
            });
            await loadCatalog();
        } catch (err) {
            alert(err.response?.data?.detail || 'Error saving margin');
        }
        setSaving({ ...saving, [item.item_id]: false });
    };

    const handlePublish = async (item) => {
        if (!item.pricing_id) {
            alert('Set a margin first before publishing.');
            return;
        }
        try {
            await pricingAPI.publish(item.pricing_id);
            await loadCatalog();
        } catch (err) {
            alert(err.response?.data?.detail || 'Error publishing');
        }
    };

    const handleUnpublish = async (item) => {
        try {
            await pricingAPI.unpublish(item.pricing_id);
            await loadCatalog();
        } catch (err) {
            alert(err.response?.data?.detail || 'Error unpublishing');
        }
    };

    const totalFG = catalog.length;
    const listed = catalog.filter(c => c.status === 'listed').length;
    const draft = totalFG - listed;

    if (loading) return <div className="card" style={{ padding: 'var(--space-8)', textAlign: 'center' }}>Loading catalog...</div>;

    return (
        <div>
            {/* Stat Bar */}
            <div className="stats-grid" style={{ marginBottom: 'var(--space-6)' }}>
                <div className="stat-card">
                    <div className="stat-label">Total Finished Goods</div>
                    <div className="stat-value">{totalFG}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Listed (Ready to Sell)</div>
                    <div className="stat-value" style={{ color: 'var(--success)' }}>{listed}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Draft (Pending Review)</div>
                    <div className="stat-value" style={{ color: 'var(--text-muted)' }}>{draft}</div>
                </div>
            </div>

            {/* Catalog Table */}
            <div className="card">
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th style={{ textAlign: 'right' }}>Stock</th>
                                <th style={{ textAlign: 'right' }}>Cost (WAC)</th>
                                <th style={{ textAlign: 'right' }}>Margin %</th>
                                <th style={{ textAlign: 'right' }}>Selling Price</th>
                                <th style={{ textAlign: 'center' }}>Status</th>
                                {isAdmin && <th>Actions</th>}
                            </tr>
                        </thead>
                        <tbody>
                            {catalog.map(item => {
                                const localMargin = margins[item.item_id] ?? '';
                                const livePrice = computePrice(item.current_wac, localMargin);
                                const isSaving = saving[item.item_id];

                                return (
                                    <tr key={item.item_id}>
                                        <td>
                                            <div className="font-bold">{item.item_name}</div>
                                            <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
                                                {item.item_sku}
                                            </div>
                                        </td>
                                        <td style={{ textAlign: 'right' }} className="font-mono">
                                            {item.current_stock > 0 ? (
                                                formatNumber(item.current_stock)
                                            ) : (
                                                <span style={{ color: 'var(--danger)', fontSize: 'var(--font-xs)' }}>No Stock</span>
                                            )}
                                        </td>
                                        <td style={{ textAlign: 'right' }} className="font-mono" title="Cost may change as new production batches complete. Re-publish to lock in updated selling price.">
                                            <span style={{ color: 'var(--warning)' }}>{formatCurrency(item.current_wac)}</span>
                                        </td>
                                        <td style={{ textAlign: 'right' }}>
                                            {isAdmin ? (
                                                <input
                                                    className="form-input"
                                                    type="number"
                                                    step="0.1"
                                                    min="0"
                                                    max="500"
                                                    value={localMargin}
                                                    onChange={e => handleMarginChange(item.item_id, e.target.value)}
                                                    style={{ width: 80, textAlign: 'right', padding: '4px 8px' }}
                                                    placeholder="%"
                                                />
                                            ) : (
                                                <span className="font-mono">{item.profit_margin_percent != null ? `${item.profit_margin_percent}%` : '—'}</span>
                                            )}
                                        </td>
                                        <td style={{ textAlign: 'right' }} className="font-mono font-bold">
                                            {localMargin !== '' && localMargin != null
                                                ? formatCurrency(livePrice)
                                                : '—'}
                                        </td>
                                        <td style={{ textAlign: 'center' }}>
                                            {item.status === 'listed' ? (
                                                <span className="status-badge" style={{ background: 'var(--success)', color: '#fff', padding: '2px 10px', borderRadius: 999, fontSize: 'var(--font-xs)' }}>Listed</span>
                                            ) : (
                                                <span className="status-badge" style={{ background: 'var(--bg-secondary)', color: 'var(--text-muted)', padding: '2px 10px', borderRadius: 999, fontSize: 'var(--font-xs)' }}>Draft</span>
                                            )}
                                        </td>
                                        {isAdmin && (
                                            <td>
                                                <div className="flex gap-2">
                                                    <button
                                                        className="btn btn-primary btn-sm"
                                                        onClick={() => handleSaveMargin(item)}
                                                        disabled={isSaving}
                                                    >
                                                        {isSaving ? '...' : 'Save'}
                                                    </button>
                                                    {item.status === 'listed' ? (
                                                        <button className="btn btn-secondary btn-sm" onClick={() => handleUnpublish(item)}>
                                                            Unpublish
                                                        </button>
                                                    ) : (
                                                        <button
                                                            className="btn btn-sm"
                                                            style={{ background: 'var(--success)', color: '#fff', border: 'none' }}
                                                            onClick={() => handlePublish(item)}
                                                            disabled={!item.pricing_id}
                                                        >
                                                            Publish
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        )}
                                    </tr>
                                );
                            })}
                            {catalog.length === 0 && (
                                <tr><td colSpan={isAdmin ? 7 : 6} className="empty-state"><p>No finished goods found. Create items first.</p></td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
