/**
 * Bharat Market Intelligence Agent — Landing Page JavaScript
 *
 * Renders:
 * - 3D particle network animation on hero canvas
 * - Live event ticker with sample data
 * - Sample event cards
 * - Stats, features, data sources, trust grid
 * - AI chat demo interaction
 *
 * Security: All DOM content inserted via textContent/createElement (no innerHTML).
 */

(function () {
    'use strict';

    // ============================================================
    // 3D Particle Network — Hero Canvas Animation
    // ============================================================
    const canvas = document.getElementById('hero-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let particles = [];
        let animationId;
        const PARTICLE_COUNT = 80;
        const CONNECTION_DISTANCE = 150;
        const MOUSE = { x: -9999, y: -9999 };

        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }

        function createParticles() {
            particles = [];
            for (let i = 0; i < PARTICLE_COUNT; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: (Math.random() - 0.5) * 0.5,
                    radius: Math.random() * 2 + 1,
                    color: i % 5 === 0
                        ? 'rgba(245, 158, 11, 0.8)'  // saffron accent
                        : i % 7 === 0
                            ? 'rgba(59, 130, 246, 0.7)' // blue accent
                            : 'rgba(148, 163, 184, 0.4)', // neutral
                    pulsePhase: Math.random() * Math.PI * 2,
                    pulseSpeed: 0.01 + Math.random() * 0.02,
                });
            }
        }

        function drawParticles() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw connections
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < CONNECTION_DISTANCE) {
                        const alpha = (1 - dist / CONNECTION_DISTANCE) * 0.15;
                        ctx.beginPath();
                        ctx.strokeStyle = `rgba(245, 158, 11, ${alpha})`;
                        ctx.lineWidth = 0.5;
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            }

            // Draw particles
            for (const p of particles) {
                p.pulsePhase += p.pulseSpeed;
                const pulse = 1 + Math.sin(p.pulsePhase) * 0.3;
                const r = p.radius * pulse;

                // Glow effect
                ctx.beginPath();
                ctx.arc(p.x, p.y, r * 3, 0, Math.PI * 2);
                ctx.fillStyle = p.color.replace(/[\d.]+\)/, '0.05)');
                ctx.fill();

                // Core
                ctx.beginPath();
                ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.fill();

                // Mouse repulsion
                const mdx = p.x - MOUSE.x;
                const mdy = p.y - MOUSE.y;
                const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
                if (mdist < 200) {
                    const force = (200 - mdist) / 200 * 0.02;
                    p.vx += (mdx / mdist) * force;
                    p.vy += (mdy / mdist) * force;
                }

                // Update position
                p.x += p.vx;
                p.y += p.vy;

                // Damping
                p.vx *= 0.999;
                p.vy *= 0.999;

                // Wrap around
                if (p.x < 0) p.x = canvas.width;
                if (p.x > canvas.width) p.x = 0;
                if (p.y < 0) p.y = canvas.height;
                if (p.y > canvas.height) p.y = 0;
            }

            animationId = requestAnimationFrame(drawParticles);
        }

        resizeCanvas();
        createParticles();
        drawParticles();

        window.addEventListener('resize', () => {
            resizeCanvas();
            createParticles();
        });

        canvas.addEventListener('mousemove', (e) => {
            MOUSE.x = e.clientX;
            MOUSE.y = e.clientY;
        });

        canvas.addEventListener('mouseleave', () => {
            MOUSE.x = -9999;
            MOUSE.y = -9999;
        });
    }

    // ============================================================
    // Navigation Toggle (Mobile)
    // ============================================================
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
        });
    }

    // ============================================================
    // Sample Data — Demo Events
    // ============================================================
    const DEMO_EVENTS = [
        {
            company: 'Tata Motors',
            symbol: 'TATAMOTORS',
            type: 'Earnings Commentary',
            impact: 'positive',
            severity: 'Medium',
            confidence: 87,
            time: '5 minutes ago',
            source: 'BSE Announcement',
            summary: 'Tata Motors reported strong Q4 results with JLR margins improving to 8.5%. Management commentary highlighted robust order book and EV transition progress.',
            whyMatters: 'Margin expansion and improving product mix signal sustainable profitability improvement in premium segment.'
        },
        {
            company: 'HDFC Bank',
            symbol: 'HDFCBANK',
            type: 'Rating Change',
            impact: 'positive',
            severity: 'High',
            confidence: 92,
            time: '12 minutes ago',
            source: 'News / Rating Agency',
            summary: 'Credit rating agency upgraded HDFC Bank outlook to "Positive" citing strong asset quality and improved post-merger integration metrics.',
            whyMatters: 'Rating upgrade signals reduced risk perception and may attract institutional flows.'
        },
        {
            company: 'Reliance Industries',
            symbol: 'RELIANCE',
            type: 'Management Update',
            impact: 'neutral',
            severity: 'Medium',
            confidence: 78,
            time: '23 minutes ago',
            source: 'Exchange Filing',
            summary: 'Reliance announced restructuring of retail arm with new subsidiary formation for quick commerce vertical.',
            whyMatters: 'Structural reorganization may unlock value but execution risk remains.'
        },
        {
            company: 'Adani Enterprises',
            symbol: 'ADANIENT',
            type: 'Governance Concern',
            impact: 'negative',
            severity: 'High',
            confidence: 84,
            time: '38 minutes ago',
            source: 'News Reports',
            summary: 'Multiple news outlets reported regulatory scrutiny on related-party transactions across Adani Group entities.',
            whyMatters: 'Governance concerns may increase risk premium and affect institutional holdings.'
        },
    ];

    const TICKER_ITEMS = [
        { company: 'TCS', event: 'Board Meeting Outcome — Q1 Results', impact: 'positive' },
        { company: 'INFY', event: 'Guidance Revision — FY27 Revenue', impact: 'neutral' },
        { company: 'SBIN', event: 'Asset Quality Improvement — NPA Down 15bps', impact: 'positive' },
        { company: 'TATASTEEL', event: 'Capacity Expansion — 5MT Greenfield', impact: 'positive' },
        { company: 'SUNPHARMA', event: 'USFDA Observation — Form 483', impact: 'negative' },
        { company: 'BAJFINANCE', event: 'AUM Growth — 32% YoY', impact: 'positive' },
        { company: 'ITC', event: 'Demerger Update — Hotels Listing Date', impact: 'neutral' },
        { company: 'MARUTI', event: 'Monthly Sales — Record Export Volume', impact: 'positive' },
        { company: 'WIPRO', event: 'Large Deal Win — $500M TCV', impact: 'positive' },
        { company: 'COALINDIA', event: 'Production Shortfall — Monsoon Impact', impact: 'negative' },
    ];

    // ============================================================
    // Render Event Ticker
    // ============================================================
    function renderTicker() {
        const track = document.getElementById('ticker-track');
        if (!track) return;

        // Clear existing content safely
        track.replaceChildren();

        // Double the items for seamless infinite scroll
        const allItems = [...TICKER_ITEMS, ...TICKER_ITEMS];

        allItems.forEach(item => {
            const div = document.createElement('div');
            div.className = 'ticker-item';

            const dot = document.createElement('span');
            dot.style.width = '6px';
            dot.style.height = '6px';
            dot.style.borderRadius = '50%';
            dot.style.background = item.impact === 'positive'
                ? 'var(--color-positive)'
                : item.impact === 'negative'
                    ? 'var(--color-negative)'
                    : 'var(--color-neutral)';

            const companySpan = document.createElement('span');
            companySpan.className = 'company';
            companySpan.textContent = item.company;

            const eventSpan = document.createElement('span');
            eventSpan.textContent = item.event;
            eventSpan.style.color = 'var(--text-secondary)';

            div.appendChild(dot);
            div.appendChild(companySpan);
            div.appendChild(eventSpan);
            track.appendChild(div);
        });
    }

    // ============================================================
    // Render Sample Event Cards
    // ============================================================
    function renderEventCards() {
        const container = document.getElementById('sample-events');
        if (!container) return;
        container.replaceChildren();

        DEMO_EVENTS.forEach((event, idx) => {
            const card = document.createElement('div');
            card.className = 'glass-card event-card animate-fade-in-up animate-delay-' + (idx + 1);

            // Indicator bar
            const indicator = document.createElement('div');
            indicator.className = 'event-indicator ' + event.impact;

            // Content
            const content = document.createElement('div');
            content.className = 'event-content';

            // Meta row
            const meta = document.createElement('div');
            meta.className = 'event-meta';

            const companyEl = document.createElement('span');
            companyEl.className = 'event-company';
            companyEl.textContent = event.company;

            const badge = document.createElement('span');
            badge.className = 'badge badge-' + (event.impact === 'positive' ? 'positive' : event.impact === 'negative' ? 'negative' : 'neutral');
            badge.textContent = event.type;

            const confidence = document.createElement('span');
            confidence.className = 'badge badge-warning';
            confidence.textContent = event.confidence + '% conf.';

            const time = document.createElement('span');
            time.className = 'event-time';
            time.textContent = event.time;

            meta.appendChild(companyEl);
            meta.appendChild(badge);
            meta.appendChild(confidence);
            meta.appendChild(time);

            // Summary
            const summary = document.createElement('p');
            summary.className = 'event-summary';
            summary.textContent = event.summary;

            // Why it matters
            const why = document.createElement('p');
            why.style.cssText = 'font-size: 0.82rem; color: var(--accent-primary); margin-top: 8px; font-weight: 500;';
            why.textContent = '💡 ' + event.whyMatters;

            // Source
            const source = document.createElement('p');
            source.style.cssText = 'font-size: 0.75rem; color: var(--text-muted); margin-top: 6px;';
            source.textContent = '📎 Source: ' + event.source;

            content.appendChild(meta);
            content.appendChild(summary);
            content.appendChild(why);
            content.appendChild(source);

            card.appendChild(indicator);
            card.appendChild(content);
            container.appendChild(card);
        });
    }

    // ============================================================
    // Render Stats
    // ============================================================
    function renderStats() {
        const grid = document.getElementById('stats-grid');
        if (!grid) return;
        grid.replaceChildren();

        const stats = [
            { value: '50+', label: 'Companies Tracked', color: 'var(--accent-primary)' },
            { value: '10', label: 'Data Sources', color: 'var(--accent-secondary)' },
            { value: '9', label: 'AI Agents', color: 'var(--accent-tertiary)' },
            { value: '24/7', label: 'Live Monitoring', color: 'var(--color-positive)' },
        ];

        stats.forEach((stat, i) => {
            const card = document.createElement('div');
            card.className = 'glass-card stat-card animate-fade-in-up animate-delay-' + (i + 1);

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

    // ============================================================
    // Render Features Grid
    // ============================================================
    function renderFeatures() {
        const grid = document.getElementById('features-grid');
        if (!grid) return;
        grid.replaceChildren();

        const features = [
            { icon: '📡', title: 'Real-Time Ingestion', desc: 'Streaming data from BSE, NSE, news, filings, and transcripts via Redpanda/Kafka topics.' },
            { icon: '🤖', title: 'Multi-Agent Pipeline', desc: '9 LangGraph agents for classification, impact analysis, citation verification, and compliance.' },
            { icon: '💬', title: 'AI Chatbot', desc: '8-mode chatbot with Groq LLM routing, local fallback, semantic cache, and source-only mode.' },
            { icon: '📊', title: 'Signal Watchlists', desc: 'Bullish & bearish signal candidates scored daily with thesis, risks, and citations.' },
            { icon: '🔒', title: 'Compliance Layer', desc: 'Financial guardrails block unsafe advice. Safe labels. Always-on disclaimers.' },
            { icon: '📝', title: 'Audit Trail', desc: 'Append-only audit logs with SHA-256 hash chaining for tamper-evident record keeping.' },
            { icon: '📈', title: 'Observability', desc: 'Langfuse traces, Prometheus metrics, Grafana dashboards, and Evidently drift monitoring.' },
            { icon: '🚀', title: 'Production-Ready', desc: 'Docker Compose + Kubernetes, CI/CD with eval gates, auto-scaling architecture.' },
        ];

        features.forEach((f, i) => {
            const card = document.createElement('div');
            card.className = 'glass-card animate-fade-in-up animate-delay-' + ((i % 5) + 1);

            const icon = document.createElement('div');
            icon.className = 'feature-icon';
            icon.textContent = f.icon;

            const title = document.createElement('div');
            title.className = 'feature-title';
            title.textContent = f.title;

            const desc = document.createElement('div');
            desc.className = 'feature-desc';
            desc.textContent = f.desc;

            card.appendChild(icon);
            card.appendChild(title);
            card.appendChild(desc);
            grid.appendChild(card);
        });
    }

    // ============================================================
    // Render Data Sources
    // ============================================================
    function renderSources() {
        const grid = document.getElementById('sources-grid');
        if (!grid) return;
        grid.replaceChildren();

        const sources = [
            'BSE India', 'NSE India', 'RBI', 'SEBI',
            'MoneyControl', 'Economic Times', 'LiveMint',
            'Company IR Pages', 'Earnings Transcripts', 'Yahoo Finance (Demo)',
        ];

        sources.forEach(s => {
            const tag = document.createElement('div');
            tag.className = 'source-tag';

            const dot = document.createElement('span');
            dot.className = 'dot';

            const text = document.createElement('span');
            text.textContent = s;

            tag.appendChild(dot);
            tag.appendChild(text);
            grid.appendChild(tag);
        });
    }

    // ============================================================
    // Render Trust Grid
    // ============================================================
    function renderTrust() {
        const grid = document.getElementById('trust-grid');
        if (!grid) return;
        grid.replaceChildren();

        const items = [
            { icon: '🔍', title: 'Source Citations', desc: 'Every AI-generated insight links back to the original source document, URL, and timestamp.' },
            { icon: '🛡️', title: 'Compliance Guardrails', desc: 'Built-in filters prevent financial advice, buy/sell calls, and unsafe recommendations.' },
            { icon: '📋', title: 'Evaluation Pipeline', desc: 'DeepEval + RAGAS + Promptfoo continuously test faithfulness, hallucination, and safety.' },
        ];

        items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'glass-card trust-card';

            const icon = document.createElement('div');
            icon.className = 'trust-icon';
            icon.textContent = item.icon;

            const title = document.createElement('div');
            title.className = 'trust-title';
            title.textContent = item.title;

            const desc = document.createElement('div');
            desc.className = 'trust-desc';
            desc.textContent = item.desc;

            card.appendChild(icon);
            card.appendChild(title);
            card.appendChild(desc);
            grid.appendChild(card);
        });
    }

    // ============================================================
    // AI Chat Demo
    // ============================================================
    const DEMO_CONVERSATIONS = [
        {
            user: 'What happened with Tata Motors this week?',
            assistant: 'Tata Motors reported strong Q4 FY26 results. JLR (Jaguar Land Rover) margins improved to 8.5%, driven by favorable product mix and cost optimization. Domestic PV segment grew 12% YoY with strong SUV demand. EV portfolio expansion on track with Curvv and Harrier EV launches planned.',
            citation: '📎 Sources: BSE Filing (22 May 2026), Earnings Call Transcript (21 May 2026), MoneyControl (22 May 2026) | Confidence: High',
        },
        {
            user: 'Which sectors have the most negative events today?',
            assistant: 'Based on today\'s detected events:\n\n1. Metals & Mining — 3 negative events (commodity price pressure, margin warnings)\n2. IT Services — 2 negative events (guidance caution, deal pipeline slowdown)\n3. Energy — 1 negative event (regulatory hearing)\n\nThese are based on publicly available announcements and news. Please verify independently.',
            citation: '📎 Sources: BSE/NSE Announcements, News Aggregation | Confidence: Medium',
        },
    ];

    function renderChatDemo() {
        const container = document.getElementById('demo-messages');
        if (!container) return;
        container.replaceChildren();

        const firstConvo = DEMO_CONVERSATIONS[0];

        // User message
        const userMsg = document.createElement('div');
        userMsg.className = 'demo-msg user';
        userMsg.textContent = firstConvo.user;
        container.appendChild(userMsg);

        // Assistant message
        const assistantMsg = document.createElement('div');
        assistantMsg.className = 'demo-msg assistant';

        const answerText = document.createElement('span');
        answerText.textContent = firstConvo.assistant;

        const citation = document.createElement('span');
        citation.className = 'citation';
        citation.textContent = firstConvo.citation;

        assistantMsg.appendChild(answerText);
        assistantMsg.appendChild(citation);
        container.appendChild(assistantMsg);
    }

    // Demo input handler
    const demoInput = document.getElementById('demo-input');
    const demoSend = document.getElementById('demo-send');

    function handleDemoSend() {
        if (!demoInput || !demoInput.value.trim()) return;
        const container = document.getElementById('demo-messages');
        if (!container) return;

        const query = demoInput.value.trim();
        demoInput.value = '';

        // Add user message
        const userMsg = document.createElement('div');
        userMsg.className = 'demo-msg user';
        userMsg.textContent = query;
        container.appendChild(userMsg);

        // Simulate thinking
        const thinking = document.createElement('div');
        thinking.className = 'demo-msg assistant';
        thinking.textContent = '🔍 Searching market intelligence...';
        thinking.style.opacity = '0.6';
        container.appendChild(thinking);
        container.scrollTop = container.scrollHeight;

        // Simulate response
        setTimeout(() => {
            thinking.remove();

            const convo = DEMO_CONVERSATIONS[1] || DEMO_CONVERSATIONS[0];
            const assistantMsg = document.createElement('div');
            assistantMsg.className = 'demo-msg assistant';

            const answerText = document.createElement('span');
            answerText.textContent = 'This is a demo preview. In the full version, the AI analyst would provide a source-cited answer based on real-time market data, company filings, and news analysis. Connect to the backend to enable live responses.';

            const citation = document.createElement('span');
            citation.className = 'citation';
            citation.textContent = '📎 Demo mode — connect backend for live intelligence | Confidence: N/A';

            assistantMsg.appendChild(answerText);
            assistantMsg.appendChild(citation);
            container.appendChild(assistantMsg);
            container.scrollTop = container.scrollHeight;
        }, 1500);
    }

    if (demoSend) {
        demoSend.addEventListener('click', handleDemoSend);
    }
    if (demoInput) {
        demoInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') handleDemoSend();
        });
    }

    // ============================================================
    // Scroll Animations (Intersection Observer)
    // ============================================================
    function setupScrollAnimations() {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            },
            { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
        );

        document.querySelectorAll('.animate-fade-in-up').forEach(el => {
            observer.observe(el);
        });
    }

    // ============================================================
    // Initialize (Demo Data — immediate)
    // ============================================================
    renderTicker();
    renderEventCards();
    renderStats();
    renderFeatures();
    renderSources();
    renderTrust();
    renderChatDemo();

    // Delay scroll animations to avoid interfering with initial load
    setTimeout(setupScrollAnimations, 300);

    // ============================================================
    // Live Data Overlay — Replace demo with real events if available
    // ============================================================
    function formatRelativeTime(dateStr) {
        const now = Date.now();
        const then = new Date(dateStr).getTime();
        const seconds = Math.floor((now - then) / 1000);
        if (seconds < 60) return 'just now';
        if (seconds < 3600) return Math.floor(seconds / 60) + ' min ago';
        if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
        return Math.floor(seconds / 86400) + 'd ago';
    }

    async function fetchLiveData() {
        if (!window.BharatAPI) return;

        try {
            const summary = await window.BharatAPI.getMarketSummary();
            const liveEvents = summary.latest_events || [];

            if (liveEvents.length === 0) return; // Keep demo data

            // ── Update ticker with live events ──
            const track = document.getElementById('ticker-track');
            if (track && liveEvents.length > 0) {
                track.replaceChildren();

                // Build ticker items from live events (doubled for scroll)
                const tickerData = liveEvents.map(function (e) {
                    return {
                        company: e.company_symbol || e.company_name || 'Market',
                        event: (e.event_title || '').substring(0, 60),
                        impact: e.impact_label || 'neutral',
                    };
                });
                const allItems = tickerData.concat(tickerData);

                allItems.forEach(function (item) {
                    var div = document.createElement('div');
                    div.className = 'ticker-item';

                    var dot = document.createElement('span');
                    dot.style.width = '6px';
                    dot.style.height = '6px';
                    dot.style.borderRadius = '50%';
                    dot.style.flexShrink = '0';
                    dot.style.background = item.impact === 'positive'
                        ? 'var(--color-positive)'
                        : item.impact === 'negative'
                            ? 'var(--color-negative)'
                            : 'var(--color-neutral)';

                    var companySpan = document.createElement('span');
                    companySpan.className = 'company';
                    companySpan.textContent = item.company;

                    var eventSpan = document.createElement('span');
                    eventSpan.textContent = item.event;
                    eventSpan.style.color = 'var(--text-secondary)';

                    div.appendChild(dot);
                    div.appendChild(companySpan);
                    div.appendChild(eventSpan);
                    track.appendChild(div);
                });
            }

            // ── Update event cards with live events ──
            var container = document.getElementById('sample-events');
            if (container && liveEvents.length > 0) {
                container.replaceChildren();

                // Show up to 4 events
                var eventsToShow = liveEvents.slice(0, 4);
                eventsToShow.forEach(function (event, idx) {
                    var card = document.createElement('div');
                    card.className = 'glass-card event-card animate-fade-in-up animate-delay-' + (idx + 1);

                    var indicator = document.createElement('div');
                    indicator.className = 'event-indicator ' + (event.impact_label || 'neutral');

                    var content = document.createElement('div');
                    content.className = 'event-content';

                    // Meta row
                    var meta = document.createElement('div');
                    meta.className = 'event-meta';

                    var companyEl = document.createElement('span');
                    companyEl.className = 'event-company';
                    companyEl.textContent = event.company_symbol || event.company_name || 'Market';

                    var badge = document.createElement('span');
                    var impactClass = event.impact_label === 'positive' ? 'positive'
                        : event.impact_label === 'negative' ? 'negative' : 'neutral';
                    badge.className = 'badge badge-' + impactClass;
                    badge.textContent = (event.event_type || 'event').replace(/_/g, ' ');

                    var confidence = document.createElement('span');
                    confidence.className = 'badge badge-warning';
                    confidence.textContent = event.confidence_score
                        ? Math.round(event.confidence_score * 100) + '% conf.'
                        : 'N/A';

                    var time = document.createElement('span');
                    time.className = 'event-time';
                    time.textContent = event.detected_at
                        ? formatRelativeTime(event.detected_at)
                        : 'recently';

                    meta.appendChild(companyEl);
                    meta.appendChild(badge);
                    meta.appendChild(confidence);
                    meta.appendChild(time);

                    // Title
                    var titleEl = document.createElement('div');
                    titleEl.className = 'event-title';
                    titleEl.style.cssText = 'font-weight: 600; font-size: 0.95rem; margin-bottom: 6px; color: var(--text-primary);';
                    titleEl.textContent = event.event_title || '';

                    // Summary
                    var summaryEl = document.createElement('p');
                    summaryEl.className = 'event-summary';
                    summaryEl.textContent = event.event_summary || '';

                    // Source tier badge
                    var sourceEl = document.createElement('p');
                    sourceEl.style.cssText = 'font-size: 0.75rem; color: var(--text-muted); margin-top: 6px;';
                    var tier = event.source_tier || 4;
                    var tierLabel = tier === 1 ? '⚡ Exchange Filing'
                        : tier === 3 ? '📰 Aggregator'
                        : '📄 News';
                    sourceEl.textContent = '📎 Source: ' + tierLabel;

                    content.appendChild(meta);
                    content.appendChild(titleEl);
                    content.appendChild(summaryEl);
                    content.appendChild(sourceEl);

                    card.appendChild(indicator);
                    card.appendChild(content);
                    container.appendChild(card);
                });
            }

            // ── Update stats with live counts ──
            var statsGrid = document.getElementById('stats-grid');
            if (statsGrid) {
                statsGrid.replaceChildren();
                var liveStats = [
                    { value: summary.total_events_today || '0', label: 'Events Today', color: 'var(--accent-primary)' },
                    { value: summary.positive_events || '0', label: 'Positive Signals', color: 'var(--color-positive)' },
                    { value: summary.negative_events || '0', label: 'Risk Events', color: 'var(--color-negative)' },
                    { value: '24/7', label: 'Live Monitoring', color: 'var(--accent-secondary)' },
                ];
                liveStats.forEach(function (stat) {
                    var card = document.createElement('div');
                    card.className = 'glass-card stat-card';
                    var value = document.createElement('div');
                    value.className = 'stat-value';
                    value.style.color = stat.color;
                    value.textContent = stat.value;
                    var label = document.createElement('div');
                    label.className = 'stat-label';
                    label.textContent = stat.label;
                    card.appendChild(value);
                    card.appendChild(label);
                    statsGrid.appendChild(card);
                });
            }

        } catch (err) {
            // Backend not available — keep demo data (already rendered)
        }
    }

    // Fetch live data on load (non-blocking — demo shows immediately)
    fetchLiveData();

    // Auto-refresh live data every 60 seconds
    setInterval(fetchLiveData, 60000);

})();
