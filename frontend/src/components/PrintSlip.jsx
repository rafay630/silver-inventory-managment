import { useRef } from 'react';

/**
 * Reusable print slip component.
 * Renders a clean, print-optimized document in a modal overlay.
 * 
 * Props:
 *   title        - Slip title (e.g. "Sales Invoice", "Production Order")
 *   refNumber    - Reference number (e.g. "SO-000001")
 *   date         - Date string to display
 *   onClose      - Close handler
 *   children     - Slip body content (tables, summaries, etc.)
 *   footer       - Optional extra footer content
 */
export default function PrintSlip({ title, refNumber, date, onClose, children, footer }) {
    const slipRef = useRef();

    const handlePrint = () => {
        window.print();
    };

    return (
        <div className="modal-overlay print-overlay" onClick={onClose}>
            <div className="print-slip-container" onClick={e => e.stopPropagation()}>
                {/* Screen-only toolbar */}
                <div className="print-toolbar no-print">
                    <button className="btn btn-primary btn-sm" onClick={handlePrint}>🖨️ Print</button>
                    <button className="btn btn-secondary btn-sm" onClick={onClose}>✕ Close</button>
                </div>

                {/* Printable slip */}
                <div className="print-slip" ref={slipRef}>
                    <div className="print-header">
                        <div className="print-company">
                            <h2 className="print-company-name">Silver Inventory</h2>
                            <p className="print-company-sub">Manufacturing ERP System</p>
                        </div>
                        <div className="print-doc-info">
                            <h3 className="print-doc-title">{title}</h3>
                            <p className="print-ref"><strong>Ref:</strong> {refNumber}</p>
                            {date && <p className="print-date"><strong>Date:</strong> {date}</p>}
                        </div>
                    </div>

                    <div className="print-divider" />

                    <div className="print-body">
                        {children}
                    </div>

                    <div className="print-divider" />

                    <div className="print-footer">
                        {footer && <div className="print-footer-extra">{footer}</div>}
                        <div className="print-footer-meta">
                            <p>System Generated — {new Date().toLocaleString()}</p>
                            <p>Silver Inventory Manufacturing ERP</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

/**
 * Helper: Print detail row (label + value)
 */
export function PrintDetail({ label, value }) {
    return (
        <div className="print-detail-row">
            <span className="print-detail-label">{label}</span>
            <span className="print-detail-value">{value}</span>
        </div>
    );
}

/**
 * Helper: Print table wrapper
 */
export function PrintTable({ headers, children }) {
    return (
        <table className="print-table">
            <thead>
                <tr>
                    {headers.map((h, i) => (
                        <th key={i} className={h.align === 'right' ? 'text-right' : ''}>{h.label || h}</th>
                    ))}
                </tr>
            </thead>
            <tbody>{children}</tbody>
        </table>
    );
}
