/**
 * Unified Trader Form Component
 * Handles both create and edit modes with a single implementation
 *
 * Usage:
 *   <div x-data="traderForm({ mode: 'create' })">
 *   <div x-data="traderForm({ mode: 'edit', traderId: 1 })">
 */

function traderForm(config = {}) {
    return {
        // Configuration
        mode: config.mode || 'create', // 'create' or 'edit'
        traderId: config.traderId || null,

        // Form data
        formData: {
            name: '',
            initial_balance: 10000,
            risk_tolerance: 'medium',
            trading_timezone: 'America/New_York',
            trading_ethos: '',
            status: 'active'
        },

        // State
        loading: false,
        errors: {},

        // Initialize
        async init() {
            if (this.mode === 'edit' && this.traderId) {
                await this.loadTrader();
            }
        },

        // Load trader data for editing
        async loadTrader() {
            this.loading = true;

            try {
                const trader = this.$store.traders.getById(this.traderId);
                if (trader) {
                    this.formData = {
                        name: trader.name,
                        risk_tolerance: trader.risk_tolerance,
                        trading_timezone: trader.trading_timezone || 'America/New_York',
                        trading_ethos: trader.trading_ethos || '',
                        status: trader.status
                    };
                } else {
                    // Fetch from API if not in store
                    const response = await fetch(`/api/traders/${this.traderId}`);
                    const data = await response.json();
                    this.formData = {
                        name: data.name,
                        risk_tolerance: data.risk_tolerance,
                        trading_timezone: data.trading_timezone || 'America/New_York',
                        trading_ethos: data.trading_ethos || '',
                        status: data.status
                    };
                }
            } catch (error) {
                console.error('Error loading trader:', error);
                alert('Error loading trader: ' + error.message);
            } finally {
                this.loading = false;
            }
        },

        // Validate form
        validate() {
            this.errors = {};

            if (!this.formData.name || this.formData.name.trim() === '') {
                this.errors.name = 'Trader name is required';
            }

            if (this.mode === 'create') {
                if (!this.formData.initial_balance || this.formData.initial_balance < 100) {
                    this.errors.initial_balance = 'Initial balance must be at least $100';
                }
            }

            return Object.keys(this.errors).length === 0;
        },

        // Submit form
        async submit() {
            if (!this.validate()) {
                return;
            }

            this.loading = true;

            try {
                if (this.mode === 'create') {
                    await this.$store.traders.create(this.formData);
                    alert('Trader created successfully!');
                    this.reset();
                    this.$dispatch('trader-created');
                } else {
                    await this.$store.traders.update(this.traderId, this.formData);
                    alert('Trader updated successfully!');
                    this.$dispatch('trader-updated', { id: this.traderId });
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                this.loading = false;
            }
        },

        // Reset form
        reset() {
            this.formData = {
                name: '',
                initial_balance: 10000,
                risk_tolerance: 'medium',
                trading_timezone: 'America/New_York',
                trading_ethos: '',
                status: 'active'
            };
            this.errors = {};
        },

        // Get button text based on mode
        getSubmitButtonText() {
            if (this.loading) {
                return this.mode === 'create' ? 'Creating...' : 'Updating...';
            }
            return this.mode === 'create' ? 'Create Trader' : 'Save Changes';
        }
    };
}
