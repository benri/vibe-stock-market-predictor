/**
 * Analysis History Component
 * Displays recent analysis history for a trader
 *
 * Usage:
 *   <div x-data="analysisHistory(traderId)">
 */

function analysisHistory(traderId) {
    return {
        traderId,
        history: [],
        loading: false,

        async init() {
            await this.load();
        },

        async load() {
            if (!this.traderId) return;

            this.loading = true;
            try {
                const response = await fetch(`/api/traders/${this.traderId}/watchlist/history?limit=20`);
                const data = await response.json();
                this.history = data.history || [];
            } catch (error) {
                console.error('Error loading analysis history:', error);
                alert('Error loading analysis history');
            } finally {
                this.loading = false;
            }
        },

        getRecClass(recommendation) {
            if (!recommendation) return 'neutral';
            return recommendation.toLowerCase().replace(' ', '-');
        },

        parseSignals(signals) {
            if (!signals) return 'N/A';
            try {
                const parsed = typeof signals === 'string' ? JSON.parse(signals) : signals;
                if (Array.isArray(parsed) && parsed.length > 0) {
                    const preview = parsed.slice(0, 2).join(', ');
                    return parsed.length > 2 ? `${preview} +${parsed.length - 2} more` : preview;
                }
            } catch (e) {}
            return 'N/A';
        }
    };
}
