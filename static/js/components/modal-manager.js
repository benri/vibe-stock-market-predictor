/**
 * Generic Modal Manager Component for Alpine.js
 * Replaces separate modal implementations with a unified system
 *
 * Usage:
 *   <div x-data="modalManager()">
 *     <button @click="openModal('edit-trader', { traderId: 1 })">Edit</button>
 *   </div>
 */

function modalManager() {
    return {
        // State
        activeModal: null,
        modalData: null,
        modalHistory: [],

        // Open a modal
        openModal(modalName, data = null) {
            // Close existing modal if any
            if (this.activeModal) {
                this.modalHistory.push(this.activeModal);
            }

            this.activeModal = modalName;
            this.modalData = data;

            // Prevent body scroll when modal is open
            document.body.style.overflow = 'hidden';

            // Dispatch event for modal-specific logic
            this.$dispatch('modal-opened', { modal: modalName, data });
        },

        // Close current modal
        closeModal() {
            const closedModal = this.activeModal;

            this.activeModal = null;
            this.modalData = null;

            // Restore body scroll
            document.body.style.overflow = '';

            // Dispatch event
            this.$dispatch('modal-closed', { modal: closedModal });
        },

        // Check if a specific modal is open
        isModalOpen(modalName) {
            return this.activeModal === modalName;
        },

        // Handle ESC key
        handleEscape(e) {
            if (e.key === 'Escape' && this.activeModal) {
                this.closeModal();
            }
        },

        // Handle click outside modal
        handleClickOutside(e) {
            if (e.target.classList.contains('modal')) {
                this.closeModal();
            }
        }
    };
}
