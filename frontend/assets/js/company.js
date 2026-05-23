/**
 * Bharat Market Intelligence Agent — Company Hub JavaScript
 */

(function () {
    'use strict';

    // 1. Get symbol from URL
    const urlParams = new URLSearchParams(window.location.search);
    let rawSymbol = urlParams.get('symbol') || 'RELIANCE'; // default if none provided
    rawSymbol = rawSymbol.toUpperCase().trim();
    
    // Remove spaces for TradingView compatibility (e.g. "TATA STEEL" -> "TATASTEEL")
    const cleanSymbol = rawSymbol.replace(/\s+/g, '');
    
    // Add BSE prefix for TradingView if not present (NSE restricts widget embedding)
    const tvSymbol = cleanSymbol.includes(':') ? cleanSymbol : 'BSE:' + cleanSymbol;
    
    // Display symbol (can have spaces for the title, but we'll use raw)
    const displaySymbol = rawSymbol.includes(':') ? rawSymbol.split(':')[1] : rawSymbol;

    // Update basic UI elements
    document.getElementById('c-symbol').textContent = tvSymbol;
    document.getElementById('c-name').textContent = displaySymbol + " Analysis";
    document.title = `${displaySymbol} — Bharat Market Intelligence`;

    // 2. Initialize TradingView Widgets
    function initTradingView() {
        /**
         * Direct DOM injection for TradingView widgets.
         * 
         * WHY NOT Blob URLs / srcdoc iframes:
         * TradingView widgets make XHR calls back to their servers.
         * Blob URLs create an opaque origin (blob:null) which blocks
         * these requests due to same-origin policy. This is why the
         * Fundamentals showed only headers and Technicals showed
         * interval tabs but no gauge/data.
         *
         * The fix: inject the widget script directly into the page DOM.
         * For symbols with & (e.g. M&M), we JSON.stringify the config
         * which properly escapes special chars inside the script text.
         */
        function createTVWidget(container, widgetScript, config) {
            if (!container) return;
            container.innerHTML = '';

            // Create the widget wrapper that TradingView expects
            const wrapper = document.createElement('div');
            wrapper.className = 'tradingview-widget-container';
            wrapper.style.cssText = 'width:100%;height:100%;';

            const inner = document.createElement('div');
            inner.className = 'tradingview-widget-container__widget';
            inner.style.cssText = 'width:100%;height:100%;';
            wrapper.appendChild(inner);

            // Create the script element with config as its text content
            const script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = widgetScript;
            script.async = true;
            script.textContent = JSON.stringify(config);
            wrapper.appendChild(script);

            container.appendChild(wrapper);
        }

        // Main Chart — uses TradingView JS API (works fine)
        if (window.TradingView) {
            new TradingView.widget({
                "autosize": true,
                "symbol": tvSymbol,
                "interval": "D",
                "timezone": "Asia/Kolkata",
                "theme": "dark",
                "style": "1",
                "locale": "in",
                "enable_publishing": false,
                "backgroundColor": "#060a13",
                "gridColor": "#1a1f2e",
                "hide_top_toolbar": false,
                "hide_legend": false,
                "save_image": false,
                "container_id": "tv_chart_main",
                "toolbar_bg": "#060a13"
            });
        }

        // Fundamentals — direct DOM injection (fixes blank widget)
        createTVWidget(
            document.getElementById('tv_fundamentals_main'),
            'https://s3.tradingview.com/external-embedding/embed-widget-financials.js',
            {
                "colorTheme": "dark",
                "isTransparent": true,
                "largeChartUrl": "",
                "displayMode": "regular",
                "width": "100%",
                "height": "100%",
                "symbol": tvSymbol,
                "locale": "in"
            }
        );

        // Technicals — direct DOM injection (fixes blank gauge)
        createTVWidget(
            document.getElementById('tv_technicals_main'),
            'https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js',
            {
                "interval": "1D",
                "width": "100%",
                "isTransparent": true,
                "height": "100%",
                "symbol": tvSymbol,
                "showIntervalTabs": true,
                "displayMode": "single",
                "locale": "in",
                "colorTheme": "dark"
            }
        );
    }

    // 3. Fetch company metadata (name, sector)
    async function loadCompanyInfo() {
        try {
            if (!window.BharatAPI) return;
            const company = await window.BharatAPI.getCompany(cleanSymbol);
            if (company) {
                document.getElementById('c-name').textContent = company.company_name;
                document.getElementById('c-symbol').textContent = company.nse_symbol || company.symbol;
                if (company.sector) {
                    document.getElementById('c-sector').textContent = `${company.sector} · ${company.industry || 'Intelligence Hub'}`;
                }
            }
        } catch (e) {
            // Not in DB — keep the default display
            console.log(`Company ${cleanSymbol} not in database — TradingView widgets will still work`);
        }
    }

    // 4. Load AI Intelligence Data
    async function loadAIData() {
        // Pre-check: is the API module even loaded?
        if (!window.BharatAPI || !window.BharatAPI.getThesis) {
            showNoDataState('Backend API not loaded. Please refresh the page.');
            return;
        }

        let thesisResponse = null;
        let eventsResponse = null;
        let thesisError = null;
        let eventsError = null;

        // Fetch thesis and events independently (don't let one failure kill both)
        try {
            thesisResponse = await window.BharatAPI.getThesis(cleanSymbol);
        } catch (e) {
            thesisError = e;
        }

        try {
            eventsResponse = await window.BharatAPI.getCompanyEvents(cleanSymbol, { limit: 5 });
        } catch (e) {
            eventsError = e;
        }

        // If BOTH failed with "Company not found", show a clean message
        const is404 = (e) => e && (e.message.includes('Company not found') || e.message.includes('404'));
        if (is404(thesisError) && is404(eventsError)) {
            showNoDataState(`${displaySymbol} is not yet tracked in our intelligence database. TradingView charts above show live market data.`);
            return;
        }

        // If backend is down entirely
        if (thesisError && eventsError) {
            showNoDataState('Unable to reach the intelligence backend. Charts above show live market data from TradingView.');
            return;
        }

        // ── Render thesis data ──────────────────────────────────────
        const bullishTheses = thesisResponse?.bullish_theses || [];
        const bearishTheses = thesisResponse?.bearish_theses || [];

        const totalTheses = bullishTheses.length + bearishTheses.length;
        let isBullish = bullishTheses.length >= bearishTheses.length;
        let scoreStr = "--";
        
        if (totalTheses > 0) {
            const ratio = bullishTheses.length / totalTheses;
            const calculated = 1.0 + (ratio * 8.9);
            scoreStr = calculated.toFixed(1);
        }

        // Update Score Circle
        const circle = document.getElementById('ai-score-circle');
        circle.textContent = scoreStr;
        if (totalTheses > 0) {
            circle.className = `score-circle ${isBullish ? 'bullish' : 'bearish'}`;
        }

        // Update Labels
        const labelEl = document.getElementById('ai-sentiment-label');
        if (totalTheses > 0) {
            labelEl.textContent = isBullish ? "Bullish Outlook" : "Bearish Risk Alert";
            labelEl.style.color = isBullish ? "var(--color-positive)" : "var(--color-negative)";
            document.getElementById('ai-confidence').textContent = "Based on public data";
        } else {
            labelEl.textContent = "Awaiting AI Analysis";
            labelEl.style.color = "var(--text-muted)";
            document.getElementById('ai-confidence').textContent = "See Prediction Meter above for real-time signals";
        }

        // Update Pros
        const prosList = document.getElementById('ai-pros');
        if (bullishTheses.length > 0) {
            prosList.innerHTML = bullishTheses.slice(0, 3).map(t => `<li>${t.thesis_summary}</li>`).join('');
        } else {
            prosList.innerHTML = `<li><span style="color: var(--text-muted);">AI thesis generation pending. Use the Prediction Meter above for live signals.</span></li>`;
        }

        // Update Cons
        const consList = document.getElementById('ai-cons');
        if (bearishTheses.length > 0) {
            consList.innerHTML = bearishTheses.slice(0, 3).map(t => `<li>${t.thesis_summary}</li>`).join('');
        } else {
            consList.innerHTML = `<li><span style="color: var(--text-muted);">AI risk analysis pending. Candlestick patterns and technical indicators are available above.</span></li>`;
        }

        // ── Render events data ──────────────────────────────────────
        const events = eventsResponse?.events || [];
        const newsFeed = document.getElementById('ai-news-feed');

        if (events.length > 0) {
            const newsHtml = events.map(e => `
                <div class="news-item">
                    <div class="news-time">${new Date(e.event_time).toLocaleString()}</div>
                    <div class="news-title">${e.event_title}</div>
                    <div class="news-summary">${e.event_summary || 'No summary available.'}</div>
                </div>
            `).join('');
            newsFeed.innerHTML = newsHtml;
        } else {
            newsFeed.innerHTML = `
                <div class="empty-state" style="padding: var(--space-2xl); text-align: center;">
                    <p style="color: var(--text-secondary); margin: 0;">No recent events ingested for ${displaySymbol}.</p>
                    <p style="color: var(--text-muted); font-size: 0.8rem; margin-top: var(--space-sm);">Run the data ingestion pipeline to populate filings, announcements, and news. Live candlestick patterns and predictions are available above.</p>
                </div>
            `;
        }
    }

    /**
     * Show a clean "no data" state instead of confusing error messages.
     */
    function showNoDataState(message) {
        document.getElementById('ai-score-circle').textContent = "—";
        document.getElementById('ai-score-circle').className = 'score-circle';

        const labelEl = document.getElementById('ai-sentiment-label');
        labelEl.textContent = "No Data Available";
        labelEl.style.color = "var(--text-muted)";
        document.getElementById('ai-confidence').textContent = "—";

        document.getElementById('ai-pros').innerHTML = `<li><span style="color: var(--text-muted);">No analysis available yet.</span></li>`;
        document.getElementById('ai-cons').innerHTML = `<li><span style="color: var(--text-muted);">No analysis available yet.</span></li>`;

        document.getElementById('ai-news-feed').innerHTML = `
            <div class="empty-state" style="padding: var(--space-2xl); text-align: center;">
                <p style="color: var(--text-secondary); margin: 0; font-size: 0.9rem;">${message}</p>
            </div>
        `;
    }

    // ═══════════════════════════════════════════════════════════════
    // 5. PREDICTION METER — Bullish/Bearish Gauge
    // ═══════════════════════════════════════════════════════════════

    async function loadPredictionMeter() {
        const canvas = document.getElementById('prediction-gauge');
        if (!canvas) return;

        const dirEl = document.getElementById('meter-direction');
        const confEl = document.getElementById('meter-confidence');

        // Draw initial empty gauge
        drawGauge(canvas, 0.5, 'neutral');

        // Fetch candlestick analysis
        if (!window.BharatAPI || !window.BharatAPI.getCandlestickAnalysis) {
            dirEl.textContent = 'Unavailable';
            dirEl.style.color = 'var(--text-muted)';
            confEl.textContent = 'API not loaded';
            return;
        }

        try {
            const data = await window.BharatAPI.getCandlestickAnalysis(cleanSymbol, {
                period: '6mo',
                interval: '1d'
            });

            if (!data || !data.prediction) {
                throw new Error('No prediction data');
            }

            const pred = data.prediction;
            const patterns = data.detected_patterns || [];

            // Convert prediction to 0-1 gauge position
            // 0 = strong bearish, 0.5 = neutral, 1 = strong bullish
            let gaugeVal = 0.5;
            if (pred.direction === 'bullish') {
                gaugeVal = 0.5 + (pred.confidence * 0.5);
            } else if (pred.direction === 'bearish') {
                gaugeVal = 0.5 - (pred.confidence * 0.5);
            }
            gaugeVal = Math.max(0.03, Math.min(0.97, gaugeVal));

            // Animate the gauge
            animateGauge(canvas, gaugeVal, pred.direction);

            // Direction label
            const dirText = getDirectionText(gaugeVal);
            dirEl.textContent = dirText.text;
            dirEl.style.color = dirText.color;

            // Confidence
            confEl.textContent = `${Math.round(pred.confidence * 100)}% confidence`;

            // Populate indicators
            populateIndicators(pred, patterns);

        } catch (e) {
            console.warn('Prediction meter failed:', e.message);
            // Show graceful fallback
            dirEl.textContent = 'Data Loading...';
            dirEl.style.color = 'var(--text-muted)';
            confEl.textContent = 'Retrying in background';

            // Retry once after 15 seconds
            setTimeout(async () => {
                try {
                    const data = await window.BharatAPI.getCandlestickAnalysis(cleanSymbol, {
                        period: '3mo',
                        interval: '1d'
                    });
                    if (data && data.prediction) {
                        const pred = data.prediction;
                        let gv = 0.5;
                        if (pred.direction === 'bullish') gv = 0.5 + pred.confidence * 0.5;
                        else if (pred.direction === 'bearish') gv = 0.5 - pred.confidence * 0.5;
                        gv = Math.max(0.03, Math.min(0.97, gv));
                        animateGauge(canvas, gv, pred.direction);
                        const dt = getDirectionText(gv);
                        dirEl.textContent = dt.text;
                        dirEl.style.color = dt.color;
                        confEl.textContent = `${Math.round(pred.confidence * 100)}% confidence`;
                        populateIndicators(pred, data.detected_patterns || []);
                    }
                } catch (_) {
                    dirEl.textContent = 'Unavailable';
                    confEl.textContent = 'Try refreshing';
                }
            }, 15000);
        }
    }

    function getDirectionText(gaugeVal) {
        if (gaugeVal >= 0.85) return { text: 'STRONG BUY', color: '#22c55e' };
        if (gaugeVal >= 0.65) return { text: 'BULLISH', color: '#4ade80' };
        if (gaugeVal >= 0.55) return { text: 'SLIGHTLY BULLISH', color: '#86efac' };
        if (gaugeVal >= 0.45) return { text: 'NEUTRAL', color: '#f59e0b' };
        if (gaugeVal >= 0.35) return { text: 'SLIGHTLY BEARISH', color: '#fca5a5' };
        if (gaugeVal >= 0.15) return { text: 'BEARISH', color: '#f87171' };
        return { text: 'STRONG SELL', color: '#ef4444' };
    }

    function drawGauge(canvas, value, direction) {
        const ctx = canvas.getContext('2d');
        const W = canvas.width;
        const H = canvas.height;
        const cx = W / 2;
        const cy = H - 10;
        const radius = Math.min(W, H * 2) / 2 - 20;

        ctx.clearRect(0, 0, W, H);

        // Arc parameters
        const startAngle = Math.PI;
        const endAngle = 2 * Math.PI;

        // Background arc segments (gradient: red → yellow → green)
        const segments = [
            { start: 0, end: 0.2, color: '#dc2626' },
            { start: 0.2, end: 0.35, color: '#ef4444' },
            { start: 0.35, end: 0.45, color: '#f59e0b' },
            { start: 0.45, end: 0.55, color: '#eab308' },
            { start: 0.55, end: 0.65, color: '#84cc16' },
            { start: 0.65, end: 0.8, color: '#22c55e' },
            { start: 0.8, end: 1.0, color: '#16a34a' },
        ];

        segments.forEach(seg => {
            const a1 = startAngle + seg.start * Math.PI;
            const a2 = startAngle + seg.end * Math.PI;
            ctx.beginPath();
            ctx.arc(cx, cy, radius, a1, a2);
            ctx.lineWidth = 18;
            ctx.strokeStyle = seg.color;
            ctx.globalAlpha = 0.25;
            ctx.stroke();
        });

        // Active arc (filled to current value)
        ctx.globalAlpha = 1.0;
        const activeEnd = startAngle + value * Math.PI;
        const gradient = ctx.createLinearGradient(cx - radius, cy, cx + radius, cy);
        gradient.addColorStop(0, '#ef4444');
        gradient.addColorStop(0.3, '#f59e0b');
        gradient.addColorStop(0.5, '#eab308');
        gradient.addColorStop(0.7, '#84cc16');
        gradient.addColorStop(1, '#22c55e');

        ctx.beginPath();
        ctx.arc(cx, cy, radius, startAngle, activeEnd);
        ctx.lineWidth = 18;
        ctx.strokeStyle = gradient;
        ctx.lineCap = 'round';
        ctx.stroke();

        // Glow effect on active arc
        ctx.beginPath();
        ctx.arc(cx, cy, radius, startAngle, activeEnd);
        ctx.lineWidth = 18;
        const glowColor = value > 0.6 ? 'rgba(34,197,94,0.15)' :
                          value < 0.4 ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)';
        ctx.strokeStyle = glowColor;
        ctx.shadowColor = value > 0.6 ? '#22c55e' : value < 0.4 ? '#ef4444' : '#f59e0b';
        ctx.shadowBlur = 20;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Needle
        const needleAngle = startAngle + value * Math.PI;
        const needleLen = radius - 25;
        const nx = cx + Math.cos(needleAngle) * needleLen;
        const ny = cy + Math.sin(needleAngle) * needleLen;

        // Needle line
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(nx, ny);
        ctx.lineWidth = 3;
        ctx.strokeStyle = '#ffffff';
        ctx.lineCap = 'round';
        ctx.stroke();

        // Needle center dot
        ctx.beginPath();
        ctx.arc(cx, cy, 6, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.beginPath();
        ctx.arc(cx, cy, 3, 0, Math.PI * 2);
        ctx.fillStyle = value > 0.6 ? '#22c55e' : value < 0.4 ? '#ef4444' : '#f59e0b';
        ctx.fill();

        // Tick marks
        ctx.globalAlpha = 0.5;
        for (let i = 0; i <= 10; i++) {
            const a = startAngle + (i / 10) * Math.PI;
            const inner = radius + 12;
            const outer = radius + (i % 5 === 0 ? 20 : 16);
            ctx.beginPath();
            ctx.moveTo(cx + Math.cos(a) * inner, cy + Math.sin(a) * inner);
            ctx.lineTo(cx + Math.cos(a) * outer, cy + Math.sin(a) * outer);
            ctx.lineWidth = i % 5 === 0 ? 2 : 1;
            ctx.strokeStyle = '#ffffff';
            ctx.stroke();
        }
        ctx.globalAlpha = 1;
    }

    function animateGauge(canvas, targetVal, direction) {
        let current = 0.5;
        const steps = 40;
        const increment = (targetVal - current) / steps;
        let step = 0;

        function frame() {
            current += increment;
            step++;
            drawGauge(canvas, current, direction);
            if (step < steps) {
                requestAnimationFrame(frame);
            } else {
                drawGauge(canvas, targetVal, direction);
            }
        }
        requestAnimationFrame(frame);
    }

    function populateIndicators(prediction, patterns) {
        // Trend alignment
        const trendEl = document.getElementById('mi-trend');
        if (trendEl) {
            const ta = prediction.trend_alignment || 'neutral';
            const trendText = ta.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const trendColor = ta.includes('bullish') ? '#22c55e' :
                               ta.includes('bearish') ? '#ef4444' : '#f59e0b';
            trendEl.textContent = trendText;
            trendEl.style.color = trendColor;
        }

        // RSI — extract from summary
        const rsiEl = document.getElementById('mi-rsi');
        if (rsiEl) {
            const rsiMatch = (prediction.summary || '').match(/RSI:\s*(\d+)/);
            if (rsiMatch) {
                const rsiVal = parseInt(rsiMatch[1]);
                let rsiLabel = rsiVal < 30 ? 'Oversold' : rsiVal > 70 ? 'Overbought' : 'Normal';
                let rsiColor = rsiVal < 30 ? '#22c55e' : rsiVal > 70 ? '#ef4444' : 'var(--text-primary)';
                rsiEl.textContent = `${rsiVal} (${rsiLabel})`;
                rsiEl.style.color = rsiColor;
            } else {
                rsiEl.textContent = '—';
            }
        }

        // Pattern count
        const patternsEl = document.getElementById('mi-patterns');
        if (patternsEl) {
            const bullish = patterns.filter(p => p.pattern_type === 'bullish').length;
            const bearish = patterns.filter(p => p.pattern_type === 'bearish').length;
            if (patterns.length > 0) {
                patternsEl.innerHTML = `<span style="color:#22c55e;">${bullish} bullish</span> · <span style="color:#ef4444;">${bearish} bearish</span>`;
            } else {
                patternsEl.textContent = 'None detected';
            }
        }

        // Support
        const supportEl = document.getElementById('mi-support');
        if (supportEl && prediction.support_level) {
            supportEl.textContent = '₹' + prediction.support_level.toLocaleString('en-IN');
        }

        // Resistance
        const resistanceEl = document.getElementById('mi-resistance');
        if (resistanceEl && prediction.resistance_level) {
            resistanceEl.textContent = '₹' + prediction.resistance_level.toLocaleString('en-IN');
        }

        // Pattern badges
        const summaryEl = document.getElementById('meter-patterns-summary');
        if (summaryEl && patterns.length > 0) {
            // Deduplicate by name
            const seen = new Set();
            const unique = patterns.filter(p => {
                if (seen.has(p.pattern_name)) return false;
                seen.add(p.pattern_name);
                return true;
            }).slice(0, 6);

            summaryEl.innerHTML = unique.map(p => {
                const cls = p.pattern_type === 'bullish' ? 'bullish' :
                            p.pattern_type === 'bearish' ? 'bearish' : 'neutral';
                const icon = p.pattern_type === 'bullish' ? '▲' :
                             p.pattern_type === 'bearish' ? '▼' : '◆';
                return `<span class="meter-pat-badge ${cls}">${icon} ${p.pattern_name}</span>`;
            }).join('');
        }
    }

    // Nav toggle
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
    }

    // ═══════════════════════════════════════════════════════════════
    // 6. MULTI-TIMEFRAME STOCK RATING
    // ═══════════════════════════════════════════════════════════════

    async function loadStockRating() {
        if (!window.BharatAPI || !window.BharatAPI.getStockRating) return;

        try {
            const data = await window.BharatAPI.getStockRating(cleanSymbol);
            if (!data || !data.timeframes) throw new Error('No rating data');

            renderOverallRating(data.overall);
            renderTimeframeCards(data.timeframes);
        } catch (e) {
            console.warn('Stock rating failed:', e.message);
            // Remove loading spinners and show fallback
            const grid = document.getElementById('sr-timeframe-grid');
            if (grid) {
                grid.querySelectorAll('.sr-tf-card').forEach(card => {
                    card.classList.remove('sr-loading');
                    const spinner = card.querySelector('.sr-tf-spinner');
                    if (spinner) spinner.remove();
                    const existing = card.querySelector('.sr-tf-rating');
                    if (!existing) {
                        const fallback = document.createElement('div');
                        fallback.className = 'sr-tf-rating neutral';
                        fallback.textContent = 'UNAVAILABLE';
                        card.appendChild(fallback);
                    }
                });
            }
            const overallLabel = document.getElementById('sr-overall-label');
            if (overallLabel) overallLabel.textContent = 'Rating unavailable — data loading';
        }
    }

    function renderOverallRating(overall) {
        if (!overall) return;

        const badge = document.getElementById('sr-overall-badge');
        const label = document.getElementById('sr-overall-label');
        const scoreEl = document.getElementById('sr-overall-score');
        const confEl = document.getElementById('sr-overall-conf');
        const factorsEl = document.getElementById('sr-overall-factors');

        // Score badge with animation
        badge.className = 'sr-overall-badge ' + overall.rating_class;
        animateNumber(badge, overall.score, true);

        // Labels
        label.textContent = 'Overall: ' + overall.rating;
        label.style.color = getRatingColor(overall.rating_class);
        scoreEl.textContent = 'Score: ' + (overall.score > 0 ? '+' : '') + overall.score + ' / 10';
        confEl.textContent = 'Confidence: ' + overall.confidence + '%';

        // Key factors
        if (factorsEl && overall.key_factors) {
            factorsEl.innerHTML = overall.key_factors.slice(0, 6).map(f => {
                const isBullish = f.includes('▲');
                const isBearish = f.includes('▼');
                const cls = isBullish ? 'bullish' : isBearish ? 'bearish' : '';
                // Sanitize: use textContent approach via DOM
                const tag = document.createElement('span');
                tag.className = 'sr-factor-tag ' + cls;
                tag.textContent = f;
                return tag.outerHTML;
            }).join('');
        }
    }

    function renderTimeframeCards(timeframes) {
        const tfMap = {
            '1D': 'sr-tf-1d',
            '1W': 'sr-tf-1w',
            '1M': 'sr-tf-1m',
            '3M': 'sr-tf-3m',
        };

        for (const [key, elementId] of Object.entries(tfMap)) {
            const card = document.getElementById(elementId);
            const tf = timeframes[key];
            if (!card || !tf) continue;

            card.classList.remove('sr-loading');
            card.className = 'glass-card sr-tf-card ' + tf.rating_class;

            const scoreClass = tf.score > 0 ? 'positive' : tf.score < 0 ? 'negative' : 'zero';

            card.innerHTML = `
                <div class="sr-tf-label">${tf.timeframe}</div>
                <div class="sr-tf-rating ${tf.rating_class}">${tf.rating}</div>
                <div class="sr-tf-score ${scoreClass}" data-target="${tf.score}">0</div>
                <div class="sr-tf-conf">${tf.confidence}% confidence</div>
                <div class="sr-tf-indicators">
                    ${tf.bullish_patterns > 0 ? `<span class="sr-tf-ind" style="color:#22c55e;">▲${tf.bullish_patterns} bullish</span>` : ''}
                    ${tf.bearish_patterns > 0 ? `<span class="sr-tf-ind" style="color:#ef4444;">▼${tf.bearish_patterns} bearish</span>` : ''}
                    <span class="sr-tf-ind">RSI ${tf.rsi}</span>
                </div>
            `;

            // Animate the score number
            const scoreEl = card.querySelector('.sr-tf-score');
            if (scoreEl) {
                animateNumber(scoreEl, tf.score, true);
            }
        }
    }

    function animateNumber(element, target, showSign) {
        const duration = 800;
        const start = performance.now();
        const startVal = 0;

        function update(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = startVal + (target - startVal) * eased;
            const formatted = current.toFixed(1);
            element.textContent = (showSign && current > 0 ? '+' : '') + formatted;
            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.textContent = (showSign && target > 0 ? '+' : '') + target.toFixed(1);
            }
        }
        requestAnimationFrame(update);
    }

    function getRatingColor(ratingClass) {
        const colors = {
            strong_buy: '#22c55e',
            buy: '#4ade80',
            neutral: '#f59e0b',
            sell: '#f87171',
            strong_sell: '#ef4444',
        };
        return colors[ratingClass] || '#f59e0b';
    }

    // ═══════════════════════════════════════════════════════════════
    // 7. NEWS IMPACT TIMELINE
    // ═══════════════════════════════════════════════════════════════

    async function loadNewsImpact() {
        if (!window.BharatAPI || !window.BharatAPI.getCompanyEvents) return;

        const listEl = document.getElementById('sr-news-list');
        if (!listEl) return;

        try {
            const eventsData = await window.BharatAPI.getCompanyEvents(cleanSymbol, { limit: 8 });
            const events = eventsData?.events || [];

            if (events.length === 0) {
                listEl.innerHTML = `
                    <div style="padding: var(--space-lg); text-align: center; color: var(--text-muted); font-size: 0.82rem;">
                        No recent news events for ${displaySymbol}. Run the data pipeline to ingest latest filings and announcements.
                    </div>
                `;
                return;
            }

            listEl.innerHTML = events.map(e => {
                const impact = e.impact_label || 'neutral';
                const dotClass = impact === 'positive' ? 'positive' :
                                 impact === 'negative' ? 'negative' : 'neutral';
                const sentiment = e.sentiment_score || 0;
                const sentimentText = sentiment > 0.2 ? '▲ Bullish' :
                                      sentiment < -0.2 ? '▼ Bearish' : '◆ Neutral';
                const sentimentColor = sentiment > 0.2 ? '#22c55e' :
                                       sentiment < -0.2 ? '#ef4444' : '#f59e0b';

                let timeAgo = '';
                try {
                    const eventDate = new Date(e.event_time);
                    const hoursAgo = Math.round((Date.now() - eventDate.getTime()) / 3600000);
                    if (hoursAgo < 24) timeAgo = hoursAgo + 'h ago';
                    else if (hoursAgo < 168) timeAgo = Math.round(hoursAgo / 24) + 'd ago';
                    else timeAgo = eventDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
                } catch (_) {}

                // Create elements safely for headline text
                const headlineSpan = document.createElement('span');
                headlineSpan.textContent = e.event_title || e.event_type || 'Event';
                const safeHeadline = headlineSpan.innerHTML;

                return `
                    <div class="sr-news-item">
                        <div class="sr-news-dot ${dotClass}"></div>
                        <div class="sr-news-body">
                            <div class="sr-news-headline">${safeHeadline}</div>
                            <div class="sr-news-meta">
                                <span style="color:${sentimentColor}">${sentimentText}</span>
                                ${e.event_type ? ' · ' + e.event_type.replace(/_/g, ' ') : ''}
                                ${timeAgo ? ' · ' + timeAgo : ''}
                                ${e.severity ? ' · ' + e.severity : ''}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

        } catch (e) {
            listEl.innerHTML = `
                <div style="padding: var(--space-lg); text-align: center; color: var(--text-muted); font-size: 0.82rem;">
                    News timeline unavailable. The company may not be tracked yet.
                </div>
            `;
        }
    }

    // Execute
    initTradingView();
    loadCompanyInfo();
    loadAIData();
    loadPredictionMeter();
    loadStockRating();
    loadNewsImpact();

})();
