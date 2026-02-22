export function formatWeight(value, unit = 'g') {
    if (value === null || value === undefined) return '—';
    const num = parseFloat(value);
    if (isNaN(num)) return '—';
    return `${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })} ${unit}`;
}

export function formatCurrency(value) {
    if (value === null || value === undefined) return '—';
    const num = parseFloat(value);
    if (isNaN(num)) return '—';
    return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined) return '—';
    const num = parseFloat(value);
    if (isNaN(num)) return '—';
    return num.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
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
        planned: 'badge-silver',
        in_progress: 'badge-blue',
        in_process: 'badge-blue',
        completed: 'badge-green',
        cancelled: 'badge-red',
        rejected: 'badge-red',
        confirmed: 'badge-green',
        draft: 'badge-silver',
        healthy: 'badge-green',
        low: 'badge-amber',
        critical: 'badge-red',
        active: 'badge-green',
        inactive: 'badge-red',
    };
    return map[status] || 'badge-silver';
}

export function itemTypeLabel(type) {
    const map = {
        raw_material: 'Raw Material',
        finished_good: 'Finished Good',
    };
    return map[type] || type;
}

export function itemTypeBadge(type) {
    const map = {
        raw_material: 'badge-amber',
        finished_good: 'badge-green',
    };
    return map[type] || 'badge-silver';
}
