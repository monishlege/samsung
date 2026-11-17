
import base64
import logging
import os
import time
from pathlib import Path

import pandas as pd
import streamlit as st

import database
import ai_engine

logger = logging.getLogger(__name__)


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="CampusConnect AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

def _read_setting(section, name, environment_name):
    value = os.environ.get(environment_name)
    if value:
        return value
    try:
        return st.secrets.get(section, {}).get(name)
    except FileNotFoundError:
        return None


database_path = _read_setting("database", "path", "CAMPUS_DB_PATH")
if database_path:
    database.configure_database(database_path)

database.create_table()

admin_username = _read_setting("auth", "admin_username", "CAMPUS_ADMIN_USERNAME")
admin_password = _read_setting("auth", "admin_password", "CAMPUS_ADMIN_PASSWORD")
if bool(admin_username) != bool(admin_password):
    raise RuntimeError(
        "Configure both auth.admin_username and auth.admin_password to bootstrap an administrator."
    )
if admin_username and admin_password:
    database.create_bootstrap_admin(admin_username, admin_password)


SESSION_IDLE_SECONDS = 30 * 60
SESSION_MAX_SECONDS = 12 * 60 * 60


def _clear_authenticated_session():
    for key in (
        "authenticated_user_id",
        "auth_session_started",
        "auth_last_activity",
    ):
        st.session_state.pop(key, None)


def _start_authenticated_session(account):
    now = time.time()
    st.session_state["authenticated_user_id"] = account["id"]
    st.session_state["auth_session_started"] = now
    st.session_state["auth_last_activity"] = now


def _get_authenticated_user():
    user_id = st.session_state.get("authenticated_user_id")
    if user_id is None:
        return None

    now = time.time()
    session_started = st.session_state.get("auth_session_started", now)
    last_activity = st.session_state.get("auth_last_activity", now)
    if (
        now - last_activity > SESSION_IDLE_SECONDS
        or now - session_started > SESSION_MAX_SECONDS
    ):
        _clear_authenticated_session()
        return None

    account = database.get_user_by_id(user_id)
    if account is None:
        _clear_authenticated_session()
        return None

    st.session_state["auth_last_activity"] = now
    return account


def _render_authentication():
    st.title("🎓 CampusConnect AI")
    st.subheader("Sign in to your campus account")
    sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])

    with sign_in_tab:
        with st.form("sign_in_form"):
            username = st.text_input("Username", max_chars=30)
            password = st.text_input(
                "Password",
                type="password",
                max_chars=1024,
            )
            submitted = st.form_submit_button(
                "Sign in",
                use_container_width=True,
            )
        if submitted:
            account = database.authenticate_user(username, password)
            if account is None:
                st.error("Sign-in failed. Check your credentials or try again later.")
            else:
                _start_authenticated_session(account)
                st.rerun()

    with sign_up_tab:
        st.caption(
            "Self-registration is available for students and faculty. "
            "An administrator assigns privileged roles."
        )
        with st.form("sign_up_form"):
            full_name = st.text_input("Full name", max_chars=120)
            new_username = st.text_input(
                "Choose a username",
                max_chars=30,
            )
            role = st.selectbox("Account type", ["Student", "Faculty"])
            new_password = st.text_input(
                "Password (at least 12 characters)",
                type="password",
                max_chars=1024,
            )
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                max_chars=1024,
            )
            submitted = st.form_submit_button(
                "Create account",
                use_container_width=True,
            )
        if submitted:
            if new_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                try:
                    user_id = database.create_user(
                        full_name,
                        new_username,
                        new_password,
                        role,
                    )
                except ValueError as error:
                    st.error(str(error))
                else:
                    account = database.get_user_by_id(user_id)
                    _start_authenticated_session(account)
                    st.rerun()

    if database.get_admin_count() == 0:
        st.warning(
            "No administrator is configured. Set auth.admin_username and "
            "auth.admin_password in Streamlit secrets; the password must be "
            "at least 16 characters."
        )


# ==================================================
# 2. BACKGROUND IMAGE
# ==================================================

def add_background():

    image_path = Path(__file__).parent / "campus.jpg"

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
            logger.exception("Unable to load the campus background image.")
            st.warning("Unable to load background image.")

    else:
        st.warning(
            "Background image not found. "
            "Check campus.jpg in the project folder."
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


user = _get_authenticated_user()
if user is None:
    _render_authentication()
    st.stop()


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
st.sidebar.write(f"Signed in as **{user['full_name']}** ({user['role']})")
if st.sidebar.button("Sign out", use_container_width=True):
    _clear_authenticated_session()
    st.rerun()

st.sidebar.markdown("### Main Menu")

pages = ["Dashboard", "Submit Complaint", "View Complaints"]
if user["role"] == "Admin":
    pages.append("User Management")

page = st.sidebar.selectbox(
    "Navigate to",
    pages
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

    can_view_all_complaints = user["role"] in {
        "Admin",
        "Maintenance Staff",
    }
    complaints = database.get_complaints(
        None if can_view_all_complaints else user["id"]
    )

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

        st.write(f"Submitting as **{user['full_name']}** ({user['role']}).")

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

            if not complaint.strip():

                st.error(
                    "Please fill in the complaint description."
                )

            else:

                full_complaint = (
                    f"Role: {user['role']}. "
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
                        user["id"],
                        user["full_name"],
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

                except Exception:
                    logger.exception("Complaint submission failed.")
                    st.error("Complaint submission failed. Please try again.")


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

elif page == "User Management":

    if user["role"] != "Admin":
        st.error("Administrator access is required.")
        st.stop()

    st.header("👥 User Management")
    st.write("Assign or change account roles. Only administrators can access this page.")

    users = database.get_users()
    if users.empty:
        st.info("No user accounts are available.")
    else:
        st.dataframe(
            users[["id", "full_name", "username", "role", "is_active", "created_at"]],
            use_container_width=True,
            hide_index=True,
        )

        accounts = users.to_dict("records")
        account_ids = [account["id"] for account in accounts]
        selected_user_id = st.selectbox(
            "Account",
            account_ids,
            format_func=lambda account_id: next(
                f"{account['full_name']} ({account['username']})"
                for account in accounts
                if account["id"] == account_id
            ),
        )
        selected_account = next(
            account
            for account in accounts
            if account["id"] == selected_user_id
        )
        roles = sorted(database.VALID_ROLES)
        current_role_index = roles.index(selected_account["role"])

        with st.form("user_role_form"):
            new_role = st.selectbox(
                "Role",
                roles,
                index=current_role_index,
            )
            role_submitted = st.form_submit_button("Update role")

        if role_submitted:
            try:
                database.update_user_role(
                    user["id"],
                    selected_user_id,
                    new_role,
                )
            except (PermissionError, ValueError) as error:
                st.error(str(error))
            else:
                st.success("User role updated.")
                st.rerun()


# ==================================================
# 12. FOOTER
# ==================================================

st.markdown("""
<div class="footer">
    <h3>🎓 CampusConnect AI</h3>
    <p>Smart Campus | AI-Powered Complaint Management</p>
    <p>Developed using Python, Streamlit, SQLite and AI</p>
</div>
""", unsafe_allow_html=True)
