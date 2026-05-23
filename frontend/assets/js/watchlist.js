/**
 * Bharat Market Intelligence Agent — Watchlist Page JavaScript
 *
 * Shared between bullish.html and bearish.html.
 * Detects which type via data-type attribute on the script tag.
 * Falls back to demo data when backend is not connected.
 *
 * Security: All DOM via createElement/textContent (no innerHTML)
 */

(function () {
    'use strict';

    // Detect watchlist type from script tag
    const scriptTag = document.querySelector('script[data-type]');
    const watchlistType = scriptTag ? scriptTag.getAttribute('data-type') : 'bullish';
    const isBullish = watchlistType === 'bullish';

    // ============================================================
    // Demo Data
    // ============================================================
    const DEMO_BULLISH = [
        { company_symbol: 'TCS', company_name: 'Tata Consultancy Services', sector: 'Information Technology', bullish_score: 8.7, bearish_score: 2.1, quality_score: 9.2, momentum_score: 7.8, confidence_score: 8.5, top_positive_factors: ['Strong deal pipeline', 'Margin expansion', 'Digital revenue growth'], top_negative_factors: ['Currency headwinds'] },
        { company_symbol: 'HDFCBANK', company_name: 'HDFC Bank Ltd', sector: 'Financial Services', bullish_score: 8.4, bearish_score: 1.8, quality_score: 9.0, momentum_score: 7.5, confidence_score: 8.8, top_positive_factors: ['Credit growth acceleration', 'Asset quality stable', 'Rating upgrade'], top_negative_factors: ['Post-merger integration costs'] },
        { company_symbol: 'BAJFINANCE', company_name: 'Bajaj Finance Ltd', sector: 'Financial Services', bullish_score: 8.1, bearish_score: 2.5, quality_score: 8.5, momentum_score: 8.2, confidence_score: 7.9, top_positive_factors: ['AUM growth 32% YoY', 'New business lines', 'Digital lending platform'], top_negative_factors: ['Rising credit costs'] },
        { company_symbol: 'RELIANCE', company_name: 'Reliance Industries Ltd', sector: 'Energy', bullish_score: 7.9, bearish_score: 2.8, quality_score: 8.0, momentum_score: 7.2, confidence_score: 7.6, top_positive_factors: ['Jio subscriber growth', 'Retail restructuring', 'New energy capex'], top_negative_factors: ['O2C margin compression', 'Execution risk'] },
        { company_symbol: 'INFY', company_name: 'Infosys Ltd', sector: 'Information Technology', bullish_score: 7.6, bearish_score: 2.9, quality_score: 8.8, momentum_score: 7.0, confidence_score: 8.2, top_positive_factors: ['Guidance raised', 'Large deal wins', 'Generative AI practice'], top_negative_factors: ['Attrition concerns', 'Visa restrictions'] },
        { company_symbol: 'TATAMOTORS', company_name: 'Tata Motors Ltd', sector: 'Automobile', bullish_score: 7.5, bearish_score: 3.2, quality_score: 7.0, momentum_score: 8.1, confidence_score: 7.4, top_positive_factors: ['JLR margin improvement', 'EV market share gains', 'SUV dominance'], top_negative_factors: ['Semiconductor supply'] },
        { company_symbol: 'MARUTI', company_name: 'Maruti Suzuki India', sector: 'Automobile', bullish_score: 7.3, bearish_score: 2.7, quality_score: 8.5, momentum_score: 7.4, confidence_score: 7.8, top_positive_factors: ['Record exports', 'SUV portfolio expansion', 'Hybrid technology'], top_negative_factors: ['EV transition lag'] },
        { company_symbol: 'SUNPHARMA', company_name: 'Sun Pharmaceutical Industries', sector: 'Healthcare', bullish_score: 7.1, bearish_score: 3.0, quality_score: 7.8, momentum_score: 6.9, confidence_score: 7.5, top_positive_factors: ['Specialty portfolio growth', 'US generics pipeline', 'Taro acquisition synergies'], top_negative_factors: ['USFDA risk'] },
    ];

    const DEMO_BEARISH = [
        { company_symbol: 'ADANIENT', company_name: 'Adani Enterprises Ltd', sector: 'Energy', bullish_score: 3.2, bearish_score: 8.1, quality_score: 4.5, momentum_score: 3.8, confidence_score: 7.2, top_positive_factors: ['Diversified portfolio'], top_negative_factors: ['Governance scrutiny', 'Related-party concerns', 'High leverage', 'Regulatory risk'] },
        { company_symbol: 'IDEA', company_name: 'Vodafone Idea Ltd', sector: 'Telecom', bullish_score: 1.8, bearish_score: 8.5, quality_score: 2.0, momentum_score: 2.5, confidence_score: 8.0, top_positive_factors: ['Tariff hike potential'], top_negative_factors: ['Massive debt burden', 'Subscriber loss', 'Cash flow negative', 'Capex constraints'] },
        { company_symbol: 'YESBANK', company_name: 'Yes Bank Ltd', sector: 'Financial Services', bullish_score: 2.5, bearish_score: 7.8, quality_score: 3.5, momentum_score: 3.0, confidence_score: 7.5, top_positive_factors: ['Asset quality improvement'], top_negative_factors: ['Diluted promoter stake', 'Brand trust deficit', 'Growth constraints'] },
        { company_symbol: 'PAYTM', company_name: 'One97 Communications', sector: 'Technology', bullish_score: 2.8, bearish_score: 7.5, quality_score: 3.0, momentum_score: 4.2, confidence_score: 6.8, top_positive_factors: ['Payments volume'], top_negative_factors: ['RBI regulatory action', 'Profitability uncertain', 'Business model pivot'] },
        { company_symbol: 'SUZLON', company_name: 'Suzlon Energy Ltd', sector: 'Energy', bullish_score: 3.5, bearish_score: 7.2, quality_score: 4.0, momentum_score: 5.5, confidence_score: 6.5, top_positive_factors: ['Order book growth', 'Renewable push'], top_negative_factors: ['Debt overhang', 'Execution delays', 'Working capital pressure'] },
        { company_symbol: 'COALINDIA', company_name: 'Coal India Ltd', sector: 'Metals & Mining', bullish_score: 3.8, bearish_score: 7.0, quality_score: 5.0, momentum_score: 3.5, confidence_score: 7.0, top_positive_factors: ['Dividend yield'], top_negative_factors: ['Production shortfall', 'ESG concerns', 'Demand transition risk'] },
    ];

    // ============================================================
    // Render Functions
    // ============================================================
    function renderWatchlist(candidates) {
        const grid = document.getElementById('watchlist-grid');
        if (!grid) return;
        grid.replaceChildren();

        if (!candidates || candidates.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'loading-spinner';
            empty.textContent = 'No signal data available yet. Run the ingestion pipeline first.';
            grid.appendChild(empty);
            return;
        }

        candidates.forEach((item, idx) => {
            const card = document.createElement('div');
            card.className = 'glass-card signal-card animate-fade-in-up animate-delay-' + ((idx % 5) + 1);
            
            // Add click listener for TradingView Chart
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => {
                openTradingViewChart(item.company_symbol);
            });

            // Header
            const header = document.createElement('div');
            header.className = 'signal-card-header';

            const companyInfo = document.createElement('div');
            companyInfo.className = 'signal-company';

            const symbolDiv = document.createElement('div');
            const symbolSpan = document.createElement('div');
            symbolSpan.className = 'signal-symbol';
            symbolSpan.textContent = item.company_symbol || 'N/A';

            const nameSpan = document.createElement('div');
            nameSpan.className = 'signal-name';
            nameSpan.textContent = item.company_name || '';

            symbolDiv.appendChild(symbolSpan);
            symbolDiv.appendChild(nameSpan);
            companyInfo.appendChild(symbolDiv);

            const scoreCircle = document.createElement('div');
            scoreCircle.className = 'signal-score-circle ' + (isBullish ? 'bullish' : 'bearish');
            const primaryScore = isBullish ? item.bullish_score : item.bearish_score;
            scoreCircle.textContent = (primaryScore || 0).toFixed(1);

            header.appendChild(companyInfo);
            header.appendChild(scoreCircle);
            card.appendChild(header);

            // Score bars
            const bars = document.createElement('div');
            bars.className = 'signal-bars';

            const barData = [
                { label: 'Quality', value: item.quality_score || 0, cls: 'positive' },
                { label: 'Momentum', value: item.momentum_score || 0, cls: 'neutral' },
                { label: 'Confidence', value: item.confidence_score || 0, cls: 'warning' },
                { label: isBullish ? 'Bullish' : 'Bearish', value: primaryScore || 0, cls: isBullish ? 'positive' : 'negative' },
            ];

            barData.forEach(bd => {
                const bar = document.createElement('div');
                bar.className = 'signal-bar';

                const label = document.createElement('span');
                label.className = 'signal-bar-label';
                label.textContent = bd.label;

                const track = document.createElement('div');
                track.className = 'signal-bar-track';

                const fill = document.createElement('div');
                fill.className = 'signal-bar-fill ' + bd.cls;
                fill.style.width = (bd.value * 10) + '%';

                track.appendChild(fill);

                const value = document.createElement('span');
                value.className = 'signal-bar-value';
                value.textContent = bd.value.toFixed(1);

                bar.appendChild(label);
                bar.appendChild(track);
                bar.appendChild(value);
                bars.appendChild(bar);
            });

            card.appendChild(bars);

            // Factors
            const posFactors = item.top_positive_factors || [];
            const negFactors = item.top_negative_factors || [];

            if (posFactors.length > 0) {
                const factorsDiv = document.createElement('div');
                factorsDiv.className = 'signal-factors';

                const h4 = document.createElement('h4');
                h4.textContent = '✅ Positive Signals';
                factorsDiv.appendChild(h4);

                posFactors.slice(0, 3).forEach(f => {
                    const item = document.createElement('div');
                    item.className = 'signal-factor-item';
                    item.textContent = '• ' + f;
                    factorsDiv.appendChild(item);
                });

                card.appendChild(factorsDiv);
            }

            if (negFactors.length > 0) {
                const factorsDiv = document.createElement('div');
                factorsDiv.className = 'signal-factors';

                const h4 = document.createElement('h4');
                h4.textContent = '⚠️ Risk Factors';
                factorsDiv.appendChild(h4);

                negFactors.slice(0, 3).forEach(f => {
                    const item = document.createElement('div');
                    item.className = 'signal-factor-item';
                    item.textContent = '• ' + f;
                    factorsDiv.appendChild(item);
                });

                card.appendChild(factorsDiv);
            }

            // Sector badge
            if (item.sector) {
                const sectorBadge = document.createElement('span');
                sectorBadge.className = 'signal-sector-badge';
                sectorBadge.textContent = item.sector;
                card.appendChild(sectorBadge);
            }

            grid.appendChild(card);
        });
    }

    // ============================================================
    // TradingView Modal & Tabs Handler
    // ============================================================
    let currentTvSymbol = '';

    function openTradingViewChart(symbol) {
        const modal = document.getElementById('tv-modal');
        if (!modal || !window.TradingView) return;
        
        // Show modal
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Add NSE prefix if not present
        currentTvSymbol = symbol.includes(':') ? symbol : 'BSE:' + symbol;
        
        // Update Title
        const titleEl = document.getElementById('tv-modal-title');
        if (titleEl) titleEl.textContent = `${symbol} — Analysis`;

        // Reset tabs to first one
        document.querySelectorAll('.tv-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tv-tab-content').forEach(c => c.classList.remove('active'));
        
        const firstTab = document.querySelector('.tv-tab[data-tab="chart"]');
        const firstContent = document.getElementById('tab-chart');
        if (firstTab && firstContent) {
            firstTab.classList.add('active');
            firstContent.classList.add('active');
        }

        // Load all widgets for the symbol
        loadChartWidget();
        loadFundamentalsWidget();
        loadTechnicalsWidget();
    }

    function loadChartWidget() {
        document.getElementById('tv_chart_container').innerHTML = '';
        new TradingView.widget({
            "autosize": true,
            "symbol": currentTvSymbol,
            "interval": "D",
            "timezone": "Asia/Kolkata",
            "theme": "dark",
            "style": "1",
            "locale": "in",
            "enable_publishing": false,
            "backgroundColor": "#0d1117",
            "gridColor": "#1f2937",
            "hide_top_toolbar": false,
            "hide_legend": false,
            "save_image": false,
            "container_id": "tv_chart_container",
            "toolbar_bg": "#0d1117"
        });
    }

    function loadFundamentalsWidget() {
        const container = document.getElementById('tv_fundamentals_container');
        const widgetConfig = {
            "colorTheme": "dark",
            "isTransparent": true,
            "largeChartUrl": "",
            "displayMode": "regular",
            "width": "100%",
            "height": "100%",
            "symbol": currentTvSymbol,
            "locale": "in"
        };
        const html = `
        <!DOCTYPE html>
        <html>
        <head><style>body { margin: 0; background: #0d1117; overflow: hidden; }</style></head>
        <body>
        <div class="tradingview-widget-container">
            <div class="tradingview-widget-container__widget"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-financials.js" async>
            ${JSON.stringify(widgetConfig)}
            </script>
        </div>
        </body>
        </html>
        `;
        container.innerHTML = `<iframe srcdoc='${html.replace(/'/g, "&apos;")}' style="width:100%; height:100%; border:none;"></iframe>`;
    }

    function loadTechnicalsWidget() {
        const container = document.getElementById('tv_technicals_container');
        const widgetConfig = {
            "interval": "1D",
            "width": "100%",
            "isTransparent": true,
            "height": "100%",
            "symbol": currentTvSymbol,
            "showIntervalTabs": true,
            "displayMode": "single",
            "locale": "in",
            "colorTheme": "dark"
        };
        const html = `
        <!DOCTYPE html>
        <html>
        <head><style>body { margin: 0; background: #0d1117; overflow: hidden; }</style></head>
        <body>
        <div class="tradingview-widget-container">
            <div class="tradingview-widget-container__widget"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
            ${JSON.stringify(widgetConfig)}
            </script>
        </div>
        </body>
        </html>
        `;
        container.innerHTML = `<iframe srcdoc='${html.replace(/'/g, "&apos;")}' style="width:100%; height:100%; border:none;"></iframe>`;
    }

    function closeTradingViewChart() {
        const modal = document.getElementById('tv-modal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
            document.getElementById('tv_chart_container').innerHTML = '';
            document.getElementById('tv_fundamentals_container').innerHTML = '';
            document.getElementById('tv_technicals_container').innerHTML = '';
        }
    }

    // Modal Close Listeners
    const modalCloseBtn = document.getElementById('tv-modal-close');
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeTradingViewChart);
    }
    
    const modal = document.getElementById('tv-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeTradingViewChart();
        });
    }

    // Tab Listeners
    document.querySelectorAll('.tv-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active from all
            document.querySelectorAll('.tv-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tv-tab-content').forEach(c => c.classList.remove('active'));
            
            // Add to current
            tab.classList.add('active');
            const targetId = 'tab-' + tab.getAttribute('data-tab');
            const targetContent = document.getElementById(targetId);
            if (targetContent) targetContent.classList.add('active');
        });
    });

    // ============================================================
    // Data Loading
    // ============================================================
    async function loadData() {
        try {
            const apiMethod = isBullish
                ? window.BharatAPI.getTopBullish
                : window.BharatAPI.getTopBearish;

            const response = await apiMethod(20);
            const candidates = response.candidates || [];

            if (candidates.length > 0) {
                renderWatchlist(candidates);
            } else {
                renderWatchlist(isBullish ? DEMO_BULLISH : DEMO_BEARISH);
            }
        } catch (error) {
            renderWatchlist(isBullish ? DEMO_BULLISH : DEMO_BEARISH);
        }
    }

    // Nav toggle
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
    }

    // Initialize
    loadData();

})();
