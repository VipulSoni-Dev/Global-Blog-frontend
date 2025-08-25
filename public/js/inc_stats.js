(function () {
  const CSV_URL = 'https://stooq.com/q/d/l/?s=intc.us&i=d'; // daily OHLCV CSV
  const statsEl = document.getElementById('intc-stats-content');
  const canvas = document.getElementById('intc-canvas');
  if (!statsEl || !canvas) return;
  const ctx = canvas.getContext('2d');

  const fmt = n => '$' + n.toFixed(2);
  const pct = n => (n >= 0 ? '+' : '') + n.toFixed(1) + '%';

  function parseCSV(text) {
    const lines = text.trim().split('\n');
    const header = (lines.shift() || '').split(',');
    const col = k => header.indexOf(k);
    return lines.map(line => {
      const c = line.split(',');
      return {
        date: c[col('Date')],
        open: Number(c[col('Open')]),
        high: Number(c[col('High')]),
        low: Number(c[col('Low')]),
        close: Number(c[col('Close')]),
        volume: Number(c[col('Volume')])
      };
    });
  }

  function computeStats(series) {
    const closes = series.map(d => d.close);
    const start = closes[0], end = closes[closes.length - 1];
    const high = Math.max(...closes), low = Math.min(...closes);
    const totalReturn = (end / start - 1) * 100;
    const cagr = (Math.pow(end / start, 1/5) - 1) * 100;

    let peak = closes[0], maxDD = 0;
    for (const c of closes) { if (c > peak) peak = c; const dd = (c/peak - 1) * 100; if (dd < maxDD) maxDD = dd; }

    const rets = [];
    for (let i = 1; i < closes.length; i++) rets.push(Math.log(closes[i]/closes[i-1]));
    const mean = rets.reduce((a,b)=>a+b,0) / (rets.length || 1);
    const variance = rets.reduce((a,b)=>a + Math.pow(b - mean, 2), 0) / (rets.length > 1 ? (rets.length - 1) : 1);
    const annVol = Math.sqrt(variance) * Math.sqrt(252) * 100;

    return { start, end, high, low, totalReturn, cagr, maxDD, annVol };
  }

  function renderStats(s) {
    statsEl.innerHTML = `
      <ul>
        <li><strong>Start Price (≈5y ago):</strong> ${fmt(s.start)}</li>
        <li><strong>Latest Price:</strong> ${fmt(s.end)}</li>
        <li><strong>5-Year High:</strong> ${fmt(s.high)}</li>
        <li><strong>5-Year Low:</strong> ${fmt(s.low)}</li>
        <li><strong>Total Return (5y):</strong> ${pct(s.totalReturn)}</li>
        <li><strong>CAGR (≈):</strong> ${pct(s.cagr)}</li>
        <li><strong>Max Drawdown:</strong> ${pct(s.maxDD)}</li>
        <li><strong>Realized Volatility (ann.):</strong> ${s.annVol.toFixed(1)}%</li>
      </ul>
    `;
  }

  function drawLine(series) {
    // responsive sizing
    const wrap = document.getElementById('intc-canvas-wrap');
    if (wrap) {
      const w = Math.max(360, wrap.clientWidth - 32);
      const ratio = window.devicePixelRatio || 1;
      canvas.style.width = w + 'px';
      canvas.width = Math.floor(w * ratio);
      canvas.height = Math.floor(360 * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    }
    const padding = { left: 48, right: 12, top: 16, bottom: 28 };
    const W = canvas.width / (window.devicePixelRatio || 1);
    const H = canvas.height / (window.devicePixelRatio || 1);
    const plotW = W - padding.left - padding.right;
    const plotH = H - padding.top - padding.bottom;

    const closes = series.map(d => d.close);
    const min = Math.min(...closes), max = Math.max(...closes);
    const x = i => padding.left + (i / (series.length - 1)) * plotW;
    const y = v => padding.top + (1 - (v - min) / (max - min || 1)) * plotH;

    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = '#e5e7eb'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(padding.left, padding.top); ctx.lineTo(padding.left, H - padding.bottom); ctx.lineTo(W - padding.right, H - padding.bottom); ctx.stroke();

    ctx.fillStyle = '#6b7280'; ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto, sans-serif';
    for (let t = 0; t <= 5; t++) {
      const v = min + (t/5)*(max - min); const yy = y(v);
      ctx.strokeStyle = '#f3f4f6'; ctx.beginPath(); ctx.moveTo(padding.left, yy); ctx.lineTo(W - padding.right, yy); ctx.stroke();
      ctx.fillText('$' + v.toFixed(0), 6, yy + 4);
    }

    ctx.strokeStyle = '#2563eb'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x(0), y(closes[0]));
    for (let i = 1; i < series.length; i++) ctx.lineTo(x(i), y(closes[i]));
    ctx.stroke();

    const lastX = x(series.length - 1), lastY = y(closes[closes.length - 1]);
    ctx.fillStyle = '#111827'; ctx.beginPath(); ctx.arc(lastX, lastY, 3.
