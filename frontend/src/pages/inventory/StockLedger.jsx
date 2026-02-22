import { useState, useEffect } from 'react';
import { stockLedgerAPI, itemsAPI, warehousesAPI } from '../../services/api';
import { formatCurrency, formatNumber, formatDateTime, formatDate, itemTypeLabel, itemTypeBadge } from '../../utils/formatters';
import PrintSlip, { PrintDetail, PrintTable } from '../../components/PrintSlip';

export default function StockLedger() {
    const [activeTab, setActiveTab] = useState('balances');
    const [balances, setBalances] = useState([]);
    const [entries, setEntries] = useState([]);
    const [items, setItems] = useState([]);
    const [warehouses, setWarehouses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ item_id: '', warehouse_id: '', item_type: '' });
    const [printMode, setPrintMode] = useState(false);

    useEffect(() => { loadMasterData(); }, []);
    useEffect(() => { loadData(); }, [activeTab, filters]);

    const loadMasterData = async () => {
        try {
            const [itemsRes, whRes] = await Promise.all([itemsAPI.list(), warehousesAPI.list()]);
            setItems(itemsRes.data);
            setWarehouses(whRes.data);
        } catch (err) { console.error(err); }
    };

    const loadData = async () => {
        setLoading(true);
        try {
            if (activeTab === 'balances') {
                const res = await stockLedgerAPI.balances(filters.item_type || undefined, filters.warehouse_id || undefined);
                setBalances(res.data);
            } else {
                const res = await stockLedgerAPI.entries({
                    item_id: filters.item_id || undefined,
                    warehouse_id: filters.warehouse_id || undefined,
                    limit: 100,
                });
                setEntries(res.data);
            }
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const txnTypeColors = {
        opening_stock: 'badge-silver',
        purchase: 'badge-green',
        wip_issue: 'badge-blue',
        production_output: 'badge-purple',
        sale: 'badge-amber',
        adjustment: 'badge-red',
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Stock Ledger</h1>
                    <p className="page-subtitle">Inventory movements & current balances</p>
                </div>
                <button className="btn btn-secondary" onClick={() => setPrintMode(true)}>🖨️ Print Report</button>
            </div>

            <div className="filter-bar mb-4 flex gap-3">
                <button className={`btn ${activeTab === 'balances' ? 'btn-primary' : 'btn-secondary'} btn-sm`} onClick={() => setActiveTab('balances')}>
                    Balances
                </button>
                <button className={`btn ${activeTab === 'entries' ? 'btn-primary' : 'btn-secondary'} btn-sm`} onClick={() => setActiveTab('entries')}>
                    Ledger Entries
                </button>
                <select className="form-select" style={{ maxWidth: 180 }} value={filters.warehouse_id} onChange={e => setFilters({ ...filters, warehouse_id: e.target.value })}>
                    <option value="">All Warehouses</option>
                    {warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                </select>
                {activeTab === 'balances' && (
                    <select className="form-select" style={{ maxWidth: 180 }} value={filters.item_type} onChange={e => setFilters({ ...filters, item_type: e.target.value })}>
                        <option value="">All Types</option>
                        <option value="raw_material">Raw Materials</option>
                        <option value="finished_good">Finished Goods</option>
                    </select>
                )}
                {activeTab === 'entries' && (
                    <select className="form-select" style={{ maxWidth: 200 }} value={filters.item_id} onChange={e => setFilters({ ...filters, item_id: e.target.value })}>
                        <option value="">All Items</option>
                        {items.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
                    </select>
                )}
            </div>

            <div className="card">
                <div className="data-table-wrapper">
                    {loading ? (
                        <div className="empty-state"><p>Loading...</p></div>
                    ) : activeTab === 'balances' ? (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Item</th>
                                    <th>Type</th>
                                    <th>Warehouse</th>
                                    <th>Balance</th>
                                    <th>Avg Cost</th>
                                    <th>Total Value</th>
                                </tr>
                            </thead>
                            <tbody>
                                {balances.map((b, i) => (
                                    <tr key={i}>
                                        <td className="font-bold">{b.item_name}</td>
                                        <td><span className={`badge ${itemTypeBadge(b.item_type)}`}>{itemTypeLabel(b.item_type)}</span></td>
                                        <td>{b.warehouse_name || 'All'}</td>
                                        <td className="font-mono">{formatNumber(b.balance)}</td>
                                        <td className="font-mono">{formatCurrency(b.weighted_avg_cost)}</td>
                                        <td className="font-mono font-bold">{formatCurrency(b.total_value)}</td>
                                    </tr>
                                ))}
                                {balances.length === 0 && (
                                    <tr><td colSpan={6} className="empty-state"><p>No balances found.</p></td></tr>
                                )}
                            </tbody>
                        </table>
                    ) : (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Item</th>
                                    <th>Warehouse</th>
                                    <th>Type</th>
                                    <th>Qty In</th>
                                    <th>Qty Out</th>
                                    <th>Rate</th>
                                    <th>Value</th>
                                    <th>Reference</th>
                                </tr>
                            </thead>
                            <tbody>
                                {entries.map((e) => (
                                    <tr key={e.id}>
                                        <td className="font-mono" style={{ fontSize: 'var(--font-xs)' }}>{formatDateTime(e.posting_date || e.created_at)}</td>
                                        <td className="font-bold">{e.item_name}</td>
                                        <td>{e.warehouse_name}</td>
                                        <td><span className={`badge ${txnTypeColors[e.reference_type] || 'badge-silver'}`}>{(e.reference_type || '').replace(/_/g, ' ')}</span></td>
                                        <td className="font-mono text-green">{parseFloat(e.qty_in) > 0 ? formatNumber(e.qty_in) : ''}</td>
                                        <td className="font-mono text-red">{parseFloat(e.qty_out) > 0 ? formatNumber(e.qty_out) : ''}</td>
                                        <td className="font-mono">{formatCurrency(e.rate)}</td>
                                        <td className="font-mono">{formatCurrency(e.value_effect)}</td>
                                        <td className="font-mono" style={{ fontSize: 'var(--font-xs)' }}>{e.reference_id ? e.reference_id.substring(0, 8) + '…' : '—'}</td>
                                    </tr>
                                ))}
                                {entries.length === 0 && (
                                    <tr><td colSpan={9} className="empty-state"><p>No entries found.</p></td></tr>
                                )}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* Print Stock Report */}
            {printMode && (
                <PrintSlip
                    title={activeTab === 'balances' ? 'Stock Balance Report' : 'Stock Ledger Report'}
                    refNumber={`SL-${new Date().toISOString().split('T')[0]}`}
                    date={new Date().toLocaleDateString()}
                    onClose={() => setPrintMode(false)}
                >
                    {activeTab === 'balances' ? (
                        <PrintTable headers={['Item', 'Type', 'Warehouse', { label: 'Balance', align: 'right' }, { label: 'Avg Cost', align: 'right' }, { label: 'Total Value', align: 'right' }]}>
                            {balances.map((b, i) => (
                                <tr key={i}>
                                    <td>{b.item_name}</td>
                                    <td>{itemTypeLabel(b.item_type)}</td>
                                    <td>{b.warehouse_name || 'All'}</td>
                                    <td className="text-right font-mono">{formatNumber(b.balance)}</td>
                                    <td className="text-right font-mono">{formatCurrency(b.weighted_avg_cost)}</td>
                                    <td className="text-right font-mono font-bold">{formatCurrency(b.total_value)}</td>
                                </tr>
                            ))}
                            <tr style={{ borderTop: '2px solid #333' }}>
                                <td colSpan={5} className="font-bold">TOTAL INVENTORY VALUE</td>
                                <td className="text-right font-mono font-bold">{formatCurrency(balances.reduce((s, b) => s + (parseFloat(b.total_value) || 0), 0))}</td>
                            </tr>
                        </PrintTable>
                    ) : (
                        <PrintTable headers={['Date', 'Item', 'Warehouse', 'Type', { label: 'Qty In', align: 'right' }, { label: 'Qty Out', align: 'right' }, { label: 'Rate', align: 'right' }, { label: 'Value', align: 'right' }]}>
                            {entries.map((e, i) => (
                                <tr key={i}>
                                    <td>{formatDate(e.posting_date || e.created_at)}</td>
                                    <td>{e.item_name}</td>
                                    <td>{e.warehouse_name}</td>
                                    <td>{(e.reference_type || '').replace(/_/g, ' ')}</td>
                                    <td className="text-right font-mono">{parseFloat(e.qty_in) > 0 ? formatNumber(e.qty_in) : ''}</td>
                                    <td className="text-right font-mono">{parseFloat(e.qty_out) > 0 ? formatNumber(e.qty_out) : ''}</td>
                                    <td className="text-right font-mono">{formatCurrency(e.rate)}</td>
                                    <td className="text-right font-mono">{formatCurrency(e.value_effect)}</td>
                                </tr>
                            ))}
                        </PrintTable>
                    )}
                </PrintSlip>
            )}
        </div>
    );
}
