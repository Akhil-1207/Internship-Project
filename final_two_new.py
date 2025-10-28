import streamlit as st
import pandas as pd
import plotly.express as px
import yagmail
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import logging

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Employee Performance Dashboard", layout="wide")

# --- Styling ---
st.markdown(
    """
    <style>
    .chat-container { background: #121212; padding: 15px; border-radius: 10px; }
    .chat-message { padding: 8px; margin: 5px; border-radius: 8px; font-family: 'Open Sans'; font-size: 15px; }
    .user-message { background-color: #2B7A78; color: #FFF; text-align: right; margin-left: 20%; }
    .bot-message { background-color: #333; color: #FFF; text-align: left; margin-right: 20%; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Load Data ---
sheet_url = "https://docs.google.com/spreadsheets/d/1OxU_4C8zAp_3sqcmj2dnn4YB7N6xcI6PUPLWSG-yl4E/export?format=csv"
try:
    df = pd.read_csv(sheet_url)
except Exception as e:
    st.error("Failed to load data.")
    df = pd.DataFrame()

# --- Preprocessing ---
if not df.empty:
    df['Hire_Date'] = pd.to_datetime(df['Hire_Date'], errors='coerce')
    df['Years_At_Company'] = (pd.Timestamp.now() - df['Hire_Date']).dt.days / 365.25

# --- Sidebar Filters ---
st.sidebar.header("Filters")
departments = df['Department'].dropna().unique().tolist() if not df.empty else []
job_titles = df['Job_Title'].dropna().unique().tolist() if not df.empty else []
remote_options = ['All', 'Work From Home', 'Work From Office', 'Hybrid']
employee_ids = ['All'] + df['Employee_ID'].dropna().astype(str).unique().tolist() if not df.empty else ['All']

selected_employee = st.sidebar.selectbox("Select Employee ID", employee_ids)
selected_department = st.sidebar.selectbox("Select Department", ["All"] + departments)
selected_job = st.sidebar.selectbox("Select Job Title", ["All"] + job_titles)
selected_remote = st.sidebar.selectbox("Select Remote Work Type", remote_options)
date_range = st.sidebar.date_input(
    "Filter by Hire Date Range",
    [df['Hire_Date'].min(), df['Hire_Date'].max()] if not df.empty else [datetime.now(), datetime.now()]
)

# Apply Filters
filtered_df = df.copy() if not df.empty else pd.DataFrame()
if not filtered_df.empty:
    if selected_employee != "All":
        filtered_df = filtered_df[filtered_df['Employee_ID'] == selected_employee]
    if selected_department != "All":
        filtered_df = filtered_df[filtered_df['Department'] == selected_department]
    if selected_job != "All":
        filtered_df = filtered_df[filtered_df['Job_Title'] == selected_job]
    if selected_remote != "All":
        filtered_df = filtered_df[filtered_df['Remote_Work_Category'] == selected_remote]
    if len(date_range) == 2:
        filtered_df = filtered_df[(filtered_df['Hire_Date'] >= pd.to_datetime(date_range[0])) & (filtered_df['Hire_Date'] <= pd.to_datetime(date_range[1]))]

# --- Email Notifications ---
st.subheader("Email Notifications")
sender_email = "akhilmiriyala998@gmail.com"
receiver_admin_email = "akhilmiriyala998@gmail.com"
yag = yagmail.SMTP(user=sender_email, password="vqollmbkelbybdut")

col1, col2, col3 = st.columns(3)

# Button 1: Low Satisfaction
with col1:
    if st.button("Send Low Satisfaction"):
        low_sat_df = df[df['Satisfaction_Level'] == 'Low'] if not df.empty else pd.DataFrame()
        if not low_sat_df.empty:
            content = "Low Satisfaction Employees:\n" + "\n".join([f"EmpID: {row['Employee_ID']}, Dept: {row['Department']}, Job: {row['Job_Title']}" for _, row in low_sat_df.iterrows()])
            yag.send(to=receiver_admin_email, subject="🚨 Low Satisfaction", contents=content)
            st.success("✅ Low Satisfaction email sent.")
        else:
            st.info("No employees with low satisfaction.")

# Button 2: Low Performance
with col2:
    if st.button("Send Low Performance"):
        low_perf_df = df[df['Performance_Level'] == 'Low'] if not df.empty else pd.DataFrame()
        if not low_perf_df.empty:
            content = "Low Performance Employees:\n" + "\n".join([f"EmpID: {row['Employee_ID']}, Dept: {row['Department']}, Job: {row['Job_Title']}" for _, row in low_perf_df.iterrows()])
            yag.send(to=receiver_admin_email, subject="🚨 Low Performance", contents=content)
            st.success("✅ Low Performance email sent.")
        else:
            st.info("No employees with low performance.")

# Button 3: High Retention Risk
with col3:
    if st.button("Send High Retention Risk"):
        high_ret_df = df[df['Retention_Risk_Level'] == 'High'] if not df.empty else pd.DataFrame()
        if not high_ret_df.empty:
            content = "High Retention Risk Employees:\n" + "\n".join([f"EmpID: {row['Employee_ID']}, Dept: {row['Department']}, Job: {row['Job_Title']}" for _, row in high_ret_df.iterrows()])
            yag.send(to=receiver_admin_email, subject="🚨 High Retention Risk", contents=content)
            st.success("✅ High Retention Risk email sent.")
        else:
            st.info("No employees with high retention risk.")

# --- KPI Cards ---
if not filtered_df.empty:
    productivity_avg = filtered_df['Productivity score'].mean()
    avg_salary = filtered_df['Annual Salary'].mean() if 'Annual Salary' in filtered_df else 0
    num_employees = len(filtered_df)
    remote_eff = filtered_df['Remote_Work_Efficiency'].mean() if 'Remote_Work_Efficiency' in filtered_df else 0
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Remote Work Efficiency", f"{remote_eff:.2f}")
    col2.metric("Productivity Score", f"{productivity_avg:.2f}")
    col3.metric("Average Salary", f"${avg_salary:,.2f}")
    col4.metric("Employees", num_employees)

# --- Visual Analytics ---
st.subheader("Visual Analytics")

# Row 1 visuals
row1_col1, row1_col2 = st.columns(2)

# 1. Employee Count by Retention Risk Level and Job Title
with row1_col1:
    st.markdown("### Employee Count by Retention Risk Level and Job Title")
    retention_count = filtered_df.groupby(['Job_Title', 'Retention_Risk_Level'])['Employee_ID'].count().reset_index()
    retention_count.rename(columns={'Employee_ID': 'Number_of_Employees'}, inplace=True)
    fig_ret = px.bar(
        retention_count, x='Job_Title', y='Number_of_Employees', color='Retention_Risk_Level',
        color_discrete_sequence=px.colors.qualitative.Bold,
        title="Employee Count by Retention Risk Level"
    )
    st.plotly_chart(fig_ret, use_container_width=True)

# 2. Performance Level Distribution by Job Title
with row1_col2:
    st.markdown("### Performance Level Distribution by Job Title")
    tree_data = filtered_df.groupby(['Job_Title', 'Performance_Level'])['Employee_ID'].count().reset_index()
    tree_data.rename(columns={'Employee_ID': 'Number_of_Employees'}, inplace=True)
    fig_tree = px.treemap(
        tree_data, path=['Job_Title', 'Performance_Level'], values='Number_of_Employees', color='Performance_Level',
        color_discrete_map={'Low': '#FF4040', 'Medium': '#FFA500', 'High': '#228B22'},
        title="Performance Level by Job Title"
    )
    st.plotly_chart(fig_tree, use_container_width=True)

# Row 2 visual
st.markdown("### Remote Work Efficiency by Department")
remote_efficiency = filtered_df.groupby(['Department', 'Remote_Work_Category'])['Productivity score'].mean().reset_index()
fig_remote = px.bar(
    remote_efficiency, x='Department', y='Productivity score', color='Remote_Work_Category',
    color_discrete_sequence=px.colors.sequential.Tealgrn, barmode='group',
    title="Remote Work Efficiency by Department"
)
st.plotly_chart(fig_remote, use_container_width=True)

# Row 3 visuals
row3_col1, row3_col2, row3_col3 = st.columns(3)

# 3. Remote Work Type Distribution
with row3_col1:
    st.markdown("### Remote Work Type Distribution")
    remote_data = filtered_df['Remote_Work_Category'].value_counts().reset_index()
    remote_data.columns = ['Remote_Work_Category', 'Count']
    fig_pie = px.pie(remote_data, names='Remote_Work_Category', values='Count', color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig_pie, use_container_width=True)

# 4. Average Satisfaction by Department
with row3_col2:
    st.markdown("### Average Satisfaction by Department")
    sat_avg = filtered_df.groupby('Department')['Employee_Satisfaction_Score'].mean().reset_index()
    fig_sat = px.bar(sat_avg, x='Department', y='Employee_Satisfaction_Score', color='Department', color_discrete_sequence=px.colors.qualitative.Safe)
    st.plotly_chart(fig_sat, use_container_width=True)

# 5. Performance Trend by Years at Company
with row3_col3:
    st.markdown("### Performance Trend by Years at Company")
    filtered_df['Years_Bin'] = pd.cut(filtered_df['Years_At_Company'], bins=10).apply(lambda x: x.mid)
    trend_data = filtered_df.groupby(['Years_Bin', 'Job_Title'])['Performance_Score'].mean().reset_index()
    fig_line = px.line(trend_data, x='Years_Bin', y='Performance_Score', color='Job_Title', color_discrete_sequence=px.colors.qualitative.Plotly)
    st.plotly_chart(fig_line, use_container_width=True)

# --- Chatbot ---
st.subheader("Chatbot")
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for chat in st.session_state.chat_history:
    css_class = 'user-message' if chat['role'] == 'user' else 'bot-message'
    st.markdown(f"<div class='chat-message {css_class}'>{chat['message']}</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

input_col, btn_col = st.columns([5, 1])
with input_col:
    user_input = st.text_input("Type your question:", key="chat_input")
with btn_col:
    ask_pressed = st.button("Ask")

if ask_pressed and user_input:
    st.session_state.chat_history.append({"role": "user", "message": user_input})
    st.session_state.chat_history.append({"role": "bot", "message": "I'm processing your question..."})
    st.experimental_rerun()

if st.button("Delete Chat History"):
    st.session_state.chat_history.clear()
    st.success("Chat history deleted.")

st_autorefresh(interval=5 * 60 * 1000, key="data_refresh")
