export function formatWeight(value, unit = 'g') {
    if (value === null || value === undefined) return '—';
    const num = parseFloat(value);
    if (isNaN(num)) return '—';
    return `${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })} ${unit}`;
}

export function formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
    });
}

export function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}

export function formatPercent(value) {
    if (value === null || value === undefined) return '—';
    return `${parseFloat(value).toFixed(2)}%`;
}

export function statusColor(status) {
    const map = {
        in_progress: 'badge-blue',
        in_process: 'badge-blue',
        completed: 'badge-green',
        cancelled: 'badge-red',
        rejected: 'badge-red',
        healthy: 'badge-green',
        low: 'badge-amber',
        critical: 'badge-red',
    };
    return map[status] || 'badge-silver';
}
