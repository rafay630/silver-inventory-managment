import { useState, useEffect } from 'react';
import { accountingAPI } from '../../services/api';
import { formatCurrency, formatDate } from '../../utils/formatters';
import PrintSlip, { PrintDetail, PrintTable } from '../../components/PrintSlip';

export default function Accounting() {
    const [activeTab, setActiveTab] = useState('trial-balance');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [accounts, setAccounts] = useState([]);
    const [journalEntries, setJournalEntries] = useState([]);
    const [printJE, setPrintJE] = useState(null);
    const [printReport, setPrintReport] = useState(false);

    useEffect(() => { loadTab(); }, [activeTab]);

    const loadTab = async () => {
        setLoading(true);
        try {
            if (activeTab === 'trial-balance') {
                const res = await accountingAPI.trialBalance();
                setData(res.data);
            } else if (activeTab === 'profit-loss') {
                const res = await accountingAPI.profitAndLoss('2025-01-01', '2026-12-31');
                setData(res.data);
            } else if (activeTab === 'balance-sheet') {
                const res = await accountingAPI.balanceSheet();
                setData(res.data);
            } else if (activeTab === 'accounts') {
                const res = await accountingAPI.listAccounts();
                setAccounts(res.data);
            } else if (activeTab === 'journal-entries') {
                const res = await accountingAPI.listJournalEntries({ limit: 50 });
                setJournalEntries(res.data);
            }
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    const tabs = [
        { id: 'trial-balance', label: 'Trial Balance' },
        { id: 'profit-loss', label: 'Profit & Loss' },
        { id: 'balance-sheet', label: 'Balance Sheet' },
        { id: 'accounts', label: 'Chart of Accounts' },
        { id: 'journal-entries', label: 'Journal Entries' },
    ];

    const reportTitles = {
        'trial-balance': 'Trial Balance',
        'profit-loss': 'Profit & Loss Statement',
        'balance-sheet': 'Balance Sheet',
    };

    const renderContent = () => {
        if (loading) return <div className="empty-state"><p>Loading...</p></div>;

        if (activeTab === 'trial-balance') {
            if (!data) return null;
            const rows = data.rows || [];
            return (
                <>
                    <div className="mb-4" style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
                        As of: {formatDate(data.as_of_date)}
                    </div>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Code</th>
                                <th>Account Name</th>
                                <th>Type</th>
                                <th className="text-right">Debit</th>
                                <th className="text-right">Credit</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map((r, i) => (
                                <tr key={i}>
                                    <td className="font-mono">{r.account_code}</td>
                                    <td className="font-bold">{r.account_name}</td>
                                    <td><span className="badge badge-silver">{r.account_type}</span></td>
                                    <td className="text-right font-mono">{parseFloat(r.debit) > 0 ? formatCurrency(r.debit) : ''}</td>
                                    <td className="text-right font-mono">{parseFloat(r.credit) > 0 ? formatCurrency(r.credit) : ''}</td>
                                </tr>
                            ))}
                        </tbody>
                        <tfoot>
                            <tr style={{ borderTop: '2px solid var(--accent-silver)' }}>
                                <td colSpan={3} className="font-bold">TOTALS</td>
                                <td className="text-right font-mono font-bold">{formatCurrency(data.total_debit)}</td>
                                <td className="text-right font-mono font-bold">{formatCurrency(data.total_credit)}</td>
                            </tr>
                        </tfoot>
                    </table>
                    <p className="mt-4">
                        <span className={`badge ${data.is_balanced ? 'badge-green' : 'badge-red'}`}>
                            {data.is_balanced ? '✓ Trial Balance is Balanced' : '⚠ Trial Balance is Unbalanced'}
                        </span>
                    </p>
                </>
            );
        }

        if (activeTab === 'profit-loss' && data) {
            const income = data.income || [];
            const expenses = data.expenses || [];
            return (
                <div>
                    <div className="stats-grid mb-6">
                        <div className="stat-card">
                            <div className="stat-icon green">💰</div>
                            <div className="stat-info"><div className="stat-label">Total Income</div><div className="stat-value">{formatCurrency(data.total_income)}</div></div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon red">📊</div>
                            <div className="stat-info"><div className="stat-label">Total Expenses</div><div className="stat-value">{formatCurrency(data.total_expenses)}</div></div>
                        </div>
                        <div className="stat-card">
                            <div className={`stat-icon ${parseFloat(data.net_profit) >= 0 ? 'cyan' : 'red'}`}>🏆</div>
                            <div className="stat-info"><div className="stat-label">Net Profit</div><div className="stat-value">{formatCurrency(data.net_profit)}</div></div>
                        </div>
                    </div>
                    {income.length > 0 && (
                        <div className="card mb-4">
                            <h4 className="card-title mb-4" style={{ color: 'var(--accent-green)' }}>Income</h4>
                            <table className="data-table">
                                <thead><tr><th>Account</th><th className="text-right">Amount</th></tr></thead>
                                <tbody>
                                    {income.map((a, i) => <tr key={i}><td>{a.account_name}</td><td className="text-right font-mono text-green">{formatCurrency(a.balance)}</td></tr>)}
                                </tbody>
                            </table>
                        </div>
                    )}
                    {expenses.length > 0 && (
                        <div className="card">
                            <h4 className="card-title mb-4" style={{ color: 'var(--accent-red)' }}>Expenses</h4>
                            <table className="data-table">
                                <thead><tr><th>Account</th><th className="text-right">Amount</th></tr></thead>
                                <tbody>
                                    {expenses.map((a, i) => <tr key={i}><td>{a.account_name}</td><td className="text-right font-mono text-red">{formatCurrency(a.balance)}</td></tr>)}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            );
        }

        if (activeTab === 'balance-sheet' && data) {
            const renderSection = (title, items, color) => items?.length > 0 && (
                <div className="card mt-4">
                    <h4 className="card-title mb-4" style={{ color: `var(--accent-${color})` }}>{title}</h4>
                    <table className="data-table">
                        <thead><tr><th>Account</th><th className="text-right">Balance</th></tr></thead>
                        <tbody>{items.map((a, i) => <tr key={i}><td>{a.account_name}</td><td className={`text-right font-mono text-${color}`}>{formatCurrency(a.balance)}</td></tr>)}</tbody>
                    </table>
                </div>
            );
            return (
                <div>
                    <div className="stats-grid mb-4">
                        <div className="stat-card"><div className="stat-icon green">📦</div><div className="stat-info"><div className="stat-label">Total Assets</div><div className="stat-value">{formatCurrency(data.total_assets)}</div></div></div>
                        <div className="stat-card"><div className="stat-icon red">📋</div><div className="stat-info"><div className="stat-label">Total Liabilities</div><div className="stat-value">{formatCurrency(data.total_liabilities)}</div></div></div>
                        <div className="stat-card"><div className="stat-icon cyan">🏛</div><div className="stat-info"><div className="stat-label">Total Equity</div><div className="stat-value">{formatCurrency(data.total_equity)}</div></div></div>
                    </div>
                    {renderSection('Assets', data.assets, 'green')}
                    {renderSection('Liabilities', data.liabilities, 'red')}
                    {renderSection('Equity', data.equity, 'blue')}
                </div>
            );
        }

        if (activeTab === 'accounts') {
            return (
                <table className="data-table">
                    <thead><tr><th>Code</th><th>Account Name</th><th>Type</th><th>Parent</th></tr></thead>
                    <tbody>
                        {accounts.map(a => <tr key={a.id}><td className="font-mono">{a.code}</td><td className="font-bold">{a.name}</td><td><span className="badge badge-silver">{a.account_type}</span></td><td className="text-muted">{a.parent_code || '—'}</td></tr>)}
                        {accounts.length === 0 && <tr><td colSpan={4} className="empty-state"><p>No accounts.</p></td></tr>}
                    </tbody>
                </table>
            );
        }

        if (activeTab === 'journal-entries') {
            return (
                <table className="data-table">
                    <thead><tr><th>Entry #</th><th>Date</th><th>Narration</th><th>Reference</th><th>Lines</th><th>Actions</th></tr></thead>
                    <tbody>
                        {journalEntries.map(je => (
                            <tr key={je.id}>
                                <td className="font-mono font-bold">{je.entry_number || je.id.substring(0, 8)}</td>
                                <td className="font-mono" style={{ fontSize: 'var(--font-xs)' }}>{formatDate(je.entry_date)}</td>
                                <td className="font-bold">{je.narration || je.description || '—'}</td>
                                <td className="font-mono" style={{ fontSize: 'var(--font-xs)' }}>{je.reference_type || '—'}</td>
                                <td>{je.lines?.length || 0}</td>
                                <td><button className="btn btn-secondary btn-sm" onClick={() => setPrintJE(je)}>🖨️</button></td>
                            </tr>
                        ))}
                        {journalEntries.length === 0 && <tr><td colSpan={6} className="empty-state"><p>No entries.</p></td></tr>}
                    </tbody>
                </table>
            );
        }

        return null;
    };

    const isPrintableReport = ['trial-balance', 'profit-loss', 'balance-sheet'].includes(activeTab);

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Accounting</h1>
                    <p className="page-subtitle">Financial reports & double-entry ledger</p>
                </div>
                {isPrintableReport && data && (
                    <button className="btn btn-secondary" onClick={() => setPrintReport(true)}>🖨️ Print Report</button>
                )}
            </div>
            <div className="filter-bar mb-4 flex gap-3" style={{ overflowX: 'auto' }}>
                {tabs.map(tab => <button key={tab.id} className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-secondary'} btn-sm`} onClick={() => setActiveTab(tab.id)}>{tab.label}</button>)}
            </div>
            <div className="card"><div className="data-table-wrapper">{renderContent()}</div></div>

            {/* Print Journal Entry Voucher */}
            {printJE && (
                <PrintSlip
                    title="Journal Voucher"
                    refNumber={`JE-${printJE.entry_number || printJE.id.substring(0, 8)}`}
                    date={formatDate(printJE.entry_date)}
                    onClose={() => setPrintJE(null)}
                >
                    <PrintDetail label="Narration" value={printJE.narration || printJE.description || '—'} />
                    <PrintDetail label="Reference Type" value={printJE.reference_type || '—'} />
                    <PrintDetail label="Posted" value={printJE.is_posted ? 'Yes' : 'No'} />
                    <PrintTable headers={['Account', { label: 'Debit', align: 'right' }, { label: 'Credit', align: 'right' }]}>
                        {(printJE.lines || []).map((line, i) => (
                            <tr key={i}>
                                <td>{line.account_name || line.account_code || '—'}</td>
                                <td className="text-right font-mono">{parseFloat(line.debit || 0) > 0 ? formatCurrency(line.debit) : ''}</td>
                                <td className="text-right font-mono">{parseFloat(line.credit || 0) > 0 ? formatCurrency(line.credit) : ''}</td>
                            </tr>
                        ))}
                        <tr style={{ borderTop: '2px solid var(--accent-silver)' }}>
                            <td className="font-bold">TOTAL</td>
                            <td className="text-right font-mono font-bold">{formatCurrency((printJE.lines || []).reduce((s, l) => s + (parseFloat(l.debit) || 0), 0))}</td>
                            <td className="text-right font-mono font-bold">{formatCurrency((printJE.lines || []).reduce((s, l) => s + (parseFloat(l.credit) || 0), 0))}</td>
                        </tr>
                    </PrintTable>
                </PrintSlip>
            )}

            {/* Print Financial Report */}
            {printReport && data && (
                <PrintSlip
                    title={reportTitles[activeTab] || 'Financial Report'}
                    refNumber={`RPT-${new Date().toISOString().split('T')[0]}`}
                    date={new Date().toLocaleDateString()}
                    onClose={() => setPrintReport(false)}
                >
                    {activeTab === 'trial-balance' && (
                        <>
                            <PrintDetail label="As of" value={formatDate(data.as_of_date)} />
                            <PrintTable headers={['Code', 'Account', 'Type', { label: 'Debit', align: 'right' }, { label: 'Credit', align: 'right' }]}>
                                {(data.rows || []).map((r, i) => (
                                    <tr key={i}>
                                        <td className="font-mono">{r.account_code}</td>
                                        <td>{r.account_name}</td>
                                        <td>{r.account_type}</td>
                                        <td className="text-right font-mono">{parseFloat(r.debit) > 0 ? formatCurrency(r.debit) : ''}</td>
                                        <td className="text-right font-mono">{parseFloat(r.credit) > 0 ? formatCurrency(r.credit) : ''}</td>
                                    </tr>
                                ))}
                                <tr style={{ borderTop: '2px solid #333' }}>
                                    <td colSpan={3} className="font-bold">TOTALS</td>
                                    <td className="text-right font-mono font-bold">{formatCurrency(data.total_debit)}</td>
                                    <td className="text-right font-mono font-bold">{formatCurrency(data.total_credit)}</td>
                                </tr>
                            </PrintTable>
                        </>
                    )}
                    {activeTab === 'profit-loss' && (
                        <>
                            <PrintDetail label="Period" value={`${formatDate(data.from_date)} to ${formatDate(data.to_date)}`} />
                            {(data.income || []).length > 0 && (
                                <>
                                    <h4 className="print-section-title">Income</h4>
                                    <PrintTable headers={['Account', { label: 'Amount', align: 'right' }]}>
                                        {data.income.map((a, i) => <tr key={i}><td>{a.account_name}</td><td className="text-right font-mono">{formatCurrency(a.balance)}</td></tr>)}
                                        <tr style={{ borderTop: '2px solid #333' }}><td className="font-bold">Total Income</td><td className="text-right font-mono font-bold">{formatCurrency(data.total_income)}</td></tr>
                                    </PrintTable>
                                </>
                            )}
                            {(data.expenses || []).length > 0 && (
                                <>
                                    <h4 className="print-section-title">Expenses</h4>
                                    <PrintTable headers={['Account', { label: 'Amount', align: 'right' }]}>
                                        {data.expenses.map((a, i) => <tr key={i}><td>{a.account_name}</td><td className="text-right font-mono">{formatCurrency(a.balance)}</td></tr>)}
                                        <tr style={{ borderTop: '2px solid #333' }}><td className="font-bold">Total Expenses</td><td className="text-right font-mono font-bold">{formatCurrency(data.total_expenses)}</td></tr>
                                    </PrintTable>
                                </>
                            )}
                            <div className="print-total-row"><span>Net Profit</span><span>{formatCurrency(data.net_profit)}</span></div>
                        </>
                    )}
                    {activeTab === 'balance-sheet' && (
                        <>
                            <PrintDetail label="As of" value={formatDate(data.as_of_date)} />
                            {['assets', 'liabilities', 'equity'].map(section => (data[section] || []).length > 0 && (
                                <div key={section}>
                                    <h4 className="print-section-title">{section.charAt(0).toUpperCase() + section.slice(1)}</h4>
                                    <PrintTable headers={['Account', { label: 'Balance', align: 'right' }]}>
                                        {data[section].map((a, i) => <tr key={i}><td>{a.account_name}</td><td className="text-right font-mono">{formatCurrency(a.balance)}</td></tr>)}
                                        <tr style={{ borderTop: '2px solid #333' }}><td className="font-bold">Total {section.charAt(0).toUpperCase() + section.slice(1)}</td><td className="text-right font-mono font-bold">{formatCurrency(data[`total_${section}`])}</td></tr>
                                    </PrintTable>
                                </div>
                            ))}
                        </>
                    )}
                </PrintSlip>
            )}
        </div>
    );
}
