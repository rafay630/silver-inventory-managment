import { useState, useEffect } from 'react';
import { HiOutlinePlus, HiOutlineCheck, HiOutlineX } from 'react-icons/hi';
import { productionAPI, productsAPI } from '../../services/api';
import { formatWeight, formatDateTime, statusColor, formatPercent } from '../../utils/formatters';

export default function BatchList() {
    const [batches, setBatches] = useState([]);
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modal, setModal] = useState(null); // 'create' | 'complete'
    const [selectedBatch, setSelectedBatch] = useState(null);
    const [form, setForm] = useState({});
    const [filter, setFilter] = useState('');

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const [batchRes, prodRes] = await Promise.all([
                productionAPI.listBatches(filter || undefined),
                productsAPI.list(),
            ]);
            setBatches(batchRes.data);
            setProducts(prodRes.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    useEffect(() => { loadData(); }, [filter]);

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            await productionAPI.createBatch({
                product_id: form.product_id,
                planned_quantity: parseInt(form.planned_quantity),
                notes: form.notes,
            });
            setModal(null); setForm({});
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error creating batch'); }
    };

    const handleComplete = async (e) => {
        e.preventDefault();
        try {
            await productionAPI.completeBatch(selectedBatch.id, {
                completed_quantity: parseInt(form.completed_quantity),
                rejected_quantity: parseInt(form.rejected_quantity || 0),
                actual_wastage: form.actual_wastage || {},
                notes: form.notes,
            });
            setModal(null); setForm({}); setSelectedBatch(null);
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error completing batch'); }
    };

    const handleCancel = async (batchId) => {
        if (!confirm('Cancel this batch? Materials will be returned to stock.')) return;
        try {
            await productionAPI.cancelBatch(batchId);
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Production Batches</h1>
                    <p className="page-subtitle">Create and manage production runs</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setModal('create'); setForm({}); }}>
                    <HiOutlinePlus /> Create Batch
                </button>
            </div>

            <div className="filter-bar">
                <select className="form-select" value={filter} onChange={e => setFilter(e.target.value)}>
                    <option value="">All Statuses</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                </select>
            </div>

            <div className="card">
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Batch #</th>
                                <th>Product</th>
                                <th>Planned</th>
                                <th>Completed</th>
                                <th>Rejected</th>
                                <th>Status</th>
                                <th>Started</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {batches.map((b) => (
                                <tr key={b.id}>
                                    <td className="font-bold font-mono">{b.batch_number}</td>
                                    <td>{b.product_name}</td>
                                    <td>{b.planned_quantity}</td>
                                    <td>{b.completed_quantity}</td>
                                    <td className={b.rejected_quantity > 0 ? 'text-red' : ''}>{b.rejected_quantity}</td>
                                    <td><span className={`badge ${statusColor(b.status)}`}>{b.status.replace('_', ' ')}</span></td>
                                    <td>{formatDateTime(b.started_at)}</td>
                                    <td>
                                        {b.status === 'in_progress' && (
                                            <div className="flex gap-2">
                                                <button className="btn btn-success btn-sm" onClick={() => { setSelectedBatch(b); setModal('complete'); setForm({ completed_quantity: b.planned_quantity }); }}>
                                                    <HiOutlineCheck /> Complete
                                                </button>
                                                <button className="btn btn-danger btn-sm" onClick={() => handleCancel(b.id)}>
                                                    <HiOutlineX /> Cancel
                                                </button>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {batches.length === 0 && !loading && (
                                <tr><td colSpan={8} className="empty-state"><p>No batches found.</p></td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create Batch Modal */}
            {modal === 'create' && (
                <div className="modal-overlay" onClick={() => setModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Create Production Batch</h3>
                            <button className="modal-close" onClick={() => setModal(null)}>×</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Product</label>
                                    <select className="form-select" value={form.product_id || ''} onChange={e => setForm({ ...form, product_id: e.target.value })} required>
                                        <option value="">Select product...</option>
                                        {products.map(p => <option key={p.id} value={p.id}>{p.name} (Wastage: {formatPercent(p.wastage_percent)})</option>)}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Production Quantity</label>
                                    <input className="form-input" type="number" value={form.planned_quantity || ''} onChange={e => setForm({ ...form, planned_quantity: e.target.value })} required min="1" />
                                </div>
                                {form.product_id && (() => {
                                    const product = products.find(p => p.id === form.product_id);
                                    if (!product || !product.bom_items?.length) return null;
                                    const qty = parseInt(form.planned_quantity) || 0;
                                    return (
                                        <div className="card" style={{ background: 'var(--bg-secondary)', marginTop: 'var(--space-4)' }}>
                                            <h4 style={{ fontSize: 'var(--font-sm)', fontWeight: 600, marginBottom: 'var(--space-3)' }}>Material Requirements Preview</h4>
                                            {product.bom_items.map(bom => {
                                                const gross = parseFloat(bom.quantity_per_unit) * qty;
                                                const wastage = gross * parseFloat(product.wastage_percent) / 100;
                                                return (
                                                    <div key={bom.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 'var(--font-xs)' }}>
                                                        <span>{bom.raw_material_name}</span>
                                                        <span className="font-mono">{formatWeight(gross + wastage)} (incl. {formatWeight(wastage)} wastage)</span>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    );
                                })()}
                                <div className="form-group mt-4">
                                    <label className="form-label">Notes</label>
                                    <textarea className="form-textarea" value={form.notes || ''} onChange={e => setForm({ ...form, notes: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Create Batch</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Complete Batch Modal */}
            {modal === 'complete' && selectedBatch && (
                <div className="modal-overlay" onClick={() => setModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Complete Batch — {selectedBatch.batch_number}</h3>
                            <button className="modal-close" onClick={() => { setModal(null); setSelectedBatch(null); }}>×</button>
                        </div>
                        <form onSubmit={handleComplete}>
                            <div className="modal-body">
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Completed Quantity</label>
                                        <input className="form-input" type="number" value={form.completed_quantity || ''} onChange={e => setForm({ ...form, completed_quantity: e.target.value })} required min="0" max={selectedBatch.planned_quantity} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Rejected Quantity</label>
                                        <input className="form-input" type="number" value={form.rejected_quantity || 0} onChange={e => setForm({ ...form, rejected_quantity: e.target.value })} min="0" />
                                    </div>
                                </div>
                                {selectedBatch.materials?.map(m => (
                                    <div key={m.id} className="form-group">
                                        <label className="form-label">Actual Wastage — {m.raw_material_name} (expected: {formatWeight(m.wastage_expected)})</label>
                                        <input className="form-input" type="number" step="0.0001"
                                            value={form.actual_wastage?.[m.raw_material_id] || ''}
                                            onChange={e => setForm({ ...form, actual_wastage: { ...(form.actual_wastage || {}), [m.raw_material_id]: e.target.value } })}
                                        />
                                    </div>
                                ))}
                                <div className="form-group">
                                    <label className="form-label">Notes</label>
                                    <textarea className="form-textarea" value={form.notes || ''} onChange={e => setForm({ ...form, notes: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => { setModal(null); setSelectedBatch(null); }}>Cancel</button>
                                <button type="submit" className="btn btn-success">Complete Batch</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
