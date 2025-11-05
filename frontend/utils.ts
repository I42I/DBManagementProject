export function toISOZ(d: Date | string): string {
    if (typeof d === 'string') {
        if (d.endsWith('Z')) return d;
        const dt = new Date(d);
        const utc = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000);
        return utc.toISOString().replace(/\.\d{3}Z$/, 'Z');
    }
    const utc = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
    return utc.toISOString().replace(/\.\d{3}Z$/, 'Z');
}

export function formatName(p: { identite?: { prenom?: string; nom?: string } } | null) {
    if (!p?.identite) return '—';
    const { prenom = '', nom = '' } = p.identite;
    return `${prenom} ${nom}`.trim() || '—';
}