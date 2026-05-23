/**
 * Bharat Market Intelligence Agent — Chat Page JavaScript
 *
 * Handles:
 * - Chat message sending/receiving
 * - Mode selection
 * - Suggested query buttons
 * - Thinking animation
 * - Citation rendering
 * - Auto-scrolling
 *
 * Security: All DOM via createElement/textContent (no innerHTML)
 */

(function () {
    'use strict';

    let currentMode = 'general_market';
    let isProcessing = false;

    const messagesContainer = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const suggestedContainer = document.getElementById('suggested-queries');

    // ============================================================
    // Mode Selection
    // ============================================================
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.getAttribute('data-mode');
        });
    });

    // ============================================================
    // Suggested Queries
    // ============================================================
    document.querySelectorAll('.suggested-query').forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.getAttribute('data-query');
            if (query && !isProcessing) {
                chatInput.value = query;
                sendMessage();
            }
        });
    });

    // ============================================================
    // Send Message
    // ============================================================
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message || isProcessing) return;

        isProcessing = true;
        chatSend.disabled = true;
        chatInput.value = '';

        // Hide suggestions after first message
        if (suggestedContainer) {
            suggestedContainer.style.display = 'none';
        }

        // Add user message
        addMessage('user', message);

        // Add thinking indicator
        const thinkingEl = addThinking();

        try {
            // Call API
            const response = await window.BharatAPI.chat(message, currentMode);

            // Remove thinking
            thinkingEl.remove();

            // Add assistant response
            addAssistantMessage(response);

        } catch (error) {
            thinkingEl.remove();

            // Fallback response
            addAssistantMessage({
                answer: 'I apologize, but I\'m unable to connect to the AI backend right now. ' +
                    'Please ensure the backend server is running on port 8000, or try again shortly.',
                citations: [],
                confidence: 'low',
                disclaimer: 'This is for informational purposes only. Not investment advice.',
                model_used: 'frontend_fallback',
                latency_ms: 0,
            });
        }

        isProcessing = false;
        chatSend.disabled = false;
        chatInput.focus();
    }

    // ============================================================
    // DOM Builders (XSS-safe — no innerHTML)
    // ============================================================
    function addMessage(role, text) {
        const msg = document.createElement('div');
        msg.className = 'msg ' + role;
        msg.textContent = text;
        messagesContainer.appendChild(msg);
        scrollToBottom();
        return msg;
    }

    function addThinking() {
        const msg = document.createElement('div');
        msg.className = 'msg thinking';

        const text = document.createElement('span');
        text.textContent = 'Analyzing sources ';

        const dots = document.createElement('span');
        dots.className = 'thinking-dots';
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dots.appendChild(dot);
        }

        msg.appendChild(text);
        msg.appendChild(dots);
        messagesContainer.appendChild(msg);
        scrollToBottom();
        return msg;
    }

    function addAssistantMessage(response) {
        const msg = document.createElement('div');
        msg.className = 'msg assistant';

        // Answer text — handle markdown-like formatting
        const answerLines = (response.answer || '').split('\n');
        answerLines.forEach((line, idx) => {
            if (line.trim() === '') {
                if (idx > 0) msg.appendChild(document.createElement('br'));
                return;
            }

            const p = document.createElement('p');
            p.style.margin = '4px 0';

            // Bold text: **text**
            if (line.includes('**')) {
                const parts = line.split('**');
                parts.forEach((part, i) => {
                    if (i % 2 === 1) {
                        const strong = document.createElement('strong');
                        strong.textContent = part;
                        p.appendChild(strong);
                    } else {
                        p.appendChild(document.createTextNode(part));
                    }
                });
            } else if (line.startsWith('• ') || line.startsWith('- ')) {
                p.style.paddingLeft = '16px';
                p.textContent = line;
            } else {
                p.textContent = line;
            }

            msg.appendChild(p);
        });

        // Citations
        if (response.citations && response.citations.length > 0) {
            const citationsDiv = document.createElement('div');
            citationsDiv.className = 'citations';

            response.citations.forEach((cite, idx) => {
                const citeItem = document.createElement('div');
                citeItem.className = 'citation-item';

                const num = document.createElement('span');
                num.className = 'cite-num';
                num.textContent = '📎 [' + (idx + 1) + ']';

                const text = document.createElement('span');
                const parts = [cite.source || 'Source'];
                if (cite.published_at) parts.push(cite.published_at.slice(0, 10));
                text.textContent = parts.join(' — ');

                citeItem.appendChild(num);
                citeItem.appendChild(text);
                citationsDiv.appendChild(citeItem);
            });

            msg.appendChild(citationsDiv);
        }

        // Meta row
        const meta = document.createElement('div');
        meta.className = 'msg-meta';

        if (response.model_used) {
            const model = document.createElement('span');
            model.textContent = '🤖 ' + response.model_used;
            meta.appendChild(model);
        }

        if (response.latency_ms) {
            const latency = document.createElement('span');
            latency.textContent = '⚡ ' + response.latency_ms + 'ms';
            meta.appendChild(latency);
        }

        if (response.confidence) {
            const conf = document.createElement('span');
            conf.textContent = '📊 ' + response.confidence + ' confidence';
            meta.appendChild(conf);
        }

        if (response.cached) {
            const cached = document.createElement('span');
            cached.textContent = '💾 cached';
            cached.style.color = 'var(--color-positive)';
            meta.appendChild(cached);
        }

        msg.appendChild(meta);

        // Disclaimer
        if (response.disclaimer) {
            const disclaimer = document.createElement('span');
            disclaimer.className = 'disclaimer-text';
            disclaimer.textContent = '⚖️ ' + response.disclaimer;
            msg.appendChild(disclaimer);
        }

        messagesContainer.appendChild(msg);
        scrollToBottom();
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // ============================================================
    // Event Listeners
    // ============================================================
    chatSend.addEventListener('click', sendMessage);

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });

    // Nav toggle
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
    }

})();
