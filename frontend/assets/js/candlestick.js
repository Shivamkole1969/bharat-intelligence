/**
 * Bharat Market Intelligence — Nison Candlestick Pattern Chart
 *
 * Interactive canvas-based candlestick chart with:
 * - OHLCV candle rendering (green/red)
 * - Detected pattern markers
 * - Dotted projection candles for predicted future
 * - Support/resistance lines
 * - Zoom in/out + pan (drag) + scroll wheel zoom
 * - Proper date labels on X-axis
 * - Hover tooltips with OHLCV + patterns
 * - Responsive sizing
 *
 * Based on Steve Nison's Japanese Candlestick Charting Techniques.
 */

(function () {
    'use strict';

    // ── State ──────────────────────────────────────────────────────────────
    let chartData = null;
    let canvas = null;
    let ctx = null;
    let hoveredCandle = -1;
    let tooltipEl = null;

    // Zoom & Pan state
    let viewStart = 0;   // index of first visible candle
    let viewEnd = 0;     // index of last visible candle (exclusive)
    let isDragging = false;
    let dragStartX = 0;
    let dragStartViewStart = 0;

    const MIN_VISIBLE = 10;
    const MAX_VISIBLE = 400;

    const COLORS = {
        bg: '#060a13',
        grid: 'rgba(255,255,255,0.04)',
        gridText: 'rgba(255,255,255,0.35)',
        bullish: '#22c55e',
        bullishFill: 'rgba(34,197,94,0.85)',
        bearish: '#ef4444',
        bearishFill: 'rgba(239,68,68,0.85)',
        projBullish: 'rgba(34,197,94,0.4)',
        projBearish: 'rgba(239,68,68,0.4)',
        projBullishBorder: 'rgba(34,197,94,0.7)',
        projBearishBorder: 'rgba(239,68,68,0.7)',
        projLine: 'rgba(245,158,11,0.7)',
        projFill: 'rgba(245,158,11,0.06)',
        support: 'rgba(34,197,94,0.3)',
        resistance: 'rgba(239,68,68,0.3)',
        patternBadge: 'rgba(245,158,11,0.9)',
        volume: 'rgba(255,255,255,0.08)',
        tooltip: 'rgba(13,19,33,0.95)',
        amber: '#f59e0b',
        divider: 'rgba(245,158,11,0.5)',
        crosshair: 'rgba(255,255,255,0.15)',
    };

    const PATTERN_ICONS = {
        bullish: '🟢',
        bearish: '🔴',
        neutral: '🟡',
    };

    // ── Initialization ─────────────────────────────────────────────────────

    async function initCandlestickChart() {
        const container = document.getElementById('nison-chart');
        const periodSelect = document.getElementById('nison-period');

        if (!container) return;

        // Get symbol from URL
        const urlParams = new URLSearchParams(window.location.search);
        const rawSymbol = (urlParams.get('symbol') || 'RELIANCE').toUpperCase().trim();
        const cleanSymbol = rawSymbol.replace(/\s+/g, '');

        // Period selector
        if (periodSelect) {
            periodSelect.addEventListener('change', () => {
                loadAndRender(cleanSymbol, periodSelect.value);
            });
        }

        await loadAndRender(cleanSymbol, periodSelect ? periodSelect.value : '6mo');
    }

    async function loadAndRender(symbol, period) {
        const container = document.getElementById('nison-chart');
        const patternsPanel = document.getElementById('nison-patterns');
        const predictionBar = document.getElementById('nison-prediction');

        // Show loading
        container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);font-size:0.9rem;">Analyzing candlestick patterns...</div>';
        if (patternsPanel) patternsPanel.innerHTML = '';
        if (predictionBar) predictionBar.innerHTML = '';

        try {
            if (!window.BharatAPI || !window.BharatAPI.getCandlestickAnalysis) {
                throw new Error('API not loaded');
            }

            chartData = await window.BharatAPI.getCandlestickAnalysis(symbol, { period, interval: '1d' });

            if (!chartData || !chartData.ohlcv || chartData.ohlcv.length < 10) {
                throw new Error('Insufficient data');
            }

            // Set initial view to show all candles
            const projected = chartData.prediction?.projected_candles || [];
            viewStart = 0;
            viewEnd = chartData.ohlcv.length + projected.length;

            // Render chart
            renderChart(container);

            // Render pattern panel
            if (patternsPanel) renderPatterns(patternsPanel, chartData.detected_patterns);

            // Render prediction bar
            if (predictionBar) renderPrediction(predictionBar, chartData.prediction);

        } catch (e) {
            container.innerHTML = `
                <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:8px;">
                    <span style="font-size:1.5rem;">🕯️</span>
                    <p style="color:var(--text-muted);font-size:0.85rem;margin:0;">Candlestick analysis unavailable</p>
                    <p style="color:var(--text-muted);font-size:0.75rem;margin:0;">${e.message || 'Unable to fetch price data'}</p>
                </div>
            `;
        }
    }

    // ── Chart Renderer ─────────────────────────────────────────────────────

    function getAllCandles() {
        if (!chartData) return [];
        const ohlcv = chartData.ohlcv;
        const projected = chartData.prediction?.projected_candles || [];

        // Generate future dates for projected candles
        const lastDate = ohlcv.length > 0 ? new Date(ohlcv[ohlcv.length - 1].date) : new Date();

        return [
            ...ohlcv,
            ...projected.map((p, j) => {
                const futureDate = new Date(lastDate);
                futureDate.setDate(futureDate.getDate() + j + 1);
                // Skip weekends
                while (futureDate.getDay() === 0 || futureDate.getDay() === 6) {
                    futureDate.setDate(futureDate.getDate() + 1);
                }
                return {
                    date: futureDate.toISOString().slice(0, 10),
                    open: p.open, high: p.high, low: p.low, close: p.close,
                    _projected: true
                };
            })
        ];
    }

    function renderChart(container) {
        container.innerHTML = '';

        // Chart wrapper
        const wrapper = document.createElement('div');
        wrapper.style.cssText = 'position:relative;width:100%;height:100%;';
        container.appendChild(wrapper);

        // Canvas
        canvas = document.createElement('canvas');
        canvas.style.cssText = 'width:100%;height:100%;cursor:crosshair;display:block;';
        wrapper.appendChild(canvas);

        // Tooltip
        tooltipEl = document.createElement('div');
        tooltipEl.className = 'nison-tooltip';
        tooltipEl.style.display = 'none';
        wrapper.appendChild(tooltipEl);

        // Zoom controls
        const controls = document.createElement('div');
        controls.className = 'chart-zoom-controls';
        controls.innerHTML = `
            <button class="chart-zoom-btn" id="zoom-in" title="Zoom In">＋</button>
            <button class="chart-zoom-btn" id="zoom-out" title="Zoom Out">－</button>
            <button class="chart-zoom-btn" id="zoom-fit" title="Fit All">⊞</button>
            <button class="chart-zoom-btn" id="zoom-proj" title="Focus Projected">🔮</button>
        `;
        wrapper.appendChild(controls);

        resizeCanvas();
        draw();

        // Events
        window.addEventListener('resize', () => { resizeCanvas(); draw(); });

        // Mouse hover
        canvas.addEventListener('mousemove', (e) => {
            if (isDragging) {
                handleDrag(e);
                return;
            }
            const rect = canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) * (canvas.width / rect.width);
            const y = (e.clientY - rect.top) * (canvas.height / rect.height);
            handleHover(x, y, rect, e);
        });

        canvas.addEventListener('mouseleave', () => {
            hoveredCandle = -1;
            tooltipEl.style.display = 'none';
            draw();
        });

        // Drag to pan
        canvas.addEventListener('mousedown', (e) => {
            isDragging = true;
            dragStartX = e.clientX;
            dragStartViewStart = viewStart;
            canvas.style.cursor = 'grabbing';
        });

        window.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                canvas.style.cursor = 'crosshair';
            }
        });

        // Scroll wheel zoom
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const rect = canvas.getBoundingClientRect();
            const mouseRatio = (e.clientX - rect.left) / rect.width;
            const visibleCount = viewEnd - viewStart;
            const zoomFactor = e.deltaY > 0 ? 1.15 : 0.87;
            const newVisible = Math.round(Math.max(MIN_VISIBLE, Math.min(MAX_VISIBLE, visibleCount * zoomFactor)));
            const diff = newVisible - visibleCount;
            const leftAdj = Math.round(diff * mouseRatio);
            const rightAdj = diff - leftAdj;

            const allCandles = getAllCandles();
            viewStart = Math.max(0, viewStart - leftAdj);
            viewEnd = Math.min(allCandles.length, viewEnd + rightAdj);
            if (viewEnd - viewStart < MIN_VISIBLE) viewEnd = Math.min(allCandles.length, viewStart + MIN_VISIBLE);
            draw();
        }, { passive: false });

        // Zoom buttons
        document.getElementById('zoom-in').addEventListener('click', () => zoomBy(0.7));
        document.getElementById('zoom-out').addEventListener('click', () => zoomBy(1.4));
        document.getElementById('zoom-fit').addEventListener('click', () => {
            viewStart = 0;
            viewEnd = getAllCandles().length;
            draw();
        });
        document.getElementById('zoom-proj').addEventListener('click', () => {
            // Focus on last 20 candles + projected
            const ohlcvLen = chartData.ohlcv.length;
            const projLen = chartData.prediction?.projected_candles?.length || 0;
            viewStart = Math.max(0, ohlcvLen - 15);
            viewEnd = ohlcvLen + projLen;
            draw();
        });
    }

    function zoomBy(factor) {
        const allCandles = getAllCandles();
        const center = (viewStart + viewEnd) / 2;
        const half = ((viewEnd - viewStart) * factor) / 2;
        viewStart = Math.max(0, Math.round(center - half));
        viewEnd = Math.min(allCandles.length, Math.round(center + half));
        if (viewEnd - viewStart < MIN_VISIBLE) viewEnd = Math.min(allCandles.length, viewStart + MIN_VISIBLE);
        draw();
    }

    function handleDrag(e) {
        const allCandles = getAllCandles();
        const rect = canvas.getBoundingClientRect();
        const dx = e.clientX - dragStartX;
        const candlesPerPx = (viewEnd - viewStart) / rect.width;
        const shift = Math.round(-dx * candlesPerPx);
        const newStart = Math.max(0, Math.min(allCandles.length - MIN_VISIBLE, dragStartViewStart + shift));
        const visibleCount = viewEnd - viewStart;
        viewStart = newStart;
        viewEnd = Math.min(allCandles.length, newStart + visibleCount);
        draw();
    }

    function resizeCanvas() {
        if (!canvas) return;
        const rect = canvas.parentElement.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
    }

    function draw() {
        if (!ctx || !chartData) return;

        const W = canvas.width / (window.devicePixelRatio || 1);
        const H = canvas.height / (window.devicePixelRatio || 1);
        const allCandles = getAllCandles();
        const ohlcvLen = chartData.ohlcv.length;

        // Visible slice
        const visCandles = allCandles.slice(viewStart, viewEnd);
        const visCount = visCandles.length;
        if (visCount === 0) return;

        const margin = { top: 24, right: 65, bottom: 36, left: 10 };
        const chartW = W - margin.left - margin.right;
        const chartH = H - margin.top - margin.bottom;

        // Price range for visible candles
        let minPrice = Infinity, maxPrice = -Infinity;
        visCandles.forEach(c => {
            if (c.low < minPrice) minPrice = c.low;
            if (c.high > maxPrice) maxPrice = c.high;
        });
        const priceRange = maxPrice - minPrice || 1;
        const padding = priceRange * 0.06;
        minPrice -= padding;
        maxPrice += padding;

        const candleW = Math.max(3, Math.min(16, (chartW / visCount) * 0.65));
        const gap = chartW / visCount;

        function priceToY(price) {
            return margin.top + chartH - ((price - minPrice) / (maxPrice - minPrice)) * chartH;
        }

        function indexToX(visIdx) {
            return margin.left + gap * visIdx + gap / 2;
        }

        // ── Clear ──
        ctx.fillStyle = COLORS.bg;
        ctx.fillRect(0, 0, W, H);

        // ── Grid lines ──
        const gridLines = 6;
        ctx.strokeStyle = COLORS.grid;
        ctx.lineWidth = 1;
        ctx.font = '10px monospace';
        ctx.fillStyle = COLORS.gridText;
        ctx.textAlign = 'right';

        for (let i = 0; i <= gridLines; i++) {
            const price = minPrice + (maxPrice - minPrice) * (i / gridLines);
            const y = priceToY(price);
            ctx.beginPath();
            ctx.moveTo(margin.left, y);
            ctx.lineTo(W - margin.right, y);
            ctx.stroke();
            ctx.fillText('₹' + price.toFixed(price > 1000 ? 0 : 2), W - 5, y + 3);
        }

        // ── Support / Resistance lines ──
        const pred = chartData.prediction;
        if (pred) {
            const sy = priceToY(pred.support_level);
            const ry = priceToY(pred.resistance_level);

            // Only draw if in visible price range
            if (pred.support_level >= minPrice && pred.support_level <= maxPrice) {
                ctx.strokeStyle = COLORS.support;
                ctx.lineWidth = 1;
                ctx.setLineDash([8, 4]);
                ctx.beginPath();
                ctx.moveTo(margin.left, sy);
                ctx.lineTo(W - margin.right, sy);
                ctx.stroke();
                ctx.fillStyle = 'rgba(34,197,94,0.6)';
                ctx.font = '9px monospace';
                ctx.textAlign = 'left';
                ctx.fillText('S: ₹' + pred.support_level.toFixed(0), margin.left + 4, sy - 4);
            }

            if (pred.resistance_level >= minPrice && pred.resistance_level <= maxPrice) {
                ctx.strokeStyle = COLORS.resistance;
                ctx.setLineDash([8, 4]);
                ctx.beginPath();
                ctx.moveTo(margin.left, ry);
                ctx.lineTo(W - margin.right, ry);
                ctx.stroke();
                ctx.fillStyle = 'rgba(239,68,68,0.6)';
                ctx.font = '9px monospace';
                ctx.textAlign = 'left';
                ctx.fillText('R: ₹' + pred.resistance_level.toFixed(0), margin.left + 4, ry - 4);
            }
            ctx.setLineDash([]);
        }

        // ── Projection zone background ──
        const projStartVisIdx = ohlcvLen - viewStart;
        if (projStartVisIdx > 0 && projStartVisIdx < visCount) {
            const projX = indexToX(projStartVisIdx) - gap / 2;
            ctx.fillStyle = COLORS.projFill;
            ctx.fillRect(projX, margin.top, W - margin.right - projX, chartH);
        }

        // ── Draw candles ──
        visCandles.forEach((c, vi) => {
            const x = indexToX(vi);
            const globalIdx = vi + viewStart;
            const isProjected = c._projected;
            const isBullish = c.close >= c.open;
            const bodyTop = priceToY(Math.max(c.open, c.close));
            const bodyBot = priceToY(Math.min(c.open, c.close));
            const bodyH = Math.max(1, bodyBot - bodyTop);

            if (isProjected) {
                // ── Projected candle (with glow effect) ──
                const color = isBullish ? COLORS.projBullish : COLORS.projBearish;
                const borderColor = isBullish ? COLORS.projBullishBorder : COLORS.projBearishBorder;

                // Glow
                ctx.shadowColor = isBullish ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)';
                ctx.shadowBlur = 6;

                // Wick (dotted)
                ctx.strokeStyle = borderColor;
                ctx.lineWidth = 1.5;
                ctx.setLineDash([3, 2]);
                ctx.beginPath();
                ctx.moveTo(x, priceToY(c.high));
                ctx.lineTo(x, priceToY(c.low));
                ctx.stroke();
                ctx.setLineDash([]);

                // Body
                ctx.fillStyle = color;
                ctx.fillRect(x - candleW / 2, bodyTop, candleW, bodyH);

                // Dashed border
                ctx.strokeStyle = borderColor;
                ctx.lineWidth = 1.5;
                ctx.setLineDash([3, 2]);
                ctx.strokeRect(x - candleW / 2, bodyTop, candleW, bodyH);
                ctx.setLineDash([]);

                ctx.shadowBlur = 0;
            } else {
                // ── Real candle ──
                const wickColor = isBullish ? COLORS.bullish : COLORS.bearish;
                const fillColor = isBullish ? COLORS.bullishFill : COLORS.bearishFill;

                // Wick
                ctx.strokeStyle = wickColor;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(x, priceToY(c.high));
                ctx.lineTo(x, priceToY(c.low));
                ctx.stroke();

                // Body
                ctx.fillStyle = fillColor;
                ctx.fillRect(x - candleW / 2, bodyTop, candleW, bodyH);

                // Highlight hovered candle
                if (globalIdx === hoveredCandle) {
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 1.5;
                    ctx.strokeRect(x - candleW / 2 - 1, bodyTop - 1, candleW + 2, bodyH + 2);
                }
            }
        });

        // ── Projection divider ──
        if (projStartVisIdx > 0 && projStartVisIdx < visCount) {
            const divX = indexToX(projStartVisIdx) - gap / 2;
            ctx.strokeStyle = COLORS.divider;
            ctx.lineWidth = 1.5;
            ctx.setLineDash([5, 3]);
            ctx.beginPath();
            ctx.moveTo(divX, margin.top);
            ctx.lineTo(divX, H - margin.bottom);
            ctx.stroke();
            ctx.setLineDash([]);

            // Labels
            ctx.font = '10px sans-serif';
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.textAlign = 'right';
            ctx.fillText('Actual', divX - 6, margin.top + 14);
            ctx.fillStyle = COLORS.amber;
            ctx.textAlign = 'left';
            ctx.fillText('Projected →', divX + 6, margin.top + 14);
        }

        // ── Projection trend line ──
        const projCandles = chartData.prediction?.projected_candles || [];
        if (projCandles.length > 1 && projStartVisIdx > 0 && projStartVisIdx <= visCount) {
            ctx.strokeStyle = COLORS.projLine;
            ctx.lineWidth = 2;
            ctx.setLineDash([6, 4]);
            ctx.beginPath();

            // Start from last real candle
            const lastRealVisIdx = projStartVisIdx - 1;
            if (lastRealVisIdx >= 0 && lastRealVisIdx < visCount) {
                const lastReal = visCandles[lastRealVisIdx];
                ctx.moveTo(indexToX(lastRealVisIdx), priceToY(lastReal.close));
            }

            projCandles.forEach((p, j) => {
                const projVisIdx = projStartVisIdx + j;
                if (projVisIdx >= 0 && projVisIdx < visCount) {
                    ctx.lineTo(indexToX(projVisIdx), priceToY(p.close));
                }
            });
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // ── Pattern markers ──
        const patterns = chartData.detected_patterns || [];
        const markedIndices = new Set();
        patterns.slice(0, 15).forEach(p => {
            const idx = Math.max(...p.candle_indices);
            if (idx >= ohlcvLen || markedIndices.has(idx)) return;
            markedIndices.add(idx);

            const visIdx = idx - viewStart;
            if (visIdx < 0 || visIdx >= visCount) return;

            const x = indexToX(visIdx);
            const candle = chartData.ohlcv[idx];
            const markerY = priceToY(candle.high) - 14;

            const color = p.pattern_type === 'bullish' ? COLORS.bullish :
                          p.pattern_type === 'bearish' ? COLORS.bearish : COLORS.amber;

            ctx.fillStyle = color;
            ctx.beginPath();
            if (p.pattern_type === 'bullish') {
                ctx.moveTo(x, markerY + 8);
                ctx.lineTo(x - 5, markerY);
                ctx.lineTo(x + 5, markerY);
            } else {
                ctx.moveTo(x, markerY);
                ctx.lineTo(x - 5, markerY + 8);
                ctx.lineTo(x + 5, markerY + 8);
            }
            ctx.closePath();
            ctx.fill();
        });

        // ── Date labels ──
        ctx.fillStyle = COLORS.gridText;
        ctx.font = '9px monospace';
        ctx.textAlign = 'center';
        const maxLabels = Math.min(10, visCount);
        const labelStep = Math.max(1, Math.floor(visCount / maxLabels));
        for (let vi = 0; vi < visCount; vi += labelStep) {
            const x = indexToX(vi);
            const c = visCandles[vi];
            if (!c.date) continue;

            let label;
            if (c._projected) {
                label = c.date.substring(5); // MM-DD
            } else {
                // Format as "Mar 22" or "15 May"
                try {
                    const d = new Date(c.date);
                    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                    label = months[d.getMonth()] + ' ' + d.getDate();
                } catch {
                    label = c.date.substring(5);
                }
            }
            ctx.fillText(label, x, H - margin.bottom + 14);
        }
    }

    // ── Hover / Tooltip ────────────────────────────────────────────────────

    function handleHover(mouseX, mouseY, canvasRect, event) {
        if (!chartData) return;

        const W = canvas.width / (window.devicePixelRatio || 1);
        const allCandles = getAllCandles();
        const visCount = viewEnd - viewStart;
        const margin = { top: 24, right: 65, bottom: 36, left: 10 };
        const gap = (W - margin.left - margin.right) / visCount;

        const visIdx = Math.floor((mouseX - margin.left) / gap);
        const globalIdx = visIdx + viewStart;

        if (visIdx >= 0 && visIdx < visCount && globalIdx < allCandles.length) {
            hoveredCandle = globalIdx;
            const c = allCandles[globalIdx];

            // Find patterns at this index
            const patternsHere = globalIdx < chartData.ohlcv.length
                ? (chartData.detected_patterns || []).filter(p => p.candle_indices.includes(globalIdx))
                : [];

            let patternHtml = '';
            if (patternsHere.length > 0) {
                patternHtml = '<div style="margin-top:6px;border-top:1px solid rgba(255,255,255,0.1);padding-top:4px;">' +
                    patternsHere.map(p =>
                        `<div style="font-size:10px;color:${p.pattern_type === 'bullish' ? COLORS.bullish : COLORS.bearish};">` +
                        `${PATTERN_ICONS[p.pattern_type]} ${p.pattern_name}</div>`
                    ).join('') + '</div>';
            }

            const projLabel = c._projected ? '<span style="color:#f59e0b;font-size:9px;">PROJECTED</span><br>' : '';
            const change = ((c.close - c.open) / c.open * 100).toFixed(2);
            const changeColor = c.close >= c.open ? COLORS.bullish : COLORS.bearish;

            // Format date nicely
            let dateLabel = c.date;
            try {
                const d = new Date(c.date);
                dateLabel = d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
            } catch {}

            tooltipEl.innerHTML = `
                ${projLabel}
                <div style="font-weight:700;color:var(--text-primary);margin-bottom:4px;">${dateLabel}</div>
                <div style="display:grid;grid-template-columns:auto auto;gap:2px 12px;font-size:11px;">
                    <span style="color:var(--text-muted);">Open</span><span>₹${c.open.toFixed(2)}</span>
                    <span style="color:var(--text-muted);">High</span><span>₹${c.high.toFixed(2)}</span>
                    <span style="color:var(--text-muted);">Low</span><span>₹${c.low.toFixed(2)}</span>
                    <span style="color:var(--text-muted);">Close</span><span style="font-weight:700;">₹${c.close.toFixed(2)}</span>
                    <span style="color:var(--text-muted);">Chg</span><span style="color:${changeColor}">${change}%</span>
                </div>
                ${patternHtml}
            `;
            tooltipEl.style.display = 'block';

            // Position tooltip
            const tooltipX = event.clientX - canvasRect.left + 15;
            const tooltipY = event.clientY - canvasRect.top - 10;
            tooltipEl.style.left = Math.min(tooltipX, canvasRect.width - 200) + 'px';
            tooltipEl.style.top = Math.max(0, tooltipY) + 'px';

        } else {
            hoveredCandle = -1;
            tooltipEl.style.display = 'none';
        }

        draw();
    }

    // ── Pattern Panel ──────────────────────────────────────────────────────

    function renderPatterns(container, patterns) {
        if (!patterns || patterns.length === 0) {
            container.innerHTML = `
                <div style="padding:var(--space-lg);text-align:center;color:var(--text-muted);font-size:0.85rem;">
                    No significant patterns detected in the last 30 sessions.
                </div>
            `;
            return;
        }

        // Deduplicate by name, keep most recent/confident
        const seen = new Map();
        patterns.forEach(p => {
            if (!seen.has(p.pattern_name) || p.confidence > seen.get(p.pattern_name).confidence) {
                seen.set(p.pattern_name, p);
            }
        });
        const unique = Array.from(seen.values()).slice(0, 8);

        container.innerHTML = unique.map(p => {
            const icon = PATTERN_ICONS[p.pattern_type] || '🟡';
            const confPct = Math.round(p.confidence * 100);
            const confColor = p.confidence >= 0.7 ? COLORS.bullish :
                              p.confidence >= 0.5 ? COLORS.amber : COLORS.bearish;
            const typeColor = p.pattern_type === 'bullish' ? COLORS.bullish :
                              p.pattern_type === 'bearish' ? COLORS.bearish : COLORS.amber;

            return `
                <div class="nison-pattern-card">
                    <div class="npc-header">
                        <span class="npc-icon">${icon}</span>
                        <span class="npc-name">${p.pattern_name}</span>
                        <span class="npc-type" style="color:${typeColor};">${p.pattern_type.toUpperCase()}</span>
                    </div>
                    <div class="npc-conf">
                        <div class="npc-conf-bar">
                            <div class="npc-conf-fill" style="width:${confPct}%;background:${confColor};"></div>
                        </div>
                        <span class="npc-conf-label">${confPct}%</span>
                    </div>
                    <p class="npc-desc">${p.description}</p>
                    <div class="npc-meta">
                        <span>📖 ${p.nison_chapter}</span>
                        <span>⚡ ${p.reliability} reliability</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ── Prediction Bar ─────────────────────────────────────────────────────

    function renderPrediction(container, prediction) {
        if (!prediction || !prediction.summary) {
            container.innerHTML = '';
            return;
        }

        const dirColor = prediction.direction === 'bullish' ? COLORS.bullish :
                          prediction.direction === 'bearish' ? COLORS.bearish : COLORS.amber;
        const dirIcon = prediction.direction === 'bullish' ? '📈' :
                        prediction.direction === 'bearish' ? '📉' : '➡️';
        const confPct = Math.round(prediction.confidence * 100);

        container.innerHTML = `
            <div class="nison-pred-inner">
                <div class="nison-pred-dir" style="color:${dirColor};">
                    <span style="font-size:1.4rem;">${dirIcon}</span>
                    <span class="nison-pred-label">${prediction.direction.toUpperCase()} BIAS</span>
                    <span class="nison-pred-conf">${confPct}% confidence</span>
                </div>
                <div class="nison-pred-summary">${prediction.summary}</div>
                <div class="nison-pred-levels">
                    <span style="color:${COLORS.bullish};">Support: ₹${prediction.support_level.toLocaleString()}</span>
                    <span style="color:${COLORS.bearish};">Resistance: ₹${prediction.resistance_level.toLocaleString()}</span>
                </div>
            </div>
        `;
    }

    // ── Boot ────────────────────────────────────────────────────────────────

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCandlestickChart);
    } else {
        setTimeout(initCandlestickChart, 100);
    }

})();
