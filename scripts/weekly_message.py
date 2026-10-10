# -*- coding: utf-8 -*-
# Sends the weekly Anja & Drake WhatsApp (plans + 5 Croatian words) via CallMeBot.
# Runs on GitHub Actions every Sunday. Secrets come from env.
import json, os, time, datetime, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "sets.json"), encoding="utf-8"))
GENERAL = data["general"]
SEASONAL = data["seasonal"]

def michigan_today():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/Detroit")).date()
    except Exception:
        return datetime.date.today()

def week_number(d):
    return (d - datetime.date(2026, 1, 1)).days // 7

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

def is_sunny_weekend(d):
    try:
        url = ("https://api.open-meteo.com/v1/forecast?latitude=42.03&longitude=-85.82"
               "&daily=weather_code&timezone=America%2FDetroit&forecast_days=10")
        with urllib.request.urlopen(url, timeout=15) as r:
            j = json.load(r)
        t = j["daily"]["time"]; c = j["daily"]["weather_code"]
        for i, ds in enumerate(t):
            dd = datetime.date.fromisoformat(ds)
            if dd >= d and dd.weekday() in (5, 6) and c[i] in (0, 1):
                return True
            if dd > d and dd.weekday() == 6:
                break
    except Exception:
        pass
    return False

def current_set(d):
    hk = holiday_key(d)
    if hk: return SEASONAL[hk]
    if is_sunny_weekend(d): return SEASONAL["sunny"]
    idx = week_number(d) % (len(GENERAL) + 1)
    return GENERAL[idx] if idx < len(GENERAL) else SEASONAL[season_key(d)]

def build_message(d):
    st = current_set(d)
    L = []
    L.append("Anja & Drake, happy Sunday!")
    L.append("")
    L.append("This week:")
    L.append("- Wed & Thu: Drake's calls")
    L.append("- Fri morning: sauna")
    L.append("- Sun: church")
    L.append("")
    L.append("Croatian this weekend (" + st["theme"] + "):")
    for i, w in enumerate(st["words"], 1):
        L.append(f"{i}. {w['hr']} = {w['en']}  ({w['say']})")
        L.append(f"   {w['exHr']}  /  {w['exEn']}")
    L.append("")
    L.append("Full calendar: https://anjagregoran.github.io/our-plans/")
    return "\n".join(L)

def send(phone, key, text):
    if not phone or not key:
        print("skip: missing phone/key"); return
    q = urllib.parse.urlencode({"phone": phone, "text": text, "apikey": key})
    url = "https://api.callmebot.com/whatsapp.php?" + q
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            print("sent to", phone, "->", r.read().decode("utf-8", "ignore")[:120])
    except Exception as e:
        print("error sending to", phone, ":", e)

def main():
    d = michigan_today()
    msg = build_message(d)
    print("----- message -----")
    print(msg)
    print("-------------------")
    send(os.environ.get("ANJA_PHONE"), os.environ.get("ANJA_KEY"), msg)
    time.sleep(6)
    send(os.environ.get("DRAKE_PHONE"), os.environ.get("DRAKE_KEY"), msg)

if __name__ == "__main__":
    main()
