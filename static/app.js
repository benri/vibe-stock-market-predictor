// ========================================
// TAB SWITCHING
// ========================================

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');

    // Add active class to clicked button
    event.target.classList.add('active');

    // Load traders if switching to traders tab
    if (tabName === 'traders') {
        loadTraders();
        loadApiUsage();
        startApiUsageAutoRefresh();
    } else {
        stopApiUsageAutoRefresh();
    }
}

// ========================================
// STOCK ANALYSIS FUNCTIONS
// ========================================

function setTickers(tickers) {
    document.getElementById('tickerInput').value = tickers;
}

async function analyzeStocks() {
    const input = document.getElementById('tickerInput').value.trim();
    if (!input) {
        alert('Please enter at least one stock ticker');
        return;
    }

    const tickers = input.split(',').map(t => t.trim()).filter(t => t);
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const btn = document.getElementById('analyzeBtn');

    loading.style.display = 'block';
    results.innerHTML = '';
    btn.disabled = true;

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tickers })
        });

        const data = await response.json();

        if (data.error) {
            results.innerHTML = '<div class="error">Error: ' + data.error + '</div>';
        } else {
            displayResults(data.results);
        }
    } catch (error) {
        results.innerHTML = '<div class="error">Error: ' + error.message + '</div>';
    } finally {
        loading.style.display = 'none';
        btn.disabled = false;
    }
}

function displayResults(results) {
    const container = document.getElementById('results');
    container.innerHTML = '<h2>Analysis Results</h2>';

    results.forEach(stock => {
        if (stock.error) {
            container.innerHTML += '<div class="stock-card error-card"><h3>' + stock.ticker +
                '</h3><p class="error">' + stock.error + '</p></div>';
            return;
        }

        const recClass = stock.recommendation.replace(' ', '-').toLowerCase();
        const changeClass = stock.price_change_6mo >= 0 ? 'positive' : 'negative';
        const changeSymbol = stock.price_change_6mo >= 0 ? '▲' : '▼';

        let signalsList = '';
        stock.signals.forEach(signal => {
            signalsList += '<li>' + signal + '</li>';
        });

        container.innerHTML += '<div class="stock-card">' +
            '<div class="stock-header">' +
            '<div>' +
            '<h3>' + stock.ticker + '</h3>' +
            '<p class="company-name">' + stock.company_name + '</p>' +
            '</div>' +
            '<div class="price-info">' +
            '<div class="current-price">$' + stock.current_price + '</div>' +
            '<div class="price-change ' + changeClass + '">' +
            changeSymbol + ' ' + Math.abs(stock.price_change_6mo) + '% (6mo)' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div class="recommendation ' + recClass + '">' +
            '<span class="rec-label">' + stock.recommendation + '</span>' +
            '<span class="confidence">Confidence: ' + stock.confidence + '%</span>' +
            '</div>' +
            '<div class="indicators">' +
            '<div class="indicator"><span class="label">20-Day MA:</span><span class="value">$' + (stock.sma_20 || 'N/A') + '</span></div>' +
            '<div class="indicator"><span class="label">50-Day MA:</span><span class="value">$' + (stock.sma_50 || 'N/A') + '</span></div>' +
            '<div class="indicator"><span class="label">RSI:</span><span class="value">' + (stock.rsi || 'N/A') + '</span></div>' +
            '<div class="indicator"><span class="label">MACD:</span><span class="value">' + (stock.macd || 'N/A') + '</span></div>' +
            '<div class="indicator"><span class="label">Momentum:</span><span class="value">' + (stock.momentum ? stock.momentum + '%' : 'N/A') + '</span></div>' +
            '</div>' +
            '<div class="signals"><h4>Key Signals:</h4><ul>' + signalsList + '</ul></div>' +
            '</div>';
    });
}

// ========================================
// TRADER MANAGEMENT FUNCTIONS
// ========================================

function showCreateTraderForm() {
    document.getElementById('create-trader-form').style.display = 'block';
}

function hideCreateTraderForm() {
    document.getElementById('create-trader-form').style.display = 'none';
    // Clear form
    document.getElementById('traderName').value = '';
    document.getElementById('initialBalance').value = '10000';
    document.getElementById('riskTolerance').value = 'medium';
    document.getElementById('tradingTimezone').value = 'America/New_York';
    document.getElementById('tradingEthos').value = '';
}

async function createTrader() {
    const name = document.getElementById('traderName').value.trim();
    const initialBalance = parseFloat(document.getElementById('initialBalance').value);
    const riskTolerance = document.getElementById('riskTolerance').value;
    const tradingTimezone = document.getElementById('tradingTimezone').value;
    const tradingEthos = document.getElementById('tradingEthos').value.trim();

    if (!name) {
        alert('Please enter a trader name');
        return;
    }

    if (initialBalance < 100) {
        alert('Initial balance must be at least $100');
        return;
    }

    try {
        const response = await fetch('/api/traders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                initial_balance: initialBalance,
                risk_tolerance: riskTolerance,
                trading_timezone: tradingTimezone,
                trading_ethos: tradingEthos || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert('Trader created successfully!');
            hideCreateTraderForm();
            loadTraders();
        } else {
            alert('Error: ' + (data.error || 'Failed to create trader'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function loadTraders() {
    const loading = document.getElementById('traders-loading');
    const container = document.getElementById('traders-list');

    loading.style.display = 'block';
    container.innerHTML = '';

    try {
        const response = await fetch('/api/traders');
        const data = await response.json();

        if (data.traders && data.traders.length > 0) {
            displayTraders(data.traders);
        } else {
            container.innerHTML = '<div class="error">No traders found. Create your first trader to get started!</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="error">Error loading traders: ' + error.message + '</div>';
    } finally {
        loading.style.display = 'none';
    }
}

function displayTraders(traders) {
    const container = document.getElementById('traders-list');
    container.innerHTML = '';

    traders.forEach(trader => {
        const profitLossClass = trader.profit_loss >= 0 ? 'positive' : 'negative';
        const profitLossSymbol = trader.profit_loss >= 0 ? '▲' : '▼';

        let ethosHtml = '';
        if (trader.trading_ethos) {
            ethosHtml = '<div class="trader-ethos">' +
                '<h4>Trading Philosophy</h4>' +
                '<p>' + trader.trading_ethos + '</p>' +
                '</div>';
        }

        const unrealizedClass = trader.unrealized_pl >= 0 ? 'positive' : 'negative';
        const unrealizedSymbol = trader.unrealized_pl >= 0 ? '▲' : '▼';
        const winRateClass = trader.win_rate >= 50 ? 'positive' : 'negative';

        // Watchlist badge
        const useCustom = trader.use_custom_watchlist || false;
        const watchlistSize = trader.watchlist_size || 6;
        const customWatchlist = trader.custom_watchlist || [];
        let watchlistBadge = '';

        if (useCustom) {
            watchlistBadge = `<span class="watchlist-badge custom" title="Using custom watchlist with ${customWatchlist.length} tickers">📋 Custom: ${customWatchlist.length} tickers</span>`;
        } else {
            watchlistBadge = `<span class="watchlist-badge pool" title="Using pool-based watchlist (${watchlistSize} tickers per session)">🌐 Pool: ${watchlistSize} tickers</span>`;
        }

        const card = document.createElement('div');
        card.className = 'trader-card ' + trader.status;
        card.innerHTML = `
            <div class="trader-header">
                <div class="trader-info">
                    <h3>${trader.name}</h3>
                    <div class="trader-badges">
                        <span class="trader-status ${trader.status}">${trader.status}</span>
                        ${watchlistBadge}
                    </div>
                </div>
                <div class="trader-actions">
                    <button class="icon-btn" onclick="editTrader(${trader.id})" title="Edit Trader">✏️ Edit</button>
                    <button class="icon-btn" onclick="viewTraderDetails(${trader.id})" title="View Details">📊 Details</button>
                    <button class="icon-btn" onclick="deleteTrader(${trader.id}, '${trader.name}')" title="Delete Trader">🗑️ Delete</button>
                </div>
            </div>
            <div class="trader-stats">
                <div class="stat">
                    <div class="stat-label">Cash Balance</div>
                    <div class="stat-value">$${trader.current_balance.toLocaleString()}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Portfolio Value</div>
                    <div class="stat-value">$${trader.portfolio_value.toLocaleString()}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Total Value</div>
                    <div class="stat-value">$${trader.total_value.toLocaleString()}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Unrealized P/L</div>
                    <div class="stat-value ${unrealizedClass}">${unrealizedSymbol} $${Math.abs(trader.unrealized_pl).toLocaleString()}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Total P/L</div>
                    <div class="stat-value ${profitLossClass}">${profitLossSymbol} $${Math.abs(trader.profit_loss).toLocaleString()}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Total Return</div>
                    <div class="stat-value ${profitLossClass}">${trader.profit_loss_percentage.toFixed(2)}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Trades (Buy/Sell)</div>
                    <div class="stat-value">${trader.buy_trades}/${trader.sell_trades}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Win Rate</div>
                    <div class="stat-value ${winRateClass}">${trader.win_rate.toFixed(1)}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Risk Tolerance</div>
                    <div class="stat-value">${trader.risk_tolerance.charAt(0).toUpperCase() + trader.risk_tolerance.slice(1)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Trading Exchange</div>
                    <div class="stat-value">${trader.trading_timezone ? (trader.trading_timezone.includes('New_York') ? '🇺🇸 NYSE' : trader.trading_timezone.includes('London') ? '🇬🇧 LSE' : trader.trading_timezone.includes('Tokyo') ? '🇯🇵 TSE' : trader.trading_timezone) : '🇺🇸 NYSE'}</div>
                </div>
            </div>
            ${ethosHtml}
        `;

        container.appendChild(card);
    });
}

async function editTrader(traderId) {
    try {
        const response = await fetch(`/api/traders/${traderId}`);
        const trader = await response.json();

        document.getElementById('editTraderId').value = trader.id;
        document.getElementById('editTraderName').value = trader.name;
        document.getElementById('editRiskTolerance').value = trader.risk_tolerance;
        document.getElementById('editStatus').value = trader.status;
        document.getElementById('editTradingTimezone').value = trader.trading_timezone || 'America/New_York';
        document.getElementById('editTradingEthos').value = trader.trading_ethos || '';

        document.getElementById('edit-trader-modal').style.display = 'block';
    } catch (error) {
        alert('Error loading trader: ' + error.message);
    }
}

async function updateTrader() {
    const traderId = document.getElementById('editTraderId').value;
    const name = document.getElementById('editTraderName').value.trim();
    const riskTolerance = document.getElementById('editRiskTolerance').value;
    const status = document.getElementById('editStatus').value;
    const tradingTimezone = document.getElementById('editTradingTimezone').value;
    const tradingEthos = document.getElementById('editTradingEthos').value.trim();

    if (!name) {
        alert('Please enter a trader name');
        return;
    }

    try {
        const response = await fetch(`/api/traders/${traderId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                risk_tolerance: riskTolerance,
                status,
                trading_timezone: tradingTimezone,
                trading_ethos: tradingEthos || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert('Trader updated successfully!');
            closeEditModal();
            loadTraders();
        } else {
            alert('Error: ' + (data.error || 'Failed to update trader'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function deleteTrader(traderId, traderName) {
    if (!confirm(`Are you sure you want to delete trader "${traderName}"? This will delete all their trades and portfolio data.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/traders/${traderId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('Trader deleted successfully');
            loadTraders();
        } else {
            const data = await response.json();
            alert('Error: ' + (data.error || 'Failed to delete trader'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

let portfolioChartInstance = null;
let profitLossChartInstance = null;

async function viewTraderDetails(traderId) {
    try {
        const [traderRes, historyRes] = await Promise.all([
            fetch(`/api/traders/${traderId}`),
            fetch(`/api/traders/${traderId}/performance-history`)
        ]);

        const trader = await traderRes.json();
        const history = await historyRes.json();

        // Set modal title
        document.getElementById('charts-trader-name').textContent = `${trader.name} - Performance Charts`;

        // Show modal
        document.getElementById('charts-modal').style.display = 'block';

        // Destroy previous chart instances if they exist
        if (portfolioChartInstance) {
            portfolioChartInstance.destroy();
        }
        if (profitLossChartInstance) {
            profitLossChartInstance.destroy();
        }

        // Create Portfolio Value Chart
        const portfolioCtx = document.getElementById('portfolioChart').getContext('2d');
        portfolioChartInstance = new Chart(portfolioCtx, {
            type: 'line',
            data: {
                labels: history.labels,
                datasets: [
                    {
                        label: 'Cash Balance',
                        data: history.balance,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Portfolio Value',
                        data: history.portfolio_value,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Total Value',
                        data: history.total_value,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += '$' + context.parsed.y.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });

        // Create Profit/Loss Chart
        const profitLossCtx = document.getElementById('profitLossChart').getContext('2d');
        const plColors = history.profit_loss.map(val => val >= 0 ? 'rgba(16, 185, 129, 0.8)' : 'rgba(239, 68, 68, 0.8)');

        profitLossChartInstance = new Chart(profitLossCtx, {
            type: 'line',
            data: {
                labels: history.labels,
                datasets: [
                    {
                        label: 'Profit/Loss',
                        data: history.profit_loss,
                        borderColor: function(context) {
                            const value = context.parsed?.y;
                            return value >= 0 ? '#10b981' : '#ef4444';
                        },
                        backgroundColor: function(context) {
                            const value = context.parsed?.y;
                            return value >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
                        },
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        segment: {
                            borderColor: function(ctx) {
                                return ctx.p1.parsed.y >= 0 ? '#10b981' : '#ef4444';
                            },
                            backgroundColor: function(ctx) {
                                return ctx.p1.parsed.y >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
                            }
                        }
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                const value = context.parsed.y;
                                label += (value >= 0 ? '+' : '') + '$' + value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            callback: function(value) {
                                return (value >= 0 ? '+' : '') + '$' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: function(context) {
                                if (context.tick.value === 0) {
                                    return '#000';
                                }
                                return 'rgba(0, 0, 0, 0.1)';
                            },
                            lineWidth: function(context) {
                                if (context.tick.value === 0) {
                                    return 2;
                                }
                                return 1;
                            }
                        }
                    }
                }
            }
        });

    } catch (error) {
        alert('Error loading trader charts: ' + error.message);
    }
}

function closeChartsModal() {
    document.getElementById('charts-modal').style.display = 'none';
    // Destroy charts when closing
    if (portfolioChartInstance) {
        portfolioChartInstance.destroy();
        portfolioChartInstance = null;
    }
    if (profitLossChartInstance) {
        profitLossChartInstance.destroy();
        profitLossChartInstance = null;
    }
}

function closeEditModal() {
    document.getElementById('edit-trader-modal').style.display = 'none';
}

// ========================================
// API USAGE DASHBOARD
// ========================================

let apiUsageRefreshInterval = null;

async function loadApiUsage() {
    try {
        const response = await fetch('/api/api-usage?days=1');
        const data = await response.json();

        if (data && data.today) {
            displayApiUsageWidget(data);
        }
    } catch (error) {
        console.error('Error loading API usage:', error);
        document.getElementById('usage-status-message').textContent = 'Failed to load API usage data';
    }
}

function displayApiUsageWidget(data) {
    const today = data.today;
    const calls = today.calls || 0;
    const remaining = today.remaining || 0;
    const limit = today.limit || 25;
    const percentage = today.percentage_used || 0;

    // Update values
    document.getElementById('api-calls-today').textContent = calls;
    document.getElementById('api-calls-remaining').textContent = remaining;
    document.getElementById('usage-percentage').textContent = Math.round(percentage) + '%';

    // Update progress bar
    const progressFill = document.getElementById('usage-progress-fill');
    progressFill.style.width = percentage + '%';

    // Update progress bar color based on usage
    progressFill.className = 'usage-progress-fill';
    if (percentage < 60) {
        progressFill.classList.add('low');
    } else if (percentage < 80) {
        progressFill.classList.add('medium');
    } else {
        progressFill.classList.add('high');
    }

    // Update status message
    let statusMessage = '';
    if (remaining === 0) {
        statusMessage = '⚠️ Daily limit reached! Trading paused until tomorrow.';
    } else if (percentage >= 80) {
        statusMessage = `⚠️ ${remaining} calls remaining - approaching limit`;
    } else if (percentage >= 60) {
        statusMessage = `✓ ${remaining} calls remaining - good capacity`;
    } else {
        statusMessage = `✓ ${remaining} calls remaining - excellent capacity`;
    }

    document.getElementById('usage-status-message').textContent = statusMessage;
}

async function refreshApiUsage() {
    const refreshIcon = document.getElementById('api-refresh-icon');
    refreshIcon.style.animation = 'spin 0.5s linear';

    await loadApiUsage();

    setTimeout(() => {
        refreshIcon.style.animation = '';
    }, 500);
}

function startApiUsageAutoRefresh() {
    // Refresh every 30 seconds
    if (apiUsageRefreshInterval) {
        clearInterval(apiUsageRefreshInterval);
    }
    apiUsageRefreshInterval = setInterval(loadApiUsage, 30000);
}

function stopApiUsageAutoRefresh() {
    if (apiUsageRefreshInterval) {
        clearInterval(apiUsageRefreshInterval);
        apiUsageRefreshInterval = null;
    }
}

async function showApiDetailsModal() {
    try {
        const response = await fetch('/api/api-usage?days=7');
        const data = await response.json();

        let detailsHTML = '<div class="api-details">';
        detailsHTML += '<h3>Last 7 Days API Usage</h3>';

        if (data && data.recent && data.recent.daily_breakdown) {
            detailsHTML += '<table class="api-table">';
            detailsHTML += '<tr><th>Date</th><th>Calls</th></tr>';

            data.recent.daily_breakdown.forEach(day => {
                detailsHTML += `<tr><td>${day.date}</td><td>${day.calls}</td></tr>`;
            });

            detailsHTML += '</table>';
            detailsHTML += `<p><strong>Average:</strong> ${data.recent.avg_daily} calls/day</p>`;
        }

        detailsHTML += '</div>';

        alert(detailsHTML.replace(/<[^>]*>/g, '\n')); // Simple display for now
    } catch (error) {
        alert('Error loading API details: ' + error.message);
    }
}

// ========================================
// MODAL TAB SWITCHING
// ========================================

function switchModalTab(tabName) {
    // Hide all modal tabs
    document.querySelectorAll('.modal-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all modal tab buttons
    document.querySelectorAll('.modal-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById('modal-' + tabName + '-tab').classList.add('active');

    // Add active class to clicked button
    event.target.classList.add('active');

    // Load content when switching to specific tabs
    const traderId = document.getElementById('editTraderId').value;
    if (tabName === 'watchlist' && traderId) {
        loadWatchlistConfig(traderId);
    } else if (tabName === 'history' && traderId) {
        loadAnalysisHistory(traderId);
    }
}

// ========================================
// WATCHLIST MANAGEMENT
// ========================================

let currentWatchlistTickers = [];

async function loadWatchlistConfig(traderId) {
    try {
        const response = await fetch(`/api/traders/${traderId}/watchlist`);
        const data = await response.json();

        // Set watchlist size
        const watchlistSize = data.watchlist_size || 6;
        document.getElementById('watchlistSize').value = watchlistSize;
        document.getElementById('watchlistSizeDisplay').textContent = watchlistSize;
        document.getElementById('poolSizeDisplay').textContent = watchlistSize;

        // Set custom watchlist mode
        const useCustom = data.use_custom_watchlist || false;
        document.getElementById('useCustomWatchlist').checked = useCustom;

        // Load custom tickers
        currentWatchlistTickers = data.custom_watchlist || [];

        // Update UI based on mode
        toggleWatchlistMode();

        // Display custom tickers if in custom mode
        if (useCustom && currentWatchlistTickers.length > 0) {
            displayCustomTickerChips();
        }
    } catch (error) {
        console.error('Error loading watchlist config:', error);
        alert('Error loading watchlist configuration: ' + error.message);
    }
}

function toggleWatchlistMode() {
    const useCustom = document.getElementById('useCustomWatchlist').checked;
    const customSection = document.getElementById('custom-watchlist-section');
    const poolInfo = document.getElementById('pool-watchlist-info');

    if (useCustom) {
        customSection.style.display = 'block';
        poolInfo.style.display = 'none';
        displayCustomTickerChips();
    } else {
        customSection.style.display = 'none';
        poolInfo.style.display = 'block';
    }
}

function updateWatchlistSizeDisplay() {
    const size = document.getElementById('watchlistSize').value;
    document.getElementById('watchlistSizeDisplay').textContent = size;
    document.getElementById('poolSizeDisplay').textContent = size;
}

function displayCustomTickerChips() {
    const container = document.getElementById('customTickerChips');
    container.innerHTML = '';

    if (currentWatchlistTickers.length === 0) {
        container.innerHTML = '<p class="empty-message">No tickers added yet. Click "Add Tickers" to get started.</p>';
        return;
    }

    currentWatchlistTickers.forEach(ticker => {
        const chip = document.createElement('div');
        chip.className = 'ticker-chip';
        chip.innerHTML = `
            <span>${ticker}</span>
            <button class="chip-remove" onclick="removeTickerFromWatchlist('${ticker}')" title="Remove">×</button>
        `;
        container.appendChild(chip);
    });
}

function removeTickerFromWatchlist(ticker) {
    currentWatchlistTickers = currentWatchlistTickers.filter(t => t !== ticker);
    displayCustomTickerChips();
}

async function saveWatchlistConfig() {
    const traderId = document.getElementById('editTraderId').value;
    const useCustom = document.getElementById('useCustomWatchlist').checked;
    const watchlistSize = parseInt(document.getElementById('watchlistSize').value);

    // Validate custom tickers if custom mode is enabled
    if (useCustom && currentWatchlistTickers.length === 0) {
        alert('Please add at least one ticker to your custom watchlist, or switch to pool-based mode.');
        return;
    }

    try {
        const response = await fetch(`/api/traders/${traderId}/watchlist`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                use_custom_watchlist: useCustom,
                custom_watchlist: useCustom ? currentWatchlistTickers : null,
                watchlist_size: watchlistSize
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert('Watchlist configuration saved successfully!');
            loadTraders(); // Refresh trader cards
        } else {
            alert('Error: ' + (data.error || 'Failed to save watchlist configuration'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function viewTickerPool() {
    const traderId = document.getElementById('editTraderId').value;
    const trader = await fetch(`/api/traders/${traderId}`).then(r => r.json());
    const timezone = trader.trading_timezone || 'America/New_York';

    // Open ticker browser in view-only mode
    await openTickerBrowser(false);

    // Filter by timezone/exchange
    const exchangeMap = {
        'America/New_York': 'NYSE/NASDAQ',
        'Europe/London': 'LSE',
        'Asia/Tokyo': 'TSE'
    };
    const exchange = exchangeMap[timezone] || 'NYSE/NASDAQ';
    document.getElementById('exchangeFilter').value = exchange;
    await filterTickerPool();
}

// ========================================
// TICKER BROWSER
// ========================================

let tickerPoolData = [];
let selectedTickers = new Set();
let isAddMode = true;

async function openTickerBrowser(addMode = true) {
    isAddMode = addMode;
    selectedTickers.clear();

    // Load ticker pool
    document.getElementById('ticker-grid').innerHTML = '<p class="loading-message">Loading tickers...</p>';
    document.getElementById('ticker-browser-modal').style.display = 'block';

    try {
        const response = await fetch('/api/ticker-pool');
        const data = await response.json();
        tickerPoolData = data.tickers || [];

        // Pre-select current watchlist tickers if in add mode
        if (isAddMode) {
            currentWatchlistTickers.forEach(ticker => {
                selectedTickers.add(ticker);
            });
        }

        displayTickerPool(tickerPoolData);
        updateSelectedCount();
    } catch (error) {
        console.error('Error loading ticker pool:', error);
        document.getElementById('ticker-grid').innerHTML = '<p class="error">Error loading tickers: ' + error.message + '</p>';
    }
}

function closeTickerBrowser() {
    document.getElementById('ticker-browser-modal').style.display = 'none';
    selectedTickers.clear();
    tickerPoolData = [];

    // Reset filters
    document.getElementById('tickerSearchInput').value = '';
    document.getElementById('sectorFilter').value = '';
    document.getElementById('exchangeFilter').value = '';
}

async function filterTickerPool() {
    const search = document.getElementById('tickerSearchInput').value.toLowerCase();
    const sector = document.getElementById('sectorFilter').value;
    const exchange = document.getElementById('exchangeFilter').value;

    let filtered = tickerPoolData.filter(ticker => {
        const matchesSearch = !search ||
            ticker.ticker.toLowerCase().includes(search) ||
            (ticker.name && ticker.name.toLowerCase().includes(search));

        const matchesSector = !sector || ticker.sector === sector;
        const matchesExchange = !exchange || ticker.exchange === exchange;

        return matchesSearch && matchesSector && matchesExchange;
    });

    displayTickerPool(filtered);
}

function displayTickerPool(tickers) {
    const grid = document.getElementById('ticker-grid');

    if (tickers.length === 0) {
        grid.innerHTML = '<p class="empty-message">No tickers found matching your filters.</p>';
        return;
    }

    grid.innerHTML = '';

    tickers.forEach(ticker => {
        const isSelected = selectedTickers.has(ticker.ticker);
        const card = document.createElement('div');
        card.className = 'ticker-card-browser' + (isSelected ? ' selected' : '');
        card.onclick = () => toggleTickerSelection(ticker.ticker);

        card.innerHTML = `
            <div class="ticker-card-header-browser">
                <span class="ticker-symbol-browser">${ticker.ticker}</span>
                ${isSelected ? '<span class="selected-badge">✓</span>' : ''}
            </div>
            <div class="ticker-name-browser">${ticker.name || 'N/A'}</div>
            <div class="ticker-meta-browser">
                <span class="ticker-sector-browser">${ticker.sector || 'N/A'}</span>
                <span class="ticker-exchange-browser">${ticker.exchange || 'N/A'}</span>
            </div>
        `;

        grid.appendChild(card);
    });
}

function toggleTickerSelection(ticker) {
    if (selectedTickers.has(ticker)) {
        selectedTickers.delete(ticker);
    } else {
        selectedTickers.add(ticker);
    }

    updateSelectedCount();

    // Re-render to update visual state
    filterTickerPool();
}

function updateSelectedCount() {
    document.getElementById('selected-ticker-count').textContent = selectedTickers.size;
}

function clearTickerSelection() {
    selectedTickers.clear();
    updateSelectedCount();
    filterTickerPool();
}

function addSelectedTickers() {
    if (selectedTickers.size === 0) {
        alert('Please select at least one ticker to add.');
        return;
    }

    // Add selected tickers to current watchlist (avoiding duplicates)
    selectedTickers.forEach(ticker => {
        if (!currentWatchlistTickers.includes(ticker)) {
            currentWatchlistTickers.push(ticker);
        }
    });

    // Sort alphabetically for better UX
    currentWatchlistTickers.sort();

    // Update UI
    displayCustomTickerChips();
    closeTickerBrowser();

    alert(`Added ${selectedTickers.size} ticker(s) to watchlist. Don't forget to click "Save Watchlist" to persist changes.`);
}

// ========================================
// ANALYSIS HISTORY
// ========================================

async function loadAnalysisHistory(traderId) {
    const container = document.getElementById('analysis-history-content');
    container.innerHTML = '<p class="loading-message">Loading analysis history...</p>';

    try {
        const response = await fetch(`/api/traders/${traderId}/watchlist/history?limit=20`);
        const data = await response.json();

        if (data.history && data.history.length > 0) {
            displayAnalysisHistory(data.history);
        } else {
            container.innerHTML = '<p class="empty-message">No analysis history yet. This trader hasn\'t run any automated trading sessions.</p>';
        }
    } catch (error) {
        console.error('Error loading analysis history:', error);
        container.innerHTML = '<p class="error">Error loading analysis history: ' + error.message + '</p>';
    }
}

function displayAnalysisHistory(history) {
    const container = document.getElementById('analysis-history-content');

    let tableHTML = `
        <table class="analysis-history-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Ticker</th>
                    <th>Recommendation</th>
                    <th>Confidence</th>
                    <th>Price</th>
                    <th>Signals</th>
                </tr>
            </thead>
            <tbody>
    `;

    history.forEach(item => {
        const date = new Date(item.created_at).toLocaleString();
        const recClass = item.recommendation ? item.recommendation.replace(' ', '-').toLowerCase() : 'neutral';
        const confidence = item.confidence ? item.confidence + '%' : 'N/A';
        const price = item.price ? '$' + item.price.toFixed(2) : 'N/A';

        // Parse signals JSON if it exists
        let signalsHTML = 'N/A';
        if (item.signals) {
            try {
                const signals = typeof item.signals === 'string' ? JSON.parse(item.signals) : item.signals;
                if (Array.isArray(signals) && signals.length > 0) {
                    signalsHTML = signals.slice(0, 2).join(', ');
                    if (signals.length > 2) {
                        signalsHTML += ` +${signals.length - 2} more`;
                    }
                }
            } catch (e) {
                signalsHTML = 'N/A';
            }
        }

        tableHTML += `
            <tr>
                <td>${date}</td>
                <td><strong>${item.ticker}</strong></td>
                <td><span class="rec-badge ${recClass}">${item.recommendation || 'N/A'}</span></td>
                <td>${confidence}</td>
                <td>${price}</td>
                <td class="signals-cell">${signalsHTML}</td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    container.innerHTML = tableHTML;
}

async function refreshAnalysisHistory() {
    const traderId = document.getElementById('editTraderId').value;
    if (traderId) {
        await loadAnalysisHistory(traderId);
    }
}

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', function () {
    // Stock analysis enter key
    document.getElementById('tickerInput').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            analyzeStocks();
        }
    });

    // Close modals when clicking outside
    window.onclick = function (event) {
        const editModal = document.getElementById('edit-trader-modal');
        const tickerModal = document.getElementById('ticker-browser-modal');
        const chartsModal = document.getElementById('charts-modal');

        if (event.target === editModal) {
            closeEditModal();
        } else if (event.target === tickerModal) {
            closeTickerBrowser();
        } else if (event.target === chartsModal) {
            closeChartsModal();
        }
    };
});
