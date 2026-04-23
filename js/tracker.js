/**
 * Tracker Module — Page time tracking and event logging
 * 
 * Include this script AFTER api.js in pages where tracking is needed:
 *   <script src="js/api.js"></script>
 *   <script src="js/tracker.js"></script>
 * 
 * Automatically tracks:
 * - Time spent on the current page
 * - Sends heartbeat every 30 seconds to backend
 * - Logs page visit event on load
 */

(function () {
    let startTime = Date.now();
    let heartbeatInterval = null;
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';

    // Determine bab from page if applicable
    function getBabFromPage() {
        const params = new URLSearchParams(window.location.search);
        return params.get('bab') || '';
    }

    function getElapsedSeconds() {
        return Math.round((Date.now() - startTime) / 1000);
    }

    function startTracking() {
        const nip = getCurrentNip();
        if (!nip) return;

        // Log page visit
        trackEvent(nip, currentPage, 'page_visit', 0).catch(() => { });

        // Heartbeat every 30 seconds
        heartbeatInterval = setInterval(() => {
            const elapsed = getElapsedSeconds();
            trackEvent(nip, currentPage, 'heartbeat', elapsed).catch(() => { });

            // Also update time for materi pages
            const bab = getBabFromPage();
            if (bab) {
                trackTime(nip, bab, 30).catch(() => { });
            }
        }, 30000);
    }

    function stopTracking() {
        if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
        }

        const nip = getCurrentNip();
        if (!nip) return;

        const elapsed = getElapsedSeconds();
        // Send final event (using sendBeacon for reliability on page close)
        const data = JSON.stringify({
            page: currentPage,
            action: 'page_leave',
            duration_seconds: elapsed,
        });

        const url = `${API_BASE_URL}/materi/${nip}/track`;
        if (navigator.sendBeacon) {
            navigator.sendBeacon(url, new Blob([data], { type: 'application/json' }));
        }
    }

    // Start on load
    document.addEventListener('DOMContentLoaded', startTracking);

    // Stop on unload
    window.addEventListener('beforeunload', stopTracking);
    window.addEventListener('pagehide', stopTracking);
})();
