/**
 * Bharat Market Intelligence Agent — 3D Market Map Visualization
 *
 * Canvas-based interactive sector bubble map:
 * - Bubble size = event density / company count
 * - Color = net sentiment (green=bullish, red=bearish)
 * - Hover tooltip with details
 * - Floating animation with parallax
 *
 * Security: All DOM via createElement/textContent (no innerHTML)
 */

(function () {
    'use strict';

    const canvas = document.getElementById('map-canvas');
    const ctx = canvas.getContext('2d');
    const tooltip = document.getElementById('map-tooltip');

    // Sector demo data — replaced by API data when available
    const SECTORS = [
        { name: 'Information Technology', companies: 25, events: 42, bullish: 7.8, bearish: 2.5, color: '#10b981' },
        { name: 'Financial Services', companies: 60, events: 65, bullish: 7.2, bearish: 3.1, color: '#10b981' },
        { name: 'Energy', companies: 28, events: 35, bullish: 5.5, bearish: 5.2, color: '#f59e0b' },
        { name: 'Healthcare', companies: 30, events: 38, bullish: 6.8, bearish: 3.5, color: '#10b981' },
        { name: 'Automobile', companies: 24, events: 28, bullish: 7.0, bearish: 3.0, color: '#10b981' },
        { name: 'FMCG', companies: 18, events: 22, bullish: 6.2, bearish: 3.8, color: '#10b981' },
        { name: 'Metals & Mining', companies: 15, events: 20, bullish: 5.0, bearish: 5.5, color: '#ef4444' },
        { name: 'Construction', companies: 20, events: 25, bullish: 6.5, bearish: 3.8, color: '#10b981' },
        { name: 'Consumer Durables', companies: 25, events: 30, bullish: 6.8, bearish: 3.2, color: '#10b981' },
        { name: 'Telecom', companies: 10, events: 15, bullish: 4.5, bearish: 5.5, color: '#ef4444' },
        { name: 'Chemicals', companies: 20, events: 18, bullish: 5.8, bearish: 4.2, color: '#f59e0b' },
        { name: 'Real Estate', companies: 12, events: 16, bullish: 6.0, bearish: 4.5, color: '#f59e0b' },
        { name: 'Defence', companies: 7, events: 12, bullish: 7.5, bearish: 2.0, color: '#10b981' },
        { name: 'Infrastructure', companies: 13, events: 18, bullish: 6.2, bearish: 3.5, color: '#10b981' },
        { name: 'Technology', companies: 12, events: 20, bullish: 5.0, bearish: 6.0, color: '#ef4444' },
    ];

    let bubbles = [];
    let mouseX = 0, mouseY = 0;
    let hoveredBubble = null;
    let animationFrame;

    function resizeCanvas() {
        const wrapper = canvas.parentElement;
        canvas.width = wrapper.clientWidth;
        canvas.height = wrapper.clientHeight;
        layoutBubbles();
    }

    function layoutBubbles() {
        bubbles = [];
        const w = canvas.width;
        const h = canvas.height;
        const centerX = w * 0.42;
        const centerY = h * 0.5;

        SECTORS.forEach((sector, idx) => {
            const angle = (idx / SECTORS.length) * Math.PI * 2 - Math.PI / 2;
            const radius = Math.min(w, h) * 0.28;

            // Base size from company count
            const baseSize = 20 + sector.companies * 1.2;
            const size = Math.min(baseSize, 80);

            // Position with some organic offset
            const offsetX = Math.cos(angle + idx * 0.3) * (radius * 0.15);
            const offsetY = Math.sin(angle + idx * 0.3) * (radius * 0.15);

            const net = sector.bullish - sector.bearish;
            let color;
            if (net > 2) color = '#10b981';       // Strong bullish
            else if (net > 0) color = '#34d399';   // Mild bullish
            else if (net > -2) color = '#f59e0b';  // Neutral
            else color = '#ef4444';                // Bearish

            bubbles.push({
                x: centerX + Math.cos(angle) * radius + offsetX,
                y: centerY + Math.sin(angle) * radius + offsetY,
                baseX: centerX + Math.cos(angle) * radius + offsetX,
                baseY: centerY + Math.sin(angle) * radius + offsetY,
                size: size,
                color: color,
                sector: sector,
                phase: Math.random() * Math.PI * 2,
                speed: 0.3 + Math.random() * 0.5,
            });
        });
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const time = Date.now() / 1000;

        // Draw connection lines between nearby bubbles
        ctx.strokeStyle = 'rgba(245, 158, 11, 0.06)';
        ctx.lineWidth = 1;
        for (let i = 0; i < bubbles.length; i++) {
            for (let j = i + 1; j < bubbles.length; j++) {
                const dx = bubbles[i].x - bubbles[j].x;
                const dy = bubbles[i].y - bubbles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 200) {
                    ctx.beginPath();
                    ctx.moveTo(bubbles[i].x, bubbles[i].y);
                    ctx.lineTo(bubbles[j].x, bubbles[j].y);
                    ctx.stroke();
                }
            }
        }

        // Draw bubbles
        bubbles.forEach(b => {
            // Floating animation
            b.x = b.baseX + Math.sin(time * b.speed + b.phase) * 8;
            b.y = b.baseY + Math.cos(time * b.speed * 0.7 + b.phase) * 6;

            // Parallax with mouse
            const parallaxX = (mouseX - canvas.width / 2) * 0.02;
            const parallaxY = (mouseY - canvas.height / 2) * 0.02;
            const px = b.x + parallaxX;
            const py = b.y + parallaxY;

            const isHovered = b === hoveredBubble;
            const drawSize = isHovered ? b.size * 1.15 : b.size;

            // Glow
            const gradient = ctx.createRadialGradient(px, py, 0, px, py, drawSize);
            gradient.addColorStop(0, b.color + '40');
            gradient.addColorStop(0.7, b.color + '15');
            gradient.addColorStop(1, b.color + '00');
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(px, py, drawSize * 1.5, 0, Math.PI * 2);
            ctx.fill();

            // Main bubble
            const bubbleGrad = ctx.createRadialGradient(px - drawSize * 0.2, py - drawSize * 0.2, drawSize * 0.1, px, py, drawSize);
            bubbleGrad.addColorStop(0, b.color + 'cc');
            bubbleGrad.addColorStop(1, b.color + '66');
            ctx.fillStyle = bubbleGrad;
            ctx.beginPath();
            ctx.arc(px, py, drawSize, 0, Math.PI * 2);
            ctx.fill();

            // Border
            ctx.strokeStyle = isHovered ? b.color : b.color + '44';
            ctx.lineWidth = isHovered ? 2 : 1;
            ctx.stroke();

            // Label
            if (drawSize > 30) {
                ctx.fillStyle = '#ffffff';
                ctx.font = `${Math.max(10, drawSize * 0.22)}px "Inter", sans-serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';

                // Shorten name for small bubbles
                let label = b.sector.name;
                if (drawSize < 45) {
                    label = label.split(' ')[0];
                }
                ctx.fillText(label, px, py - 6);

                ctx.font = `bold ${Math.max(9, drawSize * 0.2)}px "JetBrains Mono", monospace`;
                const net = (b.sector.bullish - b.sector.bearish).toFixed(1);
                ctx.fillText((net >= 0 ? '+' : '') + net, px, py + 10);
            }
        });

        animationFrame = requestAnimationFrame(draw);
    }

    // Mouse interaction
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mouseX = e.clientX - rect.left;
        mouseY = e.clientY - rect.top;

        hoveredBubble = null;
        for (const b of bubbles) {
            const dx = mouseX - b.x;
            const dy = mouseY - b.y;
            if (Math.sqrt(dx * dx + dy * dy) < b.size) {
                hoveredBubble = b;
                break;
            }
        }

        if (hoveredBubble) {
            const s = hoveredBubble.sector;
            tooltip.replaceChildren();

            const name = document.createElement('div');
            name.style.fontWeight = '700';
            name.textContent = s.name;

            const stats = document.createElement('div');
            stats.style.fontSize = '0.75rem';
            stats.style.color = 'var(--text-muted)';
            stats.textContent = s.companies + ' companies • ' + s.events + ' events';

            const scores = document.createElement('div');
            scores.style.marginTop = '4px';
            scores.textContent = '📈 ' + s.bullish.toFixed(1) + '  📉 ' + s.bearish.toFixed(1) +
                '  Net: ' + (s.bullish - s.bearish).toFixed(1);

            tooltip.appendChild(name);
            tooltip.appendChild(stats);
            tooltip.appendChild(scores);

            tooltip.style.left = (e.clientX - rect.left + 15) + 'px';
            tooltip.style.top = (e.clientY - rect.top - 10) + 'px';
            tooltip.classList.add('visible');
            canvas.style.cursor = 'pointer';
        } else {
            tooltip.classList.remove('visible');
            canvas.style.cursor = 'default';
        }
    });

    canvas.addEventListener('mouseleave', () => {
        hoveredBubble = null;
        tooltip.classList.remove('visible');
    });

    // Sector info panel
    function renderSectorPanel() {
        const panel = document.getElementById('sector-list');
        if (!panel) return;
        panel.replaceChildren();

        const sorted = [...SECTORS].sort((a, b) => (b.bullish - b.bearish) - (a.bullish - a.bearish));
        sorted.forEach(s => {
            const row = document.createElement('div');
            row.className = 'sector-row';

            const name = document.createElement('span');
            name.textContent = s.name.split(' ')[0]; // Short name

            const net = s.bullish - s.bearish;
            const score = document.createElement('span');
            score.className = 'sector-score ' + (net >= 0 ? 'pos' : 'neg');
            score.textContent = (net >= 0 ? '+' : '') + net.toFixed(1);

            row.appendChild(name);
            row.appendChild(score);
            panel.appendChild(row);
        });
    }

    // Nav toggle
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
    }

    // Init
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
    renderSectorPanel();
    draw();

})();
