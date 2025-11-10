const { ipcRenderer } = require('electron');
const axios = require('axios');

const API_BASE = 'http://127.0.0.1:8765';

const searchInput = document.getElementById('searchInput');
const resultsDiv = document.getElementById('results');
const statusDiv = document.getElementById('status');

let selectedIndex = 0;
let currentResults = [];

// debounce for search
let searchTimeout;

searchInput.addEventListener('input', (e) => {
  clearTimeout(searchTimeout);
  const query = e.target.value.trim();

  if (!query) {
    resultsDiv.innerHTML = '';
    return;
  }

  // debounce 300ms
  searchTimeout = setTimeout(() => {
    searchCommand(query);
  }, 300);
});

searchInput.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    ipcRenderer.send('hide-window');
    searchInput.value = '';
    resultsDiv.innerHTML = '';
  }

  if (e.key === 'ArrowDown') {
    e.preventDefault();
    selectedIndex = Math.min(selectedIndex + 1, currentResults.length - 1);
    renderResults();
  }

  if (e.key === 'ArrowUp') {
    e.preventDefault();
    selectedIndex = Math.max(selectedIndex - 1, 0);
    renderResults();
  }

  if (e.key === 'Enter') {
    e.preventDefault();
    executeSelected();
  }
});

async function searchCommand(query) {
  showStatus('searching...');

  try {
    const response = await axios.post(`${API_BASE}/command`, {
      query: query,
      auto_execute: false
    });

    const data = response.data;

    currentResults = [];

    // build results
    if (data.matched_command) {
      currentResults.push({
        title: `▶ ${data.matched_command}`,
        desc: `run existing command`,
        type: 'matched',
        data: data
      });
    } else if (data.generated) {
      currentResults.push({
        title: `✨ new command generated`,
        desc: `press enter to run`,
        type: 'generated',
        data: data
      });
    } else {
      currentResults.push({
        title: `🤖 ${data.intent.action}`,
        desc: `press enter to generate & run`,
        type: 'intent',
        data: data
      });
    }

    selectedIndex = 0;
    renderResults();
    hideStatus();

  } catch (err) {
    showStatus('error: backend not running?');
    console.error(err);
  }
}

function renderResults() {
  resultsDiv.innerHTML = '';

  currentResults.forEach((result, idx) => {
    const div = document.createElement('div');
    div.className = 'result-item' + (idx === selectedIndex ? ' selected' : '');

    div.innerHTML = `
      <div class="title">${result.title}</div>
      <div class="desc">${result.desc}</div>
    `;

    div.onclick = () => {
      selectedIndex = idx;
      executeSelected();
    };

    resultsDiv.appendChild(div);
  });
}

async function executeSelected() {
  if (currentResults.length === 0) return;

  const selected = currentResults[selectedIndex];
  showStatus('executing...');

  try {
    const response = await axios.post(`${API_BASE}/command`, {
      query: searchInput.value,
      auto_execute: true
    });

    const data = response.data;

    if (data.executed) {
      showStatus(`✓ done: ${data.output || 'success'}`);
      setTimeout(() => {
        ipcRenderer.send('hide-window');
        searchInput.value = '';
        resultsDiv.innerHTML = '';
        hideStatus();
      }, 1500);
    } else {
      showStatus('✗ execution failed');
    }

  } catch (err) {
    showStatus('error during execution');
    console.error(err);
  }
}

function showStatus(msg) {
  statusDiv.textContent = msg;
  statusDiv.classList.add('show');
}

function hideStatus() {
  statusDiv.classList.remove('show');
}

// focus input when window shows
window.addEventListener('focus', () => {
  searchInput.focus();
  searchInput.select();
});
