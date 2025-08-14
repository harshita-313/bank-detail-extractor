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
file = st.file_uploader("Upload your bank statement (PDF)", type="pdf")

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
    transaction_pattern = r"(\d{2}-\d{2}-\d{4})\s+([A-Za-z\s]+)\s+(\d+\.\d{2})\s+(Debit|Credit)\s+(\d+\.\d{2})"
    transactions = re.findall(transaction_pattern, text)

    if transactions:
        df = pd.DataFrame(transactions, columns=["Date", "Description", "Amount", "Type", "Balance"])
    else:
        df = pd.DataFrame(columns=["Date", "Description", "Amount", "Type", "Balance"])

    # ----------------------
    # SHOW STRUCTURED DATA
    # ----------------------
    structured_data_regex = {
        "Account Holder Details": account_holder,
        "Bank Account Details": bank_details
    }
    st.subheader("📦 Structured Data (Regex Extraction)")
    st.json(structured_data_regex)

    # ----------------------
    # VERTEX AI / GEMINI
    # ----------------------
    try:
        structured_data_ai = analyze_with_gemini(text)
        st.subheader("🤖 Structured Data (Gemini AI)")
        st.json(structured_data_ai)
    except Exception as e:
        st.error(f"Error calling Vertex AI: {e}")

    # ----------------------
    # SHOW TRANSACTIONS TABLE
    # ----------------------
    st.subheader("💰 Transactions Table")
    if not df.empty:
        st.dataframe(df)
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Transactions as CSV",
            data=csv_data,
            file_name="transactions.csv",
            mime="text/csv"
        )
    else:
        st.warning("No transactions found. Check PDF format or update regex pattern.")
