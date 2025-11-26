/**
 * Ticker Pool Store - Centralized state management for ticker pool data
 * Alpine.store for managing available tickers across exchanges
 */

document.addEventListener('alpine:init', () => {
    Alpine.store('tickerPool', {
        // State
        tickers: [],
        loading: false,
        error: null,

        // Filters
        filters: {
            search: '',
            sector: '',
            exchange: ''
        },

        // Load ticker pool
        async load() {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch('/api/ticker-pool');
                const data = await response.json();
                this.tickers = data.tickers || [];
            } catch (error) {
                this.error = error.message;
                console.error('Error loading ticker pool:', error);
            } finally {
                this.loading = false;
            }
        },

        // Get filtered tickers
        getFiltered() {
            return this.tickers.filter(ticker => {
                const matchesSearch = !this.filters.search ||
                    ticker.ticker.toLowerCase().includes(this.filters.search.toLowerCase()) ||
                    (ticker.name && ticker.name.toLowerCase().includes(this.filters.search.toLowerCase()));

                const matchesSector = !this.filters.sector || ticker.sector === this.filters.sector;
                const matchesExchange = !this.filters.exchange || ticker.exchange === this.filters.exchange;

                return matchesSearch && matchesSector && matchesExchange;
            });
        },

        // Get unique sectors
        getSectors() {
            const sectors = new Set();
            this.tickers.forEach(t => {
                if (t.sector) sectors.add(t.sector);
            });
            return Array.from(sectors).sort();
        },

        // Get unique exchanges
        getExchanges() {
            const exchanges = new Set();
            this.tickers.forEach(t => {
                if (t.exchange) exchanges.add(t.exchange);
            });
            return Array.from(exchanges).sort();
        },

        // Set filter
        setFilter(type, value) {
            this.filters[type] = value;
        },

        // Clear all filters
        clearFilters() {
            this.filters = {
                search: '',
                sector: '',
                exchange: ''
            };
        }
    });
});
