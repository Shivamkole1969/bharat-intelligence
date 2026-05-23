/**
 * Bharat Market Intelligence — API Key Manager
 * 
 * Allows users to add their own API keys (GROQ, OpenAI, etc.)
 * and select models. Keys are stored in localStorage (never sent to third parties).
 */

(function () {
    'use strict';

    // ── Provider Configurations ────────────────────────────────────
    const PROVIDERS = {
        groq: {
            name: 'GROQ',
            icon: '⚡',
            models: [
                { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B (Versatile)', default: true },
                { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B (Fast)' },
                { id: 'llama-3.2-90b-vision-preview', name: 'Llama 3.2 90B Vision' },
                { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B' },
                { id: 'gemma2-9b-it', name: 'Gemma 2 9B' },
            ],
            placeholder: 'gsk_...',
            validatePrefix: 'gsk_',
        },
        openai: {
            name: 'OpenAI',
            icon: '🧠',
            models: [
                { id: 'gpt-4o', name: 'GPT-4o', default: true },
                { id: 'gpt-4o-mini', name: 'GPT-4o Mini (Faster)' },
                { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
                { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo (Budget)' },
            ],
            placeholder: 'sk-...',
            validatePrefix: 'sk-',
        },
        anthropic: {
            name: 'Anthropic',
            icon: '🔮',
            models: [
                { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', default: true },
                { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku (Fast)' },
            ],
            placeholder: 'sk-ant-...',
            validatePrefix: 'sk-ant-',
        },
        gemini: {
            name: 'Google Gemini',
            icon: '💎',
            models: [
                { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', default: true },
                { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro' },
                { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash' },
            ],
            placeholder: 'AIza...',
            validatePrefix: '',
        },
    };

    const STORAGE_KEY = 'bharat_api_config';

    // ── State ──────────────────────────────────────────────────────

    function getConfig() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
        } catch {
            return {};
        }
    }

    function saveConfig(config) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
        updateButtonState();
        // Dispatch event for other scripts to react
        window.dispatchEvent(new CustomEvent('bharat-api-config-changed', { detail: config }));
    }

    // ── Build the UI ───────────────────────────────────────────────

    function createButton() {
        const config = getConfig();
        const hasKey = config.provider && config.apiKey;

        const btn = document.createElement('button');
        btn.className = 'api-key-btn' + (hasKey ? ' has-key' : '');
        btn.id = 'api-key-toggle';
        btn.innerHTML = `<span class="key-icon">🔑</span> ${hasKey ? config.provider.toUpperCase() : 'API Key'}`;
        btn.title = hasKey ? `Connected: ${PROVIDERS[config.provider]?.name || config.provider}` : 'Add your API key';
        btn.addEventListener('click', openModal);
        return btn;
    }

    function createModal() {
        const config = getConfig();

        const overlay = document.createElement('div');
        overlay.className = 'api-modal-overlay';
        overlay.id = 'api-modal-overlay';

        // Build provider options
        let providerOpts = '<option value="">— Select Provider —</option>';
        for (const [key, prov] of Object.entries(PROVIDERS)) {
            const sel = config.provider === key ? ' selected' : '';
            providerOpts += `<option value="${key}"${sel}>${prov.icon} ${prov.name}</option>`;
        }

        // Build model options based on selected provider
        let modelOpts = '<option value="">Select provider first</option>';
        if (config.provider && PROVIDERS[config.provider]) {
            modelOpts = '';
            for (const m of PROVIDERS[config.provider].models) {
                const sel = (config.model === m.id || (!config.model && m.default)) ? ' selected' : '';
                modelOpts += `<option value="${m.id}"${sel}>${m.name}</option>`;
            }
        }

        const maskedKey = config.apiKey
            ? config.apiKey.substring(0, 6) + '•'.repeat(Math.max(0, config.apiKey.length - 10)) + config.apiKey.slice(-4)
            : '';

        overlay.innerHTML = `
            <div class="api-modal">
                <div class="api-modal-header">
                    <h3>🔑 API Configuration</h3>
                    <button class="api-modal-close" id="api-modal-close">✕</button>
                </div>

                <div class="api-field">
                    <label>AI Provider</label>
                    <select id="api-provider">${providerOpts}</select>
                </div>

                <div class="api-field">
                    <label>API Key</label>
                    <input type="password" id="api-key-input"
                           placeholder="${config.provider ? PROVIDERS[config.provider]?.placeholder || 'Enter API key' : 'Select provider first'}"
                           value="${config.apiKey || ''}"
                           autocomplete="off" spellcheck="false">
                </div>

                <div class="api-field">
                    <label>Model</label>
                    <select id="api-model">${modelOpts}</select>
                </div>

                <button class="api-save-btn" id="api-save-btn">Save Configuration</button>

                ${config.apiKey ? '<button class="api-save-btn" id="api-clear-btn" style="background: rgba(239,68,68,0.15); color: #ef4444; margin-top: 8px;">Clear API Key</button>' : ''}

                <p class="api-status ${config.apiKey ? 'connected' : ''}" id="api-status-text">
                    ${config.apiKey ? `✓ Connected to ${PROVIDERS[config.provider]?.name || 'API'}` : 'Keys are stored locally in your browser — never sent to third parties.'}
                </p>
            </div>
        `;

        // Event handlers
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal();
        });

        document.body.appendChild(overlay);

        // Wire up events after DOM insertion
        document.getElementById('api-modal-close').addEventListener('click', closeModal);
        document.getElementById('api-save-btn').addEventListener('click', handleSave);

        const clearBtn = document.getElementById('api-clear-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                saveConfig({});
                closeModal();
                openModal(); // Reopen with cleared state
            });
        }

        // Provider change → update models + placeholder
        document.getElementById('api-provider').addEventListener('change', (e) => {
            const provider = e.target.value;
            const modelSelect = document.getElementById('api-model');
            const keyInput = document.getElementById('api-key-input');

            if (provider && PROVIDERS[provider]) {
                const prov = PROVIDERS[provider];
                keyInput.placeholder = prov.placeholder;
                modelSelect.innerHTML = prov.models.map(m =>
                    `<option value="${m.id}" ${m.default ? 'selected' : ''}>${m.name}</option>`
                ).join('');
            } else {
                keyInput.placeholder = 'Select provider first';
                modelSelect.innerHTML = '<option value="">Select provider first</option>';
            }
        });

        return overlay;
    }

    function openModal() {
        let overlay = document.getElementById('api-modal-overlay');
        if (overlay) overlay.remove();
        overlay = createModal();
        // Trigger animation
        requestAnimationFrame(() => {
            requestAnimationFrame(() => overlay.classList.add('active'));
        });
    }

    function closeModal() {
        const overlay = document.getElementById('api-modal-overlay');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => overlay.remove(), 250);
        }
    }

    function handleSave() {
        const provider = document.getElementById('api-provider').value;
        const apiKey = document.getElementById('api-key-input').value.trim();
        const model = document.getElementById('api-model').value;
        const statusEl = document.getElementById('api-status-text');

        if (!provider) {
            statusEl.textContent = '⚠️ Please select a provider';
            statusEl.className = 'api-status';
            return;
        }

        if (!apiKey) {
            statusEl.textContent = '⚠️ Please enter your API key';
            statusEl.className = 'api-status';
            return;
        }

        // Basic validation
        const prov = PROVIDERS[provider];
        if (prov.validatePrefix && !apiKey.startsWith(prov.validatePrefix)) {
            statusEl.textContent = `⚠️ ${prov.name} keys typically start with "${prov.validatePrefix}"`;
            statusEl.className = 'api-status';
            return;
        }

        saveConfig({ provider, apiKey, model: model || prov.models[0]?.id });

        statusEl.textContent = `✓ Saved! Connected to ${prov.name}`;
        statusEl.className = 'api-status connected';

        setTimeout(closeModal, 800);
    }

    function updateButtonState() {
        const btn = document.getElementById('api-key-toggle');
        if (!btn) return;

        const config = getConfig();
        const hasKey = config.provider && config.apiKey;

        btn.className = 'api-key-btn' + (hasKey ? ' has-key' : '');
        btn.innerHTML = `<span class="key-icon">🔑</span> ${hasKey ? (PROVIDERS[config.provider]?.name || config.provider.toUpperCase()) : 'API Key'}`;
    }

    // ── Inject into nav ────────────────────────────────────────────

    function init() {
        // Find the nav-inner to add the button
        const navInner = document.querySelector('.nav-inner');
        if (!navInner) return;

        const btn = createButton();

        // Insert before the nav toggle
        const navToggle = document.getElementById('nav-toggle');
        if (navToggle) {
            navInner.insertBefore(btn, navToggle);
        } else {
            navInner.appendChild(btn);
        }
    }

    // Expose API config getter globally
    window.BharatAPIConfig = {
        getConfig,
        getProvider: () => getConfig().provider || null,
        getApiKey: () => getConfig().apiKey || null,
        getModel: () => getConfig().model || null,
        hasKey: () => {
            const c = getConfig();
            return !!(c.provider && c.apiKey);
        },
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
