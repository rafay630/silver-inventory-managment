import { useState, useEffect } from 'react';
import { HiOutlinePlus } from 'react-icons/hi';
import { itemsAPI, categoriesAPI, uomAPI } from '../../services/api';
import { formatCurrency, formatDate, itemTypeLabel, itemTypeBadge } from '../../utils/formatters';

export default function ItemList() {
    const [items, setItems] = useState([]);
    const [categories, setCategories] = useState([]);
    const [uoms, setUoms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('');
    const [modal, setModal] = useState(false);
    const [form, setForm] = useState({});

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const [itemsRes, catRes, uomRes] = await Promise.all([
                itemsAPI.list(filter || undefined),
                categoriesAPI.list(),
                uomAPI.list(),
            ]);
            setItems(itemsRes.data);
            setCategories(catRes.data);
            setUoms(uomRes.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    useEffect(() => {
        setLoading(true);
        itemsAPI.list(filter || undefined)
            .then(res => setItems(res.data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, [filter]);

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            await itemsAPI.create({
                ...form,
                base_cost: form.base_cost ? parseFloat(form.base_cost) : 0,
                reorder_level: form.reorder_level ? parseFloat(form.reorder_level) : 0,
            });
            setModal(false);
            setForm({});
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error creating item'); }
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Items</h1>
                    <p className="page-subtitle">Raw materials & finished goods inventory master</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setModal(true); setForm({ item_type: 'raw_material' }); }}>
                    <HiOutlinePlus /> Add Item
                </button>
            </div>

            <div className="filter-bar mb-4">
                <select className="form-select" style={{ maxWidth: 220 }} value={filter} onChange={e => setFilter(e.target.value)}>
                    <option value="">All Items</option>
                    <option value="raw_material">Raw Materials</option>
                    <option value="finished_good">Finished Goods</option>
                </select>
            </div>

            <div className="card">
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>SKU</th>
                                <th>Type</th>
                                <th>Category</th>
                                <th>UOM</th>
                                <th>Base Cost</th>
                                <th>Reorder Lvl</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((item) => (
                                <tr key={item.id}>
                                    <td className="font-bold">{item.name}</td>
                                    <td className="font-mono">{item.sku || '—'}</td>
                                    <td><span className={`badge ${itemTypeBadge(item.item_type)}`}>{itemTypeLabel(item.item_type)}</span></td>
                                    <td>{item.category_name || '—'}</td>
                                    <td>{item.uom_name || item.uom_abbreviation || '—'}</td>
                                    <td className="font-mono">{formatCurrency(item.base_cost)}</td>
                                    <td className="font-mono">{item.reorder_level || '—'}</td>
                                    <td><span className={`badge ${item.is_active ? 'badge-green' : 'badge-red'}`}>{item.is_active ? 'Active' : 'Inactive'}</span></td>
                                </tr>
                            ))}
                            {items.length === 0 && !loading && (
                                <tr><td colSpan={8} className="empty-state"><p>No items found.</p></td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create Item Modal */}
            {modal && (
                <div className="modal-overlay" onClick={() => setModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add Item</h3>
                            <button className="modal-close" onClick={() => setModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Name</label>
                                    <input className="form-input" value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })} required />
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">SKU</label>
                                        <input className="form-input" value={form.sku || ''} onChange={e => setForm({ ...form, sku: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Barcode</label>
                                        <input className="form-input" value={form.barcode || ''} onChange={e => setForm({ ...form, barcode: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Type</label>
                                        <select className="form-select" value={form.item_type || 'raw_material'} onChange={e => setForm({ ...form, item_type: e.target.value })}>
                                            <option value="raw_material">Raw Material</option>
                                            <option value="finished_good">Finished Good</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Category</label>
                                        <select className="form-select" value={form.category_id || ''} onChange={e => setForm({ ...form, category_id: e.target.value })}>
                                            <option value="">Select...</option>
                                            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                        </select>
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Unit of Measure</label>
                                        <select className="form-select" value={form.uom_id || ''} onChange={e => setForm({ ...form, uom_id: e.target.value })} required>
                                            <option value="">Select...</option>
                                            {uoms.map(u => <option key={u.id} value={u.id}>{u.name} ({u.abbreviation})</option>)}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Base Cost</label>
                                        <input className="form-input" type="number" step="0.01" value={form.base_cost || ''} onChange={e => setForm({ ...form, base_cost: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Reorder Level</label>
                                    <input className="form-input" type="number" step="0.01" value={form.reorder_level || ''} onChange={e => setForm({ ...form, reorder_level: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Description</label>
                                    <textarea className="form-textarea" value={form.description || ''} onChange={e => setForm({ ...form, description: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Create Item</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
