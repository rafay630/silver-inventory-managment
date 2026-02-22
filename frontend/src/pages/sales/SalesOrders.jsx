import { useState, useEffect } from 'react';
import { HiOutlinePlus } from 'react-icons/hi';
import { salesAPI, itemsAPI, warehousesAPI, pricingAPI } from '../../services/api';
import { formatCurrency, formatNumber, formatDate, statusColor } from '../../utils/formatters';
import PrintSlip, { PrintDetail, PrintTable } from '../../components/PrintSlip';
import SalesCatalog from './SalesCatalog';

export default function SalesOrders() {
    const [activeTab, setActiveTab] = useState('orders');
    const [orders, setOrders] = useState([]);
    const [items, setItems] = useState([]);          // all FG (for display names)
    const [listedItems, setListedItems] = useState([]); // only listed (for create modal)
    const [warehouses, setWarehouses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modal, setModal] = useState(false);
    const [form, setForm] = useState({ warehouse_id: '', customer_name: '', lines: [{ item_id: '', qty: '', unit_price: '' }] });
    const [detailOrder, setDetailOrder] = useState(null);
    const [printOrder, setPrintOrder] = useState(null);

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const [salesRes, itemsRes, whRes, listedRes] = await Promise.all([
                salesAPI.list(),
                itemsAPI.list('finished_good'),
                warehousesAPI.list(),
                pricingAPI.getListed().catch(() => ({ data: [] })),
            ]);
            setOrders(salesRes.data);
            setItems(itemsRes.data);
            setWarehouses(whRes.data);
            setListedItems(listedRes.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const addLine = () => setForm({ ...form, lines: [...form.lines, { item_id: '', qty: '', unit_price: '' }] });
    const removeLine = (idx) => setForm({ ...form, lines: form.lines.filter((_, i) => i !== idx) });
    const updateLine = (idx, field, val) => {
        const updated = [...form.lines];
        updated[idx][field] = val;
        // Auto-fill price when item selected
        if (field === 'item_id' && val) {
            const listed = listedItems.find(i => i.item_id === val);
            if (listed) {
                updated[idx].unit_price = listed.selling_price;
            }
        }
        setForm({ ...form, lines: updated });
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            await salesAPI.create({
                warehouse_id: form.warehouse_id,
                customer_name: form.customer_name,
                lines: form.lines.map(l => ({
                    item_id: l.item_id,
                    qty: parseFloat(l.qty),
                    unit_price: parseFloat(l.unit_price),
                })),
            });
            setModal(false);
            setForm({ warehouse_id: '', customer_name: '', lines: [{ item_id: '', qty: '', unit_price: '' }] });
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    const viewDetail = async (id) => {
        try {
            const res = await salesAPI.get(id);
            setDetailOrder(res.data);
        } catch (err) { console.error(err); }
    };

    const handlePrint = async (order) => {
        try {
            const res = await salesAPI.get(order.id);
            setPrintOrder(res.data);
        } catch (err) { console.error(err); }
    };

    const lineTotal = (line) => {
        const qty = parseFloat(line.qty) || 0;
        const price = parseFloat(line.unit_price) || 0;
        return qty * price;
    };

    const orderTotal = form.lines.reduce((sum, l) => sum + lineTotal(l), 0);

    const itemName = (itemId) => items.find(i => i.id === itemId)?.name || itemId?.substring(0, 8) || '—';

    // Use listed items for dropdown; fall back to all FG items if no listed items exist
    const dropdownItems = listedItems.length > 0 ? listedItems : items.map(i => ({ item_id: i.id, item_name: i.name, item_sku: i.sku, selling_price: 0 }));

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Sales</h1>
                    <p className="page-subtitle">Orders, catalog & pricing management</p>
                </div>
                {activeTab === 'orders' && (
                    <button className="btn btn-primary" onClick={() => setModal(true)}>
                        <HiOutlinePlus /> New Sale
                    </button>
                )}
            </div>

            {/* Tab Switcher */}
            <div className="flex gap-2 mb-6">
                <button
                    className={`btn ${activeTab === 'orders' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setActiveTab('orders')}
                >
                    Sales Orders
                </button>
                <button
                    className={`btn ${activeTab === 'catalog' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setActiveTab('catalog')}
                >
                    Sales Catalog
                </button>
            </div>

            {/* Orders Tab */}
            {activeTab === 'orders' && (
                <div className="card">
                    <div className="data-table-wrapper">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Order #</th>
                                    <th>Customer</th>
                                    <th>Items</th>
                                    <th>Total</th>
                                    <th>Date</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orders.map(order => (
                                    <tr key={order.id}>
                                        <td className="font-mono font-bold">{order.order_number || order.id.substring(0, 8)}</td>
                                        <td className="font-bold">{order.customer_name}</td>
                                        <td>{order.items?.length || 0} items</td>
                                        <td className="font-mono font-bold">{formatCurrency(order.total_amount)}</td>
                                        <td style={{ fontSize: 'var(--font-xs)' }}>{formatDate(order.order_date || order.created_at)}</td>
                                        <td>
                                            <div className="flex gap-2">
                                                <button className="btn btn-secondary btn-sm" onClick={() => viewDetail(order.id)}>Details</button>
                                                <button className="btn btn-secondary btn-sm" onClick={() => handlePrint(order)}>🖨️</button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                                {orders.length === 0 && !loading && (
                                    <tr><td colSpan={6} className="empty-state"><p>No sales orders found.</p></td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Catalog Tab */}
            {activeTab === 'catalog' && <SalesCatalog />}

            {/* Print Invoice */}
            {printOrder && (
                <PrintSlip
                    title="Sales Invoice"
                    refNumber={printOrder.order_number || `SO-${printOrder.id.substring(0, 8)}`}
                    date={formatDate(printOrder.order_date || printOrder.created_at)}
                    onClose={() => setPrintOrder(null)}
                    footer={
                        <div className="print-total-row">
                            <span>Grand Total</span>
                            <span>{formatCurrency(printOrder.total_amount)}</span>
                        </div>
                    }
                >
                    <PrintDetail label="Customer" value={printOrder.customer_name} />
                    <PrintDetail label="Status" value={printOrder.status || 'completed'} />
                    <PrintDetail label="Order Date" value={formatDate(printOrder.order_date || printOrder.created_at)} />

                    <PrintTable headers={['#', 'Item', { label: 'Qty', align: 'right' }, { label: 'Unit Price', align: 'right' }, { label: 'Total', align: 'right' }]}>
                        {(printOrder.items || []).map((line, i) => (
                            <tr key={i}>
                                <td>{i + 1}</td>
                                <td>{itemName(line.item_id)}</td>
                                <td className="text-right font-mono">{formatNumber(line.quantity)}</td>
                                <td className="text-right font-mono">{formatCurrency(line.unit_price)}</td>
                                <td className="text-right font-mono font-bold">{formatCurrency(line.total_price)}</td>
                            </tr>
                        ))}
                    </PrintTable>
                </PrintSlip>
            )}

            {/* Sales Detail Modal */}
            {detailOrder && (
                <div className="modal-overlay" onClick={() => setDetailOrder(null)}>
                    <div className="modal" style={{ maxWidth: 640 }} onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Order Details — {detailOrder.order_number || detailOrder.id.substring(0, 8)}</h3>
                            <button className="modal-close" onClick={() => setDetailOrder(null)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="mb-4">
                                <p><strong>Customer:</strong> {detailOrder.customer_name}</p>
                                <p><strong>Date:</strong> {formatDate(detailOrder.order_date || detailOrder.created_at)}</p>
                                <p><strong>Status:</strong> {detailOrder.status}</p>
                            </div>
                            <table className="data-table">
                                <thead>
                                    <tr><th>#</th><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr>
                                </thead>
                                <tbody>
                                    {(detailOrder.items || []).map((line, i) => (
                                        <tr key={i}>
                                            <td>{i + 1}</td>
                                            <td>{itemName(line.item_id)}</td>
                                            <td className="font-mono">{formatNumber(line.quantity)}</td>
                                            <td className="font-mono">{formatCurrency(line.unit_price)}</td>
                                            <td className="font-mono font-bold">{formatCurrency(line.total_price)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            <div className="mt-4" style={{ textAlign: 'right' }}>
                                <p className="font-bold" style={{ fontSize: 'var(--font-lg)' }}>Total: {formatCurrency(detailOrder.total_amount)}</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Create Sales Order Modal */}
            {modal && (
                <div className="modal-overlay" onClick={() => setModal(false)}>
                    <div className="modal" style={{ maxWidth: 700 }} onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">New Sales Order</h3>
                            <button className="modal-close" onClick={() => setModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Customer Name</label>
                                        <input className="form-input" value={form.customer_name} onChange={e => setForm({ ...form, customer_name: e.target.value })} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Warehouse</label>
                                        <select className="form-select" value={form.warehouse_id} onChange={e => setForm({ ...form, warehouse_id: e.target.value })} required>
                                            <option value="">Select...</option>
                                            {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                                        </select>
                                    </div>
                                </div>

                                <label className="form-label mt-4">Order Lines</label>
                                {listedItems.length > 0 && (
                                    <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', marginBottom: 'var(--space-2)' }}>
                                        Only published catalog items are shown. Price auto-fills from catalog.
                                    </p>
                                )}
                                {form.lines.map((line, idx) => (
                                    <div key={idx} className="form-row mb-4" style={{ alignItems: 'flex-end' }}>
                                        <div className="form-group" style={{ flex: 2 }}>
                                            <select className="form-select" value={line.item_id} onChange={e => updateLine(idx, 'item_id', e.target.value)} required>
                                                <option value="">Select product...</option>
                                                {dropdownItems.map(i => (
                                                    <option key={i.item_id} value={i.item_id}>
                                                        {i.item_name} {i.selling_price > 0 ? `(${formatCurrency(i.selling_price)})` : ''}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="form-group" style={{ flex: 1 }}>
                                            <input className="form-input" type="number" step="0.01" placeholder="Qty" value={line.qty} onChange={e => updateLine(idx, 'qty', e.target.value)} required />
                                        </div>
                                        <div className="form-group" style={{ flex: 1 }}>
                                            <input className="form-input" type="number" step="0.01" placeholder="Unit Price" value={line.unit_price} onChange={e => updateLine(idx, 'unit_price', e.target.value)} required />
                                            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>Default: catalog price. Edit for discount.</span>
                                        </div>
                                        <div style={{ fontSize: 'var(--font-sm)', color: 'var(--text-muted)', whiteSpace: 'nowrap', paddingBottom: 'var(--space-3)' }}>{formatCurrency(lineTotal(line))}</div>
                                        {form.lines.length > 1 && (
                                            <button type="button" className="btn btn-danger btn-sm" onClick={() => removeLine(idx)}>✕</button>
                                        )}
                                    </div>
                                ))}
                                <div className="flex items-center gap-4">
                                    <button type="button" className="btn btn-secondary btn-sm" onClick={addLine}>+ Add Line</button>
                                    <span className="font-bold" style={{ marginLeft: 'auto' }}>Total: {formatCurrency(orderTotal)}</span>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Create Sale</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
