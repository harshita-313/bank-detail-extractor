from flask import Flask, request, jsonify
import PyPDF2
import re

app = Flask(__name__)

@app.route("/extract-pdf", methods=["POST"])
def extract_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    # Read PDF
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    # -------------------
    # Extract Account Holder & Bank Details
    # -------------------
    account_holder_pattern = {
        "Name": r"Customer Name\s*:\s*(.*)",
        "Address": r"Customer Address\s*:\s*(.*)",
        "Contact": r"Contact\s*:\s*(\+?\d[\d\s-]{8,})",
        "Email": r"Email\s*:\s*([\w\.-]+@[\w\.-]+)"
    }

    bank_details_pattern = {
        "Bank Account Number": r"Account\s*:\s*(\d{9,18})",
        "IFSC Code": r"IFSC Code\s*:\s*(.*)",
        "Branch Address": r"Branch\s*Address\s*:\s*(.*)"
    }

    account_holder = {}
    bank_details = {}

    for key, pattern in bank_details_pattern.items():
        match = re.search(pattern, text, re.IGNORECASE)
        bank_details[key] = match.group(1).strip() if match else "Not found"

    for key, pattern in account_holder_pattern.items():
        match = re.search(pattern, text, re.IGNORECASE)
        account_holder[key] = match.group(1).strip() if match else "Not found"

    # -------------------
    # Extract Transactions
    # Example format: "25-04-2024  POS Purchase  4347.35  Debit   27"
    # -------------------
    transaction_pattern = r"(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+(Debit|Credit)\s+([\d,]+\.\d{2}|\d+)"
    transactions = []
    for match in re.finditer(transaction_pattern, text):
        date, description, amount, tx_type, balance = match.groups()
        transactions.append({
            "Date": date.strip(),
            "Description": description.strip(),
            "Amount": amount.strip(),
            "Type": tx_type.strip(),
            "Balance": balance.strip()
        })

    # -------------------
    structured_data = {
        "Account Holder Details": account_holder,
        "Bank Account Details": bank_details,
        "Transactions": transactions
    }

    return jsonify(structured_data)

if __name__ == "__main__":
    app.run(debug=True)

