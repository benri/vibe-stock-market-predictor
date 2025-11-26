# Alpine.js Migration Guide

## Overview

This document tracks the ongoing migration from vanilla JavaScript with inline onclick handlers to a modern Alpine.js-based component architecture.

## Completed Work

### Phase 1: Foundation ✅

**Alpine.js Integration**
- Added Alpine.js 3.13.3 via CDN to `templates/index.html`
- No build step required - framework loads from CDN

**Directory Structure Created**
```
static/
├── js/
│   ├── components/
│   │   ├── tab-manager.js       ✅ Generic tab system
│   │   ├── modal-manager.js     ✅ Generic modal system
│   │   └── trader-form.js       ✅ Unified create/edit form
│   └── stores/
│       ├── traders.js           ✅ Centralized trader state
│       ├── api-usage.js         ✅ API quota tracking
│       └── ticker-pool.js       ✅ Ticker data management
```

**Components Implemented**

1. **Tab Manager** (`static/js/components/tab-manager.js`)
   - Single implementation for all tab contexts
   - Replaces duplicate `switchTab()` and `switchModalTab()` functions
   - Data-driven configuration
   - Event-based communication

2. **Modal Manager** (`static/js/components/modal-manager.js`)
   - Unified modal system for all modals
   - Handles open/close, ESC key, click outside
   - Modal history stack support
   - Body scroll prevention

3. **Trader Form** (`static/js/components/trader-form.js`)
   - Single form for both create and edit modes
   - Mode-aware validation and submission
   - Integrates with trader store
   - Automatic form population in edit mode

**Alpine Stores Implemented**

1. **Traders Store** (`static/js/stores/traders.js`)
   - Centralized CRUD operations for traders
   - `load()`, `create()`, `update()`, `delete()`
   - Watchlist configuration management
   - Single source of truth for trader data

2. **API Usage Store** (`static/js/stores/api-usage.js`)
   - Real-time API quota tracking
   - Auto-refresh capability
   - Status message generation
   - Color-coded usage levels

3. **Ticker Pool Store** (`static/js/stores/ticker-pool.js`)
   - Ticker data management
   - Filter support (search, sector, exchange)
   - Unique sector/exchange extraction
   - Filtered ticker retrieval

**HTML Conversions Completed**

- ✅ Main tab navigation (analysis/traders tabs)
- ✅ Tab manager wrapping and lifecycle
- ✅ Quick pick buttons (onclick → @click)
- ✅ Component file loading in correct order

## DRY Improvements Achieved

### Before
```javascript
// Two duplicate functions
function switchTab(tabName) { /* 15 lines */ }
function switchModalTab(tabName) { /* 15 lines */ }

// Inline event handlers everywhere
<button onclick="switchTab('analysis')">
<button onclick="switchModalTab('settings')">
```

### After
```javascript
// One reusable component
function tabManager(config) { /* 40 lines, works everywhere */ }

// Declarative Alpine directives
<div x-data="tabManager({ tabs: ['analysis', 'traders'] })">
  <button @click="selectTab('analysis')">
  <button @click="selectTab('settings')">
```

**Result:** 30 lines → 40 lines, but now reusable infinitely

## Remaining Work

### Phase 2: Convert Remaining onclick Handlers

**Priority 1 - Critical UI Components**

1. **API Usage Widget** (lines 87-112 in index.html)
   - [ ] Convert `onclick="refreshApiUsage()"` to Alpine
   - [ ] Convert `onclick="showApiDetailsModal()"` to Alpine
   - [ ] Use `$store.apiUsage` instead of direct function calls

2. **Trader Management Buttons** (lines 114-188)
   - [ ] Convert `onclick="showCreateTraderForm()"` to `@click`
   - [ ] Convert `onclick="hideCreateTraderForm()"` to `@click`
   - [ ] Convert `onclick="createTrader()"` to `@click`
   - [ ] Convert `onclick="loadTraders()"` to `@click`

3. **Trader Cards** (dynamically generated in app.js lines 245-247)
   - [ ] Convert `onclick="editTrader(${trader.id})"` to `@click`
   - [ ] Convert `onclick="viewTraderDetails(${trader.id})"` to `@click`
   - [ ] Convert `onclick="deleteTrader(${trader.id})"` to `@click`

**Priority 2 - Modal Handlers**

4. **Edit Trader Modal** (lines 193-233)
   - [ ] Wrap in `x-data="modalManager()"`
   - [ ] Convert `onclick="closeEditModal()"` to `@click="closeModal()"`
   - [ ] Convert modal tab navigation to use `tabManager`
   - [ ] Convert `onclick="updateTrader()"` to `@click="submit()"`

5. **Watchlist Tab** (lines 235-283)
   - [ ] Convert `onchange="toggleWatchlistMode()"` to `@change`
   - [ ] Convert `oninput="updateWatchlistSizeDisplay()"` to `@input`
   - [ ] Convert `onclick="openTickerBrowser()"` to `@click`
   - [ ] Convert `onclick="viewTickerPool()"` to `@click`
   - [ ] Convert `onclick="saveWatchlistConfig()"` to `@click`

6. **Ticker Browser Modal** (lines 300-345)
   - [ ] Wrap in modal manager context
   - [ ] Convert `onclick="closeTickerBrowser()"` to `@click`
   - [ ] Convert `oninput="filterTickerPool()"` to `@input`
   - [ ] Convert `onchange="filterTickerPool()"` to `@change`
   - [ ] Convert `onclick="clearTickerSelection()"` to `@click`
   - [ ] Convert `onclick="addSelectedTickers()"` to `@click`
   - [ ] Use `$store.tickerPool` for filtering

7. **Charts Modal** (lines 347-363)
   - [ ] Wrap in modal manager
   - [ ] Convert `onclick="closeChartsModal()"` to `@click`

**Priority 3 - Stock Analysis**

8. **Stock Analysis Input** (lines 40-41)
   - [ ] Convert `onclick="analyzeStocks()"` to `@click`
   - [ ] Already done: Quick picks converted to `@click`

### Phase 3: Create Additional Components

**Recommended New Components**

1. **API Usage Widget Component**
   ```javascript
   // static/js/components/api-usage-widget.js
   function apiUsageWidget() {
     return {
       get usage() { return this.$store.apiUsage.today },
       get statusMessage() { return this.$store.apiUsage.getStatusMessage() },
       get colorClass() { return this.$store.apiUsage.getColorClass() },
       refresh() { this.$store.apiUsage.load() }
     }
   }
   ```

2. **Trader Card Component**
   ```javascript
   // static/js/components/trader-card.js
   function traderCard(traderId) {
     return {
       get trader() { return this.$store.traders.getById(traderId) },
       editTrader() { /* ... */ },
       deleteTrader() { /* ... */ },
       viewDetails() { /* ... */ }
     }
   }
   ```

3. **Ticker Browser Component**
   ```javascript
   // static/js/components/ticker-browser.js
   function tickerBrowser() {
     return {
       selectedTickers: new Set(),
       get filteredTickers() { return this.$store.tickerPool.getFiltered() },
       toggleSelection(ticker) { /* ... */ },
       addSelected() { /* ... */ }
     }
   }
   ```

### Phase 4: Layout Optimization

**Dashboard Streamlining**

1. **Collapsible API Usage Widget**
   - Move to sticky header bar
   - Compact view by default
   - Expand on click

2. **Section Collapsing**
   - Add collapse/expand to major sections
   - Remember state in localStorage
   - Reduce vertical scroll

3. **Trader Actions Consolidation**
   - Replace 3 buttons with dropdown menu
   - Reduces visual clutter

## Migration Strategy

### Step-by-Step Conversion Process

For each onclick handler:

1. **Identify the handler**
   ```html
   <button onclick="doSomething()">Click</button>
   ```

2. **Create Alpine component method (if needed)**
   ```javascript
   function myComponent() {
     return {
       doSomething() {
         // Implementation
       }
     }
   }
   ```

3. **Wrap in x-data (if not already)**
   ```html
   <div x-data="myComponent()">
     <button @click="doSomething()">Click</button>
   </div>
   ```

4. **Test functionality**
   - Verify click works
   - Check console for errors
   - Confirm state updates

5. **Remove old function from app.js (if unused)**

### Testing Checklist

After each conversion:
- [ ] Feature still works as before
- [ ] No console errors
- [ ] State updates correctly
- [ ] Events propagate properly

## Benefits Achieved So Far

1. **Code Reduction**
   - Eliminated duplicate tab switching logic (30 lines saved)
   - Single form implementation (80 lines of HTML saved when complete)

2. **Better Organization**
   - Clear separation: stores (state), components (behavior), templates (view)
   - Easy to find and modify functionality

3. **Improved Maintainability**
   - Change tab behavior once, applies everywhere
   - Single source of truth for data (stores)

4. **Modern Development Experience**
   - Reactive data binding
   - Component reusability
   - Event-driven architecture

## Next Steps

1. Complete Priority 1 conversions (critical UI)
2. Implement Priority 2 (modals)
3. Create additional component files
4. Optimize dashboard layout
5. Remove unused vanilla JS functions
6. Update documentation

## Estimated Remaining Time

- Priority 1 conversions: ~2 hours
- Priority 2 conversions: ~2 hours
- Phase 3 components: ~1.5 hours
- Phase 4 layout: ~1 hour
- Testing & cleanup: ~1 hour

**Total: ~7.5 hours**

## Notes

- All changes are backward compatible during transition
- Can be done incrementally without breaking existing functionality
- No build step required - still vanilla deployment
- Alpine.js is only 3KB gzipped overhead
