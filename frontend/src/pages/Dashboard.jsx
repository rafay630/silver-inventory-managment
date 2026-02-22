import { useState, useEffect } from 'react';
import { HiOutlineCube, HiOutlineCog, HiOutlineCurrencyDollar, HiOutlineShoppingCart, HiOutlineChartBar, HiOutlineClipboardList, HiArrowRight } from 'react-icons/hi';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { itemsAPI, stockLedgerAPI, productionAPI, salesAPI, accountingAPI } from '../services/api';
import { formatCurrency, formatNumber } from '../utils/formatters';

export default function Dashboard() {
    const [stats, setStats] = useState({ items: 0, rawMaterials: 0, finishedGoods: 0, productionOrders: 0, inProgress: 0, salesOrders: 0, totalRevenue: 0, totalInventoryValue: 0 });
    const [stockData, setStockData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => { loadDashboard(); }, []);

    const loadDashboard = async () => {
        try {
            const [itemsRes, balancesRes, prodRes, salesRes, trialRes] = await Promise.all([
                itemsAPI.list(),
                stockLedgerAPI.balances(),
                productionAPI.list(),
                salesAPI.list(),
                accountingAPI.trialBalance(),
            ]);

            const items = itemsRes.data;
            const balances = balancesRes.data;
            const orders = prodRes.data;
            const sales = salesRes.data;

            const totalInventoryValue = balances.reduce((sum, b) => sum + parseFloat(b.total_value || 0), 0);
            const totalRevenue = sales.reduce((sum, s) => sum + parseFloat(s.total_amount || 0), 0);

            setStats({
                items: items.length,
                rawMaterials: items.filter(i => i.item_type === 'raw_material').length,
                finishedGoods: items.filter(i => i.item_type === 'finished_good').length,
                productionOrders: orders.length,
                inProgress: orders.filter(o => o.status === 'in_progress').length,
                salesOrders: sales.length,
                totalRevenue,
                totalInventoryValue,
            });

            // Prepare chart data from stock balances
            const chartData = balances
                .filter(b => parseFloat(b.balance) > 0)
                .map(b => ({
                    name: b.item_name?.length > 15 ? b.item_name.substring(0, 15) + '…' : b.item_name,
                    balance: parseFloat(b.balance),
                    value: parseFloat(b.total_value || 0),
                }));
            setStockData(chartData);
        } catch (err) {
            console.error('Dashboard load error:', err);
        } finally {
            setLoading(false);
        }
    };

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
                    <div className="flow-step-value">{stats.rawMaterials}</div>
                </div>
                <div className="flow-arrow"><HiArrowRight /></div>
                <div className="flow-step active">
                    <div className="flow-step-label">In Production</div>
                    <div className="flow-step-value">{stats.inProgress}</div>
                </div>
                <div className="flow-arrow"><HiArrowRight /></div>
                <div className="flow-step">
                    <div className="flow-step-label">Finished Goods</div>
                    <div className="flow-step-value">{stats.finishedGoods}</div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon silver"><HiOutlineCube /></div>
                    <div className="stat-info">
                        <div className="stat-label">Total Items</div>
                        <div className="stat-value">{stats.items}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon cyan"><HiOutlineChartBar /></div>
                    <div className="stat-info">
                        <div className="stat-label">Inventory Value</div>
                        <div className="stat-value">{formatCurrency(stats.totalInventoryValue)}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon blue"><HiOutlineCog /></div>
                    <div className="stat-info">
                        <div className="stat-label">Production Orders</div>
                        <div className="stat-value">{stats.productionOrders}</div>
                        {stats.inProgress > 0 && <div className="stat-change positive">{stats.inProgress} in progress</div>}
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon green"><HiOutlineShoppingCart /></div>
                    <div className="stat-info">
                        <div className="stat-label">Sales Orders</div>
                        <div className="stat-value">{stats.salesOrders}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon amber"><HiOutlineCurrencyDollar /></div>
                    <div className="stat-info">
                        <div className="stat-label">Total Revenue</div>
                        <div className="stat-value">{formatCurrency(stats.totalRevenue)}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon purple"><HiOutlineClipboardList /></div>
                    <div className="stat-info">
                        <div className="stat-label">Finished Goods</div>
                        <div className="stat-value">{stats.finishedGoods}</div>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="charts-grid">
                <div className="chart-card">
                    <div className="chart-title">Stock Balances (Quantity)</div>
                    {stockData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={stockData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ background: '#1a2332', border: '1px solid #1e2d3d', borderRadius: 8 }}
                                    labelStyle={{ color: '#e2e8f0' }}
                                />
                                <Bar dataKey="balance" fill="#c0c0c0" radius={[4, 4, 0, 0]} name="Balance" />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="empty-state"><p>No stock data available</p></div>
                    )}
                </div>

                <div className="chart-card">
                    <div className="chart-title">Inventory Value by Item ($)</div>
                    {stockData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={stockData.filter(d => d.value > 0)}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ background: '#1a2332', border: '1px solid #1e2d3d', borderRadius: 8 }}
                                    labelStyle={{ color: '#e2e8f0' }}
                                    formatter={(value) => [`$${parseFloat(value).toFixed(2)}`, 'Value']}
                                />
                                <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} name="Value" />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="empty-state"><p>No valuation data available</p></div>
                    )}
                </div>
            </div>
        </div>
    );
}
