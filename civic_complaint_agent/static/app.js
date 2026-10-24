// ==========================================================================
// NagarSathi — Civic Complaint Agent Client Controller
// ==========================================================================

const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

// Helper to escape HTML characters
function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[c]));
}

// Toast notification helper
function showToast(message, type = 'info') {
  const container = $('#toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '⚠️' : 'ℹ️'}</span><span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}

// ==========================================================================
// File Upload & Drag-and-Drop Handling
// ==========================================================================
const dropZone = $('#dropZone');
const photoInput = $('#photo');
const dropPrompt = $('#dropPrompt');
const previewContainer = $('#previewContainer');
const previewImg = $('#previewImg');
const previewName = $('#previewName');
const removePhotoBtn = $('#removePhotoBtn');

function handleFileSelection(file) {
  if (!file) return;
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    showToast('Please select a JPG, PNG, or WEBP image.', 'error');
    return;
  }
  if (file.size > 8 * 1024 * 1024) {
    showToast('Photograph is too large. Maximum size is 8 MB.', 'error');
    return;
  }

  const url = URL.createObjectURL(file);
  previewImg.src = url;
  previewName.textContent = `${file.name} (${(file.size / 1024).toFixed(0)} KB)`;
  dropPrompt.style.display = 'none';
  previewContainer.style.display = 'flex';
}

dropZone.addEventListener('click', e => {
  if (e.target !== removePhotoBtn) {
    photoInput.click();
  }
});

photoInput.addEventListener('change', e => {
  if (e.target.files && e.target.files[0]) {
    handleFileSelection(e.target.files[0]);
  }
});

removePhotoBtn.addEventListener('click', e => {
  e.stopPropagation();
  photoInput.value = '';
  previewImg.src = '';
  previewContainer.style.display = 'none';
  dropPrompt.style.display = 'flex';
});

// Drag and drop events
['dragenter', 'dragover'].forEach(name => {
  dropZone.addEventListener(name, e => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });
});

['dragleave', 'drop'].forEach(name => {
  dropZone.addEventListener(name, e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
  });
});

dropZone.addEventListener('drop', e => {
  const dt = e.dataTransfer;
  if (dt && dt.files && dt.files[0]) {
    photoInput.files = dt.files;
    handleFileSelection(dt.files[0]);
  }
});

// ==========================================================================
// 1-Click Demo Presets Generator
// ==========================================================================
const PRESETS = {
  pothole: {
    category: 'pothole',
    area: 'Navrangpura',
    note: 'Deep asphalt depression near Commerce Six Roads, dangerous for two-wheelers.',
    title: 'Sample Pothole',
    color: '#34495e'
  },
  garbage: {
    category: 'garbage',
    area: 'Satellite',
    note: 'Unattended overflow of solid waste near Jodhpur crossroad collection bin.',
    title: 'Sample Waste Pile',
    color: '#795548'
  },
  streetlight: {
    category: 'streetlight',
    area: 'Maninagar',
    note: 'Pole #14 flickering and completely dark at night near Kankaria gate.',
    title: 'Sample Streetlight',
    color: '#f39c12'
  },
  waterlogging: {
    category: 'waterlogging',
    area: 'Bodakdev',
    note: 'Storm water drain blocked; knee-deep stagnant water after morning rain.',
    title: 'Sample Waterlogging',
    color: '#2980b9'
  }
};

function createSampleImageBlob(title, color) {
  const canvas = document.createElement('canvas');
  canvas.width = 600;
  canvas.height = 400;
  const ctx = canvas.getContext('2d');

  // Background
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, 600, 400);

  // Road / urban pattern
  ctx.fillStyle = '#222222';
  ctx.fillRect(0, 240, 600, 160);

  ctx.strokeStyle = '#ffffff';
  ctx.setLineDash([20, 15]);
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(0, 320);
  ctx.lineTo(600, 320);
  ctx.stroke();

  // Watermark text
  ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
  ctx.font = 'bold 32px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(`AMC Demo: ${title}`, 300, 180);

  ctx.font = '16px sans-serif';
  ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
  ctx.fillText('NagarSathi Civic Issue Simulation Photo', 300, 215);

  return new Promise(resolve => {
    canvas.toBlob(blob => {
      resolve(new File([blob], `${title.toLowerCase().replace(/\s+/g, '_')}.jpg`, { type: 'image/jpeg' }));
    }, 'image/jpeg', 0.9);
  });
}

$$('.preset-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const key = btn.dataset.preset;
    const p = PRESETS[key];
    if (!p) return;

    $('#issue_type').value = p.category;
    $('#area').value = p.area;
    $('#note').value = p.note;
    hideLocalitySuggestions();

    try {
      const sampleFile = await createSampleImageBlob(p.title, p.color);
      const dt = new DataTransfer();
      dt.items.add(sampleFile);
      photoInput.files = dt.files;
      handleFileSelection(sampleFile);
      showToast(`Loaded ${p.title} (${p.area}) preset.`, 'success');
    } catch (err) {
      console.warn('Preset blob generation:', err);
    }
  });
});

// ==========================================================================
// Interactive Locality Fallback (Section 3.C)
// ==========================================================================
const suggestionsBox = $('#localitySuggestions');
const suggestionMsg = $('#suggestionMsg');
const suggestionPills = $('#suggestionPills');

function showLocalitySuggestions(message, suggestions) {
  suggestionMsg.textContent = message || 'Locality not found in mock AMC directory. Quick select your ward:';
  suggestionPills.innerHTML = '';
  
  const wards = suggestions || ['Navrangpura', 'Maninagar', 'Satellite', 'Bodakdev', 'Paldi'];
  wards.forEach(w => {
    const pill = document.createElement('button');
    pill.type = 'button';
    pill.className = 'ward-pill';
    pill.textContent = `📍 ${w}`;
    pill.onclick = () => {
      $('#area').value = w;
      hideLocalitySuggestions();
      $('#area').focus();
      showToast(`Selected AMC Ward: ${w}`, 'success');
    };
    suggestionPills.appendChild(pill);
  });

  suggestionsBox.style.display = 'block';
  suggestionsBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideLocalitySuggestions() {
  suggestionsBox.style.display = 'none';
}

$('#area').addEventListener('input', () => {
  hideLocalitySuggestions();
});

// ==========================================================================
// Agent Pipeline Visualizer
// ==========================================================================
const pipeline = $('#agentPipeline');
const step1 = $('#pipeStep1');
const step2 = $('#pipeStep2');
const step3 = $('#pipeStep3');
const step4 = $('#pipeStep4');

function resetPipeline() {
  [step1, step2, step3, step4].forEach((s, idx) => {
    s.className = 'pipeline-step';
    s.querySelector('.step-status').textContent = '⏳';
  });
}

function updatePipelineStep(stepEl, status) {
  if (status === 'active') {
    stepEl.className = 'pipeline-step active';
    stepEl.querySelector('.step-status').textContent = '⚡';
  } else if (status === 'completed') {
    stepEl.className = 'pipeline-step completed';
    stepEl.querySelector('.step-status').textContent = '✓';
  }
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ==========================================================================
// Complaint Form Submission
// ==========================================================================
const complaintForm = $('#complaintForm');
const submitBtn = $('#submitBtn');
const resultArea = $('#result');

complaintForm.addEventListener('submit', async e => {
  e.preventDefault();
  hideLocalitySuggestions();
  resultArea.innerHTML = '';

  const areaVal = $('#area').value.trim();
  const issueVal = $('#issue_type').value;

  if (!issueVal) {
    showToast('Please select or confirm an issue category.', 'error');
    $('#issue_type').focus();
    return;
  }
  if (!areaVal) {
    showToast('Please enter an area or locality.', 'error');
    $('#area').focus();
    return;
  }

  // Visual agent workflow animation
  submitBtn.disabled = true;
  pipeline.style.display = 'block';
  resetPipeline();

  try {
    // Step 1: Vision / Analysis
    updatePipelineStep(step1, 'active');
    await sleep(250);
    updatePipelineStep(step1, 'completed');

    // Step 2: Ward Resolution
    updatePipelineStep(step2, 'active');
    await sleep(200);

    const formData = new FormData(complaintForm);
    const response = await fetch('/api/complaints', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      if (data.suggestions) {
        showLocalitySuggestions(data.error, data.suggestions);
      }
      throw new Error(data.error || 'Failed to submit complaint');
    }

    updatePipelineStep(step2, 'completed');

    // Step 3: Department Routing
    updatePipelineStep(step3, 'active');
    await sleep(200);
    updatePipelineStep(step3, 'completed');

    // Step 4: Ticket Issuance
    updatePipelineStep(step4, 'active');
    await sleep(200);
    updatePipelineStep(step4, 'completed');

    const ticket = data.ticket;
    renderComplaintResult(ticket);
    showToast('Complaint successfully lodged!', 'success');

    // Pre-populate tracking box and refresh list
    $('#tracking').value = ticket.tracking_id;
    fetchRecentTickets();

  } catch (err) {
    resultArea.innerHTML = `<div class="error-banner" style="background:#fde8e8; border:1px solid #fed7d7; color:#9b2c2c; padding:14px; border-radius:10px; margin-top:14px; font-size:0.85rem;">
      <strong>⚠️ Submission Issue:</strong> ${escapeHtml(err.message)}
    </div>`;
  } finally {
    submitBtn.disabled = false;
    setTimeout(() => {
      pipeline.style.display = 'none';
    }, 1200);
  }
});

// ==========================================================================
// Render Complaint Result Card (With Disagreement Alert)
// ==========================================================================
function renderComplaintResult(ticket) {
  const isDisagreement = ticket.has_disagreement;

  const disagreementHtml = isDisagreement ? `
    <div class="disagreement-card">
      <b>⚠️ Category Disagreement Transparently Handled (Section 3.B)</b>
      ${escapeHtml(ticket.disagreement_explanation || 'Resident selection prioritized over AI prediction for reliable routing.')}
    </div>
  ` : '';

  resultArea.innerHTML = `
    <div class="result-card">
      <div class="result-badge-row">
        <span class="ticket-status-pill ticket-status-submitted">${escapeHtml(ticket.status)}</span>
        <span style="font-size:0.75rem; color:#5e7068;">Local Mock AMC Store</span>
      </div>

      <div class="ticket-number-box">
        <div>
          <span class="ticket-number-label">Tracking Identification</span>
          <div class="ticket-number">${escapeHtml(ticket.tracking_id)}</div>
        </div>
        <button type="button" class="btn-copy" id="copyResultIdBtn">
          📋 Copy
        </button>
      </div>

      ${disagreementHtml}

      <div class="ticket-details-grid">
        <div class="detail-item">
          <span>Final Issue Category</span>
          <strong>${escapeHtml(ticket.issue_type.toUpperCase())}</strong>
        </div>
        <div class="detail-item">
          <span>Assigned AMC Ward</span>
          <strong>${escapeHtml(ticket.ward_name)} (${escapeHtml(ticket.ward_id)})</strong>
        </div>
        <div class="detail-item">
          <span>Routed Department</span>
          <strong>${escapeHtml(ticket.department)}</strong>
        </div>
        <div class="detail-item">
          <span>Lodged Locality</span>
          <strong>${escapeHtml(ticket.area)}</strong>
        </div>
      </div>

      <div class="analysis-tag-box">
        <span>🤖 Analysis Engine: <strong>${escapeHtml(ticket.analysis.mode)}</strong></span>
        ${ticket.analysis.warning ? `<span style="color:#d97706">· ${escapeHtml(ticket.analysis.warning)}</span>` : ''}
      </div>

      <button type="button" class="btn-advance-status" id="trackNowBtn" style="margin-top:16px;">
        🔍 Track this complaint in live status monitor →
      </button>
    </div>
  `;

  // Copy tracking ID handler
  $('#copyResultIdBtn').onclick = () => {
    navigator.clipboard?.writeText(ticket.tracking_id);
    showToast('Tracking ID copied to clipboard!', 'success');
  };

  // Quick switch to tracking panel
  $('#trackNowBtn').onclick = () => {
    $('#tracking').value = ticket.tracking_id;
    lookupStatus(ticket.tracking_id);
    $('#trackPanel').scrollIntoView({ behavior: 'smooth' });
  };
}

// ==========================================================================
// Status Lookup & 4-Stage Lifecycle Progression
// ==========================================================================
const statusForm = $('#statusForm');
const statusResult = $('#statusResult');

statusForm.addEventListener('submit', e => {
  e.preventDefault();
  const id = $('#tracking').value.trim();
  if (id) {
    lookupStatus(id);
  }
});

async function lookupStatus(trackingId) {
  statusResult.innerHTML = '<p class="empty-state">Fetching status from local database...</p>';
  try {
    const res = await fetch(`/api/status/${encodeURIComponent(trackingId)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Tracking ID not found.');

    renderStatusCard(data.ticket);
  } catch (err) {
    statusResult.innerHTML = `
      <div style="background:#fff1f0; border:1px solid #ffa39e; color:#cf1322; padding:12px; border-radius:8px; font-size:0.85rem; margin-top:10px;">
        ⚠️ ${escapeHtml(err.message)}
      </div>
    `;
  }
}

function renderStatusCard(ticket) {
  const stages = [
    { key: 'Submitted (mock)', label: 'Submitted' },
    { key: 'Assigned to Ward Engineer', label: 'Assigned' },
    { key: 'In Progress', label: 'In Progress' },
    { key: 'Resolved', label: 'Resolved' }
  ];

  const currentStatus = ticket.status || 'Submitted (mock)';
  let currentIdx = stages.findIndex(s => s.key.toLowerCase() === currentStatus.toLowerCase());
  if (currentIdx === -1) currentIdx = 0;

  // Timeline markup
  const timelineHtml = `
    <div class="lifecycle-timeline">
      ${stages.map((st, i) => {
        let cls = '';
        if (i < currentIdx) cls = 'passed';
        else if (i === currentIdx) cls = 'current';
        return `
          <div class="timeline-step ${cls}">
            <div class="step-marker">${i < currentIdx ? '✓' : i + 1}</div>
            <span class="step-name">${st.label}</span>
          </div>
        `;
      }).join('')}
    </div>
  `;

  // Status history list
  const history = ticket.status_history || [];
  const historyHtml = history.map(h => `
    <div class="history-item">
      <span class="history-dot"></span>
      <div class="history-content">
        <div class="history-status">${escapeHtml(h.status)}</div>
        <div class="history-note">${escapeHtml(h.note || '')}</div>
        <div class="history-time">${escapeHtml(new Date(h.at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))} · ${escapeHtml(new Date(h.at).toLocaleDateString())}</div>
      </div>
    </div>
  `).reverse().join('');

  statusResult.innerHTML = `
    <div class="result-card" style="margin-top:12px;">
      <div class="result-badge-row">
        <span class="ticket-status-pill ticket-status-${currentIdx === 3 ? 'resolved' : currentIdx === 2 ? 'progress' : currentIdx === 1 ? 'assigned' : 'submitted'}">
          ${escapeHtml(ticket.status)}
        </span>
        <small style="color:#5e7068;">Logged: ${escapeHtml(new Date(ticket.created_at).toLocaleDateString())}</small>
      </div>

      <h4 style="font-family:var(--font-display); font-size:1.15rem; color:var(--text-main); margin-bottom:4px;">
        ${escapeHtml(ticket.tracking_id)}
      </h4>

      <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:12px;">
        ${escapeHtml(ticket.description || 'Civic issue in local registry.')}
      </p>

      ${timelineHtml}

      <div class="ticket-details-grid" style="margin-top:16px;">
        <div class="detail-item">
          <span>Assigned Ward</span>
          <strong>${escapeHtml(ticket.ward_name)}</strong>
        </div>
        <div class="detail-item">
          <span>AMC Department</span>
          <strong>${escapeHtml(ticket.department)}</strong>
        </div>
        <div class="detail-item">
          <span>Locality</span>
          <strong>${escapeHtml(ticket.area)}</strong>
        </div>
        <div class="detail-item">
          <span>Routing Logic</span>
          <strong>${escapeHtml(ticket.routing_explanation || 'Category routing')}</strong>
        </div>
      </div>

      <!-- Advance Lifecycle Simulator Button (Key for hackathon demonstration) -->
      <button type="button" class="btn-advance-status" id="advanceStatusBtn" title="Simulate advancing municipal complaint status">
        ⏩ Advance Status (Demo Simulator)
      </button>

      <!-- Audit History -->
      <div class="history-list">
        <div style="font-size:0.75rem; font-weight:700; color:var(--text-muted); margin-bottom:4px;">STATUS AUDIT TRAIL:</div>
        ${historyHtml}
      </div>
    </div>
  `;

  $('#advanceStatusBtn').onclick = async () => {
    try {
      const res = await fetch(`/api/status/${encodeURIComponent(ticket.tracking_id)}/advance`, {
        method: 'POST'
      });
      const updated = await res.json();
      if (!res.ok) throw new Error(updated.error || 'Could not advance status');
      showToast(updated.message || 'Status advanced!', 'success');
      renderStatusCard(updated.ticket);
      fetchRecentTickets();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };
}

// ==========================================================================
// Recent Tickets Community Feed
// ==========================================================================
async function fetchRecentTickets() {
  const container = $('#recentTicketsList');
  const countBadge = $('#ticketCountBadge');

  try {
    const res = await fetch('/api/tickets');
    const data = await res.json();
    const tickets = data.tickets || [];

    countBadge.textContent = `${tickets.length} Report${tickets.length === 1 ? '' : 's'}`;

    if (tickets.length === 0) {
      container.innerHTML = '<p class="empty-state">No mock tickets filed yet in this session. Submit your first complaint above!</p>';
      return;
    }

    container.innerHTML = tickets.map(t => {
      const statusLower = (t.status || '').toLowerCase();
      let badgeClass = 'submitted';
      if (statusLower.includes('resolved')) badgeClass = 'resolved';
      else if (statusLower.includes('progress')) badgeClass = 'progress';
      else if (statusLower.includes('assigned')) badgeClass = 'assigned';

      return `
        <div class="recent-ticket-row" data-id="${escapeHtml(t.tracking_id)}">
          <div class="ticket-row-left">
            <b>${escapeHtml(t.tracking_id)}</b>
            <small>📍 ${escapeHtml(t.area || t.ward_name)} · ${escapeHtml(t.issue_type)}</small>
          </div>
          <span class="ticket-status-pill ticket-status-${badgeClass}">
            ${escapeHtml(t.status)}
          </span>
        </div>
      `;
    }).join('');

    // Attach click to inspect ticket
    $$('.recent-ticket-row').forEach(row => {
      row.onclick = () => {
        const id = row.dataset.id;
        $('#tracking').value = id;
        lookupStatus(id);
        $('#trackPanel').scrollIntoView({ behavior: 'smooth' });
      };
    });

  } catch (err) {
    console.warn('Recent tickets fetch error:', err);
  }
}

$('#refreshTicketsBtn').addEventListener('click', () => {
  fetchRecentTickets();
  showToast('Refreshed ticket database.', 'info');
});

$('#viewTicketsBtn').addEventListener('click', () => {
  fetchRecentTickets();
  $('.feed-card').scrollIntoView({ behavior: 'smooth' });
});

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  fetchRecentTickets();
});
