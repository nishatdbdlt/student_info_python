import streamlit as st
import pandas as pd
import os
from fpdf import FPDF

# ---------------- FILE & FOLDER ----------------
FILE = "students.csv"
IMG_FOLDER = "images"
os.makedirs(IMG_FOLDER, exist_ok=True)

# ---------------- LOGIN ----------------
def login():
    st.title("🔐 Login System")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.session_state["login"] = True
        else:
            st.error("Wrong credentials!")

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

# ---------------- LOAD DATA ----------------
if os.path.exists(FILE):
    df = pd.read_csv(FILE)

    # ✅ Fix columns + NaN
    df = df.reindex(columns=["Name", "Age", "Class", "Image"])
    df["Image"] = df["Image"].fillna("").astype(str)
else:
    df = pd.DataFrame(columns=["Name", "Age", "Class", "Image"])

st.set_page_config(page_title="Student Management PRO", layout="wide")
st.title("🎓 Student Management PRO")

# ---------------- ADD STUDENT ----------------
st.subheader("➕ Add Student")
col1, col2, col3 = st.columns(3)

with col1:
    name = st.text_input("Name")
with col2:
    age = st.number_input("Age", 1, 100)
with col3:
    student_class = st.text_input("Class")

image = st.file_uploader("Upload Photo", type=["jpg", "png"])

if st.button("Add Student"):
    if name.strip() and student_class.strip():
        img_path = ""

        if image:
            img_path = os.path.join(IMG_FOLDER, image.name)
            with open(img_path, "wb") as f:
                f.write(image.getbuffer())

        new_data = pd.DataFrame(
            [[name, age, student_class, img_path]],
            columns=["Name", "Age", "Class", "Image"]
        )

        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(FILE, index=False)
        st.success("✅ Student Added!")

# ---------------- SEARCH ----------------
st.subheader("🔍 Search Student")
search = st.text_input("Search by Name")

df_display = df.copy()
if search:
    df_display = df_display[df_display["Name"].str.contains(search, case=False)]

# ---------------- TABLE ----------------
st.subheader("📋 Student List")
st.dataframe(df_display, use_container_width=True)

# ---------------- DETAILS ----------------
st.subheader("👤 Student Details")
if len(df_display) > 0:
    idx = st.selectbox("Select Student", df_display.index)
    student = df_display.loc[idx]

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Name:** {student['Name']}")
        st.write(f"**Age:** {student['Age']}")
        st.write(f"**Class:** {student['Class']}")

    with col2:
        img = student["Image"]
        if isinstance(img, str) and img.strip() != "" and os.path.exists(img):
            st.image(img, width=200)

# ---------------- EDIT ----------------
st.subheader("✏️ Edit Student")
if len(df) > 0:
    edit_idx = st.selectbox("Select Row", df.index)

    new_name = st.text_input("New Name", df.loc[edit_idx]["Name"])
    new_age = st.number_input("New Age", 1, 100, value=int(df.loc[edit_idx]["Age"]))
    new_class = st.text_input("New Class", df.loc[edit_idx]["Class"])

    if st.button("Update"):
        df.at[edit_idx, "Name"] = new_name
        df.at[edit_idx, "Age"] = new_age
        df.at[edit_idx, "Class"] = new_class
        df.to_csv(FILE, index=False)
        st.success("✅ Updated!")

# ---------------- DELETE ----------------
st.subheader("❌ Delete Student")
if len(df) > 0:
    del_idx = st.number_input("Row Number", 0, len(df) - 1, step=1)

    if st.button("Delete"):
        df = df.drop(del_idx).reset_index(drop=True)
        df.to_csv(FILE, index=False)
        st.warning("Deleted!")

# ---------------- PDF ----------------
# ---------------- PDF + DOWNLOAD ----------------
st.subheader("🪪 ID Card")

if len(df) > 0:
    id_idx = st.selectbox("Select Student for ID", df.index)

    if st.button("Generate PDF"):
        student = df.loc[id_idx]

        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "Student ID Card", ln=True, align='C')

        pdf.set_font("Arial", size=12)
        pdf.ln(10)

        pdf.cell(200, 10, f"Name: {student['Name']}", ln=True)
        pdf.cell(200, 10, f"Age: {student['Age']}", ln=True)
        pdf.cell(200, 10, f"Class: {student['Class']}", ln=True)

        img = student["Image"]
        if isinstance(img, str) and img.strip() != "" and os.path.exists(img):
            pdf.image(img, x=80, y=60, w=40)

        # 🔥 MEMORY BUFFER
        pdf_bytes = pdf.output(dest='S').encode('latin1')

        st.download_button(
            label="📥 Download ID Card",
            data=pdf_bytes,
            file_name="id_card.pdf",
            mime="application/pdf"
        )