import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import uuid

# ---------------- FILES ----------------
FILE = "students.csv"
CLASS_FILE = "classes.csv"
ATT_FILE = "attendance.csv"
FEE_FILE = "fees.csv"
MARK_FILE = "marks.csv"
IMG_FOLDER = "images"

os.makedirs(IMG_FOLDER, exist_ok=True)

st.set_page_config(page_title="Student ERP", layout="wide")

# ---------------- LOGIN ----------------
def login():
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u == "admin" and p == "1234":
            st.session_state["login"] = True
        else:
            st.session_state["login"] = True

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

# ---------------- LOAD DATA ----------------
def load_csv(file, cols):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=cols)

df = load_csv(FILE, ["ID","Name","Age","Class","Image","Date"])
class_df = load_csv(CLASS_FILE, ["Class"])
att_df = load_csv(ATT_FILE, ["ID","Date","Status"])
fee_df = load_csv(FEE_FILE, ["ID","Amount","Status","Date"])
mark_df = load_csv(MARK_FILE, ["ID","Subject","Marks"])

# ---------------- SIDEBAR ----------------
menu = st.sidebar.selectbox("Menu", [
    "Dashboard","Class Setup","Manage Students",
    "Attendance","Fees","Marks","ID Card","Backup"
])

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Dashboard")

    st.markdown("""
    <style>
    .card{padding:20px;border-radius:15px;background:#111827;color:white;text-align:center}
    </style>
    """, unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    c1.markdown(f"<div class='card'>👨‍🎓<br>{len(df)}</div>", True)
    c2.markdown(f"<div class='card'>🎂<br>{int(df['Age'].mean()) if len(df)>0 else 0}</div>", True)
    c3.markdown(f"<div class='card'>🏫<br>{df['Class'].nunique()}</div>", True)

    # Attendance %
    if len(att_df)>0:
        p = len(att_df[att_df["Status"]=="Present"])
        t = len(att_df)
        st.metric("📅 Attendance %", f"{round((p/t)*100,2)}%")

    # Fees
    if len(fee_df)>0:
        paid = fee_df[fee_df["Status"]=="Paid"]["Amount"].sum()
        due = fee_df[fee_df["Status"]=="Due"]["Amount"].sum()
        st.metric("💵 Paid", paid)
        st.metric("❗ Due", due)

    st.bar_chart(df["Class"].value_counts())

# ---------------- CLASS SETUP ----------------
elif menu == "Class Setup":
    st.title("🏫 Class Setup")

    new_class = st.text_input("New Class")

    if st.button("Add"):
        if new_class:
            class_df = pd.concat([class_df, pd.DataFrame([[new_class]],columns=["Class"])])
            class_df.to_csv(CLASS_FILE,index=False)
            st.success("Added")

    st.dataframe(class_df)

# ---------------- STUDENT ----------------
elif menu == "Manage Students":
    st.title("🎓 Students")

    name = st.text_input("Name")
    age = st.number_input("Age",1,100)

    if len(class_df)>0:
        student_class = st.selectbox("Class", class_df["Class"])
    else:
        student_class = st.text_input("Class")

    image = st.file_uploader("Photo")

    if st.button("Add Student"):
        new_id = str(uuid.uuid4())[:8]
        date = datetime.now().strftime("%Y-%m-%d")

        img_path=""
        if image:
            img_path = os.path.join(IMG_FOLDER,f"{new_id}.png")
            with open(img_path,"wb") as f:
                f.write(image.getbuffer())

        new = pd.DataFrame([[new_id,name,age,student_class,img_path,date]],columns=df.columns)
        df = pd.concat([df,new])
        df.to_csv(FILE,index=False)
        st.success("Added")

    st.dataframe(df)

# ---------------- ATTENDANCE ----------------
elif menu == "Attendance":
    st.title("📅 Attendance")

    if len(df)>0:
        idx = st.selectbox("Student", df.index)
        student = df.loc[idx]

        status = st.radio("Status",["Present","Absent"])

        if st.button("Mark"):
            new = pd.DataFrame([[student["ID"],datetime.now().strftime("%Y-%m-%d"),status]],
                               columns=att_df.columns)
            att_df = pd.concat([att_df,new])
            att_df.to_csv(ATT_FILE,index=False)
            st.success("Done")

    st.dataframe(att_df)

# ---------------- FEES ----------------
elif menu == "Fees":
    st.title("💰 Fees")

    if len(df)>0:
        idx = st.selectbox("Student", df.index)
        student = df.loc[idx]

        amt = st.number_input("Amount",0)
        status = st.selectbox("Status",["Paid","Due"])

        if st.button("Add Fee"):
            new = pd.DataFrame([[student["ID"],amt,status,datetime.now().strftime("%Y-%m-%d")]],
                               columns=fee_df.columns)
            fee_df = pd.concat([fee_df,new])
            fee_df.to_csv(FEE_FILE,index=False)
            st.success("Added")

    st.dataframe(fee_df)

# ---------------- MARKS ----------------
elif menu == "Marks":
    st.title("📚 Marks")

    def grade(m):
        if m>=80:return "A+"
        elif m>=70:return "A"
        elif m>=60:return "B"
        else:return "C"

    if len(df)>0:
        idx = st.selectbox("Student", df.index)
        student = df.loc[idx]

        sub = st.text_input("Subject")
        m = st.number_input("Marks",0,100)

        if st.button("Add Marks"):
            new = pd.DataFrame([[student["ID"],sub,m]],columns=mark_df.columns)
            mark_df = pd.concat([mark_df,new])
            mark_df.to_csv(MARK_FILE,index=False)
            st.success("Added")

    mark_df["Grade"] = mark_df["Marks"].apply(grade)

    st.dataframe(mark_df)

    # Result
    st.subheader("Result")
    if len(df)>0:
        idx = st.selectbox("Result Student", df.index)
        student = df.loc[idx]

        sm = mark_df[mark_df["ID"]==student["ID"]]
        st.dataframe(sm)

        if len(sm)>0:
            st.metric("Avg", round(sm["Marks"].mean(),2))
            st.bar_chart(sm.set_index("Subject"))

# ---------------- ID CARD ----------------
elif menu == "ID Card":
    st.title("🪪 ID Card")

    if len(df)>0:
        idx = st.selectbox("Student", df.index)

        if st.button("Generate"):
            s = df.loc[idx]

            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("Arial","B",16)
            pdf.cell(0,20,"STUDENT ID CARD",ln=True,align="C")

            pdf.cell(0,10,f"Name: {s['Name']}",ln=True)
            pdf.cell(0,10,f"Class: {s['Class']}",ln=True)

            pdf_bytes = pdf.output(dest='S').encode('latin1')
            st.download_button("Download",pdf_bytes,"id.pdf")

# ---------------- BACKUP ----------------
elif menu == "Backup":
    st.title("📦 Backup")

    if st.button("Backup"):
        df.to_csv("backup.csv",index=False)
        st.success("Saved")

    f = st.file_uploader("Restore",type=["csv"])
    if f:
        df = pd.read_csv(f)
        df.to_csv(FILE,index=False)
        st.success("Restored")