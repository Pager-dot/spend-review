import io
import re

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Spend Review", page_icon="💸", layout="wide")

# Each category is a list of keywords matched against the transaction narration.
RULES = {
    "Food & Dining": [
        "SWIGGY", "ZOMATO", "DOMINOS", "BURGER KING", "KFC", "PIZZA", "MCDONALD",
        "RESTAURANT", "CAFE", "KIIT HOSPITALITY", "FOOD NATION", "MISTHAN",
        "BAKERY", "DHABA", "BIRYANI", "CHAI", "JUICE", "SWEET", "HOTEL",
    ],
    "Groceries & Daily": [
        "BIGBASKET", "BLINKIT", "ZEPTO", "DMART", "D MART", "GROCER", "KIRANA",
        "VARIETY S", "VT STORE", "SUPERMARKET", "GENERAL STORE", "PROVISION",
        "MILK", "DAIRY",
    ],
    "Alcohol & Bars": [
        "BEER", "BREWING", "BARRELS", "WINE", "LIQUOR", "PUB", "BAR PAR",
    ],
    "Shopping": [
        "AMAZON", "FLIPKART", "MYNTRA", "AJIO", "MEESHO", "BATA", "NIKE",
        "ADIDAS", "DECATHLON", "RELIANCE TRENDS", "LIFESTYLE", "SHOPPING",
    ],
    "Subscriptions & Software": [
        "ANTHROPIC", "CLAUDE", "GOOGLECLOUD", "GOOGLE CLOUD", "OPENAI", "ORACLE",
        "RENDER.COM", "SPACESHIP", "GITHUB", "NETFLIX", "SPOTIFY", "PRIME",
        "YOUTUBE", "HOTSTAR", "ADOBE", "NOTION", "FIGMA", "VERCEL", "AWS",
        "MICROSOFT", "APPLE", "DC SI ", "EVERSUB",
    ],
    "Entertainment & Games": [
        "STEAMGAMES", "STEAM", "PLAYSTATION", "BOOKMYSHOW", "PVR", "INOX",
        "MULTIPLEX", "CINEMA", "GAMING",
    ],
    "Travel & Transport": [
        "INDIGO", "AIR INDIA", "SPICEJET", "AKASA", "IRCTC", "RAILWAY", "UBER",
        "OLA", "RAPIDO", "REDBUS", "MAKEMYTRIP", "GOIBIBO", "YATRA", "TRAVEL",
        "TOLL", "FASTAG", "PARKING", "PETROL", "FUEL", "HP PAY", "INDIAN OIL",
    ],
    "Education & Fees": [
        "KIIT", "KALINGA INSTITUT", "COLLEGE", "UNIVERSITY", "SCHOOL", "TUITION",
        "EXAM", "COURSE", "UDEMY", "COURSERA", "FEE",
    ],
    "Health & Medical": [
        "PHARMA", "MEDICAL", "HOSPITAL", "CLINIC", "APOLLO", "MEDPLUS",
        "DIAGNOSTIC", "LAB", "DOCTOR", "PHARMACY",
    ],
    "Bills & Recharge": [
        "AIRTEL", "JIO", "VODAFONE", "VI RECHARGE", "BSNL", "ELECTRIC",
        "ELECTRICITY", "GAS", "BROADBAND", "DTH", "RECHARGE", "BILLDESK",
        "BILLPAY", "WATER",
    ],
    "Government & Official": [
        "PASSPORT SEVA", "GOI", "INCOME TAX", "GST", "MUNICIPAL", "RTO",
        "POLICE", "COURT",
    ],
    "Bank Charges & Fees": [
        "ANNUAL FEE", "MARKUP", "DCC", "CHARGE", "CHRG", "GST", "SMS CHARGES",
        "AMB ", "PENAL", "MIN BAL", "ATM WDL CHG",
    ],
    "Cash & ATM": [
        "ATW-", "ATM-", "NWD-", "CASH WDL", "CASH DEP", "SELF",
    ],
    "Investments": [
        "ZERODHA", "GROWW", "UPSTOX", "MUTUAL FUND", "SIP ", "ANGEL ONE",
        "COIN", "BSE", "NSE", "INDIAN CLEARING",
    ],
    "Transfers to People": [
        "UPI-",  # fallback for person-to-person UPI, applied last
    ],
}

CATEGORY_ORDER = list(RULES.keys())


def categorise(narration: str) -> str:
    text = str(narration).upper()
    for category in CATEGORY_ORDER:
        if category == "Transfers to People":
            continue
        for keyword in RULES[category]:
            if keyword in text:
                return category
    if text.startswith("UPI-"):
        return "Transfers to People"
    return "Other"


def clean_merchant(narration: str) -> str:
    """Pull a readable payee name out of an HDFC narration string."""
    text = str(narration).strip()
    if text.upper().startswith("UPI-"):
        return text[4:].split("-")[0].strip().title() or text
    # POS / card transactions: drop the masked card number and timestamps.
    text = re.sub(r"\b\d{6}\*{6}\d{4}\b|\b\d{6}X{6}\d{4}\b", "", text)
    text = re.sub(r"\b\d{6}\s+\d{2}[A-Z]{3}\d{2}\s+[\d:]+\b", "", text)
    return " ".join(text.split())[:45].title()


# Deliberately NOT cached: caching would keep parsed statement rows in server
# memory across sessions. Re-parsing a few hundred rows is cheap.
def load_statement(file_bytes: bytes, name: str) -> pd.DataFrame:
    engine = "xlrd" if name.lower().endswith(".xls") else None
    raw = pd.read_excel(io.BytesIO(file_bytes), header=None, engine=engine)

    # Find the header row ("Date | Narration | ...") and start reading below it.
    header_idx = None
    for i, value in raw[0].items():
        if str(value).strip().lower() == "date":
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Could not find the transaction table in this file.")

    df = raw.iloc[header_idx + 1:, :7]
    df.columns = ["Date", "Narration", "RefNo", "ValueDate",
                  "Withdrawal", "Deposit", "Balance"]

    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
    for col in ("Withdrawal", "Deposit", "Balance"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["Date"].notna() & df["Narration"].notna()].copy()
    df["Withdrawal"] = df["Withdrawal"].fillna(0)
    df["Deposit"] = df["Deposit"].fillna(0)
    df["Category"] = df["Narration"].map(categorise)
    df["Payee"] = df["Narration"].map(clean_merchant)
    return df.reset_index(drop=True)


st.title("💸 Spend Review")
st.caption("Upload your HDFC bank statement (.xls / .xlsx) to see where the money went.")

uploaded = st.file_uploader("Bank statement", type=["xls", "xlsx"])
st.caption(
    "Nothing is saved. Your file is parsed in memory and discarded when you "
    "close the tab or upload another."
)

if uploaded is None:
    st.info("Pick a statement file to get started.")
    st.stop()

try:
    df = load_statement(uploaded.getvalue(), uploaded.name)
except Exception as exc:  # noqa: BLE001 - surface any parsing problem to the user
    st.error(f"Could not read that file: {exc}")
    st.stop()

spend = df[df["Withdrawal"] > 0]

c1, c2, c3 = st.columns(3)
c1.metric("Total spent", f"₹{spend['Withdrawal'].sum():,.0f}")
c2.metric("Total received", f"₹{df['Deposit'].sum():,.0f}")
c3.metric("Transactions", f"{len(df):,}")

st.subheader("Spending by category")
by_cat = (
    spend.groupby("Category")["Withdrawal"]
    .agg(Spent="sum", Count="count")
    .sort_values("Spent", ascending=False)
)
by_cat["Share %"] = (by_cat["Spent"] / by_cat["Spent"].sum() * 100).round(1)

st.bar_chart(by_cat["Spent"], horizontal=True)
st.dataframe(
    by_cat.style.format({"Spent": "₹{:,.0f}", "Share %": "{:.1f}%"}),
    use_container_width=True,
)

st.subheader("Top payees")
top = (
    spend.groupby(["Payee", "Category"])["Withdrawal"]
    .sum()
    .sort_values(ascending=False)
    .head(20)
    .reset_index()
)
st.dataframe(
    top.style.format({"Withdrawal": "₹{:,.0f}"}),
    use_container_width=True, hide_index=True,
)

st.subheader("All transactions")
chosen = st.multiselect(
    "Filter by category", sorted(df["Category"].unique()), default=[]
)
view = df[df["Category"].isin(chosen)] if chosen else df
st.dataframe(
    view[["Date", "Payee", "Category", "Withdrawal", "Deposit", "Balance", "Narration"]],
    use_container_width=True, hide_index=True,
    column_config={"Date": st.column_config.DateColumn(format="DD MMM YYYY")},
)

st.download_button(
    "Download categorised CSV",
    view.to_csv(index=False).encode(),
    file_name="categorised_spending.csv",
    mime="text/csv",
)
