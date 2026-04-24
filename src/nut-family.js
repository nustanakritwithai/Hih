import { loadJson, escapeHtml } from './utils.js';

async function init() {
  const characters = await loadJson('src/data/characters.json');
  document.getElementById('character-grid').innerHTML = characters
    .map(
      (c) => `<article class="card"><h3>${escapeHtml(c.name)}</h3><p><strong>${escapeHtml(c.role)}</strong></p><p>บุคลิก: ${escapeHtml(c.personality)}</p><p>รับผิดชอบ: ${escapeHtml(c.topics)}</p></article>`
    )
    .join('');
}

init();
