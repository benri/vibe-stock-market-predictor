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

        const card = document.createElement('div');
        card.className = 'trader-card ' + trader.status;
        card.innerHTML = `
            <div class="trader-header">
                <div class="trader-info">
                    <h3>${trader.name}</h3>
                    <span class="trader-status ${trader.status}">${trader.status}</span>
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
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', function () {
    // Stock analysis enter key
    document.getElementById('tickerInput').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            analyzeStocks();
        }
    });

    // Close modal when clicking outside
    window.onclick = function (event) {
        const modal = document.getElementById('edit-trader-modal');
        if (event.target === modal) {
            closeEditModal();
        }
    };
});
