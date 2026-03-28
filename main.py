import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import uuid
import plotly.express as px
import plotly.graph_objects as go
import hashlib

# ─────────────────────────────────────────────
#  FILE & FOLDER CONSTANTS
# ─────────────────────────────────────────────
FILE         = "students.csv"
CLASS_FILE   = "classes.csv"
SUBJECT_FILE = "subjects.csv"
ATT_FILE     = "attendance.csv"
FEE_FILE     = "fees.csv"
MARK_FILE    = "marks.csv"
TEACHER_FILE = "teachers.csv"
USERS_FILE   = "users.csv"
IMG_FOLDER   = "images"

os.makedirs(IMG_FOLDER, exist_ok=True)

st.set_page_config(
    page_title="EduPro ERP",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── sidebar ── */
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0f172a 0%,#1e293b 100%); }
[data-testid="stSidebar"] * { color:#cbd5e1 !important; }
[data-testid="stSidebar"] .stRadio label { font-size:14px; padding:4px 0; }

/* ── metric cards ── */
.kpi { background:linear-gradient(135deg,#1e293b,#0f172a); border-radius:14px;
       padding:22px 18px; text-align:center; border:1px solid #334155;
       transition:.3s; box-shadow:0 4px 14px rgba(0,0,0,.4); }
.kpi:hover { transform:translateY(-4px); border-color:#38bdf8; }
.kpi-icon { font-size:28px; }
.kpi-label { font-size:13px; color:#94a3b8; margin-top:6px; }
.kpi-value { font-size:34px; font-weight:800; color:#38bdf8; margin-top:4px; }

/* ── section card ── */
.card { background:#1e293b; border-radius:12px; padding:20px;
        border:1px solid #334155; margin-bottom:16px; }

/* ── page title ── */
.page-title { font-size:26px; font-weight:700; color:#f1f5f9;
              border-left:4px solid #38bdf8; padding-left:12px; margin-bottom:20px; }

/* ── badge ── */
.badge-paid   { background:#166534; color:#bbf7d0; padding:2px 10px; border-radius:20px; font-size:12px; }
.badge-due    { background:#7f1d1d; color:#fecaca; padding:2px 10px; border-radius:20px; font-size:12px; }
.badge-present{ background:#14532d; color:#bbf7d0; padding:2px 10px; border-radius:20px; font-size:12px; }
.badge-absent { background:#7f1d1d; color:#fca5a5; padding:2px 10px; border-radius:20px; font-size:12px; }

/* general button override */
div.stButton > button[kind="primary"] {
    background:linear-gradient(90deg,#0ea5e9,#6366f1);
    color:#fff; border:none; border-radius:8px; font-weight:600;
}
div.stButton > button[kind="primary"]:hover { opacity:.88; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HELPER UTILITIES
# ─────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def load_csv(file: str, cols: list) -> pd.DataFrame:
    if os.path.exists(file):
        try:
            tmp = pd.read_csv(file)
            for c in cols:
                if c not in tmp.columns:
                    tmp[c] = 0 if c in ["Roll", "Age", "Marks", "Amount"] else ""
            return tmp[cols]
        except Exception:
            pass
    return pd.DataFrame(columns=cols)


def save_csv(df: pd.DataFrame, file: str):
    df.to_csv(file, index=False)


def get_grade(marks: float) -> str:
    if marks >= 80: return "A+"
    if marks >= 70: return "A"
    if marks >= 60: return "A-"
    if marks >= 50: return "B"
    if marks >= 40: return "C"
    if marks >= 33: return "D"
    return "F"


# ─────────────────────────────────────────────
#  LOAD DATA  (cached so reloads are cheap)
# ─────────────────────────────────────────────
@st.cache_data(ttl=5)
def load_all():
    students = load_csv(FILE, [
        "ID", "Name", "Age", "Class", "Roll", "Gender",
        "Phone", "Email", "Address",
        "Father_Name", "Father_Phone", "Father_Occupation",
        "Mother_Name", "Mother_Phone", "Mother_Occupation",
        "Date",
    ])
    classes   = load_csv(CLASS_FILE,   ["Class"])
    subjects  = load_csv(SUBJECT_FILE, ["Subject"])
    att       = load_csv(ATT_FILE,     ["ID", "Date", "Status"])
    fees      = load_csv(FEE_FILE,     ["ID", "Amount", "Status", "Date"])
    marks     = load_csv(MARK_FILE,    ["ID", "Subject", "Marks", "Grade"])
    teachers  = load_csv(TEACHER_FILE, [
        "T_ID", "Name", "Subject", "Class", "Phone", "Email", "Qualification", "Join_Date",
    ])
    users     = load_csv(USERS_FILE,   ["Username", "Password", "Role"])
    # seed default admin if no users
    if users.empty:
        users = pd.DataFrame([["admin", hash_pw("admin"), "Admin"]], columns=["Username", "Password", "Role"])
        save_csv(users, USERS_FILE)
    return students, classes, subjects, att, fees, marks, teachers, users

df, class_df, subject_df, att_df, fee_df, mark_df, teacher_df, users_df = load_all()


def refresh():
    st.cache_data.clear()
    st.rerun()


def get_student_list(df_: pd.DataFrame) -> list:
    if df_.empty:
        return []
    s = df_.sort_values(["Class", "Roll"])
    return s.apply(
        lambda r: f"Class {r['Class']} | Roll {r['Roll']} | {r['Name']}  ({r['ID']})", axis=1
    ).tolist()


def student_id_from_sel(sel: str) -> str:
    return sel.split("(")[-1].replace(")", "").strip()


# ─────────────────────────────────────────────
#  LOGIN / AUTH
# ─────────────────────────────────────────────
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; margin-bottom:24px;'>
          <div style='font-size:60px;'>🎓</div>
          <h1 style='color:#f1f5f9; margin:0;'>EduPro ERP</h1>
          <p style='color:#94a3b8;'>School Management System</p>
        </div>""", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### 🔐 Sign In")
            u = st.text_input("Username", placeholder="Enter username")
            p = st.text_input("Password", type="password", placeholder="Enter password")
            if st.button("Login", type="primary", use_container_width=True):
                _, _, _, _, _, _, _, users = load_all()
                match = users[(users["Username"] == u) & (users["Password"] == hash_pw(p))]
                if not match.empty:
                    st.session_state["login"] = True
                    st.session_state["username"] = u
                    st.session_state["role"] = match.iloc[0]["Role"]
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials!")


if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_page()
    st.stop()


def logout():
    for k in ["login", "username", "role"]:
        st.session_state.pop(k, None)
    st.rerun()


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
st.sidebar.markdown("""
<div style='text-align:center; padding:16px 0 8px;'>
  <div style='font-size:48px;'>🎓</div>
  <div style='font-size:18px; font-weight:700; color:#f1f5f9;'>EduPro ERP</div>
  <div style='font-size:12px; color:#64748b; margin-top:4px;'>School Management System</div>
</div>
<hr style='border-color:#334155; margin:8px 0 16px;'>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"👤 **{st.session_state.get('username','Admin')}** "
                    f"<span style='font-size:11px; color:#64748b;'>({st.session_state.get('role','Admin')})</span>",
                    unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border-color:#334155;'>", unsafe_allow_html=True)

menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard",
    "🏫 Class & Subject",
    "🎓 Manage Students",
    "👨‍🏫 Teachers",
    "📅 Attendance",
    "💰 Fees Management",
    "📚 Marks & Grades",
    "🪪 ID Card",
    "🔑 User Management",
])
st.sidebar.markdown("<hr style='border-color:#334155;'>", unsafe_allow_html=True)
st.sidebar.button("🚪 Logout", on_click=logout, type="primary", use_container_width=True)


# ─────────────────────────────────────────────
#  1. DASHBOARD
# ─────────────────────────────────────────────
if menu == "📊 Dashboard":
    st.markdown("<div class='page-title'>📊 Smart Analytics Dashboard</div>", unsafe_allow_html=True)

    total_students  = len(df)
    total_classes   = df["Class"].nunique() if total_students else 0
    total_subjects  = len(subject_df)
    total_teachers  = len(teacher_df)
    present_count   = len(att_df[att_df["Status"] == "Present"]) if not att_df.empty else 0
    att_rate        = round((present_count / len(att_df)) * 100, 1) if len(att_df) > 0 else 0
    total_collected = fee_df[fee_df["Status"] == "Paid"]["Amount"].sum() if not fee_df.empty else 0
    total_due       = fee_df[fee_df["Status"] == "Due"]["Amount"].sum()  if not fee_df.empty else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    kpis = [
        (c1, "👨‍🎓", "Students",       total_students),
        (c2, "🏫", "Classes",         total_classes),
        (c3, "📚", "Subjects",        total_subjects),
        (c4, "👨‍🏫", "Teachers",        total_teachers),
        (c5, "📅", "Attendance %",    f"{att_rate}%"),
        (c6, "💰", "Fees Collected",  f"৳{int(total_collected):,}"),
    ]
    for col, icon, label, val in kpis:
        col.markdown(f"""
        <div class='kpi'>
          <div class='kpi-icon'>{icon}</div>
          <div class='kpi-label'>{label}</div>
          <div class='kpi-value'>{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        st.markdown("#### 🏫 Class-wise Student Distribution")
        if total_students > 0:
            fig = px.pie(df, names="Class", hole=0.45,
                         color_discrete_sequence=px.colors.sequential.Teal)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#cbd5e1", legend_font_color="#cbd5e1")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No student data yet.")

    with r1c2:
        st.markdown("#### 💰 Fee Collection Overview")
        if not fee_df.empty:
            summary = fee_df.groupby("Status")["Amount"].sum().reset_index()
            fig = px.bar(summary, x="Status", y="Amount", color="Status",
                         color_discrete_map={"Paid": "#22c55e", "Due": "#ef4444"},
                         text_auto=True)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#cbd5e1")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No fee data yet.")

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown("#### 📅 Attendance – Present vs Absent")
        if not att_df.empty:
            a_sum = att_df.groupby("Status").size().reset_index(name="Count")
            fig2 = px.pie(a_sum, names="Status", values="Count", hole=0.4,
                          color="Status",
                          color_discrete_map={"Present": "#22c55e", "Absent": "#ef4444"})
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No attendance data yet.")

    with r2c2:
        st.markdown("#### 📚 Average Marks per Subject")
        if not mark_df.empty:
            avg = mark_df.groupby("Subject")["Marks"].mean().reset_index()
            avg.columns = ["Subject", "Avg Marks"]
            fig3 = px.bar(avg, x="Subject", y="Avg Marks", color="Avg Marks",
                          color_continuous_scale="Blues", text_auto=".1f")
            fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No marks data yet.")


# ─────────────────────────────────────────────
#  2. CLASS & SUBJECT
# ─────────────────────────────────────────────
elif menu == "🏫 Class & Subject":
    st.markdown("<div class='page-title'>🏫 Classes & Subjects Setup</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("##### ➕ Add Class")
            nc = st.text_input("Class Name", key="nc")
            if st.button("Save Class", type="primary", use_container_width=True):
                if nc.strip():
                    new_class_df = pd.concat([class_df, pd.DataFrame([[nc.strip()]], columns=["Class"])], ignore_index=True)
                    save_csv(new_class_df, CLASS_FILE)
                    st.success("✅ Class added!")
                    refresh()
                else:
                    st.warning("Enter a class name.")

            st.markdown("##### 📋 Existing Classes")
            st.dataframe(class_df, use_container_width=True, hide_index=True)

            if not class_df.empty:
                del_cls = st.selectbox("Delete Class", class_df["Class"].tolist(), key="del_cls")
                if st.button("🗑️ Delete Class", key="btn_del_cls"):
                    new_class_df = class_df[class_df["Class"] != del_cls].reset_index(drop=True)
                    save_csv(new_class_df, CLASS_FILE)
                    st.success("Deleted!")
                    refresh()

    with c2:
        with st.container(border=True):
            st.markdown("##### ➕ Add Subject")
            ns = st.text_input("Subject Name", key="ns")
            if st.button("Save Subject", type="primary", use_container_width=True):
                if ns.strip():
                    new_sub_df = pd.concat([subject_df, pd.DataFrame([[ns.strip()]], columns=["Subject"])], ignore_index=True)
                    save_csv(new_sub_df, SUBJECT_FILE)
                    st.success("✅ Subject added!")
                    refresh()
                else:
                    st.warning("Enter a subject name.")

            st.markdown("##### 📋 Existing Subjects")
            st.dataframe(subject_df, use_container_width=True, hide_index=True)

            if not subject_df.empty:
                del_sub = st.selectbox("Delete Subject", subject_df["Subject"].tolist(), key="del_sub")
                if st.button("🗑️ Delete Subject", key="btn_del_sub"):
                    new_sub_df = subject_df[subject_df["Subject"] != del_sub].reset_index(drop=True)
                    save_csv(new_sub_df, SUBJECT_FILE)
                    st.success("Deleted!")
                    refresh()


# ─────────────────────────────────────────────
#  3. MANAGE STUDENTS
# ─────────────────────────────────────────────
elif menu == "🎓 Manage Students":
    st.markdown("<div class='page-title'>🎓 Student Management</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["➕ Admit Student", "✏️ Update Student", "📋 View / Delete"])

    # ── TAB 1: ADD ──
    with tab1:
        with st.container(border=True):
            st.markdown("##### 👤 Personal Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                name    = st.text_input("Full Name *")
                gender  = st.selectbox("Gender", ["Male", "Female", "Other"])
                age     = st.number_input("Age", 4, 100, 10)
            with col2:
                cls_opts = class_df["Class"].tolist() if not class_df.empty else ["N/A"]
                s_class = st.selectbox("Class *", cls_opts)
                roll    = st.number_input("Roll Number *", 1, 9999, 1)
                phone   = st.text_input("Student Phone")
            with col3:
                email   = st.text_input("Email")
                address = st.text_area("Address", height=96)

            st.markdown("##### 👨‍👩‍👧 Parent / Guardian Information")
            p1, p2 = st.columns(2)
            with p1:
                st.markdown("###### Father")
                f_name  = st.text_input("Father's Name")
                f_phone = st.text_input("Father's Phone")
                f_occ   = st.text_input("Father's Occupation")
            with p2:
                st.markdown("###### Mother")
                m_name  = st.text_input("Mother's Name")
                m_phone = st.text_input("Mother's Phone")
                m_occ   = st.text_input("Mother's Occupation")

            if st.button("✅ Admit Student", type="primary"):
                if not name.strip():
                    st.error("Full Name is required.")
                else:
                    new_id = "STU-" + str(uuid.uuid4())[:6].upper()
                    today  = datetime.now().strftime("%Y-%m-%d")
                    row = pd.DataFrame([[
                        new_id, name.strip(), age, s_class, roll, gender,
                        phone, email, address,
                        f_name, f_phone, f_occ,
                        m_name, m_phone, m_occ,
                        today,
                    ]], columns=df.columns)
                    new_df = pd.concat([df, row], ignore_index=True)
                    save_csv(new_df, FILE)
                    st.success(f"🎉 Student **{name}** admitted! ID: `{new_id}`")
                    st.balloons()
                    refresh()

    # ── TAB 2: UPDATE ──
    with tab2:
        if df.empty:
            st.info("No students to update.")
        else:
            s_list = get_student_list(df)
            sel    = st.selectbox("Select Student to Update", s_list, key="upd_sel")
            stu_id = student_id_from_sel(sel)
            row    = df[df["ID"] == stu_id].iloc[0]

            with st.container(border=True):
                st.markdown("##### ✏️ Edit Details")
                col1, col2, col3 = st.columns(3)
                with col1:
                    u_name   = st.text_input("Full Name",  value=row["Name"],   key="u_name")
                    u_gender = st.selectbox("Gender", ["Male","Female","Other"],
                                            index=["Male","Female","Other"].index(row["Gender"]) if row["Gender"] in ["Male","Female","Other"] else 0,
                                            key="u_gender")
                    u_age    = st.number_input("Age", 4, 100, int(row["Age"]),  key="u_age")
                with col2:
                    cls_opts = class_df["Class"].tolist() if not class_df.empty else [row["Class"]]
                    u_class  = st.selectbox("Class", cls_opts,
                                            index=cls_opts.index(row["Class"]) if row["Class"] in cls_opts else 0,
                                            key="u_class")
                    u_roll   = st.number_input("Roll", 1, 9999, int(row["Roll"]), key="u_roll")
                    u_phone  = st.text_input("Phone",   value=str(row["Phone"]),   key="u_phone")
                with col3:
                    u_email  = st.text_input("Email",   value=str(row["Email"]),   key="u_email")
                    u_addr   = st.text_area("Address",  value=str(row["Address"]), height=96, key="u_addr")

                st.markdown("##### 👨‍👩‍👧 Parent Information")
                pp1, pp2 = st.columns(2)
                with pp1:
                    u_fn = st.text_input("Father Name",       value=str(row["Father_Name"]),       key="u_fn")
                    u_fp = st.text_input("Father Phone",      value=str(row["Father_Phone"]),      key="u_fp")
                    u_fo = st.text_input("Father Occupation", value=str(row["Father_Occupation"]), key="u_fo")
                with pp2:
                    u_mn = st.text_input("Mother Name",       value=str(row["Mother_Name"]),       key="u_mn")
                    u_mp = st.text_input("Mother Phone",      value=str(row["Mother_Phone"]),      key="u_mp")
                    u_mo = st.text_input("Mother Occupation", value=str(row["Mother_Occupation"]), key="u_mo")

                if st.button("💾 Save Changes", type="primary"):
                    idx = df.index[df["ID"] == stu_id][0]
                    df.at[idx, "Name"]               = u_name
                    df.at[idx, "Gender"]             = u_gender
                    df.at[idx, "Age"]                = u_age
                    df.at[idx, "Class"]              = u_class
                    df.at[idx, "Roll"]               = u_roll
                    df.at[idx, "Phone"]              = u_phone
                    df.at[idx, "Email"]              = u_email
                    df.at[idx, "Address"]            = u_addr
                    df.at[idx, "Father_Name"]        = u_fn
                    df.at[idx, "Father_Phone"]       = u_fp
                    df.at[idx, "Father_Occupation"]  = u_fo
                    df.at[idx, "Mother_Name"]        = u_mn
                    df.at[idx, "Mother_Phone"]       = u_mp
                    df.at[idx, "Mother_Occupation"]  = u_mo
                    save_csv(df, FILE)
                    st.success("✅ Student updated successfully!")
                    refresh()

    # ── TAB 3: VIEW / DELETE ──
    with tab3:
        if df.empty:
            st.info("No students admitted yet.")
        else:
            # search
            search = st.text_input("🔍 Search by Name / ID / Class")
            disp = df.copy().sort_values(["Class", "Roll"])
            if search:
                q = search.lower()
                disp = disp[disp.apply(lambda r: q in str(r["Name"]).lower()
                                        or q in str(r["ID"]).lower()
                                        or q in str(r["Class"]).lower(), axis=1)]

            st.markdown(f"**{len(disp)} student(s) found**")
            st.dataframe(disp[[
                "ID","Name","Age","Gender","Class","Roll",
                "Phone","Father_Name","Mother_Name","Date"
            ]], use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("##### 🗑️ Delete Student")
            s_list = get_student_list(df)
            to_del = st.selectbox("Select", s_list, key="del_stu")
            if st.button("Delete Student", type="primary"):
                del_id = student_id_from_sel(to_del)
                new_df = df[df["ID"] != del_id].reset_index(drop=True)
                save_csv(new_df, FILE)
                st.success("Student deleted.")
                refresh()


# ─────────────────────────────────────────────
#  4. TEACHERS
# ─────────────────────────────────────────────
elif menu == "👨‍🏫 Teachers":
    st.markdown("<div class='page-title'>👨‍🏫 Teacher Management</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["➕ Add Teacher", "✏️ Update Teacher", "📋 View / Delete"])

    with tab1:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                t_name  = st.text_input("Full Name *")
                t_phone = st.text_input("Phone")
                t_email = st.text_input("Email")
                t_qual  = st.text_input("Qualification")
            with c2:
                sub_opts = subject_df["Subject"].tolist() if not subject_df.empty else []
                t_sub   = st.selectbox("Subject", sub_opts) if sub_opts else st.text_input("Subject")
                cls_opts= class_df["Class"].tolist() if not class_df.empty else []
                t_cls   = st.selectbox("Class Assigned", cls_opts) if cls_opts else st.text_input("Class")
                t_join  = st.date_input("Joining Date", datetime.today())

            if st.button("✅ Add Teacher", type="primary"):
                if not t_name.strip():
                    st.error("Name is required.")
                else:
                    t_id = "TCH-" + str(uuid.uuid4())[:6].upper()
                    row  = pd.DataFrame([[
                        t_id, t_name.strip(), t_sub, t_cls,
                        t_phone, t_email, t_qual, str(t_join),
                    ]], columns=teacher_df.columns)
                    new_t = pd.concat([teacher_df, row], ignore_index=True)
                    save_csv(new_t, TEACHER_FILE)
                    st.success(f"✅ Teacher **{t_name}** added! ID: `{t_id}`")
                    refresh()

    with tab2:
        if teacher_df.empty:
            st.info("No teachers yet.")
        else:
            t_opts = teacher_df.apply(lambda r: f"{r['Name']}  ({r['T_ID']})", axis=1).tolist()
            sel_t  = st.selectbox("Select Teacher", t_opts, key="upd_t")
            t_id_sel = sel_t.split("(")[-1].replace(")", "").strip()
            trow   = teacher_df[teacher_df["T_ID"] == t_id_sel].iloc[0]

            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    ut_name  = st.text_input("Name",          value=trow["Name"],          key="ut_n")
                    ut_phone = st.text_input("Phone",         value=str(trow["Phone"]),    key="ut_ph")
                    ut_email = st.text_input("Email",         value=str(trow["Email"]),    key="ut_em")
                    ut_qual  = st.text_input("Qualification", value=str(trow["Qualification"]), key="ut_q")
                with c2:
                    sub_opts = subject_df["Subject"].tolist() if not subject_df.empty else [trow["Subject"]]
                    ut_sub   = st.selectbox("Subject", sub_opts,
                                            index=sub_opts.index(trow["Subject"]) if trow["Subject"] in sub_opts else 0,
                                            key="ut_sub")
                    cls_opts = class_df["Class"].tolist() if not class_df.empty else [trow["Class"]]
                    ut_cls   = st.selectbox("Class", cls_opts,
                                            index=cls_opts.index(trow["Class"]) if trow["Class"] in cls_opts else 0,
                                            key="ut_cls")

                if st.button("💾 Update Teacher", type="primary"):
                    idx = teacher_df.index[teacher_df["T_ID"] == t_id_sel][0]
                    for col, val in [("Name",ut_name),("Phone",ut_phone),("Email",ut_email),
                                     ("Qualification",ut_qual),("Subject",ut_sub),("Class",ut_cls)]:
                        teacher_df.at[idx, col] = val
                    save_csv(teacher_df, TEACHER_FILE)
                    st.success("✅ Teacher updated!")
                    refresh()

    with tab3:
        if teacher_df.empty:
            st.info("No teacher records.")
        else:
            search_t = st.text_input("🔍 Search Teacher")
            disp_t   = teacher_df.copy()
            if search_t:
                q = search_t.lower()
                disp_t = disp_t[disp_t.apply(lambda r: q in str(r["Name"]).lower() or q in str(r["Subject"]).lower(), axis=1)]
            st.dataframe(disp_t, use_container_width=True, hide_index=True)

            st.markdown("---")
            t_opts = teacher_df.apply(lambda r: f"{r['Name']}  ({r['T_ID']})", axis=1).tolist()
            del_t  = st.selectbox("Delete Teacher", t_opts, key="del_t")
            if st.button("🗑️ Delete Teacher", type="primary"):
                del_tid = del_t.split("(")[-1].replace(")", "").strip()
                new_t   = teacher_df[teacher_df["T_ID"] != del_tid].reset_index(drop=True)
                save_csv(new_t, TEACHER_FILE)
                st.success("Deleted!")
                refresh()


# ─────────────────────────────────────────────
#  5. ATTENDANCE
# ─────────────────────────────────────────────
elif menu == "📅 Attendance":
    st.markdown("<div class='page-title'>📅 Attendance Management</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Mark Attendance", "📊 Records", "📈 Summary"])
    s_list = get_student_list(df)

    with tab1:
        if not s_list:
            st.warning("Add students first.")
        else:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2,1,1])
                with col1:
                    sel_s  = st.selectbox("Student", s_list, key="att_sel")
                with col2:
                    att_date = st.date_input("Date", datetime.today(), key="att_date")
                with col3:
                    status = st.radio("Status", ["Present", "Absent"], horizontal=True)
                if st.button("✅ Submit", type="primary"):
                    sid  = student_id_from_sel(sel_s)
                    row  = pd.DataFrame([[sid, str(att_date), status]], columns=att_df.columns)
                    new_att = pd.concat([att_df, row], ignore_index=True)
                    save_csv(new_att, ATT_FILE)
                    st.success("Attendance recorded!")
                    refresh()

    with tab2:
        if att_df.empty:
            st.info("No attendance records.")
        else:
            disp = pd.merge(att_df, df[["ID","Name","Class","Roll"]], on="ID", how="left")
            # filter
            fc1, fc2 = st.columns(2)
            cls_filter = fc1.selectbox("Filter by Class", ["All"] + df["Class"].unique().tolist())
            sts_filter = fc2.selectbox("Filter by Status", ["All", "Present", "Absent"])
            if cls_filter != "All":
                disp = disp[disp["Class"] == cls_filter]
            if sts_filter != "All":
                disp = disp[disp["Status"] == sts_filter]
            st.dataframe(disp[["Class","Roll","Name","Date","Status"]].sort_values(["Date","Class","Roll"]),
                         use_container_width=True, hide_index=True)

            st.markdown("---")
            del_opts = [(i, f"{disp.loc[i,'Name'] if i in disp.index else ''} | {r['Date']} | {r['Status']}")
                        for i, r in att_df.iterrows()]
            if del_opts:
                del_idx = st.selectbox("Delete Record", del_opts, format_func=lambda x: x[1])
                if st.button("🗑️ Delete"):
                    new_att = att_df.drop(del_idx[0]).reset_index(drop=True)
                    save_csv(new_att, ATT_FILE)
                    st.success("Deleted!")
                    refresh()

    with tab3:
        if att_df.empty or df.empty:
            st.info("Not enough data.")
        else:
            merged = pd.merge(att_df, df[["ID","Name","Class"]], on="ID", how="left")
            summary = merged.groupby(["Name","Status"]).size().unstack(fill_value=0).reset_index()
            for col in ["Present","Absent"]:
                if col not in summary.columns:
                    summary[col] = 0
            summary["Total"] = summary["Present"] + summary["Absent"]
            summary["Att%"]  = (summary["Present"] / summary["Total"] * 100).round(1)
            st.dataframe(summary, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
#  6. FEES MANAGEMENT
# ─────────────────────────────────────────────
elif menu == "💰 Fees Management":
    st.markdown("<div class='page-title'>💰 Fees Management</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Collect Fee", "✏️ Update Fee", "📋 Records"])
    s_list = get_student_list(df)

    with tab1:
        if not s_list:
            st.warning("No students.")
        else:
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    sel_s = st.selectbox("Student", s_list, key="fee_sel")
                with c2:
                    amt   = st.number_input("Amount (৳)", 0, 1_000_000, 0)
                with c3:
                    f_status = st.selectbox("Status", ["Paid","Due"])
                if st.button("💾 Save", type="primary"):
                    sid  = student_id_from_sel(sel_s)
                    row  = pd.DataFrame([[sid, amt, f_status, datetime.now().strftime("%Y-%m-%d")]], columns=fee_df.columns)
                    new_fee = pd.concat([fee_df, row], ignore_index=True)
                    save_csv(new_fee, FEE_FILE)
                    st.success("Fee recorded!")
                    refresh()

    with tab2:
        if fee_df.empty:
            st.info("No fee records.")
        else:
            disp_f = pd.merge(fee_df.reset_index(), df[["ID","Name"]], on="ID", how="left")
            opts   = [(r["index"], f"{r['Name']} | ৳{r['Amount']} | {r['Status']} | {r['Date']}")
                      for _, r in disp_f.iterrows()]
            sel_f  = st.selectbox("Select Fee Record", opts, format_func=lambda x: x[1])
            row_f  = fee_df.loc[sel_f[0]]
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    new_amt = st.number_input("Amount", value=int(row_f["Amount"]))
                with c2:
                    new_sts = st.selectbox("Status", ["Paid","Due"],
                                           index=0 if row_f["Status"]=="Paid" else 1)
                if st.button("💾 Update Fee", type="primary"):
                    fee_df.at[sel_f[0], "Amount"] = new_amt
                    fee_df.at[sel_f[0], "Status"] = new_sts
                    save_csv(fee_df, FEE_FILE)
                    st.success("Updated!")
                    refresh()

    with tab3:
        if fee_df.empty:
            st.info("No records.")
        else:
            disp = pd.merge(fee_df, df[["ID","Name","Class"]], on="ID", how="left")
            f_status = st.selectbox("Filter Status", ["All","Paid","Due"], key="fee_flt")
            if f_status != "All":
                disp = disp[disp["Status"] == f_status]
            st.dataframe(disp[["Class","Name","Amount","Status","Date"]], use_container_width=True, hide_index=True)
            st.markdown(f"**Total: ৳{disp['Amount'].sum():,.0f}**")

            st.markdown("---")
            del_f = pd.merge(fee_df.reset_index(), df[["ID","Name"]], on="ID", how="left")
            del_opts = [(r["index"], f"{r['Name']} | ৳{r['Amount']} ({r['Status']})") for _, r in del_f.iterrows()]
            if del_opts:
                d = st.selectbox("Delete", del_opts, format_func=lambda x: x[1])
                if st.button("🗑️ Delete Fee"):
                    new_fee = fee_df.drop(d[0]).reset_index(drop=True)
                    save_csv(new_fee, FEE_FILE)
                    st.success("Deleted!")
                    refresh()


# ─────────────────────────────────────────────
#  7. MARKS & GRADES
# ─────────────────────────────────────────────
elif menu == "📚 Marks & Grades":
    st.markdown("<div class='page-title'>📚 Marks & Grading</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Add Marks", "✏️ Update Marks", "📊 Report Card"])
    s_list = get_student_list(df)

    with tab1:
        if not s_list or subject_df.empty:
            st.warning("Add students and subjects first.")
        else:
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    sel_s = st.selectbox("Student", s_list, key="mrk_sel")
                with c2:
                    sel_sub = st.selectbox("Subject", subject_df["Subject"])
                with c3:
                    marks = st.number_input("Marks", 0, 100)
                if st.button("💾 Save Marks", type="primary"):
                    sid   = student_id_from_sel(sel_s)
                    grade = get_grade(marks)
                    row   = pd.DataFrame([[sid, sel_sub, marks, grade]], columns=mark_df.columns)
                    new_m = pd.concat([mark_df, row], ignore_index=True)
                    save_csv(new_m, MARK_FILE)
                    st.success(f"Saved! Grade: **{grade}**")
                    refresh()

    with tab2:
        if mark_df.empty:
            st.info("No marks yet.")
        else:
            disp_m = pd.merge(mark_df.reset_index(), df[["ID","Name"]], on="ID", how="left")
            opts   = [(r["index"], f"{r['Name']} | {r['Subject']} | {r['Marks']}")
                      for _, r in disp_m.iterrows()]
            sel_m  = st.selectbox("Select Record", opts, format_func=lambda x: x[1])
            row_m  = mark_df.loc[sel_m[0]]
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    sub_opts = subject_df["Subject"].tolist() if not subject_df.empty else [row_m["Subject"]]
                    new_sub  = st.selectbox("Subject", sub_opts,
                                            index=sub_opts.index(row_m["Subject"]) if row_m["Subject"] in sub_opts else 0)
                with c2:
                    new_mrk = st.number_input("Marks", 0, 100, int(row_m["Marks"]))
                if st.button("💾 Update Marks", type="primary"):
                    mark_df.at[sel_m[0], "Subject"] = new_sub
                    mark_df.at[sel_m[0], "Marks"]   = new_mrk
                    mark_df.at[sel_m[0], "Grade"]   = get_grade(new_mrk)
                    save_csv(mark_df, MARK_FILE)
                    st.success("Updated!")
                    refresh()

    with tab3:
        if mark_df.empty or df.empty:
            st.info("No data.")
        else:
            s_list2 = get_student_list(df)
            sel_rpt = st.selectbox("Select Student for Report", s_list2, key="rpt_sel")
            stu_id  = student_id_from_sel(sel_rpt)
            stu_row = df[df["ID"] == stu_id].iloc[0]
            stu_marks = mark_df[mark_df["ID"] == stu_id]

            if stu_marks.empty:
                st.info("No marks for this student.")
            else:
                st.markdown(f"### 📄 Report Card: {stu_row['Name']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Class", stu_row["Class"])
                c2.metric("Roll",  stu_row["Roll"])
                avg = stu_marks["Marks"].mean()
                c3.metric("Average Marks", f"{avg:.1f}")

                st.dataframe(stu_marks[["Subject","Marks","Grade"]], use_container_width=True, hide_index=True)

                fig = px.bar(stu_marks, x="Subject", y="Marks", color="Grade", text="Grade",
                             color_discrete_sequence=px.colors.qualitative.Bold)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
                st.plotly_chart(fig, use_container_width=True)

                # PDF report card download
                if st.button("📄 Download Report Card PDF", type="primary"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_fill_color(15, 23, 42)
                    pdf.rect(0, 0, 210, 40, style="F")
                    pdf.set_font("Arial","B",20)
                    pdf.set_text_color(255,255,255)
                    pdf.set_xy(0,10)
                    pdf.cell(210,10,"EduPro ERP — Report Card",align="C")
                    pdf.set_font("Arial","",11)
                    pdf.set_xy(0,22)
                    pdf.cell(210,8,f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",align="C")

                    pdf.set_text_color(0,0,0)
                    pdf.set_font("Arial","B",13)
                    pdf.set_xy(20,50)
                    pdf.cell(0,8,f"Student: {stu_row['Name']}  |  Class: {stu_row['Class']}  |  Roll: {stu_row['Roll']}")

                    pdf.set_font("Arial","B",11)
                    pdf.set_xy(20,65)
                    pdf.set_fill_color(30,41,59)
                    pdf.set_text_color(255,255,255)
                    for h,w in [("Subject",80),("Marks",30),("Grade",30)]:
                        pdf.cell(w,8,h,border=1,fill=True,align="C")
                    pdf.ln()

                    pdf.set_font("Arial","",11)
                    pdf.set_text_color(0,0,0)
                    for _, mr in stu_marks.iterrows():
                        pdf.set_x(20)
                        pdf.cell(80,8,str(mr["Subject"]),border=1)
                        pdf.cell(30,8,str(mr["Marks"]),border=1,align="C")
                        pdf.cell(30,8,str(mr["Grade"]),border=1,align="C")
                        pdf.ln()

                    pdf.set_x(20)
                    pdf.set_font("Arial","B",11)
                    pdf.cell(80,8,"Average",border=1)
                    pdf.cell(30,8,f"{avg:.1f}",border=1,align="C")
                    pdf.cell(30,8,get_grade(avg),border=1,align="C")

                    pdf_bytes = pdf.output(dest="S").encode("latin1")
                    st.download_button("⬇️ Download PDF",data=pdf_bytes,
                                       file_name=f"{stu_row['Name']}_ReportCard.pdf",
                                       mime="application/pdf")


# ─────────────────────────────────────────────
#  8. ID CARD
# ─────────────────────────────────────────────
elif menu == "🪪 ID Card":
    st.markdown("<div class='page-title'>🪪 ID Card Generator</div>", unsafe_allow_html=True)
    s_list = get_student_list(df)

    if not s_list:
        st.warning("Admit students first.")
    else:
        sel = st.selectbox("Select Student", s_list)
        stu_id = student_id_from_sel(sel)
        s = df[df["ID"] == stu_id].iloc[0]

        with st.container(border=True):
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#1e293b,#0f172a);
                        border:2px solid #38bdf8; border-radius:14px;
                        padding:24px 32px; max-width:420px; font-family:sans-serif;'>
              <div style='font-size:20px;font-weight:800;color:#38bdf8;text-align:center;
                          border-bottom:1px solid #334155;padding-bottom:10px;margin-bottom:14px;'>
                🎓 EduPro ERP — Student ID
              </div>
              <table style='color:#e2e8f0;font-size:14px;width:100%;'>
                <tr><td style='padding:4px 0;color:#94a3b8;'>Name</td>
                    <td style='font-weight:700;'>{s['Name']}</td></tr>
                <tr><td style='color:#94a3b8;'>Class</td><td>{s['Class']}</td></tr>
                <tr><td style='color:#94a3b8;'>Roll</td><td>{s['Roll']}</td></tr>
                <tr><td style='color:#94a3b8;'>Gender</td><td>{s['Gender']}</td></tr>
                <tr><td style='color:#94a3b8;'>ID No</td><td style='font-family:monospace;color:#38bdf8;'>{s['ID']}</td></tr>
                <tr><td style='color:#94a3b8;'>Phone</td><td>{s['Phone']}</td></tr>
                <tr><td style='color:#94a3b8;'>Father</td><td>{s['Father_Name']}</td></tr>
                <tr><td style='color:#94a3b8;'>Mother</td><td>{s['Mother_Name']}</td></tr>
                <tr><td style='color:#94a3b8;'>Issued</td><td>{s['Date']}</td></tr>
              </table>
            </div>
            """, unsafe_allow_html=True)

        if st.button("📄 Generate PDF ID Card", type="primary"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_fill_color(15,23,42)
            pdf.rect(45,30,120,110,style="F")
            pdf.set_draw_color(56,189,248)
            pdf.set_line_width(1.2)
            pdf.rect(45,30,120,110)

            pdf.set_fill_color(30,41,59)
            pdf.rect(45,30,120,22,style="F")
            pdf.set_font("Arial","B",16)
            pdf.set_text_color(255,255,255)
            pdf.set_xy(45,35)
            pdf.cell(120,12,"EduPro ERP — Student ID Card",align="C")

            pdf.set_text_color(0,0,0)
            fields = [
                ("Name",     s["Name"]),
                ("Class",    s["Class"]),
                ("Roll No",  s["Roll"]),
                ("Gender",   s["Gender"]),
                ("ID No",    s["ID"]),
                ("Phone",    s["Phone"]),
                ("Father",   s["Father_Name"]),
                ("Mother",   s["Mother_Name"]),
                ("Issued",   s["Date"]),
            ]
            y = 58
            for label, value in fields:
                pdf.set_font("Arial","B",10)
                pdf.set_xy(52, y)
                pdf.cell(30,7,f"{label}:")
                pdf.set_font("Arial","",10)
                pdf.cell(80,7,str(value))
                y += 8

            pdf_bytes = pdf.output(dest="S").encode("latin1")
            st.success("ID Card ready!")
            st.download_button("⬇️ Download PDF",data=pdf_bytes,
                               file_name=f"{s['Name']}_ID.pdf",mime="application/pdf")


# ─────────────────────────────────────────────
#  9. USER MANAGEMENT
# ─────────────────────────────────────────────
elif menu == "🔑 User Management":
    st.markdown("<div class='page-title'>🔑 User Management</div>", unsafe_allow_html=True)

    if st.session_state.get("role") != "Admin":
        st.error("🚫 Admin access only.")
        st.stop()

    tab1, tab2 = st.tabs(["➕ Add User", "📋 Users"])

    with tab1:
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_u = st.text_input("Username")
            with c2:
                new_p = st.text_input("Password", type="password")
            with c3:
                new_r = st.selectbox("Role", ["Admin","Teacher","Staff"])
            if st.button("➕ Add User", type="primary"):
                if not new_u.strip() or not new_p.strip():
                    st.error("Username and Password required.")
                elif new_u in users_df["Username"].values:
                    st.error("Username already exists.")
                else:
                    row = pd.DataFrame([[new_u.strip(), hash_pw(new_p), new_r]], columns=users_df.columns)
                    new_users = pd.concat([users_df, row], ignore_index=True)
                    save_csv(new_users, USERS_FILE)
                    st.success(f"User **{new_u}** created!")
                    refresh()

    with tab2:
        if users_df.empty:
            st.info("No users.")
        else:
            disp_u = users_df[["Username","Role"]].copy()
            st.dataframe(disp_u, use_container_width=True, hide_index=True)

            st.markdown("---")
            del_u = st.selectbox("Delete User", users_df["Username"].tolist())
            if st.button("🗑️ Delete User"):
                if del_u == st.session_state.get("username"):
                    st.error("Cannot delete your own account.")
                else:
                    new_users = users_df[users_df["Username"] != del_u].reset_index(drop=True)
                    save_csv(new_users, USERS_FILE)
                    st.success(f"User **{del_u}** deleted.")
                    refresh()

            st.markdown("---")
            st.markdown("##### 🔒 Change Password")
            cp_u = st.selectbox("User", users_df["Username"].tolist(), key="cp_u")
            cp_p = st.text_input("New Password", type="password", key="cp_p")
            if st.button("Update Password", type="primary"):
                if not cp_p.strip():
                    st.error("Enter a new password.")
                else:
                    idx = users_df.index[users_df["Username"] == cp_u][0]
                    users_df.at[idx, "Password"] = hash_pw(cp_p)
                    save_csv(users_df, USERS_FILE)
                    st.success("Password updated!")
                    refresh()