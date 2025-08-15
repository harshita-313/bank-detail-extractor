import pandas as pd
import streamlit as st
import PyPDF2
import re
from analyze_transactions import analyze_with_gemini

# ----------------------
# STREAMLIT UI SETUP
# ----------------------
st.set_page_config(page_title="Bank Statement Extractor", page_icon="💳")
st.title("📄 Bank Statement Data Extractor")

# ----------------------
# FILE UPLOAD
# ----------------------
file = st.file_uploader(" your bank statement (PDF)", type="pdf")

if file is not None:
    # ----------------------
    # READ PDF CONTENT
    # ----------------------
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    # Display extracted raw text
    st.subheader("📜 Extracted Raw Text")
    with st.expander("Show/Hide Raw Text"):
        st.write(text)

    # ----------------------
    # ACCOUNT HOLDER & BANK DETAILS EXTRACTION (Regex)
    # ----------------------
    account_holder_pattern = {
        "Name": r"Customer Name\s*:\s*(.*)",
        "Address": r"Customer Address\s*:\s*(.*)",
        "Contact": r"Contact\s*:\s*(\+?\d[\d\s-]{8,})",
        "Email": r"Email\s*:\s*([\w\.-]+@[\w\.-]+)"
    }

    bank_details_pattern = {
        "Bank Account Number": r"Account\s*:\s*(\d{9,18})",
        "IFSC Code": r"IFSC Code\s*:\s*(.*)",
        "Branch Name": r"Branch Name\s*:\s*(.*)",
        "Branch Address": r"Branch Address\s*:\s*(.*)"
    }

    account_holder = {}
    bank_details = {}

    for key, pattern in account_holder_pattern.items():
        match = re.search(pattern, text, re.IGNORECASE)
        account_holder[key] = match.group(1).strip() if match else "Not found"

    for key, pattern in bank_details_pattern.items():
        match = re.search(pattern, text, re.IGNORECASE)
        bank_details[key] = match.group(1).strip() if match else "Not found"

    # ----------------------
    # TRANSACTION EXTRACTION
    # ----------------------
    transaction_pattern = r"(\d{2}-\d{2}-\d{4})\s+(.+?)\s+(\d+(?:\.\d{2})?)\s+(\d+(?:\.\d{2})?)\s+(\d+(?:\.\d{2})?)"
    transactions = re.findall(transaction_pattern, text)

    if transactions:
        df = pd.DataFrame(transactions, columns=["Date", "Description", "Deposits", "Withdrawals", "Balance"])
    else:
        df = pd.DataFrame(columns=["Date", "Description", "Amount", "Type", "Balance"])

    # ----------------------
    # VERTEX AI / GEMINI
    # ----------------------
    try:
        structured_data_ai = analyze_with_gemini(text)
        
        # Extract actual JSON from Gemini output
        gemini_json_str = structured_data_ai.get("Gemini Output", "")
        
        # Remove markdown code blocks if present
        gemini_json_str = gemini_json_str.replace("```json", "").replace("```", "").strip()
        
        # Load into a Python dict
        import json
        structured_data_ai = json.loads(gemini_json_str)
        
        st.subheader("🤖 Structured Data (Gemini AI)")
        # st.json(structured_data_ai)
    except Exception as e:
        st.error(f"Error parsing Gemini AI output: {e}")    
    # ----------------------
    # SHOW TRANSACTIONS TABLE
    # ----------------------
    # Account & Bank details cards
    st.subheader("🏦 Account & Bank Details")
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Account Holder Details")
        for k, v in structured_data_ai["Account Holder Details"].items():
            st.write(f"**{k}:** {v}")
    with col2:
        st.write("### Bank Details")
        for k, v in structured_data_ai["Bank Account Details"].items():
            st.write(f"**{k}:** {v}")

    # Transactions table
    st.subheader("💰 Transactions Table (Gemini)")
    transactions = structured_data_ai.get("Transactions", [])
    if transactions:
        df_ai = pd.DataFrame(transactions)
        st.dataframe(df_ai)
        csv_data = df_ai.to_csv(index=False)
        st.download_button("📥 Download Transactions as CSV", csv_data, "transactions.csv")
    else:
        st.warning("No transactions found from Gemini AI")

