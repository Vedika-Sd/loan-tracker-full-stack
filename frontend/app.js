const API_BASE = 'http://127.0.0.1:8000/api';
const DOCUMENTS = { id_proof: 'ID proof', income_proof: 'Income proof', address_proof: 'Address proof' };
const STATUS_LABELS = { enquiry: 'Enquiry', documents_submitted: 'Docs submitted', documents_rejected: 'Docs rejected', approved: 'Approved', rejected: 'Rejected', disbursed: 'Disbursed' };
const state = { token: localStorage.getItem('loanflow_access'), user: JSON.parse(localStorage.getItem('loanflow_user') || 'null'), applications: [], selectedId: null };
const $ = (selector) => document.querySelector(selector);

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || Object.values(data).flat().join(' ') || `Request failed (${response.status})`);
  return data;
}

function showToast(message, error = false) { const toast = $('#toast'); toast.textContent = message; toast.style.background = error ? '#b34b3a' : 'var(--ink)'; toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 3200); }
function setAuthMessage(message) { $('#auth-message').textContent = message || ''; }
function money(value) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value); }
function status(value) { return `<span class="status ${value}">${STATUS_LABELS[value] || value}</span>`; }
function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' })[char]); }

function showApp() {
  $('#auth-view').classList.add('hidden'); $('#app-view').classList.remove('hidden'); $('#session-tools').classList.remove('hidden');
  $('#user-chip').textContent = `${state.user.username} · ${state.user.role}`;
  $('#role-label').textContent = state.user.role === 'officer' ? 'OFFICER CONSOLE' : 'CUSTOMER PORTAL';
  $('#page-title').textContent = state.user.role === 'officer' ? 'Applications, in focus.' : 'Your loan journey.';
  loadDashboard();
}
function showAuth() { $('#auth-view').classList.remove('hidden'); $('#app-view').classList.add('hidden'); $('#session-tools').classList.add('hidden'); }

async function login(event) {
  event.preventDefault(); setAuthMessage(''); const values = Object.fromEntries(new FormData(event.target));
  try { const tokens = await api('/auth/login/', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(values) }); state.token = tokens.access; localStorage.setItem('loanflow_access', state.token); state.user = await api('/auth/me/'); localStorage.setItem('loanflow_user', JSON.stringify(state.user)); showApp(); }
  catch (error) { setAuthMessage(error.message); }
}
async function register(event) {
  event.preventDefault(); setAuthMessage(''); const values = Object.fromEntries(new FormData(event.target));
  try { await api('/auth/register/', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ ...values, role:'customer' }) }); setAuthMessage('Account created. Sign in to continue.'); document.querySelector('[data-auth-tab="login"]').click(); }
  catch (error) { setAuthMessage(error.message); }
}

async function loadDashboard() {
  try { state.applications = await api('/loans/'); if (!state.selectedId && state.applications[0]) state.selectedId = state.applications[0].id; if (state.selectedId && !state.applications.find((app) => app.id === state.selectedId)) state.selectedId = state.applications[0]?.id || null; renderDashboard(); }
  catch (error) { if (error.message.includes('401')) { logout(); } else showToast(error.message, true); }
}
function renderDashboard() { $('#dashboard-content').innerHTML = state.user.role === 'officer' ? renderOfficer() : renderCustomer(); bindDashboardEvents(); }
function renderCustomer() {
  const selected = state.applications.find((app) => app.id === state.selectedId);
  return `<div class="dashboard-grid"><section class="panel"><div class="panel-heading"><h2>My applications</h2><span class="panel-kicker">${state.applications.length} total</span></div><form id="new-loan-form" class="new-loan-form"><div class="stats-row"><div class="stat"><b>${state.applications.length}</b><span>applications</span></div><div class="stat"><b>${state.applications.filter((app) => app.status === 'disbursed').length}</b><span>disbursed</span></div><div class="stat"><b>${state.applications.filter((app) => ['approved','disbursed'].includes(app.status)).length}</b><span>approved / paid</span></div></div><div class="panel-heading"><h2>New enquiry</h2></div><label class="field-label">Loan amount<input class="field-input" name="amount" type="number" min="1" placeholder="100000" required></label><label class="field-label">Tenure in months<input class="field-input" name="tenure_months" type="number" min="1" placeholder="24" required></label><button class="button button-primary" type="submit">Submit enquiry <span>→</span></button></form></section><section class="panel"><div class="panel-heading"><h2>Recent applications</h2></div><div class="app-list">${applicationList()}</div></section>${selected ? renderDetail(selected, false) : '<section class="panel detail-panel empty">Select an application to view its progress.</section>'}</div>`;
}
function renderOfficer() {
  const selected = state.applications.find((app) => app.id === state.selectedId); const counts = STATUS_LABELS; const values = Object.keys(counts).map((key) => ({ key, count: state.applications.filter((app) => app.status === key).length })); const max = Math.max(1, ...values.map((item) => item.count));
  return `<div class="stats-row"><div class="stat"><b>${state.applications.length}</b><span>total applications</span></div><div class="stat"><b>${state.applications.filter((app) => app.status === 'documents_submitted').length}</b><span>awaiting review</span></div><div class="stat"><b>${state.applications.filter((app) => app.status === 'disbursed').length}</b><span>disbursed</span></div></div><div class="dashboard-grid"><section class="panel"><div class="panel-heading"><h2>Portfolio by status</h2><span class="panel-kicker">live counts</span></div>${values.map((item) => `<div class="bar-row"><span>${counts[item.key]}</span><div class="bar-track"><div class="bar-fill" style="width:${(item.count / max) * 100}%"></div></div><b>${item.count}</b></div>`).join('')}</section><section class="panel"><div class="panel-heading"><h2>Application queue</h2><span class="panel-kicker">${state.applications.length} total</span></div><div class="app-list">${applicationList()}</div></section>${selected ? renderDetail(selected, true) : '<section class="panel detail-panel empty">Select an application to review.</section>'}</div>`;
}
function applicationList() { return state.applications.length ? state.applications.map((app) => `<div class="application-item ${app.id === state.selectedId ? 'selected' : ''}" data-application-id="${app.id}"><div><div class="application-id">Application #${app.id}</div><div class="application-meta">${escapeHtml(app.customer_name || state.user.username)} · ${money(app.amount)} · ${app.tenure_months} months</div></div>${status(app.status)}</div>`).join('') : '<p class="empty">No applications yet.</p>'; }
function renderDetail(app, officer) {
  return `<section class="panel detail-panel"><div class="detail-title"><div><p class="eyebrow">APPLICATION #${app.id}</p><h2>${escapeHtml(app.customer_name || 'Personal loan')}</h2><p class="subtle">Personal Loan · created ${new Date(app.created_at).toLocaleDateString()}</p></div>${status(app.status)}</div><div class="detail-layout"><div><div class="amount">${money(app.amount)}</div><p class="subtle">Requested over ${app.tenure_months} months</p><div class="documents"><div class="panel-heading"><h2>Document checklist</h2><span class="panel-kicker">${app.documents.filter((doc) => doc.status === 'verified').length}/3 verified</span></div>${Object.entries(DOCUMENTS).map(([type, label]) => documentRow(app, type, label, officer)).join('')}</div>${officer ? officerActions(app) : ''}</div><div><div class="panel-heading"><h2>Status timeline</h2><span class="panel-kicker">read only</span></div><div class="timeline">${app.timeline.map((event) => `<div class="timeline-item"><strong>${escapeHtml(event.message)}</strong><span>${STATUS_LABELS[event.status] || event.status} · ${new Date(event.created_at).toLocaleString()}</span></div>`).join('')}</div></div></div></section>`;
}
function documentRow(app, type, label, officer) { const doc = app.documents.find((item) => item.document_type === type); if (!doc) return `<div class="document-row"><div class="document-name">${label}<small>Not uploaded</small></div>${officer ? '<span class="subtle">Awaiting customer</span>' : `<form class="upload-form" data-upload-type="${type}"><input type="file" name="file" required><button class="button button-small button-outline" type="submit">Upload</button></form>`}</div>`; return `<div class="document-row"><div class="document-name">${label}<small>${escapeHtml(doc.original_name)} · ${doc.rejection_reason ? escapeHtml(doc.rejection_reason) : ''}</small></div><div class="document-actions">${status(doc.status)}${officer && doc.status !== 'verified' ? `<button class="button button-small button-primary verify-button" data-document-id="${doc.id}" data-status="verified">Verify</button><button class="button button-small button-danger reject-button" data-document-id="${doc.id}">Reject</button>` : ''}${!officer && doc.status === 'rejected' ? `<form class="upload-form" data-upload-type="${type}"><input type="file" name="file" required><button class="button button-small button-outline" type="submit">Replace</button></form>` : ''}</div></div>`; }
function officerActions(app) { return `<div class="officer-actions">${app.status !== 'approved' && app.status !== 'disbursed' ? `<button class="button button-primary button-small decision-button" data-decision="approve" ${app.documents.filter((doc) => doc.status === 'verified').length !== 3 ? 'disabled' : ''}>Approve application</button><button class="button button-danger button-small decision-button" data-decision="reject">Reject application</button>` : ''}${app.status === 'approved' ? '<button class="button button-primary button-small disburse-button">Mark disbursed</button>' : ''}</div>`; }

function bindDashboardEvents() {
  $('#new-loan-form')?.addEventListener('submit', async (event) => { event.preventDefault(); try { const data = Object.fromEntries(new FormData(event.target)); const app = await api('/loans/', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) }); state.applications.unshift(app); state.selectedId = app.id; renderDashboard(); showToast('Enquiry submitted'); } catch (error) { showToast(error.message, true); } });
  document.querySelectorAll('[data-application-id]').forEach((element) => element.addEventListener('click', () => { state.selectedId = Number(element.dataset.applicationId); renderDashboard(); }));
  document.querySelectorAll('[data-upload-type]').forEach((form) => form.addEventListener('submit', async (event) => { event.preventDefault(); const body = new FormData(form); body.append('document_type', form.dataset.uploadType); try { await api(`/loans/${state.selectedId}/documents/`, { method:'POST', body }); await loadDashboard(); showToast('Document uploaded'); } catch (error) { showToast(error.message, true); } }));
  document.querySelectorAll('.verify-button').forEach((button) => button.addEventListener('click', () => verifyDocument(button.dataset.documentId, 'verified')));
  document.querySelectorAll('.reject-button').forEach((button) => button.addEventListener('click', () => { const reason = window.prompt('Reason for rejection', 'Document was rejected.'); if (reason) verifyDocument(button.dataset.documentId, 'rejected', reason); }));
  document.querySelectorAll('.decision-button').forEach((button) => button.addEventListener('click', () => decide(button.dataset.decision)));
  $('.disburse-button')?.addEventListener('click', disburse);
}
async function verifyDocument(documentId, documentStatus, reason = '') { try { await api(`/loans/${state.selectedId}/documents/${documentId}/verify/`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ status:documentStatus, reason }) }); await loadDashboard(); showToast(documentStatus === 'verified' ? 'Document verified' : 'Document rejected'); } catch (error) { showToast(error.message, true); } }
async function decide(decision) { const reason = decision === 'reject' ? window.prompt('Reason for rejection', 'Application was rejected.') : ''; if (decision === 'reject' && !reason) return; try { await api(`/loans/${state.selectedId}/decision/`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ decision, reason }) }); await loadDashboard(); showToast(`Application ${decision}d`); } catch (error) { showToast(error.message, true); } }
async function disburse() { try { await api(`/loans/${state.selectedId}/disburse/`, { method:'POST', headers:{'Content-Type':'application/json'}, body:'{}' }); await loadDashboard(); showToast('Application marked disbursed'); } catch (error) { showToast(error.message, true); } }
function logout() { localStorage.removeItem('loanflow_access'); localStorage.removeItem('loanflow_user'); state.token = null; state.user = null; state.applications = []; state.selectedId = null; showAuth(); }

document.querySelectorAll('[data-auth-tab]').forEach((tab) => tab.addEventListener('click', () => { document.querySelectorAll('[data-auth-tab]').forEach((item) => item.classList.toggle('active', item === tab)); $('#login-form').classList.toggle('hidden', tab.dataset.authTab !== 'login'); $('#register-form').classList.toggle('hidden', tab.dataset.authTab !== 'register'); setAuthMessage(''); }));
$('#login-form').addEventListener('submit', login); $('#register-form').addEventListener('submit', register); $('#logout-button').addEventListener('click', logout); $('#refresh-button').addEventListener('click', loadDashboard);
if (state.token && state.user) showApp(); else showAuth();
