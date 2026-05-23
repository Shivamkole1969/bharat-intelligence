/**
 * Bharat Market Intelligence — User Guide Modal
 *
 * Self-contained component that injects:
 * 1. A "📖 Guide" button into the navbar
 * 2. A slide-in panel with full feature documentation
 *
 * Include this script on any page to add the guide.
 */

(function () {
    'use strict';

    // ── Inject CSS ──────────────────────────────────────────────────────
    const css = `
    .guide-trigger {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 8px;
        background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(245,158,11,0.05));
        border: 1px solid rgba(245,158,11,0.3);
        color: #f59e0b;
        font-size: 0.78rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        letter-spacing: 0.02em;
        white-space: nowrap;
    }
    .guide-trigger:hover {
        background: linear-gradient(135deg, rgba(245,158,11,0.25), rgba(245,158,11,0.1));
        border-color: rgba(245,158,11,0.5);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(245,158,11,0.15);
    }
    .guide-trigger-icon {
        font-size: 1rem;
    }

    /* Overlay */
    .guide-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(4px);
        z-index: 9998;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease, visibility 0.3s ease;
    }
    .guide-overlay.active {
        opacity: 1;
        visibility: visible;
    }

    /* Panel */
    .guide-panel {
        position: fixed;
        top: 0;
        right: 0;
        width: 480px;
        max-width: 92vw;
        height: 100vh;
        background: #0a0f1a;
        border-left: 1px solid rgba(245,158,11,0.15);
        z-index: 9999;
        transform: translateX(100%);
        transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    .guide-panel.active {
        transform: translateX(0);
    }

    .guide-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 24px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        background: rgba(0,0,0,0.3);
        flex-shrink: 0;
    }
    .guide-header h2 {
        margin: 0;
        font-size: 1.15rem;
        font-weight: 700;
        color: #f5f5f5;
    }
    .guide-header h2 span {
        color: #f59e0b;
    }
    .guide-close {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
        background: rgba(255,255,255,0.04);
        color: #999;
        font-size: 1.1rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }
    .guide-close:hover {
        background: rgba(239,68,68,0.15);
        border-color: rgba(239,68,68,0.3);
        color: #ef4444;
    }

    .guide-body {
        flex: 1;
        overflow-y: auto;
        padding: 24px;
    }
    .guide-body::-webkit-scrollbar { width: 4px; }
    .guide-body::-webkit-scrollbar-track { background: transparent; }
    .guide-body::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

    .guide-section {
        margin-bottom: 28px;
    }
    .guide-section-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #f59e0b;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .guide-section-title .gs-icon {
        font-size: 1.1rem;
    }
    .guide-desc {
        font-size: 0.82rem;
        color: rgba(255,255,255,0.7);
        line-height: 1.6;
        margin-bottom: 10px;
    }
    .guide-features {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .guide-features li {
        font-size: 0.78rem;
        color: rgba(255,255,255,0.6);
        padding: 5px 0 5px 18px;
        position: relative;
        line-height: 1.5;
    }
    .guide-features li::before {
        content: '→';
        position: absolute;
        left: 0;
        color: #22c55e;
        font-weight: 700;
    }
    .guide-kbd {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 4px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        font-size: 0.7rem;
        font-family: monospace;
        color: rgba(255,255,255,0.6);
    }
    .guide-tip {
        padding: 10px 14px;
        border-radius: 8px;
        background: rgba(34,197,94,0.06);
        border: 1px solid rgba(34,197,94,0.15);
        font-size: 0.75rem;
        color: rgba(34,197,94,0.9);
        margin-top: 8px;
    }
    .guide-divider {
        height: 1px;
        background: rgba(255,255,255,0.06);
        margin: 20px 0;
    }
    .guide-footer {
        padding: 16px 24px;
        border-top: 1px solid rgba(255,255,255,0.06);
        text-align: center;
        font-size: 0.7rem;
        color: rgba(255,255,255,0.3);
        flex-shrink: 0;
        background: rgba(0,0,0,0.2);
    }
    `;

    const style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);

    // ── Guide Content ───────────────────────────────────────────────────
    const guideHTML = `
    <div class="guide-section">
        <div class="guide-section-title"><span class="gs-icon">🏠</span> Landing Page</div>
        <div class="guide-desc">The homepage shows a live market overview with real-time event summaries, top bullish/bearish signals, and quick search to jump to any NSE Top 500 company.</div>
        <ul class="guide-features">
            <li>Search any company by name or NSE symbol in the top search bar</li>
            <li>Live market events refresh every 60 seconds</li>
            <li>Quick-access cards link directly to Dashboard, AI Chat, and Analysis</li>
        </ul>
    </div>

    <div class="guide-section">
        <div class="guide-section-title"><span class="gs-icon">📊</span> Live Dashboard</div>
        <div class="guide-desc">Real-time intelligence feed showing the latest market events detected by our AI pipeline — earnings, insider trades, regulatory actions, and more.</div>
        <ul class="guide-features">
            <li><strong>Market Clock</strong> — Shows IST time, session state (Pre-Open / Normal / Closing / Closed), and countdown to next session</li>
            <li><strong>Filter tabs</strong> — Switch between All / Positive / Negative / Neutral events</li>
            <li><strong>Event cards</strong> — Click any company name to open its full analysis page</li>
            <li>Data refreshes automatically every 20 seconds</li>
        </ul>
    </div>

    <div class="guide-section">
        <div class="guide-section-title"><span class="gs-icon">🏢</span> Company Analysis Hub</div>
        <div class="guide-desc">The most powerful page — comprehensive analysis for any company combining live charts, AI predictions, technical analysis, and news intelligence.</div>
        <ul class="guide-features">
            <li><strong>Prediction Meter</strong> — Bullish/Bearish gauge based on EMA trends, RSI, and candlestick patterns</li>
            <li><strong>Multi-Timeframe Rating</strong> — Stock ratings across 1 Day / 1 Week / 1 Month / 3 Months</li>
            <li><strong>News Impact Timeline</strong> — Recent events with sentiment tagging (Bullish/Bearish/Neutral)</li>
            <li><strong>Interactive Chart</strong> — Full TradingView chart with technical indicators</li>
            <li><strong>Fundamentals</strong> — Revenue, earnings, cash flow from TradingView</li>
            <li><strong>Technical Gauge</strong> — Moving averages, oscillators, and summary signal</li>
            <li><strong>Candlestick Patterns</strong> — 28 Steve Nison patterns with projected future candles</li>
            <li><strong>AI Intelligence</strong> — Bullish/bearish thesis with conviction score</li>
        </ul>
        <div class="guide-tip">💡 Tip: Use the search bar in the navigation to quickly switch between companies.</div>
    </div>

    <div class="guide-section">
        <div class="guide-section-title"><span class="gs-icon">🕯️</span> Candlestick Pattern Chart</div>
        <div class="guide-desc">Interactive canvas chart that detects 28 candlestick patterns from Steve Nison's methodology and projects future price movement.</div>
        <ul class="guide-features">
            <li><strong>Zoom</strong> — Use scroll wheel or ＋/－ buttons</li>
            <li><strong>Pan</strong> — Click and drag to scroll through time</li>
            <li><strong>Hover</strong> — See OHLCV data and detected patterns for any candle</li>
            <li><strong>🔮 Projected</strong> — Dashed candles show predicted future movement</li>
            <li><strong>Support/Resistance</strong> — Dotted lines show key price levels</li>
            <li>Select period: 3 Months / 6 Months / 1 Year / 2 Years</li>
        </ul>
    </div>

    <div class="guide-section">
        <div class="guide-section-title"><span class="gs-icon">📈</span> Stock Ratings</div>
        <div class="guide-desc">Multi-timeframe ratings computed from 5 technical signals — EMA trend, RSI momentum, candlestick patterns, volume trend, and rate of change.</div>
        <ul class="guide-features">
            <li><strong>5-Tier Scale</strong> — STRONG BUY → BUY → NEUTRAL → SELL → STRONG SELL</li>
            <li><strong>Score</strong> — Ranges from -10 (most bearish) to +10 (most bullish)</li>
            <li><strong>Key Factors</strong> — See exactly what's driving each rating</li>
            <li>Longer timeframes (1M, 3M) carry more weight in the overall consensus</li>
        </ul>
    </div>

    <div class="guide-section">
        <div class="guide-section-title"><span class="gs-icon">🤖</span> AI Chat</div>
        <div class="guide-desc">Ask questions about any Indian company in plain English. The AI retrieves relevant filings, news, and technical data to answer.</div>
        <ul class="guide-features">
            <li>Try: "What's happening with Reliance?"</li>
            <li>Try: "Compare TCS and Infosys recent news"</li>
            <li>Try: "Why is HDFC Bank falling?"</li>
            <li>Answers include source citations from NSE filings and news</li>
        </ul>
    </div>

    <div class="guide-section">
        <div class="guide-section-title"><span class="gs-icon">🟢</span> Bullish & <span style="color:#ef4444;">Bearish</span> Watchlists</div>
        <div class="guide-desc">Ranked lists of companies with the strongest bullish or bearish signals based on recent event analysis.</div>
        <ul class="guide-features">
            <li>Scores are computed from event sentiment, recency, type weights, and severity</li>
            <li>Click any company to see its full analysis page</li>
            <li>Updated every time the data pipeline runs</li>
        </ul>
    </div>

    <div class="guide-section">
        <div class="guide-section-title"><span class="gs-icon">🌐</span> 3D Market Map</div>
        <div class="guide-desc">Interactive 3D visualization of the market showing company relationships, sectors, and signal strength.</div>
    </div>

    <div class="guide-section">
        <div class="guide-section-title"><span class="gs-icon">🔍</span> Audit Trail</div>
        <div class="guide-desc">Full transparency log of every data ingestion, classification, and scoring action taken by the system. Verify the integrity of the intelligence pipeline.</div>
    </div>

    <div class="guide-divider"></div>

    <div class="guide-section">
        <div class="guide-section-title"><span class="gs-icon">⚠️</span> Important Disclaimer</div>
        <div class="guide-desc" style="color: rgba(245,158,11,0.8);">
            This platform is for <strong>educational and research purposes only</strong>. 
            Ratings, predictions, and signals reflect statistical tendencies from technical analysis — they are NOT guarantees of future performance. 
            This is NOT investment advice. Always consult a SEBI-registered investment adviser before making financial decisions.
        </div>
    </div>
    `;

    // ── Build DOM ───────────────────────────────────────────────────────

    function init() {
        // 1. Add trigger button to nav
        const navLinks = document.getElementById('nav-links');
        if (navLinks) {
            const li = document.createElement('li');
            const btn = document.createElement('button');
            btn.className = 'guide-trigger';
            btn.id = 'guide-trigger';
            btn.innerHTML = '<span class="guide-trigger-icon">📖</span> Guide';
            btn.setAttribute('aria-label', 'Open User Guide');
            li.appendChild(btn);
            navLinks.appendChild(li);
        }

        // 2. Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'guide-overlay';
        overlay.id = 'guide-overlay';
        document.body.appendChild(overlay);

        // 3. Create panel
        const panel = document.createElement('div');
        panel.className = 'guide-panel';
        panel.id = 'guide-panel';
        panel.setAttribute('role', 'dialog');
        panel.setAttribute('aria-label', 'User Guide');
        panel.innerHTML = `
            <div class="guide-header">
                <h2>📖 <span>User Guide</span></h2>
                <button class="guide-close" id="guide-close" aria-label="Close guide">✕</button>
            </div>
            <div class="guide-body">${guideHTML}</div>
            <div class="guide-footer">
                Bharat Market Intelligence Agent · Built with ❤️ for Indian Investors · v2.0
            </div>
        `;
        document.body.appendChild(panel);

        // 4. Event listeners
        const trigger = document.getElementById('guide-trigger');
        const closeBtn = document.getElementById('guide-close');

        function openGuide() {
            overlay.classList.add('active');
            panel.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeGuide() {
            overlay.classList.remove('active');
            panel.classList.remove('active');
            document.body.style.overflow = '';
        }

        if (trigger) trigger.addEventListener('click', openGuide);
        if (closeBtn) closeBtn.addEventListener('click', closeGuide);
        overlay.addEventListener('click', closeGuide);

        // ESC key closes
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && panel.classList.contains('active')) {
                closeGuide();
            }
        });
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
