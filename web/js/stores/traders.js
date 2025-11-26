/**
 * Traders Store - Centralized state management for traders
 * Alpine.store for managing trader data across components
 */

document.addEventListener('alpine:init', () => {
    Alpine.store('traders', {
        // State
        list: [],
        loading: false,
        error: null,

        // Load all traders
        async load() {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch('/api/traders');
                const data = await response.json();
                this.list = data.traders || [];
            } catch (error) {
                this.error = error.message;
                console.error('Error loading traders:', error);
            } finally {
                this.loading = false;
            }
        },

        // Get trader by ID
        getById(id) {
            return this.list.find(t => t.id === id);
        },

        // Create new trader
        async create(traderData) {
            try {
                const response = await fetch('/api/traders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(traderData)
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to create trader');
                }

                const newTrader = await response.json();
                this.list.push(newTrader);
                return newTrader;
            } catch (error) {
                this.error = error.message;
                throw error;
            }
        },

        // Update existing trader
        async update(id, traderData) {
            try {
                const response = await fetch(`/api/traders/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(traderData)
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to update trader');
                }

                const updatedTrader = await response.json();
                const index = this.list.findIndex(t => t.id === id);
                if (index !== -1) {
                    this.list[index] = updatedTrader;
                }
                return updatedTrader;
            } catch (error) {
                this.error = error.message;
                throw error;
            }
        },

        // Delete trader
        async delete(id) {
            try {
                const response = await fetch(`/api/traders/${id}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to delete trader');
                }

                this.list = this.list.filter(t => t.id !== id);
            } catch (error) {
                this.error = error.message;
                throw error;
            }
        },

        // Update watchlist configuration
        async updateWatchlist(id, watchlistConfig) {
            try {
                const response = await fetch(`/api/traders/${id}/watchlist`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(watchlistConfig)
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to update watchlist');
                }

                // Reload traders to get updated data
                await this.load();
            } catch (error) {
                this.error = error.message;
                throw error;
            }
        }
    });
});
