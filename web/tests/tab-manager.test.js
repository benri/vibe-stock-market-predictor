/**
 * Tests for tab-manager component
 */

// Load the component function
const fs = require('fs');
const path = require('path');
eval(fs.readFileSync(path.join(__dirname, '../../static/js/components/tab-manager.js'), 'utf8'));

describe('tabManager Component', () => {
    test('initializes with default tab', () => {
        const component = tabManager({ tabs: ['tab1', 'tab2'], default: 'tab1' });
        component.init();

        expect(component.currentTab).toBe('tab1');
    });

    test('initializes with first tab if no default', () => {
        const component = tabManager({ tabs: ['tab1', 'tab2'] });
        component.init();

        expect(component.currentTab).toBe('tab1');
    });

    test('selectTab changes current tab', () => {
        const component = tabManager({ tabs: ['tab1', 'tab2'], default: 'tab1' });
        component.$dispatch = jest.fn(); // Mock Alpine's $dispatch

        component.selectTab('tab2');

        expect(component.currentTab).toBe('tab2');
    });

    test('selectTab fires callback when provided', () => {
        const callback = jest.fn();
        const component = tabManager({
            tabs: ['tab1', 'tab2'],
            default: 'tab1',
            onTabChange: callback
        });
        component.$dispatch = jest.fn();

        component.selectTab('tab2');

        expect(callback).toHaveBeenCalledWith('tab2', 'tab1');
    });

    test('isActive returns correct boolean', () => {
        const component = tabManager({ tabs: ['tab1', 'tab2'], default: 'tab1' });

        expect(component.isActive('tab1')).toBe(true);
        expect(component.isActive('tab2')).toBe(false);
    });

    test('selectTab does nothing if already active', () => {
        const callback = jest.fn();
        const component = tabManager({
            tabs: ['tab1', 'tab2'],
            default: 'tab1',
            onTabChange: callback
        });

        component.selectTab('tab1');

        expect(callback).not.toHaveBeenCalled();
    });
});
