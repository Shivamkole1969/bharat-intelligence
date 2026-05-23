/**
 * Bharat Market Intelligence Agent — Global Search Autocomplete
 * 
 * Fetches company list from the backend API on first focus,
 * then provides Google Finance style autocomplete with keyboard navigation.
 */

(function () {
    'use strict';

    // Company cache — populated on first search focus from API
    let ALL_COMPANIES = [];
    let companiesFetched = false;
    let fetchingCompanies = false;

    /**
     * Fetch the full company list from the backend API.
     * Falls back to a static list if the API is unreachable.
     */
    async function fetchCompanies() {
        if (companiesFetched || fetchingCompanies) return;
        fetchingCompanies = true;

        try {
            const API_BASE = window.BharatAPI ? window.BharatAPI.BASE_URL : (
                (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
                    ? 'http://127.0.0.1:8000/api' : '/api'
            );
            const response = await fetch(`${API_BASE}/companies?limit=500&is_active=true`);
            if (response.ok) {
                const data = await response.json();
                const companies = data.companies || data;
                if (Array.isArray(companies) && companies.length > 0) {
                    ALL_COMPANIES = companies.map(c => ({
                        symbol: c.symbol || c.nse_symbol,
                        name: c.company_name,
                        sector: c.sector || ''
                    }));
                    companiesFetched = true;
                    return;
                }
            }
        } catch (e) {
            console.log('Company API not reachable, using fallback list');
        }

        // Fallback: static top 50 if API fails
        if (ALL_COMPANIES.length === 0) {
            ALL_COMPANIES = FALLBACK_COMPANIES;
            companiesFetched = true;
        }
        fetchingCompanies = false;
    }

    // Static fallback list (top 50 only, used if API is unreachable)
    const FALLBACK_COMPANIES = [
        { symbol: "RELIANCE", name: "Reliance Industries Ltd", sector: "Energy" },
        { symbol: "TCS", name: "Tata Consultancy Services Ltd", sector: "IT" },
        { symbol: "HDFCBANK", name: "HDFC Bank Ltd", sector: "Financial Services" },
        { symbol: "ICICIBANK", name: "ICICI Bank Ltd", sector: "Financial Services" },
        { symbol: "INFY", name: "Infosys Ltd", sector: "IT" },
        { symbol: "SBIN", name: "State Bank of India", sector: "Financial Services" },
        { symbol: "BHARTIARTL", name: "Bharti Airtel Ltd", sector: "Telecom" },
        { symbol: "ITC", name: "ITC Ltd", sector: "FMCG" },
        { symbol: "HINDUNILVR", name: "Hindustan Unilever Ltd", sector: "FMCG" },
        { symbol: "LT", name: "Larsen & Toubro Ltd", sector: "Construction" },
        { symbol: "BAJFINANCE", name: "Bajaj Finance Ltd", sector: "Financial Services" },
        { symbol: "HCLTECH", name: "HCL Technologies Ltd", sector: "IT" },
        { symbol: "MARUTI", name: "Maruti Suzuki India Ltd", sector: "Automobile" },
        { symbol: "SUNPHARMA", name: "Sun Pharmaceutical Industries Ltd", sector: "Healthcare" },
        { symbol: "TATAMOTORS", name: "Tata Motors Ltd", sector: "Automobile" },
        { symbol: "KOTAKBANK", name: "Kotak Mahindra Bank Ltd", sector: "Financial Services" },
        { symbol: "AXISBANK", name: "Axis Bank Ltd", sector: "Financial Services" },
        { symbol: "ONGC", name: "Oil and Natural Gas Corporation Ltd", sector: "Energy" },
        { symbol: "NTPC", name: "NTPC Ltd", sector: "Energy" },
        { symbol: "TITAN", name: "Titan Company Ltd", sector: "Consumer Durables" },
        { symbol: "TATASTEEL", name: "Tata Steel Ltd", sector: "Metals & Mining" },
        { symbol: "ADANIENT", name: "Adani Enterprises Ltd", sector: "Conglomerate" },
        { symbol: "WIPRO", name: "Wipro Ltd", sector: "IT" },
        { symbol: "NESTLEIND", name: "Nestle India Ltd", sector: "FMCG" },
        { symbol: "TECHM", name: "Tech Mahindra Ltd", sector: "IT" },
        { symbol: "PNB", name: "Punjab National Bank", sector: "Financial Services" },
        { symbol: "BANKBARODA", name: "Bank of Baroda", sector: "Financial Services" },
        { symbol: "YESBANK", name: "Yes Bank Ltd", sector: "Financial Services" },
        { symbol: "ZOMATO", name: "Zomato Ltd", sector: "Consumer Services" },
        { symbol: "PAYTM", name: "One97 Communications Ltd", sector: "IT" },
        { symbol: "NYKAA", name: "FSN E-Commerce Ventures Ltd", sector: "Consumer Services" },
        { symbol: "TRENT", name: "Trent Ltd", sector: "Consumer Durables" },
        { symbol: "BHEL", name: "Bharat Heavy Electricals Ltd", sector: "Capital Goods" },
        { symbol: "HAL", name: "Hindustan Aeronautics Ltd", sector: "Defence" },
        { symbol: "IRCTC", name: "Indian Railway Catering And Tourism Corporation Ltd", sector: "Consumer Services" },
        { symbol: "RVNL", name: "Rail Vikas Nigam Ltd", sector: "Infrastructure" },
        { symbol: "SUZLON", name: "Suzlon Energy Ltd", sector: "Energy" },
        { symbol: "IDEA", name: "Vodafone Idea Ltd", sector: "Telecom" },
        { symbol: "TATAPOWER", name: "Tata Power Company Ltd", sector: "Energy" },
        { symbol: "VEDL", name: "Vedanta Ltd", sector: "Metals & Mining" },
        { symbol: "IOC", name: "Indian Oil Corporation Ltd", sector: "Energy" },
        { symbol: "INDIGO", name: "InterGlobe Aviation Ltd", sector: "Consumer Services" },
        { symbol: "BEL", name: "Bharat Electronics Ltd", sector: "Defence" },
        { symbol: "DLF", name: "DLF Ltd", sector: "Real Estate" },
        { symbol: "CIPLA", name: "Cipla Ltd", sector: "Healthcare" },
        { symbol: "DRREDDY", name: "Dr. Reddy's Laboratories Ltd", sector: "Healthcare" },
        { symbol: "DMART", name: "Avenue Supermarts Ltd", sector: "Consumer Services" },
        { symbol: "COALINDIA", name: "Coal India Ltd", sector: "Metals & Mining" },
        { symbol: "JIOFIN", name: "Jio Financial Services Ltd", sector: "Financial Services" },
        { symbol: "INDHOTEL", name: "Indian Hotels Company Ltd", sector: "Consumer Services" },
    ];

    function initAutocomplete() {
        const searchForms = document.querySelectorAll('.nav-search');

        searchForms.forEach(form => {
            const input = form.querySelector('input[name="symbol"]');
            if (!input) return;

            // Create wrapper if not exists
            if (!input.parentElement.classList.contains('autocomplete-wrapper')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'autocomplete-wrapper';
                wrapper.style.position = 'relative';
                wrapper.style.flex = '1';
                wrapper.style.display = 'flex';
                wrapper.style.alignItems = 'center';
                input.parentNode.insertBefore(wrapper, input);
                wrapper.appendChild(input);
            }

            const wrapper = input.parentElement;

            // Create dropdown element
            let dropdown = wrapper.querySelector('.autocomplete-dropdown');
            if (!dropdown) {
                dropdown = document.createElement('div');
                dropdown.className = 'autocomplete-dropdown';
                dropdown.style.display = 'none';
                wrapper.appendChild(dropdown);
            }

            let currentFocus = -1;

            // Fetch companies on first focus
            input.addEventListener('focus', async function () {
                if (!companiesFetched) {
                    await fetchCompanies();
                }
                if (this.value && dropdown.children.length > 0) {
                    dropdown.style.display = 'block';
                }
            });

            // Input listener
            input.addEventListener('input', async function () {
                const val = this.value;
                dropdown.innerHTML = '';
                currentFocus = -1;

                if (!val) {
                    dropdown.style.display = 'none';
                    return;
                }

                // Ensure companies are loaded
                if (!companiesFetched) {
                    await fetchCompanies();
                }

                const valLower = val.toLowerCase();
                const matches = ALL_COMPANIES.filter(company =>
                    company.symbol.toLowerCase().includes(valLower) ||
                    company.name.toLowerCase().includes(valLower)
                );

                // Sort: exact symbol prefix first, then by symbol length (shorter = more relevant)
                matches.sort((a, b) => {
                    const aStartsWith = a.symbol.toLowerCase().startsWith(valLower) ? 0 : 1;
                    const bStartsWith = b.symbol.toLowerCase().startsWith(valLower) ? 0 : 1;
                    if (aStartsWith !== bStartsWith) return aStartsWith - bStartsWith;
                    return a.symbol.length - b.symbol.length;
                });

                if (matches.length > 0) {
                    dropdown.style.display = 'block';
                    matches.slice(0, 10).forEach(match => {
                        const item = document.createElement('div');
                        item.className = 'autocomplete-item';

                        // Highlight matching text
                        const escapedVal = val.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        const regex = new RegExp(`(${escapedVal})`, "gi");
                        const highlightedSymbol = match.symbol.replace(regex, "<span class='highlight'>$1</span>");
                        const highlightedName = match.name.replace(regex, "<span class='highlight'>$1</span>");

                        const sectorTag = match.sector
                            ? `<span class="ac-sector">${match.sector}</span>`
                            : '';

                        item.innerHTML = `<span class="ac-symbol">${highlightedSymbol}</span> <span class="ac-name">${highlightedName}</span>${sectorTag}`;

                        item.addEventListener('click', function (e) {
                            input.value = match.symbol;
                            dropdown.style.display = 'none';
                            form.submit();
                        });

                        dropdown.appendChild(item);
                    });
                } else {
                    dropdown.style.display = 'none';
                }
            });

            // Keyboard navigation
            input.addEventListener('keydown', function (e) {
                const items = dropdown.querySelectorAll('.autocomplete-item');
                if (items.length === 0 || dropdown.style.display === 'none') return;

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    currentFocus++;
                    addActive(items);
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    currentFocus--;
                    addActive(items);
                } else if (e.key === 'Enter') {
                    if (currentFocus > -1) {
                        e.preventDefault();
                        items[currentFocus].click();
                    }
                }
            });

            function addActive(items) {
                if (!items) return;
                removeActive(items);
                if (currentFocus >= items.length) currentFocus = 0;
                if (currentFocus < 0) currentFocus = items.length - 1;
                items[currentFocus].classList.add('active');
            }

            function removeActive(items) {
                items.forEach(item => item.classList.remove('active'));
            }

            // Close dropdown if clicked outside
            document.addEventListener('click', function (e) {
                if (e.target !== input && e.target !== dropdown && !dropdown.contains(e.target)) {
                    dropdown.style.display = 'none';
                }
            });

            // Re-open if clicked inside and has value
            input.addEventListener('focus', function () {
                if (this.value && dropdown.children.length > 0) {
                    dropdown.style.display = 'block';
                }
            });
        });
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAutocomplete);
    } else {
        initAutocomplete();
    }

})();
