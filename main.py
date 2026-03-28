import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import uuid

# ---------------- CONFIG ----------------
FILE = "students.csv"
IMG_FOLDER = "images"
os.makedirs(IMG_FOLDER, exist_ok=True)

st.set_page_config(page_title="Student ERP", layout="wide")

# ---------------- LOGIN ----------------
def login():
    st.markdown("## 🔐 Login System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state["login"] = True
            st.session_state["role"] = "admin"
        else:
            st.session_state["login"] = True
            st.session_state["role"] = "user"

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

# ---------------- LOAD DATA ----------------
if os.path.exists(FILE):
    df = pd.read_csv(FILE)
    df = df.reindex(columns=["ID","Name","Age","Class","Image","Date"])
    df["Image"] = df["Image"].fillna("").astype(str)
else:
    df = pd.DataFrame(columns=["ID","Name","Age","Class","Image","Date"])

# ---------------- SIDEBAR ----------------
st.sidebar.title("🎓 Student ERP")

menu = st.sidebar.selectbox("Menu", [
    "Dashboard",
    "Manage Students",
    "ID Card",
    "Backup/Restore"
])

if st.sidebar.button("🚪 Logout"):
    st.session_state["login"] = False
    st.rerun()

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric("👨‍🎓 Students", len(df))
    col2.metric("🎂 Avg Age", int(df["Age"].mean()) if len(df)>0 else 0)
    col3.metric("🏫 Classes", df["Class"].nunique() if len(df)>0 else 0)

    st.markdown("### 📊 Class Distribution")
    if len(df) > 0:
        st.bar_chart(df["Class"].value_counts())

    st.markdown("### 📈 Age Chart")
    if len(df) > 0:
        st.line_chart(df["Age"])

# ---------------- MANAGE ----------------
elif menu == "Manage Students":
    st.title("🎓 Manage Students")

    # ---- ADD ----
    st.subheader("➕ Add Student")

    col1, col2, col3 = st.columns(3)

    with col1:
        name = st.text_input("Name")
    with col2:
        age = st.number_input("Age", 1, 100)
    with col3:
        student_class = st.text_input("Class")

    image = st.file_uploader("Upload Photo", type=["jpg","png"])
    camera = st.camera_input("Take Photo")

    if camera:
        image = camera

    if image:
        st.image(image, width=120)

    if st.button("Add Student"):
        if name.strip() and student_class.strip():
            new_id = str(uuid.uuid4())[:8]
            date = datetime.now().strftime("%Y-%m-%d")

            img_path = ""
            if image:
                img_path = os.path.join(IMG_FOLDER, f"{new_id}.png")
                with open(img_path, "wb") as f:
                    f.write(image.getbuffer())

            new_data = pd.DataFrame(
                [[new_id, name, age, student_class, img_path, date]],
                columns=["ID","Name","Age","Class","Image","Date"]
            )

            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(FILE, index=False)

            st.toast("Student Added 🎉")

    # ---- FILTER ----
    st.subheader("🎯 Filter")

    df_display = df.copy()

    if len(df) > 0:
        selected_class = st.selectbox("Class", ["All"] + list(df["Class"].unique()))
        if selected_class != "All":
            df_display = df_display[df_display["Class"] == selected_class]

    search = st.text_input("Search Name")
    if search:
        df_display = df_display[df_display["Name"].str.contains(search, case=False)]

    # ---- TABLE ----
    st.subheader("📋 Student List")
    st.dataframe(df_display, use_container_width=True)

    st.download_button("📥 Download CSV", df.to_csv(index=False), "students.csv")

    # ---- DETAILS CARD ----
    st.subheader("👤 Profile")

    if len(df_display) > 0:
        idx = st.selectbox("Select Student", df_display.index)
        student = df_display.loc[idx]

        st.markdown(f"""
        <div style="padding:20px;border-radius:10px;background:#f0f2f6">
        <h3>👤 {student['Name']}</h3>
        <p>🆔 {student['ID']}</p>
        <p>🎂 {student['Age']}</p>
        <p>📚 {student['Class']}</p>
        <p>📅 {student['Date']}</p>
        </div>
        """, unsafe_allow_html=True)

        if student["Image"] and os.path.exists(student["Image"]):
            st.image(student["Image"], width=150)

    # ---- EDIT / DELETE (ADMIN ONLY) ----
    if st.session_state["role"] == "admin":

        st.subheader("✏️ Edit")
        if len(df) > 0:
            edit_idx = st.selectbox("Row", df.index)

            new_name = st.text_input("New Name", df.loc[edit_idx]["Name"])
            new_age = st.number_input("New Age", 1, 100, value=int(df.loc[edit_idx]["Age"]))
            new_class = st.text_input("New Class", df.loc[edit_idx]["Class"])

            if st.button("Update"):
                df.at[edit_idx, "Name"] = new_name
                df.at[edit_idx, "Age"] = new_age
                df.at[edit_idx, "Class"] = new_class
                df.to_csv(FILE, index=False)
                st.success("Updated!")

        st.subheader("❌ Delete")
        if len(df) > 0:
            del_idx = st.number_input("Row", 0, len(df)-1)

            if st.button("Delete"):
                df = df.drop(del_idx).reset_index(drop=True)
                df.to_csv(FILE, index=False)
                st.warning("Deleted!")

# ---------------- ID CARD ----------------
elif menu == "ID Card":
    st.title("🪪 ID Card Generator")

    if len(df) > 0:
        idx = st.selectbox("Select Student", df.index)

        if st.button("Generate"):
            student = df.loc[idx]

            pdf = FPDF()
            pdf.add_page()

            pdf.set_fill_color(0,102,204)
            pdf.rect(10,10,190,40,'F')

            pdf.set_text_color(255,255,255)
            pdf.set_font("Arial",'B',16)
            pdf.cell(0,20,"STUDENT ID CARD", ln=True, align='C')

            pdf.set_text_color(0,0,0)
            pdf.ln(10)

            pdf.cell(0,10,f"ID: {student['ID']}", ln=True)
            pdf.cell(0,10,f"Name: {student['Name']}", ln=True)
            pdf.cell(0,10,f"Class: {student['Class']}", ln=True)

            if student["Image"] and os.path.exists(student["Image"]):
                pdf.image(student["Image"], x=80, y=60, w=40)

            pdf_bytes = pdf.output(dest='S').encode('latin1')

            st.download_button("📥 Download ID", pdf_bytes, "id_card.pdf")

# ---------------- BACKUP ----------------
elif menu == "Backup/Restore":
    st.title("📦 Backup System")

    if st.button("Backup Data"):
        df.to_csv("backup.csv", index=False)
        st.success("Backup Saved!")

    file = st.file_uploader("Restore CSV", type=["csv"])

    if file:
        df = pd.read_csv(file)
        df.to_csv(FILE, index=False)
        st.success("Data Restored!")