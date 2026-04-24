import { loadJson, escapeHtml } from './utils.js';

async function init() {
  const products = await loadJson('src/data/products.json');
  document.getElementById('product-grid').innerHTML = products
    .map(
      (p) => `<article class="card"><span class="badge">${escapeHtml(p.badge)}</span><h3>${escapeHtml(p.name)}</h3><p>ประเภท: ${escapeHtml(p.category)}</p><p>เหมาะกับ: ${escapeHtml(p.bestFor.join(', '))}</p><p>จุดเด่น: ${escapeHtml(p.highlight)}</p><p>ข้อควรระวัง: ${escapeHtml(p.notFor.join(', '))}</p><p>ช่วงราคา: ${escapeHtml(p.priceRange)} บาท</p><p>แนะนำโดย: ${escapeHtml(p.characterRecommend)}</p><a class="btn btn-primary" href="${escapeHtml(p.affiliateUrl)}" target="_blank" rel="noopener noreferrer">ดูใน Shopee</a></article>`
    )
    .join('');
}

init();
