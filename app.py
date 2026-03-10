"""
KBM Pricing Delegation & Approval Matrix - Flask Web Application
================================================================
Project Costing System (PCS) & Proposal Contract Management (PCM)
"""

import sqlite3
import hashlib
import os
import json
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, session, jsonify, g)

from config import (
    PCS_LOB_OPTIONS, PCS_TYPES, OPPORTUNITY_STATUSES, DOC_TYPES,
    PCM_CATEGORIES, STATUS_COLORS,
    DIS_BID_SIZE_LEVELS, DIS_MARGIN_MATRIX,
    DS_BID_SIZE_LEVELS, DS_SERVICES_BID_SIZE_LEVELS, DS_MARGIN_MATRIX,
    MS_BID_SIZE_LEVELS, MS_MARGIN_LEVELS,
    ES_BID_SIZE_LEVELS, ES_MARGIN_MATRIX,
    PCM_DELEGATION,
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'kbm-secret-key-change-in-production')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kbm_approval.db")


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def _hash_pw(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL DEFAULT '',
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        approval_level INTEGER DEFAULT 0,
        lob TEXT DEFAULT '',
        active INTEGER DEFAULT 1
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS pcs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_number TEXT NOT NULL,
        salesforce_number TEXT DEFAULT '',
        customer_name TEXT NOT NULL,
        lob TEXT NOT NULL,
        sub_lob TEXT NOT NULL DEFAULT '',
        section TEXT DEFAULT '',
        sub_section TEXT DEFAULT '',
        pcs_type TEXT NOT NULL DEFAULT 'New',
        reference_pcs TEXT DEFAULT '',
        bid_size REAL NOT NULL DEFAULT 0,
        total_cost REAL NOT NULL DEFAULT 0,
        selling_price REAL NOT NULL DEFAULT 0,
        profit_margin REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Draft',
        current_approver_level INTEGER DEFAULT 0,
        required_approval_level INTEGER DEFAULT 0,
        opportunity_status TEXT DEFAULT 'Qualifying',
        quality_review_type TEXT DEFAULT '',
        quality_review_status TEXT DEFAULT 'Pending',
        documents TEXT DEFAULT '[]',
        comments TEXT DEFAULT '',
        created_by TEXT DEFAULT '',
        created_at TEXT,
        updated_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS pcs_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pcs_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        action_by TEXT NOT NULL,
        level INTEGER DEFAULT 0,
        comment TEXT DEFAULT '',
        timestamp TEXT NOT NULL,
        FOREIGN KEY (pcs_id) REFERENCES pcs(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS pcm (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_number TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        pcm_category TEXT NOT NULL DEFAULT 'TSS',
        sub_lob TEXT NOT NULL,
        contract_type TEXT NOT NULL DEFAULT 'Renewal',
        list_price REAL NOT NULL DEFAULT 0,
        selling_price REAL NOT NULL DEFAULT 0,
        discount_pct REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Draft',
        current_approver TEXT DEFAULT '',
        required_approver TEXT DEFAULT '',
        comments TEXT DEFAULT '',
        created_by TEXT DEFAULT '',
        created_at TEXT,
        updated_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS pcm_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pcm_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        action_by TEXT NOT NULL,
        comment TEXT DEFAULT '',
        timestamp TEXT NOT NULL,
        FOREIGN KEY (pcm_id) REFERENCES pcm(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS cost_sheet_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pcs_id INTEGER NOT NULL UNIQUE,
        country TEXT DEFAULT 'Kuwait',
        currency TEXT DEFAULT 'KWD',
        exchange_rate REAL DEFAULT 0.3125,
        local_charges_pct REAL DEFAULT 6.45,
        customs_duty_pct REAL DEFAULT 5.0,
        nl_consolidated_pct REAL DEFAULT 2.1,
        default_cisco_discount_pct REAL DEFAULT 64.0,
        deal_id TEXT DEFAULT '',
        FOREIGN KEY (pcs_id) REFERENCES pcs(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS cost_sheet_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pcs_id INTEGER NOT NULL,
        line_number INTEGER NOT NULL,
        section TEXT DEFAULT '',
        subsection TEXT DEFAULT '',
        subsection_code TEXT DEFAULT '',
        supplier TEXT DEFAULT '',
        supplier_number TEXT DEFAULT '',
        part_number TEXT DEFAULT '',
        description TEXT DEFAULT '',
        uom TEXT DEFAULT 'EA',
        qty REAL DEFAULT 0,
        unit_list_price REAL DEFAULT 0,
        discount_pct REAL DEFAULT 0,
        total_list REAL DEFAULT 0,
        total_transfer REAL DEFAULT 0,
        total_cif REAL DEFAULT 0,
        gbm_cost REAL DEFAULT 0,
        gp_pct REAL DEFAULT 0,
        requested_sell REAL DEFAULT 0,
        local_charges_loading REAL DEFAULT 0,
        total_sell_usd REAL DEFAULT 0,
        total_local_currency REAL DEFAULT 0,
        notes TEXT DEFAULT '',
        FOREIGN KEY (pcs_id) REFERENCES pcs(id)
    )""")

    conn.commit()
    conn.close()


def seed_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count > 0:
        conn.close()
        return

    users = [
        ("presales1",  "presales1",  "Ahmad Al-Sabah",    "Pre-Sales",       0, ""),
        ("presales2",  "presales2",  "Fatima Al-Rashid",   "Pre-Sales",       0, ""),
        ("dm1",        "dm1",        "Khalid Hassan",      "Delivery Manager",  1, "DIS"),
        ("um1",        "um1",        "Sara Al-Mutawa",     "User Manager",      2, "DIS"),
        ("sddc_lead",  "sddc_lead",  "Omar Behbehani",     "SDDC & IBM Leader", 3, "DIS"),
        ("lob_dir",    "lob_dir",    "Huda Al-Kandari",    "LOB Director",      4, "DIS"),
        ("svc_lead",   "svc_lead",   "Nasser Al-Shammari", "Services Leader",     1, "Digital Solution"),
        ("ibm_lead",   "ibm_lead",   "Rania Al-Essa",      "IBM Digital Leader",  2, "Digital Solution"),
        ("svc_mgr",    "svc_mgr",    "Bader Al-Ajmi",      "Services Manager",    3, "Digital Solution"),
        ("lob_ds",     "lob_ds",     "Mona Al-Sabah",      "LOB Digital Solutions", 5, "Digital Solution"),
        ("ms_lead",    "ms_lead",    "Tariq Al-Enezi",     "MS Leader",                 1, "Managed Services"),
        ("ms_mgr",     "ms_mgr",     "Dalal Al-Fahad",     "Managed Services Manager",  3, "Managed Services"),
        ("es_lead",    "es_lead",    "Yousef Al-Dosari",   "ES Leader",            1, "Enterprise Systems"),
        ("es_mgr",     "es_mgr",     "Noura Al-Kharafi",   "ES Manager",           2, "Enterprise Systems"),
        ("dir_es",     "dir_es",     "Ali Al-Ghanim",      "Director Ent Systems", 3, "Enterprise Systems"),
        ("bfo_fin",    "bfo_fin",    "Salwa Al-Mulla",     "BFO Finance Manager", 5, ""),
        ("bfo",        "bfo",        "Waleed Al-Hamad",    "BFO",                 5, ""),
        ("cfo",        "cfo",        "Mohammed Al-Bahar",  "CFO Finance",         6, ""),
        ("ceo",        "ceo",        "Faisal Al-Ayyar",    "CEO",                 7, ""),
        ("tss_mgr",    "tss_mgr",    "Hussain Al-Qattan",  "TSS Manager",          0, "TSS"),
        ("sl_mgr",     "sl_mgr",     "Amina Al-Roumi",     "Support Line Manager", 0, "TSS"),
        ("dis_dcs",    "dis_dcs",    "Jaber Al-Ahmad",     "DIS Director of Customer Success", 0, "DIS"),
        ("bfo_financial", "bfo_financial", "Layla Al-Sager", "BFO Financial", 4, "Digital Solution"),
    ]
    for u in users:
        username, pw, full_name, role, level, lob = u
        c.execute("""INSERT INTO users (username, password, full_name, role, approval_level, lob)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (username, _hash_pw(pw), full_name, role, level, lob))
    conn.commit()
    conn.close()


def seed_sample_pcs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if c.execute("SELECT COUNT(*) FROM pcs").fetchone()[0] > 0:
        conn.close()
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Project 1: Nutanix NDB
    c.execute("""INSERT INTO pcs (project_number, salesforce_number, customer_name, lob, sub_lob,
        section, sub_section, pcs_type, bid_size, total_cost, selling_price,
        profit_margin, status, current_approver_level, required_approval_level,
        opportunity_status, quality_review_type, quality_review_status,
        comments, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    ("C5K324", "KWT-202509-97171", "ABK", "DIS", "SDDC",
     "SDDC", "SDDC - SW - New", "New",
     116832.0, 102149.0, 116832.0, 12.56,
     "Draft", 0, 4,
     "Proposing", "PQAR Lite", "Pending",
     "Nutanix Database Service - 48 vCPU cores", "presales1", now, now))
    pcs1 = c.lastrowid
    c.execute("INSERT INTO pcs_history (pcs_id, action, action_by, level, comment, timestamp) VALUES (?,?,?,?,?,?)",
        (pcs1, "PCS Created", "presales1", 0, "Nutanix NDB SDDC project for ABK", now))

    # Project 2: Cisco Networking
    c.execute("""INSERT INTO pcs (project_number, salesforce_number, customer_name, lob, sub_lob,
        section, sub_section, pcs_type, bid_size, total_cost, selling_price,
        profit_margin, status, current_approver_level, required_approval_level,
        opportunity_status, quality_review_type, quality_review_status,
        comments, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    ("C5K401", "KWT-202510-98234", "Ministry of Education", "DIS", "Networking",
     "Networking", "NW - Products Cisco", "New",
     285000.0, 228000.0, 285000.0, 20.0,
     "Submitted", 1, 2,
     "Proposing", "PQAR Lite", "Pending",
     "Campus Network Refresh - Catalyst 9300/9200", "presales1", now, now))
    pcs2 = c.lastrowid
    c.execute("INSERT INTO pcs_history (pcs_id, action, action_by, level, comment, timestamp) VALUES (?,?,?,?,?,?)",
        (pcs2, "PCS Created", "presales1", 0, "Campus Network Refresh", now))
    c.execute("INSERT INTO pcs_history (pcs_id, action, action_by, level, comment, timestamp) VALUES (?,?,?,?,?,?)",
        (pcs2, "Submitted for Approval", "presales1", 1, "Bid $285K, GP 20%", now))

    # Project 3: Security (Approved)
    c.execute("""INSERT INTO pcs (project_number, salesforce_number, customer_name, lob, sub_lob,
        section, sub_section, pcs_type, bid_size, total_cost, selling_price,
        profit_margin, status, current_approver_level, required_approval_level,
        opportunity_status, quality_review_type, quality_review_status,
        comments, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    ("C5K502", "KWT-202511-99105", "Kuwait Finance House", "DIS", "Network Security",
     "Network Security", "Security - Products Non-Cisco", "New",
     195000.0, 156000.0, 195000.0, 20.0,
     "Approved", 2, 2,
     "Negotiating", "PQAR Lite", "Approved",
     "Next-Gen Firewall & SIEM Deployment", "presales2", now, now))
    pcs3 = c.lastrowid
    c.execute("INSERT INTO pcs_history (pcs_id, action, action_by, level, comment, timestamp) VALUES (?,?,?,?,?,?)",
        (pcs3, "PCS Created", "presales2", 0, "NGFW & SIEM deployment for KFH", now))
    c.execute("INSERT INTO pcs_history (pcs_id, action, action_by, level, comment, timestamp) VALUES (?,?,?,?,?,?)",
        (pcs3, "Approved (Final)", "um1", 2, "Final approval granted", now))

    # Project 4: IBM Power
    c.execute("""INSERT INTO pcs (project_number, salesforce_number, customer_name, lob, sub_lob,
        section, sub_section, pcs_type, bid_size, total_cost, selling_price,
        profit_margin, status, current_approver_level, required_approval_level,
        opportunity_status, quality_review_type, quality_review_status,
        comments, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    ("C5K603", "KWT-202512-99501", "Kuwait Oil Company", "DIS", "IBM HW",
     "Infrastructure", "IBM HW - New (Power/Storage/FlashSystem)", "New",
     425000.0, 340000.0, 425000.0, 20.0,
     "Draft", 0, 3,
     "Qualifying", "PQAR Full", "Pending",
     "IBM Power S1022 + FlashSystem 5200 + Db2", "presales1", now, now))

    # PCM Record
    c.execute("""INSERT INTO pcm (contract_number, customer_name, pcm_category, sub_lob, contract_type,
        list_price, selling_price, discount_pct, status, current_approver,
        required_approver, comments, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    ("PCM-2025-0041", "ABK", "DIS", "NW Maintenance", "Renewal",
     52416.0, 48222.72, 8.0, "Draft", "", "",
     "Nutanix NDB Year 2 Renewal", "presales1", now, now))

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# APPROVAL ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def _highest_bid_level(bid_size, levels):
    result = 0
    for lvl in levels:
        if bid_size >= lvl["min_bid"]:
            result = lvl["level"]
    return result


def _lowest_margin_level(profit_margin, thresholds):
    for i, thr in enumerate(thresholds):
        if profit_margin >= thr:
            return i + 1
    return len(thresholds)


def determine_pcs_approval(lob, section, sub_section, bid_size, profit_margin):
    if lob == "DIS":
        bid_levels = DIS_BID_SIZE_LEVELS
        key = (section, sub_section)
        margin_thresholds = DIS_MARGIN_MATRIX.get(key)
        if margin_thresholds is None:
            return 7, DIS_BID_SIZE_LEVELS, "Unknown sub-section: defaults to CEO"
    elif lob == "Digital Solution":
        bid_levels = (DS_SERVICES_BID_SIZE_LEVELS
                      if sub_section == "Services" else DS_BID_SIZE_LEVELS)
        margin_thresholds = DS_MARGIN_MATRIX.get(sub_section)
        if margin_thresholds is None:
            return 7, DS_BID_SIZE_LEVELS, "Unknown sub-section: defaults to CEO"
    elif lob == "Managed Services":
        bid_levels = MS_BID_SIZE_LEVELS
        margin_thresholds = []
        for lvl in bid_levels:
            margin_thresholds.append(MS_MARGIN_LEVELS.get(lvl["level"], 100.0))
    elif lob == "Enterprise Systems":
        bid_levels = ES_BID_SIZE_LEVELS
        sub_key = "Services" if "Service" in (sub_section or "") else "Hardware"
        margin_thresholds = ES_MARGIN_MATRIX.get(sub_key)
        if margin_thresholds is None:
            return 6, ES_BID_SIZE_LEVELS, "Unknown sub-section"
        while len(margin_thresholds) < len(bid_levels):
            margin_thresholds.append(-100.0)
    else:
        return 1, [], "Unknown LOB"

    bid_level = _highest_bid_level(bid_size, bid_levels)
    margin_level = _lowest_margin_level(profit_margin, margin_thresholds)
    required = max(bid_level, margin_level)
    chain = [lvl for lvl in bid_levels if lvl["level"] <= required]
    detail = (f"Bid size requires Level {bid_level}, "
              f"Margin ({profit_margin}%) requires Level {margin_level} "
              f"=> Approval through Level {required}")
    return required, chain, detail


def determine_pcm_delegation(sub_lob, discount_pct):
    delegation = PCM_DELEGATION.get(sub_lob)
    if not delegation:
        return "CFO", [], "Unknown sub-LOB: defaults to CFO"
    for entry in delegation:
        if discount_pct <= entry["max_discount"]:
            idx = delegation.index(entry)
            chain = delegation[:idx + 1]
            detail = (f"Discount {discount_pct}% <= {entry['max_discount']}% "
                      f"=> {entry['role']} can approve")
            return entry["role"], chain, detail
    last = delegation[-1]
    return last["role"], delegation, f"Discount {discount_pct}% => {last['role']}"


def get_quality_review_type(bid_size):
    if bid_size < 10_000:
        return "PQAR Waived"
    elif bid_size < 200_000:
        return "PQAR Lite"
    else:
        return "PQAR Full"


def get_approval_levels(lob):
    if lob == "DIS":
        return DIS_BID_SIZE_LEVELS
    elif lob == "Digital Solution":
        return DS_BID_SIZE_LEVELS
    elif lob == "Managed Services":
        return MS_BID_SIZE_LEVELS
    elif lob == "Enterprise Systems":
        return ES_BID_SIZE_LEVELS
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# COST SHEET FORMULAS
# ═══════════════════════════════════════════════════════════════════════════════

def cs_recalc_line(line, local_charges_pct=6.45, exchange_rate=0.3125):
    qty = line.get("qty", 0)
    ulp = line.get("unit_list_price", 0)
    disc = line.get("discount_pct", 0)
    line["total_list"] = ulp * qty
    line["total_transfer"] = line["total_list"] * (1.0 - disc / 100.0)
    line["total_cif"] = line["total_transfer"] * (1.0 + local_charges_pct / 100.0)
    gbm_cost = line.get("gbm_cost", 0)
    if gbm_cost == 0:
        line["gbm_cost"] = line["total_cif"]
        gbm_cost = line["gbm_cost"]
    sell = line.get("requested_sell", 0)
    if sell > 0:
        line["gp_pct"] = ((sell - gbm_cost) / sell * 100.0) if sell else 0
    else:
        target = line.get("gp_pct", 0)
        if target > 0 and gbm_cost > 0:
            sell = gbm_cost / (1.0 - target / 100.0) if target < 100 else gbm_cost
            line["requested_sell"] = sell
        else:
            line["requested_sell"] = gbm_cost
            line["gp_pct"] = 0
    line["total_sell_usd"] = line["requested_sell"]
    line["total_local_currency"] = line["total_sell_usd"] * exchange_rate
    return line


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def current_user():
    if 'user_id' not in session:
        return None
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    return dict(user) if user else None


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Please enter username and password.', 'danger')
            return render_template('login.html')

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND active=1",
                          (username,)).fetchone()
        if not user or dict(user)['password'] != _hash_pw(password):
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = user['role']
        flash(f'Welcome, {user["full_name"]}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    db = get_db()
    stats = {
        'total_pcs': db.execute("SELECT COUNT(*) FROM pcs").fetchone()[0],
        'pcs_draft': db.execute("SELECT COUNT(*) FROM pcs WHERE status='Draft'").fetchone()[0],
        'pcs_review': db.execute("SELECT COUNT(*) FROM pcs WHERE status LIKE 'Under Review%' OR status='Submitted'").fetchone()[0],
        'pcs_approved': db.execute("SELECT COUNT(*) FROM pcs WHERE status='Approved'").fetchone()[0],
        'pcs_rejected': db.execute("SELECT COUNT(*) FROM pcs WHERE status='Rejected'").fetchone()[0],
        'total_pcm': db.execute("SELECT COUNT(*) FROM pcm").fetchone()[0],
        'pcm_approved': db.execute("SELECT COUNT(*) FROM pcm WHERE status='Approved'").fetchone()[0],
    }
    recent_pcs = db.execute("""SELECT id, project_number, customer_name, lob, bid_size,
        profit_margin, status, updated_at FROM pcs ORDER BY updated_at DESC LIMIT 20""").fetchall()
    return render_template('dashboard.html', stats=stats, recent_pcs=recent_pcs,
                         status_colors=STATUS_COLORS)


# ─── PCS Routes ──────────────────────────────────────────────────────────────

@app.route('/pcs')
@login_required
def pcs_list():
    db = get_db()
    lob_filter = request.args.get('lob', 'All')
    status_filter = request.args.get('status', 'All')

    query = "SELECT * FROM pcs WHERE 1=1"
    params = []
    if lob_filter != 'All':
        query += " AND lob = ?"
        params.append(lob_filter)
    if status_filter != 'All':
        if status_filter == 'Under Review':
            query += " AND (status LIKE 'Under Review%' OR status='Submitted')"
        else:
            query += " AND status = ?"
            params.append(status_filter)
    query += " ORDER BY updated_at DESC"

    pcs_records = db.execute(query, params).fetchall()
    lobs = list(PCS_LOB_OPTIONS.keys())
    return render_template('pcs_list.html', records=pcs_records, lobs=lobs,
                         lob_filter=lob_filter, status_filter=status_filter,
                         status_colors=STATUS_COLORS)


@app.route('/pcs/<int:pcs_id>')
@login_required
def pcs_detail(pcs_id):
    db = get_db()
    pcs = db.execute("SELECT * FROM pcs WHERE id = ?", (pcs_id,)).fetchone()
    if not pcs:
        flash('PCS not found.', 'danger')
        return redirect(url_for('pcs_list'))

    history = db.execute("SELECT * FROM pcs_history WHERE pcs_id = ? ORDER BY timestamp DESC",
                         (pcs_id,)).fetchall()
    lines = db.execute("SELECT * FROM cost_sheet_lines WHERE pcs_id = ? ORDER BY line_number",
                       (pcs_id,)).fetchall()

    levels = get_approval_levels(pcs['lob'])
    req_level = pcs['required_approval_level']
    curr_level = pcs['current_approver_level']

    chain = []
    for lvl in levels:
        if lvl['level'] > req_level:
            break
        status_mark = ''
        if lvl['level'] < curr_level:
            status_mark = 'approved'
        elif lvl['level'] == curr_level and pcs['status'] not in ('Approved', 'Rejected', 'Draft'):
            status_mark = 'pending'
        elif pcs['status'] == 'Approved':
            status_mark = 'approved'
        chain.append({**lvl, 'status_mark': status_mark})

    user = current_user()
    # Compute grand totals from lines
    gt = {'total_list': 0, 'total_transfer': 0, 'total_cif': 0,
          'gbm_cost': 0, 'total_sell_usd': 0, 'total_local_currency': 0}
    for ln in lines:
        for f in gt:
            gt[f] += ln[f] if ln[f] else 0
    gt['gross_profit'] = gt['total_sell_usd'] - gt['gbm_cost']
    gt['gp_pct'] = ((gt['total_sell_usd'] - gt['gbm_cost']) / gt['total_sell_usd'] * 100
                    if gt['total_sell_usd'] else 0)

    return render_template('pcs_detail.html', pcs=pcs, history=history,
                         lines=lines, chain=chain, user=user, gt=gt,
                         status_colors=STATUS_COLORS)


@app.route('/pcs/new', methods=['GET', 'POST'])
@login_required
def pcs_new():
    if request.method == 'POST':
        db = get_db()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = current_user()

        project_number = request.form.get('project_number', '').strip()
        customer_name = request.form.get('customer_name', '').strip()
        lob = request.form.get('lob', '')
        section = request.form.get('section', '')
        sub_section = request.form.get('sub_section', '')

        if not project_number or not customer_name or not lob:
            flash('Project number, customer name, and LOB are required.', 'danger')
            return render_template('pcs_form.html', pcs_types=PCS_TYPES,
                                 lob_options=PCS_LOB_OPTIONS,
                                 opp_statuses=OPPORTUNITY_STATUSES)

        db.execute("""INSERT INTO pcs (project_number, salesforce_number, customer_name,
            lob, sub_lob, section, sub_section, pcs_type, reference_pcs,
            bid_size, total_cost, selling_price, profit_margin,
            status, opportunity_status, comments, created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (project_number,
             request.form.get('salesforce_number', ''),
             customer_name, lob,
             request.form.get('sub_lob', ''),
             section, sub_section,
             request.form.get('pcs_type', 'New'),
             request.form.get('reference_pcs', ''),
             float(request.form.get('bid_size', 0) or 0),
             float(request.form.get('total_cost', 0) or 0),
             float(request.form.get('selling_price', 0) or 0),
             float(request.form.get('profit_margin', 0) or 0),
             'Draft',
             request.form.get('opportunity_status', 'Qualifying'),
             request.form.get('comments', ''),
             user['username'] if user else 'system',
             now, now))
        pcs_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        db.execute("""INSERT INTO pcs_history (pcs_id, action, action_by, level, comment, timestamp)
            VALUES (?, 'PCS Created', ?, 0, ?, ?)""",
            (pcs_id, user['full_name'] if user else 'System',
             request.form.get('comments', ''), now))
        db.commit()

        flash(f'PCS {project_number} created successfully!', 'success')
        return redirect(url_for('pcs_detail', pcs_id=pcs_id))

    return render_template('pcs_form.html', pcs_types=PCS_TYPES,
                         lob_options=PCS_LOB_OPTIONS,
                         opp_statuses=OPPORTUNITY_STATUSES)


@app.route('/pcs/<int:pcs_id>/submit', methods=['POST'])
@login_required
def pcs_submit(pcs_id):
    db = get_db()
    pcs = db.execute("SELECT * FROM pcs WHERE id = ?", (pcs_id,)).fetchone()
    if not pcs:
        flash('PCS not found.', 'danger')
        return redirect(url_for('pcs_list'))

    user = current_user()
    if user and user['role'] != 'Pre-Sales':
        flash('Only Pre-Sales users can submit PCS for approval.', 'danger')
        return redirect(url_for('pcs_detail', pcs_id=pcs_id))

    if pcs['status'] != 'Draft':
        flash('Only Draft PCS can be submitted.', 'warning')
        return redirect(url_for('pcs_detail', pcs_id=pcs_id))

    # Calculate required approval level
    req_level, _, _ = determine_pcs_approval(
        pcs['lob'], pcs['section'], pcs['sub_section'],
        pcs['bid_size'], pcs['profit_margin'])
    qa_type = get_quality_review_type(pcs['bid_size'])

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comment = request.form.get('comment', '')

    db.execute("""UPDATE pcs SET status='Submitted', current_approver_level=1,
        required_approval_level=?, quality_review_type=?, updated_at=? WHERE id=?""",
        (req_level, qa_type, now, pcs_id))
    db.execute("""INSERT INTO pcs_history (pcs_id, action, action_by, level, comment, timestamp)
        VALUES (?, 'Submitted for Approval', ?, 0, ?, ?)""",
        (pcs_id, user['full_name'] if user else 'System', comment, now))
    db.commit()

    flash(f'PCS {pcs["project_number"]} submitted for approval (Level 1 through {req_level}).', 'success')
    return redirect(url_for('pcs_detail', pcs_id=pcs_id))


@app.route('/pcs/<int:pcs_id>/approve', methods=['POST'])
@login_required
def pcs_approve(pcs_id):
    db = get_db()
    pcs = db.execute("SELECT * FROM pcs WHERE id = ?", (pcs_id,)).fetchone()
    if not pcs:
        flash('PCS not found.', 'danger')
        return redirect(url_for('pcs_list'))

    if pcs['status'] not in ('Submitted', 'Under Review'):
        flash(f'Cannot approve PCS in status: {pcs["status"]}', 'warning')
        return redirect(url_for('pcs_detail', pcs_id=pcs_id))

    user = current_user()
    curr_level = pcs['current_approver_level']
    req_level = pcs['required_approval_level']

    levels = get_approval_levels(pcs['lob'])
    role = "Approver"
    for lvl in levels:
        if lvl["level"] == curr_level:
            role = lvl["role"]
            break

    if user and user['role'] not in ('CEO', 'CFO Finance') and user['role'] != role:
        flash(f'This PCS requires approval from: {role} (Level {curr_level}). Your role: {user["role"]}', 'danger')
        return redirect(url_for('pcs_detail', pcs_id=pcs_id))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comment = request.form.get('comment', '')

    if curr_level >= req_level:
        db.execute("UPDATE pcs SET status='Approved', updated_at=? WHERE id=?", (now, pcs_id))
        db.execute("""INSERT INTO pcs_history (pcs_id, action, action_by, level, comment, timestamp)
            VALUES (?, 'Approved (Final)', ?, ?, ?, ?)""",
            (pcs_id, user['full_name'] if user else 'System', curr_level, comment, now))
        flash(f'PCS {pcs["project_number"]} FULLY APPROVED!', 'success')
    else:
        next_level = curr_level + 1
        db.execute("""UPDATE pcs SET status='Under Review', current_approver_level=?,
            updated_at=? WHERE id=?""", (next_level, now, pcs_id))
        db.execute("""INSERT INTO pcs_history (pcs_id, action, action_by, level, comment, timestamp)
            VALUES (?, 'Approved at Level', ?, ?, ?, ?)""",
            (pcs_id, user['full_name'] if user else 'System', curr_level, comment, now))
        next_role = "Next Approver"
        for lvl in levels:
            if lvl["level"] == next_level:
                next_role = lvl["role"]
                break
        flash(f'Approved at Level {curr_level}. Escalated to Level {next_level} ({next_role}).', 'info')

    db.commit()
    return redirect(url_for('pcs_detail', pcs_id=pcs_id))


@app.route('/pcs/<int:pcs_id>/reject', methods=['POST'])
@login_required
def pcs_reject(pcs_id):
    db = get_db()
    pcs = db.execute("SELECT * FROM pcs WHERE id = ?", (pcs_id,)).fetchone()
    if not pcs:
        flash('PCS not found.', 'danger')
        return redirect(url_for('pcs_list'))

    user = current_user()
    if user and user['role'] == 'Pre-Sales':
        flash('Pre-Sales users cannot reject PCS.', 'danger')
        return redirect(url_for('pcs_detail', pcs_id=pcs_id))

    comment = request.form.get('comment', '').strip()
    if not comment:
        flash('Please provide a reason for rejection.', 'warning')
        return redirect(url_for('pcs_detail', pcs_id=pcs_id))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute("UPDATE pcs SET status='Rejected', current_approver_level=0, updated_at=? WHERE id=?",
               (now, pcs_id))
    db.execute("""INSERT INTO pcs_history (pcs_id, action, action_by, level, comment, timestamp)
        VALUES (?, 'Rejected', ?, ?, ?, ?)""",
        (pcs_id, user['full_name'] if user else 'System',
         pcs['current_approver_level'], comment, now))
    db.commit()
    flash(f'PCS {pcs["project_number"]} REJECTED.', 'danger')
    return redirect(url_for('pcs_detail', pcs_id=pcs_id))


@app.route('/pcs/<int:pcs_id>/delete', methods=['POST'])
@login_required
def pcs_delete(pcs_id):
    db = get_db()
    pcs = db.execute("SELECT * FROM pcs WHERE id = ?", (pcs_id,)).fetchone()
    if not pcs or pcs['status'] not in ('Draft', 'Rejected'):
        flash('Only Draft or Rejected PCS can be deleted.', 'warning')
        return redirect(url_for('pcs_list'))

    db.execute("DELETE FROM cost_sheet_lines WHERE pcs_id = ?", (pcs_id,))
    db.execute("DELETE FROM cost_sheet_config WHERE pcs_id = ?", (pcs_id,))
    db.execute("DELETE FROM pcs_history WHERE pcs_id = ?", (pcs_id,))
    db.execute("DELETE FROM pcs WHERE id = ?", (pcs_id,))
    db.commit()
    flash(f'PCS {pcs["project_number"]} deleted.', 'info')
    return redirect(url_for('pcs_list'))


# ─── PCM Routes ──────────────────────────────────────────────────────────────

@app.route('/pcm')
@login_required
def pcm_list():
    db = get_db()
    records = db.execute("SELECT * FROM pcm ORDER BY updated_at DESC").fetchall()
    return render_template('pcm_list.html', records=records, status_colors=STATUS_COLORS,
                         pcm_categories=PCM_CATEGORIES)


@app.route('/pcm/new', methods=['GET', 'POST'])
@login_required
def pcm_new():
    if request.method == 'POST':
        db = get_db()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = current_user()

        contract_number = request.form.get('contract_number', '').strip()
        customer_name = request.form.get('customer_name', '').strip()
        if not contract_number or not customer_name:
            flash('Contract number and customer name are required.', 'danger')
            return render_template('pcm_form.html', pcm_categories=PCM_CATEGORIES)

        list_price = float(request.form.get('list_price', 0) or 0)
        selling_price = float(request.form.get('selling_price', 0) or 0)
        discount_pct = ((list_price - selling_price) / list_price * 100) if list_price else 0

        sub_lob = request.form.get('sub_lob', '')
        req_approver, _, _ = determine_pcm_delegation(sub_lob, discount_pct)

        db.execute("""INSERT INTO pcm (contract_number, customer_name, pcm_category, sub_lob,
            contract_type, list_price, selling_price, discount_pct, status,
            required_approver, comments, created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (contract_number, customer_name,
             request.form.get('pcm_category', 'TSS'),
             sub_lob,
             request.form.get('contract_type', 'Renewal'),
             list_price, selling_price, round(discount_pct, 2),
             'Draft', req_approver,
             request.form.get('comments', ''),
             user['username'] if user else 'system', now, now))
        pcm_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("""INSERT INTO pcm_history (pcm_id, action, action_by, comment, timestamp)
            VALUES (?, 'PCM Created', ?, ?, ?)""",
            (pcm_id, user['full_name'] if user else 'System', '', now))
        db.commit()

        flash(f'PCM {contract_number} created. Required approver: {req_approver}', 'success')
        return redirect(url_for('pcm_list'))

    return render_template('pcm_form.html', pcm_categories=PCM_CATEGORIES)


@app.route('/pcm/<int:pcm_id>')
@login_required
def pcm_detail(pcm_id):
    db = get_db()
    pcm = db.execute("SELECT * FROM pcm WHERE id = ?", (pcm_id,)).fetchone()
    if not pcm:
        flash('PCM not found.', 'danger')
        return redirect(url_for('pcm_list'))
    history = db.execute("SELECT * FROM pcm_history WHERE pcm_id = ? ORDER BY timestamp DESC",
                         (pcm_id,)).fetchall()
    user = current_user()
    return render_template('pcm_detail.html', pcm=pcm, history=history,
                         user=user, status_colors=STATUS_COLORS)


@app.route('/pcm/<int:pcm_id>/submit', methods=['POST'])
@login_required
def pcm_submit(pcm_id):
    db = get_db()
    pcm = db.execute("SELECT * FROM pcm WHERE id = ?", (pcm_id,)).fetchone()
    if not pcm or pcm['status'] != 'Draft':
        flash('Only Draft PCM can be submitted.', 'warning')
        return redirect(url_for('pcm_list'))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = current_user()
    req_approver, _, detail = determine_pcm_delegation(pcm['sub_lob'], pcm['discount_pct'])

    db.execute("UPDATE pcm SET status='Submitted', current_approver=?, required_approver=?, updated_at=? WHERE id=?",
               (req_approver, req_approver, now, pcm_id))
    db.execute("""INSERT INTO pcm_history (pcm_id, action, action_by, comment, timestamp)
        VALUES (?, 'Submitted for Approval', ?, ?, ?)""",
        (pcm_id, user['full_name'] if user else 'System', detail, now))
    db.commit()
    flash(f'PCM submitted. Required: {req_approver}', 'success')
    return redirect(url_for('pcm_detail', pcm_id=pcm_id))


@app.route('/pcm/<int:pcm_id>/approve', methods=['POST'])
@login_required
def pcm_approve(pcm_id):
    db = get_db()
    pcm = db.execute("SELECT * FROM pcm WHERE id = ?", (pcm_id,)).fetchone()
    if not pcm or pcm['status'] not in ('Submitted',):
        flash('Cannot approve this PCM.', 'warning')
        return redirect(url_for('pcm_list'))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = current_user()
    comment = request.form.get('comment', '')

    db.execute("UPDATE pcm SET status='Approved', updated_at=? WHERE id=?", (now, pcm_id))
    db.execute("""INSERT INTO pcm_history (pcm_id, action, action_by, comment, timestamp)
        VALUES (?, 'Approved', ?, ?, ?)""",
        (pcm_id, user['full_name'] if user else 'System', comment, now))
    db.commit()
    flash('PCM Approved!', 'success')
    return redirect(url_for('pcm_detail', pcm_id=pcm_id))


@app.route('/pcm/<int:pcm_id>/reject', methods=['POST'])
@login_required
def pcm_reject(pcm_id):
    db = get_db()
    pcm = db.execute("SELECT * FROM pcm WHERE id = ?", (pcm_id,)).fetchone()
    if not pcm or pcm['status'] not in ('Submitted',):
        flash('Cannot reject this PCM.', 'warning')
        return redirect(url_for('pcm_list'))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = current_user()
    comment = request.form.get('comment', '')

    db.execute("UPDATE pcm SET status='Rejected', updated_at=? WHERE id=?", (now, pcm_id))
    db.execute("""INSERT INTO pcm_history (pcm_id, action, action_by, comment, timestamp)
        VALUES (?, 'Rejected', ?, ?, ?)""",
        (pcm_id, user['full_name'] if user else 'System', comment, now))
    db.commit()
    flash('PCM Rejected.', 'danger')
    return redirect(url_for('pcm_detail', pcm_id=pcm_id))


# ─── Approval Matrix Reference ──────────────────────────────────────────────

@app.route('/matrix')
@login_required
def approval_matrix():
    return render_template('matrix.html',
                         dis_levels=DIS_BID_SIZE_LEVELS,
                         ds_levels=DS_BID_SIZE_LEVELS,
                         ms_levels=MS_BID_SIZE_LEVELS,
                         es_levels=ES_BID_SIZE_LEVELS,
                         pcm_delegation=PCM_DELEGATION)


# ─── Cost Sheet Lines API ───────────────────────────────────────────────────

@app.route('/api/pcs/<int:pcs_id>/lines', methods=['GET'])
@login_required
def api_get_lines(pcs_id):
    db = get_db()
    lines = db.execute("SELECT * FROM cost_sheet_lines WHERE pcs_id = ? ORDER BY line_number",
                       (pcs_id,)).fetchall()
    return jsonify([dict(l) for l in lines])


@app.route('/api/pcs/<int:pcs_id>/lines', methods=['POST'])
@login_required
def api_add_line(pcs_id):
    db = get_db()
    data = request.json
    line = cs_recalc_line(data)

    db.execute("""INSERT INTO cost_sheet_lines
        (pcs_id, line_number, section, subsection, subsection_code,
         supplier, supplier_number, part_number, description,
         uom, qty, unit_list_price, discount_pct,
         total_list, total_transfer, total_cif, gbm_cost,
         gp_pct, requested_sell, local_charges_loading,
         total_sell_usd, total_local_currency, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (pcs_id, line.get('line_number', 0),
         line.get('section', ''), line.get('subsection', ''),
         line.get('subsection_code', ''),
         line.get('supplier', ''), line.get('supplier_number', ''),
         line.get('part_number', ''), line.get('description', ''),
         line.get('uom', 'EA'), line.get('qty', 0),
         line.get('unit_list_price', 0), line.get('discount_pct', 0),
         line.get('total_list', 0), line.get('total_transfer', 0),
         line.get('total_cif', 0), line.get('gbm_cost', 0),
         line.get('gp_pct', 0), line.get('requested_sell', 0),
         line.get('local_charges_loading', 0),
         line.get('total_sell_usd', 0), line.get('total_local_currency', 0),
         line.get('notes', '')))
    db.commit()
    return jsonify({'status': 'ok', 'id': db.execute("SELECT last_insert_rowid()").fetchone()[0]})


@app.route('/api/lines/<int:line_id>', methods=['DELETE'])
@login_required
def api_delete_line(line_id):
    db = get_db()
    db.execute("DELETE FROM cost_sheet_lines WHERE id = ?", (line_id,))
    db.commit()
    return jsonify({'status': 'ok'})


@app.route('/api/pcs/<int:pcs_id>/sync', methods=['POST'])
@login_required
def api_sync_pcs(pcs_id):
    """Recalculate PCS totals from cost sheet lines."""
    db = get_db()
    lines = db.execute("SELECT * FROM cost_sheet_lines WHERE pcs_id = ?", (pcs_id,)).fetchall()
    gt = {'total_sell_usd': 0, 'gbm_cost': 0}
    for ln in lines:
        gt['total_sell_usd'] += ln['total_sell_usd'] or 0
        gt['gbm_cost'] += ln['gbm_cost'] or 0
    gp_pct = ((gt['total_sell_usd'] - gt['gbm_cost']) / gt['total_sell_usd'] * 100
              if gt['total_sell_usd'] else 0)

    pcs = db.execute("SELECT * FROM pcs WHERE id = ?", (pcs_id,)).fetchone()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    req_level = 0
    if pcs:
        req_level, _, _ = determine_pcs_approval(
            pcs['lob'], pcs['section'], pcs['sub_section'],
            gt['total_sell_usd'], gp_pct)
        qa_type = get_quality_review_type(gt['total_sell_usd'])
        db.execute("""UPDATE pcs SET bid_size=?, total_cost=?, selling_price=?,
            profit_margin=?, required_approval_level=?, quality_review_type=?,
            updated_at=? WHERE id=?""",
            (gt['total_sell_usd'], gt['gbm_cost'], gt['total_sell_usd'],
             round(gp_pct, 2), req_level, qa_type, now, pcs_id))
    db.commit()
    return jsonify({'status': 'ok', 'bid_size': gt['total_sell_usd'],
                    'total_cost': gt['gbm_cost'], 'gp_pct': round(gp_pct, 2),
                    'required_level': req_level})


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT PROCESSORS
# ═══════════════════════════════════════════════════════════════════════════════

@app.context_processor
def inject_user():
    return {'current_user': current_user()}


@app.template_filter('currency')
def currency_filter(value):
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


@app.template_filter('pct')
def pct_filter(value):
    try:
        return f"{float(value):.2f}%"
    except (ValueError, TypeError):
        return "0.00%"


# ═══════════════════════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

with app.app_context():
    init_db()
    seed_users()
    seed_sample_pcs()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
