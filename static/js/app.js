// Nifty100 App JS - AJAX utilities and handlers
// API base URL
const API_BASE = '/api/';

// Fetch wrapper with error handling
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return response.json();
}

// Screener AJAX handler
function initScreener() {
  const form = document.querySelector('.filter-bar form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const params = new URLSearchParams(formData).toString();
    
    try {
      const data = await apiFetch(`screener/?${params}`);
      updateScreenerTable(data);
    } catch (err) {
      console.error('Screener fetch failed', err);
    }
  });
}

// Update screener table with API data
function updateScreenerTable(companies) {
  const tbody = document.querySelector('.leaderboard-table tbody');
  if (!tbody) return;
  
  tbody.innerHTML = companies.map((c, idx) => `
    <tr onclick="window.location='/company/${c.symbol}/'">
      <td>${idx + 1}</td>
      <td><a href="/company/${c.symbol}/">${c.symbol}</a></td>
      <td>${c.company_name}</td>
      <td><span class="sector-tag">${c.sector_name}</span></td>
      <td>${c.face_value || '—'}</td>
      <td>${c.book_value || '—'}</td>
      <td class="${c.roce_percentage > 15 ? 'positive' : ''}">${c.roce_percentage || '—'}%</td>
      <td class="${c.roe_percentage > 15 ? 'positive' : ''}">${c.roe_percentage || '—'}%</td>
      <td class="score-cell">${c.latest_score || '—'}</td>
      <td><span class="health-badge health-${c.health_label?.toLowerCase()}">${c.health_label || ''}</span></td>
    </tr>
  `).join('') || '<tr><td colspan="10">No matches</td></tr>';
}

// Compare handler
function initCompare() {
  const form = document.querySelector('.compare-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const params = new URLSearchParams(formData).toString().replace(/sym1=/, 'sym=').replace(/sym2=/, 'sym=');
    
    try {
      const data = await apiFetch(`compare/?${params}`);
      updateCompareGrid(data);
    } catch (err) {
      console.error('Compare fetch failed', err);
    }
  });
}

function updateCompareGrid(companies) {
  // Update compare.html grid with companies data
  console.log('Update compare with:', companies);
}

// Init on DOM load
document.addEventListener('DOMContentLoaded', () => {
  initScreener();
  initCompare();
  
  // Profit/Loss enhanced display (e.g., modals)
  // TODO: Add click handlers for expandable rows
});
