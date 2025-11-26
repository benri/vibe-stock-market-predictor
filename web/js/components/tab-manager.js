/**
 * Generic Tab Manager Component for Alpine.js
 * Replaces both switchTab() and switchModalTab() with a single reusable component
 *
 * Usage:
 *   <div x-data="tabManager({ tabs: ['analysis', 'traders'], default: 'analysis' })">
 */

function tabManager(config = {}) {
    return {
        // Configuration
        tabs: config.tabs || [],
        currentTab: config.default || (config.tabs && config.tabs[0]) || null,
        onTabChange: config.onTabChange || null,

        // Initialize
        init() {
            // If no default set, use first tab
            if (!this.currentTab && this.tabs.length > 0) {
                this.currentTab = this.tabs[0];
            }
        },

        // Select a tab
        selectTab(tabName) {
            if (this.currentTab === tabName) return;

            const oldTab = this.currentTab;
            this.currentTab = tabName;

            // Fire callback if provided
            if (this.onTabChange) {
                this.onTabChange(tabName, oldTab);
            }

            // Dispatch custom event for parent components to listen
            this.$dispatch('tab-changed', { tab: tabName, previous: oldTab });
        },

        // Check if tab is active
        isActive(tabName) {
            return this.currentTab === tabName;
        }
    };
}
