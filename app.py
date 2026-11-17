
import streamlit as st
import pandas as pd
import base64
from pathlib import Path

import database
import ai_engine


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="CampusConnect AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

database.create_table()


# ==================================================
# 2. BACKGROUND IMAGE
# ==================================================

def add_background():

    image_path = Path(__file__).parent / "assets" / "campus.jpg"

    if image_path.exists() and image_path.stat().st_size > 0:

        try:
            with open(image_path, "rb") as file:
                encoded = base64.b64encode(file.read()).decode()

            css = f"""
            <style>
            .stApp {{
                background-image:
                    linear-gradient(
                        rgba(5, 12, 28, 0.90),
                        rgba(5, 12, 28, 0.94)
                    ),
                    url("data:image/jpeg;base64,{encoded}");

                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            </style>
            """

            st.markdown(css, unsafe_allow_html=True)

        except Exception:
            st.warning("Unable to load background image.")

    else:
        st.warning(
            "Background image not found. "
            "Check assets/campus.jpg."
        )


add_background()


# ==================================================
# 3. TEXT READABILITY AND UI DESIGN
# ==================================================

st.markdown("""
<style>

/* Main application */

.stApp {
    color: #F8FAFC;
    font-family: Arial, Helvetica, sans-serif;
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Headings */

h1 {
    color: #60A5FA !important;
    font-size: 38px !important;
    font-weight: 800 !important;
}

h2 {
    color: #93C5FD !important;
    font-size: 28px !important;
    font-weight: 750 !important;
}

h3 {
    color: #BFDBFE !important;
    font-size: 22px !important;
    font-weight: 700 !important;
}

/* Body text */

p, li, label, .stMarkdown {
    color: #F1F5F9 !important;
    font-size: 16px !important;
    line-height: 1.7 !important;
}

[data-testid="stCaptionContainer"] {
    color: #CBD5E1 !important;
    font-size: 14px !important;
}

/* Sidebar */

[data-testid="stSidebar"] {
    background: #0B1730 !important;
    border-right: 1px solid #263B5C;
}

[data-testid="stSidebar"] * {
    color: #F8FAFC !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2 {
    color: #60A5FA !important;
}

/* Metric cards */

[data-testid="stMetric"] {
    background: #102341 !important;
    border: 1px solid #31547D !important;
    border-radius: 14px !important;
    padding: 22px !important;
    box-shadow: 0 5px 18px rgba(0,0,0,0.25);
}

[data-testid="stMetricLabel"] {
    color: #CBD5E1 !important;
    font-size: 15px !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 32px !important;
    font-weight: 800 !important;
}

/* Text input fields */

.stTextInput input,
.stTextArea textarea {
    background: #F8FAFC !important;
    color: #111827 !important;
    border: 2px solid #64748B !important;
    border-radius: 8px !important;
    font-size: 16px !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #64748B !important;
    opacity: 1 !important;
}

/* Dropdowns */

[data-baseweb="select"] > div {
    background: #F8FAFC !important;
    color: #111827 !important;
    border: 1px solid #64748B !important;
}

[data-baseweb="select"] * {
    color: #111827 !important;
}

[data-baseweb="popover"],
[data-baseweb="menu"] {
    background: #FFFFFF !important;
}

[data-baseweb="menu"] * {
    color: #111827 !important;
}

/* Form labels */

.stTextInput label,
.stTextArea label,
.stSelectbox label {
    color: #FFFFFF !important;
    font-size: 16px !important;
    font-weight: 700 !important;
}

/* Buttons */

.stButton > button,
.stFormSubmitButton > button {
    background: #2563EB !important;
    color: #FFFFFF !important;
    border: 1px solid #60A5FA !important;
    border-radius: 9px !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    padding: 10px 20px !important;
    min-height: 45px !important;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #1D4ED8 !important;
    color: #FFFFFF !important;
}

/* Tables */

[data-testid="stDataFrame"] {
    background: #FFFFFF !important;
    border-radius: 10px !important;
}

/* Charts */

[data-testid="stVegaLiteChart"] {
    background: #FFFFFF !important;
    padding: 12px !important;
    border-radius: 12px !important;
}

/* Footer */

.footer {
    text-align: center;
    background: #0B1730;
    padding: 25px;
    border-radius: 12px;
    border: 1px solid #263B5C;
    margin-top: 35px;
}

.footer h3 {
    color: #60A5FA !important;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 4. HEADER
# ==================================================

st.title("🎓 CampusConnect AI")

st.subheader("Smart Campus Complaint Management System")

st.markdown(
    "A centralized platform to report, track and manage "
    "campus complaints using Artificial Intelligence."
)

st.divider()


# ==================================================
# 5. SIDEBAR NAVIGATION
# ==================================================

st.sidebar.title("🎓 CampusConnect AI")

st.sidebar.markdown("### Main Menu")

page = st.sidebar.selectbox(
    "Navigate to",
    [
        "Dashboard",
        "Submit Complaint",
        "View Complaints"
    ]
)

st.sidebar.divider()

st.sidebar.markdown("### About")

st.sidebar.write(
    "CampusConnect AI simplifies campus complaint "
    "management through intelligent categorization "
    "and priority prediction."
)


# ==================================================
# 6. LOAD COMPLAINTS
# ==================================================

def load_complaints():

    complaints = database.get_complaints()

    columns = [
        "ID",
        "Name",
        "Complaint",
        "Category",
        "Priority",
        "Status"
    ]

    if complaints is None or len(complaints) == 0:
        return pd.DataFrame(columns=columns)

    if isinstance(complaints, pd.DataFrame):

        df = complaints.copy()

        if len(df.columns) == 6:
            df.columns = columns

        return df

    return pd.DataFrame(
        complaints,
        columns=columns
    )


# ==================================================
# 7. NORMALIZE PRIORITY VALUES
# ==================================================

def normalize_priority(value):

    value = str(value).strip().lower()

    if value == "high":
        return "High"

    elif value == "medium":
        return "Medium"

    elif value == "low":
        return "Low"

    return "Medium"


def get_priority_counts(df):

    priority_order = ["High", "Medium", "Low"]

    if df.empty:

        return pd.Series(
            [0, 0, 0],
            index=priority_order,
            dtype=int
        )

    normalized = df["Priority"].apply(normalize_priority)

    return (
        normalized
        .value_counts()
        .reindex(priority_order, fill_value=0)
    )


# ==================================================
# 8. DASHBOARD
# ==================================================

if page == "Dashboard":

    st.header("📊 Dashboard")

    st.write(
        "Monitor campus complaints and understand "
        "the current complaint management status."
    )

    df = load_complaints()

    total = len(df)

    if total > 0:

        status = df["Status"].astype(str).str.strip().str.lower()

        pending = (status == "pending").sum()
        progress = status.isin(
            ["in progress", "in-progress", "inprogress"]
        ).sum()
        resolved = (status == "resolved").sum()

    else:

        pending = 0
        progress = 0
        resolved = 0

    # Dashboard metrics

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Complaints", total)
    col2.metric("Pending", int(pending))
    col3.metric("In Progress", int(progress))
    col4.metric("Resolved", int(resolved))

    st.divider()

    # Recent complaints

    st.subheader("📌 Recent Complaints")

    if total > 0:

        st.dataframe(
            df.tail(5).iloc[::-1],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No complaints have been submitted yet.")

    st.divider()

    # Analytics

    if total > 0:

        st.subheader("📈 Complaint Analytics")

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("### Complaints by Category")

            category_counts = df["Category"].value_counts()

            st.bar_chart(category_counts)

        with col2:

            st.markdown("### Complaints by Priority")

            priority_counts = get_priority_counts(df)

            st.bar_chart(priority_counts)

            st.caption(
                "Priority distribution: High, Medium and Low."
            )

        # Priority summary

        st.divider()

        st.subheader("⚡ Priority Summary")

        high, medium, low = st.columns(3)

        high.metric(
            "🔴 High Priority",
            int(priority_counts["High"])
        )

        medium.metric(
            "🟠 Medium Priority",
            int(priority_counts["Medium"])
        )

        low.metric(
            "🟢 Low Priority",
            int(priority_counts["Low"])
        )


# ==================================================
# 9. SUBMIT COMPLAINT
# ==================================================

elif page == "Submit Complaint":

    st.header("📝 Submit a Complaint")

    st.write(
        "Report any issue related to campus facilities "
        "or services. Our AI system will analyze your complaint."
    )

    st.divider()

    with st.form("complaint_form"):

        st.subheader("Personal Information")

        name = st.text_input(
            "Student / Faculty Name",
            placeholder="Enter your full name"
        )

        role = st.selectbox(
            "Select Your Role",
            [
                "Student",
                "Faculty",
                "Admin",
                "Maintenance Staff"
            ]
        )

        st.subheader("Complaint Information")

        location = st.selectbox(
            "Select Campus Location",
            [
                "Academic Block",
                "Library",
                "Computer Lab",
                "Classroom",
                "Canteen",
                "Hostel",
                "Parking Area",
                "Washroom",
                "Sports Ground",
                "Other"
            ]
        )

        complaint = st.text_area(
            "Describe Your Complaint",
            placeholder="Explain your problem clearly...",
            height=160
        )

        submitted = st.form_submit_button(
            "🚀 Submit Complaint",
            use_container_width=True
        )

        if submitted:

            if not name.strip() or not complaint.strip():

                st.error(
                    "Please fill in your name and complaint description."
                )

            else:

                full_complaint = (
                    f"Role: {role}. "
                    f"Location: {location}. "
                    f"Complaint: {complaint}"
                )

                try:

                    category, priority = (
                        ai_engine.analyze_complaint(full_complaint)
                    )

                    # Ensure standard priority value

                    priority = normalize_priority(priority)

                    database.add_complaint(
                        name,
                        full_complaint,
                        category,
                        priority
                    )

                    st.success(
                        "Complaint submitted successfully!"
                    )

                    st.subheader("🤖 AI Analysis Result")

                    col1, col2 = st.columns(2)

                    col1.metric(
                        "Predicted Category",
                        category
                    )

                    col2.metric(
                        "Predicted Priority",
                        priority
                    )

                    if priority == "High":

                        st.error(
                            "High priority: This complaint "
                            "requires urgent attention."
                        )

                    elif priority == "Medium":

                        st.warning(
                            "Medium priority: This complaint "
                            "requires timely attention."
                        )

                    else:

                        st.success(
                            "Low priority: This complaint "
                            "can be handled through routine maintenance."
                        )

                    st.balloons()

                except Exception as error:

                    st.error(
                        f"Complaint submission failed: {error}"
                    )


# ==================================================
# 10. VIEW COMPLAINTS
# ==================================================

elif page == "View Complaints":

    st.header("📋 Complaint Management")

    st.write(
        "View and filter complaints submitted by "
        "students and faculty members."
    )

    df = load_complaints()

    if df.empty:

        st.info("No complaints are available.")

    else:

        # Normalize priority for consistent filtering

        df["Priority"] = df["Priority"].apply(normalize_priority)

        st.subheader("🔎 Filter Complaints")

        col1, col2, col3 = st.columns(3)

        with col1:

            status_options = [
                "All"
            ] + sorted(
                df["Status"].dropna().astype(str).unique().tolist()
            )

            selected_status = st.selectbox(
                "Complaint Status",
                status_options
            )

        with col2:

            category_options = [
                "All"
            ] + sorted(
                df["Category"].dropna().astype(str).unique().tolist()
            )

            selected_category = st.selectbox(
                "Complaint Category",
                category_options
            )

        with col3:

            priority_options = [
                "All",
                "High",
                "Medium",
                "Low"
            ]

            selected_priority = st.selectbox(
                "Complaint Priority",
                priority_options
            )

        filtered_df = df.copy()

        if selected_status != "All":

            filtered_df = filtered_df[
                filtered_df["Status"] == selected_status
            ]

        if selected_category != "All":

            filtered_df = filtered_df[
                filtered_df["Category"] == selected_category
            ]

        if selected_priority != "All":

            filtered_df = filtered_df[
                filtered_df["Priority"] == selected_priority
            ]

        st.divider()

        st.subheader("Complaint Records")

        st.caption(
            f"Total matching complaints: {len(filtered_df)}"
        )

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # Analytics

        st.subheader("📈 Complaint Analytics")

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("### Complaints by Category")

            st.bar_chart(
                df["Category"].value_counts()
            )

        with col2:

            st.markdown("### Complaints by Priority")

            priority_counts = get_priority_counts(df)

            st.bar_chart(priority_counts)

        st.divider()

        st.subheader("⚡ Priority Distribution")

        priority_counts = get_priority_counts(df)

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "🔴 High",
            int(priority_counts["High"])
        )

        col2.metric(
            "🟠 Medium",
            int(priority_counts["Medium"])
        )

        col3.metric(
            "🟢 Low",
            int(priority_counts["Low"])
        )


# ==================================================
# 11. FOOTER
# ==================================================

st.markdown("""
<div class="footer">
    <h3>🎓 CampusConnect AI</h3>
    <p>Smart Campus | AI-Powered Complaint Management</p>
    <p>Developed using Python, Streamlit, SQLite and AI</p>
</div>
""", unsafe_allow_html=True)
