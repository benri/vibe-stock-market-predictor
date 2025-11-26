/**
 * Trader Card Component
 * Handles actions for individual trader cards
 *
 * Usage:
 *   <div x-data="traderCard(trader)">
 */

function traderCard(trader) {
    return {
        trader,

        // Edit trader
        editTrader() {
            this.$dispatch('open-trader-modal', { traderId: trader.id });
        },

        // View performance details
        async viewDetails() {
            try {
                console.log('viewDetails called for trader:', trader.id);

                const [traderRes, historyRes] = await Promise.all([
                    fetch(`/api/traders/${trader.id}`),
                    fetch(`/api/traders/${trader.id}/performance-history`)
                ]);

                const traderData = await traderRes.json();
                const history = await historyRes.json();

                console.log('Trader data:', traderData);
                console.log('History data:', history);

                // Dispatch event with trader and history data
                console.log('Dispatching open-charts-modal event');
                this.$dispatch('open-charts-modal', {
                    trader: traderData,
                    history: history
                });
            } catch (error) {
                console.error('Error loading trader charts:', error);
                alert('Error loading trader charts: ' + error.message);
            }
        },

        // Delete trader
        async deleteTrader() {
            if (!confirm(`Are you sure you want to delete trader "${trader.name}"? This will delete all their trades and portfolio data.`)) {
                return;
            }

            try {
                await this.$store.traders.delete(trader.id);
                alert('Trader deleted successfully');
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
    };
}
