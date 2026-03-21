import streamlit as st
import pandas as pd
import json
import hashlib
import os
from datetime import date, datetime, timedelta
from pathlib import Path

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
            <b>Admin:</b> admin / savera@2025 &nbsp;|&nbsp;
            <b>Front Desk:</b> frontdesk / desk@123 &nbsp;|&nbsp;
            <b>Manager:</b> manager / manager@123
        </div>
        """, unsafe_allow_html=True)

# ── Gate: stop here if not logged in ─────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    show_login()
    st.stop()

# ── Data file paths ───────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
ROOMS_FILE    = DATA_DIR / "rooms.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"
BILLS_FILE    = DATA_DIR / "bills.json"
EXPENSES_FILE = DATA_DIR / "expenses.json"

# ── Helpers: load / save JSON ─────────────────────────────────────────────────
def load(path, default):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default

def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ── Seed demo data ────────────────────────────────────────────────────────────
def seed_data():
    if not ROOMS_FILE.exists():
        save(ROOMS_FILE, [
            {"num": "101", "type": "Standard", "ac": "Non-AC", "price": 2000, "extra_bed": True,  "extra_price": 400, "bonfire": False, "bonfire_price": 0,   "status": "available"},
            {"num": "102", "type": "Deluxe",   "ac": "AC",     "price": 3500, "extra_bed": True,  "extra_price": 600, "bonfire": True,  "bonfire_price": 800, "status": "occupied"},
            {"num": "103", "type": "Suite",     "ac": "AC",     "price": 6000, "extra_bed": True,  "extra_price": 800, "bonfire": True,  "bonfire_price": 800, "status": "available"},
            {"num": "104", "type": "Standard",  "ac": "AC",     "price": 2500, "extra_bed": False, "extra_price": 0,   "bonfire": False, "bonfire_price": 0,   "status": "cleaning"},
            {"num": "105", "type": "Deluxe",    "ac": "AC",     "price": 3500, "extra_bed": True,  "extra_price": 600, "bonfire": True,  "bonfire_price": 800, "status": "available"},
        ])
    if not BOOKINGS_FILE.exists():
        save(BOOKINGS_FILE, [
            {"id": 1, "guest": "Rajan Mehta", "phone": "9876543210", "room": "102",
             "agent": "Skyline Travels", "checkin": "2025-03-15", "checkout": "2025-03-22",
             "extra_bed": True, "bonfire": False, "season": "Peak", "notes": "Late arrival", "status": "checked-in"},
            {"id": 2, "guest": "Aisha Khan", "phone": "9812345678", "room": "103",
             "agent": "Himalayan Tours", "checkin": "2025-03-18", "checkout": "2025-03-25",
             "extra_bed": False, "bonfire": True, "season": "Peak", "notes": "", "status": "confirmed"},
        ])
    if not BILLS_FILE.exists():
        save(BILLS_FILE, [])
    if not EXPENSES_FILE.exists():
        save(EXPENSES_FILE, [
            {"id": 1, "date": "2025-03-10", "category": "Electricity", "desc": "Monthly bill",  "amount": 8500},
            {"id": 2, "date": "2025-03-12", "category": "Laundry",     "desc": "Linen washing", "amount": 2000},
        ])

seed_data()

# ── Load all data into session state ─────────────────────────────────────────
if "rooms"    not in st.session_state: st.session_state.rooms    = load(ROOMS_FILE,    [])
if "bookings" not in st.session_state: st.session_state.bookings = load(BOOKINGS_FILE, [])
if "bills"    not in st.session_state: st.session_state.bills    = load(BILLS_FILE,    [])
if "expenses" not in st.session_state: st.session_state.expenses = load(EXPENSES_FILE, [])

def persist():
    save(ROOMS_FILE,    st.session_state.rooms)
    save(BOOKINGS_FILE, st.session_state.bookings)
    save(BILLS_FILE,    st.session_state.bills)
    save(EXPENSES_FILE, st.session_state.expenses)

def nights(cin, cout):
    d1 = datetime.strptime(str(cin), "%Y-%m-%d")
    d2 = datetime.strptime(str(cout), "%Y-%m-%d")
    return max(1, (d2 - d1).days)

def get_room(num):
    return next((r for r in st.session_state.rooms if r["num"] == num), None)

def fmt(n):
    return f"₹{int(n):,}"

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
    st.markdown("---")
    role_badge = {"admin": "🔴 Admin", "manager": "🟡 Manager", "staff": "🟢 Staff"}.get(st.session_state.user_role, "👤")
    st.markdown(f"**{st.session_state.user_name}** &nbsp; {role_badge}")
    st.markdown("---")
    page = st.radio("Navigate", [
        "📊 Dashboard",
        "🛏️ Rooms",
        "📋 Bookings",
        "📅 Calendar",
        "₹  Billing",
        "🧾 Expenses",
        "📈 Reports",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.caption(f"📅 {date.today().strftime('%d %b %Y, %A')}")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ["logged_in", "username", "user_name", "user_role"]:
            st.session_state.pop(key, None)
        st.rerun()

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
        cols = st.columns(3)
        for i, r in enumerate(rooms):
            color = {"occupied": "#f8d7da", "available": "#d4edda", "cleaning": "#fff3cd"}.get(r["status"], "#eee")
            icon  = {"occupied": "🔴", "available": "🟢", "cleaning": "🟡"}.get(r["status"], "⚪")
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background:{color};border-radius:8px;padding:10px;text-align:center;margin-bottom:8px">
                  <div style="font-size:20px;font-weight:700">{r['num']}</div>
                  <div style="font-size:12px;color:#555">{r['type']} · {r['ac']}</div>
                  <div style="font-size:12px;margin-top:4px">{icon} {r['status']}</div>
                </div>""", unsafe_allow_html=True)

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

    tab1, tab2 = st.tabs(["All Rooms", "➕ Add Room"])

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
                    statuses = ["available", "occupied", "cleaning"]
                    cur_idx  = statuses.index(r["status"]) if r["status"] in statuses else 0
                    new_stat = statuses[(cur_idx + 1) % 3]
                    if sc1.button("🔄", key=f"tog_{r['num']}", help=f"Set to {new_stat}"):
                        r["status"] = new_stat
                        persist()
                        st.rerun()
                    if sc2.button("✏️", key=f"edit_r_{r['num']}", help="Edit room"):
                        st.session_state["edit_room"] = r["num"]
                        st.rerun()
                    if sc3.button("🗑️", key=f"del_{r['num']}"):
                        st.session_state.rooms = [x for x in st.session_state.rooms if x["num"] != r["num"]]
                        persist()
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
                            r["type"]         = new_type
                            r["ac"]           = new_ac
                            r["price"]        = new_price
                            r["status"]       = new_stat2
                            r["extra_bed"]    = new_eb
                            r["extra_price"]  = new_ep if new_eb else 0
                            r["bonfire"]      = new_bf
                            r["bonfire_price"]= new_bfp if new_bf else 0
                            persist()
                            st.session_state.pop("edit_room", None)
                            st.success(f"✅ Room {r['num']} updated!")
                            st.rerun()
                        if cancel_it:
                            st.session_state.pop("edit_room", None)
                            st.rerun()
                st.markdown("---")

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
                    st.session_state.rooms.append({
                        "num": num, "type": rtyp, "ac": ac,
                        "price": price, "extra_bed": extra_bed,
                        "extra_price": extra_price if extra_bed else 0,
                        "bonfire": bonfire,
                        "bonfire_price": bonfire_price if bonfire else 0,
                        "status": "available"
                    })
                    persist()
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

    tab1, tab2 = st.tabs(["All Bookings", "➕ New Booking"])

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
                    if b["status"] == "checked-in":
                        if a1.button("✅ Out", key=f"co_{b['id']}", help="Checkout"):
                            b["status"] = "checked-out"
                            room = get_room(b["room"])
                            if room:
                                room["status"] = "cleaning"
                            persist()
                            st.rerun()
                    if a2.button("🗑️", key=f"db_{b['id']}", help="Delete"):
                        st.session_state.bookings = [x for x in st.session_state.bookings if x["id"] != b["id"]]
                        persist()
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
                            b["guest"]           = new_guest
                            b["phone"]           = new_phone
                            b["checkin"]         = str(new_checkin)
                            b["checkout"]        = str(new_checkout)
                            b["agent"]           = new_agent
                            b["season"]          = new_season
                            b["extra_bed"]       = new_eb
                            b["extra_bed_count"] = int(new_eb_cnt) if new_eb else 0
                            b["bonfire"]         = new_bf
                            b["status"]          = new_status
                            b["meal_plan"]       = new_meal
                            b["notes"]           = new_notes
                            if new_status == "checked-out":
                                for rn in b.get("rooms", [b.get("room","")]):
                                    rm = get_room(rn)
                                    if rm: rm["status"] = "cleaning"
                            persist()
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
                        rnums  = [r.split("–")[0].strip() for r in rooms_selected]
                        new_id = max((b["id"] for b in st.session_state.bookings), default=0) + 1
                        st.session_state.bookings.append({
                            "id": new_id, "guest": guest, "phone": phone,
                            "room": ", ".join(rnums),
                            "rooms": rnums,
                            "agent": agent,
                            "checkin": str(checkin), "checkout": str(checkout),
                            "extra_bed": extra_bed,
                            "extra_bed_count": int(extra_bed_count) if extra_bed and extra_bed_count != "0 (None)" else 0,
                            "season": season,
                            "bonfire": bonfire_requested,
                            "meal_plan": meal_plan,
                            "meal_price": meal_price,
                            "advance_paid": advance_paid,
                            "advance_method": advance_method,
                            "notes": notes, "status": "confirmed"
                        })
                        for rnum in rnums:
                            room = get_room(rnum)
                            if room: room["status"] = "occupied"
                        persist()
                        msg = f"✅ Booking confirmed for **{guest}** — Room(s) {', '.join(rnums)} | {checkin} → {checkout}"
                        if extra_bed and extra_bed_count != "0 (None)": msg += f" | 🛏️ {extra_bed_count} Extra Bed(s)"
                        if bonfire_requested: msg += " | 🔥 Bonfire"
                        if meal_plan != "No Meals (Room Only)": msg += f" | 🍽️ {meal_plan.split('(')[0].strip()}"
                        if advance_paid > 0:  msg += f" | 💳 Advance: Rs.{advance_paid:,} ({advance_method})"
                        st.success(msg)
                        st.rerun()

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
                    if b["status"] != "Paid":
                        if btn1.button("✅ Mark as Paid", key=f"pay_{b['bill_id']}"):
                            b["status"] = "Paid"
                            persist()
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
                    bill_num = len(st.session_state.bills) + 1
                    st.session_state.bills.append({
                        "bill_id":        f"BILL-{bill_num:03d}",
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
                    })
                    persist()
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
                    new_id = max((e["id"] for e in st.session_state.expenses), default=0) + 1
                    st.session_state.expenses.append({
                        "id": new_id, "date": str(exp_date),
                        "category": category, "desc": desc, "amount": amount
                    })
                    persist()
                    st.success("Expense added!")
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
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
