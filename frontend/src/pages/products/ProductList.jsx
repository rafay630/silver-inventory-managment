import { useState, useEffect } from 'react';
import { HiOutlinePlus } from 'react-icons/hi';
import { productsAPI, rawMaterialsAPI } from '../../services/api';
import { formatWeight, formatPercent } from '../../utils/formatters';

export default function ProductList() {
    const [products, setProducts] = useState([]);
    const [materials, setMaterials] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modal, setModal] = useState(null); // 'product' | 'bom'
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [form, setForm] = useState({});

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const [prodRes, matRes] = await Promise.all([productsAPI.list(), rawMaterialsAPI.list()]);
            setProducts(prodRes.data);
            setMaterials(matRes.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const handleCreateProduct = async (e) => {
        e.preventDefault();
        try {
            await productsAPI.create(form);
            setModal(null); setForm({});
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    const handleAddBOM = async (e) => {
        e.preventDefault();
        try {
            await productsAPI.addBOM(selectedProduct.id, form);
            setModal(null); setForm({});
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Products & BOM</h1>
                    <p className="page-subtitle">Product master with Bill of Materials</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setModal('product'); setForm({ wastage_percent: 0, unit: 'pieces' }); }}>
                    <HiOutlinePlus /> Add Product
                </button>
            </div>

            {products.map((product) => (
                <div key={product.id} className="card mb-4">
                    <div className="card-header">
                        <div>
                            <h3 className="card-title">{product.name}</h3>
                            <p className="text-muted" style={{ fontSize: 'var(--font-xs)', marginTop: '2px' }}>
                                SKU: {product.sku || '—'} &nbsp;|&nbsp; Wastage: {formatPercent(product.wastage_percent)} &nbsp;|&nbsp; Unit: {product.unit}
                            </p>
                        </div>
                        <button className="btn btn-secondary btn-sm" onClick={() => { setSelectedProduct(product); setModal('bom'); setForm({}); }}>
                            <HiOutlinePlus /> Add BOM Item
                        </button>
                    </div>
                    {product.bom_items && product.bom_items.length > 0 ? (
                        <div className="data-table-wrapper">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Raw Material</th>
                                        <th>Type</th>
                                        <th>Qty Per Unit</th>
                                        <th>With Wastage ({formatPercent(product.wastage_percent)})</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {product.bom_items.map((bom) => {
                                        const withWastage = parseFloat(bom.quantity_per_unit) * (1 + parseFloat(product.wastage_percent) / 100);
                                        return (
                                            <tr key={bom.id}>
                                                <td className="font-bold">{bom.raw_material_name}</td>
                                                <td><span className={`badge ${bom.raw_material_type === 'SILVER' ? 'badge-silver' : 'badge-amber'}`}>{bom.raw_material_type}</span></td>
                                                <td className="font-mono">{formatWeight(bom.quantity_per_unit)}</td>
                                                <td className="font-mono text-amber">{formatWeight(withWastage)}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="empty-state"><p>No BOM items. Add raw materials for this product.</p></div>
                    )}
                </div>
            ))}

            {products.length === 0 && !loading && (
                <div className="card"><div className="empty-state"><p>No products found. Create your first product.</p></div></div>
            )}

            {/* Create Product Modal */}
            {modal === 'product' && (
                <div className="modal-overlay" onClick={() => setModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add Product</h3>
                            <button className="modal-close" onClick={() => setModal(null)}>×</button>
                        </div>
                        <form onSubmit={handleCreateProduct}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Product Name</label>
                                    <input className="form-input" value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })} required />
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">SKU</label>
                                        <input className="form-input" value={form.sku || ''} onChange={e => setForm({ ...form, sku: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Unit</label>
                                        <input className="form-input" value={form.unit || 'pieces'} onChange={e => setForm({ ...form, unit: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Wastage % (manual input per product)</label>
                                    <input className="form-input" type="number" step="0.01" value={form.wastage_percent || 0} onChange={e => setForm({ ...form, wastage_percent: e.target.value })} required />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Description</label>
                                    <textarea className="form-textarea" value={form.description || ''} onChange={e => setForm({ ...form, description: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Create Product</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Add BOM Item Modal */}
            {modal === 'bom' && (
                <div className="modal-overlay" onClick={() => setModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add BOM Item — {selectedProduct?.name}</h3>
                            <button className="modal-close" onClick={() => setModal(null)}>×</button>
                        </div>
                        <form onSubmit={handleAddBOM}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Raw Material</label>
                                    <select className="form-select" value={form.raw_material_id || ''} onChange={e => setForm({ ...form, raw_material_id: e.target.value })} required>
                                        <option value="">Select material...</option>
                                        {materials.map(m => <option key={m.id} value={m.id}>{m.name} ({m.material_type})</option>)}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Quantity Per Unit (grams)</label>
                                    <input className="form-input" type="number" step="0.0001" value={form.quantity_per_unit || ''} onChange={e => setForm({ ...form, quantity_per_unit: e.target.value })} required />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Add BOM Item</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
