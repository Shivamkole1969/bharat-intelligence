/**
 * Bharat Market Intelligence Agent — Audit Page JavaScript
 *
 * Loads system health, pipeline stats, chain verification,
 * and recent audit logs.
 *
 * Security: All DOM via createElement/textContent (no innerHTML)
 */

(function () {
    'use strict';

    const API_BASE = window.BharatAPI ? window.BharatAPI.BASE_URL : 'http://127.0.0.1:8000/api';

    // Demo data for when backend is offline
    const DEMO_HEALTH = {
        overall_status: 'degraded',
        database: { status: 'healthy', latency_ms: 12 },
        redis: { status: 'not_configured' },
        kafka: { status: 'not_configured' },
        llm_providers: {
            groq: { status: 'configured', model: 'llama-3.1-70b-versatile' },
            openai: { status: 'not_configured' },
            ollama: { status: 'not_reachable' },
        },
        data_freshness: {
            status: 'no_data',
            documents_last_24h: 0,
            events_last_24h: 0,
        },
    };

    const DEMO_STATS = {
        documents: { total: 0, chunks: 0, embedded: 0, embedding_coverage: 0 },
        events: { total: 0, by_type: {}, by_impact: {} },
    };

    const DEMO_CHAIN = {
        status: 'empty',
        total_entries: 0,
        verified: 0,
        broken_count: 0,
    };

    // ============================================================
    // Health Cards
    // ============================================================
    function renderHealth(data) {
        const grid = document.getElementById('health-grid');
        if (!grid) return;
        grid.replaceChildren();

        const cards = [
            { label: 'Overall Status', value: data.overall_status || '—', cls: data.overall_status === 'healthy' ? 'positive' : 'warning' },
            { label: 'Database', value: data.database?.status || '—', sub: data.database?.latency_ms ? data.database.latency_ms + 'ms' : '', cls: data.database?.status === 'healthy' ? 'positive' : 'negative' },
            { label: 'Data Freshness', value: data.data_freshness?.status || '—', sub: data.data_freshness?.data_age_hours ? data.data_freshness.data_age_hours + 'h old' : '', cls: data.data_freshness?.status === 'fresh' ? 'positive' : data.data_freshness?.status === 'stale' ? 'warning' : 'neutral' },
            { label: 'LLM (Groq)', value: data.llm_providers?.groq?.status || '—', cls: data.llm_providers?.groq?.status === 'configured' ? 'positive' : 'neutral' },
            { label: 'LLM (Ollama)', value: data.llm_providers?.ollama?.status || '—', cls: data.llm_providers?.ollama?.status === 'healthy' ? 'positive' : 'neutral' },
            { label: 'Redis', value: data.redis?.status || '—', cls: data.redis?.status === 'healthy' ? 'positive' : 'neutral' },
        ];

        cards.forEach(c => {
            const card = document.createElement('div');
            card.className = 'glass-card';

            const num = document.createElement('div');
            num.className = 'stat-number ' + c.cls;
            num.textContent = c.value;

            const label = document.createElement('div');
            label.className = 'stat-label';
            label.textContent = c.label;

            card.appendChild(num);
            if (c.sub) {
                const sub = document.createElement('div');
                sub.className = 'stat-label';
                sub.textContent = c.sub;
                card.appendChild(sub);
            }
            card.appendChild(label);
            grid.appendChild(card);
        });
    }

    // ============================================================
    // Pipeline Stats
    // ============================================================
    function renderStats(data) {
        const grid = document.getElementById('stats-grid');
        if (!grid) return;
        grid.replaceChildren();

        const docs = data.documents || {};
        const events = data.events || {};

        const cards = [
            { label: 'Total Documents', value: docs.total || 0, cls: 'neutral' },
            { label: 'Document Chunks', value: docs.chunks || 0, cls: 'neutral' },
            { label: 'Embedded Chunks', value: docs.embedded || 0, cls: docs.embedding_coverage > 80 ? 'positive' : 'warning' },
            { label: 'Embedding Coverage', value: (docs.embedding_coverage || 0) + '%', cls: docs.embedding_coverage > 80 ? 'positive' : 'warning' },
            { label: 'Total Events', value: events.total || 0, cls: 'neutral' },
            { label: 'Docs (24h)', value: data.data_freshness?.documents_last_24h || 0, cls: 'neutral' },
        ];

        cards.forEach(c => {
            const card = document.createElement('div');
            card.className = 'glass-card';

            const num = document.createElement('div');
            num.className = 'stat-number ' + c.cls;
            num.textContent = c.value;

            const label = document.createElement('div');
            label.className = 'stat-label';
            label.textContent = c.label;

            card.appendChild(num);
            card.appendChild(label);
            grid.appendChild(card);
        });
    }

    // ============================================================
    // Chain Verification
    // ============================================================
    function renderChain(data) {
        const container = document.getElementById('chain-verify');
        if (!container) return;
        container.replaceChildren();

        const badge = document.createElement('span');
        badge.className = 'chain-badge ' + (data.status === 'valid' || data.status === 'empty' ? 'valid' : 'invalid');

        if (data.status === 'valid') {
            badge.textContent = '✅ Chain Valid — ' + data.verified + ' entries verified';
        } else if (data.status === 'empty') {
            badge.textContent = 'ℹ️ No audit entries yet';
        } else {
            badge.textContent = '❌ Integrity Violation — ' + data.broken_count + ' broken links';
        }

        container.appendChild(badge);

        if (data.checked_at) {
            const time = document.createElement('p');
            time.style.cssText = 'color: var(--text-muted); font-size: 0.78rem; margin-top: 8px;';
            time.textContent = 'Checked at: ' + data.checked_at;
            container.appendChild(time);
        }
    }

    // ============================================================
    // Audit Log Table
    // ============================================================
    function renderAuditLogs(data) {
        const tbody = document.getElementById('audit-tbody');
        if (!tbody) return;
        tbody.replaceChildren();

        const entries = data.entries || [];
        if (entries.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 5;
            cell.style.textAlign = 'center';
            cell.style.color = 'var(--text-muted)';
            cell.textContent = 'No audit entries yet. Run the ingestion pipeline to generate entries.';
            row.appendChild(cell);
            tbody.appendChild(row);
            return;
        }

        entries.forEach(e => {
            const row = document.createElement('tr');

            const tdTime = document.createElement('td');
            tdTime.textContent = e.created_at ? e.created_at.slice(0, 19).replace('T', ' ') : '—';

            const tdActor = document.createElement('td');
            tdActor.textContent = (e.actor_type || '—') + (e.actor_id ? '/' + e.actor_id : '');

            const tdAction = document.createElement('td');
            tdAction.textContent = e.action || '—';

            const tdEntity = document.createElement('td');
            tdEntity.textContent = (e.entity_type || '') + (e.entity_id ? '#' + e.entity_id.slice(0, 8) : '');

            const tdHash = document.createElement('td');
            tdHash.style.fontFamily = 'var(--font-mono)';
            tdHash.style.fontSize = '0.72rem';
            tdHash.textContent = e.current_hash || '—';

            row.appendChild(tdTime);
            row.appendChild(tdActor);
            row.appendChild(tdAction);
            row.appendChild(tdEntity);
            row.appendChild(tdHash);
            tbody.appendChild(row);
        });
    }

    // ============================================================
    // Load All Data
    // ============================================================
    async function loadAll() {
        // Health
        try {
            const health = await fetch(API_BASE + '/health/deep').then(r => r.json());
            renderHealth(health);
        } catch { renderHealth(DEMO_HEALTH); }

        // Stats
        try {
            const stats = await fetch(API_BASE + '/admin/stats').then(r => r.json());
            renderStats(stats);
        } catch { renderStats(DEMO_STATS); }

        // Chain
        try {
            const chain = await fetch(API_BASE + '/audit/verify').then(r => r.json());
            renderChain(chain);
        } catch { renderChain(DEMO_CHAIN); }

        // Logs
        try {
            const logs = await fetch(API_BASE + '/audit/logs?limit=20').then(r => r.json());
            renderAuditLogs(logs);
        } catch { renderAuditLogs({ entries: [] }); }
    }

    // Nav toggle
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
    }

    loadAll();

})();
