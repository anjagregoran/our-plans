# -*- coding: utf-8 -*-
# Sunday WhatsApp for Anja & Drake. Sent as TWO messages (plans, then Croatian) so nothing is truncated.
import json, os, time, datetime, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
def load_json(name, default):
    for p in (os.path.join(HERE, name), name):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            pass
    return default

data = load_json("sets.json", {"general": [], "seasonal": {}})
GENERAL = data.get("general", [])
SEASONAL = data.get("seasonal", {})
EVENTS = load_json("events.json", [])

VERSES = [
    ("I can do all things through Christ which strengtheneth me.", "Philippians 4:13 (KJV)"),
    ("This is the day which the LORD hath made; we will rejoice and be glad in it.", "Psalm 118:24 (KJV)"),
    ("Be strong and of a good courage; be not afraid, neither be thou dismayed: for the LORD thy God is with thee whithersoever thou goest.", "Joshua 1:9 (KJV)"),
    ("In every thing give thanks: for this is the will of God in Christ Jesus concerning you.", "1 Thessalonians 5:18 (KJV)"),
    ("Commit thy works unto the LORD, and thy thoughts shall be established.", "Proverbs 16:3 (KJV)"),
    ("Charity suffereth long, and is kind.", "1 Corinthians 13:4 (KJV)"),
    ("Trust in the LORD with all thine heart; and lean not unto thine own understanding.", "Proverbs 3:5 (KJV)"),
    ("The LORD is my shepherd; I shall not want.", "Psalm 23:1 (KJV)"),
]
REMINDERS = [
    "Take a few minutes together to look at the week and breathe.",
    "Drink your water, rest well, and be kind to each other.",
    "Plan one little thing you are both looking forward to.",
    "Check in on how you are both feeling this week.",
]
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DOW_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def michigan_today():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/Detroit")).date()
    except Exception:
        return datetime.date.today()

def week_number(d): return (d - datetime.date(2026, 1, 1)).days // 7
def season_key(d):
    m = d.month
    if m == 12 or m <= 2: return "winter"
    if m <= 5: return "spring"
    if m <= 8: return "summer"
    return "autumn"
def holiday_key(d):
    m, day = d.month, d.day
    if m == 12 and 10 <= day <= 26: return "christmas"
    if (m == 12 and day >= 27) or (m == 1 and day <= 6): return "newyear"
    if m == 10 and day >= 24: return "halloween"
    if m == 2 and 7 <= day <= 16: return "valentine"
    if (m == 3 and day >= 25) or (m == 4 and day <= 22): return "easter"
    return None

def fetch_forecast(d):
    try:
        url = ("https://api.open-meteo.com/v1/forecast?latitude=42.03&longitude=-85.82"
               "&daily=weather_code,temperature_2m_max,temperature_2m_min"
               "&temperature_unit=fahrenheit&timezone=America%2FDetroit&forecast_days=7")
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.load(r)["daily"]
    except Exception:
        return None

def is_sunny_weekend(fc, d):
    if not fc: return False
    for i, ds in enumerate(fc["time"]):
        dt = datetime.date.fromisoformat(ds)
        if dt >= d and dt.weekday() in (5, 6) and fc["weather_code"][i] in (0, 1):
            return True
        if dt > d and dt.weekday() == 6:
            break
    return False

def weather_line(fc, d):
    if not fc: return None
    try:
        hi = fc["temperature_2m_max"]; code = fc["weather_code"]; times = fc["time"]
        highs = [h for h in hi if h is not None]
        if not highs: return None
        lo_h, hi_h = round(min(highs)), round(max(highs))
        best_i, best_score = None, None
        for i in range(len(times)):
            if datetime.date.fromisoformat(times[i]) < d: continue
            clear = 1 if (code[i] is not None and code[i] <= 2) else 0
            score = (clear, hi[i] if hi[i] is not None else -999)
            if best_score is None or score > best_score:
                best_score, best_i = score, i
        emoji = "☀️" if (best_score and best_score[0] == 1) else "\U0001f326️"
        s = f"{emoji} Weather in Michigan: highs around {lo_h}-{hi_h}°F this week"
        if best_i is not None:
            s += f", best day to get out looks like {DOW_FULL[datetime.date.fromisoformat(times[best_i]).weekday()]}"
        return s + "."
    except Exception:
        return None

def current_set(fc, d):
    hk = holiday_key(d)
    if hk: return SEASONAL[hk]
    if is_sunny_weekend(fc, d): return SEASONAL.get("sunny", GENERAL[0])
    idx = week_number(d) % (len(GENERAL) + 1)
    return GENERAL[idx] if idx < len(GENERAL) else SEASONAL[season_key(d)]

def week_events(d):
    out = []
    for e in EVENTS:
        try:
            ed = datetime.date.fromisoformat(e["date"])
        except Exception:
            continue
        if d <= ed <= d + datetime.timedelta(days=8):
            out.append((ed, e))
    out.sort(key=lambda x: x[0])
    return out

def build_main(d, fc):
    v, ref = VERSES[week_number(d) % len(VERSES)]
    rem = REMINDERS[week_number(d) % len(REMINDERS)]
    L = []
    L.append("Hey Drake and Anja, happy Sunday! \U0001f49b Get ready for the week ahead by looking at everything you have planned.")
    L.append("")
    L.append("\U0001f4d6 Verse of the week:")
    L.append('"' + v + '" - ' + ref)
    L.append("")
    L.append("\U0001f33f Reminder: " + rem)
    wl = weather_line(fc, d)
    if wl:
        L.append(""); L.append(wl)
    L.append("")
    L.append("\U0001f4c5 This week:")
    L.append("\U0001f4de Wed & Thu: Drake’s work calls")
    L.append("\U0001f9d6 Fri: sauna in the morning")
    L.append("⛪ Sun: church")
    for ed, e in week_events(d):
        label = DOW[ed.weekday()] + " " + str(ed.day) + " " + MON[ed.month - 1]
        tail = "  (maybe)" if e.get("maybe") else ""
        em = e.get("emoji", "•")
        L.append(f"{em} {label}: {e['title']}{tail}")
    L.append("")
    L.append("\U0001f4f2 Full calendar: https://anjagregoran.github.io/our-plans/")
    return "\n".join(L)

def build_croatian(d, fc):
    st = current_set(fc, d)
    L = []
    L.append("\U0001f1ed\U0001f1f7 Croatian this weekend (" + st["theme"] + "):")
    L.append("Five little words for Drake \U0001f49b")
    for i, w in enumerate(st["words"], 1):
        L.append("")
        L.append(f"{i}. {w['hr']} = {w['en']}  ({w['say']})")
        L.append(f"   {w['exHr']}  /  {w['exEn']}")
    return "\n".join(L)

def send(phone, key, text):
    if not phone or not key:
        print("skip: missing phone/key"); return
    q = urllib.parse.urlencode({"phone": phone, "text": text, "apikey": key})
    try:
        with urllib.request.urlopen("https://api.callmebot.com/whatsapp.php?" + q, timeout=30) as r:
            print("sent to", phone, "->", r.read().decode("utf-8", "ignore")[:90])
    except Exception as e:
        print("error sending to", phone, ":", e)

def main():
    d = michigan_today()
    fc = fetch_forecast(d)
    m1 = build_main(d, fc)
    m2 = build_croatian(d, fc)
    print("----- message 1 -----\n" + m1 + "\n----- message 2 -----\n" + m2 + "\n---------------------")
    recipients = [
        (os.environ.get("ANJA_PHONE"), os.environ.get("ANJA_KEY")),
        (os.environ.get("DRAKE_PHONE"), os.environ.get("DRAKE_KEY")),
    ]
    for phone, key in recipients:
        send(phone, key, m1)
        time.sleep(6)
        send(phone, key, m2)
        time.sleep(6)

if __name__ == "__main__":
    main()
