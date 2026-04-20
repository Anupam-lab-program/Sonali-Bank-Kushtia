import streamlit as st
import pandas as pd
import datetime
import sqlite3
import io
from fpdf import FPDF


# --- ১. ডাটাবেস ফাংশনসমূহ ---
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


def clean_text(text):
    return str(text).encode('ascii', 'ignore').decode('ascii')


def create_loan_pdf(name, mobile, loan_type, amount, interest):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Sonali Bank Kushtia - Loan Application", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Customer Name: {clean_text(name)}", ln=1)
    pdf.cell(200, 10, txt=f"Mobile: {clean_text(mobile)}", ln=1)
    pdf.cell(200, 10, txt=f"Loan Type: {clean_text(loan_type)}", ln=1)
    pdf.cell(200, 10, txt=f"Amount: {amount:,.2f} BDT", ln=1)
    pdf.cell(200, 10, txt=f"Total Interest: {interest:,.2f} BDT", ln=1)
    return pdf.output(dest='S').encode('latin-1')

def create_emi_pdf(p, r, n, emi, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="EMI Breakup Report - Sonali Bank", ln=1, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(5)
    pdf.cell(200, 7, txt=f"Principal: {p} | Rate: {r}% | Months: {n} | Monthly EMI: {emi:,.2f}", ln=1)
    pdf.ln(5)
    pdf.cell(30, 8, "Month", 1); pdf.cell(50, 8, "Interest", 1); pdf.cell(50, 8, "Principal", 1); pdf.cell(50, 8, "Balance", 1); pdf.ln()
    for i, row in df.iterrows():
        pdf.cell(30, 8, str(int(row['Month'])), 1)
        pdf.cell(50, 8, f"{row['Interest']:,.2f}", 1)
        pdf.cell(50, 8, f"{row['Principal']:,.2f}", 1)
        pdf.cell(50, 8, f"{row['Balance']:,.2f}", 1, 1)
    return pdf.output(dest='S').encode('latin-1', 'ignore')


# --- ২. কাস্টম সিএসএস ---
st.set_page_config(page_title="Sonali Bank Kushtia", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #2798F5; }
    .main-header { color: white !important; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    .card { background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid #1e8449; margin-bottom: 20px; color: black; }
    .sc-result { background-color: #FFD700; padding: 20px; border-radius: 15px; border: 2px solid white; color: black; text-align: center; }
    .success-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 8px solid #28a745; color: black; font-weight: bold; margin-bottom: 15px; }
    label { color: white !important; font-weight: bold !important; }
    div.stButton > button { background-color: #1e8449 !important; color: white !important; border-radius: 12px; height: 3.5em; font-weight: bold; border: 1px solid white; }
    /* অ্যাডমিন প্যানেলের টেবিল এবং ডাটাফ্রেমের ব্যাকগ্রাউন্ড উজ্জ্বল করা */
    [data-testid="stTable"], [data-testid="stDataFrame"], .stTable {
        background-color: white !important;
        color: black !important;
        border-radius: 10px;
        padding: 10px;
    }

    /* টেবিলের ভেতরের টেক্সট কালার কালো নিশ্চিত করা */
    [data-testid="stTable"] td, [data-testid="stTable"] th {
        color: black !important;
    }

    /* ইনপুট বক্সের উজ্জ্বলতা বাড়ানো */
    .stTextInput input, .stNumberInput input {
        background-color: #f0f2f6 !important;
        color: black !important;
        /* টেবিল, ইনপুট এবং স্লাইডার এরিয়া সাদা করা */
[data-testid="stTable"], [data-testid="stDataFrame"], .stSlider, .stNumberInput {
    background-color: white !important;
    padding: 20px !important;
    border-radius: 12px !important;
    color: black !important;
}

/* স্লাইডারের টেক্সট কালার কালো করা */
.stSlider label, .stNumberInput label {
    color: black !important;
}
    }
    </style>
   
    """, unsafe_allow_html=True)

# --- ৩. সাইডবার ---
choice = st.sidebar.radio("পেজ নির্বাচন করুন:",
                          ["💰 লোন আবেদন", "🧮 মাসিক সঞ্চয় স্কীম", "📜 সঞ্চয়পত্র প্রকল্প", "🔒 অ্যাডমিন প্যানেল"])

# --- ৪. পেজ ১: লোন আবেদন (ছবি ও এনআইডিসহ) ---
if choice == "💰 লোন আবেদন":
    st.markdown("<h1 class='main-header'>🏦 লোন আবেদন ও ডকুমেন্ট সংযোজন</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        u_name = st.text_input("গ্রাহকের নাম (ইংরেজিতে):")
        u_mobile = st.text_input("মোবাইল নম্বর:")
        u_salary = st.number_input("মাসিক বেতন (টাকা):", min_value=0)
        u_photo = st.file_uploader("📸 ছবি আপলোড করুন", type=['jpg', 'png', 'jpeg'])
    with col2:
        u_amount = st.number_input("লোনের পরিমাণ (টাকা):", min_value=0)
        u_type = st.selectbox("লোনের ধরন:", ["Home Loan", "Personal Loan", "OD Loan"])
        u_nid = st.file_uploader("💳 এনআইডি কপি আপলোড করুন", type=['jpg', 'png', 'pdf'])

    if st.button("হিসাব এবং আবেদন জমা দিন"):
        if u_name and u_photo and u_nid and u_amount > 0:
            rate = 8.5 if "Home" in u_type else (11.0 if "Personal" in u_type else 9.5)
            interest = (u_amount * rate) / 100

            conn = sqlite3.connect('sonali_kushtia_final.db')
            c = conn.cursor()
            c.execute("INSERT INTO loans (time, name, mobile, type, amount, interest) VALUES (?,?,?,?,?,?)",
                      (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), u_name, u_mobile, u_type, u_amount,
                       interest))
            conn.commit();
            conn.close()

            st.markdown(f'<div class="success-card">✅ আবেদন সফল! মোট মুনাফা: {interest:,.2f} টাকা।</div>',
                        unsafe_allow_html=True)
            pdf_bytes = create_loan_pdf(u_name, u_mobile, u_type, u_amount, interest)
            st.download_button("📥 লোন ফরম (PDF) ডাউনলোড", pdf_bytes, f"{u_name}_loan.pdf")
        else:
            st.warning("সব তথ্য এবং ছবি/এনআইডি আপলোড করুন।")


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
