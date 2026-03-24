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
    if role == "admin":
        return ["📊 Dashboard","🛏️ Rooms","📋 Bookings","📅 Calendar",
                "₹  Billing","💳 Payments","🧾 Expenses","📈 Reports","👥 Guests (CRM)"]
    return PERMISSIONS.get(role, {}).get("pages", ["📊 Dashboard"])

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
def load_all():
    """Load all data fresh from database into session state."""
    st.session_state.rooms    = DB.get_rooms()
    st.session_state.bookings = DB.get_bookings()
    st.session_state.bills    = DB.get_bills()
    st.session_state.expenses = DB.get_expenses()
    st.session_state.payments = DB.get_payments()

def persist():
    pass  # Data is written directly to DB — kept for compatibility

load_all()

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
    """Returns (status, booking) for a room on a given date based on bookings."""
    for b in st.session_state.bookings:
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
    return "available", None

def check_overbooking(room_num, checkin_str, checkout_str, exclude_booking_id=None):
    """Returns list of conflicting bookings for a room+daterange."""
    try:
        cin  = datetime.strptime(checkin_str,  "%Y-%m-%d").date()
        cout = datetime.strptime(checkout_str, "%Y-%m-%d").date()
    except:
        return []
    conflicts = []
    for b in st.session_state.bookings:
        if b.get("status") == "checked-out":
            continue
        if exclude_booking_id and b.get("id") == exclude_booking_id:
            continue
        rooms_list = b.get("rooms", [b.get("room", "")])
        if not isinstance(rooms_list, list):
            rooms_list = [rooms_list]
        if room_num not in rooms_list:
            continue
        try:
            bcin  = datetime.strptime(b["checkin"],  "%Y-%m-%d").date()
            bcout = datetime.strptime(b["checkout"], "%Y-%m-%d").date()
            if dates_overlap(cin, cout, bcin, bcout):
                conflicts.append(b)
        except:
            pass
    return conflicts

def sync_room_statuses():
    """Auto-update room statuses based on today's bookings."""
    today = date.today()
    for r in st.session_state.rooms:
        if r.get("status") == "cleaning":
            continue
        status, _ = get_room_status_on_date(r["num"], today)
        if r.get("status") != status:
            DB.update_room(r["num"], {"status": status})

# ── Auto-sync room statuses on every page load ───────────────────────────────
sync_room_statuses()

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
    if st.session_state.get("db_mode") == "online":
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
    st.caption(f"📅 {date.today().strftime('%d %b %Y, %A')}")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ["logged_in", "username", "user_name", "user_role"]:
            st.session_state.pop(key, None)
        st.rerun()

# ── Offline warning banner ────────────────────────────────────────────────────
if st.session_state.get("db_mode") == "offline":
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
    if st.session_state.get("db_mode") == "offline":
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
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Room Status")

        # ── Date picker ───────────────────────────────────────────────────────
        selected_date = st.date_input(
            "📅 Select a date to check room status",
            value=date.today(),
            help="Pick any date to see which rooms are occupied or available on that day"
        )

        today_date = date.today()
        is_today   = (selected_date == today_date)

        # Label above the room grid
        if is_today:
            st.markdown(
                "<div style='background:#f3eeff;border-left:4px solid #7c3aed;"
                "padding:8px 12px;border-radius:6px;font-size:13px;margin-bottom:10px'>"
                "🟣 <b>Today — Live Status</b></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='background:#e0f2fe;border-left:4px solid #0284c7;"
                f"padding:8px 12px;border-radius:6px;font-size:13px;margin-bottom:10px'>"
                f"📅 <b>Showing status for {selected_date.strftime('%d %B %Y')}</b></div>",
                unsafe_allow_html=True
            )

        # ── Helper: find booking status for a room on a given date ────────────
        def room_status_on_date(room_num, check_date):
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
                        return "occupied", b.get("guest", "Guest")
                except:
                    pass
            return None, None

        # ── Room grid ─────────────────────────────────────────────────────────
        cols = st.columns(3)
        for i, r in enumerate(rooms):
            if is_today:
                status = r["status"]
                _, g   = room_status_on_date(r["num"], selected_date)
                guest  = g or ""
            else:
                bk_status, guest = room_status_on_date(r["num"], selected_date)
                status = bk_status if bk_status else "available"
                guest  = guest or ""

            color = {"occupied":"#f8d7da","available":"#d4edda","cleaning":"#fff3cd"}.get(status,"#eee")
            icon  = {"occupied":"🔴","available":"🟢","cleaning":"🟡"}.get(status,"⚪")
            guest_line = (
                f"<div style='font-size:11px;color:#666;margin-top:3px;"
                f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{guest}</div>"
                if guest else ""
            )
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:{color};border-radius:8px;padding:10px;
                            text-align:center;margin-bottom:8px;
                            border:1px solid rgba(0,0,0,0.06)">
                  <div style="font-size:20px;font-weight:700;color:#1a1a1a">{r['num']}</div>
                  <div style="font-size:11px;color:#666">{r['type']} · {r['ac']}</div>
                  <div style="font-size:12px;margin-top:4px">{icon} {status}</div>
                  {guest_line}
                </div>""", unsafe_allow_html=True)

        # ── Summary bar ───────────────────────────────────────────────────────
        occ_d   = sum(1 for r in rooms if room_status_on_date(r["num"], selected_date)[0] == "occupied")
        avail_d = len(rooms) - occ_d
        st.markdown(
            f"<div style='background:#f3eeff;border-radius:8px;padding:10px 14px;"
            f"margin-top:6px;font-size:13px;display:flex;gap:16px'>"
            f"🔴 <b>{occ_d} Occupied</b> &nbsp;&nbsp; 🟢 <b>{avail_d} Available</b>"
            f"</div>", unsafe_allow_html=True
        )

    with col2:
        st.subheader("Recent Bookings")
        if bookings:
            df = pd.DataFrame(bookings)[["guest", "room", "checkin", "checkout", "status"]].tail(8)
            df.columns = ["Guest", "Room", "Check-in", "Check-out", "Status"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No bookings yet.")

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
                c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1.5, 1, 1.5, 1.5, 1.5, 2.5])
                c1.markdown(f"**{r['num']}**")
                c2.write(r["type"])
                c3.write(r["ac"])
                c4.write(fmt(r["price"]) + "/night")
                c5.write(f"Extra Bed: {'Yes +' + fmt(r['extra_price']) if r['extra_bed'] else 'No'}")
                c6.markdown(f"<span style='background:{color};padding:2px 10px;border-radius:12px;font-size:12px'>{r['status']}</span> {'🔥' if r.get('bonfire') else ''}", unsafe_allow_html=True)
                with c7:
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
                            st.rerun()
                    if can("edit_room") and sc2.button("✏️", key=f"edit_r_{r['num']}", help="Edit room"):
                        st.session_state["edit_room"] = r["num"]
                        st.rerun()
                    if can("delete_room") and sc3.button("🗑️", key=f"del_{r['num']}"):
                        require_online()
                        DB.delete_room(r["num"])
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
                        ec3, ec4 = st.columns(2)
                        new_price = ec3.number_input("Price/Night (Rs.)", min_value=0,
                                                     value=int(r["price"]), step=100)
                        new_stat2 = ec4.selectbox("Status", ["available","occupied","cleaning"],
                                                  index=["available","occupied","cleaning"].index(r.get("status","available")))
                        ec5, ec6 = st.columns(2)
                        new_eb    = ec5.checkbox("Extra Bed?", value=r.get("extra_bed", False))
                        new_ep    = ec6.number_input("Extra Bed Charge (Rs.)", min_value=0,
                                                     value=int(r.get("extra_price",0)), step=50)
                        ec7, ec8 = st.columns(2)
                        new_bf    = ec7.checkbox("🔥 Bonfire?", value=r.get("bonfire", False))
                        new_bfp   = ec8.number_input("Bonfire Charge (Rs.)", min_value=0,
                                                     value=int(r.get("bonfire_price",0)), step=50)
                        save_col, cancel_col = st.columns(2)
                        save_it   = save_col.form_submit_button("💾 Save Changes", use_container_width=True)
                        cancel_it = cancel_col.form_submit_button("✖ Cancel", use_container_width=True)
                        if save_it:
                            DB.update_room(r["num"], {
                                "type": new_type, "ac": new_ac,
                                "price": new_price, "status": new_stat2,
                                "extra_bed": new_eb,
                                "extra_price": new_ep if new_eb else 0,
                                "bonfire": new_bf,
                                "bonfire_price": new_bfp if new_bf else 0,
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
            c3, c4 = st.columns(2)
            price = c3.number_input("Price per Night (₹)", min_value=0, value=2500, step=100)
            ac    = c4.selectbox("AC / Non-AC", ["AC", "Non-AC"])
            c5, c6 = st.columns(2)
            extra_bed   = c5.checkbox("Extra Bed Available?")
            extra_price = c6.number_input("Extra Bed Charge (₹/night)", min_value=0, value=500, step=50)
            c7, c8 = st.columns(2)
            bonfire       = c7.checkbox("🔥 Bonfire Available?")
            bonfire_price = c8.number_input("Bonfire Charge (₹/session)", min_value=0, value=800, step=50)
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
                        "price": price, "extra_bed": extra_bed,
                        "extra_price": extra_price if extra_bed else 0,
                        "bonfire": bonfire,
                        "bonfire_price": bonfire_price if bonfire else 0,
                        "status": "available"
                    })
                    msg = f"✅ Room **{num}** added successfully! | {rtyp} | {ac} | {fmt(price)}/night"
                    if extra_bed: msg += f" | 🛏️ Extra Bed: {fmt(extra_price)}/night"
                    if bonfire:   msg += f" | 🔥 Bonfire: {fmt(bonfire_price)}/session"
                    st.success(msg)
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: BOOKINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Bookings":
    st.title("📋 Bookings")

    tab1, tab2, tab3 = st.tabs(["All Bookings", "➕ New Booking", "📤 Import from Excel"])

    with tab1:
        bookings = st.session_state.bookings
        col1, col2 = st.columns([2, 1])
        search        = col1.text_input("🔍 Search by guest name", placeholder="Type name...")
        status_filter = col2.selectbox("Filter by status", ["All", "checked-in", "confirmed", "checked-out"])

        filtered = [b for b in bookings
                    if (not search or search.lower() in b["guest"].lower())
                    and (status_filter == "All" or b["status"] == status_filter)]

        if not filtered:
            st.info("No bookings found.")
        else:
            # ── Column headers ──────────────────────────────────────────────
            h0,h1,h2,h3,h4,h5,h6,h7,h8 = st.columns([2.2,0.8,1.2,1.2,0.8,1.5,1,1.4,1.8])
            h0.markdown("**Guest**")
            h1.markdown("**Room**")
            h2.markdown("**Check-in**")
            h3.markdown("**Check-out**")
            h4.markdown("**Nights**")
            h5.markdown("**Agent**")
            h6.markdown("**Extras**")
            h7.markdown("**Total**")
            h8.markdown("**Action**")
            st.markdown("<hr style='margin:2px 0 6px 0; border-color:#d8b4fe'>", unsafe_allow_html=True)

            for b in reversed(filtered):
                n           = nights(b["checkin"], b["checkout"])
                r           = get_room(b["room"])
                room_charge = r["price"] * n if r else 0
                extra_bed   = (r["extra_price"] * n if r else 0) if b.get("extra_bed") else 0
                total       = room_charge + extra_bed
                status_icon = {"checked-in": "🟢", "confirmed": "🔵", "checked-out": "⚫"}.get(b["status"], "⚪")
                extras_str  = " ".join(filter(None, [
                    "🛏️" if b.get("extra_bed") else "",
                    "🔥" if b.get("bonfire") else "",
                ])) or "—"

                c0,c1,c2,c3,c4,c5,c6,c7,c8 = st.columns([2.2,0.8,1.2,1.2,0.8,1.5,1,1.4,1.8])
                c0.write(f"{status_icon} **{b['guest']}**")
                c1.write(b["room"])
                c2.write(b["checkin"])
                c3.write(b["checkout"])
                c4.write(str(n))
                c5.write(b.get("agent") or "—")
                c6.write(extras_str)
                c7.write(fmt(total))
                with c8:
                    a1, a2 = st.columns(2)
                    if b["status"] == "checked-in" and can("checkout_guest"):
                        if a1.button("✅ Out", key=f"co_{b['id']}", help="Checkout"):
                            require_online()
                            require_online()
                            DB.update_booking(b["id"], {"status": "checked-out"})
                            DB.update_room(b["room"].split(",")[0].strip(), {"status": "cleaning"})
                            st.rerun()
                    if can("delete_booking") and a2.button("🗑️", key=f"db_{b['id']}", help="Delete"):
                        require_online()
                        DB.delete_booking(b["id"])
                        st.rerun()

                # collapsible extra details
                with st.expander("📋 More details"):
                    d1, d2, d3 = st.columns(3)
                    d1.write(f"📞 **Phone:** {b['phone']}")
                    d1.write(f"🌄 **Season:** {b.get('season', '—')}")
                    d1.write(f"🏢 **Agent:** {b.get('agent') or '—'}")
                    d1.write(f"🍽️ **Meal Plan:** {b.get('meal_plan', 'No Meals')}")
                    eb_txt = f"Yes × {b.get('extra_bed_count', 1)} bed(s)" if b.get('extra_bed') else 'No'
                    d2.write(f"🛏️ **Extra Bed:** {eb_txt}")
                    d2.write(f"🔥 **Bonfire:** {'Yes' if b.get('bonfire') else 'No'}")
                    adv = b.get('advance_paid', 0)
                    d2.write(f"💳 **Advance:** {fmt(adv) + ' (' + b.get('advance_method','Cash') + ')' if adv else 'None'}")
                    rooms_list = b.get('rooms', [b.get('room','—')])
                    if isinstance(rooms_list, list) and len(rooms_list) > 1:
                        d3.write(f"🛏️ **All Rooms:** {', '.join(rooms_list)}")
                    d3.write(f"📝 **Notes:** {b.get('notes') or '—'}")
                    if st.button("✏️ Edit This Booking", key=f"edit_b_{b['id']}"):
                        st.session_state["edit_booking"] = b["id"]
                        st.rerun()

                # ── Inline edit form ──────────────────────────────────────────
                if st.session_state.get("edit_booking") == b["id"]:
                    with st.form(f"edit_booking_{b['id']}"):
                        st.markdown(f"**✏️ Editing Booking — {b['guest']}**")
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
                        do_save   = sv.form_submit_button("💾 Save Changes", use_container_width=True)
                        do_cancel = cn.form_submit_button("✖ Cancel",        use_container_width=True)
                        if do_save:
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
                            st.session_state.pop("edit_booking", None)
                            st.success(f"✅ Booking for {new_guest} updated!")
                            st.rerun()
                        if do_cancel:
                            st.session_state.pop("edit_booking", None)
                            st.rerun()

                st.markdown("<hr style='margin:4px 0; border-color:#f0e6ff'>", unsafe_allow_html=True)

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
                room_options = [f"{r['num']} – {r['type']} ({r['ac']}) {fmt(r['price'])}/night" for r in available_rooms]
                rooms_selected = st.multiselect("Select Room(s) *", room_options)

                st.markdown("---")
                st.markdown("**🛏️ Extra Bedding**")
                extra_bed       = st.checkbox("Extra Bed Required?")
                extra_bed_count = st.selectbox("Number of Extra Beds", ["0 (None)", "1", "2", "3", "4"])

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
                bonfire_requested = st.checkbox("🔥 Bonfire Requested?")
                if bonfire_requested:
                    st.caption("🔥 Bonfire charge will be added at billing time.")
                notes     = st.text_area("Notes / Special Requests", height=80)
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
                                "season": season, "bonfire": bonfire_requested,
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
                            sync_room_statuses()
                            msg = f"✅ Booking confirmed for **{guest}** — Room(s) {', '.join(rnums)} | {checkin} → {checkout}"
                            if extra_bed and extra_bed_count != "0 (None)": msg += f" | 🛏️ {extra_bed_count} Extra Bed(s)"
                            if bonfire_requested: msg += " | 🔥 Bonfire"
                            if meal_plan != "No Meals (Room Only)": msg += f" | 🍽️ {meal_plan.split('(')[0].strip()}"
                            if advance_paid > 0:  msg += f" | 💳 Advance: Rs.{advance_paid:,} ({advance_method})"
                            st.success(msg)
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
            # Multi-room: sum up all rooms
            rnums_bill   = b_data.get("rooms", [b_data.get("room","")]) if isinstance(b_data.get("rooms"), list) else [b_data.get("room","")]
            room_charge  = sum((get_room(rn)["price"] if get_room(rn) else 0) for rn in rnums_bill) * n
            eb_count     = int(b_data.get("extra_bed_count", 1)) if b_data.get("extra_bed") else 0
            extra_charge = (r_data["extra_price"] * eb_count * n if r_data else 0) if b_data.get("extra_bed") else 0

            # ── Pre-filled summary ────────────────────────────────────────────
            meal_default = b_data.get("meal_price", 0) * n if b_data.get("meal_price", 0) else 0
            adv_paid     = b_data.get("advance_paid", 0)
            meal_label   = b_data.get("meal_plan", "No Meals")

            rooms_info = ", ".join([f"Room {rn} ({fmt(get_room(rn)['price'] if get_room(rn) else 0)}/night)" for rn in rnums_bill])
            st.markdown(f"**{n} nights** | {rooms_info} = **{fmt(room_charge)}**")
            if extra_charge:
                st.markdown(f"Extra beds: {eb_count} × {n} nights × {fmt(r_data['extra_price'] if r_data else 0)}/night = **{fmt(extra_charge)}**")
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
                bonfire_charge = c4.number_input("🔥 Bonfire Charges (Rs.)",     min_value=0, value=0, step=50)
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

    tab1, tab2 = st.tabs(["Expense Log", "➕ Add Expense"])

    with tab1:
        expenses = st.session_state.expenses
        if not expenses:
            st.info("No expenses logged yet.")
        else:
            cats = {}
            for e in expenses:
                cats[e["category"]] = cats.get(e["category"], 0) + e["amount"]
            cols = st.columns(min(len(cats), 4))
            for i, (cat, amt) in enumerate(sorted(cats.items(), key=lambda x: -x[1])[:4]):
                cols[i].metric(cat, fmt(amt))
            st.markdown("---")
            df = pd.DataFrame(expenses)[["date", "category", "desc", "amount"]]
            df.columns = ["Date", "Category", "Description", "Amount (₹)"]
            df = df.sort_values("Date", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
            total_exp = sum(e["amount"] for e in expenses)
            st.markdown(f"**Total Expenses: {fmt(total_exp)}**")

    with tab2:
        if not can("add_expense"):
            lock("add_expense")
        else:
         st.subheader("Add Expense")
        with st.form("add_expense_form"):
            c1, c2 = st.columns(2)
            category = c1.selectbox("Category", ["Electricity", "Laundry", "Food & Beverages", "Maintenance", "Staff Salary", "Marketing", "Other"])
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
                    st.success("Expense added!")
                    st.rerun()

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
            # Search
            search_p = st.text_input("🔍 Search by guest name", placeholder="Type name...")
            filtered_p = [p for p in payments if not search_p or search_p.lower() in p.get("guest","").lower()]

            # Headers
            h1,h2,h3,h4,h5,h6,h7 = st.columns([0.8,2,1,1.5,1.5,1.5,1.5])
            h1.markdown("**#**")
            h2.markdown("**Guest**")
            h3.markdown("**Room**")
            h4.markdown("**Amount**")
            h5.markdown("**Method**")
            h6.markdown("**Type**")
            h7.markdown("**Date**")
            st.markdown("<hr style='margin:2px 0 6px;border-color:#d8b4fe'>", unsafe_allow_html=True)

            for p in reversed(filtered_p):
                c1,c2,c3,c4,c5,c6,c7 = st.columns([0.8,2,1,1.5,1.5,1.5,1.5])
                type_color = {"advance":"🔵","final":"🟢","partial":"🟡","refund":"🔴"}.get(p.get("type",""), "⚪")
                c1.write(str(p.get("id","")))
                c2.write(f"**{p.get('guest','')}**")
                c3.write(p.get("room","—"))
                amount_str = f"- {fmt(p['amount'])}" if p.get("type") == "refund" else fmt(p["amount"])
                c4.write(amount_str)
                c5.write(p.get("method","—"))
                c6.write(f"{type_color} {p.get('type','—').title()}")
                c7.write(p.get("date","—"))
                if p.get("note"):
                    st.caption(f"   📝 {p['note']}")
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
                        load_all()
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
            rc     = r["price"] * n if r else 0
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
