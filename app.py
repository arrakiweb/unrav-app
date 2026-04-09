import streamlit as st
import sqlite3
import pandas as pd
import datetime
import os
import matplotlib.pyplot as plt 
import calendar # Ditambahkan untuk kalender
from pdf_generator import generate_unrav_report, generate_finance_report 

# --- PENGATURAN DATABASE (v9.9 - TERBARU) ---
conn = sqlite3.connect('unrav_v7.db', check_same_thread=False)
c = conn.cursor()

# Inisialisasi Tabel
c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password TEXT, full_name TEXT, 
                pob TEXT, dob TEXT, gender TEXT, hobby TEXT, bio TEXT, 
                email TEXT, phone TEXT, notif_wa INTEGER, notif_tele INTEGER, 
                notif_email INTEGER, notif_desktop INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, task TEXT, group_name TEXT, 
                deadline TEXT, priority TEXT, status TEXT, notes TEXT, reminder INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS finance (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, type TEXT, amount REAL, 
                description TEXT, category TEXT, method TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, type TEXT, person TEXT, 
                total_amount REAL, purpose TEXT, date TEXT, method TEXT, 
                installment_scheme TEXT, installment_count INTEGER, 
                paid_count INTEGER DEFAULT 0, installment_amount REAL, 
                status TEXT, reminder INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT, content TEXT,
                category TEXT, date_created TEXT, location TEXT, link_task TEXT, link_finance TEXT, image_path TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, asset_name TEXT, 
                asset_type TEXT, value REAL, date_acquired TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, target_name TEXT, 
                amount REAL, deadline TEXT, frequency TEXT, reminder INTEGER)''')
conn.commit()

# --- MIGRASI DATABASE OTOMATIS ---
def migrate_db():
    try:
        # Menambahkan kolom username ke tabel yang belum punya
        for table in ['tasks', 'finance', 'debts', 'notes', 'assets', 'targets']:
            c.execute(f"PRAGMA table_info({table})")
            cols = [info[1] for info in c.fetchall()]
            if 'username' not in cols:
                c.execute(f"ALTER TABLE {table} ADD COLUMN username TEXT DEFAULT 'arraki'")
                
        # Migrasi Kolom Reminder Individual (Tugas, Tanggungan, Target)
        c.execute("PRAGMA table_info(tasks)")
        if 'reminder' not in [info[1] for info in c.fetchall()]:
            c.execute("ALTER TABLE tasks ADD COLUMN reminder INTEGER DEFAULT 1")
        
        c.execute("PRAGMA table_info(debts)")
        debts_cols = [info[1] for info in c.fetchall()]
        if 'total_amount' not in debts_cols:
            c.execute("ALTER TABLE debts ADD COLUMN total_amount REAL DEFAULT 0")
            c.execute("ALTER TABLE debts ADD COLUMN purpose TEXT DEFAULT '-'")
            c.execute("ALTER TABLE debts ADD COLUMN method TEXT DEFAULT '-'")
            c.execute("ALTER TABLE debts ADD COLUMN installment_scheme TEXT DEFAULT 'Tanpa Cicilan'")
            c.execute("ALTER TABLE debts ADD COLUMN installment_count INTEGER DEFAULT 1")
            c.execute("ALTER TABLE debts ADD COLUMN paid_count INTEGER DEFAULT 0")
            c.execute("ALTER TABLE debts ADD COLUMN installment_amount REAL DEFAULT 0")
            c.execute("UPDATE debts SET total_amount = amount")
        if 'reminder' not in debts_cols:
            c.execute("ALTER TABLE debts ADD COLUMN reminder INTEGER DEFAULT 1")
            
        c.execute("PRAGMA table_info(targets)")
        if 'reminder' not in [info[1] for info in c.fetchall()]:
            c.execute("ALTER TABLE targets ADD COLUMN reminder INTEGER DEFAULT 1")
        
        # Tabel Users (Sistem Notifikasi)
        c.execute("PRAGMA table_info(users)")
        users_cols = [info[1] for info in c.fetchall()]
        if 'notif_wa' not in users_cols:
            c.execute("ALTER TABLE users ADD COLUMN notif_wa INTEGER DEFAULT 0")
            c.execute("ALTER TABLE users ADD COLUMN notif_tele INTEGER DEFAULT 0")
            c.execute("ALTER TABLE users ADD COLUMN notif_email INTEGER DEFAULT 0")
            c.execute("ALTER TABLE users ADD COLUMN notif_desktop INTEGER DEFAULT 1")
            
        # Tabel Finance
        c.execute("PRAGMA table_info(finance)")
        if 'description' not in [info[1] for info in c.fetchall()]:
            c.execute("ALTER TABLE finance ADD COLUMN description TEXT DEFAULT '-'")

        # Tabel Notes (Sistem Rich Catatan)
        c.execute("PRAGMA table_info(notes)")
        notes_cols = [info[1] for info in c.fetchall()]
        if 'category' not in notes_cols:
            c.execute("ALTER TABLE notes ADD COLUMN category TEXT DEFAULT 'Umum'")
            c.execute("ALTER TABLE notes ADD COLUMN date_created TEXT DEFAULT '-'")
            c.execute("ALTER TABLE notes ADD COLUMN location TEXT DEFAULT '-'")
            c.execute("ALTER TABLE notes ADD COLUMN link_task TEXT DEFAULT '-'")
            c.execute("ALTER TABLE notes ADD COLUMN link_finance TEXT DEFAULT '-'")
            c.execute("ALTER TABLE notes ADD COLUMN image_path TEXT DEFAULT ''")
            
        conn.commit()
    except Exception as e:
        pass 

migrate_db()

c.execute("INSERT OR IGNORE INTO users (username, password, full_name, bio) VALUES ('arraki', 'unrav2024', 'Arraki', 'Mengurai benang kusut kehidupan.')")
conn.commit()

# Konfigurasi Halaman Dasar
favicon = "logo.png" if os.path.exists("logo.png") else "🧶"
st.set_page_config(page_title="UNRAV.ID", layout="wide", page_icon=favicon)

# --- FUNGSI PEMBANTU ---
def get_greeting():
    now = datetime.datetime.now()
    current_time = now.hour + (now.minute / 60.0)
    if current_time < 12: return "Selamat Pagi ☀️"
    elif current_time < 14.5: return "Selamat Siang 🌤️"
    elif current_time < 18.0: return "Selamat Sore 🌇"
    else: return "Selamat Malam 🌙"

def priority_val(p):
    if "1" in p: return 1
    if "2" in p: return 2
    if "3" in p: return 3
    return 4

def priority_icon(p):
    if "1" in p: return "🔴"
    if "2" in p: return "🟡"
    if "3" in p: return "🔵"
    return "⚪"

# Pemformatan Rupiah Rapi (Titik)
def format_rp(val):
    try: return f"Rp {float(val):,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return val

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'username' not in st.session_state: st.session_state['username'] = ""
if 'dark_mode' not in st.session_state: st.session_state['dark_mode'] = False
if 'flash_msg' not in st.session_state: st.session_state['flash_msg'] = None
if 'flash_type' not in st.session_state: st.session_state['flash_type'] = None

def show_flash_messages():
    if st.session_state['flash_msg']:
        if st.session_state['flash_type'] == 'success': st.success(st.session_state['flash_msg'])
        elif st.session_state['flash_type'] == 'error': st.error(st.session_state['flash_msg'])
        elif st.session_state['flash_type'] == 'warning': st.warning(st.session_state['flash_msg'])
        st.session_state['flash_msg'] = None
        st.session_state['flash_type'] = None

# --- CSS GLOBAL ---
css_kustom = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
html, body, p, h1, h2, h3, h4, h5, h6, label, input, select, textarea { font-family: 'Poppins', sans-serif !important; }
.block-container { padding-top: 3rem !important; padding-bottom: 0rem !important; }
h2 { font-size: 1.5rem !important; padding-bottom: 0.2rem !important; }
h3 { font-size: 1.25rem !important; }
[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
"""
if st.session_state['dark_mode']:
    css_kustom += """
    .stApp, header { background-color: #121212 !important; }
    [data-testid="stSidebar"] { background-color: #1E1E1E !important; }
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, 
    .stApp label, .stApp span:not(.material-symbols-rounded), .stApp li, [data-testid="stMarkdownContainer"] { color: #F8F9FA !important; }
    [data-testid="stMetricLabel"] > div > div > p, [data-testid="stMetricValue"] > div { color: #F8F9FA !important; }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, 
    .stSelectbox>div>div>select, .stDateInput>div>div>input { background-color: #2D2D2D !important; color: #F8F9FA !important; border: 1px solid #555 !important; }
    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button { background-color: #2D2D2D !important; color: #F8F9FA !important; border: 1px solid #555555 !important; }
    .stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover { background-color: #3D3D3D !important; border-color: #4DA8DA !important; color: #4DA8DA !important; }
    [data-baseweb="tab"] { color: #F8F9FA !important; background-color: transparent !important; }
    table th, table td { color: #F8F9FA !important; background-color: #1E1E1E !important; }
    [data-testid="stDataFrame"] { color: #F8F9FA !important; }
    """
st.markdown(f"<style>{css_kustom}</style>", unsafe_allow_html=True)

# ==========================================
# HALAMAN DEPAN (LOGIN)
# ==========================================
if not st.session_state['logged_in']:
    show_flash_messages()
    
    primary_color = "#4DA8DA" if st.session_state['dark_mode'] else "#003366"
    text_color = "white" if st.session_state['dark_mode'] else "#121212"
    muted_text = "#A0A0A0" if st.session_state['dark_mode'] else "#555555"
    
    css_login = f"""
    <style>
    /* Mengamankan agar layout kanan kiri sejajar di tengah */
    div[data-testid="stHorizontalBlock"] {{ align-items: center !important; }}
    
    /* Tombol Custom Login */
    div.stButton > button[kind="primary"] {{ background-color: {primary_color} !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }}
    div.stButton > button[kind="primary"]:hover {{ opacity: 0.8 !important; }}
    </style>
    """
    st.markdown(css_login, unsafe_allow_html=True)
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    
    col_kiri, space, col_kanan = st.columns([1, 0.1, 1.2])
    
    with col_kiri:
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c2:
            if os.path.exists("logo.png"):
                st.image("logo.png", use_container_width=True)
            else:
                st.markdown("<h1 style='text-align:center; font-size: 5rem; margin:0;'>🧶</h1>", unsafe_allow_html=True)
                
        st.markdown(f"<h2 style='text-align: center; margin-top: 10px; margin-bottom: 0; font-weight: 800; color: {text_color};'>UNRAV.ID</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: {muted_text}; margin-bottom: 1.5rem;'><i>Unravel, Focus, and Productive</i></p>", unsafe_allow_html=True)
        
        c1_t, c2_t, c3_t = st.columns([1, 1.2, 1])
        with c2_t:
            dm_toggle = st.toggle("🌙 Mode Gelap", value=st.session_state['dark_mode'])
            if dm_toggle != st.session_state['dark_mode']:
                st.session_state['dark_mode'] = dm_toggle
                st.rerun()
                
        st.markdown(f"<br><p style='text-align: center; font-size: 0.8rem; color: {muted_text}; margin-bottom: 0; margin-top: 2rem;'><i>Created by ArrakiWeb - UNRAV.ID v1.0</i></p>", unsafe_allow_html=True)

    with col_kanan:
        st.markdown(f"<h1 style='color: {primary_color}; font-weight: 800; font-size: 2.2rem; margin-bottom: 1rem;'>UNRAV.ID</h1>", unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔑 Masuk", "📝 Daftar", "🔐 Lupa", "📖 Bantuan", "ℹ️ About"])
        with tab1:
            st.write("")
            user = st.text_input("Username", key="login_user")
            pw = st.text_input("Password", type="password", key="login_pw")
            if st.button("Masuk", use_container_width=True, type="primary"):
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw))
                if c.fetchone():
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user
                    st.session_state['flash_msg'] = "Berhasil Login!"
                    st.session_state['flash_type'] = "success"
                    st.rerun()
                else: st.error("Username atau Password salah.")
        
        with tab2:
            st.subheader("Daftar Akun Baru")
            reg_user = st.text_input("Username Baru", key="r_u")
            reg_name = st.text_input("Nama Lengkap", key="r_n")
            reg_email = st.text_input("Email", key="r_e")
            reg_pw = st.text_input("Password", type="password", key="r_p")
            if st.button("Buat Akun", use_container_width=True):
                if not reg_user or not reg_pw: st.error("Username dan Password wajib diisi!")
                else:
                    try:
                        c.execute("INSERT INTO users (username, password, full_name, email) VALUES (?,?,?,?)", (reg_user, reg_pw, reg_name, reg_email))
                        conn.commit()
                        st.success("Akun dibuat! Silakan Masuk di tab sebelah.")
                        st.info(f"📧 [Sistem] Email berisi link aktivasi akun telah berhasil dikirimkan ke kotak masuk **{reg_email}**.")
                    except sqlite3.IntegrityError: st.error("Gagal! Username sudah terpakai.")
        
        with tab3:
            st.subheader("Pulihkan Password")
            fp_user = st.text_input("Username", key="fp_u")
            fp_email = st.text_input("Email", key="fp_e")
            fp_new_pw = st.text_input("Password Baru", type="password", key="fp_p")
            if st.button("Reset", use_container_width=True):
                if c.execute("SELECT * FROM users WHERE username=? AND email=?", (fp_user, fp_email)).fetchone():
                    c.execute("UPDATE users SET password=? WHERE username=?", (fp_new_pw, fp_user))
                    conn.commit()
                    st.success("Berhasil! Silakan login.")
                else: st.error("Data tidak cocok.")
        with tab4:
            st.subheader("📖 Panduan")
            st.write("1. Buat akun di tab Daftar.\n2. Lakukan login.\n3. Akses Dashboard untuk pantau produktivitas dan uang Anda.")
        with tab5:
            st.subheader("ℹ️ Tentang")
            st.write("Dibangun oleh **ArrakiWeb** (2026) untuk meringankan beban pikiran anda yang menumpuk. UNRAV berasal dari kata UNRAVEL yang berarti mengurai. Jika tugas-tugas anda tertumpuk serta tanggungan anda tak karuan sehingga menjadi benang kusut, UNRAV membantu anda untuk mengurainya. Setelah mengurai, diharapkan anda bisa fokus dan semakin produktif.")

# ==========================================
# HALAMAN UTAMA (DASHBOARD DLL)
# ==========================================
else:
    user_name = st.session_state['username']
    user_data = c.execute("SELECT * FROM users WHERE username=?", (user_name,)).fetchone()
    u_display_name = user_data[2] if user_data[2] else user_data[0]
    u_display_bio = user_data[7] if user_data[7] else "Belum ada bio."
    u_email = user_data[8] if user_data[8] else "-"
    u_phone = user_data[9] if user_data[9] else "-"
    desktop_notif = user_data[13] if len(user_data) > 13 else 1 # Cek preferensi notifikasi Desktop
    profile_pic_path = f"profile_{user_name}.png"

    # --- PENGINGAT NOTIFIKASI DESKTOP OTOMATIS (DENGAN SNOOZE) ---
    if desktop_notif == 1:
        besok = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        tugas_besok = c.execute("SELECT task FROM tasks WHERE username=? AND deadline LIKE ? AND status='Pending' AND reminder=1", (user_name, f"{besok}%")).fetchall()
        
        if tugas_besok:
            if 'notif_status' not in st.session_state: st.session_state['notif_status'] = "active"
            if 'notif_snooze_time' not in st.session_state: st.session_state['notif_snooze_time'] = datetime.datetime.now()
            if 'notif_date' not in st.session_state: st.session_state['notif_date'] = besok
            
            # Reset notif jika harinya ganti
            if st.session_state['notif_date'] != besok:
                st.session_state['notif_status'] = "active"
                st.session_state['notif_date'] = besok
                st.session_state['audio_played'] = False
                
            now_time = datetime.datetime.now()
            if st.session_state['notif_status'] == "snoozed" and now_time >= st.session_state['notif_snooze_time']:
                st.session_state['notif_status'] = "active"
                st.session_state['audio_played'] = False
                
            if st.session_state['notif_status'] == "active":
                if 'audio_played' not in st.session_state or not st.session_state['audio_played']:
                    st.markdown("""<audio autoplay style="display:none;"><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)
                    st.session_state['audio_played'] = True
                    
                st.warning("🔔 **PENGINGAT: Ada Deadline Besok!**")
                for t in tugas_besok:
                    st.write(f"- {t[0]}")
                
                # Fitur Snooze Fleksibel (Dropdown Menit/Jam)
                st.write("Tindakan:")
                c_n1, c_n2, c_n3, c_n4 = st.columns([1.5, 2, 1.5, 4])
                
                if c_n1.button("❌ Tutup", key="btn_dismiss_notif", use_container_width=True):
                    st.session_state['notif_status'] = "dismissed"
                    st.rerun()
                    
                snooze_options = ["5 Menit", "10 Menit", "30 Menit", "1 Jam", "1 Hari"]
                snooze_val = c_n2.selectbox("Waktu Tunda", snooze_options, label_visibility="collapsed")
                
                if c_n3.button("💤 Tunda", key="btn_snooze_notif", use_container_width=True):
                    mins_dict = {"5 Menit": 5, "10 Menit": 10, "30 Menit": 30, "1 Jam": 60, "1 Hari": 1440}
                    st.session_state['notif_status'] = "snoozed"
                    st.session_state['notif_snooze_time'] = now_time + datetime.timedelta(minutes=mins_dict[snooze_val])
                    st.rerun()
                    
                st.markdown("---")

    # --- SIDEBAR & NAVIGASI ---
    col_logo, col_text = st.sidebar.columns([1, 4]) 
    with col_logo:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        else: st.markdown("<h2 style='margin-top:0px;'>🧶</h2>", unsafe_allow_html=True)
    with col_text:
        st.markdown("""<div style="line-height: 1.2; margin-top: 5px;"><b style="font-size: 1.2rem;">UNRAV.ID</b><br><span style="font-size: 0.75rem; color: #A0A0A0;">Uraikan, Fokus, dan Produktif</span></div>""", unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    sb_pic1, sb_pic2, sb_pic3 = st.sidebar.columns([1, 2, 1])
    with sb_pic2:
        if os.path.exists(profile_pic_path): st.image(profile_pic_path, use_container_width=True)
        else: st.image("https://api.dicebear.com/7.x/initials/png?seed=" + u_display_name, use_container_width=True)
        
    st.sidebar.markdown(f"<h4 style='text-align: center; margin-bottom:0;'>👤 {u_display_name}</h4>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<div style='text-align: center; font-size: 12px; color: gray; margin-bottom: 10px;'>*{u_display_bio}*</div>", unsafe_allow_html=True)
    
    dm_toggle_in = st.sidebar.toggle("🌙 Mode Gelap", value=st.session_state['dark_mode'])
    if dm_toggle_in != st.session_state['dark_mode']:
        st.session_state['dark_mode'] = dm_toggle_in
        st.rerun()
        
    st.sidebar.markdown("---")
    menu = ["📊 Dashboard", "🎯 Rencana & Tugas", "📅 Kalender", "💰 Keuangan", "📝 Catatan", "⚙️ Pengaturan Profil"]
    choice = st.sidebar.radio("Navigasi Utama", menu, key="menu_utama")
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.rerun()

    show_flash_messages()

    # --- 1. DASHBOARD ---
    if choice == "📊 Dashboard":
        st.title(f"{get_greeting()}, {u_display_name}!")
        st.write(f"🕒 **{datetime.datetime.now().strftime('%H:%M')}** | 📍 Malang, Indonesia")
        st.markdown("---")
        
        dash_kiri, dash_kanan = st.columns([1, 1])
        with dash_kiri:
            st.header("🎯 Analitik Kegiatan")
            df_tasks = pd.read_sql_query("SELECT * FROM tasks WHERE username=?", conn, params=(user_name,))
            if not df_tasks.empty:
                df_pending = df_tasks[df_tasks['status'] == 'Pending'].copy()
                df_pending['is_overdue'] = pd.to_datetime(df_pending['deadline'], errors='coerce').dt.date < datetime.datetime.now().date()
                overdue_count = df_pending['is_overdue'].sum()
                if overdue_count > 0:
                    st.error(f"🚨 Perhatian! Anda punya {overdue_count} kegiatan yang MELEWATI DEADLINE/WAKTU.")
                
                st.subheader("📌 Prioritas Utama (Pending)")
                if not df_pending.empty:
                    df_pending['p_val'] = df_pending['priority'].apply(priority_val)
                    df_prio = df_pending.sort_values(by=['p_val', 'deadline']).head(5)
                    df_prio['P'] = df_prio['priority'].apply(priority_icon)
                    st.table(df_prio[['P', 'task', 'deadline', 'group_name']])
            else: st.info("Belum ada data tugas untuk dianalisis.")

        with dash_kanan:
            st.header("💰 Ringkasan Keuangan")
            df_fin = pd.read_sql_query("SELECT * FROM finance WHERE username=?", conn, params=(user_name,))
            inc = df_fin[df_fin['type'] == 'Pemasukan']['amount'].sum() if not df_fin.empty else 0
            exp = df_fin[df_fin['type'] == 'Pengeluaran']['amount'].sum() if not df_fin.empty else 0
            
            c_m1, c_m2 = st.columns(2)
            c_m1.metric("Pemasukan", format_rp(inc))
            c_m2.metric("Pengeluaran", format_rp(exp))
            st.metric("Saldo Netto", format_rp(inc - exp))
            
            df_debts = pd.read_sql_query("SELECT * FROM debts WHERE status != 'Lunas' AND username=?", conn, params=(user_name,))
            if not df_debts.empty:
                df_debts['sisa'] = df_debts['total_amount'] - (df_debts['paid_count'] * df_debts['installment_amount'])
                tot_tunggak = df_debts[df_debts['type'] != 'Piutang']['sisa'].sum()
                if tot_tunggak > 0:
                    st.error(f"⚠️ Hutang & Tunggakan: {format_rp(tot_tunggak)}")
                    st.dataframe(df_debts[['type', 'person', 'sisa']], hide_index=True)
            else: 
                st.success("Semua tanggungan lunas!")
            
        st.markdown("---")
        st.header("📈 Visualisasi Data")
        chart_kiri, chart_kanan = st.columns([1, 1])
        with chart_kiri:
            st.subheader("📊 Distribusi Kegiatan")
            if not df_tasks.empty:
                task_counts = df_tasks['group_name'].value_counts().reset_index()
                task_counts.columns = ['Kelompok', 'Jumlah']
                st.bar_chart(task_counts.set_index('Kelompok'))
            else: st.info("Tambahkan kegiatan untuk melihat grafik.")
                
        with chart_kanan:
            st.subheader("📉 Pengeluaran Terbanyak")
            if not df_fin.empty:
                df_exp_only = df_fin[df_fin['type'] == 'Pengeluaran']
                if not df_exp_only.empty:
                    exp_by_cat = df_exp_only.groupby('category')['amount'].sum().reset_index()
                    st.bar_chart(exp_by_cat.set_index('category'))
                else: st.info("Belum ada data pengeluaran.")

    # --- 2. RENCANA & TUGAS ---
    elif choice == "🎯 Rencana & Tugas":
        st.header("🎯 Manajemen Tugas & Jadwal")
        t1, t2, t3, t4 = st.tabs(["➕ Tambah", "📋 Cards View", "⚙️ Edit & Hapus", "📊 Laporan"])
        
        with t1:
            col_t_left, col_t_right = st.columns([1, 1.2])
            with col_t_left:
                with st.form("add_t"):
                    st.subheader("Form Rencana & Tugas")
                    t_jenis = st.selectbox("Jenis Entri", ["Tugas", "Kegiatan / Jadwal"])
                    t_n = st.text_input("Nama Tugas / Kegiatan")
                    t_g = st.text_input("Kelompok")
                    col_d1, col_d2 = st.columns(2)
                    t_d = col_d1.date_input("Tanggal Pelaksanaan / Deadline")
                    t_waktu = col_d2.time_input("Jam", value=datetime.time(8, 0))
                    t_p = st.select_slider("Prioritas", options=["4 - Santai", "3 - Menengah", "2 - Penting", "1 - KRITIS"])
                    
                    # Opsi Pengingat Individual
                    st.markdown("---")
                    t_remind = st.checkbox("🔔 Aktifkan Pengingat Notifikasi untuk Tugas ini", value=True)
                    
                    if st.form_submit_button("Simpan", use_container_width=True):
                        if t_n.strip() == "": st.error("Nama tidak boleh kosong!")
                        else:
                            try:
                                waktu_lengkap = f"{t_d} {t_waktu.strftime('%H:%M')}"
                                nama_final = f"[{t_jenis}] {t_n}"
                                c.execute("INSERT INTO tasks (username, task, group_name, deadline, priority, status, reminder) VALUES (?,?,?,?,?,?,?)", 
                                          (user_name, nama_final, t_g, waktu_lengkap, t_p, "Pending", int(t_remind)))
                                conn.commit()
                                st.session_state['flash_msg'] = f"{t_jenis} '{t_n}' berhasil ditambahkan!"
                                st.session_state['flash_type'] = "success"
                                st.rerun()
                            except Exception as e: st.error(f"Gagal menambah data: {e}")
            with col_t_right:
                st.write("📌 **Tugas/Kegiatan yang Baru Ditambahkan**")
                recent_tasks = pd.read_sql_query("SELECT task AS Tugas, deadline AS Deadline, priority AS Prioritas FROM tasks WHERE username=? ORDER BY id DESC LIMIT 5", conn, params=(user_name,))
                if not recent_tasks.empty: st.dataframe(recent_tasks, hide_index=True, use_container_width=True)
                else: st.caption("Belum ada data yang ditambahkan.")
        
        with t2:
            groups = pd.read_sql_query("SELECT DISTINCT group_name FROM tasks WHERE username=?", conn, params=(user_name,))
            if not groups.empty:
                cols = st.columns(3)
                border_colors = ["#FF4B4B", "#0068C9", "#29B5E8", "#00C250", "#FFB703", "#9D4EDD"] 
                for i, row in groups.iterrows():
                    with cols[i % 3]:
                        g_name = row['group_name'] if row['group_name'] else "Tanpa Kelompok"
                        color = border_colors[i % len(border_colors)]
                        tasks_in_group = pd.read_sql_query("SELECT id, task, priority FROM tasks WHERE group_name=? AND status='Pending' AND username=? LIMIT 5", conn, params=(g_name, user_name))
                        task_html = ""
                        if tasks_in_group.empty: task_html = "<p style='color:gray; font-size:12px;'>Tidak ada tugas pending.</p>"
                        else:
                            for _, tr in tasks_in_group.iterrows():
                                icon = priority_icon(tr['priority'])
                                # Font Size Diperbesar Menjadi 17px
                                task_html += f"<div style='margin-bottom: 8px; font-size: 17px; font-weight: 600;'>{icon} {tr['task']} <span style='color:gray; font-weight: normal; font-size:11px;'>(ID:{tr['id']})</span></div>"
                        card_html = f"""<div style="border: 2px solid {color}; border-radius: 12px; padding: 15px; margin-bottom: 20px; background-color: transparent;"><h4 style="margin-top:0; margin-bottom:5px;">📦 {g_name}</h4><hr style="margin: 5px 0 10px 0; border-color: {color}; opacity: 0.3;">{task_html}</div>"""
                        st.markdown(card_html, unsafe_allow_html=True)
            else: st.info("Belum ada rencana atau tugas yang dicatat.")
        
        with t3:
            col_e_left, col_e_right = st.columns([1, 1])
            with col_e_left:
                st.subheader("Ubah Status / Hapus Tugas")
                e_id = st.number_input("ID Tugas (Bisa Dilihat di Tab Laporan/Cards)", min_value=1, step=1)
                if st.button("Cek Data"):
                    # MENCEGAH BUG: Mengambil kolom spesifik, bukan SELECT *, agar kebal terhadap perubahan susunan database
                    if res := c.execute("SELECT task, group_name, deadline, priority, status, reminder FROM tasks WHERE id=? AND username=?", (e_id, user_name)).fetchone(): 
                        st.session_state['edit_t'] = res
                    else: st.warning("ID Tugas tidak ditemukan / milik akun lain.")
                
                if 'edit_t' in st.session_state:
                    edit_data = st.session_state['edit_t']
                    
                    try:
                        dt_obj = datetime.datetime.strptime(edit_data[2], "%Y-%m-%d %H:%M")
                        e_date = dt_obj.date()
                        e_time = dt_obj.time()
                    except:
                        e_date = datetime.datetime.now().date()
                        e_time = datetime.datetime.now().time()
                        
                    with st.form("edit_t_form"):
                        new_task = st.text_input("Nama Tugas / Kegiatan", value=edit_data[0])
                        new_group = st.text_input("Kategori / Kelompok", value=edit_data[1])
                        
                        col_d1, col_d2 = st.columns(2)
                        new_date = col_d1.date_input("Tanggal Pelaksanaan / Deadline", value=e_date)
                        new_time = col_d2.time_input("Jam", value=e_time)
                        
                        priority_opts = ["4 - Santai", "3 - Menengah", "2 - Penting", "1 - KRITIS"]
                        try:
                            p_index = priority_opts.index(edit_data[3])
                        except:
                            p_index = 0
                        new_prio = st.select_slider("Prioritas", options=priority_opts, value=priority_opts[p_index])
                        
                        new_stat = st.selectbox("Status", ["Pending", "Selesai"], index=0 if edit_data[4] == "Pending" else 1)
                        
                        st.markdown("---")
                        new_remind = st.checkbox("🔔 Aktifkan Pengingat Notifikasi untuk Tugas ini", value=bool(edit_data[5]))
                        
                        btn_update = st.form_submit_button("Update Perubahan", use_container_width=True)
                        
                        if btn_update:
                            try:
                                new_deadline = f"{new_date} {new_time.strftime('%H:%M')}"
                                c.execute("UPDATE tasks SET task=?, group_name=?, deadline=?, priority=?, status=?, reminder=? WHERE id=? AND username=?", 
                                          (new_task, new_group, new_deadline, new_prio, new_stat, int(new_remind), e_id, user_name))
                                conn.commit()
                                del st.session_state['edit_t']
                                st.session_state['flash_msg'] = f"Tugas ID {e_id} berhasil diperbarui!"
                                st.session_state['flash_type'] = "success"
                                st.rerun()
                            except Exception as e: st.error(f"Gagal mengupdate tugas: {e}")
                            
                    # Tombol Hapus (Di luar form agar tidak bentrok validasi)
                    st.write("")
                    if st.button("🗑️ Hapus Permanen Tugas Ini", type="primary", use_container_width=True):
                        c.execute("DELETE FROM tasks WHERE id=? AND username=?", (e_id, user_name))
                        conn.commit()
                        del st.session_state['edit_t']
                        st.session_state['flash_msg'] = f"Tugas ID {e_id} berhasil dihapus!"
                        st.session_state['flash_type'] = "success"
                        st.rerun()

            with col_e_right: 
                st.info("ℹ️ **Cara Menggunakan Fitur Ini:**\n\n1. Lihat **ID Tugas** pada tulisan kecil abu-abu di dalam tab *Cards View*.\n2. Masukkan angka ID tersebut, klik **Cek Data**.\n3. Jika ingin merubah judul, kategori, jadwal, prioritas, atau menyatakan tugas sudah selesai, atur datanya lalu klik **Update Perubahan**.\n4. Jika tugas salah input atau ingin dihapus total dari riwayat, klik tombol merah **Hapus Permanen Tugas Ini** di paling bawah.")
        
        with t4:
            df_all_t = pd.read_sql_query("SELECT * FROM tasks WHERE username=?", conn, params=(user_name,))
            if not df_all_t.empty:
                df_all_t['deadline_date'] = pd.to_datetime(df_all_t['deadline'], errors='coerce').dt.date
                now_date = datetime.datetime.now().date()
                
                group_counts = df_all_t['group_name'].value_counts()
                terlewat = df_all_t[(df_all_t['status'] == 'Pending') & (df_all_t['deadline_date'] < now_date)]
                ke_depan = df_all_t[(df_all_t['status'] == 'Pending') & (df_all_t['deadline_date'] >= now_date) & (df_all_t['deadline_date'] <= now_date + datetime.timedelta(days=3))]
                prioritas = df_all_t[(df_all_t['status'] == 'Pending') & (df_all_t['priority'].str.contains("1"))]
                
                st.write("📌 **Ringkasan Data Kegiatan:**")
                sum_col1, sum_col2, sum_col3 = st.columns(3)
                sum_col1.metric("Kritis (Prioritas 1)", len(prioritas))
                sum_col2.metric("Terlewat Deadline", len(terlewat))
                sum_col3.metric("Mendesak (H+3)", len(ke_depan))
                st.markdown("---")
                
                fig_prio, ax1 = plt.subplots(figsize=(5, 4))
                df_all_t['priority'].value_counts().sort_index().plot(kind='bar', ax=ax1, color='#4F46E5')
                ax1.set_title("Distribusi Prioritas Tugas", fontsize=10)
                plt.xticks(rotation=15, fontsize=8)
                fig_prio.tight_layout()
                fig_prio.savefig("chart_prioritas.png") 

                fig_kat, ax2 = plt.subplots(figsize=(5, 4))
                df_all_t['group_name'].value_counts().plot(kind='pie', ax=ax2, autopct='%1.1f%%', textprops={'fontsize': 8})
                ax2.set_ylabel("")
                ax2.set_title("Kategori Tugas Terbanyak", fontsize=10)
                fig_kat.tight_layout()
                fig_kat.savefig("chart_kategori.png") 

                fig_trend, ax3 = plt.subplots(figsize=(10, 3))
                df_trend = df_all_t.groupby('deadline_date').size()
                df_trend.plot(kind='line', ax=ax3, marker='o', color='#FF4B4B')
                ax3.set_title("Trend Kepadatan Deadline/Jadwal", fontsize=10)
                ax3.set_xlabel("Tanggal", fontsize=8)
                ax3.set_ylabel("Jumlah Data", fontsize=8)
                plt.xticks(fontsize=8)
                fig_trend.tight_layout()
                fig_trend.savefig("chart_trend.png") 

                st.write("📈 **Visualisasi Analisis Tugas & Jadwal**")
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1: st.pyplot(fig_prio)
                with col_chart2: st.pyplot(fig_kat)
                st.pyplot(fig_trend)
                st.markdown("---")
                
                col_tabel1, col_tabel2 = st.columns(2)
                with col_tabel1:
                    st.error(f"🚨 **Terlewat Waktu ({len(terlewat)})**")
                    if not terlewat.empty: st.dataframe(terlewat[['id', 'task', 'deadline']], hide_index=True, use_container_width=True)
                    else: st.caption("Aman, tidak ada yang terlewat.")
                with col_tabel2:
                    st.warning(f"⏳ **Segera Datang / H+3 ({len(ke_depan)})**")
                    if not ke_depan.empty: st.dataframe(ke_depan[['id', 'task', 'deadline']], hide_index=True, use_container_width=True)
                    else: st.caption("Tidak ada hal mendesak dalam waktu dekat.")
                st.markdown("---")
                
                user_dict = {
                    "nama_lengkap": u_display_name,
                    "username": f"@{user_name}",
                    "kontak": f"{u_email} / {u_phone}",
                    "tanggal_cetak": datetime.datetime.now().strftime("%d %B %Y")
                }
                tasks_list = [{"no": i + 1, "nama": row['task'], "deadline": row['deadline'], "prioritas": row['priority'].split(' - ')[1] if ' - ' in row['priority'] else row['priority'], "status": row['status']} for i, row in df_all_t.iterrows()]
                kumpulan_gambar = ["chart_prioritas.png", "chart_kategori.png", "chart_trend.png"]

                try:
                    pdf_filename = generate_unrav_report(user_dict, tasks_list, chart_images=kumpulan_gambar)
                    with open(pdf_filename, "rb") as f: pdf_bytes = f.read()
                    st.write("📥 **Unduh Laporan Analitik Lengkap**")
                    st.download_button(label="Download Laporan UNRAV.ID (PDF + Visualisasi)", data=pdf_bytes, file_name="Laporan_Lengkap_UNRAV.pdf", mime="application/pdf", type="primary")
                except Exception as e: st.error(f"Gagal generate PDF: {e}")
            else: st.info("Belum ada data kegiatan untuk dilaporkan.")

    # --- MENU BARU: KALENDER ---
    elif choice == "📅 Kalender":
        st.header("📅 Kalender Kegiatan & Keuangan")
        st.write("Pantau seluruh jadwal rencana kegiatan, tugas, dan tagihan Anda di satu tempat.")
        
        now = datetime.datetime.now()
        col_y, col_m = st.columns(2)
        sel_year = col_y.selectbox("Pilih Tahun", range(now.year - 5, now.year + 6), index=5)
        sel_month = col_m.selectbox("Pilih Bulan", range(1, 13), index=now.month - 1)
        
        df_t = pd.read_sql_query("SELECT task, deadline FROM tasks WHERE username=?", conn, params=(user_name,))
        df_d = pd.read_sql_query("SELECT type, purpose, date FROM debts WHERE username=? AND status!='Lunas'", conn, params=(user_name,))
        
        cal = calendar.monthcalendar(sel_year, sel_month)
        days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        
        # Header Kalender
        cols = st.columns(7)
        for i, day in enumerate(days):
            cols[i].markdown(f"<div style='text-align:center; font-weight:bold; background-color:#4DA8DA; color:white; padding:5px; border-radius:5px;'>{day}</div>", unsafe_allow_html=True)
            
        # Body Kalender
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    day_str = f"{sel_year}-{sel_month:02d}-{day:02d}"
                    t_events = df_t[df_t['deadline'].str.startswith(day_str, na=False)] if not df_t.empty else pd.DataFrame()
                    d_events = df_d[df_d['date'] == day_str] if not df_d.empty else pd.DataFrame()
                    
                    with cols[i].container():
                        st.markdown(f"<div style='border:1px solid #CCC; border-radius:5px; padding:5px; min-height:100px;'><b>{day}</b>", unsafe_allow_html=True)
                        for _, r in t_events.iterrows():
                            st.caption(f"📌 {r['task']}")
                        for _, r in d_events.iterrows():
                            st.caption(f"💰 {r['type']}: {r['purpose']}")
                        st.markdown("</div>", unsafe_allow_html=True)

    # --- 3. KEUANGAN ---
    elif choice == "💰 Keuangan":
        st.header("💰 Manajemen Keuangan Terpadu")
        tab_in, tab_out, tab_debt, tab_asset, tab_target, tab_edit_fin, tab_report = st.tabs(["📥 Masuk", "📤 Keluar", "🤝 Tanggungan", "💎 Aset", "🎯 Target Impian", "⚙️ Edit / Hapus", "📊 Laporan"])

        with tab_in:
            col_in_left, col_in_right = st.columns([1, 1.2])
            with col_in_left:
                with st.form("form_masuk"):
                    st.subheader("Catat Pemasukan")
                    col1, col2 = st.columns(2)
                    f_desc = col1.text_input("Uang Apa (Deskripsi)")
                    f_amt = col2.number_input("Jumlah (Rp)", min_value=0, step=1000)
                    f_cat = col1.text_input("Kategori (Bebas Isi)", placeholder="Misal: Gaji, Project...")
                    f_met = col2.text_input("Metode (Tunai/Transfer)")
                    f_date = st.date_input("Tanggal", key="in_date")
                    if st.form_submit_button("Simpan Uang Masuk", use_container_width=True):
                        c.execute("INSERT INTO finance (username, type, amount, description, category, method, date) VALUES (?,?,?,?,?,?,?)", 
                                  (user_name, "Pemasukan", f_amt, f_desc, f_cat if f_cat else "Lainnya", f_met, str(f_date)))
                        conn.commit()
                        st.session_state['flash_msg'] = "Pemasukan berhasil dicatat!"
                        st.session_state['flash_type'] = "success"
                        st.rerun()
            with col_in_right:
                st.write("📌 **Daftar Pemasukan Terbaru**")
                df_in = pd.read_sql_query("SELECT id as ID, date as Tanggal, description as Deskripsi, category as Kategori, amount as Nominal FROM finance WHERE type='Pemasukan' AND username=? ORDER BY id DESC", conn, params=(user_name,))
                if not df_in.empty: 
                    df_in['Nominal'] = df_in['Nominal'].apply(format_rp)
                    st.dataframe(df_in, hide_index=True, use_container_width=True)
                else: st.caption("Belum ada data pemasukan.")

        with tab_out:
            col_out_left, col_out_right = st.columns([1, 1.2])
            with col_out_left:
                with st.form("form_keluar"):
                    st.subheader("Catat Pengeluaran")
                    col1, col2 = st.columns(2)
                    f_desc = col1.text_input("Keluar Untuk Apa")
                    f_amt = col2.number_input("Jumlah (Rp)", min_value=0, step=1000)
                    f_cat = col1.text_input("Kategori (Bebas Isi)", placeholder="Misal: Makan, Transport...")
                    f_met = col2.text_input("Metode (Tunai/Transfer)")
                    f_date = st.date_input("Tanggal", key="out_date")
                    if st.form_submit_button("Simpan Uang Keluar", use_container_width=True):
                        c.execute("INSERT INTO finance (username, type, amount, description, category, method, date) VALUES (?,?,?,?,?,?,?)", 
                                  (user_name, "Pengeluaran", f_amt, f_desc, f_cat if f_cat else "Lainnya", f_met, str(f_date)))
                        conn.commit()
                        st.session_state['flash_msg'] = "Pengeluaran berhasil dicatat!"
                        st.session_state['flash_type'] = "success"
                        st.rerun()
            with col_out_right:
                st.write("📌 **Daftar Pengeluaran Terbaru**")
                df_out = pd.read_sql_query("SELECT id as ID, date as Tanggal, description as Deskripsi, category as Kategori, amount as Nominal FROM finance WHERE type='Pengeluaran' AND username=? ORDER BY id DESC", conn, params=(user_name,))
                if not df_out.empty: 
                    df_out['Nominal'] = df_out['Nominal'].apply(format_rp)
                    st.dataframe(df_out, hide_index=True, use_container_width=True)
                else: st.caption("Belum ada data pengeluaran.")

        with tab_debt:
            col_d_left, col_d_right = st.columns([1, 1.2])
            with col_d_left:
                st.subheader("Catat Tanggungan")
                with st.form("form_tanggungan"):
                    d_type = st.selectbox("Tipe", ["Hutang", "Piutang", "Tunggakan"])
                    col1, col2 = st.columns(2)
                    d_person = col1.text_input("Pihak Terkait (Siapa)")
                    d_amt = col2.number_input("Total Nominal (Rp)", min_value=0)
                    d_purp = col1.text_input("Tujuan/Untuk Apa")
                    d_date = col2.date_input("Tanggal")
                    d_met = col1.text_input("Metode Transaksi")
                    
                    st.markdown("---")
                    st.caption("Opsi Cicilan (Opsional)")
                    d_scheme = st.selectbox("Skema Cicilan", ["Tanpa Cicilan", "Harian", "Mingguan", "Bulanan", "Tahunan", "Lainnya"])
                    d_count = st.number_input("Mencicil Berapa Kali?", min_value=1, value=1)
                    d_inst_amt = st.number_input("Nominal Per Cicilan (Rp)", min_value=0)
                    d_status = st.selectbox("Status", ["Belum Dibayar", "Proses Mencicil", "Lunas"])
                    
                    st.markdown("---")
                    d_remind = st.checkbox("🔔 Aktifkan Pengingat Notifikasi untuk tagihan ini", value=True)
                    
                    if st.form_submit_button("Simpan Tanggungan", use_container_width=True):
                        c.execute("""INSERT INTO debts (username, type, person, total_amount, purpose, date, method, 
                                     installment_scheme, installment_count, installment_amount, status, reminder) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", 
                                  (user_name, d_type, d_person, d_amt, d_purp, str(d_date), d_met, d_scheme, d_count, d_inst_amt, d_status, int(d_remind)))
                        conn.commit()
                        st.session_state['flash_msg'] = "Data Tanggungan Berhasil Disimpan!"
                        st.session_state['flash_type'] = "success"
                        st.rerun()

            with col_d_right:
                st.write("📌 **Daftar Tanggungan & Pembayaran**")
                df_d = pd.read_sql_query("SELECT * FROM debts WHERE status != 'Lunas' AND username=?", conn, params=(user_name,))
                if not df_d.empty:
                    df_hutang = df_d[df_d['type'] == 'Hutang']
                    df_piutang = df_d[df_d['type'] == 'Piutang']
                    df_tunggakan = df_d[df_d['type'] == 'Tunggakan']
                    
                    def render_debt_list(df_subset, icon, title):
                        if not df_subset.empty:
                            st.markdown(f"##### {icon} {title}")
                            for idx, row in df_subset.iterrows():
                                with st.expander(f"(ID:{row['id']}) {row['person']} - {format_rp(row['total_amount'])}"):
                                    sisa = row['total_amount'] - (row['paid_count'] * row['installment_amount'])
                                    st.write(f"**Tujuan:** {row['purpose']} | **Sisa:** {format_rp(sisa)}")
                                    st.write(f"**Cicilan:** {row['paid_count']}/{row['installment_count']} ({row['installment_scheme']})")
                                    col_up1, col_up2 = st.columns(2)
                                    if col_up1.button("Bayar 1 Cicilan", key=f"pay_{row['id']}"):
                                        new_paid = row['paid_count'] + 1
                                        new_stat = "Lunas" if new_paid >= row['installment_count'] else "Proses Mencicil"
                                        c.execute("UPDATE debts SET paid_count=?, status=? WHERE id=? AND username=?", (new_paid, new_stat, row['id'], user_name))
                                        conn.commit(); st.rerun()
                                    if col_up2.button("Set Lunas", key=f"lunas_{row['id']}"):
                                        c.execute("UPDATE debts SET status='Lunas' WHERE id=? AND username=?", (row['id'], user_name))
                                        conn.commit(); st.rerun()

                    render_debt_list(df_hutang, "🛑", "Hutang Saya")
                    render_debt_list(df_piutang, "🟢", "Piutang Saya (Orang lain berhutang)")
                    render_debt_list(df_tunggakan, "⚠️", "Tunggakan")
                else: 
                    st.success("Semua tanggungan lunas / Belum ada data.")

        with tab_asset:
            col_a_left, col_a_right = st.columns([1, 1.2])
            with col_a_left:
                st.subheader("Catat Aset Kekayaan")
                with st.form("form_aset"):
                    a_name = st.text_input("Nama Aset (Misal: Rumah Malang, Emas 10g)")
                    a_type = st.selectbox("Kategori Aset", ["Properti/Tanah", "Kendaraan", "Logam Mulia (Emas)", "Saham/Reksa Dana", "Tunai/Tabungan", "Lainnya"])
                    a_val = st.number_input("Estimasi Nilai Saat Ini (Rp)", min_value=0, step=1000000)
                    a_date = st.date_input("Tanggal Perolehan/Pencatatan")
                    if st.form_submit_button("Simpan Aset", use_container_width=True):
                        c.execute("INSERT INTO assets (username, asset_name, asset_type, value, date_acquired) VALUES (?,?,?,?,?)", 
                                  (user_name, a_name, a_type, a_val, str(a_date)))
                        conn.commit()
                        st.session_state['flash_msg'] = "Aset berhasil dicatat!"
                        st.session_state['flash_type'] = "success"
                        st.rerun()
            with col_a_right:
                st.write("📌 **Daftar Aset Saya**")
                df_a = pd.read_sql_query("SELECT id as ID, asset_name as 'Nama Aset', asset_type as Kategori, value as 'Estimasi Nilai' FROM assets WHERE username=? ORDER BY id DESC", conn, params=(user_name,))
                if not df_a.empty: 
                    df_a['Estimasi Nilai'] = df_a['Estimasi Nilai'].apply(format_rp)
                    st.dataframe(df_a, hide_index=True, use_container_width=True)
                else: st.caption("Belum ada data aset.")

        # --- MENU BARU: TARGET IMPIAN ---
        with tab_target:
            col_t1, col_t2 = st.columns([1, 1.2])
            with col_t1:
                st.subheader("Buat Target Keuangan")
                with st.form("form_target"):
                    t_name = st.text_input("Nama Target (Misal: Beli Mobil)")
                    t_amt = st.number_input("Nominal Target (Rp)", min_value=0, step=1000000)
                    t_date = st.date_input("Target Tercapai Pada")
                    t_freq = st.selectbox("Frekuensi Menabung", ["Harian", "Mingguan", "Bulanan"])
                    
                    st.markdown("---")
                    tgt_remind = st.checkbox("🔔 Aktifkan Pengingat Nabung", value=True)
                    
                    if st.form_submit_button("Simpan Target", use_container_width=True):
                        c.execute("INSERT INTO targets (username, target_name, amount, deadline, frequency, reminder) VALUES (?,?,?,?,?,?)",
                                  (user_name, t_name, t_amt, str(t_date), t_freq, int(tgt_remind)))
                        conn.commit()
                        st.session_state['flash_msg'] = "Target Keuangan Berhasil Dibuat!"
                        st.session_state['flash_type'] = "success"
                        st.rerun()
            with col_t2:
                st.write("📌 **Target Impian Saya**")
                df_tgt = pd.read_sql_query("SELECT * FROM targets WHERE username=? ORDER BY id DESC", conn, params=(user_name,))
                if not df_tgt.empty:
                    for _, r in df_tgt.iterrows():
                        with st.expander(f"🎯 {r['target_name']} - {format_rp(r['amount'])}"):
                            delta = (pd.to_datetime(r['deadline']).date() - datetime.datetime.now().date()).days
                            if delta > 0:
                                if r['frequency'] == "Harian": periods = delta
                                elif r['frequency'] == "Mingguan": periods = delta / 7
                                else: periods = delta / 30
                                saving_per_period = r['amount'] / periods if periods > 0 else r['amount']
                                st.write(f"**Tenggat Waktu:** {r['deadline']} ({delta} hari lagi)")
                                st.write(f"**Rekomendasi Nabung:** {format_rp(saving_per_period)} per {r['frequency'].replace('an', '')}")
                                if st.button("Hapus Target", key=f"del_tgt_{r['id']}"):
                                    c.execute("DELETE FROM targets WHERE id=? AND username=?", (r['id'], user_name))
                                    conn.commit(); st.rerun()
                            else:
                                st.error("Waktu target sudah habis!")
                                if st.button("Hapus Target", key=f"del_tgt_{r['id']}"):
                                    c.execute("DELETE FROM targets WHERE id=? AND username=?", (r['id'], user_name))
                                    conn.commit(); st.rerun()
                else: st.caption("Belum ada target keuangan.")

        with tab_edit_fin:
            col_e_left, col_e_right = st.columns([1, 1])
            with col_e_left:
                st.subheader("⚙️ Edit / Hapus Data Keuangan")
                edit_type = st.radio("Pilih Kategori Data:", ["Pemasukan / Pengeluaran", "Tanggungan (Hutang/Piutang)", "Aset"])
                e_id = st.number_input("Masukkan ID Data (Lihat ID di tabel sebelah)", min_value=1, step=1)
                
                if edit_type == "Pemasukan / Pengeluaran": db_table = "finance"
                elif edit_type == "Tanggungan (Hutang/Piutang)": db_table = "debts"
                else: db_table = "assets"
                    
                if st.button("Cari Data"):
                    c.execute(f"SELECT * FROM {db_table} WHERE id=? AND username=?", (e_id, user_name))
                    res = c.fetchone()
                    if res: 
                        col_names = [description[0] for description in c.description]
                        data_dict = dict(zip(col_names, res))
                        st.session_state['edit_fin'] = {"table": db_table, "data": data_dict}
                    else: st.warning("ID tidak ditemukan atau bukan milik akun Anda.")
                    
                if 'edit_fin' in st.session_state and st.session_state['edit_fin']['table'] == db_table:
                    st.info(f"Data Ditemukan! (ID: {e_id})")
                    data_dict = st.session_state['edit_fin']['data']
                    
                    with st.form("form_edit_finance"):
                        if db_table == "finance":
                            f_type = st.selectbox("Tipe", ["Pemasukan", "Pengeluaran"], index=["Pemasukan", "Pengeluaran"].index(data_dict.get('type', 'Pemasukan')))
                            f_desc = st.text_input("Deskripsi", value=data_dict.get('description', ''))
                            f_amt = st.number_input("Jumlah (Rp)", min_value=0, step=1000, value=int(data_dict.get('amount', 0)))
                            f_cat = st.text_input("Kategori", value=data_dict.get('category', ''))
                            f_met = st.text_input("Metode", value=data_dict.get('method', ''))
                            try: e_date = datetime.datetime.strptime(data_dict.get('date', ''), "%Y-%m-%d").date()
                            except: e_date = datetime.datetime.now().date()
                            f_date = st.date_input("Tanggal", value=e_date)
                            
                            if st.form_submit_button("Update Data", use_container_width=True):
                                c.execute("UPDATE finance SET type=?, amount=?, description=?, category=?, method=?, date=? WHERE id=? AND username=?",
                                          (f_type, f_amt, f_desc, f_cat, f_met, str(f_date), e_id, user_name))
                                conn.commit()
                                del st.session_state['edit_fin']
                                st.session_state['flash_msg'] = "Data Keuangan berhasil diperbarui!"
                                st.session_state['flash_type'] = "success"
                                st.rerun()
                                
                        elif db_table == "debts":
                            d_type = st.selectbox("Tipe", ["Hutang", "Piutang", "Tunggakan"], index=["Hutang", "Piutang", "Tunggakan"].index(data_dict.get('type', 'Hutang')))
                            c1, c2 = st.columns(2)
                            d_person = c1.text_input("Pihak Terkait", value=data_dict.get('person', ''))
                            d_amt = c2.number_input("Total Nominal (Rp)", min_value=0, value=int(data_dict.get('total_amount', 0)))
                            d_purp = c1.text_input("Tujuan", value=data_dict.get('purpose', ''))
                            try: e_date = datetime.datetime.strptime(data_dict.get('date', ''), "%Y-%m-%d").date()
                            except: e_date = datetime.datetime.now().date()
                            d_date = c2.date_input("Tanggal", value=e_date)
                            d_met = st.text_input("Metode", value=data_dict.get('method', ''))
                            
                            st.markdown("---")
                            scheme_opts = ["Tanpa Cicilan", "Harian", "Mingguan", "Bulanan", "Tahunan", "Lainnya"]
                            d_scheme = st.selectbox("Skema Cicilan", scheme_opts, index=scheme_opts.index(data_dict.get('installment_scheme', 'Tanpa Cicilan')) if data_dict.get('installment_scheme') in scheme_opts else 0)
                            c3, c4 = st.columns(2)
                            d_count = c3.number_input("Mencicil Berapa Kali?", min_value=1, value=int(data_dict.get('installment_count', 1)))
                            d_inst_amt = c4.number_input("Nominal Per Cicilan (Rp)", min_value=0, value=int(data_dict.get('installment_amount', 0)))
                            d_paid = c3.number_input("Sudah Dibayar (Kali)", min_value=0, value=int(data_dict.get('paid_count', 0)))
                            
                            status_opts = ["Belum Dibayar", "Proses Mencicil", "Lunas"]
                            d_status = c4.selectbox("Status", status_opts, index=status_opts.index(data_dict.get('status', 'Belum Dibayar')) if data_dict.get('status') in status_opts else 0)
                            
                            d_remind = st.checkbox("🔔 Aktifkan Pengingat Notifikasi", value=bool(data_dict.get('reminder', 1)))
                            
                            if st.form_submit_button("Update Data", use_container_width=True):
                                c.execute("""UPDATE debts SET type=?, person=?, total_amount=?, purpose=?, date=?, method=?,
                                             installment_scheme=?, installment_count=?, paid_count=?, installment_amount=?, status=?, reminder=?
                                             WHERE id=? AND username=?""",
                                          (d_type, d_person, d_amt, d_purp, str(d_date), d_met, d_scheme, d_count, d_paid, d_inst_amt, d_status, int(d_remind), e_id, user_name))
                                conn.commit()
                                del st.session_state['edit_fin']
                                st.session_state['flash_msg'] = "Data Tanggungan berhasil diperbarui!"
                                st.session_state['flash_type'] = "success"
                                st.rerun()
                                
                        elif db_table == "assets":
                            a_name = st.text_input("Nama Aset", value=data_dict.get('asset_name', ''))
                            type_opts = ["Properti/Tanah", "Kendaraan", "Logam Mulia (Emas)", "Saham/Reksa Dana", "Tunai/Tabungan", "Lainnya"]
                            a_type = st.selectbox("Kategori Aset", type_opts, index=type_opts.index(data_dict.get('asset_type', 'Lainnya')) if data_dict.get('asset_type') in type_opts else 0)
                            a_val = st.number_input("Estimasi Nilai Saat Ini (Rp)", min_value=0, step=1000000, value=int(data_dict.get('value', 0)))
                            try: e_date = datetime.datetime.strptime(data_dict.get('date_acquired', ''), "%Y-%m-%d").date()
                            except: e_date = datetime.datetime.now().date()
                            a_date = st.date_input("Tanggal Perolehan", value=e_date)
                            
                            if st.form_submit_button("Update Data", use_container_width=True):
                                c.execute("UPDATE assets SET asset_name=?, asset_type=?, value=?, date_acquired=? WHERE id=? AND username=?",
                                          (a_name, a_type, a_val, str(a_date), e_id, user_name))
                                conn.commit()
                                del st.session_state['edit_fin']
                                st.session_state['flash_msg'] = "Data Aset berhasil diperbarui!"
                                st.session_state['flash_type'] = "success"
                                st.rerun()
                    
                    st.write("")
                    if st.button("🗑️ Hapus Permanen Data Ini", type="primary", use_container_width=True):
                        c.execute(f"DELETE FROM {db_table} WHERE id=? AND username=?", (e_id, user_name))
                        conn.commit()
                        del st.session_state['edit_fin']
                        st.session_state['flash_msg'] = "Data berhasil dihapus!"
                        st.session_state['flash_type'] = "success"
                        st.rerun()

            with col_e_right:
                st.info("ℹ️ **Cara Menggunakan Fitur Ini:**\n\n1. Pilih **Kategori Data** yang ingin diubah (Pemasukan, Tanggungan, atau Aset).\n2. Lihat **ID Data** pada tulisan kecil abu-abu di dalam tabel/daftar di tab lain.\n3. Masukkan angka ID tersebut dan klik **Cari Data**.\n4. Formulir pengubahan akan muncul secara otomatis. Anda dapat mengganti nilai apapun (nominal, status, kategori, dll) sesuai kebutuhan, lalu klik **Update Data**.\n5. Jika Anda salah memasukkan data atau ingin menghapusnya sama sekali dari riwayat, klik tombol merah **Hapus Permanen Data Ini**.")

        with tab_report:
            df_fin = pd.read_sql_query("SELECT * FROM finance WHERE username=?", conn, params=(user_name,))
            df_debts = pd.read_sql_query("SELECT * FROM debts WHERE username=?", conn, params=(user_name,))
            df_assets = pd.read_sql_query("SELECT * FROM assets WHERE username=?", conn, params=(user_name,))
            
            inc = df_fin[df_fin['type'] == 'Pemasukan']['amount'].sum() if not df_fin.empty else 0
            exp = df_fin[df_fin['type'] == 'Pengeluaran']['amount'].sum() if not df_fin.empty else 0
            tot_aset = df_assets['value'].sum() if not df_assets.empty else 0
            saldo_kas = inc - exp
            
            if not df_debts.empty:
                df_hutang = df_debts[(df_debts['type'] == 'Hutang') & (df_debts['status'] != 'Lunas')]
                tot_h = (df_hutang['total_amount'] - (df_hutang['paid_count'] * df_hutang['installment_amount'])).sum() if not df_hutang.empty else 0
                df_piutang = df_debts[(df_debts['type'] == 'Piutang') & (df_debts['status'] != 'Lunas')]
                tot_p = (df_piutang['total_amount'] - (df_piutang['paid_count'] * df_piutang['installment_amount'])).sum() if not df_piutang.empty else 0
                df_tunggakan = df_debts[(df_debts['type'] == 'Tunggakan') & (df_debts['status'] != 'Lunas')]
                tot_t = (df_tunggakan['total_amount'] - (df_tunggakan['paid_count'] * df_tunggakan['installment_amount'])).sum() if not df_tunggakan.empty else 0
            else:
                tot_h, tot_p, tot_t = 0, 0, 0
                
            kekayaan_bersih = saldo_kas + tot_aset - (tot_h + tot_t)

            rep_c1, rep_c2, rep_c3 = st.columns(3)
            rep_c1.metric("Total Pemasukan", format_rp(inc))
            rep_c2.metric("Total Pengeluaran", format_rp(exp))
            rep_c3.metric("Saldo Kas", format_rp(saldo_kas))

            rep_c4, rep_c5, rep_c6 = st.columns(3)
            rep_c4.metric("Sisa Hutang", format_rp(tot_h), delta_color="inverse")
            rep_c5.metric("Sisa Piutang", format_rp(tot_p))
            rep_c6.metric("Sisa Tunggakan", format_rp(tot_t), delta_color="inverse")
            
            st.markdown("---")
            rep_a1, rep_a2 = st.columns(2)
            rep_a1.metric("💎 Total Nilai Aset", format_rp(tot_aset))
            rep_a2.metric("🌟 KEKAYAAN BERSIH (Kas + Aset - Hutang)", format_rp(kekayaan_bersih))

            st.markdown("---")
            col_graph1, col_graph2 = st.columns(2)
            kumpulan_gambar_keuangan = []
            
            with col_graph1:
                st.subheader("Tren Pemasukan")
                df_in_trend = df_fin[df_fin['type'] == 'Pemasukan'].copy()
                if not df_in_trend.empty:
                    df_in_trend['date'] = pd.to_datetime(df_in_trend['date'], errors='coerce').dt.date
                    fig_in, ax_in = plt.subplots(figsize=(5, 4))
                    df_in_trend.groupby('date')['amount'].sum().plot(kind='line', ax=ax_in, marker='o', color='#00C250')
                    ax_in.set_title("Tren Pemasukan", fontsize=10)
                    plt.xticks(rotation=15, fontsize=8)
                    fig_in.tight_layout()
                    fig_in.savefig("chart_pemasukan.png")
                    kumpulan_gambar_keuangan.append("chart_pemasukan.png")
                    st.pyplot(fig_in)
                else: st.info("Belum ada data pemasukan untuk grafik.")
            
            with col_graph2:
                st.subheader("Pengeluaran Terbesar")
                df_out_cat = df_fin[df_fin['type'] == 'Pengeluaran']
                if not df_out_cat.empty:
                    fig_out, ax_out = plt.subplots(figsize=(5, 4))
                    df_out_cat.groupby('category')['amount'].sum().sort_values(ascending=False).head(5).plot(kind='bar', ax=ax_out, color='#FF4B4B')
                    ax_out.set_title("Kategori Pengeluaran (Top 5)", fontsize=10)
                    plt.xticks(rotation=15, fontsize=8)
                    fig_out.tight_layout()
                    fig_out.savefig("chart_pengeluaran.png")
                    kumpulan_gambar_keuangan.append("chart_pengeluaran.png")
                    st.pyplot(fig_out)
                else: st.info("Belum ada data pengeluaran untuk grafik.")

            st.markdown("---")
            user_dict = {
                "nama_lengkap": u_display_name,
                "username": f"@{user_name}",
                "kontak": f"{u_email} / {u_phone}",
                "tanggal_cetak": datetime.datetime.now().strftime("%d %B %Y")
            }
            fin_data = {
                "pemasukan": inc, "pengeluaran": exp, "saldo": saldo_kas,
                "hutang": tot_h, "piutang": tot_p, "tunggakan": tot_t,
                "aset": tot_aset, "hutang_tunggakan": (tot_h + tot_t), "kekayaan_bersih": kekayaan_bersih
            }
            fin_list = pd.read_sql_query("SELECT date, type, description, category, amount FROM finance WHERE username=? ORDER BY id DESC LIMIT 30", conn, params=(user_name,)).to_dict('records')

            try:
                pdf_filename = generate_finance_report(user_dict, fin_data, fin_list, chart_images=kumpulan_gambar_keuangan)
                with open(pdf_filename, "rb") as f:
                    pdf_bytes = f.read()

                st.write("📥 **Unduh Laporan Finansial Lengkap**")
                st.download_button(
                    label="Download Laporan Keuangan UNRAV.ID (PDF + Visualisasi)", 
                    data=pdf_bytes, 
                    file_name="Laporan_Keuangan_UNRAV.pdf", 
                    mime="application/pdf",
                    type="primary"
                )
            except Exception as e:
                st.error(f"Gagal generate PDF Keuangan. Pastikan pdf_generator.py sudah diupdate.")

    # --- 4. CATATAN (RICH-TEXT & LINKING) ---
    elif choice == "📝 Catatan":
        st.header("📝 Ruang Catatan (Rich Text)")
        t_tulis, t_daftar = st.tabs(["✍️ Tulis Catatan", "📖 Daftar Catatan"])
        
        with t_tulis:
            col_t_left, col_t_right = st.columns([2, 1])
            with col_t_left:
                with st.form("form_catatan"):
                    st.subheader("Buat Catatan Baru")
                    c_title = st.text_input("Judul Catatan")
                    
                    c_col1, c_col2 = st.columns(2)
                    c_cat = c_col1.text_input("Kategori", placeholder="Misal: Jurnal, Ide Bisnis...")
                    c_loc = c_col2.text_input("Lokasi (Opsional)", placeholder="Misal: Kafe Kopi...")
                    
                    # Relasi ke Tugas dan Keuangan
                    list_tasks = [f"{r['id']} - {r['task']}" for _, r in pd.read_sql_query("SELECT id, task FROM tasks WHERE username=? AND status='Pending'", conn, params=(user_name,)).iterrows()]
                    list_fin = [f"{r['id']} - {r['description']} (Rp {r['amount']})" for _, r in pd.read_sql_query("SELECT id, description, amount FROM finance WHERE username=? ORDER BY id DESC LIMIT 20", conn, params=(user_name,)).iterrows()]
                    
                    c_link_task = c_col1.selectbox("Kaitkan dengan Tugas (Opsional)", ["- Tidak Ada -"] + list_tasks)
                    c_link_fin = c_col2.selectbox("Kaitkan dengan Keuangan (Opsional)", ["- Tidak Ada -"] + list_fin)
                    
                    c_content = st.text_area("Isi Catatan (Gunakan panduan Markdown di sebelah kanan)", height=250)
                    c_img = st.file_uploader("Upload Gambar Lampiran (Opsional)", type=["png", "jpg", "jpeg"])
                    
                    if st.form_submit_button("Simpan Catatan", use_container_width=True):
                        if not c_title or not c_content:
                            st.error("Judul dan Isi Catatan tidak boleh kosong!")
                        else:
                            date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            c.execute("INSERT INTO notes (username, title, content, category, date_created, location, link_task, link_finance, image_path) VALUES (?,?,?,?,?,?,?,?,?)",
                                      (user_name, c_title, c_content, c_cat, date_now, c_loc, c_link_task, c_link_fin, ""))
                            note_id = c.lastrowid
                            
                            # Simpan Gambar Jika Ada
                            if c_img is not None:
                                img_path = f"note_img_{note_id}_{user_name}.png"
                                with open(img_path, "wb") as f: f.write(c_img.getbuffer())
                                c.execute("UPDATE notes SET image_path=? WHERE id=?", (img_path, note_id))
                            
                            conn.commit()
                            st.session_state['flash_msg'] = "Catatan berhasil disimpan!"
                            st.session_state['flash_type'] = "success"
                            st.rerun()
            with col_t_right:
                st.info("💡 **Panduan Format Markdown**\n\n"
                        "Untuk mempercantik teks catatan, gunakan simbol berikut:\n\n"
                        "**Tebal:** `**teks tebal**`\n"
                        "*Miring:* `*teks miring*`\n"
                        "~~Coret:~~ `~~teks dicoret~~`\n\n"
                        "**Judul (Heading):**\n"
                        "`# Judul Besar`\n"
                        "`## Judul Sedang`\n"
                        "`### Judul Kecil`\n\n"
                        "**Daftar (List):**\n"
                        "`- Poin pertama`\n"
                        "`- Poin kedua`\n\n"
                        "**Garis Pemisah:**\n"
                        "`---`\n\n"
                        "**Catatan otomatis akan berubah** menjadi format rapi saat Anda menyimpannya dan melihatnya di tab **Daftar Catatan**!")
                        
        with t_daftar:
            st.subheader("Daftar Catatan Saya")
            df_notes = pd.read_sql_query("SELECT * FROM notes WHERE username=? ORDER BY id DESC", conn, params=(user_name,))
            if not df_notes.empty:
                for _, n in df_notes.iterrows():
                    with st.expander(f"📁 [{n['category']}] {n['title']} - {n['date_created']}"):
                        st.markdown(f"**Lokasi:** {n['location']}")
                        if n['link_task'] != "- Tidak Ada -": st.markdown(f"🔗 **Terkait Tugas:** {n['link_task']}")
                        if n['link_finance'] != "- Tidak Ada -": st.markdown(f"🔗 **Terkait Keuangan:** {n['link_finance']}")
                        
                        st.markdown("---")
                        st.markdown(n['content']) # Menampilkan format Markdown
                        
                        if n['image_path'] and os.path.exists(n['image_path']):
                            st.image(n['image_path'], use_container_width=True)
                            
                        st.markdown("---")
                        n_col1, n_col2 = st.columns(2)
                        with n_col1:
                            if st.button("🗑️ Hapus Catatan", key=f"del_note_{n['id']}"):
                                if n['image_path'] and os.path.exists(n['image_path']): os.remove(n['image_path'])
                                c.execute("DELETE FROM notes WHERE id=? AND username=?", (n['id'], user_name))
                                conn.commit(); st.rerun()
            else:
                st.info("Belum ada catatan yang dibuat.")

    # --- 5. PENGATURAN PROFIL ---
    elif choice == "⚙️ Pengaturan Profil":
        st.header("⚙️ Pengaturan & Profil Pengguna")
        
        col_pp1, col_pp2 = st.columns([2, 1])
        with col_pp1:
            st.subheader("📝 Data Diri & Username")
            with st.form("profile_form"):
                p_user_new = st.text_input("Username (Bisa Diubah)", value=user_data[0]) 
                p_name = st.text_input("Nama Lengkap", value=user_data[2] if user_data[2] else "")
                
                col_p1, col_p2 = st.columns(2)
                p_pob = col_p1.text_input("Tempat Lahir", value=user_data[3] if user_data[3] else "")
                try: default_dob = pd.to_datetime(user_data[4]).date() if user_data[4] else datetime.date(2000, 1, 1)
                except: default_dob = datetime.date(2000, 1, 1)
                p_dob = col_p2.date_input("Tanggal Lahir", value=default_dob)
                
                gender_options = ["Laki-laki", "Perempuan", "Tidak Ingin Menyebutkan"]
                curr_g = user_data[5] if user_data[5] in gender_options else "Laki-laki"
                p_gender = col_p1.selectbox("Jenis Kelamin", gender_options, index=gender_options.index(curr_g))
                p_hobby = col_p2.text_input("Hobi", value=user_data[6] if user_data[6] else "")

                p_email = col_p1.text_input("Email", value=user_data[8] if user_data[8] else "")
                p_phone = col_p2.text_input("No. HP", value=user_data[9] if user_data[9] else "")
                p_bio = st.text_area("Bio Singkat", value=user_data[7] if user_data[7] else "")

                if st.form_submit_button("Simpan Perubahan Profil", use_container_width=True):
                    try:
                        # Logika Khusus Pergantian Username
                        if p_user_new != user_name:
                            is_exist = c.execute("SELECT username FROM users WHERE username=?", (p_user_new,)).fetchone()
                            if is_exist:
                                st.error("Username tersebut sudah dipakai orang lain! Pilih yang lain.")
                            else:
                                # Update semua tabel ke username baru agar data tidak hilang
                                tables = ['users', 'tasks', 'finance', 'debts', 'notes', 'assets', 'targets']
                                for tbl in tables:
                                    c.execute(f"UPDATE {tbl} SET username=? WHERE username=?", (p_user_new, user_name))
                                st.session_state['username'] = p_user_new
                                user_name = p_user_new # Set active variable
                        
                        # Update Profil
                        c.execute("""UPDATE users SET 
                                    full_name=?, pob=?, dob=?, gender=?, hobby=?, bio=?, email=?, phone=? 
                                    WHERE username=?""", 
                                  (p_name, p_pob, str(p_dob), p_gender, p_hobby, p_bio, p_email, p_phone, user_name))
                        conn.commit()
                        st.session_state['flash_msg'] = "Profil berhasil diperbarui dengan sukses!"
                        st.session_state['flash_type'] = "success"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat menyimpan profil: {e}")

        with col_pp2:
            st.subheader("🖼️ Foto Profil")
            if os.path.exists(profile_pic_path): st.image(profile_pic_path, use_container_width=True)
            else: st.image("https://api.dicebear.com/7.x/initials/png?seed=" + u_display_name, use_container_width=True)
            
            uploaded_file = st.file_uploader("Unggah baru (1:1)", type=["png", "jpg", "jpeg"])
            if uploaded_file is not None:
                if st.button("💾 Simpan Foto", type="primary", use_container_width=True):
                    with open(profile_pic_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    st.rerun()
            if os.path.exists(profile_pic_path):
                if st.button("🗑️ Hapus Foto", use_container_width=True):
                    os.remove(profile_pic_path); st.rerun()
            
            st.markdown("---")
            st.subheader("🔔 Pengingat & Notifikasi")
            st.caption("Pilih jalur pengiriman notifikasi/reminder tugas (saat ini berbasis In-App):")
            with st.form("form_notif"):
                n_desktop = st.checkbox("Notifikasi Desktop / In-App (Rekomendasi)", value=bool(user_data[13] if len(user_data) > 13 else 1))
                n_email = st.checkbox("Kirim ke Email (Simulasi Lokal)", value=bool(user_data[12] if len(user_data) > 12 else 0))
                
                if st.form_submit_button("Simpan Pengaturan Notif", use_container_width=True):
                    # Set WA dan Tele ke 0 (dinonaktifkan sesuai permintaan)
                    c.execute("UPDATE users SET notif_wa=0, notif_tele=0, notif_email=?, notif_desktop=? WHERE username=?", 
                              (int(n_email), int(n_desktop), user_name))
                    conn.commit()
                    st.success("Pengaturan notifikasi berhasil disimpan!")