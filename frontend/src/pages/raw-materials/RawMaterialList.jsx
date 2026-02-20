import { useState, useEffect } from 'react';
import { HiOutlinePlus, HiOutlineShoppingCart, HiOutlineAdjustments } from 'react-icons/hi';
import { rawMaterialsAPI, suppliersAPI } from '../../services/api';
import { formatWeight, formatDate, statusColor } from '../../utils/formatters';

export default function RawMaterialList() {
    const [materials, setMaterials] = useState([]);
    const [suppliers, setSuppliers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modal, setModal] = useState(null); // 'create' | 'purchase' | 'adjust'
    const [form, setForm] = useState({});

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const [matRes, supRes] = await Promise.all([rawMaterialsAPI.list(), suppliersAPI.list()]);
            setMaterials(matRes.data);
            setSuppliers(supRes.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            await rawMaterialsAPI.create(form);
            setModal(null); setForm({});
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    const handlePurchase = async (e) => {
        e.preventDefault();
        try {
            await rawMaterialsAPI.purchase({ ...form, purchase_date: form.purchase_date || new Date().toISOString().split('T')[0] });
            setModal(null); setForm({});
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    const handleAdjust = async (e) => {
        e.preventDefault();
        try {
            await rawMaterialsAPI.adjust(form);
            setModal(null); setForm({});
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    const getStockStatus = (m) => {
        const stock = parseFloat(m.current_stock || 0);
        const reorder = parseFloat(m.reorder_level || 0);
        if (stock <= 0) return 'critical';
        if (stock <= reorder) return 'low';
        return 'healthy';
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Raw Materials</h1>
                    <p className="page-subtitle">Silver & Brass inventory management</p>
                </div>
                <div className="flex gap-3">
                    <button className="btn btn-secondary" onClick={() => { setModal('adjust'); setForm({}); }}>
                        <HiOutlineAdjustments /> Adjust Stock
                    </button>
                    <button className="btn btn-secondary" onClick={() => { setModal('purchase'); setForm({}); }}>
                        <HiOutlineShoppingCart /> Purchase Entry
                    </button>
                    <button className="btn btn-primary" onClick={() => { setModal('create'); setForm({ material_type: 'SILVER', unit: 'grams' }); }}>
                        <HiOutlinePlus /> Add Material
                    </button>
                </div>
            </div>

            <div className="card">
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Material</th>
                                <th>Type</th>
                                <th>Current Stock</th>
                                <th>Unit</th>
                                <th>Reorder Level</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {materials.map((m) => (
                                <tr key={m.id}>
                                    <td className="font-bold">{m.name}</td>
                                    <td><span className={`badge ${m.material_type === 'SILVER' ? 'badge-silver' : 'badge-amber'}`}>{m.material_type}</span></td>
                                    <td className="font-mono">{formatWeight(m.current_stock, m.unit)}</td>
                                    <td>{m.unit}</td>
                                    <td className="font-mono">{formatWeight(m.reorder_level, m.unit)}</td>
                                    <td><span className={`badge ${statusColor(getStockStatus(m))}`}>{getStockStatus(m)}</span></td>
                                </tr>
                            ))}
                            {materials.length === 0 && !loading && (
                                <tr><td colSpan={6} className="empty-state"><p>No materials found. Add your first raw material.</p></td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create Material Modal */}
            {modal === 'create' && (
                <div className="modal-overlay" onClick={() => setModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add Raw Material</h3>
                            <button className="modal-close" onClick={() => setModal(null)}>×</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Name</label>
                                    <input className="form-input" value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })} required />
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Type</label>
                                        <select className="form-select" value={form.material_type || 'SILVER'} onChange={e => setForm({ ...form, material_type: e.target.value })}>
                                            <option value="SILVER">Silver</option>
                                            <option value="BRASS">Brass</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Unit</label>
                                        <select className="form-select" value={form.unit || 'grams'} onChange={e => setForm({ ...form, unit: e.target.value })}>
                                            <option value="grams">Grams</option>
                                            <option value="kg">Kilograms</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Reorder Level</label>
                                    <input className="form-input" type="number" step="0.0001" value={form.reorder_level || ''} onChange={e => setForm({ ...form, reorder_level: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Create Material</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Purchase Entry Modal */}
            {modal === 'purchase' && (
                <div className="modal-overlay" onClick={() => setModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Record Purchase</h3>
                            <button className="modal-close" onClick={() => setModal(null)}>×</button>
                        </div>
                        <form onSubmit={handlePurchase}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Raw Material</label>
                                    <select className="form-select" value={form.raw_material_id || ''} onChange={e => setForm({ ...form, raw_material_id: e.target.value })} required>
                                        <option value="">Select material...</option>
                                        {materials.map(m => <option key={m.id} value={m.id}>{m.name} ({m.material_type})</option>)}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Supplier</label>
                                    <select className="form-select" value={form.supplier_id || ''} onChange={e => setForm({ ...form, supplier_id: e.target.value })}>
                                        <option value="">Select supplier (optional)...</option>
                                        {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                                    </select>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Quantity</label>
                                        <input className="form-input" type="number" step="0.0001" value={form.quantity || ''} onChange={e => setForm({ ...form, quantity: e.target.value })} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Unit Price</label>
                                        <input className="form-input" type="number" step="0.01" value={form.unit_price || ''} onChange={e => setForm({ ...form, unit_price: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Purchase Date</label>
                                        <input className="form-input" type="date" value={form.purchase_date || ''} onChange={e => setForm({ ...form, purchase_date: e.target.value })} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Invoice #</label>
                                        <input className="form-input" value={form.invoice_number || ''} onChange={e => setForm({ ...form, invoice_number: e.target.value })} />
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Record Purchase</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Adjust Stock Modal */}
            {modal === 'adjust' && (
                <div className="modal-overlay" onClick={() => setModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Adjust Stock</h3>
                            <button className="modal-close" onClick={() => setModal(null)}>×</button>
                        </div>
                        <form onSubmit={handleAdjust}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Raw Material</label>
                                    <select className="form-select" value={form.raw_material_id || ''} onChange={e => setForm({ ...form, raw_material_id: e.target.value })} required>
                                        <option value="">Select material...</option>
                                        {materials.map(m => <option key={m.id} value={m.id}>{m.name} ({m.material_type})</option>)}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Quantity (negative to deduct)</label>
                                    <input className="form-input" type="number" step="0.0001" value={form.quantity || ''} onChange={e => setForm({ ...form, quantity: e.target.value })} required />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Notes</label>
                                    <textarea className="form-textarea" value={form.notes || ''} onChange={e => setForm({ ...form, notes: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Adjust Stock</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
