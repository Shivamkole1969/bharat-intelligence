/**
 * Bharat Market Intelligence Agent — API Client
 *
 * Centralized HTTP client for backend communication.
 * All requests go through this module for consistent error handling.
 */

(function () {
    'use strict';

    const API_BASE = (() => {
        // 1. Check for configured backend URL (set in HTML meta tag for deployment)
        const meta = document.querySelector('meta[name="api-base"]');
        if (meta && meta.content) return meta.content;
        // 2. Local dev
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
            return 'http://127.0.0.1:8000/api';
        // 3. Same-origin (Docker nginx proxy)
        return '/api';
    })();

    /**
     * Make an API request with error handling.
     * @param {string} endpoint - API path (e.g., '/companies')
     * @param {object} options - Fetch options
     * @returns {Promise<object>} Response data
     */
    async function apiRequest(endpoint, options = {}) {
        const url = API_BASE + endpoint;

        const defaultHeaders = {
            'Content-Type': 'application/json',
        };

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
                throw new Error('Backend unavailable. Please ensure the server is running.');
            }
            throw error;
        }
    }

    // Public API methods
    window.BharatAPI = {
        // Health
        health: () => apiRequest('/health'),

        // Companies
        listCompanies: (params = {}) => {
            const query = new URLSearchParams(params).toString();
            return apiRequest('/companies' + (query ? '?' + query : ''));
        },
        getCompany: (symbol) => apiRequest('/companies/' + encodeURIComponent(symbol)),
        getSectors: () => apiRequest('/companies/sectors'),

        // Events
        getLatestEvents: (params = {}) => {
            const query = new URLSearchParams(params).toString();
            return apiRequest('/events/latest' + (query ? '?' + query : ''));
        },
        getCompanyEvents: (symbol, params = {}) => {
            const query = new URLSearchParams(params).toString();
            return apiRequest('/events/company/' + encodeURIComponent(symbol) + (query ? '?' + query : ''));
        },
        getSectorEvents: (sector, params = {}) => {
            const query = new URLSearchParams(params).toString();
            return apiRequest('/events/sector/' + encodeURIComponent(sector) + (query ? '?' + query : ''));
        },
        getMarketSummary: () => apiRequest('/events/summary'),

        // Signals
        getTopBullish: (limit = 10) => apiRequest('/signals/bullish/top?limit=' + limit),
        getTopBearish: (limit = 10) => apiRequest('/signals/bearish/top?limit=' + limit),
        getThesis: (symbol) => apiRequest('/signals/thesis/' + encodeURIComponent(symbol)),

        // Chat — passes user API key config if available
        chat: (message, mode = 'general_market', companySymbol = null) => {
            const body = {
                message: message,
                mode: mode,
            };
            if (companySymbol) {
                body.company_symbol = companySymbol;
            }
            // Attach user API key config if available
            if (window.BharatAPIConfig && window.BharatAPIConfig.hasKey()) {
                body.user_api_config = {
                    provider: window.BharatAPIConfig.getProvider(),
                    api_key: window.BharatAPIConfig.getApiKey(),
                    model: window.BharatAPIConfig.getModel(),
                };
            }
            return apiRequest('/chat', {
                method: 'POST',
                body: JSON.stringify(body),
            });
        },

        // Admin
        triggerIngestion: (fetchBse = true, fetchNews = true) =>
            apiRequest('/admin/ingest/trigger?fetch_bse=' + fetchBse + '&fetch_news=' + fetchNews, { method: 'POST' }),
        getStats: () => apiRequest('/admin/stats'),
        classifyBatch: (limit = 100) =>
            apiRequest('/admin/classify/batch?limit=' + limit, { method: 'POST' }),

        // Observability
        getMetrics: () => apiRequest('/metrics/json'),
        deepHealth: () => apiRequest('/health/deep'),
        verifyAuditChain: () => apiRequest('/audit/verify'),
        getAuditLogs: (params = {}) => {
            const query = new URLSearchParams(params).toString();
            return apiRequest('/audit/logs' + (query ? '?' + query : ''));
        },

        // Candlestick Pattern Analysis
        getCandlestickAnalysis: (symbol, params = {}) => {
            const query = new URLSearchParams(params).toString();
            return apiRequest('/candlestick/' + encodeURIComponent(symbol) + (query ? '?' + query : ''));
        },

        // Multi-Timeframe Stock Rating
        getStockRating: (symbol, params = {}) => {
            const query = new URLSearchParams(params).toString();
            return apiRequest('/candlestick/' + encodeURIComponent(symbol) + '/rating' + (query ? '?' + query : ''));
        },

        // Expose base URL
        BASE_URL: API_BASE,
    };

})();
