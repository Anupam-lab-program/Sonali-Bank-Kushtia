import streamlit as st
import pandas as pd
import datetime
import sqlite3
import io
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# --- ১. ডাটাবেস এবং পেজ কনফিগারেশন ---
st.set_page_config(page_title="Sonali Bank Kushtia", layout="wide")

def init_db():
    conn = sqlite3.connect('sonali_kushtia_final.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS loans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, name TEXT, 
                  mobile TEXT, type TEXT, amount REAL, interest REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mobile TEXT, 
                  password TEXT, status TEXT DEFAULT 'Pending')''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, time TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- ২. কাস্টম সিএসএস ---
st.markdown("""
    <style>
    .stApp { background-color: #2798F5; }
    .main-header { color: white !important; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    label { color: white !important; font-weight: bold !important; }
    div.stButton > button { background-color: #1e8449 !important; color: white !important; border-radius: 12px; height: 3.5em; font-weight: bold; border: 1px solid white; }
    </style>
    """, unsafe_allow_html=True)

# --- ৩. সাইডবার মেনু কন্ট্রোল ---
st.sidebar.title("💳 সোনালী ব্যাংক মেনু")
selection = st.sidebar.radio("পেজ নির্বাচন করুন:", ["মূল ওয়েবসাইট", "📊 ডাটা ড্যাশবোর্ড", "🔒 অ্যাডমিন প্যানেল"])

# --- ৪. ডাটা ড্যাশবোর্ড পেজ (গুগল শিট) ---
if selection == "📊 ডাটা ড্যাশবোর্ড":
    st.markdown("<h1 class='main-header'>📊 রিয়েল টাইম ডাটা ড্যাশবোর্ড</h1>", unsafe_allow_html=True)
    
    def load_data():
        try:
            conn_gs = st.connection("gsheets", type=GSheetsConnection)
            # আপনার গুগল শিট লিঙ্কটি এখানে ব্যবহার করা হয়েছে
            df = conn_gs.read(spreadsheet="https://docs.google.com/spreadsheets/d/1CsEpeI-_VQC0RdPwn7cnGKCQDDU4rE7j-cToqFWq9NM/")
            return df
        except Exception as e:
            st.error(f"ডাটাবেসের সাথে কানেক্ট করা যাচ্ছে না: {e}")
            return None

    with st.spinner('গুগল শিট থেকে ডাটা আনা হচ্ছে...'):
        data = load_data()
        if data is not None:
            st.success("সর্বশেষ ডাটা লোড হয়েছে!")
            st.dataframe(data, use_container_width=True)
            
            # ডাউনলোড বাটন
            csv = data.to_csv(index=False).encode('utf-8')
            st.download_button("Excel/CSV হিসেবে ডাউনলোড করুন", csv, "bank_data.csv", "text/csv")

# --- ৫. অ্যাডমিন প্যানেল পেজ ---
elif selection == "🔒 অ্যাডমিন প্যানেল":
    st.markdown("<h1 class='main-header'>🔒 সিকিউরড অ্যাডমিন প্যানেল</h1>", unsafe_allow_html=True)
    conn = sqlite3.connect('sonali_kushtia_final.db')
    c = conn.cursor()
    
    auth_mode = st.radio("অপশন নির্বাচন করুন:", ["লগইন", "নতুন কর্মকর্তা রেজিস্ট্রেশন", "ম্যানেজার কন্ট্রোল"])
    
    if auth_mode == "নতুন কর্মকর্তা রেজিস্ট্রেশন":
        r_name = st.text_input("আপনার পূর্ণ নাম:")
        r_mob = st.text_input("মোবাইল নম্বর:")
        r_pw = st.text_input("পাসওয়ার্ড তৈরী করুন:", type="password")
        if st.button("রেজিস্ট্রেশন আবেদন পাঠান"):
            if r_name and r_mob and r_pw:
                c.execute("INSERT INTO users (name, mobile, password, status) VALUES (?,?,?,?)", (r_name, r_mob, r_pw, 'Pending'))
                conn.commit()
                st.info("আবেদন পাঠানো হয়েছে। ম্যানেজার অনুমোদন করলে লগইন করতে পারবেন।")
    
    elif auth_mode == "লগইন":
        l_mob = st.text_input("মোবাইল নম্বর:")
        l_pw = st.text_input("পাসওয়ার্ড:", type="password")
        if st.button("লগইন করুন"):
            user = c.execute("SELECT * FROM users WHERE mobile=? AND password=? AND status='Approved'", (l_mob, l_pw)).fetchone()
            if user:
                c.execute("INSERT INTO logs (user, time) VALUES (?,?)", (user[1], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.session_state['logged'] = True
                st.success(f"স্বাগতম {user[1]}!")
            else:
                st.error("ভুল তথ্য অথবা আইডি অনুমোদিত নয়।")
        
        if st.session_state.get('logged'):
            df_loans = pd.read_sql_query("SELECT * FROM loans", conn)
            st.subheader("📊 গ্রাহক লোন ডাটাবেস")
            st.dataframe(df_loans, use_container_width=True)

    elif auth_mode == "ম্যানেজার কন্ট্রোল":
        if st.text_input("ম্যানেজার সিক্রেট কোড:", type="password") == "sonali123":
            st.subheader("পেন্ডিং ইউজার লিস্ট")
            df_pending = pd.read_sql_query("SELECT id, name, mobile, status FROM users WHERE status='Pending'", conn)
            st.table(df_pending)
            u_id = st.number_input("কাকে অনুমোদন দিবেন? (আইডি লিখুন):", min_value=1, step=1)
            if st.button("অনুমোদন দিন"):
                c.execute("UPDATE users SET status='Approved' WHERE id=?", (u_id,))
                conn.commit()
                st.success("অনুমোদিত হয়েছে!")
                st.rerun()
            st.subheader("📜 লগইন রিপোর্ট")
            st.table(pd.read_sql_query("SELECT * FROM logs", conn))
    conn.close()

# --- ৬. মূল ওয়েবসাইট পেজ ---
else:
    st.markdown("<h1 class='main-header'>সোনালী ব্যাংক কুষ্টিয়া শাখা</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ডিজিটাল ব্যাংকিং পোর্টালে আপনাকে স্বাগতম</h3>", unsafe_allow_html=True)
    
    # এখানে আপনার মূল ওয়েবসাইটের ক্যালকুলেটর বা অন্যান্য কোডগুলো থাকবে
    st.info("বাম পাশের মেনু থেকে বিভিন্ন সেবা গ্রহণ করুন।")
