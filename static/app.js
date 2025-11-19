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

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('tickerInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            analyzeStocks();
        }
    });
});
