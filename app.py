import streamlit as st
import pandas as pd
import json
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

# ── Seed demo data if files are empty ────────────────────────────────────────
def seed_data():
    if not ROOMS_FILE.exists():
        save(ROOMS_FILE, [
            {"num": "101", "type": "Standard", "ac": "Non-AC", "price": 2000, "extra_bed": True,  "extra_price": 400, "status": "available"},
            {"num": "102", "type": "Deluxe",   "ac": "AC",     "price": 3500, "extra_bed": True,  "extra_price": 600, "status": "occupied"},
            {"num": "103", "type": "Suite",     "ac": "AC",     "price": 6000, "extra_bed": True,  "extra_price": 800, "status": "available"},
            {"num": "104", "type": "Standard",  "ac": "AC",     "price": 2500, "extra_bed": False, "extra_price": 0,   "status": "cleaning"},
            {"num": "105", "type": "Deluxe",    "ac": "AC",     "price": 3500, "extra_bed": True,  "extra_price": 600, "status": "available"},
        ])
    if not BOOKINGS_FILE.exists():
        save(BOOKINGS_FILE, [
            {"id": 1, "guest": "Rajan Mehta",  "phone": "9876543210", "room": "102",
             "agent": "Skyline Travels", "checkin": "2025-03-15", "checkout": "2025-03-22",
             "extra_bed": True, "season": "Peak", "notes": "Late arrival", "status": "checked-in"},
            {"id": 2, "guest": "Aisha Khan",   "phone": "9812345678", "room": "103",
             "agent": "Himalayan Tours", "checkin": "2025-03-18", "checkout": "2025-03-25",
             "extra_bed": False, "season": "Peak", "notes": "", "status": "confirmed"},
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
    /* ── Purple theme ── */
    [data-testid="stSidebar"] { background: #3b1f6e !important; }
    [data-testid="stSidebar"] * { color: #e8d9ff !important; }
    [data-testid="stSidebar"] .stRadio label { color: #e8d9ff !important; }
    [data-testid="stSidebar"] hr { border-color: #5a3a9a !important; }

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
    page = st.radio("Navigate", [
        "📊 Dashboard",
        "🛏️ Rooms",
        "📋 Bookings",
        "₹  Billing",
        "🧾 Expenses",
        "📈 Reports",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.caption(f"📅 {date.today().strftime('%d %b %Y, %A')}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("📊 Dashboard")

    rooms    = st.session_state.rooms
    bookings = st.session_state.bookings
    bills    = st.session_state.bills

    occ   = sum(1 for r in rooms if r["status"] == "occupied")
    avail = sum(1 for r in rooms if r["status"] == "available")
    clean = sum(1 for r in rooms if r["status"] == "cleaning")
    rev   = sum(b["room_charge"] + b.get("food",0) + b.get("laundry",0) +
                b.get("extra_bed",0) + b.get("electricity",0) + b.get("other",0)
                for b in bills)
    pending = sum(1 for b in bookings if b["status"] == "checked-in")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔴 Occupied",       occ)
    c2.metric("🟢 Available",      avail)
    c3.metric("🟡 Cleaning",       clean)
    c4.metric("₹  Total Revenue",  fmt(rev))
    c5.metric("⏳ Pending Checkouts", pending)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Room Status")
        cols = st.columns(3)
        for i, r in enumerate(rooms):
            color = {"occupied":"#f8d7da","available":"#d4edda","cleaning":"#fff3cd"}.get(r["status"],"#eee")
            icon  = {"occupied":"🔴","available":"🟢","cleaning":"🟡"}.get(r["status"],"⚪")
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
            df = pd.DataFrame(bookings)[["guest","room","checkin","checkout","status"]].tail(8)
            df.columns = ["Guest","Room","Check-in","Check-out","Status"]
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
                color = {"occupied":"#f8d7da","available":"#d4edda","cleaning":"#fff3cd"}.get(r["status"],"#eee")
                c1,c2,c3,c4,c5,c6,c7 = st.columns([1,1.5,1,1.5,1.5,1.5,2])
                c1.markdown(f"**{r['num']}**")
                c2.write(r["type"])
                c3.write(r["ac"])
                c4.write(fmt(r["price"]) + "/night")
                c5.write(f"Extra Bed: {'Yes +'+fmt(r['extra_price']) if r['extra_bed'] else 'No'}")
                c6.markdown(f"<span style='background:{color};padding:2px 10px;border-radius:12px;font-size:12px'>{r['status']}</span> {'🔥' if r.get('bonfire') else ''}", unsafe_allow_html=True)
                with c7:
                    sc1, sc2, sc3 = st.columns(3)
                    statuses = ["available","occupied","cleaning"]
                    cur_idx  = statuses.index(r["status"]) if r["status"] in statuses else 0
                    new_stat = statuses[(cur_idx + 1) % 3]
                    if sc1.button("🔄", key=f"tog_{r['num']}", help=f"Set to {new_stat}"):
                        r["status"] = new_stat
                        persist()
                        st.rerun()
                    if sc2.button("🗑️", key=f"del_{r['num']}"):
                        st.session_state.rooms = [x for x in st.session_state.rooms if x["num"] != r["num"]]
                        persist()
                        st.rerun()
                st.markdown("---")

    with tab2:
        st.subheader("Add New Room")
        with st.form("add_room_form"):
            c1, c2 = st.columns(2)
            num  = c1.text_input("Room Number", placeholder="e.g. 201")
            rtyp = c2.selectbox("Room Type", ["Standard","Deluxe","Suite"])
            c3, c4 = st.columns(2)
            price = c3.number_input("Price per Night (₹)", min_value=0, value=2500, step=100)
            ac    = c4.selectbox("AC / Non-AC", ["AC","Non-AC"])
            c5, c6 = st.columns(2)
            extra_bed   = c5.checkbox("Extra Bed Available?")
            extra_price = c6.number_input("Extra Bed Charge (₹/night)", min_value=0, value=500, step=50)
            c7, c8 = st.columns(2)
            bonfire         = c7.checkbox("🔥 Bonfire Available?")
            bonfire_price   = c8.number_input("Bonfire Charge (₹/session)", min_value=0, value=800, step=50)
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
                    st.success(f"Room {num} added!")
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: BOOKINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Bookings":
    st.title("📋 Bookings")

    tab1, tab2 = st.tabs(["All Bookings", "➕ New Booking"])

    with tab1:
        bookings = st.session_state.bookings
        col1, col2 = st.columns([2,1])
        search = col1.text_input("🔍 Search by guest name", placeholder="Type name...")
        status_filter = col2.selectbox("Filter by status", ["All","checked-in","confirmed","checked-out"])

        filtered = [b for b in bookings
                    if (not search or search.lower() in b["guest"].lower())
                    and (status_filter == "All" or b["status"] == status_filter)]

        if not filtered:
            st.info("No bookings found.")
        else:
            for b in reversed(filtered):
                n = nights(b["checkin"], b["checkout"])
                r = get_room(b["room"])
                room_charge = r["price"] * n if r else 0
                badge_color = {"checked-in":"#d4edda","confirmed":"#cce5ff","checked-out":"#e2e3e5"}.get(b["status"],"#eee")
                badge_text  = {"checked-in":"🟢 Checked In","confirmed":"🔵 Confirmed","checked-out":"⚫ Checked Out"}.get(b["status"],b["status"])

                with st.expander(f"**{b['guest']}**  —  Room {b['room']}  |  {b['checkin']} → {b['checkout']}  ({n} nights)  |  {fmt(room_charge)}"):
                    c1,c2,c3 = st.columns(3)
                    c1.write(f"📞 **Phone:** {b['phone']}")
                    c1.write(f"🏢 **Agent:** {b.get('agent') or '—'}")
                    c2.write(f"🌄 **Season:** {b.get('season','—')}")
                    c2.write(f"🛏️ **Extra Bed:** {'Yes' if b.get('extra_bed') else 'No'}")
                    c2.write(f"🔥 **Bonfire:** {'Yes' if b.get('bonfire') else 'No'}")
                    c3.markdown(f"<span style='background:{badge_color};padding:4px 12px;border-radius:12px;font-size:13px'>{badge_text}</span>", unsafe_allow_html=True)
                    if b.get("notes"):
                        st.caption(f"📝 Notes: {b['notes']}")
                    bc1, bc2 = st.columns(8)[:2]
                    if b["status"] == "checked-in":
                        if bc1.button("✅ Checkout", key=f"co_{b['id']}"):
                            b["status"] = "checked-out"
                            room = get_room(b["room"])
                            if room: room["status"] = "cleaning"
                            persist()
                            st.rerun()
                    if bc2.button("🗑️ Delete", key=f"db_{b['id']}"):
                        st.session_state.bookings = [x for x in st.session_state.bookings if x["id"] != b["id"]]
                        persist()
                        st.rerun()

    with tab2:
        st.subheader("New Booking")
        available_rooms = [r for r in st.session_state.rooms if r["status"] in ["available","cleaning"]]
        if not available_rooms:
            st.warning("No available rooms right now.")
        else:
            with st.form("add_booking_form"):
                c1,c2 = st.columns(2)
                guest = c1.text_input("Guest Name *")
                phone = c2.text_input("Phone Number")
                c3,c4 = st.columns(2)
                room_options = [f"{r['num']} – {r['type']} ({r['ac']}) {fmt(r['price'])}/night" for r in available_rooms]
                room_sel = c3.selectbox("Select Room *", room_options)
                agent    = c4.text_input("Travel Agent (optional)")
                c5,c6 = st.columns(2)
                checkin  = c5.date_input("Check-in Date",  value=date.today())
                checkout = c6.date_input("Check-out Date", value=date.today() + timedelta(days=3))
                c7,c8 = st.columns(2)
                extra_bed = c7.checkbox("Extra Bed?")
                season    = c8.selectbox("Season", ["Peak","Off-Peak"])
                # Bonfire — show only if any available room has bonfire
                bonfire_rooms = [r for r in available_rooms if r.get("bonfire")]
                bonfire_requested = st.checkbox("🔥 Bonfire Requested?") if bonfire_rooms else False
                if bonfire_requested:
                    st.caption("Bonfire charge will be added at billing time.")
                notes = st.text_area("Notes / Special Requests", height=80)
                submitted = st.form_submit_button("✅ Confirm Booking", use_container_width=True)
                if submitted:
                    if not guest:
                        st.error("Enter guest name.")
                    elif checkout <= checkin:
                        st.error("Check-out must be after check-in.")
                    else:
                        rnum = room_sel.split("–")[0].strip()
                        new_id = max((b["id"] for b in st.session_state.bookings), default=0) + 1
                        st.session_state.bookings.append({
                            "id": new_id, "guest": guest, "phone": phone,
                            "room": rnum, "agent": agent,
                            "checkin": str(checkin), "checkout": str(checkout),
                            "extra_bed": extra_bed, "season": season,
                            "bonfire": bonfire_requested,
                            "notes": notes, "status": "confirmed"
                        })
                        room = get_room(rnum)
                        if room: room["status"] = "occupied"
                        persist()
                        st.success(f"Booking confirmed for {guest}!" + (" 🔥 Bonfire noted!" if bonfire_requested else ""))
                        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: BILLING
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "₹  Billing":
    st.title("₹ Billing & Invoices")

    tab1, tab2 = st.tabs(["All Bills", "➕ Generate Bill"])

    with tab1:
        bills = st.session_state.bills
        if not bills:
            st.info("No bills generated yet.")
        else:
            for b in reversed(bills):
                    total = b["room_charge"] + b.get("food",0) + b.get("laundry",0) + b.get("extra_bed",0) + b.get("electricity",0) + b.get("bonfire",0) + b.get("other",0)
                    with st.expander(f"**{b['bill_id']}**  —  {b['guest']}  |  Room {b['room']}  |  **{fmt(total)}**  |  {b['status']}"):
                        c1,c2,c3,c4 = st.columns(4)
                        c1.metric("Room Charge",   fmt(b["room_charge"]))
                        c2.metric("Food",          fmt(b.get("food",0)))
                        c3.metric("Laundry",       fmt(b.get("laundry",0)))
                        c4.metric("Extra Bed",     fmt(b.get("extra_bed",0)))
                        c1b,c2b,c3b,c4b = st.columns(4)
                        c1b.metric("Electricity",  fmt(b.get("electricity",0)))
                        c2b.metric("🔥 Bonfire",   fmt(b.get("bonfire",0)))
                        c3b.metric("Other",        fmt(b.get("other",0)))
                        c4b.metric("TOTAL",        fmt(total))
                        paid_btn, _ = st.columns(8)[:2]
                        if b["status"] != "Paid":
                            if paid_btn.button("✅ Mark as Paid", key=f"pay_{b['bill_id']}"):
                                b["status"] = "Paid"
                                persist()
                                st.rerun()

    with tab2:
        st.subheader("Generate New Bill")
        active_bookings = [b for b in st.session_state.bookings if b["status"] in ["checked-in","confirmed","checked-out"]]
        if not active_bookings:
            st.warning("No bookings available for billing.")
        else:
            booking_opts = [f"{b['guest']} – Room {b['room']} ({b['checkin']} → {b['checkout']})" for b in active_bookings]
            sel = st.selectbox("Select Booking", booking_opts)
            b_idx  = booking_opts.index(sel)
            b_data = active_bookings[b_idx]
            r_data = get_room(b_data["room"])
            n      = nights(b_data["checkin"], b_data["checkout"])
            room_charge = r_data["price"] * n if r_data else 0
            extra_charge = (r_data["extra_price"] * n if r_data else 0) if b_data.get("extra_bed") else 0

            st.markdown(f"**{n} nights** × {fmt(r_data['price'] if r_data else 0)}/night = **{fmt(room_charge)}**")
            if extra_charge:
                st.markdown(f"Extra bed: {n} nights × {fmt(r_data['extra_price'])}/night = **{fmt(extra_charge)}**")

            with st.form("bill_form"):
                c1,c2 = st.columns(2)
                food      = c1.number_input("🍽️ Food Charges (₹)",       min_value=0, value=0, step=50)
                laundry   = c2.number_input("👕 Laundry Charges (₹)",     min_value=0, value=0, step=50)
                c3,c4 = st.columns(2)
                electricity = c3.number_input("💡 Electricity Charges (₹)", min_value=0, value=0, step=50)
                bonfire_charge = c4.number_input("🔥 Bonfire Charges (₹)",  min_value=0, value=0, step=50)
                other = st.number_input("📦 Other Charges (₹)", min_value=0, value=0, step=50)
                total = room_charge + extra_charge + food + laundry + electricity + bonfire_charge + other
                st.markdown(f"### 💰 Total: {fmt(total)}")
                submitted = st.form_submit_button("🧾 Save Bill", use_container_width=True)
                if submitted:
                    bill_num = len(st.session_state.bills) + 1
                    st.session_state.bills.append({
                        "bill_id": f"BILL-{bill_num:03d}",
                        "guest": b_data["guest"],
                        "room":  b_data["room"],
                        "nights": n,
                        "room_charge": room_charge,
                        "extra_bed":   extra_charge,
                        "food":        food,
                        "laundry":     laundry,
                        "electricity": electricity,
                        "bonfire":     bonfire_charge,
                        "other":       other,
                        "total":       total,
                        "status":      "Pending",
                        "date":        str(date.today()),
                    })
                    persist()
                    st.success(f"Bill saved! Total: {fmt(total)}")
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
            # Summary metrics
            cats = {}
            for e in expenses:
                cats[e["category"]] = cats.get(e["category"], 0) + e["amount"]
            cols = st.columns(min(len(cats), 4))
            for i, (cat, amt) in enumerate(sorted(cats.items(), key=lambda x:-x[1])[:4]):
                cols[i].metric(cat, fmt(amt))
            st.markdown("---")

            df = pd.DataFrame(expenses)[["date","category","desc","amount"]]
            df.columns = ["Date","Category","Description","Amount (₹)"]
            df = df.sort_values("Date", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)

            total_exp = sum(e["amount"] for e in expenses)
            st.markdown(f"**Total Expenses: {fmt(total_exp)}**")

    with tab2:
        st.subheader("Add Expense")
        with st.form("add_expense_form"):
            c1,c2 = st.columns(2)
            category = c1.selectbox("Category", ["Electricity","Laundry","Food & Beverages","Maintenance","Staff Salary","Marketing","Other"])
            amount   = c2.number_input("Amount (₹)", min_value=0, value=0, step=100)
            c3,c4 = st.columns(2)
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

    total_rev = sum(b["room_charge"] + b.get("food",0) + b.get("laundry",0) +
                    b.get("extra_bed",0) + b.get("electricity",0) + b.get("other",0)
                    for b in bills)
    total_exp = sum(e["amount"] for e in expenses)
    net       = total_rev - total_exp

    c1,c2,c3 = st.columns(3)
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
            if t not in type_data: type_data[t] = {"total":0,"occupied":0}
            type_data[t]["total"] += 1
            if r["status"] == "occupied": type_data[t]["occupied"] += 1
        occ_df = pd.DataFrame([
            {"Room Type": t, "Total": d["total"], "Occupied": d["occupied"],
             "Occupancy %": round(d["occupied"]/d["total"]*100) if d["total"] else 0}
            for t,d in type_data.items()
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
            exp_df = pd.DataFrame(list(cats.items()), columns=["Category","Amount"])
            st.bar_chart(exp_df.set_index("Category"))
            st.dataframe(exp_df, hide_index=True, use_container_width=True)
        else:
            st.info("No expenses yet.")

    st.markdown("---")
    st.subheader("Booking Summary")
    if bookings:
        rows = []
        for b in bookings:
            r = get_room(b["room"])
            n = nights(b["checkin"], b["checkout"])
            rc = r["price"] * n if r else 0
            eb = (r["extra_price"] * n if r else 0) if b.get("extra_bed") else 0
            bill = next((bl for bl in bills if bl["guest"]==b["guest"] and bl["room"]==b["room"]), None)
            extras = (bill.get("food",0)+bill.get("laundry",0)+bill.get("electricity",0)+bill.get("other",0)) if bill else 0
            rows.append({"Guest": b["guest"], "Room": b["room"], "Nights": n,
                         "Season": b.get("season","—"), "Room Charge": rc,
                         "Extra Bed": eb, "Food+Laundry+Elec": extras,
                         "Total": rc+eb+extras, "Status": b["status"]})
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown(f"**Grand Total Revenue from Bookings: {fmt(df['Total'].sum())}**")
    else:
        st.info("No bookings yet.")
