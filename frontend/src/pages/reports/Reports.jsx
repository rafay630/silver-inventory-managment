import { useState, useEffect } from 'react';
import { reportsAPI, productionAPI } from '../../services/api';
import { formatCurrency, formatNumber, formatDate } from '../../utils/formatters';
import PrintSlip, { PrintDetail, PrintTable } from '../../components/PrintSlip';

export default function Reports() {
    const [activeTab, setActiveTab] = useState('inventory-valuation');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [prodOrders, setProdOrders] = useState([]);
    const [selectedOrder, setSelectedOrder] = useState('');
    const [printMode, setPrintMode] = useState(false);

    useEffect(() => { loadTab(); }, [activeTab, selectedOrder]);
    useEffect(() => {
        productionAPI.list().then(r => setProdOrders(r.data)).catch(() => { });
    }, []);

    const loadTab = async () => {
        setLoading(true);
        setData(null);
        try {
            if (activeTab === 'inventory-valuation') {
                const res = await reportsAPI.inventoryValuation();
                setData(res.data);
            } else if (activeTab === 'wip-summary') {
                const res = await reportsAPI.wipSummary();
                setData(res.data);
            } else if (activeTab === 'material-consumption') {
                const res = await reportsAPI.materialConsumption();
                setData(res.data);
            } else if (activeTab === 'production-cost' && selectedOrder) {
                const res = await reportsAPI.productionCostSheet(selectedOrder);
                setData(res.data);
            }
        } catch (err) { console.error(err); setData(null); }
        finally { setLoading(false); }
    };

    const tabs = [
        { id: 'inventory-valuation', label: 'Inventory Valuation' },
        { id: 'wip-summary', label: 'WIP Summary' },
        { id: 'material-consumption', label: 'Material Consumption' },
        { id: 'production-cost', label: 'Production Cost Sheet' },
    ];

    const renderContent = () => {
        if (loading) return <div className="empty-state"><p>Loading report...</p></div>;
        if (activeTab === 'production-cost' && !selectedOrder) return <div className="empty-state"><p>Select a production order above to view its cost sheet.</p></div>;
        if (!data) return <div className="empty-state"><p>No data available.</p></div>;

        if (activeTab === 'inventory-valuation') {
            const items = Array.isArray(data) ? data : [];
            const grandTotal = items.reduce((s, r) => s + (r.total_value || 0), 0);
            return (
                <>
                    <table className="data-table">
                        <thead><tr><th>Item</th><th>Warehouse</th><th className="text-right">Balance</th><th className="text-right">Avg Cost</th><th className="text-right">Value</th></tr></thead>
                        <tbody>
                            {items.map((r, i) => (
                                <tr key={i}>
                                    <td className="font-bold">{r.item_name}</td>
                                    <td>{r.warehouse_name}</td>
                                    <td className="text-right font-mono">{formatNumber(r.balance)}</td>
                                    <td className="text-right font-mono">{formatCurrency(r.weighted_avg_cost)}</td>
                                    <td className="text-right font-mono font-bold">{formatCurrency(r.total_value)}</td>
                                </tr>
                            ))}
                        </tbody>
                        <tfoot>
                            <tr style={{ borderTop: '2px solid var(--accent-silver)' }}>
                                <td colSpan={4} className="font-bold">Grand Total</td>
                                <td className="text-right font-mono font-bold">{formatCurrency(grandTotal)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </>
            );
        }

        if (activeTab === 'wip-summary') {
            const items = Array.isArray(data) ? data : [];
            return (
                <table className="data-table">
                    <thead><tr><th>Order #</th><th>Qty (Ordered/Done)</th><th className="text-right">Material Cost</th><th className="text-right">Expense Cost</th><th className="text-right">Total WIP</th></tr></thead>
                    <tbody>
                        {items.map((r, i) => (
                            <tr key={i}>
                                <td className="font-bold font-mono">{r.order_number}</td>
                                <td className="font-mono">{formatNumber(r.order_qty)} / {formatNumber(r.completed_qty)}</td>
                                <td className="text-right font-mono">{formatCurrency(r.material_cost)}</td>
                                <td className="text-right font-mono">{formatCurrency(r.expense_cost)}</td>
                                <td className="text-right font-mono font-bold">{formatCurrency(r.total_wip_value)}</td>
                            </tr>
                        ))}
                        {items.length === 0 && <tr><td colSpan={5} className="empty-state"><p>No WIP data.</p></td></tr>}
                    </tbody>
                </table>
            );
        }

        if (activeTab === 'material-consumption') {
            const items = Array.isArray(data) ? data : [];
            const totalCost = items.reduce((s, r) => s + (r.total_cost || 0), 0);
            return (
                <table className="data-table">
                    <thead><tr><th>Material</th><th className="text-right">Qty Consumed</th><th className="text-right">Total Cost</th></tr></thead>
                    <tbody>
                        {items.map((r, i) => (
                            <tr key={i}>
                                <td className="font-bold">{r.item_name}</td>
                                <td className="text-right font-mono">{formatNumber(r.total_quantity)}</td>
                                <td className="text-right font-mono font-bold">{formatCurrency(r.total_cost)}</td>
                            </tr>
                        ))}
                        {items.length === 0 && <tr><td colSpan={3} className="empty-state"><p>No consumption data.</p></td></tr>}
                    </tbody>
                    <tfoot>
                        <tr style={{ borderTop: '2px solid var(--accent-silver)' }}>
                            <td colSpan={2} className="font-bold">Total</td>
                            <td className="text-right font-mono font-bold">{formatCurrency(totalCost)}</td>
                        </tr>
                    </tfoot>
                </table>
            );
        }

        if (activeTab === 'production-cost') {
            return (
                <div>
                    {/* Header Stats */}
                    <div className="stats-grid mb-6">
                        <div className="stat-card">
                            <div className="stat-icon cyan">🔧</div>
                            <div className="stat-info"><div className="stat-label">Order</div><div className="stat-value">{data.order_number}</div></div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon green">📦</div>
                            <div className="stat-info"><div className="stat-label">Qty (Ordered / Done)</div><div className="stat-value">{formatNumber(data.order_qty)} / {formatNumber(data.completed_qty)}</div></div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon amber">💵</div>
                            <div className="stat-info"><div className="stat-label">Total Cost</div><div className="stat-value">{formatCurrency(data.total_production_cost)}</div></div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon red">📊</div>
                            <div className="stat-info"><div className="stat-label">Unit Cost</div><div className="stat-value">{formatCurrency(data.unit_cost)}</div></div>
                        </div>
                    </div>

                    {/* Materials */}
                    <div className="card mb-4">
                        <h4 className="card-title mb-4">Materials ({formatCurrency(data.total_material_cost)})</h4>
                        <table className="data-table">
                            <thead><tr><th>Material</th><th className="text-right">Quantity</th><th className="text-right">Cost</th></tr></thead>
                            <tbody>
                                {(data.materials || []).map((m, i) => (
                                    <tr key={i}>
                                        <td className="font-bold">{m.item_name}</td>
                                        <td className="text-right font-mono">{formatNumber(m.quantity)}</td>
                                        <td className="text-right font-mono">{formatCurrency(m.cost)}</td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot>
                                <tr style={{ borderTop: '2px solid var(--accent-silver)' }}>
                                    <td colSpan={2} className="font-bold">Subtotal</td>
                                    <td className="text-right font-mono font-bold">{formatCurrency(data.total_material_cost)}</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>

                    {/* Expenses */}
                    <div className="card">
                        <h4 className="card-title mb-4">Expenses ({formatCurrency(data.total_expenses)})</h4>
                        <table className="data-table">
                            <thead><tr><th>Type</th><th>Description</th><th>Date</th><th className="text-right">Amount</th></tr></thead>
                            <tbody>
                                {(data.expenses || []).map((e, i) => (
                                    <tr key={i}>
                                        <td><span className="badge badge-silver">{(e.expense_type || '').replace(/_/g, ' ')}</span></td>
                                        <td>{e.description}</td>
                                        <td className="font-mono" style={{ fontSize: 'var(--font-xs)' }}>{formatDate(e.date)}</td>
                                        <td className="text-right font-mono">{formatCurrency(e.amount)}</td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot>
                                <tr style={{ borderTop: '2px solid var(--accent-silver)' }}>
                                    <td colSpan={3} className="font-bold">Subtotal</td>
                                    <td className="text-right font-mono font-bold">{formatCurrency(data.total_expenses)}</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            );
        }

        return null;
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Reports</h1>
                    <p className="page-subtitle">Manufacturing & inventory analytics</p>
                </div>
                {data && <button className="btn btn-secondary" onClick={() => setPrintMode(true)}>🖨️ Print Report</button>}
            </div>
            <div className="filter-bar mb-4 flex gap-3" style={{ overflowX: 'auto', flexWrap: 'wrap' }}>
                {tabs.map(tab => <button key={tab.id} className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-secondary'} btn-sm`} onClick={() => setActiveTab(tab.id)}>{tab.label}</button>)}
                {activeTab === 'production-cost' && (
                    <select className="form-select" style={{ maxWidth: 300 }} value={selectedOrder} onChange={e => setSelectedOrder(e.target.value)}>
                        <option value="">Select production order...</option>
                        {prodOrders.map(o => <option key={o.id} value={o.id}>{o.order_number || o.id.substring(0, 8)} — {o.product_name || 'Product'} ({o.status})</option>)}
                    </select>
                )}
            </div>
            <div className="card"><div className="data-table-wrapper">{renderContent()}</div></div>

            {/* Print Report */}
            {printMode && data && (
                <PrintSlip
                    title={tabs.find(t => t.id === activeTab)?.label || 'Report'}
                    refNumber={`RPT-${new Date().toISOString().split('T')[0]}`}
                    date={new Date().toLocaleDateString()}
                    onClose={() => setPrintMode(false)}
                >
                    {activeTab === 'inventory-valuation' && (() => {
                        const items = Array.isArray(data) ? data : [];
                        return (
                            <PrintTable headers={['Item', 'Warehouse', { label: 'Balance', align: 'right' }, { label: 'Avg Cost', align: 'right' }, { label: 'Value', align: 'right' }]}>
                                {items.map((r, i) => (
                                    <tr key={i}>
                                        <td>{r.item_name}</td>
                                        <td>{r.warehouse_name}</td>
                                        <td className="text-right font-mono">{formatNumber(r.balance)}</td>
                                        <td className="text-right font-mono">{formatCurrency(r.weighted_avg_cost)}</td>
                                        <td className="text-right font-mono font-bold">{formatCurrency(r.total_value)}</td>
                                    </tr>
                                ))}
                                <tr style={{ borderTop: '2px solid #333' }}>
                                    <td colSpan={4} className="font-bold">Grand Total</td>
                                    <td className="text-right font-mono font-bold">{formatCurrency(items.reduce((s, r) => s + (r.total_value || 0), 0))}</td>
                                </tr>
                            </PrintTable>
                        );
                    })()}

                    {activeTab === 'wip-summary' && (() => {
                        const items = Array.isArray(data) ? data : [];
                        return (
                            <PrintTable headers={['Order #', 'Qty (Ordered/Done)', { label: 'Material Cost', align: 'right' }, { label: 'Expense Cost', align: 'right' }, { label: 'Total WIP', align: 'right' }]}>
                                {items.map((r, i) => (
                                    <tr key={i}>
                                        <td className="font-mono">{r.order_number}</td>
                                        <td>{formatNumber(r.order_qty)} / {formatNumber(r.completed_qty)}</td>
                                        <td className="text-right font-mono">{formatCurrency(r.material_cost)}</td>
                                        <td className="text-right font-mono">{formatCurrency(r.expense_cost)}</td>
                                        <td className="text-right font-mono font-bold">{formatCurrency(r.total_wip_value)}</td>
                                    </tr>
                                ))}
                            </PrintTable>
                        );
                    })()}

                    {activeTab === 'material-consumption' && (() => {
                        const items = Array.isArray(data) ? data : [];
                        return (
                            <PrintTable headers={['Material', { label: 'Qty Consumed', align: 'right' }, { label: 'Total Cost', align: 'right' }]}>
                                {items.map((r, i) => (
                                    <tr key={i}>
                                        <td>{r.item_name}</td>
                                        <td className="text-right font-mono">{formatNumber(r.total_quantity)}</td>
                                        <td className="text-right font-mono font-bold">{formatCurrency(r.total_cost)}</td>
                                    </tr>
                                ))}
                                <tr style={{ borderTop: '2px solid #333' }}>
                                    <td colSpan={2} className="font-bold">Total</td>
                                    <td className="text-right font-mono font-bold">{formatCurrency(items.reduce((s, r) => s + (r.total_cost || 0), 0))}</td>
                                </tr>
                            </PrintTable>
                        );
                    })()}

                    {activeTab === 'production-cost' && data && (
                        <>
                            <PrintDetail label="Order" value={data.order_number} />
                            <PrintDetail label="Quantity" value={`${formatNumber(data.order_qty)} ordered / ${formatNumber(data.completed_qty)} completed`} />
                            <PrintDetail label="Total Production Cost" value={formatCurrency(data.total_production_cost)} />
                            <PrintDetail label="Unit Cost" value={formatCurrency(data.unit_cost)} />

                            <h4 className="print-section-title">Materials ({formatCurrency(data.total_material_cost)})</h4>
                            <PrintTable headers={['Material', { label: 'Qty', align: 'right' }, { label: 'Cost', align: 'right' }]}>
                                {(data.materials || []).map((m, i) => (
                                    <tr key={i}>
                                        <td>{m.item_name}</td>
                                        <td className="text-right font-mono">{formatNumber(m.quantity)}</td>
                                        <td className="text-right font-mono">{formatCurrency(m.cost)}</td>
                                    </tr>
                                ))}
                            </PrintTable>

                            <h4 className="print-section-title">Expenses ({formatCurrency(data.total_expenses)})</h4>
                            <PrintTable headers={['Type', 'Description', { label: 'Amount', align: 'right' }]}>
                                {(data.expenses || []).map((e, i) => (
                                    <tr key={i}>
                                        <td>{(e.expense_type || '').replace(/_/g, ' ')}</td>
                                        <td>{e.description}</td>
                                        <td className="text-right font-mono">{formatCurrency(e.amount)}</td>
                                    </tr>
                                ))}
                            </PrintTable>

                            <div className="print-total-row">
                                <span>Total Production Cost</span>
                                <span>{formatCurrency(data.total_production_cost)}</span>
                            </div>
                        </>
                    )}
                </PrintSlip>
            )}
        </div>
    );
}
