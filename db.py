"""
db.py — Smart dual-mode database layer for Savera Inn Resort PMS

Online  → uses PostgreSQL (Supabase) — cloud, multi-user, persistent
Offline → uses local JSON files       — works without internet
"""
import os
import json
import streamlit as st
from datetime import date
from pathlib import Path

# ── Detect mode ───────────────────────────────────────────────────────────────
def _is_online():
    """Try connecting to Supabase. Returns True if successful."""
    try:
        import psycopg2
        url = st.secrets.get("DATABASE_URL", "")
        if not url:
            return False
        conn = psycopg2.connect(url, connect_timeout=10)
        conn.close()
        return True
    except Exception:
        return False

# ── Check once per session ────────────────────────────────────────────────────
if "db_mode" not in st.session_state:
    online = _is_online()
    st.session_state.db_mode = "online" if online else "offline"

MODE = st.session_state.db_mode

# ── Local JSON fallback paths ─────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
ROOMS_FILE    = DATA_DIR / "rooms.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"
BILLS_FILE    = DATA_DIR / "bills.json"
EXPENSES_FILE = DATA_DIR / "expenses.json"
PAYMENTS_FILE = DATA_DIR / "payments.json"

def _jload(path, default):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default

def _jsave(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ══════════════════════════════════════════════════════════════════════════════
# PostgreSQL helpers
# ══════════════════════════════════════════════════════════════════════════════
def _conn():
    import psycopg2
    return psycopg2.connect(st.secrets["DATABASE_URL"], connect_timeout=10)

def _run(sql, params=(), fetch=None):
    import psycopg2.extras
    conn = _conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                if fetch == "all":
                    return [dict(r) for r in cur.fetchall()]
                if fetch in ("one", "returning"):
                    row = cur.fetchone()
                    return dict(row) if row else None
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# TABLE SETUP
# ══════════════════════════════════════════════════════════════════════════════
def setup_tables():
    if MODE == "offline":
        # Just ensure local JSON files exist
        for path, default in [
            (ROOMS_FILE, []), (BOOKINGS_FILE, []),
            (BILLS_FILE, []), (EXPENSES_FILE, []), (PAYMENTS_FILE, [])
        ]:
            if not path.exists():
                _jsave(path, default)
        return

    conn = _conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    num TEXT PRIMARY KEY, type TEXT, ac TEXT,
                    price INTEGER DEFAULT 0, extra_bed BOOLEAN DEFAULT FALSE,
                    extra_price INTEGER DEFAULT 0, bonfire BOOLEAN DEFAULT FALSE,
                    bonfire_price INTEGER DEFAULT 0, status TEXT DEFAULT 'available'
                );
                CREATE TABLE IF NOT EXISTS bookings (
                    id SERIAL PRIMARY KEY, guest TEXT, phone TEXT,
                    room TEXT, rooms TEXT[], agent TEXT,
                    checkin DATE, checkout DATE,
                    extra_bed BOOLEAN DEFAULT FALSE, extra_bed_count INTEGER DEFAULT 0,
                    season TEXT DEFAULT 'Peak', bonfire BOOLEAN DEFAULT FALSE,
                    meal_plan TEXT DEFAULT 'No Meals (Room Only)', meal_price INTEGER DEFAULT 0,
                    advance_paid INTEGER DEFAULT 0, advance_method TEXT DEFAULT 'Cash',
                    notes TEXT DEFAULT '', status TEXT DEFAULT 'confirmed',
                    payment_status TEXT DEFAULT 'unpaid', created_at TIMESTAMP DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS bills (
                    bill_id TEXT PRIMARY KEY, guest TEXT, room TEXT,
                    nights INTEGER DEFAULT 0, room_charge INTEGER DEFAULT 0,
                    extra_bed INTEGER DEFAULT 0, food INTEGER DEFAULT 0,
                    laundry INTEGER DEFAULT 0, electricity INTEGER DEFAULT 0,
                    bonfire INTEGER DEFAULT 0, meal INTEGER DEFAULT 0,
                    meal_plan TEXT, other INTEGER DEFAULT 0,
                    advance_paid INTEGER DEFAULT 0, advance_method TEXT,
                    gross INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'Pending', created_date DATE, booking_id INTEGER
                );
                CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY, date DATE,
                    category TEXT, description TEXT, amount INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY, booking_id INTEGER, bill_id TEXT,
                    guest TEXT, room TEXT, amount INTEGER DEFAULT 0,
                    method TEXT, type TEXT, date DATE, note TEXT DEFAULT ''
                );
                """)
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# ROOMS
# ══════════════════════════════════════════════════════════════════════════════
def get_rooms():
    if MODE == "offline":
        return _jload(ROOMS_FILE, [])
    return _run("SELECT * FROM rooms ORDER BY num", fetch="all") or []

def add_room(r):
    if MODE == "offline":
        rooms = _jload(ROOMS_FILE, [])
        if not any(x["num"] == r["num"] for x in rooms):
            rooms.append(r)
        _jsave(ROOMS_FILE, rooms)
        return
    _run("""INSERT INTO rooms (num,type,ac,price,extra_bed,extra_price,bonfire,bonfire_price,status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (num) DO NOTHING""",
         (r["num"],r["type"],r["ac"],r["price"],r["extra_bed"],
          r["extra_price"],r["bonfire"],r["bonfire_price"],r.get("status","available")))

def update_room(num, fields):
    if MODE == "offline":
        rooms = _jload(ROOMS_FILE, [])
        for r in rooms:
            if r["num"] == num:
                r.update(fields)
        _jsave(ROOMS_FILE, rooms)
        return
    sets = ", ".join(f"{k}=%s" for k in fields)
    _run(f"UPDATE rooms SET {sets} WHERE num=%s", list(fields.values())+[num])

def delete_room(num):
    if MODE == "offline":
        rooms = _jload(ROOMS_FILE, [])
        _jsave(ROOMS_FILE, [r for r in rooms if r["num"] != num])
        return
    _run("DELETE FROM rooms WHERE num=%s", (num,))

def update_room_status(num, status):
    update_room(num, {"status": status})

# ══════════════════════════════════════════════════════════════════════════════
# BOOKINGS
# ══════════════════════════════════════════════════════════════════════════════
def _fix_booking(b):
    if b.get("rooms") is None:
        b["rooms"] = [b["room"]] if b.get("room") else []
    b["checkin"]  = str(b["checkin"])
    b["checkout"] = str(b["checkout"])
    return b

def get_bookings():
    if MODE == "offline":
        return [_fix_booking(b) for b in _jload(BOOKINGS_FILE, [])]
    rows = _run("SELECT * FROM bookings ORDER BY checkin DESC", fetch="all") or []
    return [_fix_booking(b) for b in rows]

def add_booking(b):
    if MODE == "offline":
        bookings = _jload(BOOKINGS_FILE, [])
        new_id = max((x["id"] for x in bookings), default=0) + 1
        b["id"] = new_id
        bookings.append(b)
        _jsave(BOOKINGS_FILE, bookings)
        return new_id
    row = _run("""
        INSERT INTO bookings (guest,phone,room,rooms,agent,checkin,checkout,
             extra_bed,extra_bed_count,season,bonfire,meal_plan,meal_price,
             advance_paid,advance_method,notes,status,payment_status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
    """, (b["guest"],b.get("phone",""),b["room"],b.get("rooms",[b["room"]]),
          b.get("agent",""),b["checkin"],b["checkout"],
          b.get("extra_bed",False),b.get("extra_bed_count",0),
          b.get("season","Peak"),b.get("bonfire",False),
          b.get("meal_plan","No Meals (Room Only)"),b.get("meal_price",0),
          b.get("advance_paid",0),b.get("advance_method","Cash"),
          b.get("notes",""),b.get("status","confirmed"),
          b.get("payment_status","unpaid")), fetch="returning")
    return row["id"] if row else None

def update_booking(bid, fields):
    if "checkin"  in fields: fields["checkin"]  = str(fields["checkin"])
    if "checkout" in fields: fields["checkout"] = str(fields["checkout"])
    if MODE == "offline":
        bookings = _jload(BOOKINGS_FILE, [])
        for b in bookings:
            if b["id"] == bid:
                b.update(fields)
        _jsave(BOOKINGS_FILE, bookings)
        return
    sets = ", ".join(f"{k}=%s" for k in fields)
    _run(f"UPDATE bookings SET {sets} WHERE id=%s", list(fields.values())+[bid])

def delete_booking(bid):
    if MODE == "offline":
        bookings = _jload(BOOKINGS_FILE, [])
        _jsave(BOOKINGS_FILE, [b for b in bookings if b["id"] != bid])
        return
    _run("DELETE FROM bookings WHERE id=%s", (bid,))

# ══════════════════════════════════════════════════════════════════════════════
# BILLS
# ══════════════════════════════════════════════════════════════════════════════
def get_bills():
    if MODE == "offline":
        return _jload(BILLS_FILE, [])
    rows = _run("SELECT * FROM bills ORDER BY created_date DESC", fetch="all") or []
    for b in rows:
        b["date"] = str(b.get("created_date",""))
    return rows

def add_bill(b):
    if MODE == "offline":
        bills = _jload(BILLS_FILE, [])
        bills.append(b)
        _jsave(BILLS_FILE, bills)
        return
    _run("""INSERT INTO bills (bill_id,guest,room,nights,room_charge,extra_bed,food,laundry,
             electricity,bonfire,meal,meal_plan,other,advance_paid,advance_method,
             gross,total,status,created_date,booking_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (bill_id) DO NOTHING""",
        (b["bill_id"],b["guest"],b["room"],b["nights"],
         b.get("room_charge",0),b.get("extra_bed",0),b.get("food",0),
         b.get("laundry",0),b.get("electricity",0),b.get("bonfire",0),
         b.get("meal",0),b.get("meal_plan",""),b.get("other",0),
         b.get("advance_paid",0),b.get("advance_method","Cash"),
         b.get("gross",0),b.get("total",0),b.get("status","Pending"),
         b.get("date",str(date.today())),b.get("booking_id")))

def update_bill_status(bill_id, status):
    if MODE == "offline":
        bills = _jload(BILLS_FILE, [])
        for b in bills:
            if b["bill_id"] == bill_id:
                b["status"] = status
        _jsave(BILLS_FILE, bills)
        return
    _run("UPDATE bills SET status=%s WHERE bill_id=%s", (status, bill_id))

# ══════════════════════════════════════════════════════════════════════════════
# EXPENSES
# ══════════════════════════════════════════════════════════════════════════════
def get_expenses():
    if MODE == "offline":
        return _jload(EXPENSES_FILE, [])
    rows = _run("SELECT * FROM expenses ORDER BY date DESC", fetch="all") or []
    for e in rows:
        e["desc"] = e.pop("description","")
        e["date"] = str(e["date"])
    return rows

def add_expense(e):
    if MODE == "offline":
        expenses = _jload(EXPENSES_FILE, [])
        new_id = max((x.get("id",0) for x in expenses), default=0) + 1
        e["id"] = new_id
        expenses.append(e)
        _jsave(EXPENSES_FILE, expenses)
        return
    _run("INSERT INTO expenses (date,category,description,amount) VALUES (%s,%s,%s,%s)",
         (e["date"],e["category"],e.get("desc",""),e["amount"]))

# ══════════════════════════════════════════════════════════════════════════════
# PAYMENTS
# ══════════════════════════════════════════════════════════════════════════════
def get_payments():
    if MODE == "offline":
        return _jload(PAYMENTS_FILE, [])
    rows = _run("SELECT * FROM payments ORDER BY date DESC", fetch="all") or []
    for p in rows:
        p["date"] = str(p.get("date",""))
    return rows

def add_payment(p):
    if MODE == "offline":
        payments = _jload(PAYMENTS_FILE, [])
        new_id = max((x.get("id",0) for x in payments), default=0) + 1
        p["id"] = new_id
        payments.append(p)
        _jsave(PAYMENTS_FILE, payments)
        return
    _run("""INSERT INTO payments (booking_id,bill_id,guest,room,amount,method,type,date,note)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
         (p.get("booking_id"),p.get("bill_id"),p.get("guest",""),
          p.get("room",""),p.get("amount",0),p.get("method","Cash"),
          p.get("type",""),p.get("date",str(date.today())),p.get("note","")))
