/**
 * Tests for modal-manager component
 */

const fs = require('fs');
const path = require('path');
eval(fs.readFileSync(path.join(__dirname, '../../static/js/components/modal-manager.js'), 'utf8'));

describe('modalManager Component', () => {
    let component;

    beforeEach(() => {
        // Mock document.body.style
        document.body.style = {};
        component = modalManager();
        component.$dispatch = jest.fn();
    });

    test('initializes with no active modal', () => {
        expect(component.activeModal).toBeNull();
        expect(component.modalData).toBeNull();
    });

    test('openModal sets active modal and data', () => {
        const data = { id: 123 };
        component.openModal('test-modal', data);

        expect(component.activeModal).toBe('test-modal');
        expect(component.modalData).toEqual(data);
        expect(document.body.style.overflow).toBe('hidden');
    });

    test('openModal dispatches event', () => {
        component.openModal('test-modal', { id: 123 });

        expect(component.$dispatch).toHaveBeenCalledWith('modal-opened', {
            modal: 'test-modal',
            data: { id: 123 }
        });
    });

    test('closeModal clears active modal', () => {
        component.openModal('test-modal', { id: 123 });
        component.closeModal();

        expect(component.activeModal).toBeNull();
        expect(component.modalData).toBeNull();
        expect(document.body.style.overflow).toBe('');
    });

    test('closeModal dispatches event', () => {
        component.openModal('test-modal');
        component.$dispatch = jest.fn(); // Reset mock
        component.closeModal();

        expect(component.$dispatch).toHaveBeenCalledWith('modal-closed', {
            modal: 'test-modal'
        });
    });

    test('isModalOpen returns correct boolean', () => {
        component.openModal('test-modal');

        expect(component.isModalOpen('test-modal')).toBe(true);
        expect(component.isModalOpen('other-modal')).toBe(false);
    });

    test('handleEscape closes modal on ESC key', () => {
        component.openModal('test-modal');
        const escEvent = { key: 'Escape' };

        component.handleEscape(escEvent);

        expect(component.activeModal).toBeNull();
    });

    test('handleEscape does nothing on other keys', () => {
        component.openModal('test-modal');
        const otherEvent = { key: 'Enter' };

        component.handleEscape(otherEvent);

        expect(component.activeModal).toBe('test-modal');
    });
});
