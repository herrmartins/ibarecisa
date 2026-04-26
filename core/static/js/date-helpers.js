function dateISOtoBR(isoDate) {
    if (!isoDate) return '';
    const parts = String(isoDate).split('-');
    if (parts.length !== 3) return isoDate;
    return parts[2] + '/' + parts[1] + '/' + parts[0];
}

function dateBRtoISO(brDate) {
    if (!brDate) return '';
    const parts = String(brDate).split('/');
    if (parts.length !== 3) return brDate;
    return parts[2] + '-' + parts[1].padStart(2, '0') + '-' + parts[0].padStart(2, '0');
}
