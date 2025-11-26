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
                const [traderRes, historyRes] = await Promise.all([
                    fetch(`/api/traders/${trader.id}`),
                    fetch(`/api/traders/${trader.id}/performance-history`)
                ]);

                const traderData = await traderRes.json();
                const history = await historyRes.json();

                this.$dispatch('open-charts-modal', { trader: traderData, history });
            } catch (error) {
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
