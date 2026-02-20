import { useState, useEffect } from 'react';
import { HiOutlineCube, HiOutlineCog, HiOutlineClipboardList, HiOutlineArchive, HiOutlineExclamation, HiOutlineTrendingUp, HiArrowRight } from 'react-icons/hi';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { rawMaterialsAPI, reportsAPI, productionAPI, wipAPI, finishedGoodsAPI } from '../services/api';
import { formatWeight } from '../utils/formatters';

export default function Dashboard() {
    const [stats, setStats] = useState({ silver: 0, brass: 0, batches: 0, wip: 0, fg: 0, alerts: 0 });
    const [stockData, setStockData] = useState([]);
    const [efficiencyData, setEfficiencyData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboard();
    }, []);

    const loadDashboard = async () => {
        try {
            const [materialsRes, stockRes, effRes, batchRes, wipRes, fgRes] = await Promise.all([
                rawMaterialsAPI.list(),
                reportsAPI.stockReport(),
                reportsAPI.efficiencyReport(),
                productionAPI.listBatches('in_progress'),
                wipAPI.list(),
                finishedGoodsAPI.list(),
            ]);

            const materials = materialsRes.data;
            const silver = materials.find(m => m.material_type === 'SILVER');
            const brass = materials.find(m => m.material_type === 'BRASS');

            const stockReport = stockRes.data;
            const alertCount = stockReport.filter(s => s.status === 'critical' || s.status === 'low').length;

            setStats({
                silver: silver?.current_stock || 0,
                brass: brass?.current_stock || 0,
                batches: batchRes.data.length,
                wip: wipRes.data.filter(w => w.status === 'in_process').length,
                fg: fgRes.data.reduce((sum, fg) => sum + parseFloat(fg.quantity), 0),
                alerts: alertCount,
            });

            setStockData(stockReport);
            setEfficiencyData(effRes.data.slice(0, 10));
        } catch (err) {
            console.error('Dashboard load error:', err);
        } finally {
            setLoading(false);
        }
    };

    const PIE_COLORS = ['#c0c0c0', '#cd9b47', '#3b82f6', '#10b981', '#8b5cf6'];

    if (loading) {
        return <div className="empty-state"><p>Loading dashboard...</p></div>;
    }

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Dashboard</h1>
                    <p className="page-subtitle">Manufacturing overview & key metrics</p>
                </div>
            </div>

            {/* Production Flow Visualization */}
            <div className="production-flow">
                <div className="flow-step">
                    <div className="flow-step-label">Raw Materials</div>
                    <div className="flow-step-value">{formatWeight(stats.silver + stats.brass)}</div>
                </div>
                <div className="flow-arrow"><HiArrowRight /></div>
                <div className="flow-step active">
                    <div className="flow-step-label">Work In Progress</div>
                    <div className="flow-step-value">{stats.wip}</div>
                </div>
                <div className="flow-arrow"><HiArrowRight /></div>
                <div className="flow-step">
                    <div className="flow-step-label">Finished Goods</div>
                    <div className="flow-step-value">{parseFloat(stats.fg).toFixed(0)}</div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon silver"><HiOutlineCube /></div>
                    <div className="stat-info">
                        <div className="stat-label">Silver Stock</div>
                        <div className="stat-value">{formatWeight(stats.silver)}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon brass"><HiOutlineCube /></div>
                    <div className="stat-info">
                        <div className="stat-label">Brass Stock</div>
                        <div className="stat-value">{formatWeight(stats.brass)}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon blue"><HiOutlineCog /></div>
                    <div className="stat-info">
                        <div className="stat-label">Active Batches</div>
                        <div className="stat-value">{stats.batches}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon cyan"><HiOutlineClipboardList /></div>
                    <div className="stat-info">
                        <div className="stat-label">WIP Items</div>
                        <div className="stat-value">{stats.wip}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon green"><HiOutlineArchive /></div>
                    <div className="stat-info">
                        <div className="stat-label">Finished Goods</div>
                        <div className="stat-value">{parseFloat(stats.fg).toFixed(0)}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon red"><HiOutlineExclamation /></div>
                    <div className="stat-info">
                        <div className="stat-label">Alerts</div>
                        <div className="stat-value">{stats.alerts}</div>
                        {stats.alerts > 0 && <div className="stat-change negative">Needs attention</div>}
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="charts-grid">
                <div className="chart-card">
                    <div className="chart-title">Raw Material Stock Levels</div>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={stockData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                            <XAxis dataKey="material_name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                            <Tooltip
                                contentStyle={{ background: '#1a2332', border: '1px solid #1e2d3d', borderRadius: 8 }}
                                labelStyle={{ color: '#e2e8f0' }}
                            />
                            <Bar dataKey="current_stock" fill="#c0c0c0" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="reorder_level" fill="#ef4444" radius={[4, 4, 0, 0]} opacity={0.5} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="chart-card">
                    <div className="chart-title">Production Efficiency (Recent Batches)</div>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={efficiencyData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                            <XAxis dataKey="batch_number" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} domain={[0, 100]} />
                            <Tooltip
                                contentStyle={{ background: '#1a2332', border: '1px solid #1e2d3d', borderRadius: 8 }}
                                labelStyle={{ color: '#e2e8f0' }}
                            />
                            <Bar dataKey="efficiency_percent" fill="#10b981" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
