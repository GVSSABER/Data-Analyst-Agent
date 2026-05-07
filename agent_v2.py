import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="AI Data Analyst", layout="wide")
st.title("📊 AI Data Analyst (Stable + Accurate)")

# =========================
# SESSION STATE
# =========================
if "df" not in st.session_state:
    st.session_state.df = None


# =========================
# LOAD DATA (SAFE FIX)
# =========================
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding="latin1")

    # clean column names
    df.columns = df.columns.str.strip().str.lower()

    # 🚨 DO NOT blindly convert everything to numeric
    for col in df.columns:
        # convert ONLY if column looks numeric
        df[col] = pd.to_numeric(df[col], errors="ignore")

    st.session_state.df = df

    st.success("✅ File loaded successfully")
    st.dataframe(df.head())

df = st.session_state.df


# =========================
# SMART COLUMN DETECTION
# =========================
def find_column(df, keywords):
    best_col = None
    best_score = 0

    for col in df.columns:
        score = sum(1 for k in keywords if k in col)
        if score > best_score:
            best_score = score
            best_col = col

    return best_col


def get_customer_column(df):
    for col in df.columns:
        if any(x in col for x in ["customer", "name", "client"]):
            return col
    return None


def get_numeric_df(df):
    return df.select_dtypes(include="number")


# =========================
# INTENT DETECTION
# =========================
def detect_intent(q):
    q = q.lower()

    if "total" in q or "sum" in q:
        return "sum"
    if "average" in q or "mean" in q:
        return "mean"
    if "top" in q or "highest" in q:
        return "top"

    return "other"


# =========================
# CORE ENGINE (NO AI BUGS)
# =========================
def generate_logic(question):
    if df is None:
        return None

    intent = detect_intent(question)
    num_df = get_numeric_df(df)

    # detect correct sales column
    sales_col = find_column(num_df, ["sales", "amount", "revenue", "price", "profit"])

    # =========================
    # TOTAL SALES (FIXED)
    # =========================
    if intent == "sum":
        if sales_col:
            return ("sum", sales_col)
        return ("sum_all", None)

    # =========================
    # AVERAGE
    # =========================
    if intent == "mean":
        if sales_col:
            return ("mean", sales_col)
        return ("mean_all", None)

    # =========================
    # TOP CUSTOMERS
    # =========================
    if intent == "top":
        customer_col = get_customer_column(df)
        return ("top", customer_col, sales_col)

    return ("head", None)


# =========================
# EXECUTION
# =========================
def run_logic(task):
    try:
        if df is None:
            return None

        num_df = get_numeric_df(df)

        if task[0] == "sum":
            col = task[1]
            return df[col].sum()

        if task[0] == "sum_all":
            return num_df.sum().sum()

        if task[0] == "mean":
            col = task[1]
            return df[col].mean()

        if task[0] == "mean_all":
            return num_df.mean().mean()

        if task[0] == "top":
            customer_col, sales_col = task[1], task[2]

            # FIX: fallback if wrong column
            if customer_col and sales_col:
                return (
                    df.groupby(customer_col)[sales_col]
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                )
            else:
                return num_df.sum().sort_values(ascending=False).head(10)

        return df.head()

    except Exception as e:
        st.error(f"Error: {e}")
        return df.head()


# =========================
# PLOT FIX
# =========================
def plot_result(result):
    if result is None:
        return

    plt.figure()

    if isinstance(result, pd.Series):
        result.head(10).plot(kind="bar")

    elif isinstance(result, pd.DataFrame):
        if result.shape[1] == 1:
            result.iloc[:, 0].value_counts().head(10).plot(kind="bar")
        else:
            st.dataframe(result)
            return
    else:
        st.write(result)
        return

    st.pyplot(plt)
    plt.clf()


# =========================
# UI
# =========================
question = st.text_input("Ask question (e.g. total sales, top customers)")

if st.button("Analyze"):

    if df is None:
        st.error("Upload CSV first")

    else:
        with st.spinner("Processing..."):

            task = generate_logic(question)
            result = run_logic(task)

            st.subheader("📊 Result")
            st.write(result)

            st.subheader("📈 Chart")
            plot_result(result)