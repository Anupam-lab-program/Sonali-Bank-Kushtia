import streamlit as st
import pandas as pd
import sqlite3
import re
from streamlit_gsheets import GSheetsConnection
import io
from fpdf import FPDF

# --- ১. কনফিগারেশন ও ডাটাবেস ---
st.set_page_config(page_title="Sonali Bank Kushtia", layout="wide")

def init_db():
    conn = sqlite3.connect('sonali_kushtia_final.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS loans 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, name TEXT, 
                  mobile TEXT, salary REAL, type TEXT, amount REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- ২. উন্নত সিএসএস (বক্স দৃশ্যমান করার জন্য) ---
st.markdown("""
<style>
    .stApp { background-color: #2798F5; } 
    .main-header { 
        color: white !important; 
        text-align: center; 
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 30px;
    }
    /* ইনপুট বক্সের ডিজাইন - বর্ডার গোল্ডেন করা হয়েছে */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
        background-color: white !important;
        color: black !important;
        border: 3px solid #FFD700 !important; 
        border-radius: 10px !important;
        font-weight: bold !important;
    }
    /* কার্ড ডিজাইন */
    .card { 
        background-color: white; 
        padding: 30px; 
        border-radius: 20px; 
        border-left: 10px solid #1e8449; 
        color: black; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .interest-chart { 
        background-color: #f0fdf4; 
        padding: 20px; 
        border-radius: 15px; 
        border: 2px solid #1e8449;
    }
    label { color: white !important; font-weight: bold !important; font-size: 1.1em; margin-bottom: 5px; }
    div.stButton > button { 
        background-color: #1e8449 !important; 
        color: white !important; 
        border-radius: 12px; 
        width: 100%; 
        height: 3.5em; 
        font-size: 1.1em;
        font-weight: bold;
        border: 2px solid white;
    }
</style>
""", unsafe_allow_html=True)

# --- ৩. হেল্পার ফাংশন ---
def validate_mobile(mobile):
    return re.match(r"^(01[3-9][0-9]{8})$", mobile)

# --- ৪. সাইডবার নেভিগেশন ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/thumb/3/3b/Sonali_Bank_Logo.svg/220px-Sonali_Bank_Logo.svg.png", width=100)
st.sidebar.title("💳 মেনু কন্ট্রোল")
selection = st.sidebar.radio("পেজ নির্বাচন করুন:", ["🏠 মূল ওয়েবসাইট", "📊 ডাটা ড্যাশবোর্ড", "🔒 অ্যাডমিন প্যানেল"])

# --- ৫. মূল ওয়েবসাইট পেজ ---
if selection == "🏠 মূল ওয়েবসাইট":
    st.markdown("<h1 class='main-header'>🏦 সোনালী ব্যাংক কুষ্টিয়া শাখা</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.5, 1]) 
    
    with col1:
        st.subheader("📋 লোন আবেদন ফরম")
        u_name = st.text_input("গ্রাহকের নাম (ইংরেজিতে):", placeholder="Ex: ABUL KASEM", key="u_name")
        u_mobile = st.text_input("মোবাইল নম্বর (১১ ডিজিট):", placeholder="017XXXXXXXX", key="u_mob")
        u_salary = st.number_input("আপনার মাসিক নিট বেতন (টাকা):", min_value=0, step=1000, key="u_sal")
        
        u_type = st.selectbox("লোনের ধরণ:", ["পার্সোনাল লোন", "গৃহ নির্মাণ লোন", "এসএমই লোন", "কৃষি লোন"])
        u_amount = st.number_input("কাঙ্ক্ষিত লোনের পরিমাণ (টাকা):", min_value=10000, max_value=50000000, step=5000)

        if st.button("আবেদন জমা দিন"):
            if u_name and validate_mobile(u_mobile):
                st.balloons()
                st.success(f"ধন্যবাদ {u_name}! আপনার আবেদনটি সফলভাবে সিস্টেমে জমা হয়েছে।")
            else:
                st.error("দয়া করে সঠিক নাম এবং ১১ ডিজিটের মোবাইল নম্বর দিন।")

    with col2:
        st.markdown("<div class='interest-chart'>", unsafe_allow_html=True)
        st.markdown("### 📈 সুদের হার চার্ট")
        rate_df = pd.DataFrame({
            "লোনের ধরণ": ["পার্সোনাল", "গৃহ নির্মাণ", "SME", "কৃষি"],
            "সুদের হার": ["৯.০০%", "৮.৫০%", "১০.০০%", "৪.০০%"]
        })
        st.table(rate_df)
        st.info("দ্রষ্টব্য: ব্যাংকের নিয়ম অনুযায়ী সুদের হার পরিবর্তন হতে পারে।")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- ৬. ডাটা ড্যাশবোর্ড পেজ ---
elif selection == "📊 ডাটা ড্যাশবোর্ড":
    st.markdown("<h1 class='main-header'>📊 ডাটা অ্যানালাইসিস ড্যাশবোর্ড</h1>", unsafe_allow_html=True)
    st.info("গুগল শিট থেকে ডাটা এখানে প্রদর্শিত হবে।")
    
    def load_data():
        try:
            conn_gs = st.connection("gsheets", type=GSheetsConnection)
            df = conn_gs.read(spreadsheet="https://docs.google.com/spreadsheets/d/1xU4ICiT3l_Xs9pIkt0b8pm-TIvHnXYVRnTwy7_vsnck/edit?gid=0#gid=0")
            return df
        except:
            return None

    data = load_data()
    if data is not None:
        st.success("গুগল শিট থেকে সর্বশেষ তথ্য লোড হয়েছে")
        st.dataframe(data, use_container_width=True)
    else:
        st.error("ডাটাবেসের সাথে কানেক্ট করা যাচ্ছে না।")

# --- ৫. পেজ ২: মাসিক সঞ্চয় স্কীম (নাম ও মুনাফা আপডেট) ---

elif choice == "🧮 মাসিক সঞ্চয় স্কীম":  # আপনার মেনু অনুযায়ী নাম
    st.markdown("<h1 class='main-header'>🧮 ব্যাংকিং ক্যালকুলেটর ও রিপোর্ট</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📊 EMI ক্যালকুলেটর", "💰 সঞ্চয় ও বোনাস"])

    with tab1:
        p = st.number_input("মূল টাকা:", value=100000, key="emi_p")
        r = st.number_input("মুনাফার হার (%):", value=9.0, key="emi_r")
        n = st.number_input("মেয়াদ (মাস):", value=12, key="emi_n")

        if st.button("EMI ও ব্রেকআপ রিপোর্ট তৈরি করুন"):
            m_rate = r / (12 * 100)
            emi = (p * m_rate * (1 + m_rate) ** n) / ((1 + m_rate) ** n - 1)
            st.markdown(f'<div class="card"><h3>মাসিক কিস্তি: {emi:,.2f} টাকা</h3></div>', unsafe_allow_html=True)

            # ব্রেকআপ টেবিল তৈরি
            balance = p
            rows = []
            for i in range(1, n + 1):
                i_pay = balance * m_rate
                p_pay = emi - i_pay
                balance -= p_pay
                rows.append([i, i_pay, p_pay, max(0, balance)])

            df_emi = pd.DataFrame(rows, columns=['Month', 'Interest', 'Principal', 'Balance'])
            st.dataframe(df_emi, use_container_width=True)

            # পিডিএফ জেনারেটর কল (নিশ্চিত করুন আপনার create_emi_pdf ফাংশনটি কোডের উপরে ডিফাইন করা আছে)
            try:
                pdf_emi = create_emi_pdf(p, r, n, emi, df_emi)
                st.download_button("📥 ইএমআই ব্রেকআপ রিপোর্ট (PDF)", pdf_emi, "EMI_Breakup.pdf")
            except NameError:
                st.error(
                    "পিডিএফ ফাংশনটি খুঁজে পাওয়া যায়নি। দয়া করে নিশ্চিত করুন create_emi_pdf ফাংশনটি আপনার কোডে আছে।")

    with tab2:
        st.subheader("মাসিক সঞ্চয় ও লয়্যালটি বোনাস হিসাব")
        amount = st.number_input("জমার পরিমাণ (মাসিক):", value=1000, key="save_amt")
        years = st.slider("মেয়াদ (বছর):", 1, 10, 5, key="save_yrs")
        rate_s = st.number_input("মুনাফার হার (%):", value=7.5, key="save_rate")
        is_bonus = st.checkbox("আমি কোনো কিস্তি ডিফল্টার হইনি (বোনাস পাবেন)", key="save_bonus")

        if st.button("সঞ্চয় ও মুনাফা হিসাব করুন"):
            total_months = years * 12
            principal = amount * total_months
            # ব্যাংকিং সূত্র অনুযায়ী চক্রবৃদ্ধি মুনাফা হিসাব
            profit = amount * (((1 + (rate_s / 100 / 12)) ** total_months - 1) / (rate_s / 100 / 12)) - principal

            # আপনার সেই বিশেষ বোনাস লজিক
            bonus = (amount + 1000) if is_bonus else 0

            st.markdown(f"""
                <div class="card">
                    <h3 style="color: #1e8449; text-align: center;">💰 সঞ্চয়ের ফলাফল</h3>
                    <hr>
                    <p style="font-size: 18px;">মেয়াদ শেষে আপনার <b>মূল জমা: {principal:,.2f}</b> টাকা</p>
                    <p style="font-size: 18px;">অর্জিত <b>মুনাফা: {profit:,.2f}</b> টাকা</p>
                    <p style="font-size: 18px;"><b>বোনাস: {bonus:,.2f}</b> টাকা সহ</p>
                    <h2 style="color: #28a745; text-align: center;">সর্বমোট পাবেন: {principal + profit + bonus:,.2f} টাকা</h2>
                </div>
            """, unsafe_allow_html=True)
# --- ৬. পেজ ৩: সঞ্চয়পত্র প্রকল্প (লিংকসহ) ---
elif choice == "📜 সঞ্চয়পত্র প্রকল্প":
    st.markdown("<h1 class='main-header'>📜 সঞ্চয়পত্র প্রকল্প</h1>", unsafe_allow_html=True)
    st.markdown("""
        <div class="card" style="text-align: center;">
            <p>সঞ্চয়পত্রের সর্বশেষ নিয়ম ও ফরম ডাউনলোডের জন্য ভিজিট করুন:</p>
            <a href="http://nationalsavings.gov.bd/" target="_blank">
                <button style="background-color: #1e8449; color: white; padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; font-weight: bold;">
                    অফিসিয়াল ওয়েবসাইটে যান ↗️
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)
    sc_type = st.selectbox("সঞ্চয়পত্রের ধরণ:",
                           ["৩-মাস অন্তর মুনাফা", "পরিবার সঞ্চয়পত্র", "পেনশনার সঞ্চয়পত্র", "বাংলাদেশ সঞ্চয়পত্র"])
    invest = st.number_input("বিনিয়োগের পরিমাণ (টাকা):", min_value=10000, step=10000, value=100000)
    if st.button("মুনাফা হিসাব করুন"):
        rate = 11.04 if "৩-মাস" in sc_type else 11.52
        monthly = (invest * (rate / 100)) / 12
        st.markdown(
            f'<div class="sc-result"><h2>মাসিক নিট মুনাফা: {monthly:,.2f} টাকা</h2><p>বার্ষিক হার: {rate}%</p></div>',
            unsafe_allow_html=True)

# --- ৭. পেজ ৪: অ্যাডমিন প্যানেল (রেজিস্ট্রেশন ফিক্স) ---
elif choice == "🔒 অ্যাডমিন প্যানেল":
    st.markdown("<h1 class='main-header'>🔒 সিকিউরড অ্যাডমিন প্যানেল</h1>", unsafe_allow_html=True)
    conn = sqlite3.connect('sonali_kushtia_final.db')
    c = conn.cursor()

    auth_mode = st.radio("অপশন নির্বাচন করুন:", ["লগইন", "নতুন কর্মকর্তা রেজিস্ট্রেশন", "ম্যানেজার কন্ট্রোল"])

    if auth_mode == "নতুন কর্মকর্তা রেজিস্ট্রেশন":
        st.subheader("অফিসার অ্যাকাউন্ট তৈরির আবেদন")
        r_name = st.text_input("আপনার পূর্ণ নাম:")
        r_mob = st.text_input("মোবাইল নম্বর:")
        r_pw = st.text_input("পাসওয়ার্ড তৈরী করুন:", type="password")
        if st.button("রেজিস্ট্রেশন আবেদন পাঠান"):
            if r_name and r_mob and r_pw:
                c.execute("INSERT INTO users (name, mobile, password, status) VALUES (?,?,?,?)",
                          (r_name, r_mob, r_pw, 'Pending'))
                conn.commit()
                st.info("আপনার আবেদনটি পাঠানো হয়েছে। ম্যানেজার এটি অনুমোদন করলে আপনি লগইন করতে পারবেন।")
            else:
                st.warning("সবগুলো তথ্য পূরণ করুন।")

    elif auth_mode == "লগইন":
        l_mob = st.text_input("মোবাইল নম্বর:")
        l_pw = st.text_input("পাসওয়ার্ড:", type="password")
        if st.button("লগইন করুন"):
            user = c.execute("SELECT * FROM users WHERE mobile=? AND password=? AND status='Approved'",
                             (l_mob, l_pw)).fetchone()
            if user:
                c.execute("INSERT INTO logs (user, time) VALUES (?,?)",
                          (user[1], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit();
                st.session_state['logged'] = True;
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
                conn.commit();
                st.success("অনুমোদিত হয়েছে!");
                st.rerun()
            st.subheader("📜 লগইন রিপোর্ট (অপরিবর্তনীয়)")
            st.table(pd.read_sql_query("SELECT * FROM logs", conn))
    conn.close()
