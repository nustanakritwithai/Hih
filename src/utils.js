export async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`โหลดข้อมูลไม่สำเร็จ: ${path}`);
  return res.json();
}

export function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
