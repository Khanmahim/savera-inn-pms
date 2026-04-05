"""
db.py — PostgreSQL database layer for Savera Inn Resort PMS
Always uses Supabase when DATABASE_URL is available in secrets.
"""
import json
import streamlit as st
from datetime import date
from pathlib import Path

# ── Always online if DATABASE_URL exists in secrets ───────────────────────────
try:
    _DB_URL = st.secrets["DATABASE_URL"]
    MODE = "online"
except Exception:
    _DB_URL = None
    MODE = "offline"

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

# ── PostgreSQL helpers ────────────────────────────────────────────────────────
def _conn():
    import psycopg2
    return psycopg2.connect(_DB_URL, connect_timeout=10)

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
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    message TEXT NOT NULL,
                    type TEXT DEFAULT 'info',
                    category TEXT DEFAULT 'general',
                    is_read BOOLEAN DEFAULT FALSE,
                    booking_id INTEGER,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_notifications_read
                    ON notifications (is_read);
                CREATE INDEX IF NOT EXISTS idx_notifications_created
                    ON notifications (created_at DESC);

                -- ── Indexes for faster queries ────────────────────────────────
                CREATE INDEX IF NOT EXISTS idx_bookings_dates
                    ON bookings (checkin, checkout);
                CREATE INDEX IF NOT EXISTS idx_bookings_room
                    ON bookings (room);
                CREATE INDEX IF NOT EXISTS idx_bookings_status
                    ON bookings (status);
                CREATE INDEX IF NOT EXISTS idx_bookings_guest
                    ON bookings (guest);
                CREATE INDEX IF NOT EXISTS idx_payments_booking
                    ON payments (booking_id);
                CREATE INDEX IF NOT EXISTS idx_payments_bill
                    ON payments (bill_id);
                CREATE INDEX IF NOT EXISTS idx_bills_guest
                    ON bills (guest);
                CREATE INDEX IF NOT EXISTS idx_expenses_date
                    ON expenses (date);
                CREATE INDEX IF NOT EXISTS idx_expenses_category
                    ON expenses (category);
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

def update_expense(eid, fields):
    if MODE == "offline":
        expenses = _jload(EXPENSES_FILE, [])
        for e in expenses:
            if e["id"] == eid:
                e.update(fields)
        _jsave(EXPENSES_FILE, expenses)
        return
    sets = ", ".join(f"{k}=%s" for k in fields)
    _run(f"UPDATE expenses SET {sets} WHERE id=%s", list(fields.values())+[eid])

def delete_expense(eid):
    if MODE == "offline":
        expenses = _jload(EXPENSES_FILE, [])
        _jsave(EXPENSES_FILE, [e for e in expenses if e["id"] != eid])
        return
    _run("DELETE FROM expenses WHERE id=%s", (eid,))

def update_payment(pid, fields):
    if MODE == "offline":
        payments = _jload(PAYMENTS_FILE, [])
        for p in payments:
            if p["id"] == pid:
                p.update(fields)
        _jsave(PAYMENTS_FILE, payments)
        return
    sets = ", ".join(f"{k}=%s" for k in fields)
    _run(f"UPDATE payments SET {sets} WHERE id=%s", list(fields.values())+[pid])

def delete_payment(pid):
    if MODE == "offline":
        payments = _jload(PAYMENTS_FILE, [])
        _jsave(PAYMENTS_FILE, [p for p in payments if p["id"] != pid])
        return
    _run("DELETE FROM payments WHERE id=%s", (pid,))

# ══════════════════════════════════════════════════════════════════════════════
# SQL-POWERED QUERY FUNCTIONS (replaces slow Python loops)
# ══════════════════════════════════════════════════════════════════════════════

def get_room_status_on_date_sql(room_num, check_date):
    """
    Fast SQL version — checks if a room is occupied on a given date.
    Uses index on (checkin, checkout) for O(log n) instead of O(n).
    Returns (status, booking_dict or None)
    """
    if MODE == "offline":
        # Fallback to Python loop for offline mode
        from datetime import datetime as dt
        bookings = _jload(BOOKINGS_FILE, [])
        for b in bookings:
            if b.get("status") == "checked-out":
                continue
            rooms_list = b.get("rooms", [b.get("room", "")])
            if not isinstance(rooms_list, list):
                rooms_list = [rooms_list]
            if room_num not in rooms_list:
                continue
            try:
                cin  = dt.strptime(b["checkin"],  "%Y-%m-%d").date()
                cout = dt.strptime(b["checkout"], "%Y-%m-%d").date()
                if cin <= check_date < cout:
                    return "occupied", b
            except:
                pass
        return "available", None

    row = _run("""
        SELECT * FROM bookings
        WHERE (room = %s OR %s = ANY(rooms))
          AND status != 'checked-out'
          AND checkin <= %s
          AND checkout > %s
        LIMIT 1
    """, (room_num, room_num, check_date, check_date), fetch="one")

    if row:
        row["checkin"]  = str(row["checkin"])
        row["checkout"] = str(row["checkout"])
        if row.get("rooms") is None:
            row["rooms"] = [row["room"]] if row.get("room") else []
        return "occupied", row
    return "available", None


def check_overbooking_sql(room_num, checkin_str, checkout_str, exclude_booking_id=None):
    """
    Fast SQL overbooking check — uses date index for O(log n) speed.
    Returns list of conflicting bookings.
    """
    if MODE == "offline":
        from datetime import datetime as dt
        try:
            cin  = dt.strptime(checkin_str,  "%Y-%m-%d").date()
            cout = dt.strptime(checkout_str, "%Y-%m-%d").date()
        except:
            return []
        bookings = _jload(BOOKINGS_FILE, [])
        conflicts = []
        for b in bookings:
            if b.get("status") == "checked-out": continue
            if exclude_booking_id and b.get("id") == exclude_booking_id: continue
            rooms_list = b.get("rooms", [b.get("room", "")])
            if not isinstance(rooms_list, list): rooms_list = [rooms_list]
            if room_num not in rooms_list: continue
            try:
                bcin  = dt.strptime(b["checkin"],  "%Y-%m-%d").date()
                bcout = dt.strptime(b["checkout"], "%Y-%m-%d").date()
                if cin < bcout and bcin < cout:
                    conflicts.append(b)
            except:
                pass
        return conflicts

    sql = """
        SELECT * FROM bookings
        WHERE (room = %s OR %s = ANY(rooms))
          AND status != 'checked-out'
          AND checkin < %s
          AND checkout > %s
    """
    params = [room_num, room_num, checkout_str, checkin_str]
    if exclude_booking_id:
        sql += " AND id != %s"
        params.append(exclude_booking_id)

    rows = _run(sql, params, fetch="all") or []
    for r in rows:
        r["checkin"]  = str(r["checkin"])
        r["checkout"] = str(r["checkout"])
        if r.get("rooms") is None:
            r["rooms"] = [r["room"]] if r.get("room") else []
    return rows


def sync_room_statuses_sql():
    """
    Fast SQL room sync — one query per room instead of looping all bookings.
    """
    rooms = get_rooms()
    today = date.today()
    for r in rooms:
        if r.get("status") == "cleaning":
            continue
        status, _ = get_room_status_on_date_sql(r["num"], today)
        if r.get("status") != status:
            update_room_status(r["num"], status)

# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════
NOTIF_FILE = Path("data/notifications.json")

def create_notification(message, notif_type="info", category="general", booking_id=None):
    """
    notif_type: 'info' | 'warning' | 'critical'
    category:   'checkin' | 'checkout' | 'payment' | 'booking' | 'housekeeping' | 'general'
    """
    if MODE == "offline":
        notifs = _jload(NOTIF_FILE, [])
        new_id = max((n["id"] for n in notifs), default=0) + 1
        notifs.insert(0, {
            "id": new_id, "message": message, "type": notif_type,
            "category": category, "is_read": False,
            "booking_id": booking_id,
            "created_at": str(date.today())
        })
        _jsave(NOTIF_FILE, notifs)
        return
    _run("""INSERT INTO notifications (message, type, category, booking_id)
            VALUES (%s, %s, %s, %s)""",
         (message, notif_type, category, booking_id))

def get_notifications(limit=50):
    if MODE == "offline":
        return _jload(NOTIF_FILE, [])[:limit]
    rows = _run("""SELECT * FROM notifications
                   ORDER BY created_at DESC LIMIT %s""",
                (limit,), fetch="all") or []
    for r in rows:
        r["created_at"] = str(r["created_at"])[:16]  # trim seconds
    return rows

def get_unread_count():
    if MODE == "offline":
        return sum(1 for n in _jload(NOTIF_FILE, []) if not n.get("is_read"))
    row = _run("SELECT COUNT(*) as cnt FROM notifications WHERE is_read = FALSE",
               fetch="one")
    return row["cnt"] if row else 0

def mark_notification_read(nid):
    if MODE == "offline":
        notifs = _jload(NOTIF_FILE, [])
        for n in notifs:
            if n["id"] == nid:
                n["is_read"] = True
        _jsave(NOTIF_FILE, notifs)
        return
    _run("UPDATE notifications SET is_read = TRUE WHERE id = %s", (nid,))

def mark_all_read():
    if MODE == "offline":
        notifs = _jload(NOTIF_FILE, [])
        for n in notifs:
            n["is_read"] = True
        _jsave(NOTIF_FILE, notifs)
        return
    _run("UPDATE notifications SET is_read = TRUE")

def delete_notification(nid):
    if MODE == "offline":
        notifs = _jload(NOTIF_FILE, [])
        _jsave(NOTIF_FILE, [n for n in notifs if n["id"] != nid])
        return
    _run("DELETE FROM notifications WHERE id = %s", (nid,))

def clear_all_notifications():
    if MODE == "offline":
        _jsave(NOTIF_FILE, [])
        return
    _run("DELETE FROM notifications")

def generate_smart_alerts():
    """
    Auto-generate notifications for today's hotel operations.
    Call once per day or on manual refresh.
    Avoids duplicates by checking if same message exists today.
    """
    today = date.today()
    today_str = str(today)

    def already_exists(msg_fragment):
        if MODE == "offline":
            notifs = _jload(NOTIF_FILE, [])
            return any(msg_fragment in n.get("message","") and
                       today_str in n.get("created_at","")
                       for n in notifs)
        row = _run("""SELECT id FROM notifications
                      WHERE message ILIKE %s
                      AND DATE(created_at) = %s LIMIT 1""",
                   (f"%{msg_fragment}%", today), fetch="one")
        return row is not None

    # ── Check-ins today ───────────────────────────────────────────────────────
    if MODE == "online":
        checkins = _run("""SELECT guest, room FROM bookings
                           WHERE checkin = %s AND status = 'confirmed'""",
                        (today,), fetch="all") or []
    else:
        from datetime import datetime as dt
        all_b = _jload(BOOKINGS_FILE, [])
        checkins = [b for b in all_b
                    if b.get("checkin") == today_str and b.get("status") == "confirmed"]

    if checkins and not already_exists("check-in today"):
        names = ", ".join(b["guest"] for b in checkins[:3])
        extra = f" +{len(checkins)-3} more" if len(checkins) > 3 else ""
        create_notification(
            f"🟡 {len(checkins)} check-in{'s' if len(checkins)>1 else ''} today: {names}{extra}",
            "warning", "checkin"
        )

    # ── Check-outs today ──────────────────────────────────────────────────────
    if MODE == "online":
        checkouts = _run("""SELECT guest, room FROM bookings
                            WHERE checkout = %s AND status = 'checked-in'""",
                         (today,), fetch="all") or []
    else:
        checkouts = [b for b in all_b
                     if b.get("checkout") == today_str and b.get("status") == "checked-in"]

    if checkouts and not already_exists("checkout today"):
        names = ", ".join(b["guest"] for b in checkouts[:3])
        extra = f" +{len(checkouts)-3} more" if len(checkouts) > 3 else ""
        create_notification(
            f"🔴 {len(checkouts)} checkout{'s' if len(checkouts)>1 else ''} today: {names}{extra}",
            "critical", "checkout"
        )

    # ── Overdue checkouts ─────────────────────────────────────────────────────
    if MODE == "online":
        overdue = _run("""SELECT guest, room, checkout FROM bookings
                          WHERE checkout < %s AND status = 'checked-in'""",
                       (today,), fetch="all") or []
    else:
        from datetime import datetime as dt
        overdue = [b for b in all_b
                   if b.get("checkout","") < today_str and b.get("status") == "checked-in"]

    if overdue and not already_exists("overdue checkout"):
        names = ", ".join(b["guest"] for b in overdue[:3])
        create_notification(
            f"🔴 {len(overdue)} overdue checkout{'s' if len(overdue)>1 else ''}: {names}",
            "critical", "checkout"
        )

    # ── Pending payments (bills not paid after checkout) ──────────────────────
    if MODE == "online":
        pending_bills = _run("""SELECT guest, room FROM bills
                                WHERE status = 'Pending'""",
                             fetch="all") or []
    else:
        pending_bills = [b for b in _jload(BILLS_FILE, []) if b.get("status") == "Pending"]

    if pending_bills and not already_exists("pending payment"):
        create_notification(
            f"💳 {len(pending_bills)} pending payment{'s' if len(pending_bills)>1 else ''} — bills not yet settled",
            "warning", "payment"
        )
