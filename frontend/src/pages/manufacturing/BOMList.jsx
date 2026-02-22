import { useState, useEffect } from 'react';
import { HiOutlinePlus } from 'react-icons/hi';
import { bomAPI, itemsAPI } from '../../services/api';
import { formatNumber } from '../../utils/formatters';
import PrintSlip, { PrintDetail, PrintTable } from '../../components/PrintSlip';

export default function BOMList() {
    const [boms, setBoms] = useState([]);
    const [items, setItems] = useState([]);
    const [rawMaterials, setRawMaterials] = useState([]);
    const [finishedGoods, setFinishedGoods] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modal, setModal] = useState(false);
    const [requirements, setRequirements] = useState(null);
    const [reqLoading, setReqLoading] = useState(false);
    const [form, setForm] = useState({ product_id: '', version: '1', items: [{ item_id: '', qty_per_unit: '' }] });
    const [printBom, setPrintBom] = useState(null);

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const [bomRes, itemsRes] = await Promise.all([bomAPI.list(), itemsAPI.list()]);
            setBoms(bomRes.data);
            const allItems = itemsRes.data;
            setItems(allItems);
            setRawMaterials(allItems.filter(i => i.item_type === 'raw_material'));
            setFinishedGoods(allItems.filter(i => i.item_type === 'finished_good'));
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const viewRequirements = async (bomId, qty = 1) => {
        setReqLoading(true);
        try {
            const res = await bomAPI.requirements(bomId, qty);
            setRequirements(res.data);
        } catch (err) { console.error(err); setRequirements(null); }
        finally { setReqLoading(false); }
    };

    const addLine = () => setForm({ ...form, items: [...form.items, { item_id: '', qty_per_unit: '' }] });
    const removeLine = (idx) => setForm({ ...form, items: form.items.filter((_, i) => i !== idx) });
    const updateLine = (idx, field, val) => {
        const updated = [...form.items];
        updated[idx][field] = val;
        setForm({ ...form, items: updated });
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            await bomAPI.create({
                product_id: form.product_id,
                version: form.version,
                items: form.items.map(i => ({ item_id: i.item_id, qty_per_unit: parseFloat(i.qty_per_unit) })),
            });
            setModal(false);
            setForm({ product_id: '', version: '1', items: [{ item_id: '', qty_per_unit: '' }] });
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Bill of Materials</h1>
                    <p className="page-subtitle">Product recipes & material requirements</p>
                </div>
                <button className="btn btn-primary" onClick={() => setModal(true)}>
                    <HiOutlinePlus /> New BOM
                </button>
            </div>

            <div className="card">
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th>Version</th>
                                <th>Status</th>
                                <th>Materials</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {boms.map(bom => (
                                <tr key={bom.id}>
                                    <td className="font-bold">{bom.product_name || items.find(i => i.id === bom.product_id)?.name || bom.product_id.substring(0, 8)}</td>
                                    <td className="font-mono">v{bom.version}</td>
                                    <td><span className={`badge ${bom.is_active ? 'badge-green' : 'badge-red'}`}>{bom.is_active ? 'Active' : 'Inactive'}</span></td>
                                    <td>
                                        {bom.items?.map((item, idx) => (
                                            <span key={idx} className="badge badge-silver" style={{ marginRight: 4, marginBottom: 2 }}>
                                                {item.item_name || 'Material'}: {formatNumber(item.qty_per_unit)}
                                            </span>
                                        ))}
                                    </td>
                                    <td>
                                        <div className="flex gap-2">
                                            <button className="btn btn-secondary btn-sm" onClick={() => viewRequirements(bom.id, 1)}>
                                                Requirements
                                            </button>
                                            <button className="btn btn-secondary btn-sm" onClick={() => setPrintBom(bom)}>🖨️</button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {boms.length === 0 && !loading && (
                                <tr><td colSpan={5} className="empty-state"><p>No BOMs found.</p></td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Requirements View */}
            {requirements && (
                <div className="card mt-4">
                    <div className="card-header">
                        <h3 className="card-title">Material Requirements (for 1 unit)</h3>
                        <button className="btn btn-secondary btn-sm" onClick={() => setRequirements(null)}>Close</button>
                    </div>
                    <div className="data-table-wrapper">
                        {reqLoading ? <div className="empty-state"><p>Loading...</p></div> : (
                            <table className="data-table">
                                <thead>
                                    <tr><th>Material</th><th>Required Qty</th><th>Available</th><th>Shortage</th></tr>
                                </thead>
                                <tbody>
                                    {(requirements.materials || requirements).map?.((mat, i) => (
                                        <tr key={i}>
                                            <td className="font-bold">{mat.item_name || mat.name}</td>
                                            <td className="font-mono">{formatNumber(mat.required_qty || mat.qty_per_unit)}</td>
                                            <td className="font-mono">{formatNumber(mat.available_qty)}</td>
                                            <td className="font-mono">
                                                {parseFloat(mat.shortage || 0) > 0 ? (
                                                    <span className="text-red">{formatNumber(mat.shortage)}</span>
                                                ) : (
                                                    <span className="text-green">OK</span>
                                                )}
                                            </td>
                                        </tr>
                                    )) || <tr><td colSpan={4}><pre style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)' }}>{JSON.stringify(requirements, null, 2)}</pre></td></tr>}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            )}

            {/* Print BOM Sheet */}
            {printBom && (
                <PrintSlip
                    title="Bill of Materials"
                    refNumber={`BOM-v${printBom.version}`}
                    date={new Date().toLocaleDateString()}
                    onClose={() => setPrintBom(null)}
                >
                    <PrintDetail label="Product" value={printBom.product_name || items.find(i => i.id === printBom.product_id)?.name || '—'} />
                    <PrintDetail label="Version" value={`v${printBom.version}`} />
                    <PrintDetail label="Status" value={printBom.is_active ? 'Active' : 'Inactive'} />
                    {printBom.notes && <PrintDetail label="Notes" value={printBom.notes} />}
                    <PrintTable headers={['#', 'Material', { label: 'Qty per Unit', align: 'right' }]}>
                        {(printBom.items || []).map((item, i) => (
                            <tr key={i}>
                                <td>{i + 1}</td>
                                <td>{item.item_name || items.find(it => it.id === item.item_id)?.name || '—'}</td>
                                <td className="text-right font-mono">{formatNumber(item.qty_per_unit)}</td>
                            </tr>
                        ))}
                    </PrintTable>
                </PrintSlip>
            )}

            {/* Create BOM Modal */}
            {modal && (
                <div className="modal-overlay" onClick={() => setModal(false)}>
                    <div className="modal" style={{ maxWidth: 640 }} onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Create Bill of Materials</h3>
                            <button className="modal-close" onClick={() => setModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Product (Finished Good)</label>
                                        <select className="form-select" value={form.product_id} onChange={e => setForm({ ...form, product_id: e.target.value })} required>
                                            <option value="">Select...</option>
                                            {finishedGoods.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Version</label>
                                        <input className="form-input" value={form.version} onChange={e => setForm({ ...form, version: e.target.value })} />
                                    </div>
                                </div>

                                <label className="form-label mt-4">Materials</label>
                                {form.items.map((line, idx) => (
                                    <div key={idx} className="form-row mb-4" style={{ alignItems: 'flex-end' }}>
                                        <div className="form-group" style={{ flex: 2 }}>
                                            <select className="form-select" value={line.item_id} onChange={e => updateLine(idx, 'item_id', e.target.value)} required>
                                                <option value="">Select raw material...</option>
                                                {rawMaterials.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                                            </select>
                                        </div>
                                        <div className="form-group" style={{ flex: 1 }}>
                                            <input className="form-input" type="number" step="0.001" placeholder="Qty/unit" value={line.qty_per_unit} onChange={e => updateLine(idx, 'qty_per_unit', e.target.value)} required />
                                        </div>
                                        {form.items.length > 1 && (
                                            <button type="button" className="btn btn-danger btn-sm" onClick={() => removeLine(idx)}>✕</button>
                                        )}
                                    </div>
                                ))}
                                <button type="button" className="btn btn-secondary btn-sm" onClick={addLine}>+ Add Material</button>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Create BOM</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
