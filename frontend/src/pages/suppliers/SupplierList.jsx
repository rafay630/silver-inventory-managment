import { useState, useEffect } from 'react';
import { HiOutlinePlus } from 'react-icons/hi';
import { suppliersAPI } from '../../services/api';

export default function SupplierList() {
    const [suppliers, setSuppliers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modal, setModal] = useState(false);
    const [form, setForm] = useState({});

    useEffect(() => { loadData(); }, []);
    const loadData = async () => {
        try { const res = await suppliersAPI.list(); setSuppliers(res.data); }
        catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try { await suppliersAPI.create(form); setModal(false); setForm({}); loadData(); }
        catch (err) { alert(err.response?.data?.detail || 'Error'); }
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Suppliers</h1>
                    <p className="page-subtitle">Raw material suppliers</p>
                </div>
                <button className="btn btn-primary" onClick={() => { setModal(true); setForm({}); }}>
                    <HiOutlinePlus /> Add Supplier
                </button>
            </div>

            <div className="card">
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead><tr><th>Name</th><th>Contact</th><th>Phone</th><th>Email</th><th>Status</th></tr></thead>
                        <tbody>
                            {suppliers.map(s => (
                                <tr key={s.id}>
                                    <td className="font-bold">{s.name}</td>
                                    <td>{s.contact_person || '—'}</td>
                                    <td>{s.phone || '—'}</td>
                                    <td>{s.email || '—'}</td>
                                    <td><span className={`badge ${s.is_active ? 'badge-green' : 'badge-red'}`}>{s.is_active ? 'Active' : 'Inactive'}</span></td>
                                </tr>
                            ))}
                            {suppliers.length === 0 && !loading && (
                                <tr><td colSpan={5} className="empty-state"><p>No suppliers yet.</p></td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {modal && (
                <div className="modal-overlay" onClick={() => setModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="modal-title">Add Supplier</h3>
                            <button className="modal-close" onClick={() => setModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-group"><label className="form-label">Name</label><input className="form-input" value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })} required /></div>
                                <div className="form-row">
                                    <div className="form-group"><label className="form-label">Contact Person</label><input className="form-input" value={form.contact_person || ''} onChange={e => setForm({ ...form, contact_person: e.target.value })} /></div>
                                    <div className="form-group"><label className="form-label">Phone</label><input className="form-input" value={form.phone || ''} onChange={e => setForm({ ...form, phone: e.target.value })} /></div>
                                </div>
                                <div className="form-group"><label className="form-label">Email</label><input className="form-input" type="email" value={form.email || ''} onChange={e => setForm({ ...form, email: e.target.value })} /></div>
                                <div className="form-group"><label className="form-label">Address</label><textarea className="form-textarea" value={form.address || ''} onChange={e => setForm({ ...form, address: e.target.value })} /></div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">Create Supplier</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
