import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

# Load API key from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)

def analyze_with_gemini(text):
    """
    Sends extracted PDF text to Gemini (Vertex AI) and returns structured JSON.
    """

    prompt = f"""
    You are a financial data analyst.

    Extract the following from the text below:

    1. Account Holder Details: Name, Address, Contact, Email
    2. Bank Account Details: Account Number, IFSC, Branch Name, Branch Address
    3. Transactions: list all transactions in a table with columns: Date, Description, Deposits, Withdrawals, Balance

    Return the output in JSON format like this:

    {{
    "Account Holder Details": {{
        "Name": "",
        "Address": "",
        "Contact": "",
        "Email": ""
    }},
    "Bank Account Details": {{
        "Account Number": "",
        "IFSC": "",
        "Branch Name": "",
        "Branch Address": ""
    }},
    "Transactions": [
        {{"Date": "", "Description": "", "Deposits": "", "Withdrawals": "", "Balance": ""}}
    ]
    }}

    Text:
    {text}
    """

    # Instantiate model
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    # ✅ Correct: no temperature argument
    response = model.generate_content(prompt)

    # Strip markdown code blocks if returned
    try:
        cleaned_text = response.text.strip("`").strip()
        data = json.loads(cleaned_text)
    except Exception as e:
        data = {"Gemini Output": response.text, "Error": str(e)}

    return data
