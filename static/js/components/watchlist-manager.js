/**
 * Watchlist Manager Component
 * Handles watchlist configuration for a trader
 *
 * Usage:
 *   <div x-data="watchlistManager(traderId)">
 */

function watchlistManager(traderId) {
    return {
        traderId,
        useCustom: false,
        watchlistSize: 6,
        customTickers: [],
        loading: false,

        async init() {
            await this.loadConfig();

            // Listen for tickers selected from browser
            this.$el.addEventListener('tickers-selected', (e) => {
                e.detail.tickers.forEach(ticker => {
                    if (!this.customTickers.includes(ticker)) {
                        this.customTickers.push(ticker);
                    }
                });
                this.customTickers.sort();
            });
        },

        async loadConfig() {
            if (!this.traderId) return;

            this.loading = true;
            try {
                const response = await fetch(`/api/traders/${this.traderId}/watchlist`);
                const data = await response.json();

                this.useCustom = data.use_custom_watchlist || false;
                this.watchlistSize = data.watchlist_size || 6;
                this.customTickers = data.custom_watchlist || [];
            } catch (error) {
                console.error('Error loading watchlist config:', error);
                alert('Error loading watchlist configuration');
            } finally {
                this.loading = false;
            }
        },

        removeTicker(ticker) {
            this.customTickers = this.customTickers.filter(t => t !== ticker);
        },

        async openTickerBrowser() {
            this.$dispatch('open-ticker-browser', {
                traderId: this.traderId,
                currentTickers: this.customTickers
            });
        },

        async viewTickerPool() {
            const trader = this.$store.traders.getById(this.traderId);
            const timezone = trader?.trading_timezone || 'America/New_York';

            await this.$store.tickerPool.load();

            const exchangeMap = {
                'America/New_York': 'NYSE/NASDAQ',
                'Europe/London': 'LSE',
                'Asia/Tokyo': 'TSE'
            };

            this.$store.tickerPool.setFilter('exchange', exchangeMap[timezone] || 'NYSE/NASDAQ');
            this.$dispatch('open-ticker-browser', {
                traderId: this.traderId,
                viewOnly: true
            });
        },

        async saveConfig() {
            if (this.useCustom && this.customTickers.length === 0) {
                alert('Please add at least one ticker to your custom watchlist, or switch to pool-based mode.');
                return;
            }

            this.loading = true;
            try {
                await this.$store.traders.updateWatchlist(this.traderId, {
                    use_custom_watchlist: this.useCustom,
                    custom_watchlist: this.useCustom ? this.customTickers : null,
                    watchlist_size: this.watchlistSize
                });
                alert('Watchlist configuration saved successfully!');
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                this.loading = false;
            }
        }
    };
}
