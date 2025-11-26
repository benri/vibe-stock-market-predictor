/**
 * API Usage Store - Centralized state management for API quota tracking
 * Alpine.store for managing API usage data
 */

document.addEventListener('alpine:init', () => {
    Alpine.store('apiUsage', {
        // State
        today: {
            calls: 0,
            remaining: 25,
            limit: 25,
            percentage_used: 0
        },
        loading: false,
        error: null,
        refreshInterval: null,

        // Load API usage data
        async load(days = 1) {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch(`/api/api-usage?days=${days}`);
                const data = await response.json();

                if (data && data.today) {
                    this.today = data.today;
                }
            } catch (error) {
                this.error = error.message;
                console.error('Error loading API usage:', error);
            } finally {
                this.loading = false;
            }
        },

        // Start auto-refresh
        startAutoRefresh(intervalMs = 30000) {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }

            this.refreshInterval = setInterval(() => {
                this.load();
            }, intervalMs);

            // Load immediately
            this.load();
        },

        // Stop auto-refresh
        stopAutoRefresh() {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
        },

        // Get status message based on usage
        getStatusMessage() {
            const remaining = this.today.remaining || 0;
            const percentage = this.today.percentage_used || 0;

            if (remaining === 0) {
                return '⚠️ Daily limit reached! Trading paused until tomorrow.';
            } else if (percentage >= 80) {
                return `⚠️ ${remaining} calls remaining - approaching limit`;
            } else if (percentage >= 60) {
                return `✓ ${remaining} calls remaining - good capacity`;
            } else {
                return `✓ ${remaining} calls remaining - excellent capacity`;
            }
        },

        // Get color class based on usage
        getColorClass() {
            const percentage = this.today.percentage_used || 0;

            if (percentage < 60) return 'low';
            if (percentage < 80) return 'medium';
            return 'high';
        }
    });
});
