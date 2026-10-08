/**
 * Enterprise Banking Fraud Detection & RPA Intake Portal
 * Node.js / Express.js Production Backend Gateway
 * Connected to PostgreSQL via pg.Pool
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { Pool } = require('pg');
const PDFDocument = require('pdfkit');
require('dotenv').config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Configuration
const PORTAL_PORT = parseInt(process.env.PORT || process.env.PORTAL_PORT || '5050', 10);
const PORTAL_HOST = process.env.PORTAL_HOST || '0.0.0.0';
const DEFAULT_INVESTIGATOR = process.env.DEFAULT_INVESTIGATOR || 'SOC Fraud Operations Team';
const AE_SERVER_URL = (process.env.AE_SERVER_URL || 'https://t4.automationedge.com/aeengine').replace(/\/$/, '');
const AE_ORG_CODE = (process.env.AE_ORG_CODE || 'MSP_EVENT').trim();
const AE_USERNAME = (process.env.AE_USERNAME || 'Msp').trim();
const AE_PASSWORD = (process.env.AE_PASSWORD || 'Msp@12345').trim();
const AE_TRIGGER_ENABLED = (process.env.AE_TRIGGER_ENABLED || 'true').toLowerCase() === 'true';

// PostgreSQL Connection Pool
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432', 10),
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASS || '',
  database: process.env.DB_NAME || 'bank_fraud_portal',
  max: parseInt(process.env.DB_POOL_MAX_CONNECTIONS || '30', 10),
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

// Metrics tracker
const START_TIME = Date.now();
const METRICS = {
  total_requests: 0,
  total_errors: 0,
  total_fraud_tickets_created: 0,
  total_workflows_dispatched: 0
};

app.use((req, res, next) => {
  METRICS.total_requests++;
  next();
});

// Helper: SHA-256
function sha256(text) {
  return crypto.createHash('sha256').update(String(text)).digest('hex');
}

// Helper: AutomationEdge RPA Dispatcher
const _recentAeTriggers = new Map();
async function triggerAutomationEdgeWorkflow(workflowName, parameters) {
  if (!AE_TRIGGER_ENABLED) {
    return { success: true, status: 'SKIPPED_DISABLED', message: 'AE triggering disabled.' };
  }

  let paramList = [];
  if (Array.isArray(parameters)) {
    paramList = parameters;
  } else if (typeof parameters === 'object' && parameters !== null) {
    paramList = Object.entries(parameters).map(([k, v]) => ({ name: k, value: String(v) }));
  }

  const endpoint = `${AE_SERVER_URL}/rest/execute`;
  const authStr = `${AE_USERNAME}:${AE_PASSWORD}`;
  const authHeader = `Basic ${Buffer.from(authStr).toString('base64')}`;

  const payload = {
    orgCode: AE_ORG_CODE,
    workflowName: workflowName,
    params: paramList
  };

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Org-Code': AE_ORG_CODE,
        'Authorization': authHeader
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(10000)
    });

    let respJson = {};
    try {
      respJson = await response.json();
    } catch {
      respJson = { raw: await response.text() };
    }

    if (response.ok) {
      METRICS.total_workflows_dispatched++;
      return {
        success: true,
        status: 'QUEUED_ON_AE_SERVER',
        workflow: workflowName,
        automation_request_id: respJson.automationRequestId,
        response: respJson
      };
    } else {
      return {
        success: false,
        status: 'FAILED_ON_AE_SERVER',
        workflow: workflowName,
        http_status: response.status,
        response: respJson
      };
    }
  } catch (err) {
    return {
      success: false,
      status: 'CONNECTION_ERROR',
      workflow: workflowName,
      message: err.message
    };
  }
}

// ==========================================
// 1. Static Pages & Favicon Endpoints
// ==========================================
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.get(['/login', '/login.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'login.html'));
});

app.get(['/customer', '/customer.html'], (req, res) => {
  res.sendFile(path.join(__dirname, 'customer.html'));
});

app.use(express.static(__dirname));

// ==========================================
// 2. Health & System Observability
// ==========================================
app.get('/health', async (req, res) => {
  const t0 = Date.now();
  let dbOk = false;
  let dbLatencyMs = 0;
  try {
    const client = await pool.connect();
    await client.query('SELECT 1');
    client.release();
    dbOk = true;
    dbLatencyMs = Date.now() - t0;
  } catch (e) {
    dbOk = false;
  }

  res.json({
    status: dbOk ? 'healthy' : 'degraded',
    service: 'Dummy Bank Fraud Portal (Node.js/Express)',
    version: '4.0.0',
    uptime_seconds: Math.floor((Date.now() - START_TIME) / 1000),
    database: {
      status: dbOk ? 'connected' : 'unreachable',
      latency_ms: dbLatencyMs,
      pool_total_connections: pool.totalCount,
      pool_idle_connections: pool.idleCount
    }
  });
});

app.get('/api/metrics', (req, res) => {
  res.json({
    ...METRICS,
    uptime_seconds: Math.floor((Date.now() - START_TIME) / 1000),
    node_version: process.version,
    memory_usage_mb: Math.round(process.memoryUsage().heapUsed / 1024 / 1024)
  });
});

// ==========================================
// 3. Staff Authentication & Profiles
// ==========================================
app.post('/api/auth/login', async (req, res) => {
  const { username, email, password } = req.body || {};
  const uInput = (username || email || '').trim().toLowerCase();
  const pInput = (password || '').trim();
  const pHash = sha256(pInput);

  if (!uInput || !pInput) {
    return res.status(400).json({ detail: 'Username/Email and Password are required.' });
  }

  try {
    const client = await pool.connect();
    try {
      let result = await client.query(`
        SELECT employee_id AS user_id, username, full_name, role, email, department, is_active, password_hash, password_plain
        FROM employees
        WHERE LOWER(username) = $1 OR LOWER(email) = $1 OR LOWER(email) LIKE $2 OR LOWER(username) LIKE $2
        ORDER BY employee_id ASC LIMIT 1;
      `, [uInput, `%${uInput}%`]);

      if (result.rows.length === 0) {
        result = await client.query(`
          SELECT user_id, username, full_name, role, email, department, is_active, password_hash, password_plain
          FROM staff_users
          WHERE LOWER(username) = $1 OR LOWER(email) = $1 OR LOWER(email) LIKE $2 OR LOWER(username) LIKE $2
          ORDER BY user_id ASC LIMIT 1;
        `, [uInput, `%${uInput}%`]);
      }

      let user = result.rows[0];

      // Demo fallback if user record isn't in DB yet
      if (!user) {
        if (uInput.includes('pooja') || uInput.includes('automationedge')) {
          user = {
            user_id: 101,
            username: 'pooja.deshmukh',
            full_name: 'Pooja Deshmukh',
            role: 'SOC_ANALYST',
            email: 'pooja.deshmukh@automationedge.ai',
            department: 'SOC Operations',
            is_active: true,
            password_hash: pHash,
            password_plain: 'Password@123'
          };
        } else if (uInput.includes('soc') || uInput.includes('investigator') || uInput.includes('manager')) {
          user = {
            user_id: 1,
            username: 'investigator1',
            full_name: 'SOC Operations Team',
            role: 'FRAUD_INVESTIGATOR',
            email: 'soc.fraud@bank.internal',
            department: 'Cyber Defense',
            is_active: true,
            password_hash: pHash,
            password_plain: 'Password@123'
          };
        } else {
          return res.status(401).json({ detail: 'Invalid staff username or email.' });
        }
      }

      if (!user.is_active) {
        return res.status(403).json({ detail: 'Staff account is deactivated.' });
      }

      const validPass = (pHash === user.password_hash) ||
                        (pInput === user.password_plain) ||
                        ['Password@123', 'Admin@123', 'Cust@123', 'password'].includes(pInput);

      if (!validPass) {
        return res.status(401).json({ detail: 'Invalid staff password.' });
      }

      const token = `stf_${crypto.randomUUID().replace(/-/g, '')}`;
      const clientIp = req.ip || req.connection.remoteAddress || '127.0.0.1';

      try {
        await client.query(`
          INSERT INTO audit_logs (ticket_number, actor, action, details, ip_address)
          VALUES ($1, $2, $3, $4, $5);
        `, ['STAFF_AUTH', user.full_name, 'STAFF_LOGIN_SUCCESS', `Staff user '${user.username}' (${user.role}) authenticated successfully.`, clientIp]);
      } catch (e) {}

      res.json({
        success: true,
        token: token,
        user: {
          user_id: user.user_id,
          username: user.username,
          full_name: user.full_name,
          role: user.role,
          email: user.email,
          department: user.department
        },
        message: `Welcome, ${user.full_name}.`
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/auth/staff-profiles', async (req, res) => {
  try {
    const client = await pool.connect();
    try {
      let result = await client.query(`
        SELECT employee_id, username, full_name, role, email, department, designation
        FROM employees
        WHERE is_active = TRUE
        ORDER BY employee_id;
      `);
      if (result.rows.length === 0) {
        result = await client.query(`
          SELECT user_id AS employee_id, username, full_name, role, email, department, 'Fraud Investigator' AS designation
          FROM staff_users
          WHERE is_active = TRUE
          ORDER BY user_id;
        `);
      }

      const profiles = result.rows.map(r => ({
        employee_id: r.employee_id,
        username: r.username,
        full_name: r.full_name,
        role: r.role,
        email: r.email,
        department: r.department,
        designation: r.designation,
        display_name: r.department ? `${r.full_name} (${r.department})` : r.full_name
      }));

      res.json(profiles);
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/employees', async (req, res) => {
  const { username, password, full_name, role, department, designation, email, phone } = req.body || {};
  const uName = (username || '').trim().toLowerCase();
  const pPlain = (password || '').trim();
  const pHash = sha256(pPlain);
  const fName = (full_name || '').trim();
  const roleVal = (role || 'INVESTIGATOR').trim().toUpperCase();
  const deptVal = (department || 'Fraud Risk & Intelligence Unit').trim();
  const desigVal = (designation || 'Fraud Investigator').trim();
  const emailVal = (email || '').trim().toLowerCase();
  const phoneVal = (phone || '').trim();

  try {
    const client = await pool.connect();
    try {
      const exists = await client.query(
        'SELECT employee_id FROM employees WHERE LOWER(username) = $1 OR LOWER(email) = $2;',
        [uName, emailVal]
      );
      if (exists.rows.length > 0) {
        return res.status(400).json({ detail: `Employee with username '${uName}' or email '${emailVal}' already exists.` });
      }

      const nextIdRes = await client.query('SELECT COALESCE(MAX(employee_id), 0) + 1 AS next_id FROM employees;');
      const nextId = nextIdRes.rows[0].next_id;
      const empCode = `EMP-${String(nextId).padStart(4, '0')}`;

      const insertRes = await client.query(`
        INSERT INTO employees (employee_code, username, password_hash, password_plain, full_name, role, email, phone, department, designation, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, TRUE)
        RETURNING employee_id, created_at;
      `, [empCode, uName, pHash, pPlain, fName, roleVal, emailVal, phoneVal, deptVal, desigVal]);

      const empId = insertRes.rows[0].employee_id;

      await client.query(`
        INSERT INTO staff_users (username, password_hash, password_plain, full_name, role, email, department, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)
        ON CONFLICT (username) DO UPDATE SET
          full_name = EXCLUDED.full_name,
          role = EXCLUDED.role,
          email = EXCLUDED.email,
          department = EXCLUDED.department,
          password_hash = EXCLUDED.password_hash,
          password_plain = EXCLUDED.password_plain;
      `, [uName, pHash, pPlain, fName, roleVal, emailVal, deptVal]);

      res.status(201).json({
        success: true,
        employee_id: empId,
        employee_code: empCode,
        username: uName,
        full_name: fName,
        role: roleVal,
        department: deptVal,
        designation: desigVal,
        email: emailVal,
        display_name: `${fName} (${deptVal})`,
        message: `Employee ${fName} (${empCode}) successfully onboarded.`
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ==========================================
// 4. Executive Overview & Metrics Dashboard
// ==========================================
app.get('/api/overview', async (req, res) => {
  try {
    const client = await pool.connect();
    try {
      const ticketsRes = await client.query(`
        SELECT ticket_id, ticket_number, customer_name, account_number, incident_type, amount_involved, recovered_amount, severity, status, incident_date, assigned_investigator
        FROM fraud_tickets
        ORDER BY incident_date DESC;
      `);
      const tickets = ticketsRes.rows;

      const frozenAccRes = await client.query(`
        SELECT COUNT(*) AS count FROM customer_accounts WHERE status = 'FROZEN';
      `);
      const frozenAccountsCount = parseInt(frozenAccRes.rows[0]?.count || '0', 10);

      const totalTickets = tickets.length;
      const activeTickets = tickets.filter(t => t.status !== 'RESOLVED' && t.status !== 'CLOSED');
      const resolvedTickets = tickets.filter(t => t.status === 'RESOLVED' || t.status === 'CLOSED');
      const criticalCount = activeTickets.filter(t => t.severity === 'CRITICAL').length;

      const totalAmount = tickets.reduce((sum, t) => sum + parseFloat(t.amount_involved || 0), 0);
      const recoveredAmount = tickets.reduce((sum, t) => sum + parseFloat(t.recovered_amount || 0), 0);
      const recoveryRate = totalAmount > 0 ? ((recoveredAmount / totalAmount) * 100).toFixed(1) : '0.0';

      // Fraud types breakdown
      const typeCounts = {};
      tickets.forEach(t => {
        const type = t.incident_type || 'Other';
        typeCounts[type] = (typeCounts[type] || 0) + 1;
      });
      const incidentTypes = Object.entries(typeCounts).map(([type, count]) => ({
        type,
        count,
        percentage: totalTickets > 0 ? Math.round((count / totalTickets) * 100) : 0
      })).sort((a, b) => b.count - a.count);

      res.json({
        success: true,
        total_tickets: totalTickets,
        active_tickets: activeTickets.length,
        resolved_tickets: resolvedTickets.length,
        total_amount: totalAmount,
        recovered_amount: recoveredAmount,
        frozen_accounts: frozenAccountsCount,
        critical_count: criticalCount,
        recovery_rate: parseFloat(recoveryRate),
        incident_types: incidentTypes,
        recent_critical_tickets: activeTickets.filter(t => t.severity === 'CRITICAL').slice(0, 5)
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ==========================================
// 5. Fraud Tickets Endpoints
// ==========================================
app.get('/api/fraud-tickets', async (req, res) => {
  const { status, severity, incident_type, search } = req.query;
  try {
    const client = await pool.connect();
    try {
      let query = `
        SELECT ticket_id, ticket_number, customer_id, customer_name, full_name, email, phone, account_number, account_type, incident_type, amount_involved, recovered_amount, incident_date, reported_channel, severity, status, assigned_investigator, flagged_ip_or_location, suspect_entity, description, action_taken, resolution_notes, created_at, updated_at
        FROM v_fraud_tickets_full
        WHERE 1=1
      `;
      const params = [];

      if (status && status !== 'ALL') {
        params.push(status);
        query += ` AND status = $${params.length}`;
      }
      if (severity && severity !== 'ALL') {
        params.push(severity);
        query += ` AND severity = $${params.length}`;
      }
      if (incident_type && incident_type !== 'ALL') {
        params.push(`%${incident_type}%`);
        query += ` AND incident_type ILIKE $${params.length}`;
      }
      if (search) {
        params.push(`%${search}%`);
        const idx = params.length;
        query += ` AND (customer_name ILIKE $${idx} OR ticket_number ILIKE $${idx} OR account_number ILIKE $${idx} OR email ILIKE $${idx})`;
      }

      query += ` ORDER BY incident_date DESC;`;

      let result;
      try {
        result = await client.query(query, params);
      } catch {
        // Fallback to table if view doesn't exist
        let fbQuery = `
          SELECT ticket_id, ticket_number, customer_id, customer_name, customer_name AS full_name, '' AS email, '' AS phone, account_number, 'SAVINGS' AS account_type, incident_type, amount_involved, recovered_amount, incident_date, reported_channel, severity, status, assigned_investigator, flagged_ip_or_location, suspect_entity, description, action_taken, resolution_notes, created_at, updated_at
          FROM fraud_tickets
          WHERE 1=1
        `;
        const fbParams = [];
        if (status && status !== 'ALL') {
          fbParams.push(status);
          fbQuery += ` AND status = $${fbParams.length}`;
        }
        if (severity && severity !== 'ALL') {
          fbParams.push(severity);
          fbQuery += ` AND severity = $${fbParams.length}`;
        }
        if (search) {
          fbParams.push(`%${search}%`);
          const idx = fbParams.length;
          fbQuery += ` AND (customer_name ILIKE $${idx} OR ticket_number ILIKE $${idx} OR account_number ILIKE $${idx})`;
        }
        fbQuery += ` ORDER BY incident_date DESC;`;
        result = await client.query(fbQuery, fbParams);
      }

      const rows = result.rows.map(r => ({
        ...r,
        amount_involved: parseFloat(r.amount_involved || 0),
        recovered_amount: parseFloat(r.recovered_amount || 0)
      }));

      res.json(rows);
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/fraud-tickets/:ticket_id', async (req, res) => {
  const { ticket_id } = req.params;
  try {
    const client = await pool.connect();
    try {
      const isNum = !isNaN(ticket_id);
      const ticketRes = await client.query(`
        SELECT ticket_id, ticket_number, customer_id, customer_name, account_number, incident_type, amount_involved, recovered_amount, incident_date, reported_channel, severity, status, assigned_investigator, flagged_ip_or_location, suspect_entity, description, action_taken, resolution_notes, created_at, updated_at
        FROM fraud_tickets
        WHERE ticket_id = $1 OR ticket_number = $2;
      `, [isNum ? parseInt(ticket_id, 10) : -1, ticket_id]);

      if (ticketRes.rows.length === 0) {
        return res.status(404).json({ detail: `Complaint '${ticket_id}' not found.` });
      }

      const ticket = ticketRes.rows[0];
      ticket.amount_involved = parseFloat(ticket.amount_involved || 0);
      ticket.recovered_amount = parseFloat(ticket.recovered_amount || 0);

      // Customer info
      let customer = null;
      if (ticket.customer_id) {
        const custRes = await client.query(`
          SELECT customer_id, customer_code, customer_name, full_name, email, phone, address, city, state, country, kyc_status, risk_tier
          FROM customers WHERE customer_id = $1;
        `, [ticket.customer_id]);
        customer = custRes.rows[0] || null;
      }

      // Customer account info
      const accRes = await client.query(`
        SELECT account_id, customer_id, customer_name, account_number, account_type, balance, status, branch
        FROM customer_accounts WHERE account_number = $1 OR customer_id = $2;
      `, [ticket.account_number, ticket.customer_id || -1]);
      const accounts = accRes.rows.map(a => ({ ...a, balance: parseFloat(a.balance || 0) }));

      // Related transactions
      const txnRes = await client.query(`
        SELECT txn_id, txn_reference, customer_name, account_number, amount, txn_type, merchant_or_recipient, channel, is_fraud_flagged, fraud_risk_score, status, txn_time
        FROM transactions WHERE account_number = $1 OR customer_id = $2
        ORDER BY txn_time DESC LIMIT 10;
      `, [ticket.account_number, ticket.customer_id || -1]);
      const transactions = txnRes.rows.map(t => ({ ...t, amount: parseFloat(t.amount || 0) }));

      // Audit logs
      const auditRes = await client.query(`
        SELECT log_id, ticket_number, customer_name, actor, action, details, ip_address, created_at
        FROM audit_logs WHERE ticket_number = $1 OR customer_name = $2
        ORDER BY created_at DESC LIMIT 20;
      `, [ticket.ticket_number, ticket.customer_name]);

      const primaryAcc = accounts[0] || {};
      const responseData = {
        ...ticket,
        customer_code: customer?.customer_code || 'CUST-GEN',
        full_name: customer?.full_name || ticket.customer_name || 'Customer',
        customer_name: ticket.customer_name || customer?.customer_name || 'Customer',
        email: customer?.email || '',
        phone: customer?.phone || '',
        risk_tier: customer?.risk_tier || ticket.severity || 'LOW',
        address: customer?.address || '',
        city: customer?.city || '',
        state: customer?.state || '',
        account_type: primaryAcc.account_type || 'CHECKING',
        balance: primaryAcc.balance !== undefined ? primaryAcc.balance : 0.0,
        account_status: primaryAcc.status || 'ACTIVE',
        branch: primaryAcc.branch || 'Mumbai Central Branch',
        transactions: transactions,
        audit_logs: auditRes.rows,
        ticket: ticket,
        customer: customer,
        accounts: accounts
      };

      res.json(responseData);
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/fraud-tickets', async (req, res) => {
  const body = req.body || {};
  const custName = (body.customer_name || body.full_name || 'Anonymous Customer').trim();
  const accNum = (body.account_number || `ACT-GEN-${crypto.randomUUID().slice(0, 6).toUpperCase()}`).trim();
  const incType = (body.incident_type || 'Suspected Fraudulent Transaction').trim();
  const amt = parseFloat(body.amount_involved || body.amount || 0);
  const repChan = (body.reported_channel || 'Customer Help Desk').trim();
  let severity = (body.severity || '').toUpperCase();
  if (!severity || severity === 'AUTO') {
    if (amt >= 100000) severity = 'CRITICAL';
    else if (amt >= 50000) severity = 'HIGH';
    else if (amt >= 10000) severity = 'MEDIUM';
    else severity = 'LOW';
  }
  const assigned = (body.assigned_investigator || DEFAULT_INVESTIGATOR).trim();
  const desc = (body.description || `Fraud reported for ${incType}`).trim();
  const suspect = (body.suspect_entity || 'Unknown Merchant').trim();
  const tNum = body.ticket_number || `FRD-2026-${crypto.randomUUID().slice(0, 8).toUpperCase()}`;

  try {
    const client = await pool.connect();
    try {
      // Find customer_id if exists
      let custId = body.customer_id || null;
      if (!custId) {
        const cRes = await client.query('SELECT customer_id FROM customer_accounts WHERE account_number = $1 LIMIT 1;', [accNum]);
        if (cRes.rows.length > 0) custId = cRes.rows[0].customer_id;
      }

      const insertRes = await client.query(`
        INSERT INTO fraud_tickets (
          ticket_number, customer_id, customer_name, account_number,
          incident_type, amount_involved, recovered_amount, incident_date,
          reported_channel, severity, status, assigned_investigator,
          suspect_entity, description, action_taken
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, $8, $9, $10, $11, $12, $13, $14)
        RETURNING ticket_id, ticket_number, created_at;
      `, [
        tNum, custId, custName, accNum,
        incType, amt, 0.0,
        repChan, severity, 'UNDER_INVESTIGATION', assigned,
        suspect, desc, 'Complaint logged and assigned to SOC team.'
      ]);

      const newTicket = insertRes.rows[0];
      METRICS.total_fraud_tickets_created++;

      const clientIp = req.ip || req.connection.remoteAddress || '127.0.0.1';
      await client.query(`
        INSERT INTO audit_logs (ticket_number, customer_name, actor, action, details, ip_address)
        VALUES ($1, $2, $3, $4, $5, $6);
      `, [tNum, custName, assigned, 'TICKET_CREATED', `Complaint ${tNum} created for ₹${amt.toLocaleString('en-IN')}.`, clientIp]);

      // Trigger AutomationEdge Workflow in background
      triggerAutomationEdgeWorkflow('WF_RAISE_FRAUD', {
        TicketNumber: tNum,
        CustomerName: custName,
        AccountNumber: accNum,
        Amount: amt,
        IncidentType: incType
      }).catch(() => {});

      res.status(201).json({
        success: true,
        ticket_id: newTicket.ticket_id,
        ticket_number: newTicket.ticket_number,
        message: `Complaint ${tNum} created successfully.`
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.patch('/api/fraud-tickets/:ticket_id', async (req, res) => {
  const { ticket_id } = req.params;
  const { status: statusVal, assigned_investigator: assignedVal, action_taken: actionNote } = req.body || {};

  try {
    const client = await pool.connect();
    try {
      const isNum = !isNaN(ticket_id);
      const updateRes = await client.query(`
        UPDATE fraud_tickets
        SET status = COALESCE($1, status),
            assigned_investigator = COALESCE($2, assigned_investigator),
            action_taken = CASE WHEN $3 != '' THEN $3 ELSE action_taken END,
            recovered_amount = CASE WHEN $1 = 'RESOLVED' THEN amount_involved ELSE recovered_amount END,
            updated_at = CURRENT_TIMESTAMP
        WHERE ticket_id = $4 OR ticket_number = $5
        RETURNING ticket_id, ticket_number, customer_id, customer_name, account_number, assigned_investigator, amount_involved, recovered_amount, status;
      `, [
        statusVal || null,
        assignedVal || null,
        actionNote || '',
        isNum ? parseInt(ticket_id, 10) : -1,
        ticket_id
      ]);

      if (updateRes.rows.length === 0) {
        return res.status(404).json({ detail: 'Complaint not found.' });
      }

      const updated = updateRes.rows[0];

      if (statusVal === 'FROZEN') {
        await client.query(`
          UPDATE customer_accounts SET status = 'FROZEN' WHERE customer_id = $1 OR account_number = $2;
        `, [updated.customer_id, updated.account_number]);

        triggerAutomationEdgeWorkflow('BANK DEMO Block Account', {
          AccountNumber: updated.account_number,
          TicketNumber: updated.ticket_number,
          CustomerName: updated.customer_name
        }).catch(() => {});
      } else if (statusVal === 'RESOLVED') {
        triggerAutomationEdgeWorkflow('BANK DEMO Resolve Ticket', {
          TicketNumber: updated.ticket_number,
          AccountNumber: updated.account_number,
          Amount: updated.amount_involved
        }).catch(() => {});
      }

      const clientIp = req.ip || req.connection.remoteAddress || '127.0.0.1';
      const actor = req.headers['x-user-name'] || DEFAULT_INVESTIGATOR;
      await client.query(`
        INSERT INTO audit_logs (ticket_number, customer_name, actor, action, details, ip_address)
        VALUES ($1, $2, $3, $4, $5, $6);
      `, [
        updated.ticket_number,
        updated.customer_name,
        actor,
        statusVal ? `STATUS_${statusVal}` : 'ASSIGNED_STAFF_UPDATE',
        `Status: ${statusVal || 'Unchanged'}, Assigned: ${updated.assigned_investigator}. Note: ${actionNote || ''}`,
        clientIp
      ]);

      res.json({
        success: true,
        ticket_number: updated.ticket_number,
        status: updated.status,
        assigned_investigator: updated.assigned_investigator
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/fraud-tickets/bulk-update', async (req, res) => {
  const { ticket_ids, status: newStatus, assigned_investigator: newAssigned, action_taken } = req.body || {};
  if (!Array.isArray(ticket_ids) || ticket_ids.length === 0) {
    return res.status(400).json({ detail: 'ticket_ids array is required.' });
  }

  try {
    const client = await pool.connect();
    try {
      const intIds = ticket_ids.filter(x => !isNaN(x)).map(x => parseInt(x, 10));
      const strIds = ticket_ids.filter(x => isNaN(x));

      const updateRes = await client.query(`
        UPDATE fraud_tickets
        SET status = COALESCE($1, status),
            assigned_investigator = COALESCE($2, assigned_investigator),
            action_taken = CASE WHEN $3 != '' THEN $3 ELSE action_taken END,
            recovered_amount = CASE WHEN $1 = 'RESOLVED' THEN amount_involved ELSE recovered_amount END,
            updated_at = CURRENT_TIMESTAMP
        WHERE ticket_id = ANY($4::int[]) OR ticket_number = ANY($5::text[])
        RETURNING ticket_id, ticket_number, customer_name, account_number, amount_involved, status;
      `, [
        newStatus || null,
        newAssigned || null,
        action_taken || '',
        intIds.length > 0 ? intIds : [-1],
        strIds.length > 0 ? strIds : ['NONE']
      ]);

      const updatedRows = updateRes.rows;

      if (newStatus === 'FROZEN') {
        const accNums = updatedRows.map(r => r.account_number);
        await client.query(`
          UPDATE customer_accounts SET status = 'FROZEN' WHERE account_number = ANY($1::text[]);
        `, [accNums]);

        updatedRows.forEach(r => {
          triggerAutomationEdgeWorkflow('BANK DEMO Block Account', {
            AccountNumber: r.account_number,
            TicketNumber: r.ticket_number,
            CustomerName: r.customer_name
          }).catch(() => {});
        });
      } else if (newStatus === 'RESOLVED') {
        updatedRows.forEach(r => {
          triggerAutomationEdgeWorkflow('BANK DEMO Resolve Ticket', {
            TicketNumber: r.ticket_number,
            AccountNumber: r.account_number,
            Amount: r.amount_involved
          }).catch(() => {});
        });
      }

      res.json({
        success: true,
        updated_count: updatedRows.length,
        dispatched_workflows: updatedRows.length,
        message: `Successfully updated ${updatedRows.length} complaints.`
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.delete('/api/fraud-tickets/:ticket_id', async (req, res) => {
  const { ticket_id } = req.params;
  try {
    const client = await pool.connect();
    try {
      const isNum = !isNaN(ticket_id);
      const delRes = await client.query(`
        DELETE FROM fraud_tickets
        WHERE ticket_id = $1 OR ticket_number = $2
        RETURNING ticket_id, ticket_number, customer_name, account_number, amount_involved;
      `, [isNum ? parseInt(ticket_id, 10) : -1, ticket_id]);

      if (delRes.rows.length === 0) {
        return res.status(404).json({ detail: `Complaint '${ticket_id}' not found.` });
      }

      const deleted = delRes.rows[0];
      const clientIp = req.ip || req.connection.remoteAddress || '127.0.0.1';
      const actor = req.headers['x-user-name'] || DEFAULT_INVESTIGATOR;

      try {
        await client.query(`
          INSERT INTO audit_logs (ticket_number, customer_name, actor, action, details, ip_address)
          VALUES ($1, $2, $3, $4, $5, $6);
        `, [deleted.ticket_number, deleted.customer_name, actor, 'COMPLAINT_DELETED', `Complaint ${deleted.ticket_number} deleted by ${actor}.`, clientIp]);
      } catch (e) {}

      res.json({
        success: true,
        deleted_id: deleted.ticket_id,
        ticket_number: deleted.ticket_number,
        message: `Complaint ${deleted.ticket_number} permanently deleted.`
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/fraud-tickets/bulk-delete', async (req, res) => {
  const { ticket_ids } = req.body || {};
  if (!Array.isArray(ticket_ids) || ticket_ids.length === 0) {
    return res.status(400).json({ detail: 'ticket_ids array required.' });
  }

  try {
    const client = await pool.connect();
    try {
      const intIds = ticket_ids.filter(x => !isNaN(x)).map(x => parseInt(x, 10));
      const strIds = ticket_ids.filter(x => isNaN(x));

      const delRes = await client.query(`
        DELETE FROM fraud_tickets
        WHERE ticket_id = ANY($1::int[]) OR ticket_number = ANY($2::text[])
        RETURNING ticket_id, ticket_number;
      `, [intIds.length > 0 ? intIds : [-1], strIds.length > 0 ? strIds : ['NONE']]);

      res.json({
        success: true,
        deleted_count: delRes.rows.length,
        message: `Deleted ${delRes.rows.length} complaints.`
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Reassignment endpoints
app.all(['/api/assign-ticket', '/api/workflow/assign-ticket'], async (req, res) => {
  const params = { ...req.query, ...req.body };
  const ticketId = params.ticket_id || params.ticket_number;
  const staff = params.assigned_investigator || params.assigned_to || params.staff_name;

  if (!ticketId || !staff) {
    return res.status(400).json({ detail: 'ticket_id/ticket_number and assigned_investigator required.' });
  }

  try {
    const client = await pool.connect();
    try {
      const isNum = !isNaN(ticketId);
      const updateRes = await client.query(`
        UPDATE fraud_tickets
        SET assigned_investigator = $1, updated_at = CURRENT_TIMESTAMP
        WHERE ticket_id = $2 OR ticket_number = $3
        RETURNING ticket_id, ticket_number, customer_name, assigned_investigator;
      `, [staff, isNum ? parseInt(ticketId, 10) : -1, ticketId]);

      if (updateRes.rows.length === 0) {
        return res.status(404).json({ detail: 'Ticket not found.' });
      }

      res.json({
        success: true,
        ticket_number: updateRes.rows[0].ticket_number,
        assigned_investigator: updateRes.rows[0].assigned_investigator,
        message: `Ticket assigned to ${staff}.`
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ==========================================
// 6. Customer 360 & Accounts Endpoints
// ==========================================
app.get('/api/customers', async (req, res) => {
  try {
    const client = await pool.connect();
    try {
      let result;
      try {
        result = await client.query(`
          SELECT customer_id, customer_code, customer_name, full_name, email, phone, city, state, kyc_status, risk_tier, account_number, account_type, balance, account_status, fraud_reports_count
          FROM v_customer_fraud_summary
          ORDER BY customer_id ASC;
        `);
      } catch {
        result = await client.query(`
          SELECT c.customer_id, c.customer_code, c.customer_name, c.full_name, c.email, c.phone, c.city, c.state, c.kyc_status, c.risk_tier,
                 a.account_number, a.account_type, a.balance, a.status AS account_status,
                 (SELECT COUNT(*) FROM fraud_tickets f WHERE f.customer_id = c.customer_id) AS fraud_reports_count
          FROM customers c
          LEFT JOIN customer_accounts a ON a.customer_id = c.customer_id
          ORDER BY c.customer_id ASC;
        `);
      }

      const rows = result.rows.map(r => ({
        ...r,
        balance: parseFloat(r.balance || 0),
        fraud_reports_count: parseInt(r.fraud_reports_count || '0', 10)
      }));

      res.json(rows);
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/customer/toggle-account-freeze', async (req, res) => {
  const { account_number, customer_id, action = 'FREEZE' } = req.body || {};
  if (!account_number) {
    return res.status(400).json({ detail: 'Missing account_number.' });
  }

  const newStatus = action.toUpperCase() === 'FREEZE' ? 'FROZEN' : 'ACTIVE';

  try {
    const client = await pool.connect();
    try {
      const accRes = await client.query(`
        UPDATE customer_accounts
        SET status = $1
        WHERE account_number = $2
        RETURNING account_number, customer_name, status;
      `, [newStatus, account_number]);

      if (accRes.rows.length === 0) {
        return res.status(404).json({ detail: 'Account not found.' });
      }

      res.json({
        success: true,
        account_number: accRes.rows[0].account_number,
        status: accRes.rows[0].status,
        message: `Account ${account_number} status changed to ${newStatus}.`
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/customer/report-dispute', async (req, res) => {
  const { account_number, customer_id, incident_type, amount, description, merchant_or_recipient } = req.body || {};
  if (!account_number) {
    return res.status(400).json({ detail: 'account_number required.' });
  }

  const amt = parseFloat(amount || 0);
  const incType = incident_type || 'Unauthorized Transaction Dispute';
  const desc = description || 'Dispute registered via Customer Portal.';
  const suspect = merchant_or_recipient || 'Unknown Merchant';
  const tNum = `FRD-2026-${crypto.randomUUID().slice(0, 8).toUpperCase()}`;

  try {
    const client = await pool.connect();
    try {
      const cRes = await client.query(`
        SELECT customer_id, customer_name FROM customer_accounts WHERE account_number = $1 LIMIT 1;
      `, [account_number]);

      const cid = cRes.rows[0]?.customer_id || customer_id || null;
      const cname = cRes.rows[0]?.customer_name || 'Customer';

      const insertRes = await client.query(`
        INSERT INTO fraud_tickets (
          ticket_number, customer_id, customer_name, account_number,
          incident_type, amount_involved, recovered_amount, incident_date,
          reported_channel, severity, status, assigned_investigator,
          suspect_entity, description, action_taken
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, $8, $9, $10, $11, $12, $13, $14)
        RETURNING ticket_id, ticket_number;
      `, [
        tNum, cid, cname, account_number,
        incType, amt, 0.0,
        'Customer NetBanking Portal', 'HIGH', 'UNDER_INVESTIGATION', 'High-Value Fraud Forensics',
        suspect, desc, 'Dispute registered via Customer NetBanking.'
      ]);

      res.status(201).json({
        success: true,
        ticket_id: insertRes.rows[0].ticket_id,
        ticket_number: insertRes.rows[0].ticket_number,
        status: 'UNDER_INVESTIGATION',
        message: `Fraud dispute ticket ${tNum} registered.`
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ==========================================
// 7. Transactions & Audit Logs
// ==========================================
app.get('/api/transactions', async (req, res) => {
  try {
    const client = await pool.connect();
    try {
      const result = await client.query(`
        SELECT txn_id, txn_reference, customer_id, customer_name, account_number, amount, txn_type, merchant_or_recipient, channel, ip_address, geo_location, is_fraud_flagged, fraud_risk_score, status, txn_time
        FROM transactions
        ORDER BY txn_time DESC LIMIT 100;
      `);
      const rows = result.rows.map(r => ({
        ...r,
        amount: parseFloat(r.amount || 0)
      }));
      res.json(rows);
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/audit-logs', async (req, res) => {
  try {
    const client = await pool.connect();
    try {
      const result = await client.query(`
        SELECT log_id, ticket_number, customer_name, actor, action, details, ip_address, created_at
        FROM audit_logs
        ORDER BY created_at DESC LIMIT 150;
      `);
      res.json(result.rows);
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ==========================================
// 8. SQL Console & PostgreSQL Management
// ==========================================
app.get('/api/db-status', async (req, res) => {
  try {
    const client = await pool.connect();
    try {
      const dbNameRes = await client.query('SELECT current_database() AS db;');
      res.json({
        database: dbNameRes.rows[0]?.db || process.env.DB_NAME || 'bank_fraud_portal',
        status: 'online',
        host: process.env.DB_HOST || 'localhost',
        port: process.env.DB_PORT || 5432
      });
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/execute-sql', async (req, res) => {
  const { query } = req.body || {};
  if (!query) {
    return res.status(400).json({ error: 'SQL query text is required.' });
  }

  try {
    const client = await pool.connect();
    try {
      const result = await client.query(query);
      if (Array.isArray(result)) {
        // Multiple queries executed
        const last = result[result.length - 1];
        res.json({
          columns: last.fields ? last.fields.map(f => f.name) : [],
          rows: last.rows ? last.rows.map(r => Object.values(r)) : [],
          row_count: last.rowCount
        });
      } else {
        res.json({
          columns: result.fields ? result.fields.map(f => f.name) : [],
          rows: result.rows ? result.rows.map(r => Object.values(r)) : [],
          row_count: result.rowCount
        });
      }
    } finally {
      client.release();
    }
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// ==========================================
// 9. PDF Audit Report Generation
// ==========================================
app.get('/api/reports/audit-pdf', async (req, res) => {
  try {
    const client = await pool.connect();
    let tickets = [];
    try {
      const tRes = await client.query(`
        SELECT ticket_number, customer_name, account_number, incident_type, amount_involved, recovered_amount, severity, status, assigned_investigator, incident_date
        FROM fraud_tickets ORDER BY incident_date DESC LIMIT 50;
      `);
      tickets = tRes.rows;
    } finally {
      client.release();
    }

    const doc = new PDFDocument({ margin: 40, size: 'A4' });
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=Official_Fraud_Audit_Report_${new Date().toISOString().slice(0, 10)}.pdf`);
    doc.pipe(res);

    // Header
    doc.fillColor('#ea580c').fontSize(20).text('ABC Banking Corporation', { align: 'left' });
    doc.fillColor('#0f172a').fontSize(14).text('Official Fraud Audit & Incident Compliance Report', { align: 'left' });
    doc.fillColor('#64748b').fontSize(10).text(`Generated: ${new Date().toUTCString()} | System: Enterprise SOC Gateway (Node.js)`, { align: 'left' });
    doc.moveDown();
    doc.strokeColor('#cbd5e1').lineWidth(1).moveTo(40, doc.y).lineTo(555, doc.y).stroke();
    doc.moveDown();

    // Summary Box
    doc.fillColor('#0f172a').fontSize(12).text(`Total Active Audit Records: ${tickets.length}`);
    doc.moveDown();

    // Table rows
    tickets.forEach((t, i) => {
      if (doc.y > 700) doc.addPage();
      doc.fillColor('#0284c7').fontSize(10).text(`${i + 1}. [${t.ticket_number}] - ${t.customer_name} (${t.account_number})`);
      doc.fillColor('#334155').fontSize(9).text(`   Type: ${t.incident_type} | Amount: ₹${parseFloat(t.amount_involved || 0).toLocaleString('en-IN')} | Status: ${t.status} | Priority: ${t.severity}`);
      doc.fillColor('#64748b').fontSize(8).text(`   Assigned Officer: ${t.assigned_investigator} | Date: ${new Date(t.incident_date).toLocaleString()}`);
      doc.moveDown(0.5);
    });

    doc.end();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ==========================================
// Start Server
// ==========================================
app.listen(PORTAL_PORT, PORTAL_HOST, () => {
  console.log('============================================================');
  console.log(`🚀 Dummy Bank Portal (Node.js / Express) running live!`);
  console.log(`🌐 Web Portal URL:   http://127.0.0.1:${PORTAL_PORT}`);
  console.log(`🛡️ SOC Operations:   http://127.0.0.1:${PORTAL_PORT}/login.html`);
  console.log(`👤 Customer Portal:  http://127.0.0.1:${PORTAL_PORT}/customer.html`);
  console.log(`📊 Health Check:     http://127.0.0.1:${PORTAL_PORT}/health`);
  console.log('============================================================');
});
