import { useState, useEffect } from 'react';
import { HiOutlinePlus } from 'react-icons/hi';
import { productionAPI, bomAPI, warehousesAPI, itemsAPI } from '../../services/api';
import { formatCurrency, formatNumber, formatDate, statusColor } from '../../utils/formatters';
import PrintSlip, { PrintDetail, PrintTable } from '../../components/PrintSlip';

export default function ProductionOrders() {
    const [orders, setOrders] = useState([]);
    const [boms, setBoms] = useState([]);
    const [warehouses, setWarehouses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('');
    const [modal, setModal] = useState(false);
    const [form, setForm] = useState({});
    const [actionModal, setActionModal] = useState(null);
    const [completeForm, setCompleteForm] = useState({});
    const [printOrder, setPrintOrder] = useState(null);

    useEffect(() => { loadData(); }, [filter]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [ordersRes, bomsRes, whRes] = await Promise.all([
                productionAPI.list(filter || undefined),
                bomAPI.list(),
                warehousesAPI.list(),
            ]);
            setOrders(ordersRes.data);
            setBoms(bomsRes.data);
            setWarehouses(whRes.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            await productionAPI.create({
                bom_id: form.bom_id,
                planned_qty: parseFloat(form.planned_qty),
                source_warehouse_id: form.source_warehouse_id,
                target_warehouse_id: form.target_warehouse_id,
            });
            setModal(false); setForm({});
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    const handleStart = async (id) => {
        if (!confirm('Start this production order?')) return;
        try { await productionAPI.start(id); loadData(); }
        catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    const handleCancel = async (id) => {
        if (!confirm('Cancel this production order?')) return;
        try { await productionAPI.cancel(id); loadData(); }
        catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    const handleComplete = async (e) => {
        e.preventDefault();
        try {
            await productionAPI.complete(actionModal.id, {
                actual_qty: parseFloat(completeForm.actual_qty),
                wastage_qty: parseFloat(completeForm.wastage_qty || 0),
            });
            setActionModal(null); setCompleteForm({});
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Production Orders</h1>
                    <p className="page-subtitle">Plan, track & complete manufacturing orders</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setModal(true); setForm({}); }}>
                    <HiOutlinePlus /> New Order
                </button>
            </div>

            <div className="filter-bar mb-4 flex gap-3">
                <select className="form-select" style={{ maxWidth: 200 }} value={filter} onChange={e => setFilter(e.target.value)}>
                    <option value="">All Statuses</option>
                    <option value="planned">Planned</option>
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
                                <th>Order #</th>
                                <th>Product</th>
                                <th>BOM</th>
                                <th>Qty</th>
                                <th>Status</th>
                                <th>Source → Target</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {orders.map(order => (
                                <tr key={order.id}>
                                    <td className="font-mono font-bold">{order.order_number || order.id.substring(0, 8)}</td>
                                    <td className="font-bold">{order.product_name || '—'}</td>
                                    <td className="font-mono">v{order.bom_version || '—'}</td>
                                    <td className="font-mono">
                                        {formatNumber(order.planned_qty)}
                                        {order.actual_qty && <span className="text-muted"> → {formatNumber(order.actual_qty)}</span>}
                                    </td>
                                    <td><span className={`badge ${statusColor(order.status)}`}>{order.status.replace(/_/g, ' ')}</span></td>
                                    <td style={{ fontSize: 'var(--font-xs)' }}>{order.source_warehouse_name || '—'} → {order.target_warehouse_name || '—'}</td>
                                    <td style={{ fontSize: 'var(--font-xs)' }}>{formatDate(order.created_at)}</td>
                                    <td>
                                        <div className="flex gap-2">
                                            {order.status === 'planned' && (
                                                <>
                                                    <button className="btn btn-success btn-sm" onClick={() => handleStart(order.id)}>Start</button>
                                                    <button className="btn btn-danger btn-sm" onClick={() => handleCancel(order.id)}>Cancel</button>
                                                </>
                                            )}
                                            {order.status === 'in_progress' && (
                                                <button className="btn btn-primary btn-sm" onClick={() => { setActionModal(order); setCompleteForm({ actual_qty: order.planned_qty, wastage_qty: 0 }); }}>Complete</button>
                                            )}
                                            <button className="btn btn-secondary btn-sm" onClick={() => setPrintOrder(order)}>🖨️</button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {orders.length === 0 && !loading && (
                                <tr><td colSpan={8} className="empty-state"><p>No production orders found.</p></td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Print Production Slip */}
            {printOrder && (
                <PrintSlip
                    title="Production Order"
                    refNumber={printOrder.order_number || `PO-${printOrder.id.substring(0, 8)}`}
                    date={formatDate(printOrder.created_at)}
                    onClose={() => setPrintOrder(null)}
                >
                    <PrintDetail label="Product" value={printOrder.product_name || '—'} />
                    <PrintDetail label="BOM Version" value={`v${printOrder.bom_version || '—'}`} />
                    <PrintDetail label="Status" value={(printOrder.status || '').replace(/_/g, ' ')} />
                    <PrintDetail label="Planned Qty" value={formatNumber(printOrder.order_qty || printOrder.planned_qty)} />
                    {printOrder.completed_qty > 0 && <PrintDetail label="Completed Qty" value={formatNumber(printOrder.completed_qty)} />}
                    <PrintDetail label="Source Warehouse" value={printOrder.source_warehouse_name || '—'} />
                    <PrintDetail label="Target Warehouse" value={printOrder.target_warehouse_name || '—'} />
                    {printOrder.start_date && <PrintDetail label="Start Date" value={formatDate(printOrder.start_date)} />}
                    {printOrder.end_date && <PrintDetail label="End Date" value={formatDate(printOrder.end_date)} />}
                    {printOrder.requirements?.length > 0 && (
                        <>
                            <h4 className="print-section-title">Material Requirements</h4>
                            <PrintTable headers={['Material', { label: 'Required Qty', align: 'right' }]}>
                                {printOrder.requirements.map((r, i) => (
                                    <tr key={i}>
                                        <td>{r.item_name || r.item_id?.substring(0, 8)}</td>
                                        <td className="text-right font-mono">{formatNumber(r.required_qty)}</td>
                                    </tr>
                                ))}
                            </PrintTable>
                        </>
                    )}
                </PrintSlip>
            )}

            {/* Create Order Modal */}
            {modal && (
                <div className="modal-overlay" onClick={() => setModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">New Production Order</h3>
                            <button className="modal-close" onClick={() => setModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Bill of Materials</label>
                                    <select className="form-select" value={form.bom_id || ''} onChange={e => setForm({ ...form, bom_id: e.target.value })} required>
                                        <option value="">Select BOM...</option>
                                        {boms.map(b => <option key={b.id} value={b.id}>{b.product_name || 'Product'} (v{b.version})</option>)}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Planned Quantity</label>
                                    <input className="form-input" type="number" step="0.01" value={form.planned_qty || ''} onChange={e => setForm({ ...form, planned_qty: e.target.value })} required />
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Source Warehouse</label>
                                        <select className="form-select" value={form.source_warehouse_id || ''} onChange={e => setForm({ ...form, source_warehouse_id: e.target.value })} required>
                                            <option value="">Select...</option>
                                            {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Target Warehouse</label>
                                        <select className="form-select" value={form.target_warehouse_id || ''} onChange={e => setForm({ ...form, target_warehouse_id: e.target.value })} required>
                                            <option value="">Select...</option>
                                            {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Create Order</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Complete Order Modal */}
            {actionModal && (
                <div className="modal-overlay" onClick={() => setActionModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Complete Production Order</h3>
                            <button className="modal-close" onClick={() => setActionModal(null)}>×</button>
                        </div>
                        <form onSubmit={handleComplete}>
                            <div className="modal-body">
                                <p className="text-muted mb-4">Planned: {formatNumber(actionModal.planned_qty)} units</p>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Actual Output Qty</label>
                                        <input className="form-input" type="number" step="0.01" value={completeForm.actual_qty || ''} onChange={e => setCompleteForm({ ...completeForm, actual_qty: e.target.value })} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Wastage Qty</label>
                                        <input className="form-input" type="number" step="0.01" value={completeForm.wastage_qty || ''} onChange={e => setCompleteForm({ ...completeForm, wastage_qty: e.target.value })} />
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setActionModal(null)}>Cancel</button>
                                <button type="submit" className="btn btn-success">Complete Order</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
