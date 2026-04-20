# আগের ৩ লাইনের বদলে নিচের ৩ লাইন বসান
import streamlit as st
from streamlit_gsheets import GSheetsConnection

conn = st.connection("gsheets", type=GSheetsConnection)
from datetime import datetime
from fpdf import FPDF
import io

# --- ১. গুগল শিট কানেকশন ---
conn = st.connection("gsheets", type=GSheetsConnection)

# ম্যানেজার পাসওয়ার্ড এখন সরাসরি সিক্রেটস থেকে আসবে
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# ডাটা রিড করার ফাংশন
def load_data():
    return conn.read(worksheet="Sonali Bank Data", ttl="0m")

# ডাটা সেভ করার ফাংশন
def save_data(df):
    conn.update(worksheet="Sonali Bank Data", data=df)

# --- ২. পিডিএফ তৈরির ফাংশন (আপনার আগের লজিক অনুযায়ী) ---
def create_loan_pdf(name, mobile, loan_type, amount):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Sonali Bank Kushtia Branch", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Customer Name: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Mobile: {mobile}", ln=True)
    pdf.cell(200, 10, txt=f"Loan Type: {loan_type}", ln=True)
    pdf.cell(200, 10, txt=f"Amount: {amount} BDT", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- ৩. ইউজার ইন্টারফেস (UI) ---
st.set_page_config(page_title="Sonali Bank Kushtia", layout="centered")

# CSS দিয়ে ব্যাকগ্রাউন্ড ঠিক করা (আপনার স্টাইল অনুযায়ী)
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #2E94F3;
    }
    .stTextInput, .stNumberInput, .stSelectbox {
        background-color: white !important;
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 লোন আবেদন ও ডকুমেন্ট সংযোজন")

with st.form("loan_form"):
    name = st.text_input("গ্রাহকের নাম (ইংরেজিতে):")
    mobile = st.text_input("মোবাইল নম্বর:")
    loan_type = st.selectbox("লোনের ধরন:", ["Home Loan", "Personal Loan", "SME Loan"])
    amount = st.number_input("লোনের পরিমাণ (টাকা):", min_value=0)
    
    submitted = st.form_submit_button("আবেদন জমা দিন")
    
    if submitted:
        if name and mobile and amount > 0:
            # নতুন ডাটা তৈরি
            new_data = pd.DataFrame([{
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Name": name,
                "Mobile": mobile,
                "Type": loan_type,
                "Amount": amount
            }])
            
            # আগের ডাটার সাথে যোগ করা
            try:
                existing_data = load_data()
                updated_data = pd.concat([existing_data, new_data], ignore_index=True)
                save_data(updated_data)
                st.success("আবেদনটি সফলভাবে গুগল শিটে সেভ হয়েছে!")
                
                # পিডিএফ ডাউনলোড বাটন
                pdf_bytes = create_loan_pdf(name, mobile, loan_type, amount)
                st.download_button(label="Download PDF", data=pdf_bytes, file_name=f"{name}_loan.pdf")
            except Exception as e:
                st.error(f"ডাটা সেভ করতে সমস্যা হয়েছে: {e}")
        else:
            st.warning("দয়া করে সব তথ্য পূরণ করুন।")

# --- ৪. ম্যানেজার প্যানেল ---
st.sidebar.title("ম্যানেজার কন্ট্রোল")
password = st.sidebar.text_input("পাসওয়ার্ড দিন:", type="password")

if password == ADMIN_PASSWORD:
    st.sidebar.success("লগইন সফল!")
    st.header("📋 সকল আবেদনকারী")
    try:
        df = load_data()
        st.dataframe(df)
    except:
        st.info("এখনো কোনো আবেদন জমা পড়েনি।")
