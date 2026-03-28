import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import uuid
import plotly.express as px

# ---------------- FILES & FOLDERS ----------------
FILE = "students.csv"
CLASS_FILE = "classes.csv"
SUBJECT_FILE = "subjects.csv"
ATT_FILE = "attendance.csv"
FEE_FILE = "fees.csv"
MARK_FILE = "marks.csv"
IMG_FOLDER = "images"

os.makedirs(IMG_FOLDER, exist_ok=True)

st.set_page_config(page_title="Pro Student ERP", page_icon="🎓", layout="wide")


# ---------------- HELPER FUNCTIONS ----------------
def get_grade(marks):
    if marks >= 80:
        return "A+"
    elif marks >= 70:
        return "A"
    elif marks >= 60:
        return "A-"
    elif marks >= 50:
        return "B"
    elif marks >= 40:
        return "C"
    elif marks >= 33:
        return "D"
    else:
        return "F"


# Robust CSV Loader
def load_csv(file, cols):
    if os.path.exists(file):
        try:
            temp_df = pd.read_csv(file)
            for col in cols:
                if col not in temp_df.columns:
                    temp_df[col] = 0 if col in ['Roll', 'Age', 'Marks', 'Amount'] else ""
            return temp_df[cols]
        except Exception:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)


# Load Data
df = load_csv(FILE, ["ID", "Name", "Age", "Class", "Roll", "Date"])
class_df = load_csv(CLASS_FILE, ["Class"])
subject_df = load_csv(SUBJECT_FILE, ["Subject"])
att_df = load_csv(ATT_FILE, ["ID", "Date", "Status"])
fee_df = load_csv(FEE_FILE, ["ID", "Amount", "Status", "Date"])
mark_df = load_csv(MARK_FILE, ["ID", "Subject", "Marks", "Grade"])


# ---------------- LOGIN ----------------
def login():
    st.markdown("<h1 style='text-align: center;'>🔐 Pro ERP Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                if u == "admin" and p == "admin":
                    st.session_state["login"] = True
                    st.rerun()
                else:
                    st.error("Invalid Username or Password!")


if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()


def logout():
    st.session_state["login"] = False
    st.rerun()


# ---------------- SIDEBAR NAVIGATION ----------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=100)
st.sidebar.title("Pro ERP Menu")
menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", "🏫 Class & Subject", "🎓 Manage Students",
    "📅 Attendance", "💰 Fees Management", "📚 Marks & Grades", "🪪 ID Card"
])
st.sidebar.button("Logout", on_click=logout, type="primary")


def get_student_list():
    if not df.empty and "Class" in df.columns and "Roll" in df.columns:
        df_sorted = df.sort_values(by=["Class", "Roll"])
        return df_sorted.apply(lambda x: f"Class {x['Class']} - Roll {x['Roll']} : {x['Name']} ({x['ID']})",
                               axis=1).tolist()
    return []


# ---------------- DASHBOARD ----------------
if menu == "📊 Dashboard":
    st.title("📊 Smart Analytics Dashboard")

    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #0f172a); border-radius: 12px; padding: 20px; text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); color: #f8fafc; border: 1px solid #334155; transition: 0.3s;
    }
    .metric-card:hover { transform: translateY(-5px); border-color: #38bdf8; }
    .metric-value { font-size: 32px; font-weight: bold; color: #38bdf8; margin-top:10px; display:block; }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    total_students = len(df)
    total_classes = df["Class"].nunique() if len(df) > 0 else 0
    total_subjects = len(subject_df)

    present_count = len(att_df[att_df["Status"] == "Present"]) if not att_df.empty else 0
    attendance_rate = round((present_count / len(att_df)) * 100, 2) if len(att_df) > 0 else 0

    c1.markdown(f"<div class='metric-card'>👨‍🎓 Total Students<span class='metric-value'>{total_students}</span></div>",
                unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>🏫 Total Classes<span class='metric-value'>{total_classes}</span></div>",
                unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'>📚 Total Subjects<span class='metric-value'>{total_subjects}</span></div>",
                unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'>📅 Attendance Rate<span class='metric-value'>{attendance_rate}%</span></div>",
                unsafe_allow_html=True)

    st.markdown("<br><hr>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏫 Class-wise Students")
        if total_students > 0:
            fig_class = px.pie(df, names="Class", hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
            st.plotly_chart(fig_class, use_container_width=True)
        else:
            st.info("No student data available to display chart.")

    with col2:
        st.subheader("💰 Fees Overview")
        if len(fee_df) > 0:
            fee_summary = fee_df.groupby("Status")["Amount"].sum().reset_index()
            fig_fee = px.bar(fee_summary, x="Status", y="Amount", color="Status",
                             color_discrete_map={"Paid": "#22c55e", "Due": "#ef4444"})
            st.plotly_chart(fig_fee, use_container_width=True)
        else:
            st.info("No fees data available to display chart.")

# ---------------- CLASS & SUBJECT ----------------
elif menu == "🏫 Class & Subject":
    st.title("🏫 Setup Classes & Subjects")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader("Add New Class")
            new_class = st.text_input("Class Name")
            if st.button("Save Class", use_container_width=True):
                if new_class:
                    class_df = pd.concat([class_df, pd.DataFrame([[new_class]], columns=["Class"])])
                    class_df.to_csv(CLASS_FILE, index=False)
                    st.success("Class Added!")
                    st.rerun()
            st.dataframe(class_df, use_container_width=True, hide_index=True)

    with c2:
        with st.container(border=True):
            st.subheader("Add New Subject")
            new_sub = st.text_input("Subject Name")
            if st.button("Save Subject", use_container_width=True):
                if new_sub:
                    subject_df = pd.concat([subject_df, pd.DataFrame([[new_sub]], columns=["Subject"])])
                    subject_df.to_csv(SUBJECT_FILE, index=False)
                    st.success("Subject Added!")
                    st.rerun()
            st.dataframe(subject_df, use_container_width=True, hide_index=True)

# ---------------- MANAGE STUDENTS ----------------
elif menu == "🎓 Manage Students":
    st.title("🎓 Student Management")

    tab1, tab2 = st.tabs(["➕ Admit New Student", "📋 View & Delete Students"])

    with tab1:
        with st.form("add_student"):
            name = st.text_input("Full Name")
            age = st.number_input("Age", 4, 100)
            student_class = st.selectbox("Class", class_df["Class"]) if not class_df.empty else st.text_input("Class")
            roll = st.number_input("Roll Number", 1)
            submit = st.form_submit_button("Admit Student", type="primary")

            if submit and name:
                new_id = "STU-" + str(uuid.uuid4())[:6].upper()
                date = datetime.now().strftime("%Y-%m-%d")
                new = pd.DataFrame([[new_id, name, age, student_class, roll, date]], columns=df.columns)
                df = pd.concat([df, new])
                df.to_csv(FILE, index=False)
                st.success(f"Student '{name}' added successfully!")
                st.rerun()

    with tab2:
        if not df.empty:
            df_sorted = df.sort_values(by=["Class", "Roll"])
            st.dataframe(df_sorted, use_container_width=True, hide_index=True)

            st.subheader("🗑️ Delete Student")
            student_list = get_student_list()
            to_delete = st.selectbox("Select Student to Delete", student_list)

            if st.button("Delete Selected Student", type="primary"):
                del_id = to_delete.split("(")[-1].replace(")", "")
                df = df[df["ID"] != del_id]
                df.to_csv(FILE, index=False)
                st.success("Student deleted successfully!")
                st.rerun()
        else:
            st.info("No students admitted yet.")

# ---------------- ATTENDANCE ----------------
elif menu == "📅 Attendance":
    st.title("📅 Attendance Management")
    tab1, tab2 = st.tabs(["➕ Mark Attendance", "📊 Attendance Records"])

    student_list = get_student_list()

    with tab1:
        if student_list:
            sel_student = st.selectbox("Select Student", student_list)
            status = st.radio("Status", ["Present", "Absent"], horizontal=True)
            if st.button("Submit Attendance", type="primary"):
                stu_id = sel_student.split("(")[-1].replace(")", "")
                new = pd.DataFrame([[stu_id, datetime.now().strftime("%Y-%m-%d"), status]], columns=att_df.columns)
                att_df = pd.concat([att_df, new])
                att_df.to_csv(ATT_FILE, index=False)
                st.success("Attendance Recorded!")
                st.rerun()
        else:
            st.warning("Please add students first.")

    with tab2:
        if not att_df.empty:
            display_att = pd.merge(att_df, df[['ID', 'Name', 'Class', 'Roll']], on="ID", how="left")
            st.dataframe(display_att[['Class', 'Roll', 'Name', 'Date', 'Status']], use_container_width=True,
                         hide_index=True)

            st.subheader("🗑️ Delete Record")
            del_options = [(idx, f"{row['Date']} - {display_att.loc[idx, 'Name']} - {row['Status']}") for idx, row in
                           att_df.iterrows()]
            if del_options:
                del_idx = st.selectbox("Select record to delete", del_options, format_func=lambda x: x[1])
                if st.button("Delete Record"):
                    att_df = att_df.drop(del_idx[0]).reset_index(drop=True)
                    att_df.to_csv(ATT_FILE, index=False)
                    st.success("Deleted!")
                    st.rerun()

# ---------------- FEES ----------------
elif menu == "💰 Fees Management":
    st.title("💰 Fees Collection")
    tab1, tab2 = st.tabs(["➕ Collect Fees", "📋 Fees Records"])

    student_list = get_student_list()

    with tab1:
        if student_list:
            sel_student = st.selectbox("Select Student", student_list)
            amt = st.number_input("Amount", 0)
            status = st.selectbox("Status", ["Paid", "Due"])
            if st.button("Save Payment", type="primary"):
                stu_id = sel_student.split("(")[-1].replace(")", "")
                new = pd.DataFrame([[stu_id, amt, status, datetime.now().strftime("%Y-%m-%d")]], columns=fee_df.columns)
                fee_df = pd.concat([fee_df, new])
                fee_df.to_csv(FEE_FILE, index=False)
                st.success("Fees Recorded!")
                st.rerun()
        else:
            st.warning("No students available.")

    with tab2:
        if not fee_df.empty:
            display_fee = pd.merge(fee_df, df[['ID', 'Name', 'Class']], on="ID", how="left")
            st.dataframe(display_fee[['Class', 'Name', 'Amount', 'Status', 'Date']], use_container_width=True,
                         hide_index=True)

            st.subheader("🗑️ Delete Fee Record")
            del_options = [(idx, f"{display_fee.loc[idx, 'Name']} - {row['Amount']} ({row['Status']})") for idx, row in
                           fee_df.iterrows()]
            if del_options:
                del_idx = st.selectbox("Select fee to delete", del_options, format_func=lambda x: x[1])
                if st.button("Delete Fee Record"):
                    fee_df = fee_df.drop(del_idx[0]).reset_index(drop=True)
                    fee_df.to_csv(FEE_FILE, index=False)
                    st.success("Deleted!")
                    st.rerun()

# ---------------- MARKS & GRADES ----------------
elif menu == "📚 Marks & Grades":
    st.title("📚 Exam Marks & Grading System")

    tab1, tab2 = st.tabs(["➕ Add Marks", "📊 View & Delete Marks"])
    student_list = get_student_list()

    with tab1:
        if student_list and not subject_df.empty:
            sel_student = st.selectbox("Select Student", student_list)
            sel_sub = st.selectbox("Select Subject", subject_df["Subject"])
            marks = st.number_input("Marks Obtained", 0, 100)

            if st.button("Save Marks", type="primary"):
                stu_id = sel_student.split("(")[-1].replace(")", "")
                grade = get_grade(marks)
                new = pd.DataFrame([[stu_id, sel_sub, marks, grade]], columns=mark_df.columns)
                mark_df = pd.concat([mark_df, new])
                mark_df.to_csv(MARK_FILE, index=False)
                st.success(f"Marks Added! Automatically Assigned Grade: {grade}")
                st.rerun()
        else:
            st.warning("Please make sure Students and Subjects are added first.")

    with tab2:
        if not mark_df.empty:
            display_marks = pd.merge(mark_df, df[['ID', 'Name', 'Class', 'Roll']], on="ID", how="left")
            st.dataframe(display_marks[['Class', 'Roll', 'Name', 'Subject', 'Marks', 'Grade']],
                         use_container_width=True, hide_index=True)

            st.subheader("🗑️ Delete Marks Record")
            del_options = [(idx, f"{display_marks.loc[idx, 'Name']} - {row['Subject']} (Marks: {row['Marks']})") for
                           idx, row in mark_df.iterrows()]
            if del_options:
                del_idx = st.selectbox("Select mark entry to delete", del_options, format_func=lambda x: x[1])
                if st.button("Delete Record"):
                    mark_df = mark_df.drop(del_idx[0]).reset_index(drop=True)
                    mark_df.to_csv(MARK_FILE, index=False)
                    st.success("Deleted successfully!")
                    st.rerun()

# ---------------- ID CARD ----------------
elif menu == "🪪 ID Card":
    st.title("🪪 Generate Professional ID Card")
    student_list = get_student_list()

    if student_list:
        sel_student = st.selectbox("Select Student", student_list)
        stu_id = sel_student.split("(")[-1].replace(")", "")
        s = df[df["ID"] == stu_id].iloc[0]

        st.info("Click below to generate and download a print-ready PDF ID Card.")

        if st.button("📄 Generate ID Card", type="primary"):
            pdf = FPDF()
            pdf.add_page()

            pdf.set_draw_color(56, 189, 248)
            pdf.set_line_width(1.5)
            pdf.rect(50, 40, 110, 85)

            pdf.set_fill_color(30, 41, 59)
            pdf.rect(50, 40, 110, 20, style="DF")

            pdf.set_font("Arial", "B", 18)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(50, 45)
            pdf.cell(110, 10, "STUDENT ID CARD", align="C")

            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", "B", 12)
            pdf.set_xy(60, 70)
            pdf.cell(0, 10, f"Name    :  {s['Name']}")
            pdf.set_xy(60, 80)
            pdf.cell(0, 10, f"Class     :  {s['Class']}")
            pdf.set_xy(60, 90)
            pdf.cell(0, 10, f"Roll No  :  {s['Roll']}")
            pdf.set_xy(60, 100)
            pdf.cell(0, 10, f"ID No     :  {s['ID']}")

            pdf_bytes = pdf.output(dest="S").encode("latin1")

            st.success("ID Card Generated Successfully! Download below:")
            st.download_button("⬇️ Download PDF ID Card", data=pdf_bytes, file_name=f"{s['Name']}_ID.pdf",
                               mime="application/pdf")
    else:
        st.warning("Please admit students first to generate ID cards.")