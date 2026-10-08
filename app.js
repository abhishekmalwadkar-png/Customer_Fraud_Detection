/**
 * Dummy Bank Portal - Fraud Operations Portal
 * Interactive Frontend Client with Live PostgreSQL Integration
 */

// Global State
let allTickets = [];
let filteredTickets = [];
let solvedTickets = [];
let filteredSolvedTickets = [];
let knownTicketIds = new Set();
let liveNotifications = [];
let ticketCurrentPage = 1;
const ticketPageSize = 10;
let solvedCurrentPage = 1;
const solvedPageSize = 10;
let allAuditLogs = [];
let auditCurrentPage = 1;
const auditPageSize = 10;
let allCustomers = [];
let filteredCustomers = [];
let customerCurrentPage = 1;
const customerPageSize = 10;
let customerDirectoryData = [];
let recentTxData = [];
let selectedTicketIds = new Set();
let currentDossierTicket = null;

// Staff Authentication Session
let currentStaffUser = null;

function checkAuthSession() {
  let sessionStr = localStorage.getItem("fraud_staff_session");
  if (!sessionStr) {
    // Graceful auto-session fallback: seed default active branch manager session
    const defaultUser = {
      user_id: 1,
      username: "manager",
      full_name: "Vikram Malhotra",
      role: "MANAGER",
      email: "vikram.m@bank.internal",
      department: "Fraud Risk Management (All Access)"
    };
    try {
      localStorage.setItem("fraud_staff_session", JSON.stringify(defaultUser));
      sessionStr = JSON.stringify(defaultUser);
    } catch (e) {}
  }

  try {
    currentStaffUser = JSON.parse(sessionStr);
    if (!currentStaffUser || !currentStaffUser.full_name) {
      currentStaffUser = {
        user_id: 1,
        username: "manager",
        full_name: "Vikram Malhotra",
        role: "MANAGER",
        email: "vikram.m@bank.internal",
        department: "Fraud Risk Management (All Access)"
      };
    }
  } catch (e) {
    currentStaffUser = {
      user_id: 1,
      username: "manager",
      full_name: "Vikram Malhotra",
      role: "MANAGER",
      email: "vikram.m@bank.internal",
      department: "Fraud Risk Management (All Access)"
    };
  }

  const fullName = currentStaffUser.full_name || "Vikram Malhotra";
  const roleName = currentStaffUser.role === "MANAGER" ? "Branch Manager (All Access)" : (currentStaffUser.department || "Fraud Investigator");

  // Update Header & Home Hero User Profile UI
  const nameEl = document.getElementById("headerUserName");
  const roleEl = document.getElementById("headerUserRole");
  const avatarEl = document.getElementById("headerUserAvatar");
  const heroWelcomeEl = document.getElementById("homeHeroWelcome");
  const heroSubtitleEl = document.getElementById("homeHeroSubtitle");
  const heroRoleEl = document.getElementById("homeHeroRole");

  if (nameEl) nameEl.textContent = fullName;
  if (roleEl) roleEl.textContent = roleName;
  if (avatarEl) {
    const parts = fullName.split(" ");
    const initials = parts.length > 1 ? (parts[0][0] + parts[1][0]).toUpperCase() : parts[0].slice(0, 2).toUpperCase();
    avatarEl.textContent = initials;
  }

  if (heroWelcomeEl) heroWelcomeEl.textContent = `Welcome, ${fullName}`;
  if (heroSubtitleEl) heroSubtitleEl.textContent = `${roleName} • ABC Operations Hub`;
  if (heroRoleEl) heroRoleEl.textContent = roleName;

  return true;
}

function handleStaffLogout() {
  if (confirm("Sign out from ABC?")) {
    localStorage.removeItem("fraud_staff_session");
    localStorage.removeItem("fraud_staff_token");
    window.location.href = "/login";
  }
}

let allStaffMembers = [];

async function loadStaffMembers() {
  try {
    const res = await fetch("/api/staff-users");
    if (!res.ok) return;
    const data = await res.json();
    if (Array.isArray(data) && data.length > 0) {
      allStaffMembers = data;
      populateStaffDropdowns();
    }
  } catch (err) {
    console.error("Could not load staff members from DB:", err);
  }
}

function populateStaffDropdowns() {
  if (!allStaffMembers || allStaffMembers.length === 0) return;

  const fullOptionsHtml = allStaffMembers.map(s => {
    const val = s.department ? `${s.full_name} (${s.department})` : s.full_name;
    return `<option value="${escapeHtml(val)}">${escapeHtml(val)}</option>`;
  }).join("");

  const shortOptionsHtml = allStaffMembers.map(s => {
    const val = s.department ? `${s.full_name} (${s.department})` : s.full_name;
    return `<option value="${escapeHtml(val)}">${escapeHtml(s.full_name)}</option>`;
  }).join("");

  // 1. New Ticket Modal Form dropdown
  const formStaffSelect = document.getElementById("formStaffAssignee");
  if (formStaffSelect) {
    const prevVal = formStaffSelect.value;
    formStaffSelect.innerHTML = fullOptionsHtml;
    if (prevVal) {
      for (let opt of formStaffSelect.options) {
        if (opt.value === prevVal || opt.value.includes(prevVal.split(" (")[0])) {
          formStaffSelect.value = opt.value;
          break;
        }
      }
    }
  }

  // 2. Incident Dossier / Drawer reassign dropdown
  const drawerStaffSelect = document.getElementById("selectDrawerStaff");
  if (drawerStaffSelect) {
    const prevVal = drawerStaffSelect.value;
    drawerStaffSelect.innerHTML = fullOptionsHtml;
    if (prevVal) {
      for (let opt of drawerStaffSelect.options) {
        if (opt.value === prevVal || opt.value.includes(prevVal.split(" (")[0])) {
          drawerStaffSelect.value = opt.value;
          break;
        }
      }
    }
  }

  // 3. Bulk Toolbar Staff Assign dropdown
  const bulkStaffSelect = document.getElementById("bulkStaffSelect");
  if (bulkStaffSelect) {
    const prevVal = bulkStaffSelect.value;
    bulkStaffSelect.innerHTML = shortOptionsHtml;
    if (prevVal) {
      for (let opt of bulkStaffSelect.options) {
        if (opt.value === prevVal || opt.value.includes(prevVal.split(" (")[0])) {
          bulkStaffSelect.value = opt.value;
          break;
        }
      }
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (!checkAuthSession()) return;

  initTabs();
  initClock();
  initEventListeners();
  checkSystemHealth();
  loadSavedNotifications();
  loadStaffMembers();
  loadAllData();

  // 1.5-second ultra-fast real-time auto-sync with AutomationEdge Process Studio & incoming API calls
  setInterval(() => {
    const isModalOpen = document.getElementById("newTicketModal")?.classList.contains("open");
    const isDrawerOpen = document.getElementById("drawerOverlay")?.classList.contains("open");
    if (!isModalOpen && !isDrawerOpen) {
      loadOverviewStats(true, false);
      loadFraudTickets(true);
      checkSystemHealth();
    }
  }, 1500);
});

// System Health Heartbeat Monitor
async function checkSystemHealth() {
  const badge = document.getElementById("headerHealthBadge");
  const text = document.getElementById("healthStatusText");
  if (!badge || !text) return;

  try {
    const t0 = performance.now();
    const res = await fetch("/health");
    const roundtripMs = Math.round(performance.now() - t0);
    const data = await res.json();

    if (res.ok && data.status === "UP") {
      badge.className = "header-health-badge";
      text.textContent = `Live (${data.database.ping_latency_ms || roundtripMs}ms)`;
      badge.title = `Server: ${data.server} | DB: ${data.database.status} (${data.database.pool.database}) | Threads: ${data.worker_threads}`;
    } else {
      badge.className = "header-health-badge degraded";
      text.textContent = `Degraded (${roundtripMs}ms)`;
      badge.title = "Database or service connection degraded";
    }
  } catch (err) {
    badge.className = "header-health-badge down";
    text.textContent = "Offline";
    badge.title = "Backend server unreachable";
  }
}

// 1. Tab Navigation
window.switchTab = function(targetTabId) {
  try {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(t => {
      if (t.getAttribute("data-tab") === targetTabId) {
        t.classList.add("active");
      } else {
        t.classList.remove("active");
      }
    });

    document.querySelectorAll(".tab-panel").forEach(panel => {
      if (panel.id === targetTabId) {
        panel.classList.add("active");
      } else {
        panel.classList.remove("active");
      }
    });

    if (targetTabId === "tab-dashboard") {
      try { loadOverviewStats(false, true); loadAnalytics(); } catch (e) { console.error("loadAnalytics error:", e); }
    }
    if (targetTabId === "tab-customers") {
      try { loadCustomers(); } catch (e) { console.error("loadCustomers error:", e); }
    }
    if (targetTabId === "tab-transactions") {
      try { loadTransactions(); } catch (e) { console.error("loadTransactions error:", e); }
    }
    if (targetTabId === "tab-audit") {
      try { applySolvedFilters(); loadAuditLogs(); } catch (e) { console.error("audit error:", e); }
    }
    if (targetTabId === "tab-pgadmin") {
      try { loadDbStatus(); } catch (e) { console.error("loadDbStatus error:", e); }
    }
    if (targetTabId === "tab-home") {
      try { loadOverviewStats(false, true); renderHomeUrgentList(); } catch (e) { console.error("renderHomeUrgentList error:", e); }
    }
    if (targetTabId === "tab-fraud-tickets") {
      try { applyFilters(); } catch (e) { console.error("applyFilters error:", e); }
    }
  } catch (err) {
    console.error("switchTab error:", err);
  }
};

function initTabs() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetTabId = tab.getAttribute("data-tab");
      if (targetTabId) switchTab(targetTabId);
    });
  });
}

// 2. Real-time UTC Clock
function initClock() {
  const clockEl = document.getElementById("clockValue");
  function update() {
    const now = new Date();
    clockEl.textContent = now.toUTCString().replace("GMT", "UTC");
  }
  update();
  setInterval(update, 1000);
}

// Sidebar Toggle & Collapse Controller
function initSidebarToggle() {
  const btnToggle = document.getElementById("btnSidebarToggle");
  const btnClose = document.getElementById("btnSidebarClose");
  const sidebar = document.getElementById("portalSidebar") || document.querySelector(".portal-sidebar");

  if (!sidebar) return;

  // Restore user's saved preference
  const isSavedClosed = localStorage.getItem("abc_portal_sidebar_closed") === "true";
  if (isSavedClosed) {
    document.body.classList.add("sidebar-closed");
    sidebar.classList.add("collapsed");
  }

  function toggleSidebar(forceState) {
    const isCurrentlyClosed = document.body.classList.contains("sidebar-closed") || sidebar.classList.contains("collapsed");
    const shouldClose = typeof forceState === "boolean" ? forceState : !isCurrentlyClosed;

    if (shouldClose) {
      document.body.classList.add("sidebar-closed");
      sidebar.classList.add("collapsed");
      localStorage.setItem("abc_portal_sidebar_closed", "true");
    } else {
      document.body.classList.remove("sidebar-closed");
      sidebar.classList.remove("collapsed");
      localStorage.setItem("abc_portal_sidebar_closed", "false");
    }
  }

  if (btnToggle) {
    btnToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleSidebar();
    });
  }

  if (btnClose) {
    btnClose.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleSidebar(true);
    });
  }

  // Keyboard shortcut: Ctrl + B or Cmd + B
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "TEXTAREA")) {
        return;
      }
      e.preventDefault();
      toggleSidebar();
    }
  });
}

// 3. Event Listeners
function initEventListeners() {
  initSidebarToggle();

  // Search & Filter listeners
  const searchInput = document.getElementById("ticketSearchInput");
  const filterSeverity = document.getElementById("filterSeverity");
  const filterStatus = document.getElementById("filterStatus");
  const filterIncidentType = document.getElementById("filterIncidentType");

  const onTicketFilterChange = () => {
    ticketCurrentPage = 1;
    applyFilters();
  };

  searchInput.addEventListener("input", onTicketFilterChange);
  filterSeverity.addEventListener("change", onTicketFilterChange);
  filterStatus.addEventListener("change", onTicketFilterChange);
  filterIncidentType.addEventListener("change", onTicketFilterChange);

  // Customer search
  const custSearchInput = document.getElementById("custSearchInput");
  if (custSearchInput) {
    custSearchInput.addEventListener("input", () => {
      applyCustomerSearch();
    });
  }

  // Refresh & Export buttons
  document.getElementById("btnRefreshTickets").addEventListener("click", () => {
    loadAllData();
    showToast("Refreshed data from PostgreSQL database", "success");
  });

  document.getElementById("btnExportTicketsCSV").addEventListener("click", exportTicketsCSV);

  // Modal Open / Close (if present)
  const modal = document.getElementById("newTicketModal");
  if (modal) {
    document.getElementById("btnOpenNewTicketModal")?.addEventListener("click", () => {
      openNewComplaintModal();
    });
    document.getElementById("btnCloseModal")?.addEventListener("click", () => {
      closeNewComplaintModal();
    });
    document.getElementById("btnCancelModal")?.addEventListener("click", () => {
      closeNewComplaintModal();
    });
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeNewComplaintModal();
    });

    // Auto-fill demo button listener
    document.getElementById("btnAutoFillDemo")?.addEventListener("click", autoFillDemoData);

    // Modal Amount Real-time Priority Preset Listener
    const formAmountInput = document.getElementById("formAmount");
    if (formAmountInput) {
      formAmountInput.addEventListener("input", updatePresetPriority);
      formAmountInput.addEventListener("change", updatePresetPriority);
    }

    // Modal Form Submit
    document.getElementById("newFraudTicketForm")?.addEventListener("submit", handleCreateNewTicket);
  }

  // Drawer Close
  const drawerOverlay = document.getElementById("drawerOverlay");
  document.getElementById("btnCloseDrawer").addEventListener("click", () => {
    drawerOverlay.classList.remove("open");
  });
  drawerOverlay.addEventListener("click", (e) => {
    if (e.target === drawerOverlay) drawerOverlay.classList.remove("open");
  });

  // Header Logout Button
  document.getElementById("btnLogoutHeader")?.addEventListener("click", handleStaffLogout);

  // Drawer Emergency Actions & Staff Reassignment
  document.getElementById("btnDrawerFreeze").addEventListener("click", handleFreezeAction);
  document.getElementById("btnDrawerInvestigate").addEventListener("click", () => handleStatusUpdate("UNDER_INVESTIGATION"));
  document.getElementById("btnDrawerResolve").addEventListener("click", () => handleStatusUpdate("RESOLVED"));
  document.getElementById("btnDrawerEscalate").addEventListener("click", () => handleStatusUpdate("ESCALATED"));
  document.getElementById("btnReassignStaff")?.addEventListener("click", handleReassignStaff);

  // pgAdmin SQL Runner (if present)
  const runBtn = document.getElementById("btnRunSQLQuery");
  if (runBtn) {
    runBtn.addEventListener("click", executeSQLQuery);
    document.querySelectorAll(".quick-sql-presets button").forEach(btn => {
      btn.addEventListener("click", () => {
        const queryEl = document.getElementById("sqlQueryText");
        if (queryEl) {
          queryEl.value = btn.getAttribute("data-sql");
          executeSQLQuery();
        }
      });
    });
  }

  // PDF Export trigger
  const btnDownloadSAR = document.getElementById("btnDownloadSAR");
  if (btnDownloadSAR) {
    btnDownloadSAR.addEventListener("click", async () => {
      const origHtml = btnDownloadSAR.innerHTML;
      try {
        btnDownloadSAR.disabled = true;
        btnDownloadSAR.innerHTML = `<div class="spinner" style="width: 14px; height: 14px; border-width: 2px;"></div> Generating PDF...`;
        showToast("Generating Official Fraud Audit & Compliance PDF...", "info");

        const res = await fetch("/api/reports/audit-pdf");
        if (!res.ok) {
          throw new Error(`Server returned HTTP ${res.status}`);
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `Official_Fraud_Audit_Report_${new Date().toISOString().slice(0, 10)}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        showToast("Official Audit PDF downloaded successfully.", "success");
      } catch (err) {
        showToast("Error generating PDF: " + err.message, "error");
      } finally {
        btnDownloadSAR.disabled = false;
        btnDownloadSAR.innerHTML = origHtml;
      }
    });
  }

  // Live Notification Bell Center
  const bellBtn = document.getElementById("btnNotificationBell");
  const notifDropdown = document.getElementById("notifDropdown");
  const clearNotifsBtn = document.getElementById("btnClearNotifs");

  if (bellBtn && notifDropdown) {
    bellBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const willOpen = !notifDropdown.classList.contains("open");
      if (willOpen) {
        notifDropdown.classList.add("open");
        notifDropdown.style.display = "flex";
      } else {
        notifDropdown.classList.remove("open");
        notifDropdown.style.display = "none";
      }
    });

    document.addEventListener("click", (e) => {
      if (!e.target.closest("#notifWrapper")) {
        notifDropdown.classList.remove("open");
        notifDropdown.style.display = "none";
      }
    });
  }

  if (clearNotifsBtn) {
    clearNotifsBtn.addEventListener("click", () => {
      markAllNotifsRead();
    });
  }

  const purgeNotifsBtn = document.getElementById("btnPurgeNotifs");
  if (purgeNotifsBtn) {
    purgeNotifsBtn.addEventListener("click", () => {
      clearAllNotifs();
    });
  }

  // Bulk Selection & Quick Actions Toolbar Listeners
  const selectAllCheckbox = document.getElementById("selectAllTicketsCheckbox");
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener("change", (e) => {
      const isChecked = e.target.checked;
      const startIndex = (ticketCurrentPage - 1) * ticketPageSize;
      const paginatedTickets = filteredTickets.slice(startIndex, startIndex + ticketPageSize);
      if (isChecked) {
        paginatedTickets.forEach(t => selectedTicketIds.add(String(t.ticket_id)));
      } else {
        paginatedTickets.forEach(t => selectedTicketIds.delete(String(t.ticket_id)));
      }
      updateBulkToolbar();
      renderFraudTicketsTable(filteredTickets);
    });
  }

  const tableBody = document.getElementById("fraudTicketsTableBody");
  if (tableBody) {
    tableBody.addEventListener("change", (e) => {
      if (e.target.classList.contains("ticket-select-checkbox")) {
        const tid = String(e.target.getAttribute("data-ticket-id"));
        if (e.target.checked) {
          selectedTicketIds.add(tid);
        } else {
          selectedTicketIds.delete(tid);
        }
        updateBulkToolbar();
      }
    });
  }

  // Bulk Action Buttons
  document.getElementById("btnBulkInvestigate")?.addEventListener("click", () => executeBulkAction("UNDER_INVESTIGATION", "Bulk set to In Progress"));
  document.getElementById("btnBulkFreeze")?.addEventListener("click", () => executeBulkAction("FROZEN", "Emergency account lock applied via bulk operations"));
  document.getElementById("btnBulkResolve")?.addEventListener("click", () => executeBulkAction("RESOLVED", "Bulk resolved and closed"));
  document.getElementById("btnBulkEscalate")?.addEventListener("click", () => executeBulkAction("ESCALATED", "Bulk escalated to Senior Team"));
  document.getElementById("btnBulkAssignStaff")?.addEventListener("click", () => {
    const staff = document.getElementById("bulkStaffSelect")?.value || (allStaffMembers.length > 0 ? (allStaffMembers[0].department ? `${allStaffMembers[0].full_name} (${allStaffMembers[0].department})` : allStaffMembers[0].full_name) : "Staff Officer");
    executeBulkStaffAssign(staff);
  });
  document.getElementById("btnBulkExport")?.addEventListener("click", exportSelectedTicketsCSV);
  document.getElementById("btnBulkDeselect")?.addEventListener("click", clearSelectedTickets);

  // Solved Archive Search & Filter Listeners
  const solvedSearchInput = document.getElementById("solvedSearchInput");
  const filterSolvedType = document.getElementById("filterSolvedIncidentType");
  const onSolvedFilterChange = () => {
    solvedCurrentPage = 1;
    applySolvedFilters();
  };
  if (solvedSearchInput) solvedSearchInput.addEventListener("input", onSolvedFilterChange);
  if (filterSolvedType) filterSolvedType.addEventListener("change", onSolvedFilterChange);
  document.getElementById("btnExportSolvedCSV")?.addEventListener("click", exportSolvedCSV);

  // Home Action Buttons
  document.getElementById("btnHomeNewComplaint")?.addEventListener("click", () => {
    document.getElementById("newTicketModal")?.classList.add("open");
  });
  document.getElementById("btnHomeViewQueue")?.addEventListener("click", () => {
    switchTab("tab-fraud-tickets");
  });
  document.getElementById("btnHomeViewSummary")?.addEventListener("click", () => {
    switchTab("tab-dashboard");
  });

  // History Sub-Tabs Switching (Solved Archive vs Staff Activity Logs)
  document.querySelectorAll(".history-sub-tab").forEach(tabBtn => {
    tabBtn.addEventListener("click", () => {
      document.querySelectorAll(".history-sub-tab").forEach(b => b.classList.remove("active"));
      tabBtn.classList.add("active");

      const targetSubPanelId = tabBtn.getAttribute("data-subtab");
      document.querySelectorAll(".history-sub-panel").forEach(p => {
        p.classList.remove("active");
        p.style.display = "none";
      });

      const targetPanel = document.getElementById(targetSubPanelId);
      if (targetPanel) {
        targetPanel.classList.add("active");
        targetPanel.style.display = "flex";
      }

      if (targetSubPanelId === "subtab-audit-logs") {
        loadAuditLogs();
      } else {
        applySolvedFilters();
      }
    });
  });
}

// 4. Data Loading Pipeline
async function loadAllData() {
  await Promise.all([
    loadOverviewStats(),
    loadFraudTickets()
  ]);
}

let latestOverviewData = null;

async function loadOverviewStats(isSilent = false, forceAnimate = false) {
  try {
    const res = await fetch("/api/overview");
    const data = await res.json();
    latestOverviewData = data;

    const totalTickets = data.total_tickets || 0;
    const resolvedCases = data.resolved_cases || 0;
    const activeTickets = data.active_tickets !== undefined ? data.active_tickets : Math.max(0, totalTickets - resolvedCases);
    const inProgressTickets = data.under_investigation || 0;

    const setElText = (id, val) => {
      const el = document.getElementById(id);
      if (el && el.textContent !== String(val)) el.textContent = String(val);
    };

    setElText("kpiTotalCustomers", data.total_customers || "0");
    setElText("kpiTotalTickets", totalTickets);
    setElText("badgeTicketCount", activeTickets);
    setElText("kpiTotalAmount", formatCurrency(data.total_amount || 0));
    setElText("kpiRecoveredAmount", formatCurrency(data.recovered_amount || 0));
    setElText("kpiFrozenAccounts", data.frozen_accounts || "0");
    setElText("kpiCriticalCount", data.critical_customers || "0");

    // Active & In Progress ticket counts
    setElText("kpiActiveTickets", activeTickets);
    setElText("kpiInProgressTickets", inProgressTickets);
    setElText("bubbleActiveTickets", activeTickets);
    setElText("bubbleInProgressTickets", inProgressTickets);

    // Home Pulse Cards (Port 3000 Theme)
    setElText("homeTotalRecords", data.total_customers || "240");
    setElText("homeActiveTickets", activeTickets);
    setElText("homeInProgressTickets", inProgressTickets);
    const resolvedPct = totalTickets > 0 ? `${Math.round((resolvedCases / totalTickets) * 100)}%` : "100%";
    setElText("homeSolvedTickets", resolvedPct);

    // Live Date on Hero Banner
    const heroDateEl = document.getElementById("heroLiveDate");
    if (heroDateEl) {
      const now = new Date();
      heroDateEl.textContent = now.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
    }

    // Live Recovery Metrics for both Home & Dashboard tabs
    const totalAmt = data.total_amount || 0;
    const recoveredAmt = data.recovered_amount || 0;
    const pendingAmt = Math.max(0, totalAmt - recoveredAmt);
    const pct = totalAmt > 0 ? Math.round((recoveredAmt / totalAmt) * 100) : 0;

    const setDetailsText = (grossId, recId, pendId) => {
      if (document.getElementById(grossId)) document.getElementById(grossId).textContent = formatCurrency(totalAmt);
      if (document.getElementById(recId)) document.getElementById(recId).textContent = formatCurrency(recoveredAmt);
      if (document.getElementById(pendId)) document.getElementById(pendId).textContent = formatCurrency(pendingAmt);
    };

    setDetailsText("recGrossVal", "recRecoveredVal", "recPendingVal");
    setDetailsText("homeRecGrossVal", "homeRecRecoveredVal", "homeRecPendingVal");

    renderAnimatedRecoveryGauge("dashCircularMetric", "recoveryRatePercent", pct, forceAnimate);
    renderAnimatedRecoveryGauge("homeCircularMetric", "homeRecoveryRatePercent", pct, forceAnimate);
    renderAnimatedDonutChart("homeStatusDonutChart", forceAnimate);
    if (!isSilent) {
      renderHomeUrgentList();
    }
  } catch (err) {
    console.error("Error loading overview stats:", err);
  }
}

// -------------------------------------------------------------
// Animated Counter & Chart Visualizer Handlers
// -------------------------------------------------------------
function animateCounter(element, startVal, endVal, durationMs = 800, prefix = '', suffix = '') {
  if (!element) return;
  const startNum = parseFloat(startVal) || 0;
  const endNum = parseFloat(endVal) || 0;
  if (startNum === endNum) {
    element.textContent = `${prefix}${endNum}${suffix}`;
    return;
  }
  const startTime = performance.now();
  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / durationMs, 1);
    // Smooth ease-out cubic
    const ease = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(startNum + (endNum - startNum) * ease);
    element.textContent = `${prefix}${current}${suffix}`;
    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      element.textContent = `${prefix}${endNum}${suffix}`;
    }
  }
  requestAnimationFrame(step);
}

function renderAnimatedRecoveryGauge(metricId, pctId, pct, forceAnimate = false) {
  const metricEl = document.getElementById(metricId);
  if (!metricEl) return;

  const r = 52;
  const circumference = 2 * Math.PI * r; // ~326.72
  const targetOffset = (circumference * (1 - (pct / 100))).toFixed(2);
  const ringId = `${metricId}_ring`;

  const existingRing = document.getElementById(ringId);
  const existingVal = document.getElementById(pctId);

  // If already rendered and not forced to re-animate on tab switch, silently update with no restart
  if (existingRing && existingVal && !forceAnimate) {
    existingRing.style.strokeDashoffset = targetOffset;
    existingVal.textContent = `${pct}%`;
    return;
  }

  metricEl.style.background = "none";
  metricEl.style.position = "relative";
  metricEl.innerHTML = `
    <svg width="130" height="130" viewBox="0 0 130 130" style="transform: rotate(-90deg); position: absolute; inset: 0;">
      <circle cx="65" cy="65" r="${r}" fill="transparent" stroke="#f1f5f9" stroke-width="14"></circle>
      <circle class="animated-svg-ring" id="${ringId}" cx="65" cy="65" r="${r}" fill="transparent" stroke="#10b981" stroke-width="14" stroke-linecap="round" stroke-dasharray="${circumference.toFixed(2)}" stroke-dashoffset="${circumference.toFixed(2)}"></circle>
    </svg>
    <div class="metric-circle-inner" style="box-shadow: none; z-index: 1;">
      <span class="metric-circle-val" id="${pctId}" style="color: #059669;">0%</span>
      <span class="metric-circle-sub">Money Saved</span>
    </div>
  `;

  requestAnimationFrame(() => {
    const ring = document.getElementById(ringId);
    if (ring) {
      ring.style.strokeDashoffset = targetOffset;
    }
    const valEl = document.getElementById(pctId);
    if (valEl) {
      animateCounter(valEl, 0, pct, 800, '', '%');
    }
  });
}

function renderAnimatedDonutChart(containerId, forceAnimate = false) {
  const container = document.getElementById(containerId);
  if (!container) return;

  let total = allTickets.length;
  let solvedCount = allTickets.filter(t => t.status === 'RESOLVED').length;
  let inProgCount = allTickets.filter(t => t.status === 'UNDER_INVESTIGATION').length;
  let frozenCount = allTickets.filter(t => t.status === 'FROZEN' || t.status === 'BLOCKED').length;
  let openCount = allTickets.filter(t => !['RESOLVED', 'UNDER_INVESTIGATION', 'FROZEN', 'BLOCKED', 'CLOSED'].includes(t.status)).length;

  if (total === 0 && latestOverviewData) {
    total = latestOverviewData.total_tickets || 0;
    solvedCount = latestOverviewData.resolved_cases || 0;
    inProgCount = latestOverviewData.under_investigation || 0;
    frozenCount = latestOverviewData.frozen_accounts || 0;
    openCount = Math.max(0, total - solvedCount - inProgCount - frozenCount);
  }
  const displayTotal = total || 1;

  const statusSegments = [
    { label: "Solved / Refunded", count: solvedCount, color: "#059669" },
    { label: "Under Investigation", count: inProgCount, color: "#d97706" },
    { label: "Accounts Blocked", count: frozenCount, color: "#ea580c" },
    { label: "Urgent Open", count: openCount, color: "#dc2626" }
  ].filter(s => s.count > 0);

  const r = 52;
  const circumference = 2 * Math.PI * r; // ~326.72
  let offset = 0;

  const segmentData = statusSegments.map(s => {
    const pct = s.count / displayTotal;
    const dashLength = (pct * circumference).toFixed(2);
    const spaceLength = (circumference - (pct * circumference)).toFixed(2);
    const curOffset = offset.toFixed(2);
    offset -= (pct * circumference);
    return { ...s, pct: Math.round(pct * 100), dashLength, spaceLength, offset: curOffset };
  });

  const totalValEl = document.getElementById(`${containerId}_total_val`);
  const firstSlice = document.getElementById(`${containerId}_slice_0`);

  // If already rendered and not forced to animate on tab switch, silently update with no restart
  if (totalValEl && firstSlice && !forceAnimate) {
    totalValEl.textContent = String(total);
    segmentData.forEach((s, idx) => {
      const sliceEl = document.getElementById(`${containerId}_slice_${idx}`);
      if (sliceEl) {
        sliceEl.style.strokeDasharray = `${s.dashLength} ${s.spaceLength}`;
        sliceEl.style.strokeDashoffset = s.offset;
      }
    });
    return;
  }

  let circlesHtml = `<circle cx="65" cy="65" r="${r}" fill="transparent" stroke="#f1f5f9" stroke-width="14"></circle>`;
  segmentData.forEach((s, idx) => {
    circlesHtml += `<circle id="${containerId}_slice_${idx}" class="animated-svg-slice" cx="65" cy="65" r="${r}" fill="transparent" stroke="${s.color}" stroke-width="14" stroke-dasharray="0 ${circumference.toFixed(2)}" stroke-dashoffset="${s.offset}"></circle>`;
  });

  container.innerHTML = `
    <div class="recovery-metrics-box">
      <div class="circular-metric" style="background: none; position: relative;">
        <svg width="130" height="130" viewBox="0 0 130 130" class="donut-svg" style="position: absolute; inset: 0;">
          ${circlesHtml}
        </svg>
        <div class="metric-circle-inner" style="box-shadow: none; z-index: 1;">
          <span class="metric-circle-val" id="${containerId}_total_val" style="color: var(--text-main);">0</span>
          <span class="metric-circle-sub">Total Cases</span>
        </div>
      </div>
      <div class="recovery-details-list">
        ${segmentData.map(s => `
          <div class="rec-row">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="legend-dot" style="background: ${s.color};"></span>
              <span>${s.label}:</span>
            </div>
            <strong style="color: ${s.color}; font-size: 13px;">${s.count} <small style="color: var(--text-dim); font-weight: normal; margin-left: 4px;">(${s.pct}%)</small></strong>
          </div>
        `).join("")}
      </div>
    </div>
  `;

  requestAnimationFrame(() => {
    segmentData.forEach((s, idx) => {
      const sliceEl = document.getElementById(`${containerId}_slice_${idx}`);
      if (sliceEl) {
        sliceEl.style.strokeDasharray = `${s.dashLength} ${s.spaceLength}`;
      }
    });
    const totalEl = document.getElementById(`${containerId}_total_val`);
    if (totalEl) {
      animateCounter(totalEl, 0, total, 800);
    }
  });
}

function renderHomeUrgentList() {
  const container = document.getElementById("homeUrgentList");
  if (!container) return;

  // Statuses where case is fully finished / archived:
  // Resolved, Closed, Rejected
  const finishedStatuses = new Set([
    'RESOLVED',
    'CLOSED',
    'REJECTED'
  ]);

  // Urgent Action Required list shows active High/Critical complaints needing review & triage
  const urgentTickets = allTickets.filter(t => {
    const st = String(t.status || 'OPEN').trim().toUpperCase();
    const isActive = !finishedStatuses.has(st);
    const isUrgent = t.severity === 'CRITICAL' || t.severity === 'HIGH';
    return isActive && isUrgent;
  });

  // Render the status breakdown donut chart on the RIGHT side
  renderAnimatedDonutChart("homeStatusDonutChart");

  if (urgentTickets.length === 0) {
    container.innerHTML = `
      <div class="home-resolved-banner" style="margin-bottom: 0;">
        <i class="fa-solid fa-circle-check"></i>
        <div>
          <strong>All Urgent Complaints Addressed & Processed</strong>
          <p>Zero critical escalations pending immediate triage. All accounts secured and live monitoring active.</p>
        </div>
      </div>
    `;
    return;
  }

  const displayTickets = urgentTickets.slice(0, 5);

  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
      <span style="font-size: 13px; font-weight: 700; color: #dc2626; display: flex; align-items: center; gap: 6px;">
        <i class="fa-solid fa-triangle-exclamation"></i> Urgent Action Required (${urgentTickets.length})
      </span>
      <button class="btn btn-xs btn-outline" onclick="switchTab('tab-fraud-tickets')">View All in Queue</button>
    </div>
    ${displayTickets.map(t => `
      <div class="critical-item" onclick="openIncidentDossier('${t.ticket_id}')">
        <div class="crit-left">
          <div class="crit-title-row">
            <span class="code-font" style="font-weight: 700; color: #1c1917;">${t.ticket_number}</span>
            ${getSeverityBadgeHtml(t.severity)}
            ${getStatusBadgeHtml(t.status)}
          </div>
          <div class="crit-name">${escapeHtml(t.full_name)} • <span class="code-font">${t.account_number}</span></div>
          <div class="crit-desc">${escapeHtml(t.incident_type)} (${formatCurrency(t.amount_involved)})</div>
        </div>
        <div class="crit-right">
          <button class="btn btn-xs btn-outline" onclick="event.stopPropagation(); openIncidentDossier('${t.ticket_id}')">
            <i class="fa-solid fa-bolt"></i> Investigate
          </button>
        </div>
      </div>
    `).join("")}
  `;
}

async function loadFraudTickets(isBackground = false) {
  const tbody = document.getElementById("fraudTicketsTableBody");
  try {
    const res = await fetch("/api/fraud-tickets");
    const freshTickets = await res.json();
    if (!Array.isArray(freshTickets)) return;

    if (knownTicketIds.size === 0) {
      // First visit: register existing ticket numbers & seed recent 5 as read alerts
      freshTickets.forEach(t => knownTicketIds.add(String(t.ticket_number || t.ticket_id)));
      try {
        sessionStorage.setItem("known_ticket_ids", JSON.stringify(Array.from(knownTicketIds)));
      } catch (e) {}

      if (liveNotifications.length === 0 && freshTickets.length > 0) {
        liveNotifications = freshTickets.slice(0, 5).map(t => ({
          id: t.ticket_id,
          ticket_number: t.ticket_number,
          full_name: t.full_name,
          amount: t.amount_involved,
          incident_type: t.incident_type,
          channel: t.reported_channel,
          time: t.incident_date ? new Date(t.incident_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Recent",
          read: true
        }));
        saveNotifications();
        renderNotificationList();
      }

      allTickets = freshTickets;
    } else {
      // Detect newly created complaints dispatched from AutomationEdge or API
      const newArrivals = freshTickets.filter(t => !knownTicketIds.has(String(t.ticket_number || t.ticket_id)));
      
      if (newArrivals.length > 0) {
        newArrivals.forEach(t => {
          knownTicketIds.add(String(t.ticket_number || t.ticket_id));
          t.isNew = true;

          // Push into Live Notification Center
          const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          liveNotifications.unshift({
            id: t.ticket_id,
            ticket_number: t.ticket_number,
            full_name: t.full_name,
            amount: t.amount_involved,
            incident_type: t.incident_type,
            channel: t.reported_channel,
            time: nowStr,
            read: false
          });

          showToast(`⚡ New Complaint Raised: ${t.ticket_number} (${t.full_name} - ${formatCurrency(t.amount_involved)})`, "success");
        });

        try {
          sessionStorage.setItem("known_ticket_ids", JSON.stringify(Array.from(knownTicketIds)));
        } catch (e) {}

        saveNotifications();
        triggerBellNotification(true);
        renderNotificationList();
        loadOverviewStats();
      }
      allTickets = freshTickets;
    }

    applyFilters();
  } catch (err) {
    console.error("loadFraudTickets error:", err);
    if (!isBackground) {
      tbody.innerHTML = `<tr><td colspan="10" class="loading-state" style="color: var(--rose);">Failed to load tickets from database. Please verify backend is running.</td></tr>`;
    }
  }
}

function saveNotifications() {
  try {
    sessionStorage.setItem("bank_portal_notifs", JSON.stringify(liveNotifications.slice(0, 40)));
  } catch (e) {}
}

function loadSavedNotifications() {
  try {
    const saved = sessionStorage.getItem("bank_portal_notifs");
    if (saved) {
      liveNotifications = JSON.parse(saved);
      triggerBellNotification(false);
      renderNotificationList();
    }
  } catch (e) {}
}

function playNotificationSound() {
  // Sound alerts silenced as requested
}

// -------------------------------------------------------------
// Live Notification Center Handlers
// -------------------------------------------------------------
function triggerBellNotification(shouldRing = false) {
  const bellBtn = document.getElementById("btnNotificationBell");
  const bellBadge = document.getElementById("bellBadge");
  if (!bellBtn || !bellBadge) return;

  const unreadCount = liveNotifications.filter(n => !n.read).length;

  if (unreadCount > 0) {
    bellBadge.textContent = unreadCount > 99 ? "99+" : unreadCount;
    bellBadge.classList.add("active");
    bellBadge.style.display = "flex";
  } else {
    bellBadge.textContent = "0";
    bellBadge.classList.remove("active");
    bellBadge.style.display = "none";
  }

  // Play gentle alert sound & trigger bell shake animation ONLY when new arrivals occur
  if (shouldRing && unreadCount > 0) {
    playNotificationSound();
    bellBtn.classList.remove("ring");
    void bellBtn.offsetWidth; // trigger reflow
    bellBtn.classList.add("ring");
    setTimeout(() => bellBtn.classList.remove("ring"), 700);
  }
}

function renderNotificationList() {
  const listEl = document.getElementById("notifList");
  if (!listEl) return;

  if (liveNotifications.length === 0) {
    listEl.innerHTML = `
      <div class="notif-empty">
        <i class="fa-regular fa-bell-slash"></i>
        <span>No active alerts. Listening for live RPA complaints...</span>
      </div>
    `;
    return;
  }

  listEl.innerHTML = liveNotifications.map((n, idx) => `
    <div class="notif-item ${n.read ? '' : 'unread'}" onclick="handleNotifClick(${idx}, '${n.id}')">
      <div class="notif-icon-col">
        <i class="fa-solid fa-triangle-exclamation"></i>
      </div>
      <div class="notif-content-col">
        <div class="notif-top-row">
          <span class="notif-ticket-tag">${n.ticket_number}</span>
          <span class="notif-time">${n.time}</span>
        </div>
        <div class="notif-title">${escapeHtml(n.full_name)} • ${formatCurrency(n.amount)}</div>
        <div class="notif-desc">${escapeHtml(n.incident_type)} (${escapeHtml(n.channel)})</div>
      </div>
    </div>
  `).join("");
}

window.handleNotifClick = function(notifIndex, ticketId) {
  if (liveNotifications[notifIndex]) {
    liveNotifications[notifIndex].read = true;
    saveNotifications();
  }
  triggerBellNotification(false);
  renderNotificationList();

  const dropdown = document.getElementById("notifDropdown");
  if (dropdown) {
    dropdown.classList.remove("open");
    dropdown.style.display = "none";
  }

  // Open the incident dossier slide-over
  if (ticketId) {
    openIncidentDossier(ticketId);
  }
};

function markAllNotifsRead() {
  liveNotifications.forEach(n => n.read = true);
  saveNotifications();
  triggerBellNotification(false);
  renderNotificationList();
  showToast("All notifications marked as read & alerts cleared", "info");
}

function clearAllNotifs() {
  liveNotifications = [];
  saveNotifications();
  triggerBellNotification(false);
  renderNotificationList();
  showToast("Notification inbox cleared", "info");
}

function applyFilters() {
  const searchTerm = document.getElementById("ticketSearchInput").value.trim().toLowerCase();
  const severityFilter = document.getElementById("filterSeverity").value;
  const statusFilter = document.getElementById("filterStatus").value;
  const typeFilter = document.getElementById("filterIncidentType").value;

  // Primary complaints list ONLY shows active/unresolved complaints
  const activeTicketsPool = allTickets.filter(t => t.status !== 'RESOLVED');

  filteredTickets = activeTicketsPool.filter(t => {
    // Search
    const searchMatch = !searchTerm ||
      (t.ticket_number || "").toLowerCase().includes(searchTerm) ||
      (t.full_name || t.customer_name || "").toLowerCase().includes(searchTerm) ||
      (t.email || "").toLowerCase().includes(searchTerm) ||
      (t.account_number || "").toLowerCase().includes(searchTerm) ||
      (t.customer_code || "").toLowerCase().includes(searchTerm) ||
      (t.incident_type || "").toLowerCase().includes(searchTerm);

    // Severity
    const sevMatch = severityFilter === "ALL" || (t.severity || "").toUpperCase() === severityFilter.toUpperCase();

    // Status
    const statusMatch = statusFilter === "ALL" || (t.status || "").toUpperCase() === statusFilter.toUpperCase();

    // Type
    const typeMatch = typeFilter === "ALL" || (t.incident_type || "").toLowerCase().includes(typeFilter.toLowerCase());

    return searchMatch && sevMatch && statusMatch && typeMatch;
  });

  // Update left menu badge to show active complaints count
  const badgeTicketCount = document.getElementById("badgeTicketCount");
  if (badgeTicketCount && badgeTicketCount.textContent !== String(activeTicketsPool.length)) {
    badgeTicketCount.textContent = String(activeTicketsPool.length);
  }

  renderFraudTicketsTable(filteredTickets);
  updatePillCounts();
  applySolvedFilters();
  renderHomeUrgentList();
}

function applySolvedFilters() {
  const searchInput = document.getElementById("solvedSearchInput");
  const searchTerm = searchInput ? searchInput.value.trim().toLowerCase() : "";
  const filterType = document.getElementById("filterSolvedIncidentType");
  const typeFilter = filterType ? filterType.value : "ALL";

  solvedTickets = allTickets.filter(t => t.status === 'RESOLVED');

  const solvedBadge = document.getElementById("solvedCountBadge");
  if (solvedBadge) solvedBadge.textContent = solvedTickets.length;

  filteredSolvedTickets = solvedTickets.filter(t => {
    const searchMatch = !searchTerm ||
      (t.ticket_number || "").toLowerCase().includes(searchTerm) ||
      (t.full_name || t.customer_name || "").toLowerCase().includes(searchTerm) ||
      (t.email || "").toLowerCase().includes(searchTerm) ||
      (t.account_number || "").toLowerCase().includes(searchTerm) ||
      (t.customer_code || "").toLowerCase().includes(searchTerm) ||
      (t.incident_type || "").toLowerCase().includes(searchTerm);

    const typeMatch = typeFilter === "ALL" || (t.incident_type || "").toLowerCase().includes(typeFilter.toLowerCase());

    return searchMatch && typeMatch;
  });

  renderSolvedTicketsTable(filteredSolvedTickets);
}

function renderSolvedTicketsTable(tickets) {
  const tbody = document.getElementById("solvedTicketsTableBody");
  if (!tbody) return;

  const countEl = document.getElementById("visibleSolvedCount");
  if (countEl) countEl.textContent = tickets.length;

  if (tickets.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="loading-state">No solved complaints recorded yet. When a complaint is marked as Solved, it will appear here.</td></tr>`;
    renderPaginationControls("solvedPagination", 1, 0, solvedPageSize, "changeSolvedPage");
    return;
  }

  // Slicing for pagination (10 solved complaints per page)
  const totalItems = tickets.length;
  const totalPages = Math.ceil(totalItems / solvedPageSize) || 1;
  if (solvedCurrentPage > totalPages) solvedCurrentPage = totalPages;
  if (solvedCurrentPage < 1) solvedCurrentPage = 1;

  const startIndex = (solvedCurrentPage - 1) * solvedPageSize;
  const paginatedSolvedTickets = tickets.slice(startIndex, startIndex + solvedPageSize);

  tbody.innerHTML = paginatedSolvedTickets.map(t => {
    return `
      <tr>
        <td>
          <span class="code-font" style="font-weight: 600; color: #1c1917;">${t.ticket_number}</span>
        </td>
        <td>
          <div class="customer-cell">
            <span class="customer-name">${escapeHtml(t.full_name)}</span>
            ${formatLocation(t.city, t.state, t.phone) ? `<span class="customer-sub">${escapeHtml(formatLocation(t.city, t.state, t.phone))}</span>` : ''}
          </div>
        </td>
        <td>
          <div class="customer-cell">
            <span class="customer-name" style="font-size: 11.5px; color: var(--text-muted);">${escapeHtml(t.email)}</span>
            <span class="customer-sub code-font">${escapeHtml(t.customer_code)}</span>
          </div>
        </td>
        <td>
          <div class="customer-cell">
            <span class="code-font" style="color: var(--text-main); font-weight: 500;">${t.account_number}</span>
            <span class="customer-sub">${t.account_type || 'SAVINGS'}</span>
          </div>
        </td>
        <td>
          <span style="color: var(--text-main); font-size: 12.5px; font-weight: 400;">${escapeHtml(t.incident_type)}</span>
          <div style="font-size: 10.5px; color: var(--text-dim); margin-top: 2px;">
            <i class="fa-solid fa-satellite-dish" style="font-size: 9px;"></i> ${escapeHtml(t.reported_channel)}
          </div>
        </td>
        <td>
          <div class="amount-font highlight-amber">${formatCurrency(t.amount_involved)}</div>
        </td>
        <td>
          <div class="amount-font highlight-emerald">${formatCurrency(t.recovered_amount || t.amount_involved)}</div>
        </td>
        <td>
          <span class="tag-pill tag-resolved"><i class="fa-solid fa-circle-check"></i> SOLVED</span>
        </td>
        <td>
          <span style="font-size: 12px; color: var(--text-muted);">${escapeHtml(t.assigned_investigator ? String(t.assigned_investigator).split('(')[0].trim() : 'Branch Officer')}</span>
        </td>
        <td style="text-align: right;">
          <button class="btn btn-xs btn-outline" onclick="openIncidentDossier('${t.ticket_id}')">
            <i class="fa-solid fa-eye"></i> View Details
          </button>
        </td>
      </tr>
    `;
  }).join("");

  renderPaginationControls("solvedPagination", solvedCurrentPage, totalItems, solvedPageSize, "changeSolvedPage");
}

function exportSolvedCSV() {
  if (solvedTickets.length === 0) {
    showToast("No solved complaints to export", "warning");
    return;
  }
  const headers = ["Complaint_Number", "Customer_Name", "Email", "Account_Number", "Fraud_Type", "Reported_Amount", "Recovered_Amount", "Status", "Handled_By", "Created_At"];
  const rows = solvedTickets.map(t => [
    `"${t.ticket_number}"`,
    `"${t.full_name}"`,
    `"${t.email}"`,
    `"${t.account_number}"`,
    `"${t.incident_type}"`,
    t.amount_involved,
    t.recovered_amount || 0,
    `"${t.status}"`,
    `"${t.assigned_investigator || ''}"`,
    `"${t.created_at || ''}"`
  ]);

  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `Solved_Fraud_Complaints_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast(`Exported ${solvedTickets.length} solved complaints to CSV`, "success");
}

function renderFraudTicketsTable(tickets) {
  const tbody = document.getElementById("fraudTicketsTableBody");
  document.getElementById("visibleTicketCount").textContent = tickets.length;

  if (tickets.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="loading-state">No fraud tickets match your current filters.</td></tr>`;
    renderPaginationControls("ticketsPagination", 1, 0, ticketPageSize, "changeTicketPage");
    return;
  }

  // Slicing for pagination (10 complaints per page)
  const totalItems = tickets.length;
  const totalPages = Math.ceil(totalItems / ticketPageSize) || 1;
  if (ticketCurrentPage > totalPages) ticketCurrentPage = totalPages;
  if (ticketCurrentPage < 1) ticketCurrentPage = 1;

  const startIndex = (ticketCurrentPage - 1) * ticketPageSize;
  const paginatedTickets = tickets.slice(startIndex, startIndex + ticketPageSize);

  // Synchronize master checkbox state with current page tickets
  const selectAllCheckbox = document.getElementById("selectAllTicketsCheckbox");
  if (selectAllCheckbox) {
    const visibleSelectedCount = paginatedTickets.filter(t => selectedTicketIds.has(String(t.ticket_id))).length;
    selectAllCheckbox.checked = paginatedTickets.length > 0 && visibleSelectedCount === paginatedTickets.length;
    selectAllCheckbox.indeterminate = visibleSelectedCount > 0 && visibleSelectedCount < paginatedTickets.length;
  }

  tbody.innerHTML = paginatedTickets.map(t => {
    const statusBadge = getStatusBadgeHtml(t.status);
    const newClass = t.isNew ? 'new-ticket-row' : '';
    const isChecked = selectedTicketIds.has(String(t.ticket_id)) ? 'checked' : '';

    return `
      <tr class="${newClass}" style="${isChecked ? 'background-color: #fff7ed;' : ''}">
        <td style="text-align: center; width: 38px;">
          <input type="checkbox" class="ticket-select-checkbox table-checkbox" data-ticket-id="${t.ticket_id}" ${isChecked}>
        </td>
        <td>
          <span class="code-font" style="font-weight: 600; color: #0f172a;">${escapeHtml(t.ticket_number)}</span>
          ${t.isNew ? '<span class="tag-pill" style="background: var(--brand-orange, #f87917); color: #fff; font-size: 9px; font-weight: 700; margin-left: 6px; padding: 1px 5px; border-radius: 4px;">NEW</span>' : ''}
        </td>
        <td>
          <span style="font-weight: 600; color: #1e293b; font-size: 13px;">${escapeHtml(t.full_name)}</span>
        </td>
        <td>
          <span class="code-font" style="color: #475569; font-weight: 500; font-size: 12px;">${escapeHtml(t.account_number)}</span>
        </td>
        <td>
          <span style="color: #334155; font-size: 12.5px; font-weight: 500;">${escapeHtml(t.incident_type)}</span>
        </td>
        <td>
          <div class="amount-font ${t.amount_involved > 50000 ? 'highlight-red' : 'highlight-amber'}" style="font-weight: 700; font-size: 12.5px;">
            ${formatCurrency(t.amount_involved)}
          </div>
        </td>
        <td>${statusBadge}</td>
        <td style="text-align: right;">
          <button class="btn btn-xs btn-outline" onclick="openIncidentDossier('${t.ticket_id}')">
            <i class="fa-solid fa-eye"></i> View Details
          </button>
        </td>
      </tr>
    `;
  }).join("");

  renderPaginationControls("ticketsPagination", ticketCurrentPage, totalItems, ticketPageSize, "changeTicketPage");
}

// -------------------------------------------------------------
// Pagination Controls Generator & Handlers
// -------------------------------------------------------------
function renderPaginationControls(containerId, currentPage, totalItems, pageSize, changePageFnName, itemLabel = "records") {
  const container = document.getElementById(containerId);
  if (!container) return;

  const totalPages = Math.ceil(totalItems / pageSize) || 1;

  if (totalItems === 0) {
    container.innerHTML = `
      <div class="pagination-info">
        <span>No matching ${escapeHtml(itemLabel)} found</span>
      </div>
      <div class="pagination-nav">
        <span class="pagination-page-size-tag">${pageSize} per page</span>
      </div>
    `;
    return;
  }

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  // Generate numbered page buttons
  let pagesHtml = '';
  const maxButtons = 5;
  let startPage = Math.max(1, currentPage - 2);
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  if (endPage - startPage < maxButtons - 1) {
    startPage = Math.max(1, endPage - maxButtons + 1);
  }

  if (startPage > 1) {
    pagesHtml += `<button class="pagination-btn" onclick="${changePageFnName}(1)" title="Page 1">1</button>`;
    if (startPage > 2) {
      pagesHtml += `<span class="pagination-ellipsis">…</span>`;
    }
  }

  for (let p = startPage; p <= endPage; p++) {
    const activeClass = p === currentPage ? 'active' : '';
    pagesHtml += `<button class="pagination-btn ${activeClass}" onclick="${changePageFnName}(${p})" title="Page ${p}">${p}</button>`;
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      pagesHtml += `<span class="pagination-ellipsis">…</span>`;
    }
    pagesHtml += `<button class="pagination-btn" onclick="${changePageFnName}(${totalPages})" title="Page ${totalPages}">${totalPages}</button>`;
  }

  const prevDisabled = currentPage <= 1 ? 'disabled' : '';
  const nextDisabled = currentPage >= totalPages ? 'disabled' : '';

  container.innerHTML = `
    <div class="pagination-info">
      <span>Showing <strong>${startItem} - ${endItem}</strong> of <strong>${totalItems}</strong> ${escapeHtml(itemLabel)}</span>
      <span class="pagination-page-size-tag"><i class="fa-solid fa-list-ol"></i> ${pageSize} per page</span>
    </div>
    <div class="pagination-nav">
      <button class="pagination-btn" ${prevDisabled} onclick="${changePageFnName}(${currentPage - 1})" title="Previous Page">
        <i class="fa-solid fa-chevron-left"></i> Previous
      </button>
      ${pagesHtml}
      <button class="pagination-btn" ${nextDisabled} onclick="${changePageFnName}(${currentPage + 1})" title="Next Page">
        Next <i class="fa-solid fa-chevron-right"></i>
      </button>
    </div>
  `;
}

window.changeTicketPage = function(newPage) {
  const totalPages = Math.ceil(filteredTickets.length / ticketPageSize) || 1;
  if (newPage < 1) newPage = 1;
  if (newPage > totalPages) newPage = totalPages;
  ticketCurrentPage = newPage;
  renderFraudTicketsTable(filteredTickets);
  const tableEl = document.getElementById("fraudTicketsTable");
  if (tableEl) {
    const rect = tableEl.getBoundingClientRect();
    if (rect.top < 0) {
      tableEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
};

window.changeSolvedPage = function(newPage) {
  const totalPages = Math.ceil(filteredSolvedTickets.length / solvedPageSize) || 1;
  if (newPage < 1) newPage = 1;
  if (newPage > totalPages) newPage = totalPages;
  solvedCurrentPage = newPage;
  renderSolvedTicketsTable(filteredSolvedTickets);
  const tableEl = document.getElementById("solvedTicketsTable");
  if (tableEl) {
    const rect = tableEl.getBoundingClientRect();
    if (rect.top < 0) {
      tableEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
};

window.changeAuditPage = function(newPage) {
  const totalPages = Math.ceil(allAuditLogs.length / auditPageSize) || 1;
  if (newPage < 1) newPage = 1;
  if (newPage > totalPages) newPage = totalPages;
  auditCurrentPage = newPage;
  renderAuditLogsTable();
  const tableEl = document.getElementById("auditTable");
  if (tableEl) {
    const rect = tableEl.getBoundingClientRect();
    if (rect.top < 0) {
      tableEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
};

// -------------------------------------------------------------
// Bulk Selection Handlers
// -------------------------------------------------------------
function updateBulkToolbar() {
  const bar = document.getElementById("bulkActionsBar");
  const countEl = document.getElementById("bulkSelectedCount");
  const count = selectedTicketIds.size;

  if (countEl) countEl.textContent = count;

  if (bar) {
    if (count > 0) {
      bar.style.display = "flex";
      
      // Check if any selected tickets are not yet blocked
      const selectedTickets = allTickets.filter(t => selectedTicketIds.has(String(t.ticket_id)));
      const unblockedCount = selectedTickets.filter(t => t.status !== 'FROZEN' && t.status !== 'BLOCKED' && t.account_status !== 'FROZEN' && t.account_status !== 'BLOCKED').length;
      const btnBulkFreeze = document.getElementById("btnBulkFreeze");
      if (btnBulkFreeze) {
        if (unblockedCount === 0) {
          btnBulkFreeze.style.display = "none";
        } else {
          btnBulkFreeze.style.display = "inline-flex";
        }
      }

      // Check if any selected tickets are not yet resolved
      const unresolvedCount = selectedTickets.filter(t => t.status !== 'RESOLVED' && t.status !== 'CLOSED').length;
      const btnBulkResolve = document.getElementById("btnBulkResolve");
      if (btnBulkResolve) {
        if (unresolvedCount === 0) {
          btnBulkResolve.style.display = "none";
        } else {
          btnBulkResolve.style.display = "inline-flex";
        }
      }
    } else {
      bar.style.display = "none";
    }
  }

  // Update master checkbox
  const selectAllCheckbox = document.getElementById("selectAllTicketsCheckbox");
  if (selectAllCheckbox) {
    const visibleSelectedCount = filteredTickets.filter(t => selectedTicketIds.has(String(t.ticket_id))).length;
    selectAllCheckbox.checked = filteredTickets.length > 0 && visibleSelectedCount === filteredTickets.length;
    selectAllCheckbox.indeterminate = visibleSelectedCount > 0 && visibleSelectedCount < filteredTickets.length;
  }
}

function clearSelectedTickets() {
  selectedTicketIds.clear();
  updateBulkToolbar();
  renderFraudTicketsTable(filteredTickets);
}

async function executeBulkAction(newStatus, actionNote) {
  if (selectedTicketIds.size === 0) return;
  const count = selectedTicketIds.size;
  const ticketIdsToUpdate = Array.from(selectedTicketIds);
  const friendlyStatus = newStatus === 'RESOLVED' ? 'Solved / Refunded' : (newStatus === 'FROZEN' ? 'Account Blocked' : (newStatus === 'ESCALATED' ? 'Escalated' : 'In Progress'));

  // For non-workflow status updates (e.g. internal triage), update in-memory state immediately
  if (newStatus !== "FROZEN" && newStatus !== "RESOLVED") {
    allTickets.forEach(t => {
      if (ticketIdsToUpdate.includes(String(t.ticket_id))) {
        t.status = newStatus;
      }
    });
    applyFilters();
    renderHomeUrgentList();
  }
  clearSelectedTickets();

  try {
    const res = await fetch("/api/fraud-tickets/bulk-update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticket_ids: ticketIdsToUpdate,
        status: newStatus,
        action_taken: actionNote || `Bulk action: ${friendlyStatus}`
      })
    });

    const data = await res.json();
    if (data.success) {
      if (newStatus === "FROZEN" || newStatus === "RESOLVED") {
        const wfCount = data.dispatched_workflows || count;
        showToast(`⚡ Dispatched ${wfCount} T4 workflow(s) for ${friendlyStatus}. Records will reflect once T4 execution completes.`, "info");
      } else {
        showToast(`Successfully updated ${data.updated_count} complaint(s) to "${friendlyStatus}"`, "success");
      }
      loadAllData();
    } else {
      showToast("Bulk action failed: " + (data.error || data.detail || "Unknown error"), "error");
      loadAllData();
    }
  } catch (err) {
    showToast("Error updating complaints: " + err.message, "error");
    loadAllData();
  }
}

function exportSelectedTicketsCSV() {
  if (selectedTicketIds.size === 0) {
    showToast("Please select at least one complaint to export.", "warning");
    return;
  }

  const selectedRows = allTickets.filter(t => selectedTicketIds.has(String(t.ticket_id)));
  
  const headers = ["Complaint #", "Customer Name", "Email", "Phone", "Account #", "Type", "Fraud Type", "Amount (INR)", "Recovered (INR)", "Priority", "Status", "Reported Via", "Created At"];
  const rows = selectedRows.map(t => [
    t.ticket_number,
    `"${(t.full_name || '').replace(/"/g, '""')}"`,
    t.email || '',
    t.phone || '',
    t.account_number || '',
    t.account_type || '',
    `"${(t.incident_type || '').replace(/"/g, '""')}"`,
    t.amount_involved || 0,
    t.recovered_amount || 0,
    t.severity || '',
    t.status || '',
    `"${(t.reported_channel || '').replace(/"/g, '""')}"`,
    t.created_at || ''
  ]);

  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `Selected_Fraud_Complaints_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  showToast(`Exported ${selectedRows.length} selected complaints to CSV file`, "success");
}

function updatePillCounts() {
  const crit = allTickets.filter(t => t.severity === "CRITICAL").length;
  const high = allTickets.filter(t => t.severity === "HIGH").length;
  const med = allTickets.filter(t => t.severity === "MEDIUM").length;
  const res = allTickets.filter(t => t.status === "RESOLVED").length;

  document.getElementById("pillCritCount").textContent = `${crit} Urgent`;
  document.getElementById("pillHighCount").textContent = `${high} High`;
  document.getElementById("pillMedCount").textContent = `${med} Medium`;
  document.getElementById("pillResCount").textContent = `${res} Solved`;
}

// 5. Incident Dossier Slide-Over
window.openIncidentDossier = async function(ticketId) {
  try {
    const tId = (typeof ticketId === 'object' && ticketId !== null) ? (ticketId.ticket_id || ticketId.id) : ticketId;
    const res = await fetch(`/api/fraud-tickets/${tId}`);
    if (!res.ok) throw new Error("Ticket not found");
    const rawData = await res.json();

    const ticket = rawData.ticket ? {
      ...rawData.ticket,
      customer_code: rawData.customer?.customer_code || rawData.ticket.customer_code || 'CUST-GEN',
      full_name: rawData.customer?.full_name || rawData.customer?.customer_name || rawData.ticket.customer_name || 'Customer',
      customer_name: rawData.customer?.customer_name || rawData.ticket.customer_name || 'Customer',
      email: rawData.customer?.email || rawData.ticket.email || 'N/A',
      phone: rawData.customer?.phone || rawData.ticket.phone || 'N/A',
      risk_tier: rawData.customer?.risk_tier || rawData.ticket.risk_tier || rawData.ticket.severity || 'LOW',
      account_type: rawData.accounts?.[0]?.account_type || rawData.ticket.account_type || 'CHECKING',
      balance: rawData.accounts?.[0]?.balance !== undefined ? rawData.accounts[0].balance : (rawData.ticket.balance || 0),
      account_status: rawData.accounts?.[0]?.status || rawData.ticket.account_status || 'ACTIVE',
      transactions: rawData.transactions || rawData.ticket.transactions || [],
      audit_logs: rawData.audit_logs || rawData.ticket.audit_logs || []
    } : rawData;

    currentDossierTicket = ticket;

    const tNumEl = document.getElementById("drawerTicketNumber");
    if (tNumEl) tNumEl.textContent = ticket.ticket_number || `#${ticket.ticket_id}`;
    
    // Severity badge in drawer
    const sevBadge = document.getElementById("drawerSeverityBadge");
    if (sevBadge) {
      const sev = (ticket.severity || "MEDIUM").toLowerCase();
      sevBadge.className = `tag-pill tag-${sev}`;
      sevBadge.textContent = ticket.severity || "MEDIUM";
    }

    // Helper to safely assign text
    const setTxt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = (val !== undefined && val !== null && val !== "") ? val : "N/A";
    };

    // Victim details
    setTxt("dossierName", ticket.full_name || ticket.customer_name);
    setTxt("dossierCode", ticket.customer_code || "CUST-GEN");
    setTxt("dossierEmail", ticket.email || "N/A");
    setTxt("dossierPhone", ticket.phone || "N/A");
    setTxt("dossierAccount", ticket.account_number || "N/A");
    setTxt("dossierBalance", `${ticket.account_type || 'CHECKING'} (${formatCurrency(ticket.balance || 0)}) - ${ticket.account_status || 'ACTIVE'}`);

    // Forensics
    setTxt("dossierType", ticket.incident_type || "Fraud Incident");
    setTxt("dossierAmount", formatCurrency(ticket.amount_involved || 0));
    setTxt("dossierRecovered", formatCurrency(ticket.recovered_amount || 0));
    setTxt("dossierChannel", ticket.reported_channel || "Portal");
    setTxt("dossierIp", ticket.flagged_ip_or_location || "N/A");
    setTxt("dossierSuspect", ticket.suspect_entity || "Under Forensics Tracing");
    setTxt("dossierDescription", ticket.description || "Incident logged.");
    setTxt("dossierAction", ticket.action_taken || "Incident registered in database. Active forensics docket.");

    // Assigned Staff
    const currentStaff = ticket.assigned_investigator || (allStaffMembers.length > 0 ? (allStaffMembers[0].department ? `${allStaffMembers[0].full_name} (${allStaffMembers[0].department})` : allStaffMembers[0].full_name) : "Abhishek Malwadkar (High-Value Fraud Forensics)");
    const dossierStaffEl = document.getElementById("dossierInvestigator");
    if (dossierStaffEl) dossierStaffEl.textContent = currentStaff;
    const selectStaffEl = document.getElementById("selectDrawerStaff");
    if (selectStaffEl) {
      selectStaffEl.value = currentStaff;
      if (!selectStaffEl.value && currentStaff) {
        const staffNameOnly = currentStaff.split(" (")[0].trim().toLowerCase();
        for (let opt of selectStaffEl.options) {
          if (opt.value.toLowerCase().includes(staffNameOnly)) {
            selectStaffEl.value = opt.value;
            break;
          }
        }
      }
    }

    // Linked Transactions
    const txnListEl = document.getElementById("drawerTxnList");
    if (ticket.transactions && ticket.transactions.length > 0) {
      txnListEl.innerHTML = ticket.transactions.map(tx => `
        <div class="drawer-txn-item">
          <div style="display: flex; justify-content: space-between;">
            <strong class="code-font highlight-cyan">${tx.txn_reference}</strong>
            <span class="amount-font highlight-red">${formatCurrency(tx.amount)}</span>
          </div>
          <div style="font-size: 11px; color: var(--text-dim); margin-top: 3px;">
            Target: ${escapeHtml(tx.merchant_or_recipient)} • Score: <strong>${tx.fraud_risk_score}/100</strong> • Status: <strong>${tx.status}</strong>
          </div>
        </div>
      `).join("");
    } else {
      txnListEl.innerHTML = `<div style="font-size: 12px; color: var(--text-dim);">No transactions flagged.</div>`;
    }

    // Audit logs
    const auditListEl = document.getElementById("drawerAuditList");
    if (ticket.audit_logs && ticket.audit_logs.length > 0) {
      auditListEl.innerHTML = ticket.audit_logs.map(log => `
        <div class="drawer-audit-item">
          <div style="display: flex; justify-content: space-between; font-size: 11px;">
            <strong>${escapeHtml(log.actor)}</strong>
            <span style="color: var(--text-dim);">${formatDate(log.created_at)}</span>
          </div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px;">${escapeHtml(log.details)}</div>
        </div>
      `).join("");
    } else {
      auditListEl.innerHTML = `<div style="font-size: 12px; color: var(--text-dim);">No prior audit history.</div>`;
    }

    // Check if account/ticket is already blocked
    const isBlocked = (ticket.account_status === 'FROZEN' || ticket.account_status === 'BLOCKED' || ticket.status === 'FROZEN' || ticket.status === 'BLOCKED');
    const btnFreeze = document.getElementById("btnDrawerFreeze");
    const alertBlocked = document.getElementById("drawerBlockedAlert");
    if (btnFreeze) {
      btnFreeze.style.display = "block";
      if (isBlocked) {
        btnFreeze.className = "btn btn-outline btn-block";
        btnFreeze.style.borderColor = "#10b981";
        btnFreeze.style.color = "#047857";
        btnFreeze.innerHTML = `<i class="fa-solid fa-lock-open"></i> Unblock Customer Account`;
        btnFreeze.onclick = handleUnblockAction;
      } else {
        btnFreeze.className = "btn btn-danger btn-block";
        btnFreeze.style.borderColor = "";
        btnFreeze.style.color = "";
        btnFreeze.innerHTML = `<i class="fa-solid fa-lock"></i> Temporarily Block Customer Account`;
        btnFreeze.onclick = handleFreezeAction;
      }
    }
    if (alertBlocked) alertBlocked.style.display = isBlocked ? "block" : "none";

    // Check if ticket is already resolved
    const isResolved = (ticket.status === 'RESOLVED' || ticket.status === 'CLOSED');
    const btnResolve = document.getElementById("btnDrawerResolve");
    const alertResolved = document.getElementById("drawerResolvedAlert");
    if (btnResolve) {
      btnResolve.style.display = "inline-flex";
      btnResolve.innerHTML = isResolved
        ? `<i class="fa-solid fa-circle-check"></i> Re-Trigger T4 Resolve`
        : `<i class="fa-solid fa-circle-check"></i> Mark as Solved / Refunded`;
    }
    if (alertResolved) alertResolved.style.display = isResolved ? "block" : "none";

    document.getElementById("drawerOverlay").classList.add("open");
  } catch (err) {
    console.error("Error opening ticket dossier:", err);
  }
};

// 6. Actions in Drawer
async function handleFreezeAction() {
  if (!currentDossierTicket) return;
  const accNum = currentDossierTicket.account_number;
  const ticketNum = currentDossierTicket.ticket_number;

  const btnFreeze = document.getElementById("btnDrawerFreeze");
  if (btnFreeze) {
    btnFreeze.disabled = true;
    btnFreeze.innerHTML = `<div class="spinner" style="width: 14px; height: 14px; border-width: 2px;"></div> Dispatching T4 Workflow...`;
  }

  try {
    const res = await fetch("/api/workflow/block-account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_number: accNum, ticket_number: ticketNum })
    });
    const data = await res.json();
    if (data.success) {
      currentDossierTicket.status = "FROZEN";
      currentDossierTicket.account_status = "FROZEN";
      allTickets.forEach(t => {
        if (t.ticket_number === ticketNum || String(t.ticket_id) === String(currentDossierTicket.ticket_id) || (accNum && t.account_number === accNum && t.status !== "RESOLVED" && t.status !== "CLOSED")) {
          t.status = "FROZEN";
          t.account_status = "FROZEN";
        }
      });
      applyFilters();
      loadAllData();
      document.getElementById("drawerOverlay").classList.remove("open");
    } else {
      console.error("Workflow trigger failed:", data.message || data.detail);
    }
  } catch (err) {
    console.error("Could not block account:", err);
  } finally {
    if (btnFreeze) {
      btnFreeze.disabled = false;
      btnFreeze.innerHTML = `<i class="fa-solid fa-lock"></i> Temporarily Block Customer Account`;
    }
  }
}

async function handleUnblockAction() {
  if (!currentDossierTicket) return;
  const accNum = currentDossierTicket.account_number;
  const ticketNum = currentDossierTicket.ticket_number;

  const btnFreeze = document.getElementById("btnDrawerFreeze");
  if (btnFreeze) {
    btnFreeze.disabled = true;
    btnFreeze.innerHTML = `<div class="spinner" style="width: 14px; height: 14px; border-width: 2px;"></div> Unblocking on T4...`;
  }

  try {
    const res = await fetch("/api/workflow/unblock-account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_number: accNum, ticket_number: ticketNum })
    });
    const data = await res.json();
    if (data.success) {
      currentDossierTicket.account_status = "ACTIVE";
      if (currentDossierTicket.status === "FROZEN") {
        currentDossierTicket.status = "UNDER_INVESTIGATION";
      }
      allTickets.forEach(t => {
        if (t.account_number === accNum) {
          t.account_status = "ACTIVE";
          if (t.status === "FROZEN") t.status = "UNDER_INVESTIGATION";
        }
      });
      applyFilters();
      loadAllData();
      document.getElementById("drawerOverlay").classList.remove("open");
    } else {
      console.error("Unblock failed:", data.message || data.detail);
    }
  } catch (err) {
    console.error("Could not unblock account:", err);
  } finally {
    if (btnFreeze) {
      btnFreeze.disabled = false;
      btnFreeze.innerHTML = `<i class="fa-solid fa-lock-open"></i> Unblock Customer Account`;
    }
  }
}

async function handleStatusUpdate(newStatus) {
  if (!currentDossierTicket) return;
  const ticketId = currentDossierTicket.ticket_id;
  const ticketNum = currentDossierTicket.ticket_number;
  const accNum = currentDossierTicket.account_number || "";

  try {
    let res;
    if (newStatus === "RESOLVED") {
      res = await fetch("/api/workflow/resolve-ticket", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticket_id: ticketId,
          ticket_number: ticketNum,
          account_number: accNum,
          action_taken: `Dispute verified and resolved. Refund credited back to customer on ${new Date().toLocaleDateString()}`
        })
      });
    } else {
      res = await fetch(`/api/fraud-tickets/${ticketId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: newStatus,
          action_taken: `Staff updated status to ${newStatus} on ${new Date().toLocaleDateString()}`
        })
      });
    }
    const data = await res.json();
    if (data.success) {
      currentDossierTicket.status = newStatus;
      allTickets.forEach(t => {
        if (String(t.ticket_id) === String(ticketId) || t.ticket_number === ticketNum) {
          t.status = newStatus;
        }
      });
      applyFilters();
      loadAllData();
      document.getElementById("drawerOverlay").classList.remove("open");
    } else {
      console.error("Error updating status:", data.message || data.detail);
    }
  } catch (err) {
    console.error("Could not update status:", err);
  }
}

// 7. Create New Fraud Ticket Form with Preset Priority
function getPriorityForAmount(amt) {
  const num = parseFloat(amt) || 0;
  if (num >= 100000) {
    return {
      level: "CRITICAL",
      label: "Urgent Priority (₹1,00,000+)",
      tagClass: "tag-critical",
      icon: "fa-triangle-exclamation"
    };
  }
  if (num >= 50000) {
    return {
      level: "HIGH",
      label: "High Priority (₹50,000 - ₹1,00,000)",
      tagClass: "tag-high",
      icon: "fa-circle-exclamation"
    };
  }
  if (num >= 10000) {
    return {
      level: "MEDIUM",
      label: "Medium Priority (₹10,000 - ₹50,000)",
      tagClass: "tag-medium",
      icon: "fa-shield-halved"
    };
  }
  return {
    level: "LOW",
    label: "Normal Priority (< ₹10,000)",
    tagClass: "tag-low",
    icon: "fa-circle-info"
  };
}

function updatePresetPriority() {
  const amountInput = document.getElementById("formAmount");
  const badgeEl = document.getElementById("formSeverityBadge");
  const hiddenInput = document.getElementById("formSeverity");
  if (!amountInput || !badgeEl || !hiddenInput) return;

  const priorityInfo = getPriorityForAmount(amountInput.value);
  hiddenInput.value = priorityInfo.level;
  badgeEl.className = `tag-pill ${priorityInfo.tagClass}`;
  badgeEl.innerHTML = `<i class="fa-solid ${priorityInfo.icon}"></i> ${priorityInfo.label}`;
}

async function handleReassignStaff() {
  if (!currentDossierTicket) return;
  const newStaff = document.getElementById("selectDrawerStaff").value;
  const ticketId = currentDossierTicket.ticket_id;
  const ticketNum = currentDossierTicket.ticket_number;

  // Optimistically update in-memory state
  currentDossierTicket.assigned_investigator = newStaff;
  const match = allTickets.find(t => String(t.ticket_id) === String(ticketId) || t.ticket_number === ticketNum);
  if (match) match.assigned_investigator = newStaff;
  
  const dossierStaffEl = document.getElementById("dossierInvestigator");
  if (dossierStaffEl) dossierStaffEl.textContent = newStaff;

  applyFilters();

  try {
    const res = await fetch(`/api/fraud-tickets/${ticketId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assigned_investigator: newStaff,
        action_taken: `Staff reassigned complaint to ${newStaff}`
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Complaint ${ticketNum} reassigned to ${newStaff}`, "success");
      loadAllData();
    }
  } catch (err) {
    showToast("Error reassigning staff: " + err.message, "error");
  }
}

async function executeBulkStaffAssign(newStaff) {
  if (selectedTicketIds.size === 0) {
    showToast("Please select at least one complaint to assign staff.", "warning");
    return;
  }

  const ticketIdsToUpdate = Array.from(selectedTicketIds);

  // Optimistically update in-memory state
  allTickets.forEach(t => {
    if (ticketIdsToUpdate.includes(String(t.ticket_id))) {
      t.assigned_investigator = newStaff;
    }
  });
  clearSelectedTickets();
  applyFilters();

  try {
    const res = await fetch("/api/fraud-tickets/bulk-update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticket_ids: ticketIdsToUpdate,
        assigned_investigator: newStaff,
        action_taken: `Bulk assigned complaints to ${newStaff}`
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Successfully assigned ${data.updated_count} complaints to ${newStaff}`, "success");
      loadAllData();
    } else {
      showToast("Bulk staff assignment failed: " + (data.error || data.detail || "Unknown error"), "error");
      loadAllData();
    }
  } catch (err) {
    showToast("Error updating staff: " + err.message, "error");
    loadAllData();
  }
}

// 7. Demo Presets & Fast Intake
const DEMO_FRAUD_PRESETS = [
  {
    name: "Swati Deshmukh",
    email: "swati.deshmukh467@example.com",
    phone: "+91 99382 73286",
    accNum: "ACT-BATCH-62246",
    accType: "CURRENT",
    incidentType: "Fake QR Code Scam",
    amount: 66771.55,
    suspect: "EasyLoan Mobile App Hub",
    desc: "Customer scanned unauthorized QR code at merchant outlet expecting cashback offer."
  },
  {
    name: "Vikram Iyer",
    email: "vikram.iyer972@example.com",
    phone: "+91 98174 62496",
    accNum: "ACT-BATCH-11195",
    accType: "SAVINGS",
    incidentType: "Unauthorized ATM Withdrawal",
    amount: 27651.70,
    suspect: "ATM Terminal Indiranagar Bangalore",
    desc: "Multiple cash withdrawals reported without physical ATM card or PIN shared."
  },
  {
    name: "Neha Verma",
    email: "neha.verma649@example.com",
    phone: "+91 99575 92693",
    accNum: "ACT-BATCH-83446",
    accType: "CURRENT",
    incidentType: "Fake Loan Approval Fee Scam",
    amount: 74021.43,
    suspect: "FastLoan Processing Pvt Ltd",
    desc: "Customer asked to deposit upfront verification fee for pre-approved loan disbursement."
  },
  {
    name: "Meera Singh",
    email: "meera.singh268@example.com",
    phone: "+91 99018 69905",
    accNum: "ACT-BATCH-38281",
    accType: "CURRENT",
    incidentType: "UPI Impersonation Fraud",
    amount: 35672.26,
    suspect: "QuickPay Merchant Gate #104",
    desc: "Received fake electricity bill reminder call asking to pay ₹10 via UPI approval link."
  },
  {
    name: "Aarav Patel",
    email: "aarav.patel512@example.com",
    phone: "+91 98765 43210",
    accNum: "ACT-BATCH-99412",
    accType: "SAVINGS",
    incidentType: "SIM Swap Fraud",
    amount: 125000.00,
    suspect: "Offshore Crypto Exchange Wallet",
    desc: "SIM card abruptly lost network signal; unauthorized netbanking fund transfers initiated."
  }
];

let currentDemoPresetIdx = 0;

window.openNewComplaintModal = function() {
  const modal = document.getElementById("newTicketModal");
  if (modal) {
    modal.classList.add("open");
    populateStaffDropdowns();
    updatePresetPriority();
  }
};

window.closeNewComplaintModal = function() {
  const modal = document.getElementById("newTicketModal");
  if (modal) modal.classList.remove("open");
};

window.autoFillDemoData = function() {
  const preset = DEMO_FRAUD_PRESETS[currentDemoPresetIdx % DEMO_FRAUD_PRESETS.length];
  currentDemoPresetIdx++;

  const setVal = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val;
  };

  setVal("formCustName", preset.name);
  setVal("formCustEmail", preset.email);
  setVal("formCustPhone", preset.phone);
  setVal("formAccNum", preset.accNum);
  setVal("formAccType", preset.accType);
  setVal("formIncidentType", preset.incidentType);
  setVal("formAmount", preset.amount);
  setVal("formSuspect", preset.suspect);
  setVal("formDescription", preset.desc);

  updatePresetPriority();
  showToast(`⚡ Demo autofilled: ${preset.name} (${preset.incidentType} - ₹${preset.amount.toLocaleString('en-IN')})`, "info");
};

async function handleCreateNewTicket(e) {
  e.preventDefault();
  const amt = parseFloat(document.getElementById("formAmount").value) || 0;
  const computedSeverity = getPriorityForAmount(amt).level;
  const staffAssignee = (document.getElementById("formStaffAssignee") && document.getElementById("formStaffAssignee").value)
    ? document.getElementById("formStaffAssignee").value
    : (allStaffMembers.length > 0 ? (allStaffMembers[0].department ? `${allStaffMembers[0].full_name} (${allStaffMembers[0].department})` : allStaffMembers[0].full_name) : "Abhishek Malwadkar (High-Value Fraud Forensics)");

  const payload = {
    full_name: document.getElementById("formCustName").value.trim(),
    email: document.getElementById("formCustEmail").value.trim(),
    phone: document.getElementById("formCustPhone").value.trim(),
    account_number: document.getElementById("formAccNum").value.trim(),
    account_type: document.getElementById("formAccType").value,
    incident_type: document.getElementById("formIncidentType").value,
    amount_involved: amt,
    severity: computedSeverity,
    assigned_investigator: staffAssignee,
    suspect_entity: (document.getElementById("formSuspect").value || "Unknown Beneficiary").trim(),
    description: (document.getElementById("formDescription").value || `Complaint logged for ${document.getElementById("formIncidentType").value}`).trim(),
    reported_channel: "Customer Help Desk"
  };

  try {
    const staffToken = localStorage.getItem("fraud_staff_token") || "stf_web_portal";
    const res = await fetch("/api/fraud-tickets", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${staffToken}`
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success || data.ticket_number || data.ticket_id) {
      const tNum = data.ticket_number || "FRD-2026-NEW";
      showToast(`Complaint ${tNum} created in PostgreSQL & assigned to ${staffAssignee}!`, "success");
      document.getElementById("newTicketModal")?.classList.remove("open");
      document.getElementById("newFraudTicketForm")?.reset();
      updatePresetPriority();
      loadAllData();
    } else {
      showToast("Error creating complaint: " + (data.error || data.detail || "Failed"), "error");
    }
  } catch (err) {
    showToast("Error registering complaint: " + err.message, "error");
  }
}

// 8. Customer 360 Directory
async function loadCustomers() {
  const tbody = document.getElementById("customersTableBody");
  if (!tbody) return;
  try {
    tbody.innerHTML = `<tr><td colspan="11" class="loading-state"><div class="spinner"></div> Loading customer directory from PostgreSQL...</td></tr>`;
    const res = await fetch("/api/customers");
    const data = await res.json();
    allCustomers = Array.isArray(data) ? data : [];
    filteredCustomers = [...allCustomers];
    customerCurrentPage = 1;
    applyCustomerSearch();
  } catch (err) {
    console.error("Error loading customer directory:", err);
    tbody.innerHTML = `<tr><td colspan="11" class="loading-state">Error loading customer directory.</td></tr>`;
    renderPaginationControls("customersPagination", 1, 0, customerPageSize, "changeCustomerPage", "customers");
  }
}

function applyCustomerSearch() {
  const q = (document.getElementById("custSearchInput")?.value || "").toLowerCase().trim();
  if (!q) {
    filteredCustomers = [...allCustomers];
  } else {
    filteredCustomers = allCustomers.filter(c => {
      const code = (c.customer_code || "").toLowerCase();
      const name = (c.full_name || c.customer_name || "").toLowerCase();
      const email = (c.email || "").toLowerCase();
      const phone = (c.phone || "").toLowerCase();
      const acc = (c.account_number || "").toLowerCase();
      const city = (c.city || "").toLowerCase();
      const state = (c.state || "").toLowerCase();
      return code.includes(q) || name.includes(q) || email.includes(q) || phone.includes(q) || acc.includes(q) || city.includes(q) || state.includes(q);
    });
  }
  customerCurrentPage = 1;
  renderCustomersTable();
}

function renderCustomersTable() {
  const tbody = document.getElementById("customersTableBody");
  if (!tbody) return;

  const totalItems = filteredCustomers.length;

  if (totalItems === 0) {
    tbody.innerHTML = `<tr><td colspan="11" class="loading-state">No matching customer records found.</td></tr>`;
    renderPaginationControls("customersPagination", 1, 0, customerPageSize, "changeCustomerPage", "customers");
    return;
  }

  const startIndex = (customerCurrentPage - 1) * customerPageSize;
  const paginatedCustomers = filteredCustomers.slice(startIndex, startIndex + customerPageSize);

  tbody.innerHTML = paginatedCustomers.map(c => `
    <tr>
      <td><span class="code-font highlight-cyan" style="font-weight: 700;">${c.customer_code}</span></td>
      <td>
        <div class="customer-cell">
          <span class="customer-name">${escapeHtml(c.full_name || c.customer_name)}</span>
          <span class="customer-sub">${escapeHtml(c.phone || '')}</span>
        </div>
      </td>
      <td><span style="font-size: 12px; color: var(--text-muted);">${escapeHtml(c.email)}</span></td>
      <td><span style="font-size: 12px;">${escapeHtml(formatLocation(c.city, c.state) || 'N/A')}</span></td>
      <td><span class="code-font" style="color: var(--text-main); font-weight: 600;">${c.account_number || 'ACT-PENDING'}</span></td>
      <td><span class="tag-pill tag-cyan">${c.account_type || 'CHECKING'}</span></td>
      <td><span class="amount-font highlight-emerald">${formatCurrency(c.balance)}</span></td>
      <td>
        <span class="tag-pill ${c.account_status === 'FROZEN' ? 'tag-frozen' : 'tag-resolved'}">
          ${c.account_status || 'ACTIVE'}
        </span>
      </td>
      <td>${getSeverityBadgeHtml(c.risk_tier || 'LOW')}</td>
      <td>
        <span class="tag-pill ${c.fraud_reports_count > 0 ? 'tag-critical' : 'tag-low'}">
          ${c.fraud_reports_count} Incident${c.fraud_reports_count === 1 ? '' : 's'}
        </span>
      </td>
      <td style="text-align: right;">
        <button class="btn btn-xs btn-outline" onclick="filterByCustomerName('${escapeHtml(c.full_name || c.customer_name)}')">
          <i class="fa-solid fa-list-check"></i> View Fraud
        </button>
      </td>
    </tr>
  `).join("");

  renderPaginationControls("customersPagination", customerCurrentPage, totalItems, customerPageSize, "changeCustomerPage", "customers");
}

window.changeCustomerPage = function(newPage) {
  const totalPages = Math.ceil(filteredCustomers.length / customerPageSize) || 1;
  if (newPage < 1) newPage = 1;
  if (newPage > totalPages) newPage = totalPages;
  customerCurrentPage = newPage;
  renderCustomersTable();
  const tableEl = document.getElementById("customersTable");
  if (tableEl) {
    const rect = tableEl.getBoundingClientRect();
    if (rect.top < 0) {
      tableEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
};

window.changeAuditPage = function(newPage) {
  const totalPages = Math.ceil(allAuditLogs.length / auditPageSize) || 1;
  if (newPage < 1) newPage = 1;
  if (newPage > totalPages) newPage = totalPages;
  auditCurrentPage = newPage;
  renderAuditLogsTable();
};

window.filterByCustomerName = function(name) {
  const navFraud = document.getElementById("navTabFraudTickets");
  if (navFraud) navFraud.click();
  document.getElementById("ticketSearchInput").value = name;
  applyFilters();
};

// 9. Live Transactions
async function loadTransactions() {
  const tbody = document.getElementById("txnsTableBody");
  try {
    const res = await fetch("/api/transactions");
    const txns = await res.json();

    tbody.innerHTML = txns.map(tx => `
      <tr>
        <td><span class="code-font highlight-cyan">${tx.txn_reference}</span></td>
        <td>
          <div class="customer-cell">
            <span class="customer-name">${escapeHtml(tx.full_name)}</span>
            <span class="customer-sub code-font">${tx.account_number}</span>
          </div>
        </td>
        <td><span class="code-font" style="color: var(--text-main);">${tx.account_number}</span></td>
        <td><span class="amount-font highlight-red">${formatCurrency(tx.amount)}</span></td>
        <td><span class="tag-pill tag-cyan">${tx.txn_type}</span></td>
        <td><span style="font-size: 12px;">${escapeHtml(tx.merchant_or_recipient)}</span></td>
        <td><span class="code-font" style="font-size: 11px; color: var(--text-dim);">${escapeHtml(tx.ip_address || 'Internal')}</span></td>
        <td>
          <div style="display: flex; align-items: center; gap: 8px;">
            <div class="progress-bar-wrap" style="width: 60px;">
              <div class="bar-fill ${tx.fraud_risk_score > 75 ? 'red' : 'amber'}" style="width: ${tx.fraud_risk_score}%;"></div>
            </div>
            <strong class="code-font ${tx.fraud_risk_score > 75 ? 'highlight-red' : 'highlight-amber'}">${tx.fraud_risk_score}%</strong>
          </div>
        </td>
        <td>
          <span class="tag-pill ${tx.is_fraud_flagged ? 'tag-critical' : 'tag-resolved'}">
            ${tx.is_fraud_flagged ? 'FLAGGED' : 'CLEAN'}
          </span>
        </td>
        <td>
          <span class="tag-pill ${tx.status === 'BLOCKED' ? 'tag-frozen' : (tx.status === 'HELD' ? 'tag-high' : 'tag-resolved')}">
            ${tx.status}
          </span>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="10" class="loading-state">Error loading transactions.</td></tr>`;
  }
}

// 10. Threat Analytics / Executive Charts
async function loadAnalytics() {
  try {
    const res = await fetch("/api/analytics");
    const data = await res.json();

    // Incident types bar chart
    const chartTypesEl = document.getElementById("chartIncidentTypes");
    if (chartTypesEl && data.by_type) {
      const maxCount = Math.max(...data.by_type.map(d => d.count), 1);
      chartTypesEl.innerHTML = data.by_type.map(item => {
        const pct = Math.round((item.count / maxCount) * 100);
        return `
          <div class="chart-row">
            <div class="chart-label-group">
              <span>${escapeHtml(item.type)}</span>
              <strong>${item.count} cases (${formatCurrency(item.amount)})</strong>
            </div>
            <div class="chart-bar-bg">
              <div class="chart-bar-fill" style="width: ${pct}%; background: linear-gradient(90deg, #2563eb, #38bdf8);"></div>
            </div>
          </div>
        `;
      }).join("");
    }



    // Critical queue list
    const critQueueEl = document.getElementById("criticalQueueList");
    if (critQueueEl) {
      const critTickets = allTickets.filter(t => t.severity === "CRITICAL" || t.status === "FROZEN").slice(0, 4);
      critQueueEl.innerHTML = critTickets.map(ct => `
        <div class="queue-item" onclick="openIncidentDossier('${ct.ticket_id}')">
          <div>
            <strong style="font-size: 13px; color: var(--text-main);">${escapeHtml(ct.full_name)} (${ct.ticket_number})</strong>
            <div style="font-size: 11px; color: var(--text-dim);">${escapeHtml(ct.incident_type)}</div>
          </div>
          <div style="text-align: right;">
            <div class="amount-font highlight-red">${formatCurrency(ct.amount_involved)}</div>
            <span class="tag-pill tag-critical" style="font-size: 9px; padding: 2px 6px;">${ct.status}</span>
          </div>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading analytics:", err);
  }
}

// 11. Audit Logs
async function loadAuditLogs() {
  const tbody = document.getElementById("auditTableBody");
  try {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-state"><div class="spinner"></div> Fetching staff activity logs from PostgreSQL...</td></tr>`;
    const res = await fetch("/api/audit-logs");
    const logs = await res.json();
    allAuditLogs = Array.isArray(logs) ? logs : [];
    auditCurrentPage = 1;
    renderAuditLogsTable();
  } catch (err) {
    console.error("Error loading audit logs:", err);
    tbody.innerHTML = `<tr><td colspan="7" class="loading-state">Error loading audit logs.</td></tr>`;
  }
}

function renderAuditLogsTable() {
  const tbody = document.getElementById("auditTableBody");
  if (!tbody) return;

  const totalItems = allAuditLogs.length;

  if (totalItems === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-state">No staff activity logs recorded yet.</td></tr>`;
    renderPaginationControls("auditPagination", 1, 0, auditPageSize, "changeAuditPage", "logs");
    return;
  }

  const startIndex = (auditCurrentPage - 1) * auditPageSize;
  const paginatedLogs = allAuditLogs.slice(startIndex, startIndex + auditPageSize);

  tbody.innerHTML = paginatedLogs.map(l => {
    let actionBadgeClass = "tag-medium";
    const act = (l.action || '').toUpperCase();
    if (act.includes("RESOLVED") || act.includes("SUCCESS")) {
      actionBadgeClass = "tag-resolved";
    } else if (act.includes("FROZEN") || act.includes("BLOCK") || act.includes("CRITICAL")) {
      actionBadgeClass = "tag-critical";
    } else if (act.includes("INVESTIGATION") || act.includes("CHANGED") || act.includes("REASSIGN")) {
      actionBadgeClass = "tag-high";
    }

    return `
      <tr>
        <td><span class="code-font" style="color: var(--text-dim);">#LOG-${l.log_id}</span></td>
        <td><span class="code-font highlight-cyan" style="font-weight: 700;">${escapeHtml(l.ticket_number || 'SYSTEM')}</span></td>
        <td><strong style="color: var(--text-main); font-size: 12.5px;">${escapeHtml(l.customer_name || 'System / Batch')}</strong></td>
        <td><span style="font-size: 12px; font-weight: 600; color: #334155;">${escapeHtml(l.actor || 'Staff')}</span></td>
        <td><span class="tag-pill ${actionBadgeClass}">${escapeHtml(l.action)}</span></td>
        <td><span style="font-size: 12px; color: var(--text-secondary); max-width: 320px; display: inline-block; white-space: normal; line-height: 1.4;">${escapeHtml(l.details)}</span></td>
        <td><span style="font-size: 11.5px; color: var(--text-dim); white-space: nowrap;">${formatDate(l.created_at)}</span></td>
      </tr>
    `;
  }).join("");

  renderPaginationControls("auditPagination", auditCurrentPage, totalItems, auditPageSize, "changeAuditPage", "logs");
}

// 12. PostgreSQL & pgAdmin Hub
async function loadDbStatus() {
  try {
    const res = await fetch("/api/db-status");
    const db = await res.json();
    const dbBadge = document.getElementById("dbNameBadge");
    if (dbBadge) dbBadge.textContent = db.database;
  } catch (err) {
    console.error("Error loading db status:", err);
  }
}

async function executeSQLQuery() {
  const query = document.getElementById("sqlQueryText").value.trim();
  const resultsContainer = document.getElementById("sqlResultsContainer");
  const countBadge = document.getElementById("sqlRowCountBadge");
  const statusEl = document.getElementById("sqlExecutionStatus");

  if (!query) {
    showToast("Please enter an SQL query to execute", "warning");
    return;
  }

  resultsContainer.innerHTML = `<div class="loading-state"><div class="spinner"></div> Executing SQL query against PostgreSQL...</div>`;

  try {
    const res = await fetch("/api/execute-sql", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });
    const data = await res.json();

    if (!res.ok || data.error) {
      statusEl.textContent = "Error";
      statusEl.className = "highlight-rose";
      resultsContainer.innerHTML = `<div style="padding: 20px; color: var(--rose); font-family: var(--font-mono); font-size: 12px;">PostgreSQL Error: ${escapeHtml(data.error)}</div>`;
      countBadge.textContent = "0 rows";
      return;
    }

    statusEl.textContent = "Query executed successfully";
    statusEl.className = "highlight-emerald";
    countBadge.textContent = `${data.row_count || 0} rows`;

    if (data.columns && data.rows) {
      let tableHtml = `<table class="data-table"><thead><tr>`;
      data.columns.forEach(col => {
        tableHtml += `<th>${escapeHtml(col)}</th>`;
      });
      tableHtml += `</tr></thead><tbody>`;

      data.rows.forEach(row => {
        tableHtml += `<tr>`;
        row.forEach(cell => {
          tableHtml += `<td class="code-font" style="font-size: 12px;">${cell !== null ? escapeHtml(String(cell)) : '<span style="color: var(--text-dim)">NULL</span>'}</td>`;
        });
        tableHtml += `</tr>`;
      });
      tableHtml += `</tbody></table>`;
      resultsContainer.innerHTML = tableHtml;
    } else {
      resultsContainer.innerHTML = `<div style="padding: 20px; color: var(--emerald);">${escapeHtml(data.message || 'Done')}</div>`;
    }
  } catch (err) {
    resultsContainer.innerHTML = `<div style="padding: 20px; color: var(--rose);">Execution failed: ${err.message}</div>`;
  }
}

// 13. CSV Export
function exportTicketsCSV() {
  if (allTickets.length === 0) {
    showToast("No ticket data to export", "warning");
    return;
  }

  const headers = ["Ticket Number", "Customer Name", "Customer Code", "Email", "Phone", "Account Number", "Incident Type", "Amount Flagged", "Recovered Amount", "Severity", "Status", "Investigator", "Date"];
  const rows = allTickets.map(t => [
    `"${t.ticket_number}"`,
    `"${t.full_name}"`,
    `"${t.customer_code}"`,
    `"${t.email}"`,
    `"${t.phone}"`,
    `"${t.account_number}"`,
    `"${t.incident_type}"`,
    t.amount_involved,
    t.recovered_amount,
    `"${t.severity}"`,
    `"${t.status}"`,
    `"${t.assigned_investigator}"`,
    `"${t.incident_date}"`
  ]);

  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `abc_fraud_report_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast("CSV export completed successfully", "success");
}

// Utility Helpers
function getSeverityBadgeHtml(sev) {
  const s = (sev || "MEDIUM").toUpperCase();
  if (s === "CRITICAL") return `<span class="tag-pill tag-critical"><i class="fa-solid fa-triangle-exclamation"></i> Urgent</span>`;
  if (s === "HIGH") return `<span class="tag-pill tag-high"><i class="fa-solid fa-circle-exclamation"></i> High</span>`;
  if (s === "MEDIUM") return `<span class="tag-pill tag-medium">Medium</span>`;
  return `<span class="tag-pill tag-low">Normal</span>`;
}

function getStatusBadgeHtml(status) {
  const s = (status || "OPEN").toUpperCase();
  if (s === "RESOLVED") return `<span class="tag-pill tag-resolved"><i class="fa-solid fa-circle-check"></i> Solved</span>`;
  if (s === "FROZEN") return `<span class="tag-pill tag-frozen"><i class="fa-solid fa-lock"></i> Blocked</span>`;
  if (s === "ESCALATED") return `<span class="tag-pill tag-critical"><i class="fa-solid fa-user-shield"></i> Escalated</span>`;
  if (s === "UNDER_INVESTIGATION") return `<span class="tag-pill tag-investigating"><i class="fa-solid fa-clock"></i> In Progress</span>`;
  if (s === "OPEN" || s === "NEW") return `<span class="tag-pill tag-open"><i class="fa-solid fa-bolt"></i> Urgent Open</span>`;
  return `<span class="tag-pill tag-investigating"><i class="fa-solid fa-clock"></i> ${escapeHtml(status)}</span>`;
}

function formatLocation(city, state, fallback) {
  const c = String(city || '').trim();
  const s = String(state || '').trim();
  if (c && s) return `${c}, ${s}`;
  if (c || s) return c || s;
  return fallback ? String(fallback).trim() : '';
}

function formatCurrency(val) {
  const num = typeof val === "number" ? val : parseFloat(val || 0);
  return "₹" + num.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(isoStr) {
  if (!isoStr) return "--";
  try {
    const d = new Date(isoStr);
    return d.toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return isoStr;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showToast(message, type = "info") {
  // Pop-up alerts disabled as requested: log to console only
  console.log(`[Notification ${type}]: ${message}`);
}
