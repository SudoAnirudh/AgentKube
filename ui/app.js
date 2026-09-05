/**
 * AgentKube Web UI — Frontend Engine & API Connector
 */
document.addEventListener('DOMContentLoaded', () => {
  // Config & State
  const API_BASE = window.location.origin.includes(':8000') || window.location.origin.includes('localhost') 
    ? 'http://localhost:8000' 
    : '/api';

  let executionsStore = [];
  let currentActiveExecutionId = null;
  let pollIntervalId = null;

  // DOM Elements
  const navBtns = document.querySelectorAll('.nav-btn');
  const viewPanels = document.querySelectorAll('.view-panel');
  const globalStatusPill = document.getElementById('global-status');
  
  // Dashboard Elements
  const statTotal = document.getElementById('stat-total');
  const statActive = document.getElementById('stat-active');
  const statSuccessRate = document.getElementById('stat-success-rate');
  const statSystemStatus = document.getElementById('stat-system-status');
  const recentExecutionsTbody = document.getElementById('recent-executions-tbody');
  const quickRunForm = document.getElementById('quick-run-form');
  const quickTaskInput = document.getElementById('quick-task-input');
  const quickSpinner = document.getElementById('quick-spinner');
  
  // Full Run Elements
  const fullRunForm = document.getElementById('full-run-form');
  const fullTaskInput = document.getElementById('full-task-input');
  const fullContextInput = document.getElementById('full-context-input');
  const fullSpinner = document.getElementById('full-spinner');
  
  // Details Elements
  const detailIdVal = document.getElementById('detail-id-val');
  const detailStatusVal = document.getElementById('detail-status-val');
  const detailStatusPill = document.getElementById('detail-status-pill');
  const detailStepsVal = document.getElementById('detail-steps-val');
  const detailRetriesVal = document.getElementById('detail-retries-val');
  const detailTaskPrompt = document.getElementById('detail-task-prompt');
  const detailResultBox = document.getElementById('detail-result-box');
  const detailLogsTerminal = document.getElementById('detail-logs-terminal');
  const backToExecutionsBtn = document.getElementById('back-to-executions-btn');

  // History Elements
  const historyExecutionsTbody = document.getElementById('history-executions-tbody');
  const filterBtns = document.querySelectorAll('.filter-btn');

  // ---------------------------------------------------------------------------
  // Navigation Handler
  // ---------------------------------------------------------------------------
  function switchView(targetViewId) {
    navBtns.forEach(btn => {
      if (btn.dataset.view === targetViewId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    viewPanels.forEach(panel => {
      if (panel.id === `view-${targetViewId}`) {
        panel.classList.add('active');
      } else {
        panel.classList.remove('active');
      }
    });

    if (targetViewId !== 'execution-details' && pollIntervalId) {
      clearInterval(pollIntervalId);
      pollIntervalId = null;
    }

    if (targetViewId === 'dashboard' || targetViewId === 'executions') {
      renderExecutionsTables();
    }
  }

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });

  if (backToExecutionsBtn) {
    backToExecutionsBtn.addEventListener('click', () => switchView('executions'));
  }

  // ---------------------------------------------------------------------------
  // Health Probe Check
  // ---------------------------------------------------------------------------
  async function checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/ready`);
      if (res.ok) {
        globalStatusPill.className = 'status-pill status-ready';
        globalStatusPill.querySelector('.status-text').textContent = 'API Ready';
        if (statSystemStatus) statSystemStatus.textContent = 'Healthy';
      } else {
        throw new Error('Unhealthy status code');
      }
    } catch (err) {
      globalStatusPill.className = 'status-pill status-unhealthy';
      globalStatusPill.querySelector('.status-text').textContent = 'API Offline';
      if (statSystemStatus) statSystemStatus.textContent = 'Degraded';
    }
  }

  setInterval(checkHealth, 10000);
  checkHealth();

  // ---------------------------------------------------------------------------
  // Task Submission Handler
  // ---------------------------------------------------------------------------
  async function submitTask(taskText, contextPayload = null, spinnerEl = null) {
    if (spinnerEl) spinnerEl.classList.remove('hidden');

    try {
      let contextJson = {};
      if (contextPayload && contextPayload.trim()) {
        try {
          contextJson = JSON.parse(contextPayload);
        } catch (e) {
          alert('Invalid JSON in Context Parameters field.');
          if (spinnerEl) spinnerEl.classList.add('hidden');
          return;
        }
      }

      const res = await fetch(`${API_BASE}/api/v1/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: taskText, context: contextJson })
      });

      if (!res.ok) {
        throw new Error(`API submission failed with code ${res.status}`);
      }

      const data = await res.json();
      const executionId = data.execution_id;

      // Add to local store
      const newExec = {
        execution_id: executionId,
        status: data.status || 'queued',
        task: taskText,
        created_at: new Date().toISOString(),
        execution: { steps_executed: 0, retries: 0 },
        result: null
      };

      executionsStore.unshift(newExec);
      updateDashboardStats();

      // Open Execution Details View & Poll
      openExecutionDetails(executionId);

    } catch (err) {
      alert(`Task Submission Failed: ${err.message}`);
    } finally {
      if (spinnerEl) spinnerEl.classList.add('hidden');
    }
  }

  if (quickRunForm) {
    quickRunForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const task = quickTaskInput.value;
      if (task) submitTask(task, null, quickSpinner);
    });
  }

  if (fullRunForm) {
    fullRunForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const task = fullTaskInput.value;
      const ctx = fullContextInput.value;
      if (task) submitTask(task, ctx, fullSpinner);
    });
  }

  // ---------------------------------------------------------------------------
  // Execution Details & Status Polling
  // ---------------------------------------------------------------------------
  async function fetchExecutionDetails(execId) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/agent/run/${execId}`);
      if (!res.ok) return;

      const data = await res.json();
      
      // Update local store
      const idx = executionsStore.findIndex(e => e.execution_id === execId);
      if (idx !== -1) {
        executionsStore[idx] = { ...executionsStore[idx], ...data };
      } else {
        executionsStore.unshift(data);
      }

      renderExecutionDetailsView(data);
      updateDashboardStats();

      // Stop polling if completed or failed
      if (data.status === 'completed' || data.status === 'failed') {
        if (pollIntervalId) {
          clearInterval(pollIntervalId);
          pollIntervalId = null;
        }
      }
    } catch (err) {
      console.error('Failed to poll status:', err);
    }
  }

  function openExecutionDetails(execId) {
    currentActiveExecutionId = execId;
    switchView('execution-details');
    
    // Fetch immediately
    fetchExecutionDetails(execId);

    // Setup 2s polling
    if (pollIntervalId) clearInterval(pollIntervalId);
    pollIntervalId = setInterval(() => fetchExecutionDetails(execId), 2000);
  }

  function renderExecutionDetailsView(data) {
    detailIdVal.textContent = data.execution_id;
    detailStatusVal.textContent = (data.status || 'queued').toUpperCase();
    detailTaskPrompt.textContent = data.task || 'No prompt specified';
    detailStepsVal.textContent = data.execution ? data.execution.steps_executed : 0;
    detailRetriesVal.textContent = data.execution ? data.execution.retries : 0;

    // Status Badge
    const status = (data.status || 'queued').toLowerCase();
    detailStatusPill.className = `badge badge-${status}`;
    detailStatusPill.textContent = status.toUpperCase();

    // Result Box
    if (status === 'completed' && data.result) {
      detailResultBox.innerHTML = `<strong>Result Output:</strong>\n${JSON.stringify(data.result, null, 2)}`;
    } else if (status === 'failed' && data.error) {
      detailResultBox.innerHTML = `<span class="badge badge-failed">ERROR</span> ${data.error.message || 'Execution Failed'}`;
    } else {
      detailResultBox.innerHTML = `<span class="placeholder-text">Task is currently in state '${status}'... Polling updates.</span>`;
    }

    // Terminal Logs
    detailLogsTerminal.textContent = [
      `[INFO] [${new Date().toISOString()}] Job received at API boundary (execution_id=${data.execution_id})`,
      `[INFO] [${new Date().toISOString()}] State initialized in Redis (status=${status})`,
      status === 'running' ? `[INFO] Celery worker processing agent plan...` : '',
      status === 'completed' ? `[INFO] Task execution completed successfully. Result returned.` : '',
      status === 'failed' ? `[ERROR] Task execution failed: ${data.error ? data.error.message : 'Unknown'}` : ''
    ].filter(Boolean).join('\n');
  }

  // ---------------------------------------------------------------------------
  // Table Rendering & Filters
  // ---------------------------------------------------------------------------
  function renderExecutionsTables() {
    // Recent Table
    if (recentExecutionsTbody) {
      const recentList = executionsStore.slice(0, 5);
      if (recentList.length === 0) {
        recentExecutionsTbody.innerHTML = '<tr class="empty-row"><td colspan="4">No tasks submitted yet.</td></tr>';
      } else {
        recentExecutionsTbody.innerHTML = recentList.map(exec => `
          <tr>
            <td><code class="code-font">${exec.execution_id}</code></td>
            <td><span class="badge badge-${(exec.status || 'queued').toLowerCase()}">${(exec.status || 'queued').toUpperCase()}</span></td>
            <td class="text-truncate">${(exec.task || '').slice(0, 45)}...</td>
            <td><button class="btn btn-sm btn-ghost view-btn" data-id="${exec.execution_id}">View</button></td>
          </tr>
        `).join('');
      }
    }

    // History Table
    if (historyExecutionsTbody) {
      const activeFilter = document.querySelector('.filter-btn.active')?.dataset.filter || 'all';
      const filtered = activeFilter === 'all' 
        ? executionsStore 
        : executionsStore.filter(e => (e.status || 'queued').toLowerCase() === activeFilter);

      if (filtered.length === 0) {
        historyExecutionsTbody.innerHTML = '<tr class="empty-row"><td colspan="5">No executions match selected filter.</td></tr>';
      } else {
        historyExecutionsTbody.innerHTML = filtered.map(exec => `
          <tr>
            <td><code class="code-font">${exec.execution_id}</code></td>
            <td><span class="badge badge-${(exec.status || 'queued').toLowerCase()}">${(exec.status || 'queued').toUpperCase()}</span></td>
            <td>${(exec.task || '').slice(0, 50)}...</td>
            <td>${exec.execution ? exec.execution.steps_executed : 0} steps</td>
            <td><button class="btn btn-sm btn-ghost view-btn" data-id="${exec.execution_id}">Inspect</button></td>
          </tr>
        `).join('');
      }
    }

    // Bind Click View Buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
      btn.addEventListener('click', () => openExecutionDetails(btn.dataset.id));
    });
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderExecutionsTables();
    });
  });

  function updateDashboardStats() {
    const total = executionsStore.length;
    const completed = executionsStore.filter(e => e.status === 'completed').length;
    const failed = executionsStore.filter(e => e.status === 'failed').length;

    if (statTotal) statTotal.textContent = total;
    if (statSuccessRate) {
      const rate = total > 0 ? Math.round((completed / (completed + failed || 1)) * 100) : 100;
      statSuccessRate.textContent = `${rate}%`;
    }
  }

  // Refresh Button
  const refreshBtn = document.getElementById('refresh-recent-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', renderExecutionsTables);
  }
});
