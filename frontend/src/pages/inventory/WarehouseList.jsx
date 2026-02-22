import { useState, useEffect } from 'react';
import { HiOutlinePlus } from 'react-icons/hi';
import { warehousesAPI } from '../../services/api';
import { formatCurrency, formatNumber } from '../../utils/formatters';

export default function WarehouseList() {
    const [warehouses, setWarehouses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modal, setModal] = useState(false);
    const [form, setForm] = useState({});
    const [selectedWarehouse, setSelectedWarehouse] = useState(null);
    const [warehouseStock, setWarehouseStock] = useState([]);
    const [stockLoading, setStockLoading] = useState(false);

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const res = await warehousesAPI.list();
            setWarehouses(res.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            await warehousesAPI.create(form);
            setModal(false); setForm({});
            loadData();
        } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    const viewStock = async (warehouse) => {
        setSelectedWarehouse(warehouse);
        setStockLoading(true);
        try {
            const res = await warehousesAPI.getStock(warehouse.id);
            setWarehouseStock(res.data);
        } catch (err) { console.error(err); setWarehouseStock([]); }
        finally { setStockLoading(false); }
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Warehouses</h1>
                    <p className="page-subtitle">Storage locations & stock management</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setModal(true); setForm({}); }}>
                    <HiOutlinePlus /> Add Warehouse
                </button>
            </div>

            <div className="stats-grid">
                {warehouses.map(wh => (
                    <div key={wh.id} className="stat-card" style={{ cursor: 'pointer' }} onClick={() => viewStock(wh)}>
                        <div className="stat-icon blue">🏭</div>
                        <div className="stat-info">
                            <div className="stat-label">{wh.code || '—'}</div>
                            <div className="stat-value" style={{ fontSize: 'var(--font-lg)' }}>{wh.name}</div>
                            <div className="stat-change" style={{ color: 'var(--text-muted)' }}>{wh.address || 'Click to view stock'}</div>
                        </div>
                    </div>
                ))}
            </div>

            {selectedWarehouse && (
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Stock in {selectedWarehouse.name}</h3>
                        <button className="btn btn-secondary btn-sm" onClick={() => setSelectedWarehouse(null)}>Close</button>
                    </div>
                    <div className="data-table-wrapper">
                        {stockLoading ? (
                            <div className="empty-state"><p>Loading stock...</p></div>
                        ) : (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Item</th>
                                        <th>Type</th>
                                        <th>Balance</th>
                                        <th>Avg Cost</th>
                                        <th>Total Value</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {warehouseStock.map((s, i) => (
                                        <tr key={i}>
                                            <td className="font-bold">{s.item_name}</td>
                                            <td><span className={`badge ${s.item_type === 'raw_material' ? 'badge-amber' : 'badge-green'}`}>{s.item_type === 'raw_material' ? 'Raw Material' : 'Finished Good'}</span></td>
                                            <td className="font-mono">{formatNumber(s.balance)}</td>
                                            <td className="font-mono">{formatCurrency(s.weighted_avg_cost)}</td>
                                            <td className="font-mono font-bold">{formatCurrency(s.total_value)}</td>
                                        </tr>
                                    ))}
                                    {warehouseStock.length === 0 && !stockLoading && (
                                        <tr><td colSpan={5} className="empty-state"><p>No stock in this warehouse.</p></td></tr>
                                    )}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            )}

            {/* Create Warehouse Modal */}
            {modal && (
                <div className="modal-overlay" onClick={() => setModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add Warehouse</h3>
                            <button className="modal-close" onClick={() => setModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Name</label>
                                    <input className="form-input" value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })} required />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Code</label>
                                    <input className="form-input" value={form.code || ''} onChange={e => setForm({ ...form, code: e.target.value })} required />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Address</label>
                                    <textarea className="form-textarea" value={form.address || ''} onChange={e => setForm({ ...form, address: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Create Warehouse</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
