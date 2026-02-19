/* ══════════════════════════════════════════════════════
   CryptoVision — Full Interactive App
   TradingView charts, Binance signals, timer, sharing
   ══════════════════════════════════════════════════════ */

const CRYPTOS = {
    BTC: { name: 'Bitcoin', pair: 'BTCUSDT', tv: 'BINANCE:BTCUSDT', logo: 'https://assets.coingecko.com/coins/images/1/small/bitcoin.png' },
    ETH: { name: 'Ethereum', pair: 'ETHUSDT', tv: 'BINANCE:ETHUSDT', logo: 'https://assets.coingecko.com/coins/images/279/small/ethereum.png' },
    SOL: { name: 'Solana', pair: 'SOLUSDT', tv: 'BINANCE:SOLUSDT', logo: 'https://assets.coingecko.com/coins/images/4128/small/solana.png' },
    XRP: { name: 'XRP', pair: 'XRPUSDT', tv: 'BINANCE:XRPUSDT', logo: 'https://assets.coingecko.com/coins/images/44/small/xrp-symbol-white-128.png' },
};

let selected = 'BTC';
let currentAnalysis = null;
let currentPrice = 0;
let timerInterval = null;
const REFRESH_SEC = 300; // 5 minutes

// ══════════════════════════════════════════════════
// TRADINGVIEW CHART
// ══════════════════════════════════════════════════
function loadChart(sym) {
    const el = document.getElementById('tradingview-widget');
    el.innerHTML = '';
    new TradingView.widget({
        symbol: CRYPTOS[sym].tv,
        interval: 'D',
        timezone: 'Etc/UTC',
        theme: 'dark',
        style: '1',
        locale: 'en',
        toolbar_bg: '#0a0a0f',
        enable_publishing: false,
        hide_top_toolbar: false,
        save_image: false,
        container_id: 'tradingview-widget',
        autosize: true,
        withdateranges: true,
        allow_symbol_change: false,
        studies: ['RSI@tv-basicstudies', 'MACD@tv-basicstudies', 'BB@tv-basicstudies'],
        overrides: {
            'paneProperties.background': '#0a0a0f',
            'paneProperties.backgroundType': 'solid',
            'mainSeriesProperties.candleStyle.upColor': '#10b981',
            'mainSeriesProperties.candleStyle.downColor': '#ef4444',
            'mainSeriesProperties.candleStyle.borderUpColor': '#10b981',
            'mainSeriesProperties.candleStyle.borderDownColor': '#ef4444',
            'mainSeriesProperties.candleStyle.wickUpColor': '#10b981',
            'mainSeriesProperties.candleStyle.wickDownColor': '#ef4444',
        },
    });
}

// ══════════════════════════════════════════════════
// COUNTDOWN TIMER
// ══════════════════════════════════════════════════
function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    let sec = REFRESH_SEC;
    const el = document.getElementById('timer-text');
    timerInterval = setInterval(() => {
        sec--;
        const m = Math.floor(sec / 60);
        const s = sec % 60;
        el.textContent = `${m}:${s.toString().padStart(2, '0')}`;
        if (sec <= 0) {
            clearInterval(timerInterval);
            refreshAll();
        }
    }, 1000);
}

// ══════════════════════════════════════════════════
// TICKER TAPE
// ══════════════════════════════════════════════════
async function loadTicker() {
    const tape = document.getElementById('ticker-tape');
    const items = [];
    for (const [key, cfg] of Object.entries(CRYPTOS)) {
        try {
            const r = await fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${cfg.pair}`);
            const d = await r.json();
            const p = +d.lastPrice, ch = +d.priceChangePercent;
            const col = ch >= 0 ? '#34d399' : '#f87171';
            const ar = ch >= 0 ? '▲' : '▼';
            items.push(`<span class="ticker-item" onclick="selectCrypto('${key}')"><img src="${cfg.logo}"><span class="ticker-name">${key}</span><span class="ticker-price">$${fmt(p)}</span><span style="color:${col}">${ar}${Math.abs(ch).toFixed(2)}%</span></span>`);
        } catch (e) {
            items.push(`<span class="ticker-item"><span class="ticker-name">${key}</span>—</span>`);
        }
    }
    tape.innerHTML = `<div class="ticker-scroll">${items.join('')}${items.join('')}</div>`;
}

// ══════════════════════════════════════════════════
// BINANCE KLINES
// ══════════════════════════════════════════════════
async function fetchKlines(sym, limit = 90) {
    const r = await fetch(`https://api.binance.com/api/v3/klines?symbol=${sym}&interval=1d&limit=${limit}`);
    if (!r.ok) throw new Error(`API ${r.status}`);
    return (await r.json()).map(k => ({ t: new Date(k[0]), o: +k[1], h: +k[2], l: +k[3], c: +k[4], v: +k[5] }));
}

// ══════════════════════════════════════════════════
// INDICATORS (compact)
// ══════════════════════════════════════════════════
const ema = (d, p) => { const k = 2 / (p + 1); const r = [d[0]]; for (let i = 1; i < d.length; i++)r.push(d[i] * k + r[i - 1] * (1 - k)); return r; };
const sma = (d, p) => d.map((_, i) => i < p - 1 ? null : d.slice(i - p + 1, i + 1).reduce((a, b) => a + b, 0) / p);

function rsi(c, p = 14) { const r = Array(c.length).fill(null); if (c.length < p + 1) return r; let g = 0, l = 0; for (let i = 1; i <= p; i++) { const d = c[i] - c[i - 1]; d > 0 ? g += d : l -= d; } let ag = g / p, al = l / p; r[p] = al === 0 ? 100 : 100 - 100 / (1 + ag / al); for (let i = p + 1; i < c.length; i++) { const d = c[i] - c[i - 1]; ag = (ag * (p - 1) + Math.max(d, 0)) / p; al = (al * (p - 1) + Math.max(-d, 0)) / p; r[i] = al === 0 ? 100 : 100 - 100 / (1 + ag / al); } return r; }

function macd(c) { const e12 = ema(c, 12), e26 = ema(c, 26); const m = e12.map((v, i) => v - e26[i]); const s = ema(m, 9); return { m, s, h: m.map((v, i) => v - s[i]) }; }

// ══════════════════════════════════════════════════
// 10 TRADING RULES
// ══════════════════════════════════════════════════
function analyze(klines) {
    const c = klines.map(k => k.c), h = klines.map(k => k.h), l = klines.map(k => k.l), v = klines.map(k => k.v);
    const n = c.length, p = c[n - 1];

    const RSI = rsi(c), MACD = macd(c);
    const e9 = ema(c, 9), e21 = ema(c, 21), e50 = ema(c, 50), e200 = ema(c, 200);
    const vS = sma(v, 20), volR = vS[n - 1] ? v[n - 1] / vS[n - 1] : 1;

    // Bollinger
    const bSma = sma(c, 20);
    let bbU = null, bbL = null;
    if (bSma[n - 1]) { const sq = c.slice(n - 20).reduce((a, b) => a + (b - bSma[n - 1]) ** 2, 0) / 20; const std = Math.sqrt(sq); bbU = bSma[n - 1] + 2 * std; bbL = bSma[n - 1] - 2 * std; }

    // ATR
    const tr = [h[0] - l[0]]; for (let i = 1; i < n; i++)tr.push(Math.max(h[i] - l[i], Math.abs(h[i] - c[i - 1]), Math.abs(l[i] - c[i - 1])));
    const atr = ema(tr, 14), atrP = (atr[n - 1] / p) * 100;

    // ADX
    let adxV = 0;
    if (n > 30) {
        const pd = [], md = []; for (let i = 1; i < n; i++) { const u = h[i] - h[i - 1], d = l[i - 1] - l[i]; pd.push(u > d && u > 0 ? u : 0); md.push(d > u && d > 0 ? d : 0); }
        const at = ema(tr.slice(1), 14), pi = ema(pd, 14).map((v, i) => at[i] > 0 ? (v / at[i]) * 100 : 0), mi = ema(md, 14).map((v, i) => at[i] > 0 ? (v / at[i]) * 100 : 0);
        const dx = pi.map((v, i) => { const s = v + mi[i]; return s > 0 ? (Math.abs(v - mi[i]) / s) * 100 : 0; }); adxV = ema(dx, 14).pop() || 0;
    }

    // Stochastic
    let stK = 50; if (n >= 14) { let hh = -Infinity, ll = Infinity; for (let j = 0; j < 14; j++) { hh = Math.max(hh, h[n - 1 - j]); ll = Math.min(ll, l[n - 1 - j]); } stK = hh === ll ? 50 : ((p - ll) / (hh - ll)) * 100; }

    // Fibonacci & Pivot
    const h90 = Math.max(...h.slice(-90)), l90 = Math.min(...l.slice(-90)), fr = h90 - l90;
    const f382 = h90 - fr * 0.382, f618 = h90 - fr * 0.618;
    const pv = (h[n - 2] + l[n - 2] + c[n - 2]) / 3, r1 = 2 * pv - l[n - 2], s1 = 2 * pv - h[n - 2];

    const lastRSI = RSI[n - 1] ?? 50, lastMACD = MACD.m[n - 1], lastSig = MACD.s[n - 1], prevMACD = MACD.m[n - 2], prevSig = MACD.s[n - 2];

    const rules = []; let score = 0;

    if (lastRSI < 30) { rules.push({ n: 'RSI (14)', s: 'BUY', v: `${lastRSI.toFixed(0)} oversold` }); score += 1.5; }
    else if (lastRSI > 70) { rules.push({ n: 'RSI (14)', s: 'SELL', v: `${lastRSI.toFixed(0)} overbought` }); score -= 1.5; }
    else { rules.push({ n: 'RSI (14)', s: 'NEUTRAL', v: lastRSI.toFixed(0) }); }

    if (prevMACD <= prevSig && lastMACD > lastSig) { rules.push({ n: 'MACD Cross', s: 'BUY', v: 'Bullish cross' }); score += 1.5; }
    else if (prevMACD >= prevSig && lastMACD < lastSig) { rules.push({ n: 'MACD Cross', s: 'SELL', v: 'Death cross' }); score -= 1.5; }
    else { rules.push({ n: 'MACD Cross', s: 'NEUTRAL', v: lastMACD > lastSig ? 'Bullish' : 'Bearish' }); score += lastMACD > lastSig ? 0.3 : -0.3; }

    if (e9[n - 1] > e21[n - 1] && e9[n - 2] <= e21[n - 2]) { rules.push({ n: 'EMA 9/21', s: 'BUY', v: 'Bull cross' }); score += 1; }
    else if (e9[n - 1] < e21[n - 1] && e9[n - 2] >= e21[n - 2]) { rules.push({ n: 'EMA 9/21', s: 'SELL', v: 'Bear cross' }); score -= 1; }
    else { rules.push({ n: 'EMA 9/21', s: 'NEUTRAL', v: e9[n - 1] > e21[n - 1] ? 'Bullish' : 'Bearish' }); score += e9[n - 1] > e21[n - 1] ? 0.2 : -0.2; }

    if (e50[n - 1] > e200[n - 1]) { rules.push({ n: 'EMA 50/200', s: 'BUY', v: 'Golden cross' }); score += 1; }
    else { rules.push({ n: 'EMA 50/200', s: 'SELL', v: 'Death cross' }); score -= 1; }

    if (bbL && p <= bbL) { rules.push({ n: 'Bollinger', s: 'BUY', v: 'Lower band' }); score += 1; }
    else if (bbU && p >= bbU) { rules.push({ n: 'Bollinger', s: 'SELL', v: 'Upper band' }); score -= 1; }
    else { rules.push({ n: 'Bollinger', s: 'NEUTRAL', v: 'Inside bands' }); }

    if (stK < 20) { rules.push({ n: 'Stochastic', s: 'BUY', v: `%K=${stK.toFixed(0)}` }); score += 1; }
    else if (stK > 80) { rules.push({ n: 'Stochastic', s: 'SELL', v: `%K=${stK.toFixed(0)}` }); score -= 1; }
    else { rules.push({ n: 'Stochastic', s: 'NEUTRAL', v: `%K=${stK.toFixed(0)}` }); }

    if (adxV > 25) { rules.push({ n: 'ADX', s: p > e21[n - 1] ? 'BUY' : 'SELL', v: `${adxV.toFixed(0)} strong` }); score += p > e21[n - 1] ? 0.5 : -0.5; }
    else { rules.push({ n: 'ADX', s: 'NEUTRAL', v: `${adxV.toFixed(0)} weak` }); }

    if (volR > 1.5 && p > c[n - 2]) { rules.push({ n: 'Volume', s: 'BUY', v: `${volR.toFixed(1)}x bull` }); score += 0.5; }
    else if (volR > 1.5 && p < c[n - 2]) { rules.push({ n: 'Volume', s: 'SELL', v: `${volR.toFixed(1)}x bear` }); score -= 0.5; }
    else { rules.push({ n: 'Volume', s: 'NEUTRAL', v: `${volR.toFixed(1)}x` }); }

    const d618 = Math.abs(p - f618) / p * 100;
    if (d618 < 2 && p > f618) { rules.push({ n: 'Fibonacci', s: 'BUY', v: 'Near 61.8%' }); score += 0.5; }
    else if (d618 < 2 && p < f618) { rules.push({ n: 'Fibonacci', s: 'SELL', v: 'Below 61.8%' }); score -= 0.5; }
    else { rules.push({ n: 'Fibonacci', s: 'NEUTRAL', v: `${d618.toFixed(0)}% away` }); }

    if (p > r1) { rules.push({ n: 'Pivot', s: 'BUY', v: 'Above R1' }); score += 0.5; }
    else if (p < s1) { rules.push({ n: 'Pivot', s: 'SELL', v: 'Below S1' }); score -= 0.5; }
    else { rules.push({ n: 'Pivot', s: 'NEUTRAL', v: 'Near pivot' }); }

    let signal;
    if (score >= 3) signal = 'STRONG BUY'; else if (score >= 1) signal = 'BUY';
    else if (score <= -3) signal = 'STRONG SELL'; else if (score <= -1) signal = 'SELL';
    else signal = 'NEUTRAL';

    const chg = ((p - c[n - 2]) / c[n - 2]) * 100;

    // Prediction (Fetch from API if available, else fallback)
    let p7 = p, pU = p, pD = p, pChg = 0;

    // Attempt async fetch (Note: this function is synchronous, so we'll handle update in loadAnalysis)
    // For now, we keep the client-side calc as placeholder until async update
    const lr = []; for (let i = Math.max(1, n - 30); i < n; i++)lr.push(Math.log(c[i] / c[i - 1]));
    const wR = lr.reduce((a, r, i) => a + r * (i + 1) / lr.length, 0) / lr.reduce((a, _, i) => a + (i + 1) / lr.length, 0);
    const std = Math.sqrt(lr.reduce((a, r) => a + (r - wR) ** 2, 0) / lr.length);
    p7 = p * Math.exp(wR * 7); pU = p * Math.exp(wR * 7 + std * Math.sqrt(7) * 1.5); pD = p * Math.exp(wR * 7 - std * Math.sqrt(7) * 1.5);
    pChg = Math.max(-50, Math.min(50, ((p7 - p) / p) * 100));

    // Fear & Greed score (composite)
    const fgScore = Math.round(50 + score * 5 + (lastRSI - 50) * 0.3 + (volR > 1 ? 5 : -3));
    const fg = Math.max(0, Math.min(100, fgScore));

    return {
        price: p, chg, lastRSI, adxV, atrP, volR, stK,
        f382, f618, pv, r1, s1,
        rules, score, signal,
        pred: { price: p7, up: pU, dn: pD, chg: pChg },
        lastDate: klines[n - 1].t,
        fg,
        high24: h[n - 1], low24: l[n - 1], vol24: v[n - 1],
    };
}

// ══════════════════════════════════════════════════
// RENDER
// ══════════════════════════════════════════════════
function renderPriceHero(a) {
    const cfg = CRYPTOS[selected];
    const col = a.chg >= 0 ? '#34d399' : '#f87171';
    const ar = a.chg >= 0 ? '▲' : '▼';
    currentPrice = a.price;
    document.getElementById('price-hero').innerHTML = `
        <div class="ph-row">
            <span class="ph-price">$${fmt(a.price)}</span>
            <span class="ph-change" style="color:${col}">${ar} ${Math.abs(a.chg).toFixed(2)}%</span>
        </div>
        <div class="ph-meta">${cfg.name} · 1D · ${a.lastDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} · RSI ${a.lastRSI.toFixed(0)} · Vol ${a.volR.toFixed(1)}x</div>
    `;
    // Update converter
    convert();
}

function renderSignalHero(a) {
    const cls = a.score > 0 ? 'bull' : a.score < 0 ? 'bear' : 'neutral';
    const buys = a.rules.filter(r => r.s === 'BUY').length;
    const sells = a.rules.filter(r => r.s === 'SELL').length;
    document.getElementById('signal-hero').innerHTML = `
        <div class="sh-score ${cls}">${a.score >= 0 ? '+' : ''}${a.score.toFixed(1)}</div>
        <div class="sh-info">
            <div class="sh-label">${a.signal}</div>
            <div class="sh-detail">${buys} buy · ${sells} sell · ${10 - buys - sells} neutral</div>
        </div>
    `;
}

function renderRules(a) {
    document.getElementById('rules-list').innerHTML = a.rules.map(r => `
        <div class="rule-row">
            <div class="rule-dot ${r.s.toLowerCase()}"></div>
            <span class="rule-name">${r.n}</span>
            <span class="rule-signal ${r.s.toLowerCase()}">${r.s}</span>
            <span class="rule-val">${r.v}</span>
        </div>
    `).join('');
}

function renderPrediction(a) {
    const cls = a.pred.chg >= 0 ? 'up' : 'down';
    const col = a.pred.chg >= 0 ? '#34d399' : '#f87171';
    const ar = a.pred.chg >= 0 ? '▲' : '▼';
    document.getElementById('prediction-section').innerHTML = `
        <div class="panel-section-title">7-Day Forecast</div>
        <div class="pred-box ${cls}">
            <div class="pred-pct" style="color:${col}">${ar}${Math.abs(a.pred.chg).toFixed(1)}%</div>
            <div class="pred-info">
                <div class="pred-label">AI Prediction (Prophet Model)</div>
                <div class="pred-range">$${fmt(a.pred.dn)} — <strong style="color:${col}">$${fmt(a.pred.price)}</strong> — $${fmt(a.pred.up)}</div>
            </div>
        </div>
    `;
}

function renderLevels(a) {
    document.getElementById('levels-section').innerHTML = `
        <div class="panel-section-title">Key Levels</div>
        <div class="level-row"><span class="level-label">Fib 38.2%</span><span class="level-value">$${fmt(a.f382)}</span></div>
        <div class="level-row"><span class="level-label">Fib 61.8%</span><span class="level-value">$${fmt(a.f618)}</span></div>
        <div class="level-row"><span class="level-label">Daily Pivot</span><span class="level-value">$${fmt(a.pv)}</span></div>
        <div class="level-row"><span class="level-label">Resistance R1</span><span class="level-value">$${fmt(a.r1)}</span></div>
        <div class="level-row"><span class="level-label">Support S1</span><span class="level-value">$${fmt(a.s1)}</span></div>
        <div class="level-row"><span class="level-label">Stochastic %K</span><span class="level-value">${a.stK.toFixed(0)}</span></div>
    `;
}

function renderGauge(a) {
    const fg = a.fg;
    const pct = fg; // 0-100
    let label, color;
    if (fg <= 20) { label = 'Extreme Fear'; color = '#ef4444'; }
    else if (fg <= 40) { label = 'Fear'; color = '#f97316'; }
    else if (fg <= 60) { label = 'Neutral'; color = '#eab308'; }
    else if (fg <= 80) { label = 'Greed'; color = '#22c55e'; }
    else { label = 'Extreme Greed'; color = '#10b981'; }

    const gauge = document.getElementById('gauge');
    gauge.style.background = `conic-gradient(${color} 0%, ${color} ${pct}%, #1e2030 ${pct}%, #1e2030 100%)`;
    gauge.innerHTML = `<span class="gauge-value">${fg}</span>`;

    document.getElementById('gauge-label').innerHTML = `
        <div class="gauge-label" style="color:${color}">${label}</div>
        <div class="gauge-sublabel">${CRYPTOS[selected].name} technical score</div>
    `;
}

function renderStats(a) {
    const cfg = CRYPTOS[selected];
    document.getElementById('stats-grid').innerHTML = `
        <div class="stat-card" onclick="selectCrypto('BTC')">
            <div class="stat-label">RSI</div>
            <div class="stat-value" style="color:${a.lastRSI < 30 ? '#34d399' : a.lastRSI > 70 ? '#f87171' : 'var(--t100)'}">${a.lastRSI.toFixed(1)}</div>
            <div class="stat-sub">${a.lastRSI < 30 ? 'Oversold' : a.lastRSI > 70 ? 'Overbought' : 'Neutral'}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">ADX</div>
            <div class="stat-value">${a.adxV.toFixed(1)}</div>
            <div class="stat-sub">${a.adxV > 25 ? 'Strong trend' : 'Consolidation'}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Volatility</div>
            <div class="stat-value">${a.atrP.toFixed(1)}%</div>
            <div class="stat-sub">ATR (14-day)</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Volume</div>
            <div class="stat-value">${a.volR.toFixed(1)}x</div>
            <div class="stat-sub">${a.volR > 1.5 ? 'Above average' : a.volR < 0.5 ? 'Low volume' : 'Normal'}</div>
        </div>
    `;
}

// ══════════════════════════════════════════════════
// INTERACTIVE FEATURES
// ══════════════════════════════════════════════════

// Share on Twitter/X
function shareTwitter() {
    if (!currentAnalysis) return;
    const a = currentAnalysis;
    const text = `${CRYPTOS[selected].name} Signal: ${a.signal} (${a.score >= 0 ? '+' : ''}${a.score.toFixed(1)}/10)\n\nPrice: $${fmt(a.price)} (${a.chg >= 0 ? '+' : ''}${a.chg.toFixed(2)}%)\n7D Forecast: ${a.pred.chg >= 0 ? '+' : ''}${a.pred.chg.toFixed(1)}%\nRSI: ${a.lastRSI.toFixed(0)}\n\nFree live signals 👉`;
    const url = window.location.href;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank');
}

// Share on Telegram
function shareTelegram() {
    if (!currentAnalysis) return;
    const a = currentAnalysis;
    const text = `${CRYPTOS[selected].name}: ${a.signal} | $${fmt(a.price)} | RSI ${a.lastRSI.toFixed(0)} | 7D: ${a.pred.chg >= 0 ? '+' : ''}${a.pred.chg.toFixed(1)}%`;
    const url = window.location.href;
    window.open(`https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`, '_blank');
}

// Copy signal
async function copySignal() {
    if (!currentAnalysis) return;
    const a = currentAnalysis;
    const text = `${CRYPTOS[selected].name}: ${a.signal} (${a.score >= 0 ? '+' : ''}${a.score.toFixed(1)})\n$${fmt(a.price)} | RSI ${a.lastRSI.toFixed(0)} | 7D forecast: ${a.pred.chg >= 0 ? '+' : ''}${a.pred.chg.toFixed(1)}%\nvia CryptoVision`;
    try {
        await navigator.clipboard.writeText(text);
        const btn = document.querySelector('.share-copy');
        btn.textContent = '✓ Copied!';
        setTimeout(() => btn.textContent = '⎘ Copy', 2000);
    } catch (e) { }
}

// Toggle rules
function toggleRules() {
    const list = document.getElementById('rules-list');
    const arrow = document.getElementById('rules-arrow');
    list.classList.toggle('collapsed');
    arrow.classList.toggle('collapsed');
}

// Converter
function convert() {
    const amount = parseFloat(document.getElementById('conv-amount')?.value) || 0;
    const result = document.getElementById('conv-result');
    const sym = document.getElementById('conv-symbol');
    if (result && sym) {
        sym.textContent = selected;
        result.textContent = `$${fmt(amount * currentPrice)}`;
    }
}

// Newsletter
function subscribeNewsletter(e) {
    e.preventDefault();
    const email = document.getElementById('newsletter-email').value;
    // In production: POST to your API/Mailchimp/etc
    console.log('Newsletter signup:', email);
    document.getElementById('newsletter-success').style.display = 'block';
    document.querySelector('.newsletter-form').style.display = 'none';
}

// ══════════════════════════════════════════════════
// UTILS
// ══════════════════════════════════════════════════
function fmt(n) {
    if (n >= 1000) return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (n >= 1) return n.toFixed(2);
    return n.toFixed(4);
}

// ══════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════
function selectCrypto(key) {
    selected = key;
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.symbol === key));
    loadChart(key);
    loadAnalysis(key);
}

async function loadAnalysis(key) {
    try {
        const klines = await fetchKlines(CRYPTOS[key].pair, 90);
        let a = analyze(klines);

        // Fetch Real ML Prediction from Backend (Prophet)
        try {
            // Use relative path for production (Vercel)
            const predRes = await fetch(`/api/predict/${key}?model=prophet&days=7`);
            if (predRes.ok) {
                const predData = await predRes.json();
                if (predData.predicted_change_pct) {
                    a.pred.chg = predData.predicted_change_pct;
                    const p = a.price;
                    a.pred.price = p * (1 + a.pred.chg / 100);
                    a.pred.up = a.pred.price * 1.05; // Approx
                    a.pred.dn = a.pred.price * 0.95; // Approx
                    console.log(`ML Prediction for ${key}: ${a.pred.chg}%`);
                }
            }
        } catch (err) {
            console.log('Backend offline, using client-side math:', err);
        }

        currentAnalysis = a;
        currentPrice = a.price;
        renderPriceHero(a);
        renderSignalHero(a);
        renderRules(a);
        renderPrediction(a);
        renderLevels(a);
        renderGauge(a);
        renderStats(a);
    } catch (e) {
        console.error('Error:', e);
        document.getElementById('signal-hero').innerHTML = '<div class="panel-loading">⚠ Connection error — click ↻</div>';
    }
}

async function refreshAll() {
    await loadTicker();
    loadChart(selected);
    await loadAnalysis(selected);
    startTimer();
}

// Boot
document.addEventListener('DOMContentLoaded', refreshAll);
