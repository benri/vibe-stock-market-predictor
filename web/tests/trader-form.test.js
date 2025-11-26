/**
 * Tests for trader-form component
 */

const fs = require('fs');
const path = require('path');
eval(fs.readFileSync(path.join(__dirname, '../../static/js/components/trader-form.js'), 'utf8'));

describe('traderForm Component', () => {
    test('initializes in create mode with default values', () => {
        const component = traderForm({ mode: 'create' });

        expect(component.mode).toBe('create');
        expect(component.formData.name).toBe('');
        expect(component.formData.initial_balance).toBe(10000);
        expect(component.formData.risk_tolerance).toBe('medium');
        expect(component.formData.trading_timezone).toBe('America/New_York');
    });

    test('initializes in edit mode with trader ID', () => {
        const component = traderForm({ mode: 'edit', traderId: 123 });

        expect(component.mode).toBe('edit');
        expect(component.traderId).toBe(123);
    });

    test('validate fails when name is empty', () => {
        const component = traderForm({ mode: 'create' });
        component.formData.name = '';

        const isValid = component.validate();

        expect(isValid).toBe(false);
        expect(component.errors.name).toBeDefined();
    });

    test('validate fails when initial balance is too low (create mode)', () => {
        const component = traderForm({ mode: 'create' });
        component.formData.name = 'Test Trader';
        component.formData.initial_balance = 50;

        const isValid = component.validate();

        expect(isValid).toBe(false);
        expect(component.errors.initial_balance).toBeDefined();
    });

    test('validate passes with valid data', () => {
        const component = traderForm({ mode: 'create' });
        component.formData.name = 'Test Trader';
        component.formData.initial_balance = 10000;

        const isValid = component.validate();

        expect(isValid).toBe(true);
        expect(Object.keys(component.errors)).toHaveLength(0);
    });

    test('reset clears form data', () => {
        const component = traderForm({ mode: 'create' });
        component.formData.name = 'Test';
        component.formData.risk_tolerance = 'high';
        component.errors = { name: 'Error' };

        component.reset();

        expect(component.formData.name).toBe('');
        expect(component.formData.risk_tolerance).toBe('medium');
        expect(Object.keys(component.errors)).toHaveLength(0);
    });

    test('getSubmitButtonText returns correct text based on mode and loading', () => {
        const createComponent = traderForm({ mode: 'create' });
        const editComponent = traderForm({ mode: 'edit' });

        expect(createComponent.getSubmitButtonText()).toBe('Create Trader');
        expect(editComponent.getSubmitButtonText()).toBe('Save Changes');

        createComponent.loading = true;
        editComponent.loading = true;

        expect(createComponent.getSubmitButtonText()).toBe('Creating...');
        expect(editComponent.getSubmitButtonText()).toBe('Updating...');
    });
});
