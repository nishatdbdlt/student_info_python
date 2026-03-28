import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import uuid
import plotly.express as px
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
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0f172a 0%,#1e293b 100%); }
[data-testid="stSidebar"] * { color:#cbd5e1 !important; }
[data-testid="stSidebar"] .stRadio label { font-size:14px; padding:4px 0; }
.kpi { background:linear-gradient(135deg,#1e293b,#0f172a); border-radius:14px;
       padding:22px 18px; text-align:center; border:1px solid #334155;
       transition:.3s; box-shadow:0 4px 14px rgba(0,0,0,.4); }
.kpi:hover { transform:translateY(-4px); border-color:#38bdf8; }
.kpi-icon  { font-size:28px; }
.kpi-label { font-size:13px; color:#94a3b8; margin-top:6px; }
.kpi-value { font-size:34px; font-weight:800; color:#38bdf8; margin-top:4px; }
.page-title { font-size:26px; font-weight:700; color:#f1f5f9;
              border-left:4px solid #38bdf8; padding-left:12px; margin-bottom:20px; }
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg,#0ea5e9,#6366f1);
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
    """Always reads fresh from disk — no cache."""
    if os.path.exists(file):
        try:
            tmp = pd.read_csv(file, dtype=str)
            for c in cols:
                if c not in tmp.columns:
                    tmp[c] = ""
            result = tmp[cols].copy()
            for c in ["Age", "Roll", "Marks", "Amount"]:
                if c in result.columns:
                    result[c] = pd.to_numeric(result[c], errors="coerce").fillna(0)
            return result
        except Exception:
            pass
    return pd.DataFrame(columns=cols)


def save_csv(dataframe: pd.DataFrame, file: str):
    dataframe.to_csv(file, index=False)


def get_grade(marks: float) -> str:
    m = float(marks)
    if m >= 80: return "A+"
    if m >= 70: return "A"
    if m >= 60: return "A-"
    if m >= 50: return "B"
    if m >= 40: return "C"
    if m >= 33: return "D"
    return "F"


STU_COLS = [
    "ID","Name","Age","Class","Roll","Gender",
    "Phone","Email","Address",
    "Father_Name","Father_Phone","Father_Occupation",
    "Mother_Name","Mother_Phone","Mother_Occupation",
    "Date",
]
TCH_COLS = ["T_ID","Name","Subject","Class","Phone","Email","Qualification","Join_Date"]
USR_COLS = ["Username","Password","Role"]


def load_all():
    students = load_csv(FILE,         STU_COLS)
    classes  = load_csv(CLASS_FILE,   ["Class"])
    subjects = load_csv(SUBJECT_FILE, ["Subject"])
    att      = load_csv(ATT_FILE,     ["ID","Date","Status"])
    fees     = load_csv(FEE_FILE,     ["ID","Amount","Status","Date"])
    marks    = load_csv(MARK_FILE,    ["ID","Subject","Marks","Grade"])
    teachers = load_csv(TEACHER_FILE, TCH_COLS)
    users    = load_csv(USERS_FILE,   USR_COLS)
    if users.empty:
        users = pd.DataFrame([["admin", hash_pw("admin"), "Admin"]], columns=USR_COLS)
        save_csv(users, USERS_FILE)
    return students, classes, subjects, att, fees, marks, teachers, users


def get_student_list(dataframe: pd.DataFrame) -> list:
    if dataframe.empty:
        return []
    s = dataframe.sort_values(["Class","Roll"])
    return s.apply(
        lambda r: f"Class {r['Class']} | Roll {int(float(r['Roll']))} | {r['Name']}  ({r['ID']})",
        axis=1
    ).tolist()


def sid_from(sel: str) -> str:
    return sel.split("(")[-1].replace(")", "").strip()


def refresh():
    st.rerun()


# ─────────────────────────────────────────────
#  LOAD DATA  (fresh every render — no cache)
# ─────────────────────────────────────────────
df, class_df, subject_df, att_df, fee_df, mark_df, teacher_df, users_df = load_all()


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center;margin-bottom:24px;'>
          <div style='font-size:60px;'>🎓</div>
          <h1 style='color:#f1f5f9;margin:0;'>EduPro ERP</h1>
          <p style='color:#94a3b8;'>School Management System</p>
        </div>""", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### 🔐 Sign In")
            u = st.text_input("Username", placeholder="Enter username",   key="lg_u")
            p = st.text_input("Password", type="password",
                               placeholder="Enter password", key="lg_p")
            if st.button("Login", type="primary", use_container_width=True):
                _, _, _, _, _, _, _, u_df = load_all()
                match = u_df[(u_df["Username"] == u) & (u_df["Password"] == hash_pw(p))]
                if not match.empty:
                    st.session_state.update({"login": True, "username": u,
                                             "role": match.iloc[0]["Role"]})
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials!")


if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_page()
    st.stop()


def logout():
    for k in ["login","username","role"]:
        st.session_state.pop(k, None)
    st.rerun()


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
st.sidebar.markdown("""
<div style='text-align:center;padding:16px 0 8px;'>
  <div style='font-size:48px;'>🎓</div>
  <div style='font-size:18px;font-weight:700;color:#f1f5f9;'>EduPro ERP</div>
  <div style='font-size:12px;color:#64748b;margin-top:4px;'>School Management System</div>
</div>
<hr style='border-color:#334155;margin:8px 0 16px;'>
""", unsafe_allow_html=True)
st.sidebar.markdown(
    f"👤 **{st.session_state.get('username','Admin')}** "
    f"<span style='font-size:11px;color:#64748b;'>({st.session_state.get('role','Admin')})</span>",
    unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border-color:#334155;'>", unsafe_allow_html=True)

menu = st.sidebar.radio("Navigation", [
    "📊 Dashboard", "🏫 Class & Subject", "🎓 Manage Students",
    "👨‍🏫 Teachers", "📅 Attendance", "💰 Fees Management",
    "📚 Marks & Grades", "🪪 ID Card", "🔑 User Management",
])
st.sidebar.markdown("<hr style='border-color:#334155;'>", unsafe_allow_html=True)
st.sidebar.button("🚪 Logout", on_click=logout, type="primary", use_container_width=True)


# ════════════════════════════════════════════════
#  1. DASHBOARD
# ════════════════════════════════════════════════
if menu == "📊 Dashboard":
    st.markdown("<div class='page-title'>📊 Smart Analytics Dashboard</div>", unsafe_allow_html=True)

    total_students  = len(df)
    total_classes   = df["Class"].nunique() if total_students else 0
    total_subjects  = len(subject_df)
    total_teachers  = len(teacher_df)
    present_count   = len(att_df[att_df["Status"] == "Present"]) if not att_df.empty else 0
    att_rate        = round((present_count / len(att_df)) * 100, 1) if len(att_df) > 0 else 0
    total_collected = fee_df[fee_df["Status"] == "Paid"]["Amount"].sum() if not fee_df.empty else 0

    cols = st.columns(6)
    kpi_data = [
        ("👨‍🎓","Students",      total_students),
        ("🏫", "Classes",        total_classes),
        ("📚", "Subjects",       total_subjects),
        ("👨‍🏫","Teachers",       total_teachers),
        ("📅", "Attendance %",   f"{att_rate}%"),
        ("💰", "Fees Collected", f"৳{int(total_collected):,}"),
    ]
    for col, (icon, label, val) in zip(cols, kpi_data):
        col.markdown(f"""
        <div class='kpi'><div class='kpi-icon'>{icon}</div>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value'>{val}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    r1 = st.columns(2)
    with r1[0]:
        st.markdown("#### 🏫 Class-wise Students")
        if total_students > 0:
            fig = px.pie(df, names="Class", hole=0.45,
                         color_discrete_sequence=px.colors.sequential.Teal)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No student data yet.")
    with r1[1]:
        st.markdown("#### 💰 Fee Collection Overview")
        if not fee_df.empty:
            s = fee_df.groupby("Status")["Amount"].sum().reset_index()
            fig = px.bar(s, x="Status", y="Amount", color="Status",
                         color_discrete_map={"Paid":"#22c55e","Due":"#ef4444"}, text_auto=True)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No fee data yet.")

    r2 = st.columns(2)
    with r2[0]:
        st.markdown("#### 📅 Attendance Summary")
        if not att_df.empty:
            a = att_df.groupby("Status").size().reset_index(name="Count")
            fig2 = px.pie(a, names="Status", values="Count", hole=0.4,
                          color="Status",
                          color_discrete_map={"Present":"#22c55e","Absent":"#ef4444"})
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No attendance data yet.")
    with r2[1]:
        st.markdown("#### 📚 Avg Marks per Subject")
        if not mark_df.empty:
            avg = mark_df.groupby("Subject")["Marks"].mean().reset_index()
            avg.columns = ["Subject","Avg Marks"]
            fig3 = px.bar(avg, x="Subject", y="Avg Marks", color="Avg Marks",
                          color_continuous_scale="Blues", text_auto=".1f")
            fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No marks data yet.")


# ════════════════════════════════════════════════
#  2. CLASS & SUBJECT
# ════════════════════════════════════════════════
elif menu == "🏫 Class & Subject":
    st.markdown("<div class='page-title'>🏫 Classes & Subjects Setup</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown("##### ➕ Add Class")
            nc = st.text_input("Class Name", key="nc")
            if st.button("Save Class", type="primary", use_container_width=True, key="save_class_btn"):
                if nc.strip():
                    fresh = load_csv(CLASS_FILE, ["Class"])
                    save_csv(pd.concat([fresh, pd.DataFrame([[nc.strip()]], columns=["Class"])],
                                       ignore_index=True), CLASS_FILE)
                    st.success("✅ Class added!")
                    refresh()
                else:
                    st.warning("Enter a class name.")
            st.markdown("##### 📋 Existing Classes")
            fresh_cls = load_csv(CLASS_FILE, ["Class"])
            st.dataframe(fresh_cls, use_container_width=True, hide_index=True)
            if not fresh_cls.empty:
                del_cls = st.selectbox("Select to Delete", fresh_cls["Class"].tolist(), key="del_cls")
                if st.button("🗑️ Delete Class", type="primary", key="btn_del_cls"):
                    save_csv(fresh_cls[fresh_cls["Class"] != del_cls].reset_index(drop=True), CLASS_FILE)
                    st.success(f"✅ '{del_cls}' deleted!")
                    refresh()

    with c2:
        with st.container(border=True):
            st.markdown("##### ➕ Add Subject")
            ns = st.text_input("Subject Name", key="ns")
            if st.button("Save Subject", type="primary", use_container_width=True, key="save_sub_btn"):
                if ns.strip():
                    fresh = load_csv(SUBJECT_FILE, ["Subject"])
                    save_csv(pd.concat([fresh, pd.DataFrame([[ns.strip()]], columns=["Subject"])],
                                       ignore_index=True), SUBJECT_FILE)
                    st.success("✅ Subject added!")
                    refresh()
                else:
                    st.warning("Enter a subject name.")
            st.markdown("##### 📋 Existing Subjects")
            fresh_sub = load_csv(SUBJECT_FILE, ["Subject"])
            st.dataframe(fresh_sub, use_container_width=True, hide_index=True)
            if not fresh_sub.empty:
                del_sub = st.selectbox("Select to Delete", fresh_sub["Subject"].tolist(), key="del_sub")
                if st.button("🗑️ Delete Subject", type="primary", key="btn_del_sub"):
                    save_csv(fresh_sub[fresh_sub["Subject"] != del_sub].reset_index(drop=True), SUBJECT_FILE)
                    st.success(f"✅ '{del_sub}' deleted!")
                    refresh()


# ════════════════════════════════════════════════
#  3. MANAGE STUDENTS
# ════════════════════════════════════════════════
elif menu == "🎓 Manage Students":
    st.markdown("<div class='page-title'>🎓 Student Management</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Admit Student", "✏️ Update Student", "📋 View / Delete"])

    with tab1:
        with st.container(border=True):
            st.markdown("##### 👤 Personal Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                name   = st.text_input("Full Name *",    key="add_name")
                gender = st.selectbox("Gender", ["Male","Female","Other"], key="add_gender")
                age    = st.number_input("Age", 4, 100, 10, key="add_age")
            with col2:
                cls_opts = load_csv(CLASS_FILE, ["Class"])["Class"].tolist() or ["N/A"]
                s_class  = st.selectbox("Class *", cls_opts, key="add_class")
                roll     = st.number_input("Roll Number *", 1, 9999, 1, key="add_roll")
                phone    = st.text_input("Phone", key="add_phone")
            with col3:
                email   = st.text_input("Email",   key="add_email")
                address = st.text_area("Address", height=96, key="add_addr")

            st.markdown("##### 👨‍👩‍👧 Parent / Guardian Information")
            p1, p2 = st.columns(2)
            with p1:
                st.markdown("###### Father")
                f_name  = st.text_input("Father's Name",       key="add_fn")
                f_phone = st.text_input("Father's Phone",      key="add_fp")
                f_occ   = st.text_input("Father's Occupation", key="add_fo")
            with p2:
                st.markdown("###### Mother")
                m_name  = st.text_input("Mother's Name",       key="add_mn")
                m_phone = st.text_input("Mother's Phone",      key="add_mp")
                m_occ   = st.text_input("Mother's Occupation", key="add_mo")

            if st.button("✅ Admit Student", type="primary", key="admit_btn"):
                if not name.strip():
                    st.error("Full Name is required.")
                else:
                    new_id = "STU-" + str(uuid.uuid4())[:6].upper()
                    fresh  = load_csv(FILE, STU_COLS)
                    row = pd.DataFrame([[
                        new_id, name.strip(), age, s_class, roll, gender,
                        phone, email, address,
                        f_name, f_phone, f_occ,
                        m_name, m_phone, m_occ,
                        datetime.now().strftime("%Y-%m-%d"),
                    ]], columns=STU_COLS)
                    save_csv(pd.concat([fresh, row], ignore_index=True), FILE)
                    st.success(f"🎉 **{name}** admitted!  ID: `{new_id}`")
                    st.balloons()
                    refresh()

    with tab2:
        fresh_df2 = load_csv(FILE, STU_COLS)
        if fresh_df2.empty:
            st.info("No students to update.")
        else:
            s_list = get_student_list(fresh_df2)
            sel    = st.selectbox("Select Student", s_list, key="upd_stu_sel")
            stu_id = sid_from(sel)
            row    = fresh_df2[fresh_df2["ID"] == stu_id].iloc[0]

            with st.container(border=True):
                st.markdown("##### ✏️ Edit Details")
                col1, col2, col3 = st.columns(3)
                with col1:
                    u_name   = st.text_input("Full Name",  value=str(row["Name"]),  key="u_name")
                    u_gender = st.selectbox("Gender", ["Male","Female","Other"],
                                            index=["Male","Female","Other"].index(row["Gender"])
                                            if row["Gender"] in ["Male","Female","Other"] else 0,
                                            key="upd_gender")
                    u_age    = st.number_input("Age", 4, 100, int(float(row["Age"])), key="u_age")
                with col2:
                    cls_opts = load_csv(CLASS_FILE, ["Class"])["Class"].tolist() or [row["Class"]]
                    u_class  = st.selectbox("Class", cls_opts,
                                            index=cls_opts.index(row["Class"]) if row["Class"] in cls_opts else 0,
                                            key="upd_class")
                    u_roll   = st.number_input("Roll", 1, 9999, int(float(row["Roll"])), key="u_roll")
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

                if st.button("💾 Save Changes", type="primary", key="upd_stu_btn"):
                    idx = fresh_df2.index[fresh_df2["ID"] == stu_id][0]
                    for col_, val_ in [
                        ("Name",u_name),("Gender",u_gender),("Age",u_age),
                        ("Class",u_class),("Roll",u_roll),("Phone",u_phone),
                        ("Email",u_email),("Address",u_addr),
                        ("Father_Name",u_fn),("Father_Phone",u_fp),("Father_Occupation",u_fo),
                        ("Mother_Name",u_mn),("Mother_Phone",u_mp),("Mother_Occupation",u_mo),
                    ]:
                        fresh_df2.at[idx, col_] = val_
                    save_csv(fresh_df2, FILE)
                    st.success("✅ Student updated!")
                    refresh()

    with tab3:
        fresh_df3 = load_csv(FILE, STU_COLS)
        if fresh_df3.empty:
            st.info("No students admitted yet.")
        else:
            search = st.text_input("🔍 Search by Name / ID / Class", key="stu_search")
            disp   = fresh_df3.sort_values(["Class","Roll"])
            if search:
                q = search.lower()
                disp = disp[disp.apply(
                    lambda r: q in str(r["Name"]).lower()
                           or q in str(r["ID"]).lower()
                           or q in str(r["Class"]).lower(), axis=1)]
            st.markdown(f"**{len(disp)} student(s) found**")
            st.dataframe(
                disp[["ID","Name","Age","Gender","Class","Roll","Phone","Father_Name","Mother_Name","Date"]],
                use_container_width=True, hide_index=True)
            st.markdown("---")
            st.markdown("##### 🗑️ Delete Student")
            s_list2 = get_student_list(fresh_df3)
            to_del  = st.selectbox("Select", s_list2, key="del_stu_sel")
            if st.button("Delete Student", type="primary", key="del_stu_btn"):
                del_id = sid_from(to_del)
                save_csv(fresh_df3[fresh_df3["ID"] != del_id].reset_index(drop=True), FILE)
                st.success("✅ Student deleted.")
                refresh()


# ════════════════════════════════════════════════
#  4. TEACHERS
# ════════════════════════════════════════════════
elif menu == "👨‍🏫 Teachers":
    st.markdown("<div class='page-title'>👨‍🏫 Teacher Management</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Add Teacher", "✏️ Update Teacher", "📋 View / Delete"])

    with tab1:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                t_name  = st.text_input("Full Name *",   key="t_name")
                t_phone = st.text_input("Phone",         key="t_phone")
                t_email = st.text_input("Email",         key="t_email")
                t_qual  = st.text_input("Qualification", key="t_qual")
            with c2:
                sub_list = load_csv(SUBJECT_FILE, ["Subject"])["Subject"].tolist()
                cls_list = load_csv(CLASS_FILE, ["Class"])["Class"].tolist()
                t_sub  = st.selectbox("Subject", sub_list, key="add_t_sub") if sub_list else st.text_input("Subject", key="add_t_sub_txt")
                t_cls  = st.selectbox("Class Assigned", cls_list, key="add_t_cls") if cls_list else st.text_input("Class", key="add_t_cls_txt")
                t_join = st.date_input("Joining Date", datetime.today(), key="t_join")

            if st.button("✅ Add Teacher", type="primary", key="add_teacher_btn"):
                if not t_name.strip():
                    st.error("Name is required.")
                else:
                    t_id   = "TCH-" + str(uuid.uuid4())[:6].upper()
                    fresh  = load_csv(TEACHER_FILE, TCH_COLS)
                    row    = pd.DataFrame([[t_id, t_name.strip(), t_sub, t_cls,
                                            t_phone, t_email, t_qual, str(t_join)]], columns=TCH_COLS)
                    save_csv(pd.concat([fresh, row], ignore_index=True), TEACHER_FILE)
                    st.success(f"✅ **{t_name}** added!  ID: `{t_id}`")
                    refresh()

    with tab2:
        fresh_t2 = load_csv(TEACHER_FILE, TCH_COLS)
        if fresh_t2.empty:
            st.info("No teachers yet.")
        else:
            t_opts = fresh_t2.apply(lambda r: f"{r['Name']}  ({r['T_ID']})", axis=1).tolist()
            sel_t  = st.selectbox("Select Teacher", t_opts, key="upd_t_sel")
            t_id_s = sel_t.split("(")[-1].replace(")", "").strip()
            trow   = fresh_t2[fresh_t2["T_ID"] == t_id_s].iloc[0]

            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    ut_name  = st.text_input("Name",          value=str(trow["Name"]),          key="ut_n")
                    ut_phone = st.text_input("Phone",         value=str(trow["Phone"]),         key="ut_ph")
                    ut_email = st.text_input("Email",         value=str(trow["Email"]),         key="ut_em")
                    ut_qual  = st.text_input("Qualification", value=str(trow["Qualification"]), key="ut_q")
                with c2:
                    sub_list = load_csv(SUBJECT_FILE, ["Subject"])["Subject"].tolist() or [trow["Subject"]]
                    cls_list = load_csv(CLASS_FILE, ["Class"])["Class"].tolist() or [trow["Class"]]
                    ut_sub = st.selectbox("Subject", sub_list,
                                          index=sub_list.index(trow["Subject"]) if trow["Subject"] in sub_list else 0,
                                          key="upd_t_sub")
                    ut_cls = st.selectbox("Class", cls_list,
                                          index=cls_list.index(trow["Class"]) if trow["Class"] in cls_list else 0,
                                          key="upd_t_cls")

                if st.button("💾 Update Teacher", type="primary", key="upd_t_btn"):
                    idx = fresh_t2.index[fresh_t2["T_ID"] == t_id_s][0]
                    for col_, val_ in [("Name",ut_name),("Phone",ut_phone),("Email",ut_email),
                                        ("Qualification",ut_qual),("Subject",ut_sub),("Class",ut_cls)]:
                        fresh_t2.at[idx, col_] = val_
                    save_csv(fresh_t2, TEACHER_FILE)
                    st.success("✅ Teacher updated!")
                    refresh()

    with tab3:
        fresh_t3 = load_csv(TEACHER_FILE, TCH_COLS)
        if fresh_t3.empty:
            st.info("No teacher records.")
        else:
            search_t = st.text_input("🔍 Search Teacher", key="t_search")
            disp_t   = fresh_t3.copy()
            if search_t:
                q = search_t.lower()
                disp_t = disp_t[disp_t.apply(
                    lambda r: q in str(r["Name"]).lower() or q in str(r["Subject"]).lower(), axis=1)]
            st.dataframe(disp_t, use_container_width=True, hide_index=True)
            st.markdown("---")
            t_opts2 = fresh_t3.apply(lambda r: f"{r['Name']}  ({r['T_ID']})", axis=1).tolist()
            del_t   = st.selectbox("Delete Teacher", t_opts2, key="del_t_sel")
            if st.button("🗑️ Delete Teacher", type="primary", key="del_t_btn"):
                del_tid = del_t.split("(")[-1].replace(")", "").strip()
                save_csv(fresh_t3[fresh_t3["T_ID"] != del_tid].reset_index(drop=True), TEACHER_FILE)
                st.success("✅ Deleted!")
                refresh()


# ════════════════════════════════════════════════
#  5. ATTENDANCE
# ════════════════════════════════════════════════
elif menu == "📅 Attendance":
    st.markdown("<div class='page-title'>📅 Attendance Management</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Mark Attendance", "📊 Records", "📈 Summary"])

    fresh_df_a = load_csv(FILE, STU_COLS)
    s_list_a   = get_student_list(fresh_df_a)

    with tab1:
        if not s_list_a:
            st.warning("Add students first.")
        else:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2,1,1])
                with col1:
                    sel_s = st.selectbox("Student", s_list_a, key="att_sel")
                with col2:
                    att_date = st.date_input("Date", datetime.today(), key="att_date")
                with col3:
                    status = st.radio("Status", ["Present","Absent"], horizontal=True, key="att_status")
                if st.button("✅ Submit Attendance", type="primary", key="att_btn"):
                    sid      = sid_from(sel_s)
                    fresh_a  = load_csv(ATT_FILE, ["ID","Date","Status"])
                    row      = pd.DataFrame([[sid, str(att_date), status]], columns=["ID","Date","Status"])
                    save_csv(pd.concat([fresh_a, row], ignore_index=True), ATT_FILE)
                    st.success("✅ Attendance recorded!")
                    refresh()

    with tab2:
        fresh_a2 = load_csv(ATT_FILE, ["ID","Date","Status"])
        if fresh_a2.empty:
            st.info("No attendance records.")
        else:
            disp = pd.merge(fresh_a2, fresh_df_a[["ID","Name","Class","Roll"]], on="ID", how="left")
            fc1, fc2 = st.columns(2)
            cls_f = fc1.selectbox("Filter Class",  ["All"] + fresh_df_a["Class"].unique().tolist(), key="att_cls_f")
            sts_f = fc2.selectbox("Filter Status", ["All","Present","Absent"], key="att_sts_f")
            if cls_f != "All": disp = disp[disp["Class"] == cls_f]
            if sts_f != "All": disp = disp[disp["Status"] == sts_f]
            st.dataframe(
                disp[["Class","Roll","Name","Date","Status"]].sort_values(["Date","Class","Roll"]),
                use_container_width=True, hide_index=True)
            st.markdown("---")
            merged_del = pd.merge(fresh_a2.reset_index(), fresh_df_a[["ID","Name"]], on="ID", how="left")
            del_opts = [(int(r["index"]), f"{r['Name']} | {r['Date']} | {r['Status']}")
                        for _, r in merged_del.iterrows()]
            if del_opts:
                d = st.selectbox("Select Record to Delete", del_opts,
                                 format_func=lambda x: x[1], key="del_att_sel")
                if st.button("🗑️ Delete Record", key="del_att_btn"):
                    save_csv(fresh_a2.drop(d[0]).reset_index(drop=True), ATT_FILE)
                    st.success("✅ Deleted!")
                    refresh()

    with tab3:
        fresh_a3 = load_csv(ATT_FILE, ["ID","Date","Status"])
        if fresh_a3.empty or fresh_df_a.empty:
            st.info("Not enough data.")
        else:
            merged = pd.merge(fresh_a3, fresh_df_a[["ID","Name","Class"]], on="ID", how="left")
            summary = merged.groupby(["Name","Status"]).size().unstack(fill_value=0).reset_index()
            for col_ in ["Present","Absent"]:
                if col_ not in summary.columns: summary[col_] = 0
            summary["Total"] = summary["Present"] + summary["Absent"]
            summary["Att%"]  = (summary["Present"] / summary["Total"] * 100).round(1)
            st.dataframe(summary, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════
#  6. FEES MANAGEMENT
# ════════════════════════════════════════════════
elif menu == "💰 Fees Management":
    st.markdown("<div class='page-title'>💰 Fees Management</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Collect Fee", "✏️ Update Fee", "📋 Records"])

    fresh_df_f = load_csv(FILE, STU_COLS)
    s_list_f   = get_student_list(fresh_df_f)

    with tab1:
        if not s_list_f:
            st.warning("No students.")
        else:
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    sel_s    = st.selectbox("Student", s_list_f, key="fee_sel")
                with c2:
                    amt      = st.number_input("Amount (৳)", 0, 1_000_000, 0, key="fee_amt")
                with c3:
                    f_status = st.selectbox("Status", ["Paid","Due"], key="add_fee_status")
                if st.button("💾 Save Fee", type="primary", key="save_fee_btn"):
                    sid     = sid_from(sel_s)
                    fresh_f = load_csv(FEE_FILE, ["ID","Amount","Status","Date"])
                    row     = pd.DataFrame([[sid, amt, f_status, datetime.now().strftime("%Y-%m-%d")]],
                                           columns=["ID","Amount","Status","Date"])
                    save_csv(pd.concat([fresh_f, row], ignore_index=True), FEE_FILE)
                    st.success("✅ Fee recorded!")
                    refresh()

    with tab2:
        fresh_f2 = load_csv(FEE_FILE, ["ID","Amount","Status","Date"])
        if fresh_f2.empty:
            st.info("No fee records.")
        else:
            merged_f = pd.merge(fresh_f2.reset_index(), fresh_df_f[["ID","Name"]], on="ID", how="left")
            opts = [(int(r["index"]), f"{r['Name']} | ৳{r['Amount']} | {r['Status']} | {r['Date']}")
                    for _, r in merged_f.iterrows()]
            sel_f = st.selectbox("Select Fee Record", opts,
                                 format_func=lambda x: x[1], key="upd_fee_sel")
            row_f = fresh_f2.loc[sel_f[0]]
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    new_amt = st.number_input("Amount", value=int(float(row_f["Amount"])), key="upd_fee_amt")
                with c2:
                    new_sts = st.selectbox("Status", ["Paid","Due"],
                                           index=0 if row_f["Status"] == "Paid" else 1,
                                           key="upd_fee_status")
                if st.button("💾 Update Fee", type="primary", key="upd_fee_btn"):
                    fresh_f2.at[sel_f[0], "Amount"] = new_amt
                    fresh_f2.at[sel_f[0], "Status"] = new_sts
                    save_csv(fresh_f2, FEE_FILE)
                    st.success("✅ Updated!")
                    refresh()

    with tab3:
        fresh_f3 = load_csv(FEE_FILE, ["ID","Amount","Status","Date"])
        if fresh_f3.empty:
            st.info("No records.")
        else:
            disp = pd.merge(fresh_f3, fresh_df_f[["ID","Name","Class"]], on="ID", how="left")
            flt  = st.selectbox("Filter Status", ["All","Paid","Due"], key="fee_flt")
            if flt != "All": disp = disp[disp["Status"] == flt]
            st.dataframe(disp[["Class","Name","Amount","Status","Date"]],
                         use_container_width=True, hide_index=True)
            st.markdown(f"**Total: ৳{disp['Amount'].sum():,.0f}**")
            st.markdown("---")
            merged_del = pd.merge(fresh_f3.reset_index(), fresh_df_f[["ID","Name"]], on="ID", how="left")
            del_opts = [(int(r["index"]), f"{r['Name']} | ৳{r['Amount']} ({r['Status']})")
                        for _, r in merged_del.iterrows()]
            if del_opts:
                d = st.selectbox("Delete", del_opts, format_func=lambda x: x[1], key="del_fee_sel")
                if st.button("🗑️ Delete Fee", key="del_fee_btn"):
                    save_csv(fresh_f3.drop(d[0]).reset_index(drop=True), FEE_FILE)
                    st.success("✅ Deleted!")
                    refresh()


# ════════════════════════════════════════════════
#  7. MARKS & GRADES
# ════════════════════════════════════════════════
elif menu == "📚 Marks & Grades":
    st.markdown("<div class='page-title'>📚 Marks & Grading</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Add Marks", "✏️ Update Marks", "📊 Report Card"])

    fresh_df_m = load_csv(FILE, STU_COLS)
    fresh_sub  = load_csv(SUBJECT_FILE, ["Subject"])
    s_list_m   = get_student_list(fresh_df_m)

    with tab1:
        if not s_list_m or fresh_sub.empty:
            st.warning("Add students and subjects first.")
        else:
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    sel_s   = st.selectbox("Student", s_list_m, key="mrk_sel")
                with c2:
                    sel_sub = st.selectbox("Subject", fresh_sub["Subject"].tolist(), key="add_mrk_sub")
                with c3:
                    marks_v = st.number_input("Marks (0–100)", 0, 100, 0, key="add_mrk_val")
                if st.button("💾 Save Marks", type="primary", key="save_mrk_btn"):
                    sid     = sid_from(sel_s)
                    grade   = get_grade(marks_v)
                    fresh_m = load_csv(MARK_FILE, ["ID","Subject","Marks","Grade"])
                    row     = pd.DataFrame([[sid, sel_sub, marks_v, grade]],
                                           columns=["ID","Subject","Marks","Grade"])
                    save_csv(pd.concat([fresh_m, row], ignore_index=True), MARK_FILE)
                    st.success(f"✅ Saved!  Grade: **{grade}**")
                    refresh()

    with tab2:
        fresh_m2 = load_csv(MARK_FILE, ["ID","Subject","Marks","Grade"])
        if fresh_m2.empty:
            st.info("No marks yet.")
        else:
            disp_m = pd.merge(fresh_m2.reset_index(), fresh_df_m[["ID","Name"]], on="ID", how="left")
            opts   = [(int(r["index"]), f"{r['Name']} | {r['Subject']} | {r['Marks']}")
                      for _, r in disp_m.iterrows()]
            sel_m  = st.selectbox("Select Record", opts, format_func=lambda x: x[1], key="upd_mrk_sel")
            row_m  = fresh_m2.loc[sel_m[0]]
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    sub_opts = fresh_sub["Subject"].tolist() or [row_m["Subject"]]
                    new_sub  = st.selectbox("Subject", sub_opts,
                                            index=sub_opts.index(row_m["Subject"]) if row_m["Subject"] in sub_opts else 0,
                                            key="upd_mrk_sub")
                with c2:
                    new_mrk = st.number_input("Marks", 0, 100, int(float(row_m["Marks"])), key="upd_mrk_val")
                if st.button("💾 Update Marks", type="primary", key="upd_mrk_btn"):
                    fresh_m2.at[sel_m[0], "Subject"] = new_sub
                    fresh_m2.at[sel_m[0], "Marks"]   = new_mrk
                    fresh_m2.at[sel_m[0], "Grade"]   = get_grade(new_mrk)
                    save_csv(fresh_m2, MARK_FILE)
                    st.success("✅ Updated!")
                    refresh()

    with tab3:
        fresh_m3 = load_csv(MARK_FILE, ["ID","Subject","Marks","Grade"])
        if fresh_m3.empty or fresh_df_m.empty:
            st.info("No data.")
        else:
            sel_rpt   = st.selectbox("Select Student", s_list_m, key="rpt_sel")
            stu_id    = sid_from(sel_rpt)
            stu_row   = fresh_df_m[fresh_df_m["ID"] == stu_id].iloc[0]
            stu_marks = fresh_m3[fresh_m3["ID"] == stu_id]

            if stu_marks.empty:
                st.info("No marks for this student.")
            else:
                st.markdown(f"### 📄 Report Card — {stu_row['Name']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Class", stu_row["Class"])
                c2.metric("Roll",  int(float(stu_row["Roll"])))
                avg = float(stu_marks["Marks"].mean())
                c3.metric("Average", f"{avg:.1f}  ({get_grade(avg)})")

                st.dataframe(stu_marks[["Subject","Marks","Grade"]],
                             use_container_width=True, hide_index=True)
                fig = px.bar(stu_marks, x="Subject", y="Marks", color="Grade", text="Grade",
                             color_discrete_sequence=px.colors.qualitative.Bold)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
                st.plotly_chart(fig, use_container_width=True)

                if st.button("📄 Download Report Card PDF", type="primary", key="rpt_pdf_btn"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_fill_color(15,23,42); pdf.rect(0,0,210,40,style="F")
                    pdf.set_font("Arial","B",20); pdf.set_text_color(255,255,255)
                    pdf.set_xy(0,10); pdf.cell(210,10,"EduPro ERP — Report Card",align="C")
                    pdf.set_font("Arial","",11); pdf.set_xy(0,22)
                    pdf.cell(210,8,f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",align="C")
                    pdf.set_text_color(0,0,0); pdf.set_font("Arial","B",13)
                    pdf.set_xy(20,50)
                    pdf.cell(0,8,f"Student: {stu_row['Name']}  |  Class: {stu_row['Class']}  |  Roll: {int(float(stu_row['Roll']))}")
                    pdf.set_font("Arial","B",11); pdf.set_xy(20,65)
                    pdf.set_fill_color(30,41,59); pdf.set_text_color(255,255,255)
                    for h,w in [("Subject",80),("Marks",30),("Grade",30)]:
                        pdf.cell(w,8,h,border=1,fill=True,align="C")
                    pdf.ln()
                    pdf.set_font("Arial","",11); pdf.set_text_color(0,0,0)
                    for _, mr in stu_marks.iterrows():
                        pdf.set_x(20)
                        pdf.cell(80,8,str(mr["Subject"]),border=1)
                        pdf.cell(30,8,str(int(float(mr["Marks"]))),border=1,align="C")
                        pdf.cell(30,8,str(mr["Grade"]),border=1,align="C")
                        pdf.ln()
                    pdf.set_x(20); pdf.set_font("Arial","B",11)
                    pdf.cell(80,8,"Average",border=1)
                    pdf.cell(30,8,f"{avg:.1f}",border=1,align="C")
                    pdf.cell(30,8,get_grade(avg),border=1,align="C")
                    pdf_bytes = pdf.output(dest="S").encode("latin1")
                    st.download_button("⬇️ Download PDF", data=pdf_bytes,
                                       file_name=f"{stu_row['Name']}_ReportCard.pdf",
                                       mime="application/pdf")


# ════════════════════════════════════════════════
#  8. ID CARD
# ════════════════════════════════════════════════
elif menu == "🪪 ID Card":
    st.markdown("<div class='page-title'>🪪 ID Card Generator</div>", unsafe_allow_html=True)
    fresh_df_id = load_csv(FILE, STU_COLS)
    s_list_id   = get_student_list(fresh_df_id)

    if not s_list_id:
        st.warning("Admit students first.")
    else:
        sel    = st.selectbox("Select Student", s_list_id, key="id_card_sel")
        stu_id = sid_from(sel)
        s      = fresh_df_id[fresh_df_id["ID"] == stu_id].iloc[0]

        with st.container(border=True):
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#1e293b,#0f172a);
                        border:2px solid #38bdf8;border-radius:14px;
                        padding:24px 32px;max-width:440px;font-family:sans-serif;'>
              <div style='font-size:20px;font-weight:800;color:#38bdf8;text-align:center;
                          border-bottom:1px solid #334155;padding-bottom:10px;margin-bottom:14px;'>
                🎓 EduPro ERP — Student ID
              </div>
              <table style='color:#e2e8f0;font-size:14px;width:100%;border-spacing:0 6px;'>
                <tr><td style='color:#94a3b8;width:100px;'>Name</td><td style='font-weight:700;'>{s['Name']}</td></tr>
                <tr><td style='color:#94a3b8;'>Class</td><td>{s['Class']}</td></tr>
                <tr><td style='color:#94a3b8;'>Roll</td><td>{int(float(s['Roll']))}</td></tr>
                <tr><td style='color:#94a3b8;'>Gender</td><td>{s['Gender']}</td></tr>
                <tr><td style='color:#94a3b8;'>ID No</td><td style='font-family:monospace;color:#38bdf8;'>{s['ID']}</td></tr>
                <tr><td style='color:#94a3b8;'>Phone</td><td>{s['Phone']}</td></tr>
                <tr><td style='color:#94a3b8;'>Father</td><td>{s['Father_Name']}</td></tr>
                <tr><td style='color:#94a3b8;'>Mother</td><td>{s['Mother_Name']}</td></tr>
                <tr><td style='color:#94a3b8;'>Issued</td><td>{s['Date']}</td></tr>
              </table>
            </div>""", unsafe_allow_html=True)

        if st.button("📄 Generate PDF ID Card", type="primary", key="id_pdf_btn"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_fill_color(15,23,42); pdf.rect(45,30,120,115,style="F")
            pdf.set_draw_color(56,189,248); pdf.set_line_width(1.2); pdf.rect(45,30,120,115)
            pdf.set_fill_color(30,41,59); pdf.rect(45,30,120,22,style="F")
            pdf.set_font("Arial","B",13); pdf.set_text_color(255,255,255)
            pdf.set_xy(45,37); pdf.cell(120,10,"EduPro ERP — Student ID Card",align="C")
            pdf.set_text_color(0,0,0)
            for y_pos, label, value in [
                (58,"Name",    str(s["Name"])),
                (66,"Class",   str(s["Class"])),
                (74,"Roll",    str(int(float(s["Roll"])))),
                (82,"Gender",  str(s["Gender"])),
                (90,"ID No",   str(s["ID"])),
                (98,"Phone",   str(s["Phone"])),
                (106,"Father", str(s["Father_Name"])),
                (114,"Mother", str(s["Mother_Name"])),
                (122,"Issued", str(s["Date"])),
            ]:
                pdf.set_font("Arial","B",10); pdf.set_xy(52, y_pos); pdf.cell(30,7,f"{label}:")
                pdf.set_font("Arial","",10);  pdf.cell(78,7,value)
            pdf_bytes = pdf.output(dest="S").encode("latin1")
            st.success("✅ ID Card ready!")
            st.download_button("⬇️ Download PDF", data=pdf_bytes,
                               file_name=f"{s['Name']}_ID.pdf", mime="application/pdf")


# ════════════════════════════════════════════════
#  9. USER MANAGEMENT
# ════════════════════════════════════════════════
elif menu == "🔑 User Management":
    st.markdown("<div class='page-title'>🔑 User Management</div>", unsafe_allow_html=True)

    if st.session_state.get("role") != "Admin":
        st.error("🚫 Admin access only.")
        st.stop()

    tab1, tab2 = st.tabs(["➕ Add User", "📋 Manage Users"])

    with tab1:
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_u = st.text_input("Username", key="new_uname")
            with c2:
                new_p = st.text_input("Password", type="password", key="new_upass")
            with c3:
                new_r = st.selectbox("Role", ["Admin","Teacher","Staff"], key="new_user_role")
            if st.button("➕ Add User", type="primary", key="add_user_btn"):
                fresh_u = load_csv(USERS_FILE, USR_COLS)
                if not new_u.strip() or not new_p.strip():
                    st.error("Username and Password required.")
                elif new_u in fresh_u["Username"].values:
                    st.error("Username already exists.")
                else:
                    row = pd.DataFrame([[new_u.strip(), hash_pw(new_p), new_r]], columns=USR_COLS)
                    save_csv(pd.concat([fresh_u, row], ignore_index=True), USERS_FILE)
                    st.success(f"✅ User **{new_u}** created!")
                    refresh()

    with tab2:
        fresh_u2 = load_csv(USERS_FILE, USR_COLS)
        if fresh_u2.empty:
            st.info("No users.")
        else:
            st.dataframe(fresh_u2[["Username","Role"]], use_container_width=True, hide_index=True)
            st.markdown("---")
            del_u = st.selectbox("Delete User", fresh_u2["Username"].tolist(), key="del_user_sel")
            if st.button("🗑️ Delete User", key="del_user_btn"):
                if del_u == st.session_state.get("username"):
                    st.error("❌ Cannot delete your own account.")
                else:
                    save_csv(fresh_u2[fresh_u2["Username"] != del_u].reset_index(drop=True), USERS_FILE)
                    st.success(f"✅ User **{del_u}** deleted.")
                    refresh()
            st.markdown("---")
            st.markdown("##### 🔒 Change Password")
            cp_u = st.selectbox("Select User", fresh_u2["Username"].tolist(), key="cp_u")
            cp_p = st.text_input("New Password", type="password", key="cp_p")
            if st.button("🔒 Update Password", type="primary", key="cp_btn"):
                if not cp_p.strip():
                    st.error("Enter a new password.")
                else:
                    fresh_u3 = load_csv(USERS_FILE, USR_COLS)
                    idx = fresh_u3.index[fresh_u3["Username"] == cp_u][0]
                    fresh_u3.at[idx, "Password"] = hash_pw(cp_p)
                    save_csv(fresh_u3, USERS_FILE)
                    st.success("✅ Password updated!")
                    refresh()