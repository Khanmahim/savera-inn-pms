import streamlit as st
import pandas as pd
import hashlib
from datetime import date, datetime, timedelta

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Savera Inn Resort PMS",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

USERS = {
    "admin": {
        "password_hash": hashlib.sha256("savera@2025".encode()).hexdigest(),
        "role": "admin",
        "name": "Admin",
    },
    "frontdesk": {
        "password_hash": hashlib.sha256("desk@123".encode()).hexdigest(),
        "role": "staff",
        "name": "Front Desk",
    },
    "manager": {
        "password_hash": hashlib.sha256("manager@123".encode()).hexdigest(),
        "role": "manager",
        "name": "Manager",
    },
}

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    user = USERS.get(username.lower().strip())
    if user and user["password_hash"] == hash_pw(password):
        return user
    return None

def show_login():
    st.markdown("""
<style>
    .stApp { background: #ffffff !important; }
    [data-testid="stAppViewContainer"] { background: #ffffff !important; }
    [data-testid="stHeader"] { background: #ffffff !important; }
    body, p, label, h1, h2, h3, span, div { color: #3b1f6e !important; }
    .stTextInput input {
        background: #ffffff !important;
        color: #1a1a1a !important;
        border: 1.5px solid #d8b4fe !important;
        border-radius: 8px !important;
    }
    .stTextInput label { color: #3b1f6e !important; font-weight: 600 !important; }
    .stFormSubmitButton button {
        background: #3b1f6e !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    .stFormSubmitButton button:hover { background: #5b21b6 !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
    [data-testid="stToolbar"] { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
</style>
""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align:center; margin-bottom:1.5rem;'>
                <div style='font-size:52px'>🏔️</div>
                <h1 style='color:#3b1f6e; font-size:26px; margin:8px 0 4px;'>Savera Inn Resort</h1>
                <p style='color:#7c5cbf; font-size:14px; margin:0;'>Property Management System</p>
            </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown("""
            <div style='background:white; border:1.5px solid #d8b4fe; border-radius:16px;
                        padding:2rem; box-shadow:0 4px 24px rgba(124,58,237,0.10);'>
            """, unsafe_allow_html=True)

            with st.form("login_form"):
                st.markdown("### 🔑 Sign In")
                username = st.text_input("Username", placeholder="e.g. admin")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Login →", use_container_width=True)
                if submitted:
                    user = check_login(username, password)
                    if user:
                        st.session_state.logged_in  = True
                        st.session_state.username   = username.lower().strip()
                        st.session_state.user_name  = user["name"]
                        st.session_state.user_role  = user["role"]
                        st.rerun()
                    else:
                        st.error("❌ Incorrect username or password.")

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div style='text-align:center; margin-top:1.2rem; font-size:12px; color:#999; line-height:2'>
            Contact your administrator for login credentials.
        </div>
        """, unsafe_allow_html=True)

# ── Gate: stop here if not logged in ─────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    show_login()
    st.stop()

# ── Database setup ───────────────────────────────────────────────────────────
import db as DB

# Create tables if they don't exist
try:
    DB.setup_tables()
except Exception as e:
    st.error(f"❌ Database error: {e}")
    st.stop()

# ── Role-based permissions ────────────────────────────────────────────────────
# Defines what each role CAN do. Admin can do everything always.
PERMISSIONS = {
    # Front Desk: view + bookings + billing + payments + CRM only
    # Cannot delete anything, cannot manage rooms, cannot see financials
    "staff": {
        "pages":           ["📊 Dashboard", "📋 Bookings", "📅 Calendar",
                            "🛏️ Rooms", "₹  Billing", "💳 Payments", "👥 Guests (CRM)"],
        "add_booking":     True,
        "edit_booking":    True,
        "delete_booking":  False,   # 🔒 dangerous
        "checkout_guest":  True,
        "add_room":        False,   # 🔒 admin/manager only
        "edit_room":       False,   # 🔒 admin/manager only
        "delete_room":     False,   # 🔒 admin only
        "view_billing":    True,
        "generate_bill":   True,
        "mark_paid":       False,   # 🔒 manager/admin only
        "view_expenses":   False,   # 🔒 hidden from front desk
        "add_expense":     False,   # 🔒 hidden from front desk
        "view_reports":    False,   # 🔒 hidden from front desk
        "view_payments":   True,
        "add_payment":     True,
        "add_refund":      False,   # 🔒 manager/admin only
        "view_crm":        True,
        "add_crm_note":    True,
        "import_excel":    True,
    },
    # Manager: everything except delete rooms (only admin can permanently delete)
    "manager": {
        "pages":           ["📊 Dashboard", "📋 Bookings", "📅 Calendar", "🛏️ Rooms",
                            "₹  Billing", "💳 Payments", "🧾 Expenses", "📈 Reports", "👥 Guests (CRM)"],
        "add_booking":     True,
        "edit_booking":    True,
        "delete_booking":  True,
        "checkout_guest":  True,
        "add_room":        True,
        "edit_room":       True,
        "delete_room":     False,   # 🔒 admin only — permanent action
        "view_billing":    True,
        "generate_bill":   True,
        "mark_paid":       True,
        "view_expenses":   True,
        "add_expense":     True,
        "view_reports":    True,
        "view_payments":   True,
        "add_payment":     True,
        "add_refund":      True,
        "view_crm":        True,
        "add_crm_note":    True,
        "import_excel":    True,
    },
    "admin": {},  # Admin bypasses all checks — full access
}

def can(action):
    """Check if current user has permission for an action. Admin always returns True."""
    role = st.session_state.get("user_role", "staff")
    if role == "admin":
        return True
    return PERMISSIONS.get(role, {}).get(action, False)

def allowed_pages():
    """Return list of pages the current user can see in the sidebar."""
    role = st.session_state.get("user_role", "staff")
    base = ["📊 Dashboard","🛏️ Rooms","📋 Bookings","📅 Calendar",
            "₹  Billing","💳 Payments","🧾 Expenses","📈 Reports",
            "👥 Guests (CRM)","🔔 Notifications"]
    if role == "admin":
        return base
    pages = PERMISSIONS.get(role, {}).get("pages", ["📊 Dashboard"])
    return pages + ["🔔 Notifications"]

def lock(action, message=None):
    """Show a lock message if user doesn't have permission. Returns True if blocked."""
    if not can(action):
        role = st.session_state.get("user_role", "staff")
        msg  = message or f"🔒 **Access Restricted** — This action requires higher permissions. Please ask the **Admin** or **Manager**."
        st.markdown(f"""
        <div style='background:#fef3c7;border:1.5px solid #f59e0b;border-radius:10px;
                    padding:14px 18px;display:flex;align-items:center;gap:12px;margin:8px 0'>
            <div style='font-size:28px'>🔒</div>
            <div>
                <div style='font-weight:600;color:#92400e;font-size:14px'>Access Restricted</div>
                <div style='color:#78350f;font-size:13px;margin-top:2px'>
                    Your role (<b>{role.title()}</b>) does not have permission for this action.<br>
                    Please ask the <b>Admin</b> or <b>Manager</b> to do this.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return True
    return False

# ── Load all data from PostgreSQL ────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_all_cached():
    """Cached DB fetch — only hits Supabase every 30 seconds, not on every click."""
    return {
        "rooms":    DB.get_rooms(),
        "bookings": DB.get_bookings(),
        "bills":    DB.get_bills(),
        "expenses": DB.get_expenses(),
        "payments": DB.get_payments(),
    }

def load_all():
    """Load data into session state from cache."""
    data = load_all_cached()
    st.session_state.rooms    = data["rooms"]
    st.session_state.bookings = data["bookings"]
    st.session_state.bills    = data["bills"]
    st.session_state.expenses = data["expenses"]
    st.session_state.payments = data["payments"]
    # Cache unread count alongside data — no extra DB hit per render
    if DB.MODE == "online":
        try:
            st.session_state.unread_count = DB.get_unread_count()
        except Exception:
            st.session_state.unread_count = 0

def invalidate_cache():
    """Clear cache and reload — called after writes."""
    load_all_cached.clear()
    load_all()
    if DB.MODE == "online":
        try:
            st.session_state.unread_count = DB.get_unread_count()
        except Exception:
            pass

def persist():
    pass  # Data is written directly to DB — kept for compatibility

# ── Load data on first render ─────────────────────────────────────────────────
if "data_loaded" not in st.session_state:
    load_all()
    st.session_state.data_loaded = True

def nights(cin, cout):
    d1 = datetime.strptime(str(cin), "%Y-%m-%d")
    d2 = datetime.strptime(str(cout), "%Y-%m-%d")
    return max(1, (d2 - d1).days)

def get_room(num):
    return next((r for r in st.session_state.rooms if r["num"] == num), None)

def fmt(n):
    return f"₹{int(n):,}"

# ── Availability engine ───────────────────────────────────────────────────────
def dates_overlap(cin1, cout1, cin2, cout2):
    """Check if two date ranges overlap. checkout is exclusive (day of departure)."""
    return cin1 < cout2 and cin2 < cout1

def get_room_status_on_date(room_num, check_date):
    """SQL-powered room status check — O(log n) via index."""
    return DB.get_room_status_on_date_sql(room_num, check_date)

def check_overbooking(room_num, checkin_str, checkout_str, exclude_booking_id=None):
    """SQL-powered overbooking check — O(log n) via index."""
    return DB.check_overbooking_sql(room_num, checkin_str, checkout_str, exclude_booking_id)

def sync_room_statuses():
    """SQL-powered room sync — one query per room."""
    DB.sync_room_statuses_sql()
    # Refresh cache so UI reflects updated statuses
    invalidate_cache()

# ── Sync room statuses once per day only (not every click) ──────────────────
if "last_sync_day" not in st.session_state or \
   st.session_state.last_sync_day != str(date.today()):
    if DB.MODE == "online":
        DB.sync_room_statuses_sql()
        invalidate_cache()
    st.session_state.last_sync_day = str(date.today())

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #3b1f6e !important; }
    [data-testid="stSidebar"] * { color: #e8d9ff !important; }
    [data-testid="stSidebar"] .stRadio label { color: #e8d9ff !important; }
    [data-testid="stSidebar"] hr { border-color: #5a3a9a !important; }
    .stApp { background-color: #ffffff !important; }
    [data-testid="stAppViewContainer"] { background-color: #ffffff !important; }
    div[data-testid="metric-container"] {
        background: #f3eeff;
        border-radius: 10px;
        padding: 12px 18px;
        border-left: 4px solid #7c3aed;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #f3eeff;
        border-radius: 8px 8px 0 0;
        color: #5b21b6;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: #7c3aed !important;
        color: white !important;
    }
    .stButton > button {
        background: #7c3aed;
        color: white;
        border: none;
        border-radius: 8px;
    }
    .stButton > button:hover { background: #5b21b6; }
    .stForm { border: 1px solid #d8b4fe; border-radius: 10px; padding: 16px; }
    .badge { padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-green  { background:#d4edda; color:#155724; }
    .badge-red    { background:#f8d7da; color:#721c24; }
    .badge-orange { background:#fff3cd; color:#856404; }
    .badge-blue   { background:#ede9fe; color:#5b21b6; }
    .room-box { border-radius:8px; padding:10px; text-align:center; margin:4px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏔️ Savera Inn Resort")
    st.markdown("**Property Manager**")
    # ── Online / Offline indicator ────────────────────────────────────────────
    if DB.MODE == "online":
        st.markdown("🟢 **Online** — Cloud database active")
    else:
        st.markdown("🔴 **OFFLINE MODE**")
        st.markdown("⚠️ No internet connection")
    st.markdown("---")
    role_badge = {"admin": "🔴 Admin", "manager": "🟡 Manager", "staff": "🟢 Staff"}.get(st.session_state.user_role, "👤")
    st.markdown(f"**{st.session_state.user_name}** &nbsp; {role_badge}")
    st.markdown("---")
    page = st.radio("Navigate", allowed_pages(), label_visibility="collapsed")
    st.markdown("---")

    # ── Notification bell with unread count (cached, not live DB hit) ───────────
    if DB.MODE == "online":
        unread = st.session_state.get("unread_count", 0)
        if unread > 0:
            st.markdown(f"""
            <div style='background:#dc2626;color:white;border-radius:8px;
                        padding:6px 12px;text-align:center;font-weight:600;font-size:13px;
                        margin-bottom:8px'>
                🔔 {unread} unread notification{'s' if unread>1 else ''}
            </div>""", unsafe_allow_html=True)

    # ── Auto-refresh every 60 seconds ────────────────────────────────────────
    import time
    now = time.time()
    last_refresh = st.session_state.get("last_refresh", 0)
    if now - last_refresh > 120:
        invalidate_cache()
        st.session_state.last_refresh = now

    # ── Manual refresh button ─────────────────────────────────────────────────
    if st.button("🔄 Refresh Data", use_container_width=True):
        invalidate_cache()
        st.session_state.last_refresh = time.time()
        st.success("✅ Data refreshed!")

    # ── Last refreshed time ───────────────────────────────────────────────────
    last_dt = datetime.fromtimestamp(st.session_state.get("last_refresh", now))
    st.caption(f"🕐 Updated: {last_dt.strftime('%H:%M:%S')}")
    st.caption(f"📅 {date.today().strftime('%d %b %Y, %A')}")

    if st.button("🚪 Logout", use_container_width=True):
        for key in ["logged_in", "username", "user_name", "user_role"]:
            st.session_state.pop(key, None)
        st.rerun()

# ── Smart alerts generated once per day in background ────────────────────────
if DB.MODE == "online":
    if st.session_state.get("last_alert_day") != str(date.today()):
        st.session_state.last_alert_day = str(date.today())
        try:
            DB.generate_smart_alerts()
        except Exception:
            pass

# ── Offline warning banner ────────────────────────────────────────────────────
if DB.MODE == "offline":
    st.markdown("""
    <div style='background:#dc2626;color:white;padding:16px 20px;border-radius:10px;
                margin-bottom:16px;text-align:center;font-size:16px;font-weight:600'>
        🔴 NO INTERNET CONNECTION — READ ONLY MODE<br>
        <span style='font-size:13px;font-weight:400'>
        You can VIEW data but cannot add or edit anything.<br>
        Please connect to internet before making any bookings or changes.
        </span>
    </div>
    """, unsafe_allow_html=True)

def require_online():
    """Call this before any write operation. Stops action if offline."""
    if DB.MODE == "offline":
        st.error("🔴 Cannot save — No internet connection. Please connect to internet first.")
        st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("📊 Dashboard")

    rooms    = st.session_state.rooms
    bookings = st.session_state.bookings
    bills    = st.session_state.bills

    occ     = sum(1 for r in rooms if r["status"] == "occupied")
    avail   = sum(1 for r in rooms if r["status"] == "available")
    clean   = sum(1 for r in rooms if r["status"] == "cleaning")
    rev     = sum(b["room_charge"] + b.get("food", 0) + b.get("laundry", 0) +
                  b.get("extra_bed", 0) + b.get("electricity", 0) +
                  b.get("bonfire", 0) + b.get("other", 0) for b in bills)
    pending = sum(1 for b in bookings if b["status"] == "checked-in")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔴 Occupied",          occ)
    c2.metric("🟢 Available",         avail)
    c3.metric("🟡 Cleaning",          clean)
    c4.metric("₹  Total Revenue",     fmt(rev))
    c5.metric("⏳ Pending Checkouts", pending)

    st.markdown("---")

    # ── Date picker (full width) ──────────────────────────────────────────────
    dp1, dp2 = st.columns([2,4])
    selected_date = dp1.date_input(
        "📅 View any date",
        value=date.today(),
        help="Pick any date to see full room status, check-ins and check-outs"
    )
    today_date  = date.today()
    is_today    = (selected_date == today_date)
    sel_str     = str(selected_date)

    # ── Helper: find booking details for a room on a date ────────────────────
    def room_status_on_date(room_num, check_date):
        check_str = str(check_date)
        for b in bookings:
            if b.get("status") == "checked-out":
                continue
            rooms_list = b.get("rooms", [b.get("room", "")])
            if not isinstance(rooms_list, list):
                rooms_list = [rooms_list]
            if room_num not in rooms_list:
                continue
            try:
                cin  = datetime.strptime(b["checkin"],  "%Y-%m-%d").date()
                cout = datetime.strptime(b["checkout"], "%Y-%m-%d").date()
                if cin <= check_date < cout:
                    return "occupied", b
            except:
                pass
        return None, None

    # ── Pre-compute for selected date ─────────────────────────────────────────
    checkins_sel  = [b for b in bookings
                     if b.get("checkin")  == sel_str
                     and b.get("status") not in ("checked-out",)]
    checkouts_sel = [b for b in bookings
                     if b.get("checkout") == sel_str
                     and b.get("status") in ("checked-in","confirmed")]
    overdue       = [b for b in bookings
                     if b.get("checkout","") < str(today_date)
                     and b.get("status") == "checked-in"]

    # ── Smart banner ──────────────────────────────────────────────────────────
    if is_today:
        parts = []
        if checkins_sel:  parts.append(f"🛎️ <b>{len(checkins_sel)} Check-in{'s' if len(checkins_sel)>1 else ''}</b>")
        if checkouts_sel: parts.append(f"🚪 <b>{len(checkouts_sel)} Check-out{'s' if len(checkouts_sel)>1 else ''}</b>")
        if overdue:       parts.append(f"⚠️ <b>{len(overdue)} Overdue</b>")
        if parts:
            st.markdown(
                f"<div style='background:#fef3c7;border:1.5px solid #f59e0b;border-radius:10px;"
                f"padding:10px 16px;font-size:14px;margin-bottom:12px'>"
                f"{'  &nbsp;|&nbsp;  '.join(parts)} &nbsp; — action required today"
                f"</div>", unsafe_allow_html=True)
    else:
        label = selected_date.strftime('%d %B %Y')
        st.markdown(
            f"<div style='background:#e0f2fe;border-left:4px solid #0284c7;"
            f"padding:8px 14px;border-radius:6px;font-size:13px;margin-bottom:12px'>"
            f"📅 Showing status for <b>{label}</b></div>",
            unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    # ── COL 1: Room grid ──────────────────────────────────────────────────────
    with col1:
        st.subheader("🛏️ Room Status")
        cols = st.columns(3)
        for i, r in enumerate(rooms):
            bk_status, bk = room_status_on_date(r["num"], selected_date)

            # Determine special labels for selected date
            is_checkin_day  = bk and bk.get("checkin")  == sel_str
            is_checkout_day = bk and bk.get("checkout") == sel_str

            if is_today:
                status = r["status"]
            else:
                status = bk_status if bk_status else "available"

            guest = bk.get("guest","") if bk else ""

            # Color and icon — override for check-in/checkout days
            if is_checkin_day and sel_str == bk.get("checkin"):
                color, icon, label = "#d1fae5", "🛎️", "Check-in"
            elif is_checkout_day and sel_str == bk.get("checkout"):
                color, icon, label = "#fee2e2", "🚪", "Check-out"
            elif status == "occupied":
                color, icon, label = "#f8d7da", "🔴", "Occupied"
            elif status == "cleaning":
                color, icon, label = "#fff3cd", "🟡", "Cleaning"
            else:
                color, icon, label = "#d4edda", "🟢", "Available"

            guest_line = (
                f"<div style='font-size:10px;color:#555;margin-top:2px;"
                f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{guest}</div>"
                if guest else ""
            )
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:{color};border-radius:8px;padding:10px;
                            text-align:center;margin-bottom:8px;
                            border:1px solid rgba(0,0,0,0.07)">
                  <div style="font-size:18px;font-weight:700">{r['num']}</div>
                  <div style="font-size:10px;color:#666">{r['type']} · {r['ac']}</div>
                  <div style="font-size:11px;margin-top:3px">{icon} {label}</div>
                  {guest_line}
                </div>""", unsafe_allow_html=True)

        # Summary bar
        occ_d   = sum(1 for r in rooms if room_status_on_date(r["num"], selected_date)[0] == "occupied")
        cin_d   = len(checkins_sel)
        cout_d  = len(checkouts_sel)
        avail_d = len(rooms) - occ_d
        st.markdown(
            f"<div style='background:#f3eeff;border-radius:8px;padding:10px 14px;"
            f"margin-top:4px;font-size:12px;display:flex;gap:12px;flex-wrap:wrap'>"
            f"🔴 <b>{occ_d} Occupied</b> &nbsp;"
            f"🟢 <b>{avail_d} Available</b> &nbsp;"
            f"🛎️ <b>{cin_d} Check-ins</b> &nbsp;"
            f"🚪 <b>{cout_d} Check-outs</b>"
            f"</div>", unsafe_allow_html=True)

    # ── COL 2: Today's activity list ──────────────────────────────────────────
    with col2:
        st.subheader("📋 Activity")

        # ── Check-ins ─────────────────────────────────────────────────────────
        if checkins_sel:
            st.markdown(f"**🛎️ Check-ins ({len(checkins_sel)})**")
            for b in checkins_sel:
                rms = b.get("room","?")
                st.markdown(f"""
                <div style='background:#d1fae5;border-radius:8px;padding:8px 12px;
                            margin-bottom:5px;border-left:4px solid #059669'>
                    <b>Room {rms}</b> — {b['guest']}<br>
                    <span style='font-size:11px;color:#065f46'>
                        📞 {b.get('phone','—')} &nbsp;|&nbsp;
                        {b.get('agent','Direct') or 'Direct'}
                    </span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("**🛎️ Check-ins**")
            st.caption("None today")

        st.markdown("")

        # ── Check-outs ────────────────────────────────────────────────────────
        if checkouts_sel:
            st.markdown(f"**🚪 Check-outs ({len(checkouts_sel)})**")
            for b in checkouts_sel:
                rms = b.get("room","?")
                # Check if payment is pending
                paid = sum(p.get("amount",0) for p in st.session_state.payments
                           if p.get("booking_id") == b.get("id")
                           and p.get("type") != "refund")
                has_bill = any(bl.get("booking_id") == b.get("id")
                               for bl in st.session_state.bills)
                pay_tag = ""
                if not has_bill:
                    pay_tag = "<span style='color:#dc2626;font-size:10px'>⚠️ No bill yet</span>"
                st.markdown(f"""
                <div style='background:#fee2e2;border-radius:8px;padding:8px 12px;
                            margin-bottom:5px;border-left:4px solid #dc2626'>
                    <b>Room {rms}</b> — {b['guest']}<br>
                    <span style='font-size:11px;color:#991b1b'>
                        📅 Checked in: {b.get('checkin','?')} &nbsp; {pay_tag}
                    </span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("**🚪 Check-outs**")
            st.caption("None today" if is_today else "None this day")

        st.markdown("")

        # ── Overdue (only show on today view) ─────────────────────────────────
        if is_today and overdue:
            st.markdown(f"**⚠️ Overdue Checkouts ({len(overdue)})**")
            for b in overdue:
                rms = b.get("room","?")
                st.markdown(f"""
                <div style='background:#fef3c7;border-radius:8px;padding:8px 12px;
                            margin-bottom:5px;border-left:4px solid #f59e0b'>
                    <b>Room {rms}</b> — {b['guest']}<br>
                    <span style='font-size:11px;color:#92400e'>
                        Was due: {b.get('checkout','?')}
                    </span>
                </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ROOMS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🛏️ Rooms":
    st.title("🛏️ Room Management")

    room_tabs = ["All Rooms", "➕ Add Room"] if can("add_room") else ["All Rooms"]
    tab_results = st.tabs(room_tabs)
    tab1 = tab_results[0]
    tab2 = tab_results[1] if can("add_room") else None

    with tab1:
        rooms = st.session_state.rooms
        if not rooms:
            st.info("No rooms added yet.")
        else:
            for r in rooms:
                color = {"occupied": "#f8d7da", "available": "#d4edda", "cleaning": "#fff3cd"}.get(r["status"], "#eee")
                c1, c2, c3, c4, c5 = st.columns([1, 2, 1.5, 2, 2])
                c1.markdown(f"**{r['num']}**")
                c2.write(r["type"])
                c3.write(r["ac"])
                c4.markdown(f"<span style='background:{color};padding:2px 10px;border-radius:12px;font-size:12px'>{r['status']}</span>", unsafe_allow_html=True)
                with c5:
                    sc1, sc2, sc3 = st.columns(3)
                    # Only allow toggling available <-> cleaning manually
                    # "occupied" is set automatically by the availability engine
                    if r["status"] == "occupied":
                        sc1.markdown("<div style='font-size:11px;color:#aaa;padding:4px'>Auto-set</div>", unsafe_allow_html=True)
                    else:
                        next_manual = "cleaning" if r["status"] == "available" else "available"
                        if sc1.button("🔄", key=f"tog_{r['num']}", help=f"Set to {next_manual}"):
                            require_online()
                            DB.update_room(r["num"], {"status": next_manual})
                            invalidate_cache()
                            st.rerun()
                    if can("edit_room") and sc2.button("✏️", key=f"edit_r_{r['num']}", help="Edit room"):
                        st.session_state["edit_room"] = r["num"]
                        st.rerun()
                    if can("delete_room") and sc3.button("🗑️", key=f"del_{r['num']}"):
                        require_online()
                        DB.delete_room(r["num"])
                        invalidate_cache()
                        st.rerun()
                # ── Inline edit form ──────────────────────────────────────────
                if st.session_state.get("edit_room") == r["num"]:
                    with st.form(f"edit_room_form_{r['num']}"):
                        st.markdown(f"**✏️ Editing Room {r['num']}**")
                        ec1, ec2 = st.columns(2)
                        new_type  = ec1.selectbox("Room Type", ["Standard","Deluxe","Suite"],
                                                  index=["Standard","Deluxe","Suite"].index(r["type"]))
                        new_ac    = ec2.selectbox("AC / Non-AC", ["AC","Non-AC"],
                                                  index=["AC","Non-AC"].index(r["ac"]))
                        new_stat2 = st.selectbox("Status", ["available","occupied","cleaning"],
                                                  index=["available","occupied","cleaning"].index(r.get("status","available")))
                        save_col, cancel_col = st.columns(2)
                        save_it   = save_col.form_submit_button("💾 Save Changes", use_container_width=True)
                        cancel_it = cancel_col.form_submit_button("✖ Cancel", use_container_width=True)
                        if save_it:
                            DB.update_room(r["num"], {
                                "type": new_type, "ac": new_ac,
                                "status": new_stat2,
                            })
                            st.session_state.pop("edit_room", None)
                            st.success(f"✅ Room {r['num']} updated!")
                            st.rerun()
                        if cancel_it:
                            st.session_state.pop("edit_room", None)
                            st.rerun()
                st.markdown("---")

    if tab2 is not None:
     with tab2:
        st.subheader("Add New Room")
        with st.form("add_room_form"):
            c1, c2 = st.columns(2)
            num  = c1.text_input("Room Number", placeholder="e.g. 201")
            rtyp = c2.selectbox("Room Type", ["Standard", "Deluxe", "Suite"])
            ac = st.selectbox("AC / Non-AC", ["AC", "Non-AC"])
            extra_bed     = False
            extra_price   = 0
            bonfire       = False
            bonfire_price = 0
            submitted = st.form_submit_button("✅ Add Room", use_container_width=True)
            if submitted:
                if not num:
                    st.error("Enter room number.")
                elif any(r["num"] == num for r in st.session_state.rooms):
                    st.error(f"Room {num} already exists.")
                else:
                    require_online()
                    DB.add_room({
                        "num": num, "type": rtyp, "ac": ac,
                        "price": 0, "extra_bed": extra_bed,
                        "extra_price": extra_price if extra_bed else 0,
                        "bonfire": bonfire,
                        "bonfire_price": bonfire_price if bonfire else 0,
                        "status": "available"
                    })
                    st.success(f"✅ Room **{num}** added! | {rtyp} | {ac}")
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: BOOKINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Bookings":
    st.title("📋 Bookings")

    tab1, tab2, tab3 = st.tabs(["All Bookings", "➕ New Booking", "📤 Import from Excel"])

    with tab1:
        bookings = st.session_state.bookings
        today_str = str(date.today())

        # ── Split into logical groups ─────────────────────────────────────────
        today_checkins  = sorted([b for b in bookings if b.get("checkin")  == today_str
                                   and b.get("status") in ("confirmed","checked-in")],
                                  key=lambda x: x.get("room",""))
        today_checkouts = sorted([b for b in bookings if b.get("checkout") == today_str
                                   and b.get("status") == "checked-in"],
                                  key=lambda x: x.get("room",""))
        overdue         = sorted([b for b in bookings if b.get("checkout","") < today_str
                                   and b.get("status") == "checked-in"],
                                  key=lambda x: x.get("checkout",""))
        active_stays    = sorted([b for b in bookings if b.get("status") == "checked-in"
                                   and b.get("checkout","") >= today_str
                                   and b.get("checkin","") < today_str],
                                  key=lambda x: x.get("checkout",""))
        upcoming        = sorted([b for b in bookings if b.get("status") == "confirmed"
                                   and b.get("checkin","") > today_str],
                                  key=lambda x: x.get("checkin",""))
        past_bookings   = sorted([b for b in bookings if b.get("status") == "checked-out"],
                                  key=lambda x: x.get("checkout",""), reverse=True)

        # ── Summary banner ────────────────────────────────────────────────────
        if today_checkins or today_checkouts or overdue:
            parts = []
            if overdue:         parts.append(f"🔴 {len(overdue)} overdue checkout{'s' if len(overdue)>1 else ''}")
            if today_checkouts: parts.append(f"🚪 {len(today_checkouts)} checking out today")
            if today_checkins:  parts.append(f"🛎️ {len(today_checkins)} checking in today")
            st.warning("  |  ".join(parts))

        # ── Helper: render one booking card ──────────────────────────────────
        def booking_card(b, show_checkin_btn=False, show_checkout_btn=False, border_color="#d8b4fe", bg_color="#faf5ff"):
            n   = nights(b["checkin"], b["checkout"])
            rms = b.get("room","—")
            extras = []
            if b.get("extra_bed"): extras.append("🛏️")
            if b.get("bonfire"):   extras.append("🔥")
            if b.get("meal_plan","") not in ("","No Meals (Room Only)"): extras.append("🍽️")
            ext_str = " ".join(extras) or ""

            with st.container():
                c0,c1,c2,c3,c4,c5 = st.columns([2.5,1,1.5,1.5,0.8,2.5])
                c0.markdown(f"**{b['guest']}**")
                c1.write(f"Rm {rms}")
                c2.write(b["checkin"])
                c3.write(b["checkout"])
                c4.write(f"{n}N")
                with c5:
                    btns = st.columns(3 if (show_checkin_btn or show_checkout_btn) else 2)
                    btn_idx = 0

                    if show_checkin_btn and can("add_booking"):
                        if btns[btn_idx].button("✅ Check In", key=f"ci_{b['id']}",
                                                 use_container_width=True):
                            require_online()
                            DB.update_booking(b["id"], {"status": "checked-in"})
                            for rn in b.get("rooms", [b.get("room","")]):
                                DB.update_room_status(rn.strip(), "occupied")
                            if DB.MODE == "online":
                                DB.create_notification(
                                    f"🛎️ {b['guest']} checked in — Room {rms}",
                                    "info", "checkin", b["id"]
                                )
                            invalidate_cache()
                            st.rerun()
                        btn_idx += 1

                    if show_checkout_btn and can("checkout_guest"):
                        if btns[btn_idx].button("🚪 Check Out", key=f"co_{b['id']}",
                                                  use_container_width=True):
                            require_online()
                            DB.update_booking(b["id"], {"status": "checked-out"})
                            for rn in b.get("rooms", [b.get("room","")]):
                                DB.update_room_status(rn.strip(), "cleaning")
                            if DB.MODE == "online":
                                DB.create_notification(
                                    f"🚪 {b['guest']} checked out — Room {rms}",
                                    "info", "checkout", b["id"]
                                )
                            invalidate_cache()
                            st.rerun()
                        btn_idx += 1

                    if btns[btn_idx].button("✏️", key=f"edit_btn_{b['id']}", help="Edit"):
                        st.session_state["edit_booking"] = b["id"]
                        st.rerun()

                    if can("delete_booking") and len(btns) > btn_idx+1:
                        if btns[btn_idx+1].button("🗑️", key=f"del_{b['id']}", help="Delete"):
                            require_online()
                            DB.delete_booking(b["id"])
                            invalidate_cache()
                            st.rerun()

                if ext_str or b.get("agent"):
                    st.caption(f"  {ext_str}  {'🏢 '+b['agent'] if b.get('agent') else ''}  {'📞 '+b['phone'] if b.get('phone') else ''}")

                with st.expander("📋 Details & Edit"):
                    d1, d2 = st.columns(2)
                    d1.write(f"📞 {b.get('phone','—')} | 🏢 {b.get('agent','Direct') or 'Direct'}")
                    d1.write(f"🍽️ {b.get('meal_plan','No Meals')}")
                    adv = b.get('advance_paid', 0)
                    d2.write(f"💳 Advance: {fmt(adv)} via {b.get('advance_method','—')}" if adv else "💳 No advance")
                    d2.write(f"📝 {b.get('notes','—') or '—'}")

                if st.session_state.get("edit_booking") == b["id"]:
                    with st.form(f"edit_booking_{b['id']}"):
                        st.markdown(f"**✏️ Editing — {b['guest']}**")
                        be1, be2 = st.columns(2)
                        new_guest  = be1.text_input("Guest Name", value=b["guest"])
                        new_phone  = be2.text_input("Phone", value=b.get("phone",""))
                        be3, be4 = st.columns(2)
                        new_checkin  = be3.date_input("Check-in",  value=datetime.strptime(b["checkin"],"%Y-%m-%d").date())
                        new_checkout = be4.date_input("Check-out", value=datetime.strptime(b["checkout"],"%Y-%m-%d").date())
                        be5, be6 = st.columns(2)
                        new_agent  = be5.text_input("Travel Agent", value=b.get("agent",""))
                        new_season = be6.selectbox("Season", ["Peak","Off-Peak"],
                                                   index=0 if b.get("season","Peak")=="Peak" else 1)
                        be7, be8 = st.columns(2)
                        new_eb     = be7.checkbox("Extra Bed?", value=b.get("extra_bed", False))
                        new_eb_cnt = be8.selectbox("Number of Extra Beds", [1, 2, 3, 4],
                                                    index=min(max(0, int(b.get("extra_bed_count", 1)) - 1), 3))
                        be9, be10 = st.columns(2)
                        new_bf     = be9.checkbox("🔥 Bonfire?", value=b.get("bonfire", False))
                        stat_opts  = ["confirmed","checked-in","checked-out"]
                        new_status = be10.selectbox("Status", stat_opts,
                                                    index=stat_opts.index(b.get("status","confirmed")))
                        new_meal   = st.selectbox("Meal Plan", [
                            "No Meals (Room Only)","Breakfast Only (CP)",
                            "Breakfast + Dinner (MAP)","All Meals — Breakfast, Lunch & Dinner (AP)"],
                            index=["No Meals (Room Only)","Breakfast Only (CP)",
                                   "Breakfast + Dinner (MAP)","All Meals — Breakfast, Lunch & Dinner (AP)"].index(
                                   b.get("meal_plan","No Meals (Room Only)")))
                        new_notes  = st.text_area("Notes", value=b.get("notes",""), height=60)
                        sv, cn = st.columns(2)
                        do_save   = sv.form_submit_button("💾 Save", use_container_width=True)
                        do_cancel = cn.form_submit_button("✖ Cancel", use_container_width=True)
                        if do_save:
                            require_online()
                            DB.update_booking(b["id"], {
                                "guest": new_guest, "phone": new_phone,
                                "checkin": str(new_checkin), "checkout": str(new_checkout),
                                "agent": new_agent, "season": new_season,
                                "extra_bed": new_eb,
                                "extra_bed_count": int(new_eb_cnt) if new_eb else 0,
                                "bonfire": new_bf, "status": new_status,
                                "meal_plan": new_meal, "notes": new_notes,
                            })
                            if new_status == "checked-out":
                                for rn in b.get("rooms", [b.get("room","")]):
                                    DB.update_room(rn.strip(), {"status": "cleaning"})
                            invalidate_cache()
                            st.session_state.pop("edit_booking", None)
                            st.success(f"✅ Updated!")
                            st.rerun()
                        if do_cancel:
                            st.session_state.pop("edit_booking", None)
                            st.rerun()
                st.markdown(f"<hr style='margin:3px 0;border-color:{border_color}'>",
                            unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 1 — OVERDUE (most urgent)
        # ══════════════════════════════════════════════════════════════════════
        if overdue:
            st.markdown("""
            <div style='background:#fee2e2;border:1.5px solid #dc2626;border-radius:10px;
                        padding:8px 16px;margin-bottom:8px'>
                <span style='color:#991b1b;font-weight:700;font-size:15px'>
                    🔴 Overdue Checkouts — Immediate Action Needed
                </span>
            </div>""", unsafe_allow_html=True)
            for b in overdue:
                booking_card(b, show_checkout_btn=True, border_color="#fca5a5", bg_color="#fff5f5")

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 2 — TODAY'S CHECK-OUTS
        # ══════════════════════════════════════════════════════════════════════
        if today_checkouts:
            st.markdown("""
            <div style='background:#fef3c7;border:1.5px solid #f59e0b;border-radius:10px;
                        padding:8px 16px;margin-bottom:8px;margin-top:12px'>
                <span style='color:#92400e;font-weight:700;font-size:15px'>
                    🚪 Checking Out Today
                </span>
            </div>""", unsafe_allow_html=True)
            for b in today_checkouts:
                booking_card(b, show_checkout_btn=True, border_color="#fcd34d", bg_color="#fffbeb")

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 3 — TODAY'S CHECK-INS
        # ══════════════════════════════════════════════════════════════════════
        if today_checkins:
            st.markdown("""
            <div style='background:#d1fae5;border:1.5px solid #059669;border-radius:10px;
                        padding:8px 16px;margin-bottom:8px;margin-top:12px'>
                <span style='color:#065f46;font-weight:700;font-size:15px'>
                    🛎️ Checking In Today
                </span>
            </div>""", unsafe_allow_html=True)
            for b in today_checkins:
                booking_card(b, show_checkin_btn=True, border_color="#6ee7b7", bg_color="#f0fdf4")

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 4 — ACTIVE STAYS (currently in-house)
        # ══════════════════════════════════════════════════════════════════════
        if active_stays:
            st.markdown(f"""
            <div style='background:#eff6ff;border:1.5px solid #3b82f6;border-radius:10px;
                        padding:8px 16px;margin-bottom:8px;margin-top:12px'>
                <span style='color:#1e40af;font-weight:700;font-size:15px'>
                    🏨 Currently In-House ({len(active_stays)})
                </span>
            </div>""", unsafe_allow_html=True)
            for b in active_stays:
                booking_card(b, show_checkout_btn=True, border_color="#bfdbfe", bg_color="#eff6ff")

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 5 — UPCOMING CONFIRMED
        # ══════════════════════════════════════════════════════════════════════
        if upcoming:
            st.markdown(f"""
            <div style='background:#f5f3ff;border:1.5px solid #8b5cf6;border-radius:10px;
                        padding:8px 16px;margin-bottom:8px;margin-top:12px'>
                <span style='color:#5b21b6;font-weight:700;font-size:15px'>
                    📅 Upcoming Confirmed ({len(upcoming)})
                </span>
            </div>""", unsafe_allow_html=True)
            for b in upcoming[:10]:
                booking_card(b, show_checkin_btn=False, border_color="#ddd6fe", bg_color="#f5f3ff")
            if len(upcoming) > 10:
                st.caption(f"... and {len(upcoming)-10} more upcoming bookings")

        if not any([overdue, today_checkins, today_checkouts, active_stays, upcoming]):
            st.info("No active bookings.")

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 6 — PAST BOOKINGS (hidden by default)
        # ══════════════════════════════════════════════════════════════════════
        st.markdown("---")
        show_history = st.checkbox(f"📜 Show Past Bookings ({len(past_bookings)} records)")
        if show_history:
            search_past = st.text_input("🔍 Search past bookings", placeholder="Guest name...")
            filtered_past = [b for b in past_bookings
                             if not search_past or search_past.lower() in b["guest"].lower()]
            for b in filtered_past[:30]:
                booking_card(b, border_color="#e5e7eb", bg_color="#f9fafb")
            if len(filtered_past) > 30:
                st.caption(f"Showing 30 of {len(filtered_past)} past bookings")

    with tab2:
        st.subheader("New Booking")
        available_rooms = [r for r in st.session_state.rooms if r["status"] in ["available", "cleaning"]]
        if not available_rooms:
            st.warning("No available rooms right now.")
        else:
            with st.form("add_booking_form"):
                c1, c2 = st.columns(2)
                guest = c1.text_input("Guest Name *")
                phone = c2.text_input("Phone Number")
                c3, c4 = st.columns(2)
                agent    = c3.text_input("Travel Agent (optional)")
                season   = c4.selectbox("Season", ["Peak", "Off-Peak"])
                c5, c6 = st.columns(2)
                checkin  = c5.date_input("Check-in Date",  value=date.today())
                checkout = c6.date_input("Check-out Date", value=date.today() + timedelta(days=3))

                st.markdown("---")
                st.markdown("**🛏️ Room Selection** — select one or more rooms")
                room_options = [f"{r['num']} – {r['type']} ({r['ac']})" for r in available_rooms]
                rooms_selected = st.multiselect("Select Room(s) *", room_options)
                rp1, rp2 = st.columns(2)
                room_price_per_night = rp1.number_input("Room Price per Night (₹)", min_value=0, value=2500, step=100)
                rp2.caption("💡 Price applies to all selected rooms combined")

                st.markdown("---")
                st.markdown("**🛏️ Extra Bedding**")
                extra_bed       = st.checkbox("Extra Bed Required?")
                eb1, eb2 = st.columns(2)
                extra_bed_count = eb1.selectbox("Number of Extra Beds", ["0 (None)", "1", "2", "3", "4"])
                extra_bed_price = eb2.number_input("Extra Bed Charge (₹/bed/night)", min_value=0, value=500, step=50)

                st.markdown("---")
                st.markdown("**🍽️ Meal Plan**")
                ca, cb = st.columns(2)
                meal_plan = ca.selectbox("Meal Plan", [
                    "No Meals (Room Only)",
                    "Breakfast Only (CP)",
                    "Breakfast + Dinner (MAP)",
                    "All Meals — Breakfast, Lunch & Dinner (AP)",
                ])
                meal_price = cb.number_input("Meal Charge per person per day (Rs.)", min_value=0, value=0, step=50)

                st.markdown("---")
                st.markdown("**💳 Advance Payment**")
                cp, dp = st.columns(2)
                advance_paid   = cp.number_input("Advance Amount Paid (Rs.)", min_value=0, value=0, step=100)
                advance_method = dp.selectbox("Payment Method", ["Cash", "UPI", "Bank Transfer", "Card", "Online"])

                st.markdown("---")
                st.markdown("**🔥 Bonfire**")
                bonfire_price = st.number_input(
                    "Bonfire Charge (₹/night) — leave 0 if not required",
                    min_value=0, value=0, step=50
                )
                bonfire_requested = bonfire_price > 0

                notes     = st.text_area("Notes / Special Requests", height=80)

                # ── Estimated Cost Preview ────────────────────────────────────
                st.markdown("---")
                st.markdown("**💰 Estimated Cost**")
                try:
                    n_nights    = max(1, (checkout - checkin).days)
                    est_room    = room_price_per_night * n_nights
                    est_eb      = (extra_bed_price * (int(extra_bed_count) if extra_bed and extra_bed_count != "0 (None)" else 0) * n_nights) if extra_bed else 0
                    est_meal    = meal_price * n_nights
                    est_bonfire = bonfire_price * n_nights
                    est_total   = est_room + est_eb + est_meal + est_bonfire

                    ec1, ec2, ec3, ec4, ec5 = st.columns(5)
                    ec1.metric("🛏️ Room", fmt(est_room),
                               f"{n_nights} night{'s' if n_nights>1 else ''}")
                    ec2.metric("🛏️ Extra Bed", fmt(est_eb) if est_eb else "—")
                    ec3.metric("🍽️ Meals", fmt(est_meal) if est_meal else "—")
                    ec4.metric("🔥 Bonfire", fmt(est_bonfire) if est_bonfire else "—")
                    ec5.metric("💰 Total Est.", fmt(est_total))

                    if advance_paid > 0:
                        st.markdown(
                            f"<div style='background:#eff6ff;border-radius:8px;padding:10px 14px;"
                            f"font-size:13px;margin-top:4px'>"
                            f"💳 After advance of <b>{fmt(advance_paid)}</b>: "
                            f"Balance due = <b>{fmt(max(0, est_total - advance_paid))}</b>"
                            f"</div>", unsafe_allow_html=True
                        )
                except Exception:
                    st.caption("Fill in dates and prices above to see estimate.")

                submitted = st.form_submit_button("✅ Confirm Booking", use_container_width=True)
                if submitted:
                    if not guest:
                        st.error("Enter guest name.")
                    elif not rooms_selected:
                        st.error("Select at least one room.")
                    elif checkout <= checkin:
                        st.error("Check-out must be after check-in.")
                    else:
                        rnums = [r.split("–")[0].strip() for r in rooms_selected]
                        # ── Overbooking check ─────────────────────────────────
                        conflicts = []
                        for rnum in rnums:
                            clashes = check_overbooking(rnum, str(checkin), str(checkout))
                            for c in clashes:
                                conflicts.append(f"Room {rnum} is already booked by **{c['guest']}** ({c['checkin']} → {c['checkout']})")
                        if conflicts:
                            st.error("🚫 **Overbooking Conflict!** Cannot confirm booking:")
                            for cf in conflicts:
                                st.warning(cf)
                        else:
                            require_online()
                            new_id = DB.add_booking({
                                "guest": guest, "phone": phone,
                                "room": ", ".join(rnums), "rooms": rnums,
                                "agent": agent,
                                "checkin": str(checkin), "checkout": str(checkout),
                                "extra_bed": extra_bed,
                                "extra_bed_count": int(extra_bed_count) if extra_bed and extra_bed_count != "0 (None)" else 0,
                                "extra_bed_price": extra_bed_price if extra_bed else 0,
                                "room_price": room_price_per_night,
                                "season": season, "bonfire": bonfire_requested,
                                "bonfire_price": bonfire_price,
                                "meal_plan": meal_plan, "meal_price": meal_price,
                                "advance_paid": advance_paid, "advance_method": advance_method,
                                "notes": notes, "status": "confirmed",
                                "payment_status": "partial" if advance_paid > 0 else "unpaid",
                            })
                            if advance_paid > 0:
                                DB.add_payment({
                                    "booking_id": new_id, "guest": guest,
                                    "room": ", ".join(rnums), "amount": advance_paid,
                                    "method": advance_method, "type": "advance",
                                    "date": str(date.today()), "note": "Advance at booking",
                                })
                            if DB.MODE == "online":
                                DB.create_notification(
                                    f"📋 New booking: {guest} — Room(s) {', '.join(rnums)} | {checkin} → {checkout}",
                                    "info", "booking", new_id
                                )
                            # ── Success with cost summary ─────────────────────
                            n_nights_final = max(1, (checkout - checkin).days)
                            est_final = (room_price_per_night * n_nights_final +
                                         (extra_bed_price * (int(extra_bed_count) if extra_bed and extra_bed_count != "0 (None)" else 0) * n_nights_final if extra_bed else 0) +
                                         meal_price * n_nights_final +
                                         bonfire_price * n_nights_final)
                            msg = f"✅ Booking confirmed for **{guest}** — Room(s) {', '.join(rnums)} | {checkin} → {checkout}"
                            if extra_bed and extra_bed_count != "0 (None)": msg += f" | 🛏️ {extra_bed_count} Extra Bed(s)"
                            if bonfire_requested: msg += f" | 🔥 Bonfire: {fmt(bonfire_price)}/night"
                            if meal_plan != "No Meals (Room Only)": msg += f" | 🍽️ {meal_plan.split('(')[0].strip()}"
                            if advance_paid > 0:  msg += f" | 💳 Advance: {fmt(advance_paid)}"
                            msg += f" | 💰 Est. Total: {fmt(est_final)}"
                            st.success(msg)
                            invalidate_cache()
                            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 3: IMPORT FROM EXCEL
    # ═══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("📤 Import Bookings from Excel")
        st.markdown("""
        Upload your booking calendar Excel file and all bookings will be automatically
        imported into the app — no manual data entry needed!

        **Expected format:** Date in column A, Room numbers in row 2 (cols B onwards),
        agent/booking name in each cell. This matches your existing booking calendar format.
        """)

        uploaded_file = st.file_uploader("Choose your Excel file", type=["xlsx","xls"])

        if uploaded_file:
            try:
                import pandas as pd
                df = pd.read_excel(uploaded_file, header=None)

                # Parse room numbers from row index 1
                room_cols = {}
                for col_idx in range(1, df.shape[1]):
                    val = df.iloc[1, col_idx]
                    if pd.notna(val):
                        try:
                            room_cols[col_idx] = str(int(float(val)))
                        except:
                            pass

                if not room_cols:
                    st.error("Could not find room numbers in row 2. Please check your file format.")
                else:
                    st.success(f"✅ Found {len(room_cols)} rooms: {', '.join(room_cols.values())}")

                    # Parse bookings — group consecutive days per agent+room
                    raw = {}  # (agent, room) -> list of dates
                    for row_idx in range(2, len(df)):
                        row = df.iloc[row_idx]
                        date_val = row[0]
                        if pd.isna(date_val):
                            continue
                        try:
                            d = pd.to_datetime(date_val).date()
                        except:
                            continue
                        for col_idx, room in room_cols.items():
                            cell = row[col_idx]
                            if pd.notna(cell) and str(cell).strip() and str(cell).strip().lower() != "nan":
                                agent = str(cell).strip()
                                key = (agent, room)
                                if key not in raw:
                                    raw[key] = []
                                raw[key].append(d)

                    # Convert to bookings with checkin/checkout
                    preview_bookings = []
                    for (agent, room), dates in raw.items():
                        if not dates:
                            continue
                        dates_sorted = sorted(set(dates))
                        # Group consecutive dates into single booking
                        groups = []
                        start = dates_sorted[0]
                        prev  = dates_sorted[0]
                        for d in dates_sorted[1:]:
                            from datetime import timedelta
                            if (d - prev).days <= 1:
                                prev = d
                            else:
                                groups.append((start, prev))
                                start = d
                                prev  = d
                        groups.append((start, prev))

                        for cin, cout in groups:
                            from datetime import timedelta
                            preview_bookings.append({
                                "guest":    agent,
                                "agent":    agent,
                                "room":     room,
                                "rooms":    [room],
                                "checkin":  str(cin),
                                "checkout": str(cout + timedelta(days=1)),
                                "status":   "confirmed",
                                "phone":    "",
                                "season":   "Peak",
                                "extra_bed": False,
                                "extra_bed_count": 0,
                                "bonfire":  False,
                                "meal_plan": "No Meals (Room Only)",
                                "meal_price": 0,
                                "advance_paid": 0,
                                "advance_method": "Cash",
                                "notes":    "Imported from Excel",
                            })

                    st.markdown(f"**📋 Preview — {len(preview_bookings)} bookings found:**")

                    # Show preview table
                    prev_df = pd.DataFrame([{
                        "Guest/Agent": b["guest"],
                        "Room": b["room"],
                        "Check-in": b["checkin"],
                        "Check-out": b["checkout"],
                    } for b in preview_bookings])
                    st.dataframe(prev_df, use_container_width=True, hide_index=True)

                    # Import options
                    st.markdown("---")
                    col_a, col_b = st.columns(2)
                    skip_existing = col_a.checkbox("Skip duplicates (same guest + room + date)", value=True)

                    if col_b.button("✅ Import All Bookings", type="primary", use_container_width=True):
                        imported = 0
                        skipped  = 0
                        next_id  = max((b["id"] for b in st.session_state.bookings), default=0) + 1

                        for pb in preview_bookings:
                            # Check for duplicates
                            is_dup = any(
                                x["guest"] == pb["guest"] and
                                x["room"]  == pb["room"]  and
                                x["checkin"] == pb["checkin"]
                                for x in st.session_state.bookings
                            )
                            if skip_existing and is_dup:
                                skipped += 1
                                continue

                            DB.add_booking(pb)
                            from datetime import date as date_cls
                            try:
                                cin  = date_cls.fromisoformat(pb["checkin"])
                                cout = date_cls.fromisoformat(pb["checkout"])
                                if cin <= date_cls.today() <= cout:
                                    DB.update_room(pb["room"].strip(), {"status": "occupied"})
                            except:
                                pass
                            imported += 1
                        st.success(f"🎉 Imported **{imported}** bookings! Skipped **{skipped}** duplicates.")
                        st.balloons()
                        st.rerun()

            except Exception as e:
                st.error(f"Error reading file: {e}")
                st.caption("Make sure your Excel file matches the expected format.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: BILLING
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "₹  Billing":
    st.title("₹ Billing & Invoices")

    tab1, tab2 = st.tabs(["All Bills", "➕ Generate Bill"])

    def generate_invoice_pdf(b, total):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        import io
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                topMargin=15*mm, bottomMargin=15*mm,
                                leftMargin=20*mm, rightMargin=20*mm)
        purple      = colors.HexColor("#3b1f6e")
        mid_purple  = colors.HexColor("#7c3aed")
        light_pur   = colors.HexColor("#f3eeff")
        styles      = getSampleStyleSheet()
        story       = []

        def sty(name, **kw):
            return ParagraphStyle(name, **kw)

        story.append(Paragraph("Savera Inn Resort",
            sty("h", fontSize=22, textColor=purple, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2)))
        story.append(Paragraph("Kashmir, India  |  savera.inn@gmail.com  |  +91 98765 43210",
            sty("s", fontSize=10, textColor=colors.HexColor("#7c5cbf"), alignment=TA_CENTER, spaceAfter=4)))
        story.append(HRFlowable(width="100%", thickness=2, color=mid_purple, spaceAfter=6))

        meta = Table([
            [Paragraph("INVOICE", sty("i", fontSize=16, textColor=purple, fontName="Helvetica-Bold")),
             Paragraph(f"Bill No: <b>{b['bill_id']}</b><br/>Date: {b.get('date', str(date.today()))}",
                       sty("r", fontSize=10, textColor=colors.grey, alignment=TA_RIGHT))]
        ], colWidths=["60%","40%"])
        meta.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(meta)
        story.append(Spacer(1, 5*mm))

        booking = next((bk for bk in st.session_state.bookings
                        if bk["guest"]==b["guest"] and bk["room"]==b["room"]), {})
        gdata = [
            ["Guest Name",   b["guest"],               "Room No.",   b["room"]],
            ["Phone",        booking.get("phone","—"),  "Check-in",   booking.get("checkin","—")],
            ["Travel Agent", booking.get("agent","Direct") or "Direct", "Check-out", booking.get("checkout","—")],
            ["Nights",       str(b["nights"]),           "Status",    b["status"].title()],
        ]
        gt = Table(gdata, colWidths=[35*mm,55*mm,35*mm,45*mm])
        gt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(0,-1),light_pur), ("BACKGROUND",(2,0),(2,-1),light_pur),
            ("TEXTCOLOR",(0,0),(0,-1),purple),     ("TEXTCOLOR",(2,0),(2,-1),purple),
            ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"), ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),9), ("PADDING",(0,0),(-1,-1),5),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#d8b4fe")),
        ]))
        story.append(gt)
        story.append(Spacer(1, 5*mm))

        ppn = b["room_charge"] // max(b["nights"], 1)
        charges = [["Description", "Amount"]]
        charges.append([f"Room Charges ({b['nights']} nights x Rs.{ppn:,}/night)", f"Rs. {b['room_charge']:,}"])
        if b.get("extra_bed",0):   charges.append(["Extra Bed Charges",                  f"Rs. {b['extra_bed']:,}"])
        if b.get("meal",0):        charges.append([f"Meal Plan ({b.get('meal_plan','—')})", f"Rs. {b['meal']:,}"])
        if b.get("food",0):        charges.append(["Food & Beverages",                      f"Rs. {b['food']:,}"])
        if b.get("laundry",0):     charges.append(["Laundry Charges",                       f"Rs. {b['laundry']:,}"])
        if b.get("electricity",0): charges.append(["Electricity",                           f"Rs. {b['electricity']:,}"])
        if b.get("bonfire",0):     charges.append(["Bonfire",                               f"Rs. {b['bonfire']:,}"])
        if b.get("other",0):       charges.append(["Other Charges",                         f"Rs. {b['other']:,}"])
        gross = b.get("gross", total)
        adv   = b.get("advance_paid", 0)
        charges.append(["GROSS TOTAL", f"Rs. {gross:,}"])
        if adv:
            charges.append([f"Less: Advance Paid ({b.get('advance_method','Cash')})", f"- Rs. {adv:,}"])
        charges.append(["BALANCE DUE", f"Rs. {total:,}"])

        ct = Table(charges, colWidths=[120*mm, 50*mm])
        ct.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),purple),   ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,0),10),
            ("BACKGROUND",(0,-1),(-1,-1),mid_purple), ("TEXTCOLOR",(0,-1),(-1,-1),colors.white),
            ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"), ("FONTSIZE",(0,-1),(-1,-1),11),
            ("ROWBACKGROUNDS",(0,1),(-1,-2),[colors.white, light_pur]),
            ("ALIGN",(1,0),(1,-1),"RIGHT"), ("FONTSIZE",(0,1),(-1,-2),10),
            ("PADDING",(0,0),(-1,-1),7),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#d8b4fe")),
            ("LINEABOVE",(0,-1),(-1,-1),1.5,mid_purple),
        ]))
        story.append(ct)
        story.append(Spacer(1, 5*mm))

        sc = colors.HexColor("#16a34a") if b["status"]=="Paid" else colors.HexColor("#dc2626")
        story.append(Paragraph(f"Payment Status: {b['status'].upper()}",
            sty("ps", fontSize=11, textColor=sc, fontName="Helvetica-Bold", spaceAfter=6)))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d8b4fe"), spaceAfter=4))
        story.append(Paragraph(
            "Thank you for staying at Savera Inn Resort! We hope to welcome you again soon.<br/>"
            "For queries: savera.inn@gmail.com  |  +91 98765 43210",
            sty("ft", fontSize=8, textColor=colors.grey, alignment=TA_CENTER, leading=14)))
        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    with tab1:
        bills = st.session_state.bills
        if not bills:
            st.info("No bills generated yet.")
        else:
            for b in reversed(bills):
                gross   = (b["room_charge"] + b.get("food", 0) + b.get("laundry", 0) +
                           b.get("extra_bed", 0) + b.get("electricity", 0) +
                           b.get("bonfire", 0) + b.get("meal", 0) + b.get("other", 0))
                total   = b.get("total", gross)
                with st.expander(f"**{b['bill_id']}**  —  {b['guest']}  |  Room {b['room']}  |  Balance: **{fmt(total)}**  |  {b['status']}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Room Charge", fmt(b["room_charge"]))
                    c2.metric("Food",        fmt(b.get("food", 0)))
                    c3.metric("Laundry",     fmt(b.get("laundry", 0)))
                    c4.metric("Extra Bed",   fmt(b.get("extra_bed", 0)))
                    c1b, c2b, c3b, c4b = st.columns(4)
                    c1b.metric("Electricity",  fmt(b.get("electricity", 0)))
                    c2b.metric("🔥 Bonfire",   fmt(b.get("bonfire", 0)))
                    c3b.metric("🍽️ Meals",     fmt(b.get("meal", 0)))
                    c4b.metric("Other",        fmt(b.get("other", 0)))
                    c1c, c2c, c3c, c4c = st.columns(4)
                    c1c.metric("Gross Total",  fmt(b.get("gross", total)))
                    c2c.metric("💳 Advance",   fmt(b.get("advance_paid", 0)))
                    c3c.metric("Balance Due",  fmt(b.get("total", gross)))
                    c4c.metric("Status",       b["status"])
                    btn1, btn2, _ = st.columns([2, 2, 4])
                    if b["status"] != "Paid" and can("mark_paid"):
                        if btn1.button("✅ Mark as Paid", key=f"pay_{b['bill_id']}"):
                            DB.update_bill(b["bill_id"], {"status": "Paid"})
                            st.rerun()
                    pdf_bytes = generate_invoice_pdf(b, b.get("total", gross))
                    btn2.download_button(
                        label="🖨️ Download Invoice",
                        data=pdf_bytes,
                        file_name=f"Invoice_{b['bill_id']}_{b['guest'].replace(' ','_')}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{b['bill_id']}"
                    )

    with tab2:
        if not can("generate_bill"):
            lock("generate_bill")
        else:
         st.subheader("Generate New Bill")
        active_bookings = [b for b in st.session_state.bookings if b["status"] in ["checked-in", "confirmed", "checked-out"]]
        if not active_bookings:
            st.warning("No bookings available for billing.")
        else:
            booking_opts = [f"{b['guest']} – Room {b['room']} ({b['checkin']} → {b['checkout']})" for b in active_bookings]
            sel    = st.selectbox("Select Booking", booking_opts)
            b_idx  = booking_opts.index(sel)
            b_data = active_bookings[b_idx]
            r_data = get_room(b_data["room"])
            n      = nights(b_data["checkin"], b_data["checkout"])
            # Multi-room: use price set at booking time
            rnums_bill   = b_data.get("rooms", [b_data.get("room","")]) if isinstance(b_data.get("rooms"), list) else [b_data.get("room","")]
            room_price   = int(b_data.get("room_price", 0))  # Price set at booking time
            room_charge  = room_price * n
            eb_count     = int(b_data.get("extra_bed_count", 1)) if b_data.get("extra_bed") else 0
            eb_price     = int(b_data.get("extra_bed_price", 0))
            extra_charge = eb_price * eb_count * n if b_data.get("extra_bed") and eb_count else 0

            # ── Pre-filled summary ────────────────────────────────────────────
            meal_default = b_data.get("meal_price", 0) * n if b_data.get("meal_price", 0) else 0
            adv_paid     = b_data.get("advance_paid", 0)
            meal_label   = b_data.get("meal_plan", "No Meals")
            bonfire_default = int(b_data.get("bonfire_price", 0)) * n if b_data.get("bonfire") else 0

            rooms_info = ", ".join([f"Room {rn}" for rn in rnums_bill])
            st.markdown(f"**{n} nights** | {rooms_info} | {fmt(room_price)}/night = **{fmt(room_charge)}**")
            if extra_charge:
                st.markdown(f"Extra beds: {eb_count} × {n} nights × {fmt(eb_price)}/night = **{fmt(extra_charge)}**")
            elif b_data.get("extra_bed") and eb_count:
                st.markdown(f"⚠️ Extra bed price not set — please enter below")
            if bonfire_default:
                st.markdown(f"🔥 Bonfire: {n} nights × {fmt(b_data.get('bonfire_price',0))}/night = **{fmt(bonfire_default)}**")
            if meal_default:
                st.markdown(f"Meals ({meal_label}): {n} days × {fmt(b_data.get('meal_price',0))}/day = **{fmt(meal_default)}**")
            if adv_paid:
                st.markdown(f"💳 Advance already paid: **{fmt(adv_paid)}** via {b_data.get('advance_method','Cash')}")

            with st.form("bill_form"):
                c1, c2 = st.columns(2)
                food    = c1.number_input("🍽️ Food Charges (Rs.)",    min_value=0, value=0, step=50)
                laundry = c2.number_input("👕 Laundry Charges (Rs.)", min_value=0, value=0, step=50)
                c3, c4 = st.columns(2)
                electricity    = c3.number_input("💡 Electricity Charges (Rs.)", min_value=0, value=0, step=50)
                bonfire_charge = c4.number_input("🔥 Bonfire Charges (Rs.)", min_value=0, value=int(bonfire_default), step=50)
                c5, c6 = st.columns(2)
                meal_charge = c5.number_input("🍽️ Meal Charges (Rs.)", min_value=0, value=int(meal_default), step=50)
                other       = c6.number_input("📦 Other Charges (Rs.)", min_value=0, value=0, step=50)
                advance_deduct = st.number_input("💳 Advance Already Paid — Deduct (Rs.)", min_value=0, value=int(adv_paid), step=100)
                gross = room_charge + extra_charge + food + laundry + electricity + bonfire_charge + meal_charge + other
                balance = max(0, gross - advance_deduct)
                st.markdown("---")
                col_g, col_a, col_b = st.columns(3)
                col_g.metric("Gross Total", fmt(gross))
                col_a.metric("Advance Paid", fmt(advance_deduct))
                col_b.metric("Balance Due", fmt(balance))
                submitted = st.form_submit_button("🧾 Save Bill", use_container_width=True)
                if submitted:
                    new_bill_id = DB.next_bill_id()
                    require_online()
                    DB.add_bill({
                        "bill_id":        new_bill_id,
                        "guest":          b_data["guest"],
                        "room":           b_data["room"],
                        "nights":         n,
                        "room_charge":    room_charge,
                        "extra_bed":      extra_charge,
                        "food":           food,
                        "laundry":        laundry,
                        "electricity":    electricity,
                        "bonfire":        bonfire_charge,
                        "meal":           meal_charge,
                        "meal_plan":      meal_label,
                        "other":          other,
                        "advance_paid":   advance_deduct,
                        "advance_method": b_data.get("advance_method", "Cash"),
                        "gross":          gross,
                        "total":          balance,
                        "status":         "Pending",
                        "date":           str(date.today()),
                        "booking_id":     b_data.get("id"),
                    })
                    st.success(f"✅ Bill saved! Gross: {fmt(gross)} | Advance: {fmt(advance_deduct)} | Balance Due: {fmt(balance)}")
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: EXPENSES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧾 Expenses":
    st.title("🧾 Expenses")

    CATEGORIES = ["Electricity", "Laundry", "Food & Beverages", "Maintenance",
                  "Staff Salary", "Marketing", "Other"]

    tab1, tab2, tab3 = st.tabs(["📋 Expense Log", "➕ Add Expense", "📤 Import from Excel"])

    # ── TAB 1: Expense Log with Edit & Delete ─────────────────────────────────
    with tab1:
        expenses = st.session_state.expenses
        if not expenses:
            st.info("No expenses logged yet.")
        else:
            # Summary metrics
            cats = {}
            for e in expenses:
                cats[e["category"]] = cats.get(e["category"], 0) + e["amount"]
            cols = st.columns(min(len(cats), 4))
            for i, (cat, amt) in enumerate(sorted(cats.items(), key=lambda x: -x[1])[:4]):
                cols[i].metric(cat, fmt(amt))
            st.markdown("---")

            total_exp = sum(e["amount"] for e in expenses)
            st.markdown(f"**Total Expenses: {fmt(total_exp)}**")
            st.markdown("")

            # Table headers
            h1,h2,h3,h4,h5 = st.columns([1.2,1.8,2.5,1.2,1.5])
            h1.markdown("**Date**")
            h2.markdown("**Category**")
            h3.markdown("**Description**")
            h4.markdown("**Amount**")
            h5.markdown("**Action**")
            st.markdown("<hr style='margin:2px 0 6px;border-color:#d8b4fe'>", unsafe_allow_html=True)

            for e in sorted(expenses, key=lambda x: x["date"], reverse=True):
                c1,c2,c3,c4,c5 = st.columns([1.2,1.8,2.5,1.2,1.5])
                c1.write(e["date"])
                c2.write(e["category"])
                c3.write(e.get("desc","—"))
                c4.write(fmt(e["amount"]))
                with c5:
                    a1, a2 = st.columns(2)
                    if can("add_expense") and a1.button("✏️", key=f"edit_e_{e['id']}", help="Edit"):
                        st.session_state["edit_expense"] = e["id"]
                        st.rerun()
                    if can("add_expense") and a2.button("🗑️", key=f"del_e_{e['id']}", help="Delete"):
                        require_online()
                        DB.delete_expense(e["id"])
                        invalidate_cache()
                        st.success("Expense deleted!")
                        st.rerun()

                # Inline edit form
                if st.session_state.get("edit_expense") == e["id"]:
                    with st.form(f"edit_exp_{e['id']}"):
                        st.markdown(f"**✏️ Editing expense**")
                        ee1, ee2 = st.columns(2)
                        new_cat  = ee1.selectbox("Category", CATEGORIES,
                                                  index=CATEGORIES.index(e["category"]) if e["category"] in CATEGORIES else 0)
                        new_amt  = ee2.number_input("Amount (₹)", min_value=0,
                                                     value=int(e["amount"]), step=50)
                        ee3, ee4 = st.columns(2)
                        new_date = ee3.date_input("Date", value=datetime.strptime(str(e["date"]), "%Y-%m-%d").date())
                        new_desc = ee4.text_input("Description", value=e.get("desc",""))
                        sv, cn   = st.columns(2)
                        do_save  = sv.form_submit_button("💾 Save", use_container_width=True)
                        do_cancel= cn.form_submit_button("✖ Cancel", use_container_width=True)
                        if do_save:
                            require_online()
                            DB.update_expense(e["id"], {
                                "category": new_cat, "amount": new_amt,
                                "date": str(new_date), "description": new_desc
                            })
                            st.session_state.pop("edit_expense", None)
                            invalidate_cache()
                            st.success("✅ Expense updated!")
                            st.rerun()
                        if do_cancel:
                            st.session_state.pop("edit_expense", None)
                            st.rerun()
                st.markdown("<hr style='margin:2px 0;border-color:#f0e6ff'>", unsafe_allow_html=True)

    # ── TAB 2: Add Expense ────────────────────────────────────────────────────
    with tab2:
        if not can("add_expense"):
            lock("add_expense")
        else:
            st.subheader("Add Expense")
            with st.form("add_expense_form"):
                c1, c2 = st.columns(2)
                category = c1.selectbox("Category", CATEGORIES)
                amount   = c2.number_input("Amount (₹)", min_value=0, value=0, step=100)
                c3, c4 = st.columns(2)
                exp_date = c3.date_input("Date", value=date.today())
                desc     = c4.text_input("Description", placeholder="Brief description")
                submitted = st.form_submit_button("✅ Add Expense", use_container_width=True)
                if submitted:
                    if amount <= 0:
                        st.error("Enter a valid amount.")
                    else:
                        require_online()
                        DB.add_expense({
                            "date": str(exp_date),
                            "category": category, "desc": desc, "amount": amount
                        })
                        invalidate_cache()
                        st.success(f"✅ Expense of {fmt(amount)} added!")
                        st.rerun()

    # ── TAB 3: Import from Excel ──────────────────────────────────────────────
    with tab3:
        if not can("add_expense"):
            lock("add_expense")
        else:
            st.subheader("📤 Import Expenses from Excel")
            st.markdown("""
            Upload an Excel file with these columns:
            **Date | Category | Description | Amount**

            The first row should be the header.
            """)
            uploaded = st.file_uploader("Choose Excel file", type=["xlsx","xls"])
            if uploaded:
                try:
                    df_imp = pd.read_excel(uploaded)
                    df_imp.columns = [c.strip().lower() for c in df_imp.columns]

                    # Try to find matching columns flexibly
                    col_map = {}
                    for col in df_imp.columns:
                        if "date" in col:       col_map["date"]   = col
                        if "cat" in col:        col_map["cat"]    = col
                        if "desc" in col or "note" in col: col_map["desc"] = col
                        if "amount" in col or "amt" in col or "cost" in col: col_map["amt"] = col

                    if "amt" not in col_map:
                        st.error("Could not find an Amount column. Make sure your Excel has a column named 'Amount'.")
                    else:
                        preview_rows = []
                        for _, row in df_imp.iterrows():
                            try:
                                amt = float(row[col_map["amt"]])
                                if amt <= 0: continue
                                preview_rows.append({
                                    "date":     str(pd.to_datetime(row[col_map["date"]]).date()) if "date" in col_map and pd.notna(row.get(col_map["date"])) else str(date.today()),
                                    "category": str(row[col_map["cat"]]).strip() if "cat" in col_map else "Other",
                                    "desc":     str(row[col_map["desc"]]).strip() if "desc" in col_map else "",
                                    "amount":   int(amt),
                                })
                            except:
                                continue

                        st.markdown(f"**Preview — {len(preview_rows)} expenses found:**")
                        prev_df = pd.DataFrame(preview_rows)
                        st.dataframe(prev_df, use_container_width=True, hide_index=True)
                        st.markdown(f"**Total: {fmt(sum(r['amount'] for r in preview_rows))}**")

                        if st.button("✅ Import All Expenses", type="primary", use_container_width=True):
                            require_online()
                            for row in preview_rows:
                                DB.add_expense(row)
                            invalidate_cache()
                            st.success(f"🎉 Imported {len(preview_rows)} expenses!")
                            st.balloons()
                            st.rerun()
                except Exception as ex:
                    st.error(f"Error reading file: {ex}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PAYMENTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "💳 Payments":
    st.title("💳 Payment Tracking")

    payments = st.session_state.payments
    bookings = st.session_state.bookings
    bills    = st.session_state.bills

    # ── Summary metrics ───────────────────────────────────────────────────────
    total_received = sum(p["amount"] for p in payments if p.get("type") != "refund")
    total_refunded = sum(p["amount"] for p in payments if p.get("type") == "refund")
    total_pending  = sum(
        b.get("total", 0) - sum(p["amount"] for p in payments
                                if p.get("booking_id") == b.get("booking_id") and p.get("type") != "refund")
        for b in bills if b.get("status") != "Paid"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Received",  fmt(total_received))
    c2.metric("🔴 Total Refunded",  fmt(total_refunded))
    c3.metric("⏳ Pending Bills",   sum(1 for b in bills if b.get("status") != "Paid"))
    c4.metric("📋 Transactions",    len(payments))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📋 Transaction Log", "➕ Add Payment", "💸 Refund"])

    with tab1:
        if not payments:
            st.info("No payments recorded yet.")
        else:
            search_p = st.text_input("🔍 Search by guest name", placeholder="Type name...")
            filtered_p = [p for p in payments if not search_p or search_p.lower() in p.get("guest","").lower()]

            # Headers
            h1,h2,h3,h4,h5,h6,h7,h8 = st.columns([2,1,1.5,1.5,1.5,1.5,1,1])
            h1.markdown("**Guest**")
            h2.markdown("**Room**")
            h3.markdown("**Amount**")
            h4.markdown("**Method**")
            h5.markdown("**Type**")
            h6.markdown("**Date**")
            h7.markdown("**Edit**")
            h8.markdown("**Del**")
            st.markdown("<hr style='margin:2px 0 6px;border-color:#d8b4fe'>", unsafe_allow_html=True)

            for p in reversed(filtered_p):
                type_color = {"advance":"🔵","final":"🟢","partial":"🟡","refund":"🔴","crm_note":"📌"}.get(p.get("type",""), "⚪")
                amount_str = f"- {fmt(p['amount'])}" if p.get("type") == "refund" else fmt(p.get("amount",0))

                c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([2,1,1.5,1.5,1.5,1.5,1,1])
                c1.write(f"**{p.get('guest','')}**")
                c2.write(p.get("room","—"))
                c3.write(amount_str)
                c4.write(p.get("method","—"))
                c5.write(f"{type_color} {p.get('type','—').title()}")
                c6.write(p.get("date","—"))
                if p.get("note"):
                    st.caption(f"   📝 {p['note']}")

                with c7:
                    if st.button("✏️", key=f"edit_p_{p['id']}", help="Edit"):
                        st.session_state["edit_payment"] = p["id"]
                        st.rerun()
                with c8:
                    if st.button("🗑️", key=f"del_p_{p['id']}", help="Delete"):
                        require_online()
                        DB.delete_payment(p["id"])
                        invalidate_cache()
                        st.success("Payment deleted!")
                        st.rerun()

                # Inline edit form
                if st.session_state.get("edit_payment") == p["id"]:
                    with st.form(f"edit_pay_{p['id']}"):
                        st.markdown(f"**✏️ Editing Payment — {p.get('guest','')}**")
                        ep1, ep2 = st.columns(2)
                        new_amt    = ep1.number_input("Amount (₹)", min_value=0,
                                                       value=int(p.get("amount",0)), step=100)
                        new_method = ep2.selectbox("Method",
                                                    ["Cash","UPI","Bank Transfer","Card","Online"],
                                                    index=["Cash","UPI","Bank Transfer","Card","Online"].index(
                                                        p.get("method","Cash")) if p.get("method","Cash") in
                                                        ["Cash","UPI","Bank Transfer","Card","Online"] else 0)
                        ep3, ep4 = st.columns(2)
                        type_opts  = ["advance","partial","final","refund"]
                        new_type   = ep3.selectbox("Type", type_opts,
                                                    index=type_opts.index(p.get("type","partial"))
                                                    if p.get("type") in type_opts else 0)
                        new_date   = ep4.date_input("Date",
                                                     value=datetime.strptime(str(p["date"]), "%Y-%m-%d").date()
                                                     if p.get("date") else date.today())
                        new_note   = st.text_input("Note", value=p.get("note",""))
                        sv, cn     = st.columns(2)
                        do_save    = sv.form_submit_button("💾 Save", use_container_width=True)
                        do_cancel  = cn.form_submit_button("✖ Cancel", use_container_width=True)
                        if do_save:
                            require_online()
                            DB.update_payment(p["id"], {
                                "amount": new_amt, "method": new_method,
                                "type": new_type, "date": str(new_date),
                                "note": new_note,
                            })
                            st.session_state.pop("edit_payment", None)
                            invalidate_cache()
                            st.success("✅ Payment updated!")
                            st.rerun()
                        if do_cancel:
                            st.session_state.pop("edit_payment", None)
                            st.rerun()

                st.markdown("<hr style='margin:2px 0;border-color:#f0e6ff'>", unsafe_allow_html=True)

    with tab2:
        st.subheader("Add Payment")
        # Build booking options from bills
        bill_opts = [f"{b['guest']} — Room {b['room']} | Bill {b['bill_id']} | Due: {fmt(b.get('total',0))}"
                     for b in bills]
        if not bill_opts:
            st.info("No bills generated yet. Generate a bill first.")
        else:
            with st.form("add_payment_form"):
                sel_bill = st.selectbox("Select Bill", bill_opts)
                bill_obj = bills[bill_opts.index(sel_bill)]

                already_paid = sum(p["amount"] for p in payments
                                   if p.get("bill_id") == bill_obj.get("bill_id") and p.get("type") != "refund")
                balance_due  = max(0, bill_obj.get("total", 0) - already_paid)

                st.markdown(f"**Bill Total:** {fmt(bill_obj.get('total',0))} &nbsp;|&nbsp; "
                            f"**Already Paid:** {fmt(already_paid)} &nbsp;|&nbsp; "
                            f"**Balance Due:** {fmt(balance_due)}")

                pa1, pa2 = st.columns(2)
                pay_amount = pa1.number_input("Payment Amount (₹)", min_value=0,
                                              value=int(balance_due), step=100)
                pay_method = pa2.selectbox("Payment Method",
                                           ["Cash","UPI","Bank Transfer","Card","Online"])
                pa3, pa4 = st.columns(2)
                pay_type = pa3.selectbox("Payment Type",
                                         ["final","partial","advance"])
                pay_date = pa4.date_input("Date", value=date.today())
                pay_note = st.text_input("Note (optional)", placeholder="e.g. Final settlement")
                submitted = st.form_submit_button("💳 Record Payment", use_container_width=True)
                if submitted:
                    if pay_amount <= 0:
                        st.error("Enter a valid amount.")
                    else:
                        new_pay_id = len(st.session_state.payments) + 1
                        DB.add_payment({
                            "bill_id":    bill_obj.get("bill_id"),
                            "guest":      bill_obj["guest"],
                            "room":       bill_obj["room"],
                            "amount":     pay_amount,
                            "method":     pay_method,
                            "type":       pay_type,
                            "date":       str(pay_date),
                            "note":       pay_note,
                        })
                        new_total_paid = already_paid + pay_amount
                        if new_total_paid >= bill_obj.get("total", 0):
                            DB.update_bill(bill_obj["bill_id"], {"status": "Paid"})
                        st.success(f"✅ Payment of {fmt(pay_amount)} recorded via {pay_method}!")
                        st.rerun()

    with tab3:
        if not can("add_refund"):
            lock("add_refund")
        else:
         st.subheader("Issue Refund")
        guest_bookings = [b for b in bookings if b.get("status") != "checked-out"]
        if not guest_bookings:
            st.info("No active bookings to refund.")
        else:
            with st.form("refund_form"):
                ref_opts = [f"{b['guest']} — Room {b['room']} | {b['checkin']} → {b['checkout']}"
                            for b in guest_bookings]
                sel_ref  = st.selectbox("Select Booking", ref_opts)
                bk_obj   = guest_bookings[ref_opts.index(sel_ref)]

                paid_so_far = sum(p["amount"] for p in payments
                                  if p.get("guest") == bk_obj["guest"] and
                                  p.get("room")  == bk_obj.get("room","") and
                                  p.get("type")  != "refund")
                st.markdown(f"**Total Paid So Far:** {fmt(paid_so_far)}")

                rf1, rf2 = st.columns(2)
                ref_amount = rf1.number_input("Refund Amount (₹)", min_value=0,
                                              value=int(paid_so_far), step=100)
                ref_method = rf2.selectbox("Refund Via",
                                           ["Cash","UPI","Bank Transfer","Card","Online"])
                rf3, rf4 = st.columns(2)
                ref_date   = rf3.date_input("Refund Date", value=date.today())
                ref_reason = rf4.text_input("Reason", placeholder="e.g. Cancellation")
                submitted  = st.form_submit_button("💸 Issue Refund", use_container_width=True)
                if submitted:
                    if ref_amount <= 0:
                        st.error("Enter a valid amount.")
                    elif ref_amount > paid_so_far:
                        st.error(f"Refund cannot exceed amount paid ({fmt(paid_so_far)}).")
                    else:
                        require_online()
                        DB.add_payment({
                            "booking_id": bk_obj.get("id"),
                            "bill_id":    None,
                            "guest":      bk_obj["guest"],
                            "room":       bk_obj.get("room",""),
                            "amount":     ref_amount,
                            "method":     ref_method,
                            "type":       "refund",
                            "date":       str(ref_date),
                            "note":       ref_reason,
                        })
                        invalidate_cache()
                        st.success(f"✅ Refund of {fmt(ref_amount)} issued to {bk_obj['guest']}!")
                        st.rerun()

# PAGE: REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Reports":
    st.title("📈 Reports & Analytics")

    bills    = st.session_state.bills
    expenses = st.session_state.expenses
    bookings = st.session_state.bookings
    rooms    = st.session_state.rooms

    total_rev = sum(b["room_charge"] + b.get("food", 0) + b.get("laundry", 0) +
                    b.get("extra_bed", 0) + b.get("electricity", 0) +
                    b.get("bonfire", 0) + b.get("other", 0) for b in bills)
    total_exp = sum(e["amount"] for e in expenses)
    net       = total_rev - total_exp

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Revenue",  fmt(total_rev))
    c2.metric("💸 Total Expenses", fmt(total_exp))
    c3.metric("📈 Net Profit",     fmt(net), delta=fmt(net))

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Occupancy by Room Type")
        type_data = {}
        for r in rooms:
            t = r["type"]
            if t not in type_data:
                type_data[t] = {"total": 0, "occupied": 0}
            type_data[t]["total"] += 1
            if r["status"] == "occupied":
                type_data[t]["occupied"] += 1
        occ_df = pd.DataFrame([
            {"Room Type": t, "Total": d["total"], "Occupied": d["occupied"],
             "Occupancy %": round(d["occupied"] / d["total"] * 100) if d["total"] else 0}
            for t, d in type_data.items()
        ])
        if not occ_df.empty:
            st.bar_chart(occ_df.set_index("Room Type")["Occupancy %"])
            st.dataframe(occ_df, hide_index=True, use_container_width=True)

    with col2:
        st.subheader("Expense Breakdown")
        cats = {}
        for e in expenses:
            cats[e["category"]] = cats.get(e["category"], 0) + e["amount"]
        if cats:
            exp_df = pd.DataFrame(list(cats.items()), columns=["Category", "Amount"])
            st.bar_chart(exp_df.set_index("Category"))
            st.dataframe(exp_df, hide_index=True, use_container_width=True)
        else:
            st.info("No expenses yet.")

    st.markdown("---")
    st.subheader("Booking Summary")
    if bookings:
        rows = []
        for b in bookings:
            r      = get_room(b["room"])
            n      = nights(b["checkin"], b["checkout"])
            rc     = int(b.get("room_price", 0)) * n
            eb     = (r["extra_price"] * n if r else 0) if b.get("extra_bed") else 0
            bill   = next((bl for bl in bills if bl["guest"] == b["guest"] and bl["room"] == b["room"]), None)
            extras = (bill.get("food", 0) + bill.get("laundry", 0) + bill.get("electricity", 0) +
                      bill.get("bonfire", 0) + bill.get("other", 0)) if bill else 0
            rows.append({
                "Guest": b["guest"], "Room": b["room"], "Nights": n,
                "Season": b.get("season", "—"), "Room Charge": rc,
                "Extra Bed": eb, "Food+Laundry+Elec+Bonfire": extras,
                "Total": rc + eb + extras, "Status": b["status"]
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown(f"**Grand Total Revenue from Bookings: {fmt(df['Total'].sum())}**")
    else:
        st.info("No bookings yet.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: CALENDAR
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Calendar":
    import calendar as cal_mod
    st.title("📅 Booking Calendar")

    bookings = st.session_state.bookings
    rooms    = st.session_state.rooms

    # ── Month / Year navigation ───────────────────────────────────────────────
    if "cal_year"  not in st.session_state: st.session_state.cal_year  = date.today().year
    if "cal_month" not in st.session_state: st.session_state.cal_month = date.today().month

    col_prev, col_title, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀ Prev"):
            if st.session_state.cal_month == 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            else:
                st.session_state.cal_month -= 1
            st.rerun()
    with col_next:
        if st.button("Next ▶"):
            if st.session_state.cal_month == 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.rerun()

    yr = st.session_state.cal_year
    mo = st.session_state.cal_month
    with col_title:
        st.markdown(
            f"<h3 style='text-align:center;color:#3b1f6e;margin:0'>"
            f"{date(yr, mo, 1).strftime('%B %Y')}</h3>",
            unsafe_allow_html=True
        )

    STATUS_COLOR = {"checked-in": "#bbf7d0", "confirmed": "#bfdbfe", "checked-out": "#e5e7eb"}
    STATUS_ICON  = {"checked-in": "🟢", "confirmed": "🔵", "checked-out": "⚫"}

    def booking_active(b, check_date):
        try:
            cin  = datetime.strptime(b["checkin"],  "%Y-%m-%d").date()
            cout = datetime.strptime(b["checkout"], "%Y-%m-%d").date()
            return cin <= check_date < cout
        except:
            return False

    today   = date.today()
    cal_grid = cal_mod.monthcalendar(yr, mo)

    # ── Day-of-week headers ───────────────────────────────────────────────────
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hcols = st.columns(7)
    for i, dn in enumerate(day_names):
        hcols[i].markdown(
            f"<div style='text-align:center;font-weight:600;color:#7c3aed;"
            f"padding:6px 0;border-bottom:2px solid #d8b4fe'>{dn}</div>",
            unsafe_allow_html=True
        )

    # ── Calendar grid ─────────────────────────────────────────────────────────
    for week in cal_grid:
        wcols = st.columns(7)
        for ci, day in enumerate(week):
            with wcols[ci]:
                if day == 0:
                    st.markdown("<div style='min-height:95px'></div>", unsafe_allow_html=True)
                    continue
                d       = date(yr, mo, day)
                active  = [b for b in bookings if booking_active(b, d)]
                is_today = (d == today)

                num_style = (
                    "background:#7c3aed;color:white;border-radius:50%;"
                    "width:26px;height:26px;display:inline-flex;align-items:center;"
                    "justify-content:center;font-weight:700;font-size:13px"
                    if is_today else
                    "font-weight:600;font-size:13px;color:#3b1f6e"
                )
                cell_bg = "#f5f0ff" if active else "#ffffff"
                bookings_html = ""
                for b in active[:3]:
                    color = STATUS_COLOR.get(b["status"], "#e9d5ff")
                    icon  = STATUS_ICON.get(b["status"], "⚪")
                    name  = b["guest"].split()[0]
                    bookings_html += (
                        f"<div style='background:{color};border-radius:4px;"
                        f"padding:2px 5px;margin-top:3px;font-size:11px;"
                        f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>"
                        f"{icon} {name} · {b['room']}</div>"
                    )
                if len(active) > 3:
                    bookings_html += f"<div style='font-size:10px;color:#7c3aed;margin-top:2px'>+{len(active)-3} more</div>"

                st.markdown(f"""
                <div style='border:1px solid #e9d5ff;border-radius:8px;padding:6px 7px;
                            min-height:95px;background:{cell_bg}'>
                    <span style='{num_style}'>{day}</span>
                    {bookings_html}
                </div>""", unsafe_allow_html=True)

    # ── Room timeline ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🛏️ Room Availability Timeline")

    days_in_month = cal_mod.monthrange(yr, mo)[1]
    all_days      = [date(yr, mo, d) for d in range(1, days_in_month + 1)]

    if rooms:
        header_cells = "".join(
            f"<th style='font-size:11px;padding:3px 2px;text-align:center;"
            f"color:{'#7c3aed' if d==today else '#666'};"
            f"font-weight:{'700' if d==today else '400'}'>{d.day}</th>"
            for d in all_days
        )
        rows_html = ""
        for r in rooms:
            cells = ""
            for d in all_days:
                b = next((bk for bk in bookings if bk["room"]==r["num"] and booking_active(bk, d)), None)
                if b:
                    color = STATUS_COLOR.get(b["status"], "#e9d5ff")
                    tip   = f"{b['guest']} ({b['status']})"
                    cells += f"<td title='{tip}' style='background:{color};border:1px solid #fff;min-width:24px;height:28px'></td>"
                else:
                    bg = "#fdf4ff" if d==today else "#f9fafb"
                    cells += f"<td style='background:{bg};border:1px solid #ede9fe;min-width:24px;height:28px'></td>"

            label = (
                f"<td style='padding:4px 10px;font-size:12px;font-weight:600;"
                f"color:#3b1f6e;white-space:nowrap;background:#f3eeff;"
                f"border:1px solid #e9d5ff;min-width:70px'>"
                f"Room {r['num']}<br>"
                f"<span style='font-weight:400;color:#7c5cbf;font-size:10px'>{r['type']}</span></td>"
            )
            rows_html += f"<tr>{label}{cells}</tr>"

        st.markdown(f"""
        <div style='overflow-x:auto;margin-top:8px'>
        <table style='border-collapse:collapse;font-family:sans-serif'>
            <thead>
                <tr>
                    <th style='padding:4px 10px;background:#3b1f6e;color:white;
                               font-size:12px;text-align:left;min-width:70px'>Room</th>
                    {header_cells}
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        </div>
        <div style='margin-top:10px;font-size:12px;display:flex;gap:14px;flex-wrap:wrap'>
            <span style='background:#bbf7d0;padding:2px 10px;border-radius:4px'>🟢 Checked-in</span>
            <span style='background:#bfdbfe;padding:2px 10px;border-radius:4px'>🔵 Confirmed</span>
            <span style='background:#e5e7eb;padding:2px 10px;border-radius:4px'>⚫ Checked-out</span>
            <span style='background:#f9fafb;border:1px solid #ede9fe;padding:2px 10px;border-radius:4px'>⬜ Available</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No rooms added yet.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: GUESTS CRM
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Guests (CRM)":
    st.title("👥 Guest CRM")

    bookings = st.session_state.bookings
    bills    = st.session_state.bills
    payments = st.session_state.payments

    # ── Build guest profiles from bookings ────────────────────────────────────
    guest_map = {}
    for b in bookings:
        name = b["guest"].strip()
        if name not in guest_map:
            guest_map[name] = {
                "name":          name,
                "phone":         b.get("phone", ""),
                "bookings":      [],
                "total_nights":  0,
                "total_spend":   0,
                "rooms_stayed":  set(),
                "agents":        set(),
                "meal_plans":    set(),
                "last_stay":     "",
                "first_stay":    "",
                "notes_all":     [],
            }
        g = guest_map[name]
        g["bookings"].append(b)
        n = nights(b["checkin"], b["checkout"])
        g["total_nights"] += n

        # Collect rooms
        rlist = b.get("rooms", [b.get("room", "")])
        if not isinstance(rlist, list): rlist = [rlist]
        for rn in rlist:
            g["rooms_stayed"].add(rn)

        # Agent
        if b.get("agent"):
            g["agents"].add(b["agent"])

        # Meal plan
        mp = b.get("meal_plan", "")
        if mp and mp != "No Meals (Room Only)":
            g["meal_plans"].add(mp.split("(")[0].strip())

        # Notes
        if b.get("notes"):
            g["notes_all"].append(b["notes"])

        # Dates
        if not g["first_stay"] or b["checkin"] < g["first_stay"]:
            g["first_stay"] = b["checkin"]
        if not g["last_stay"] or b["checkout"] > g["last_stay"]:
            g["last_stay"] = b["checkout"]

        # Spend from bills
        bill = next((bl for bl in bills if bl["guest"] == name and bl["room"] == b.get("room","")), None)
        if bill:
            g["total_spend"] += bill.get("total", bill.get("gross", 0))

    # Convert sets to lists for display
    for g in guest_map.values():
        g["rooms_stayed"] = sorted(g["rooms_stayed"])
        g["agents"]       = list(g["agents"])
        g["meal_plans"]   = list(g["meal_plans"])

    guests = list(guest_map.values())

    # ── Guest tier classification ─────────────────────────────────────────────
    def guest_tier(g):
        visits = len(g["bookings"])
        if visits >= 5:   return "🥇 VIP",     "#fef3c7", "#92400e"
        elif visits >= 3: return "🥈 Regular",  "#ede9fe", "#5b21b6"
        elif visits >= 2: return "🥉 Returning", "#dbeafe", "#1e40af"
        else:             return "🆕 New",       "#f0fdf4", "#166534"

    # ── Summary metrics ───────────────────────────────────────────────────────
    total_guests  = len(guests)
    repeat_guests = sum(1 for g in guests if len(g["bookings"]) > 1)
    vip_guests    = sum(1 for g in guests if len(g["bookings"]) >= 5)
    avg_nights    = round(sum(g["total_nights"] for g in guests) / max(total_guests, 1), 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Total Guests",    total_guests)
    c2.metric("🔄 Repeat Guests",   repeat_guests)
    c3.metric("🥇 VIP Guests",      vip_guests)
    c4.metric("🌙 Avg Nights/Stay", avg_nights)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["👥 Guest Profiles", "➕ Add Guest Note", "📊 Guest Analytics"])

    # ── TAB 1: Guest Profiles ─────────────────────────────────────────────────
    with tab1:
        col_s, col_f = st.columns([2, 1])
        search_g  = col_s.text_input("🔍 Search guest", placeholder="Type name or phone...")
        tier_filter = col_f.selectbox("Filter by tier", ["All", "🥇 VIP", "🥈 Regular", "🥉 Returning", "🆕 New"])

        filtered_g = [g for g in guests
                      if (not search_g or
                          search_g.lower() in g["name"].lower() or
                          search_g in g.get("phone",""))
                      and (tier_filter == "All" or guest_tier(g)[0] == tier_filter)]

        # Sort by number of visits desc
        filtered_g.sort(key=lambda g: len(g["bookings"]), reverse=True)

        if not filtered_g:
            st.info("No guests found.")
        else:
            for g in filtered_g:
                tier_label, tier_bg, tier_text = guest_tier(g)
                visits = len(g["bookings"])
                with st.expander(
                    f"{tier_label} **{g['name']}**  |  "
                    f"{visits} stay{'s' if visits>1 else ''}  |  "
                    f"{g['total_nights']} nights  |  "
                    f"Last: {g['last_stay'][:10] if g['last_stay'] else '—'}"
                ):
                    col1, col2, col3 = st.columns(3)

                    # ── Contact & identity ────────────────────────────────────
                    col1.markdown("**📞 Contact**")
                    col1.write(f"Phone: {g['phone'] or '—'}")
                    col1.markdown(f"<span style='background:{tier_bg};color:{tier_text};"
                                  f"padding:3px 10px;border-radius:12px;font-size:12px;"
                                  f"font-weight:600'>{tier_label}</span>",
                                  unsafe_allow_html=True)
                    col1.markdown("**📅 Stay History**")
                    col1.write(f"First stay: {g['first_stay'][:10] if g['first_stay'] else '—'}")
                    col1.write(f"Last stay:  {g['last_stay'][:10]  if g['last_stay']  else '—'}")
                    col1.write(f"Total stays: {visits}")
                    col1.write(f"Total nights: {g['total_nights']}")

                    # ── Preferences ───────────────────────────────────────────
                    col2.markdown("**🛏️ Room Preferences**")
                    col2.write(f"Rooms stayed: {', '.join(g['rooms_stayed']) or '—'}")
                    col2.markdown("**🍽️ Meal Preferences**")
                    col2.write(', '.join(g['meal_plans']) if g['meal_plans'] else 'No preference recorded')
                    col2.markdown("**🏢 Travel Agents**")
                    col2.write(', '.join(g['agents']) if g['agents'] else 'Direct booking')

                    # ── Spend & notes ─────────────────────────────────────────
                    col3.markdown("**💰 Spend**")
                    col3.write(f"Total spend: {fmt(g['total_spend']) if g['total_spend'] else '—'}")
                    if g["total_nights"] and g["total_spend"]:
                        col3.write(f"Avg per night: {fmt(g['total_spend'] // g['total_nights'])}")

                    # All past notes
                    if g["notes_all"]:
                        col3.markdown("**📝 Past Notes**")
                        for note in g["notes_all"]:
                            col3.caption(f"• {note}")

                    # CRM notes stored separately
                    crm_notes = [p for p in payments
                                 if p.get("type") == "crm_note" and p.get("guest") == g["name"]]
                    if crm_notes:
                        col3.markdown("**🗒️ CRM Notes**")
                        for cn in crm_notes:
                            col3.info(f"📌 {cn.get('note','')}  \n*{cn.get('date','')}*")

                    # ── Booking history table ─────────────────────────────────
                    st.markdown("**📋 All Bookings**")
                    hist_rows = []
                    for bk in sorted(g["bookings"], key=lambda x: x["checkin"], reverse=True):
                        n_nights = nights(bk["checkin"], bk["checkout"])
                        hist_rows.append({
                            "Check-in":  bk["checkin"],
                            "Check-out": bk["checkout"],
                            "Nights":    n_nights,
                            "Room(s)":   bk.get("room","—"),
                            "Agent":     bk.get("agent","Direct") or "Direct",
                            "Meal":      bk.get("meal_plan","—").split("(")[0].strip(),
                            "Status":    bk["status"],
                        })
                    st.dataframe(pd.DataFrame(hist_rows),
                                 use_container_width=True, hide_index=True)

                    # ── Upsell suggestions ────────────────────────────────────
                    suggestions = []
                    if not g["meal_plans"]:
                        suggestions.append("🍽️ Offer a meal plan — guest has never opted for one")
                    if len(g["bookings"]) == 1:
                        suggestions.append("🎁 Send a loyalty discount for second stay")
                    if len(g["bookings"]) >= 3:
                        suggestions.append("🥇 Upgrade to VIP — offer room upgrade or bonfire complimentary")
                    if g["total_nights"] > 10:
                        suggestions.append("💌 Send a thank-you message — long-stay loyal guest")

                    if suggestions:
                        st.markdown("**💡 Upsell & Loyalty Suggestions**")
                        for s in suggestions:
                            st.success(s)

    # ── TAB 2: Add CRM Note ───────────────────────────────────────────────────
    with tab2:
        st.subheader("Add Note to Guest Profile")
        st.caption("Use this to record preferences, complaints, special requests, or VIP notes.")

        if not guests:
            st.info("No guests yet.")
        else:
            with st.form("crm_note_form"):
                guest_names = sorted([g["name"] for g in guests])
                sel_guest   = st.selectbox("Select Guest", guest_names)
                note_text   = st.text_area("Note", placeholder="e.g. Prefers room 103, allergic to peanuts, celebrating anniversary...", height=100)
                note_tag    = st.selectbox("Tag", ["General", "Preference", "Complaint", "VIP Request", "Anniversary/Birthday", "Other"])
                submitted   = st.form_submit_button("📌 Save Note", use_container_width=True)
                if submitted:
                    if not note_text.strip():
                        st.error("Enter a note.")
                    else:
                        DB.add_payment({
                            "type":   "crm_note",
                            "guest":  sel_guest,
                            "note":   f"[{note_tag}] {note_text.strip()}",
                            "date":   str(date.today()),
                            "amount": 0,
                        })
                        st.success(f"✅ Note saved for {sel_guest}!")
                        st.rerun()

    # ── TAB 3: Analytics ──────────────────────────────────────────────────────
    with tab3:
        st.subheader("Guest Analytics")

        if not guests:
            st.info("No guest data yet.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🏆 Top Guests by Nights Stayed**")
                top_df = pd.DataFrame([
                    {"Guest": g["name"], "Stays": len(g["bookings"]),
                     "Total Nights": g["total_nights"],
                     "Total Spend": g["total_spend"]}
                    for g in sorted(guests, key=lambda x: x["total_nights"], reverse=True)[:10]
                ])
                st.dataframe(top_df, use_container_width=True, hide_index=True)

            with col2:
                st.markdown("**📊 Guest Tier Breakdown**")
                tier_counts = {"🥇 VIP": 0, "🥈 Regular": 0, "🥉 Returning": 0, "🆕 New": 0}
                for g in guests:
                    t = guest_tier(g)[0]
                    tier_counts[t] = tier_counts.get(t, 0) + 1
                tier_df = pd.DataFrame(list(tier_counts.items()), columns=["Tier", "Count"])
                st.bar_chart(tier_df.set_index("Tier"))

            st.markdown("---")
            st.markdown("**🔄 Repeat Guest Rate**")
            repeat_rate = round(repeat_guests / max(total_guests, 1) * 100, 1)
            st.markdown(f"""
            <div style='background:#f3eeff;border-radius:10px;padding:16px;border-left:4px solid #7c3aed'>
                <div style='font-size:28px;font-weight:700;color:#3b1f6e'>{repeat_rate}%</div>
                <div style='font-size:13px;color:#7c5cbf'>of guests have stayed more than once</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("**📅 Booking Source Breakdown**")
            agent_counts = {}
            for b in bookings:
                agent = b.get("agent", "") or "Direct"
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
            if agent_counts:
                agent_df = pd.DataFrame(list(agent_counts.items()), columns=["Source", "Bookings"])
                agent_df = agent_df.sort_values("Bookings", ascending=False)
                st.bar_chart(agent_df.set_index("Source"))
                st.dataframe(agent_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Notifications":
    st.title("🔔 Notifications")

    if DB.MODE == "offline":
        st.warning("Notifications require an internet connection.")
        st.stop()

    # ── Action buttons ────────────────────────────────────────────────────────
    col_a, col_b, col_c, _ = st.columns([1.5, 1.5, 1.5, 4])
    if col_a.button("🔄 Generate Alerts", use_container_width=True):
        DB.generate_smart_alerts()
        st.success("✅ Alerts generated!")
        st.rerun()
    if col_b.button("✅ Mark All Read", use_container_width=True):
        DB.mark_all_read()
        st.rerun()
    if col_c.button("🗑️ Clear All", use_container_width=True):
        DB.clear_all_notifications()
        st.success("All notifications cleared.")
        st.rerun()

    st.markdown("---")

    # ── Smart summary banner ──────────────────────────────────────────────────
    notifs = DB.get_notifications(limit=100)
    unread = [n for n in notifs if not n.get("is_read")]
    critical = [n for n in notifs if n.get("type") == "critical" and not n.get("is_read")]
    warnings = [n for n in notifs if n.get("type") == "warning" and not n.get("is_read")]

    if critical or warnings:
        sm1, sm2, sm3 = st.columns(3)
        sm1.metric("🔴 Critical", len(critical))
        sm2.metric("🟡 Warnings", len(warnings))
        sm3.metric("🔔 Total Unread", len(unread))
        st.markdown("---")

    if not notifs:
        st.info("🎉 No notifications yet. Click 'Generate Alerts' to check today's status.")
    else:
        # ── Color & icon mapping ──────────────────────────────────────────────
        TYPE_STYLE = {
            "critical": ("#fee2e2", "#991b1b", "🔴"),
            "warning":  ("#fef3c7", "#92400e", "🟡"),
            "info":     ("#eff6ff", "#1e40af", "🔵"),
        }
        CAT_ICON = {
            "checkin":      "🛎️",
            "checkout":     "🚪",
            "payment":      "💳",
            "booking":      "📋",
            "housekeeping": "🧹",
            "general":      "📌",
        }

        # Unread first, then read
        sorted_notifs = sorted(notifs, key=lambda n: (n.get("is_read", False), n.get("created_at","").__class__.__name__))
        unread_notifs = [n for n in notifs if not n.get("is_read")]
        read_notifs   = [n for n in notifs if n.get("is_read")]

        def render_notif(n):
            bg, tc, icon = TYPE_STYLE.get(n.get("type","info"), TYPE_STYLE["info"])
            cat_icon = CAT_ICON.get(n.get("category","general"), "📌")
            read_opacity = "opacity:0.55;" if n.get("is_read") else ""
            ts = str(n.get("created_at",""))[:16]

            nc1, nc2 = st.columns([9, 1])
            with nc1:
                st.markdown(f"""
                <div style='background:{bg};border-left:4px solid {tc};border-radius:8px;
                            padding:10px 14px;margin-bottom:6px;{read_opacity}'>
                    <div style='font-size:14px;font-weight:{"600" if not n.get("is_read") else "400"};
                                color:{tc}'>
                        {cat_icon} {n.get("message","")}
                    </div>
                    <div style='font-size:11px;color:#888;margin-top:4px'>
                        {icon} {n.get("type","info").title()} &nbsp;|&nbsp; 🕐 {ts}
                        {"" if n.get("is_read") else " &nbsp;|&nbsp; <b>● Unread</b>"}
                    </div>
                </div>""", unsafe_allow_html=True)
            with nc2:
                if not n.get("is_read"):
                    if st.button("✓", key=f"read_{n['id']}", help="Mark read"):
                        DB.mark_notification_read(n["id"])
                        st.rerun()
                if st.button("✕", key=f"del_{n['id']}", help="Delete"):
                    DB.delete_notification(n["id"])
                    st.rerun()

        if unread_notifs:
            st.markdown(f"### 🔔 Unread ({len(unread_notifs)})")
            for n in unread_notifs:
                render_notif(n)

        if read_notifs:
            st.markdown(f"### ✅ Read ({len(read_notifs)})")
            for n in read_notifs[:20]:
                render_notif(n)
