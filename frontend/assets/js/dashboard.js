/**
 * Bharat Market Intelligence Agent — Dashboard JavaScript
 *
 * Renders the live intelligence dashboard.
 * Tries to fetch from backend API first, falls back to demo data.
 * All DOM manipulation uses createElement/textContent (XSS-safe).
 */

(function () {
    'use strict';

    // ============================================================
    // NSE Market Clock
    // ============================================================
    const NSE_HOLIDAYS_2026 = [
        '2026-01-26', '2026-03-10', '2026-03-17', '2026-03-30',
        '2026-03-31', '2026-04-01', '2026-04-03', '2026-04-14',
        '2026-05-01', '2026-06-25', '2026-07-07', '2026-08-15',
        '2026-08-28', '2026-10-02', '2026-10-20', '2026-10-21',
        '2026-10-23', '2026-11-04', '2026-11-16', '2026-12-25',
    ];

    function getISTDate() {
        // Convert current UTC time to IST (UTC+5:30)
        const now = new Date();
        const utc = now.getTime() + now.getTimezoneOffset() * 60000;
        return new Date(utc + 5.5 * 3600000);
    }

    function isNSEHoliday(istDate) {
        const dateStr = istDate.getFullYear() + '-' +
            String(istDate.getMonth() + 1).padStart(2, '0') + '-' +
            String(istDate.getDate()).padStart(2, '0');
        return NSE_HOLIDAYS_2026.indexOf(dateStr) !== -1;
    }

    function getMarketSession(istDate) {
        const day = istDate.getDay();
        const hours = istDate.getHours();
        const minutes = istDate.getMinutes();
        const totalMinutes = hours * 60 + minutes;

        // Weekend check
        if (day === 0 || day === 6) {
            return { session: 'closed', reason: 'Weekend' };
        }

        // Holiday check
        if (isNSEHoliday(istDate)) {
            return { session: 'closed', reason: 'Market Holiday' };
        }

        // Pre-open: 9:00 - 9:15
        if (totalMinutes >= 540 && totalMinutes < 555) {
            return { session: 'preopen', reason: 'Pre-Open Session (9:00 – 9:15 AM)' };
        }

        // Normal trading: 9:15 - 15:30
        if (totalMinutes >= 555 && totalMinutes < 930) {
            return { session: 'live', reason: 'Normal Trading Session (9:15 AM – 3:30 PM)' };
        }

        // Closing session: 15:30 - 15:40
        if (totalMinutes >= 930 && totalMinutes < 940) {
            return { session: 'closing', reason: 'Closing Session (3:30 – 3:40 PM)' };
        }

        // Before market
        if (totalMinutes < 540) {
            return { session: 'closed', reason: 'Market opens at 9:00 AM IST' };
        }

        // After market
        return { session: 'closed', reason: 'Market closed for today' };
    }

    function getCountdown(istDate, session) {
        const hours = istDate.getHours();
        const minutes = istDate.getMinutes();
        const seconds = istDate.getSeconds();
        const totalSeconds = hours * 3600 + minutes * 60 + seconds;

        let targetLabel = '';
        let targetSeconds = 0;

        if (session === 'preopen') {
            // Countdown to trading start (9:15)
            targetLabel = 'TRADING STARTS IN';
            targetSeconds = 9 * 3600 + 15 * 60 - totalSeconds;
        } else if (session === 'live') {
            // Countdown to market close (15:30)
            targetLabel = 'MARKET CLOSES IN';
            targetSeconds = 15 * 3600 + 30 * 60 - totalSeconds;
        } else if (session === 'closing') {
            // Countdown to session end (15:40)
            targetLabel = 'SESSION ENDS IN';
            targetSeconds = 15 * 3600 + 40 * 60 - totalSeconds;
        } else {
            // Find next open
            const day = istDate.getDay();
            if (totalSeconds < 9 * 3600 && day !== 0 && day !== 6 && !isNSEHoliday(istDate)) {
                // Today before market open
                targetLabel = 'MARKET OPENS IN';
                targetSeconds = 9 * 3600 - totalSeconds;
            } else {
                // After market close or weekend — show next trading day
                let daysUntilOpen = 1;
                if (day === 5) daysUntilOpen = 3; // Friday → Monday
                else if (day === 6) daysUntilOpen = 2; // Saturday → Monday
                // Note: holiday detection for future days would need iteration

                targetLabel = 'NEXT SESSION IN';
                targetSeconds = daysUntilOpen * 86400 - totalSeconds + 9 * 3600;
            }
        }

        if (targetSeconds < 0) targetSeconds = 0;

        const h = Math.floor(targetSeconds / 3600);
        const m = Math.floor((targetSeconds % 3600) / 60);
        const s = Math.floor(targetSeconds % 60);

        return {
            label: targetLabel,
            display: String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0'),
        };
    }

    function updateMarketClock() {
        const ist = getISTDate();
        const { session, reason } = getMarketSession(ist);
        const countdown = getCountdown(ist, session);

        // Time display
        const clockEl = document.getElementById('clock-digital');
        const dateEl = document.getElementById('clock-date');
        if (clockEl) {
            const h = String(ist.getHours()).padStart(2, '0');
            const m = String(ist.getMinutes()).padStart(2, '0');
            const s = String(ist.getSeconds()).padStart(2, '0');
            clockEl.textContent = h + ':' + m + ':' + s;
        }
        if (dateEl) {
            const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            dateEl.textContent = days[ist.getDay()] + ', ' +
                ist.getDate() + ' ' + months[ist.getMonth()] + ' ' +
                ist.getFullYear() + ' · IST';
        }

        // Status display
        const widget = document.getElementById('market-clock-widget');
        const dotEl = document.getElementById('market-status-dot');
        const labelEl = document.getElementById('market-status-label');
        const infoEl = document.getElementById('market-session-info');

        if (widget) {
            widget.className = 'market-clock-widget';
            if (session === 'live') widget.classList.add('market-open');
            else if (session === 'preopen') widget.classList.add('market-preopen');
            else if (session === 'closing') widget.classList.add('market-closing');
            else widget.classList.add('market-closed');
        }

        if (dotEl) {
            dotEl.className = 'market-status-dot';
            if (session === 'live') dotEl.classList.add('live');
            else if (session === 'preopen') dotEl.classList.add('preopen');
            else if (session === 'closing') dotEl.classList.add('closing');
            else dotEl.classList.add('closed');
        }

        if (labelEl) {
            labelEl.className = 'market-status-label';
            if (session === 'live') {
                labelEl.classList.add('live');
                labelEl.textContent = '● MARKET OPEN';
            } else if (session === 'preopen') {
                labelEl.classList.add('preopen');
                labelEl.textContent = '◐ PRE-OPEN';
            } else if (session === 'closing') {
                labelEl.classList.add('closing');
                labelEl.textContent = '◑ CLOSING SESSION';
            } else {
                labelEl.classList.add('closed');
                labelEl.textContent = '○ MARKET CLOSED';
            }
        }

        if (infoEl) {
            infoEl.textContent = reason;
        }

        // Countdown
        const countdownLabel = document.getElementById('countdown-label');
        const countdownTime = document.getElementById('countdown-time');
        if (countdownLabel) countdownLabel.textContent = countdown.label;
        if (countdownTime) {
            countdownTime.textContent = countdown.display;
            countdownTime.className = 'countdown-time';
            if (session === 'live') countdownTime.classList.add('live');
            else if (session === 'preopen') countdownTime.classList.add('preopen');
            else if (session === 'closing') countdownTime.classList.add('closing');
            else countdownTime.classList.add('closed');
        }
    }

    // Start the clock — runs every second
    updateMarketClock();
    setInterval(updateMarketClock, 1000);

    // ============================================================
    // Demo Data (used when backend is not connected)
    // ============================================================
    const DEMO_EVENTS = [
        { id: '1', company_symbol: 'TATAMOTORS', company_name: 'Tata Motors Ltd', event_type: 'earnings_commentary', event_title: 'Strong Q4 Results — JLR Margins Improve', event_summary: 'Tata Motors reported strong Q4 results with JLR margins improving to 8.5%. Domestic PV segment grew 12% YoY. EV portfolio expansion on track.', impact_label: 'positive', confidence_score: 0.87, severity: 'medium', detected_at: new Date().toISOString(), source_url: '#', citations: [], sentiment_label: 'bullish', source_tier: 1, source: 'bse_exchange' },
        { id: '2', company_symbol: 'HDFCBANK', company_name: 'HDFC Bank Ltd', event_type: 'rating_change', event_title: 'Outlook Upgraded to Positive by Moody\'s', event_summary: 'Credit rating agency upgraded HDFC Bank outlook to Positive citing strong asset quality and improved post-merger integration metrics.', impact_label: 'positive', confidence_score: 0.92, severity: 'high', detected_at: new Date(Date.now() - 720000).toISOString(), source_url: '#', citations: [], sentiment_label: 'bullish', source_tier: 1, source: 'nse_exchange' },
        { id: '3', company_symbol: 'RELIANCE', company_name: 'Reliance Industries Ltd', event_type: 'management_update', event_title: 'Retail Arm Restructuring Announced', event_summary: 'Reliance announced restructuring of retail arm with new subsidiary for quick commerce vertical.', impact_label: 'neutral', confidence_score: 0.78, severity: 'medium', detected_at: new Date(Date.now() - 1380000).toISOString(), source_url: '#', citations: [], sentiment_label: 'neutral', source_tier: 1, source: 'nse_exchange' },
        { id: '4', company_symbol: 'ADANIENT', company_name: 'Adani Enterprises Ltd', event_type: 'governance_concern', event_title: 'SEBI Scrutiny on Related-Party Transactions', event_summary: 'SEBI ordered investigation into related-party transactions across Adani Group entities. Multiple flags raised on governance compliance.', impact_label: 'negative', confidence_score: 0.84, severity: 'high', detected_at: new Date(Date.now() - 2280000).toISOString(), source_url: '#', citations: [], sentiment_label: 'bearish', source_tier: 1, source: 'bse_exchange' },
        { id: '5', company_symbol: 'TCS', company_name: 'Tata Consultancy Services Ltd', event_type: 'deal_win', event_title: 'Large Deal Win — $800M TCV', event_summary: 'TCS announced a large deal win with $800M total contract value in the financial services vertical in North America.', impact_label: 'positive', confidence_score: 0.91, severity: 'high', detected_at: new Date(Date.now() - 3600000).toISOString(), source_url: '#', citations: [], sentiment_label: 'bullish', source_tier: 3, source: 'moneycontrol' },
        { id: '6', company_symbol: 'SUNPHARMA', company_name: 'Sun Pharmaceutical Industries Ltd', event_type: 'regulatory_action', event_title: 'USFDA Form 483 — Halol Plant', event_summary: 'Sun Pharma received Form 483 observations at Halol manufacturing facility. Management committed to remediation timeline.', impact_label: 'negative', confidence_score: 0.82, severity: 'medium', detected_at: new Date(Date.now() - 5400000).toISOString(), source_url: '#', citations: [], sentiment_label: 'bearish', source_tier: 3, source: 'cnbc-tv18' },
        { id: '7', company_symbol: 'INFY', company_name: 'Infosys Ltd', event_type: 'guidance_revision', event_title: 'FY27 Revenue Guidance — 4-7% CC Growth', event_summary: 'Infosys revised FY27 revenue growth guidance to 4-7% in constant currency terms, narrowing from earlier 3-6% range.', impact_label: 'positive', confidence_score: 0.85, severity: 'medium', detected_at: new Date(Date.now() - 7200000).toISOString(), source_url: '#', citations: [], sentiment_label: 'bullish', source_tier: 1, source: 'nse_exchange' },
        { id: '8', company_symbol: 'COALINDIA', company_name: 'Coal India Ltd', event_type: 'production_update', event_title: 'Production Shortfall — Monsoon Impact', event_summary: 'Coal India reported 8% production shortfall in May due to early monsoon impact on open-cast mining operations.', impact_label: 'negative', confidence_score: 0.76, severity: 'low', detected_at: new Date(Date.now() - 10800000).toISOString(), source_url: '#', citations: [], sentiment_label: 'bearish', source_tier: 4, source: 'livemint' },
    ];

    const DEMO_SECTORS = [
        { sector: 'Financial Services', event_count: 12 },
        { sector: 'Information Technology', event_count: 9 },
        { sector: 'Energy', event_count: 7 },
        { sector: 'Automobile', event_count: 6 },
        { sector: 'Healthcare', event_count: 5 },
        { sector: 'Metals & Mining', event_count: 4 },
        { sector: 'FMCG', event_count: 3 },
        { sector: 'Construction', event_count: 2 },
    ];

    let currentFilter = 'all';
    let allEvents = [];
    let isConnected = false;

    // ============================================================
    // Format Helpers
    // ============================================================
    function formatRelativeTime(dateStr) {
        const now = Date.now();
        const then = new Date(dateStr).getTime();
        const seconds = Math.floor((now - then) / 1000);

        if (seconds < 60) return 'just now';
        if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
        if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
        return Math.floor(seconds / 86400) + 'd ago';
    }

    function formatConfidence(score) {
        if (!score) return 'N/A';
        return Math.round(score * 100) + '%';
    }

    // ============================================================
    // Render Functions
    // ============================================================
    function renderStats(events) {
        const grid = document.getElementById('dashboard-stats');
        if (!grid) return;
        grid.replaceChildren();

        const positive = events.filter(e => e.impact_label === 'positive').length;
        const negative = events.filter(e => e.impact_label === 'negative').length;
        const neutral = events.filter(e => e.impact_label === 'neutral').length;

        const stats = [
            { value: events.length, label: 'Total Events', color: 'var(--accent-primary)' },
            { value: positive, label: 'Positive Signals', color: 'var(--color-positive)' },
            { value: negative, label: 'Risk Events', color: 'var(--color-negative)' },
            { value: neutral, label: 'Neutral / Monitor', color: 'var(--color-neutral)' },
        ];

        stats.forEach(stat => {
            const card = document.createElement('div');
            card.className = 'glass-card stat-card';

            const value = document.createElement('div');
            value.className = 'stat-value';
            value.style.color = stat.color;
            value.textContent = stat.value;

            const label = document.createElement('div');
            label.className = 'stat-label';
            label.textContent = stat.label;

            card.appendChild(value);
            card.appendChild(label);
            grid.appendChild(card);
        });
    }

    function renderEvents(events) {
        const container = document.getElementById('events-list');
        if (!container) return;
        container.replaceChildren();

        const filtered = currentFilter === 'all'
            ? events
            : events.filter(e => e.impact_label === currentFilter);

        if (filtered.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'empty-state glass-card';
            const p = document.createElement('p');
            p.textContent = 'No events found for this filter.';
            empty.appendChild(p);
            container.appendChild(empty);
            return;
        }

        filtered.forEach(event => {
            const card = document.createElement('div');
            card.className = 'glass-card event-card';

            // Indicator
            const indicator = document.createElement('div');
            indicator.className = 'event-indicator ' + (event.impact_label || 'neutral');

            // Content
            const content = document.createElement('div');
            content.className = 'event-content';

            // Meta row
            const meta = document.createElement('div');
            meta.className = 'event-meta';

            const company = document.createElement('span');
            company.className = 'event-company';
            company.textContent = event.company_symbol || event.company_name || 'Unknown';

            // ── Sentiment Badge (📈 Bullish / 📉 Bearish) ──
            const sentiment = event.sentiment_label || 'neutral';
            const sentimentBadge = document.createElement('span');
            if (sentiment === 'bullish') {
                sentimentBadge.className = 'badge badge-positive';
                sentimentBadge.textContent = '📈 Bullish';
                sentimentBadge.style.fontWeight = '700';
            } else if (sentiment === 'bearish') {
                sentimentBadge.className = 'badge badge-negative';
                sentimentBadge.textContent = '📉 Bearish';
                sentimentBadge.style.fontWeight = '700';
            } else {
                sentimentBadge.className = 'badge badge-neutral';
                sentimentBadge.textContent = '➖ Neutral';
            }

            // ── Source Tier Badge (⚡L1, 📰L3, 📄L4) ──
            const tier = event.source_tier || 4;
            const tierBadge = document.createElement('span');
            tierBadge.className = 'badge';
            if (tier === 1) {
                tierBadge.textContent = '⚡ Exchange';
                tierBadge.style.cssText = 'background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); font-weight: 700;';
            } else if (tier === 3) {
                tierBadge.textContent = '📰 Aggregator';
                tierBadge.style.cssText = 'background: rgba(99, 102, 241, 0.1); color: #818cf8;';
            } else {
                tierBadge.textContent = '📄 News';
                tierBadge.style.cssText = 'background: var(--bg-glass); color: var(--text-muted);';
            }

            const badge = document.createElement('span');
            const impactClass = event.impact_label === 'positive' ? 'positive'
                : event.impact_label === 'negative' ? 'negative' : 'neutral';
            badge.className = 'badge badge-' + impactClass;
            badge.textContent = (event.event_type || '').replace(/_/g, ' ');

            const conf = document.createElement('span');
            conf.className = 'badge badge-warning';
            conf.textContent = formatConfidence(event.confidence_score);

            const time = document.createElement('span');
            time.className = 'event-time';
            time.textContent = formatRelativeTime(event.detected_at);

            meta.appendChild(company);
            meta.appendChild(sentimentBadge);
            meta.appendChild(tierBadge);
            meta.appendChild(badge);
            meta.appendChild(conf);
            meta.appendChild(time);

            // Title
            const title = document.createElement('div');
            title.className = 'event-title';
            title.textContent = event.event_title;

            // Summary
            const summary = document.createElement('p');
            summary.className = 'event-summary';
            summary.textContent = event.event_summary || '';

            // Source label
            const sourceLabel = document.createElement('div');
            sourceLabel.style.cssText = 'font-size: 0.7rem; color: var(--text-muted); margin-top: 4px;';
            const sourceName = (event.source || '').replace(/_/g, ' ');
            sourceLabel.textContent = 'Source: ' + (sourceName || 'Unknown') +
                (tier === 1 ? ' — Legally mandated first disclosure' : '');

            content.appendChild(meta);
            content.appendChild(title);
            content.appendChild(summary);
            content.appendChild(sourceLabel);

            card.appendChild(indicator);
            card.appendChild(content);
            container.appendChild(card);
        });
    }

    function renderSectors(sectors) {
        const container = document.getElementById('sector-bars');
        if (!container) return;
        container.replaceChildren();

        const maxCount = Math.max(...sectors.map(s => s.event_count), 1);

        sectors.forEach(sector => {
            const row = document.createElement('div');
            row.className = 'sector-bar';

            const name = document.createElement('span');
            name.className = 'sector-name';
            name.textContent = sector.sector;

            const barContainer = document.createElement('div');
            barContainer.style.cssText = 'flex: 1; height: 6px; background: var(--bg-glass); border-radius: 3px; overflow: hidden;';

            const fill = document.createElement('div');
            fill.className = 'sector-bar-fill';
            fill.style.width = Math.round((sector.event_count / maxCount) * 100) + '%';

            const count = document.createElement('span');
            count.className = 'sector-count';
            count.textContent = sector.event_count;

            barContainer.appendChild(fill);
            row.appendChild(name);
            row.appendChild(barContainer);
            row.appendChild(count);
            container.appendChild(row);
        });
    }

    function updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        const textEl = document.getElementById('status-text');
        if (!statusEl || !textEl) return;

        if (connected) {
            statusEl.className = 'connection-status connected';
            textEl.textContent = 'Live — Connected to Backend';
        } else {
            statusEl.className = 'connection-status disconnected';
            textEl.textContent = 'Demo Mode — Backend Not Connected';
        }
    }

    // ============================================================
    // Toast Notification Logic
    // ============================================================
    function showToast(event) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast';
        
        const title = (event.event_title || '').length > 60 
            ? event.event_title.substring(0, 60) + '...' 
            : event.event_title;

        toast.innerHTML = `
            <div class="toast-header">
                <span>⚡ Live Market Alert</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
            <div class="toast-title">${event.company_symbol || 'Market'}: ${title}</div>
            <div class="toast-time">Just now</div>
        `;

        container.appendChild(toast);

        // Slide in
        setTimeout(() => toast.classList.add('show'), 100);

        // Auto remove after 8 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        }, 8000);
    }

    // ============================================================
    // Data Loading & Auto-Refresh
    // ============================================================
    let isInitialLoad = true;

    async function loadData() {
        try {
            // Try fetching from backend
            const summary = await window.BharatAPI.getMarketSummary();
            const newEvents = summary.latest_events || [];

            if (newEvents.length === 0) {
                // Backend connected but no events — use demo
                allEvents = DEMO_EVENTS;
                isConnected = true;
            } else {
                isConnected = true;
                
                // Diff check: if not initial load, look for new events to trigger toasts
                if (!isInitialLoad && allEvents.length > 0) {
                    const existingIds = new Set(allEvents.map(e => e.id));
                    const newlyAdded = newEvents.filter(e => !existingIds.has(e.id));
                    
                    if (newlyAdded.length > 0) {
                        // Show toast for up to 3 newest events to avoid spam
                        newlyAdded.slice(0, 3).forEach((e, idx) => {
                            setTimeout(() => showToast(e), idx * 800);
                        });
                    }
                }
                allEvents = newEvents;
            }

            renderStats(allEvents);
            renderEvents(allEvents);
            renderSectors(summary.top_sectors || DEMO_SECTORS);
            updateConnectionStatus(true);
            isInitialLoad = false;

        } catch (error) {
            // Backend not available — use demo data
            allEvents = DEMO_EVENTS;
            isConnected = false;

            renderStats(allEvents);
            renderEvents(allEvents);
            renderSectors(DEMO_SECTORS);
            updateConnectionStatus(false);
        }
    }

    // ============================================================
    // Filter Controls
    // ============================================================
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.getAttribute('data-filter');
            renderEvents(allEvents);
        });
    });

    // ============================================================
    // Navigation Toggle
    // ============================================================
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
        });
    }

    // ============================================================
    // Initialize
    // ============================================================
    loadData();

    // Auto-refresh every 20 seconds for near real-time updates
    setInterval(loadData, 20000);

})();
