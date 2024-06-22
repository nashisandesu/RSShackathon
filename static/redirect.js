window.addEventListener('pageshow', function(event) {
    const navEntries = performance.getEntriesByType('navigation');
    if (event.persisted || (navEntries.length > 0 && navEntries[0].type === 'reload')) {
        window.location.href = '/logout';
    }
});