import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { reportsAPI } from '../../services/api';
import { formatWeight, formatPercent, statusColor } from '../../utils/formatters';

export default function Reports() {
    const [activeTab, setActiveTab] = useState('stock');
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);

    const tabs = [
        { key: 'stock', label: 'Stock Report' },
        { key: 'wastage', label: 'Wastage' },
        { key: 'efficiency', label: 'Efficiency' },
        { key: 'wip', label: 'WIP Summary' },
        { key: 'batch', label: 'Batch History' },
        { key: 'variance', label: 'Consumption Variance' },
    ];

    useEffect(() => { loadReport(activeTab); }, [activeTab]);

    const loadReport = async (tab) => {
        setLoading(true);
        try {
            const apiMap = {
                stock: reportsAPI.stockReport,
                wastage: reportsAPI.wastageReport,
                efficiency: reportsAPI.efficiencyReport,
                wip: reportsAPI.wipSummary,
                batch: reportsAPI.batchHistory,
                variance: reportsAPI.consumptionVariance,
            };
            const res = await apiMap[tab]();
            setData(res.data);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const renderTable = () => {
        if (data.length === 0) return <div className="empty-state"><p>No data available for this report.</p></div>;

        switch (activeTab) {
            case 'stock':
                return (
                    <>
                        <div className="chart-card mb-4">
                            <div className="chart-title">Stock Levels</div>
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                                    <XAxis dataKey="material_name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                    <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                    <Tooltip contentStyle={{ background: '#1a2332', border: '1px solid #1e2d3d', borderRadius: 8 }} />
                                    <Bar dataKey="current_stock" fill="#c0c0c0" radius={[4, 4, 0, 0]} name="Current" />
                                    <Bar dataKey="reorder_level" fill="#ef4444" radius={[4, 4, 0, 0]} name="Reorder Level" opacity={0.5} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <table className="data-table">
                            <thead><tr><th>Material</th><th>Type</th><th>Stock</th><th>Reorder Level</th><th>Status</th></tr></thead>
                            <tbody>{data.map((r, i) => (
                                <tr key={i}><td className="font-bold">{r.material_name}</td><td>{r.material_type}</td><td className="font-mono">{formatWeight(r.current_stock, r.unit)}</td><td className="font-mono">{formatWeight(r.reorder_level, r.unit)}</td><td><span className={`badge ${statusColor(r.status)}`}>{r.status}</span></td></tr>
                            ))}</tbody>
                        </table>
                    </>
                );
            case 'wastage':
                return (
                    <table className="data-table">
                        <thead><tr><th>Batch</th><th>Product</th><th>Material</th><th>Expected</th><th>Actual</th><th>Variance</th><th>Variance %</th></tr></thead>
                        <tbody>{data.map((r, i) => (
                            <tr key={i}><td className="font-mono">{r.batch_number}</td><td>{r.product_name}</td><td>{r.material_name}</td><td className="font-mono">{formatWeight(r.expected_wastage)}</td><td className="font-mono">{formatWeight(r.actual_wastage)}</td><td className={`font-mono ${parseFloat(r.variance) > 0 ? 'text-red' : 'text-green'}`}>{formatWeight(r.variance)}</td><td>{formatPercent(r.variance_percent)}</td></tr>
                        ))}</tbody>
                    </table>
                );
            case 'efficiency':
                return (
                    <>
                        <div className="chart-card mb-4">
                            <div className="chart-title">Production Efficiency</div>
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                                    <XAxis dataKey="batch_number" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                                    <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} domain={[0, 100]} />
                                    <Tooltip contentStyle={{ background: '#1a2332', border: '1px solid #1e2d3d', borderRadius: 8 }} />
                                    <Bar dataKey="efficiency_percent" fill="#10b981" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <table className="data-table">
                            <thead><tr><th>Batch</th><th>Product</th><th>Planned</th><th>Completed</th><th>Rejected</th><th>Efficiency</th></tr></thead>
                            <tbody>{data.map((r, i) => (
                                <tr key={i}><td className="font-mono">{r.batch_number}</td><td>{r.product_name}</td><td>{r.planned_quantity}</td><td>{r.completed_quantity}</td><td className={r.rejected_quantity > 0 ? 'text-red' : ''}>{r.rejected_quantity}</td><td className={`font-bold ${parseFloat(r.efficiency_percent) >= 90 ? 'text-green' : 'text-amber'}`}>{formatPercent(r.efficiency_percent)}</td></tr>
                            ))}</tbody>
                        </table>
                    </>
                );
            case 'wip':
                return (
                    <table className="data-table">
                        <thead><tr><th>Product</th><th>In Process</th><th>Completed</th><th>Rejected</th></tr></thead>
                        <tbody>{data.map((r, i) => (
                            <tr key={i}><td className="font-bold">{r.product_name}</td><td className="font-mono text-blue">{parseFloat(r.total_in_process).toFixed(0)}</td><td className="font-mono text-green">{parseFloat(r.total_completed).toFixed(0)}</td><td className="font-mono text-red">{parseFloat(r.total_rejected).toFixed(0)}</td></tr>
                        ))}</tbody>
                    </table>
                );
            case 'batch':
                return (
                    <table className="data-table">
                        <thead><tr><th>Batch</th><th>Product</th><th>Planned</th><th>Completed</th><th>Status</th><th>Started</th><th>Finished</th></tr></thead>
                        <tbody>{data.map((r, i) => (
                            <tr key={i}><td className="font-mono">{r.batch_number}</td><td>{r.product_name}</td><td>{r.planned_quantity}</td><td>{r.completed_quantity}</td><td><span className={`badge ${statusColor(r.status)}`}>{r.status.replace('_', ' ')}</span></td><td>{r.started_at ? new Date(r.started_at).toLocaleDateString() : '—'}</td><td>{r.completed_at ? new Date(r.completed_at).toLocaleDateString() : '—'}</td></tr>
                        ))}</tbody>
                    </table>
                );
            case 'variance':
                return (
                    <table className="data-table">
                        <thead><tr><th>Batch</th><th>Product</th><th>Material</th><th>Required</th><th>Actual</th><th>Variance</th><th>Variance %</th></tr></thead>
                        <tbody>{data.map((r, i) => (
                            <tr key={i}><td className="font-mono">{r.batch_number}</td><td>{r.product_name}</td><td>{r.material_name}</td><td className="font-mono">{formatWeight(r.required_quantity)}</td><td className="font-mono">{formatWeight(r.actual_quantity)}</td><td className="font-mono">{formatWeight(r.variance)}</td><td>{formatPercent(r.variance_percent)}</td></tr>
                        ))}</tbody>
                    </table>
                );
            default: return null;
        }
    };

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Reports</h1>
                    <p className="page-subtitle">Manufacturing analytics & insights</p>
                </div>
            </div>

            <div className="filter-bar mb-4">
                {tabs.map(t => (
                    <button key={t.key} className={`btn ${activeTab === t.key ? 'btn-primary' : 'btn-secondary'} btn-sm`} onClick={() => setActiveTab(t.key)}>
                        {t.label}
                    </button>
                ))}
            </div>

            <div className="card">
                <div className="data-table-wrapper">
                    {loading ? <div className="empty-state"><p>Loading report...</p></div> : renderTable()}
                </div>
            </div>
        </div>
    );
}
