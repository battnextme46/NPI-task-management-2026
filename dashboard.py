import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.request
import io

# 1. ตั้งค่าหน้าเว็บให้แสดงผลเต็มจอแบบกว้าง (Wide Layout)
st.set_page_config(
    page_title="NPI Integration Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ฟังก์ชันสำหรับดึงข้อมูลจากคลาวด์บริษัทโดยตรง (Real-time 100%)
@st.cache_data(ttl=60)  # ดึงข้อมูลใหม่จาก Excel ทุกๆ 1 นาที (60 วินาที) ทำให้ข้อมูลอัปเดตอัตโนมัติ
def load_data_from_sharepoint():
    # ลิงก์ตรงที่แปลงพารามิเตอร์เป็นตัวบังคับดาวน์โหลดดิบเรียบร้อยแล้ว
    sharepoint_url = "https://asiamagneticwinding-my.sharepoint.com/personal/npi25_amw-ems_com/_layouts/15/download.aspx?UniqueId=AD9D6A3A-3A5C-457C-A831-40F97A548C03"
    
    # ส่งคำขอจำลองตัวตนเป็นบราวเซอร์เพื่อดาวน์โหลดไฟล์ข้อมูลดิบเข้าหน่วยความจำ
    req = urllib.request.Request(sharepoint_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        file_data = response.read()
    
    # อ่านข้อมูลโดยเจาะจงแท็บ 'Schedule2026' และระบุ engine เป็น openpyxl
    df = pd.read_excel(io.BytesIO(file_data), sheet_name="Schedule2026", engine="openpyxl")
    
    # ล้างช่องว่างที่อาจติดมากับชื่อคอลัมน์
    df.columns = df.columns.str.strip()
    
    # คัดกรองเอาเฉพาะแถวที่มีข้อมูล Type และ Status จริงๆ ป้องกันตารางว่างด้านล่าง
    df = df.dropna(subset=['Type', 'Status']) 
    return df

# โหลดข้อมูลเข้ามาเก็บไว้ในตัวแปรชื่อ df
try:
    df = load_data_from_sharepoint()
except Exception as e:
    st.error(f"❌ ไม่สามารถดึงข้อมูลแบบ Real-time ได้: {e}")
    st.info("💡 คำแนะนำ: หากระบบแจ้งเกี่ยวกับรูปแบบไฟล์ (format) หรือ zip file แสดงว่าองค์กรอาจมีการบล็อกสิทธิ์ไอพีภายนอก ให้เปลี่ยนไปใช้วิธีฝากไฟล์บน GitHub แทนครับ")
    st.stop()

# --- SIDEBAR FILTERS (เมนูด้านซ้ายสำหรับกรองข้อมูล) ---
st.sidebar.header("🔍 คัดกรองข้อมูล Task")

# สร้างตัวเลือกประเภทงาน (Type) บนเมนูซ้าย
all_types = df['Type'].unique().tolist()
selected_types = st.sidebar.multiselect("เลือกประเภทงาน (Type)", options=all_types, default=all_types)

# กรองข้อมูลตามที่ User เลือก
filtered_df = df[df['Type'].isin(selected_types)]


# --- MAIN INTERFACE (ส่วนแสดงผลหลักตรงกลางหน้าเว็บ) ---
st.title("🚀 NPI Integration Task Dashboard")
st.write("ระบบดึงข้อมูลและประมวลผลความคืบหน้าของงานทีม NPI แบบ Real-time")
st.markdown("---")

# 3. ส่วนแสดง KPI Metrics (ตัวเลขสำคัญด้านบนสุด)
total_tasks = len(filtered_df)
completed_tasks = len(filtered_df[filtered_df['Status'].astype(str).str.lower().str.strip() == 'closed'])
overdue_tasks = len(filtered_df[filtered_df['Status'].astype(str).str.lower().str.strip() == 'overdue'])

# คำนวณ % On-time Performance
on_time_perf = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 100.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="📊 จำนวนงานทั้งหมด", value=f"{total_tasks} Tasks")
with col2:
    st.metric(label="✅ งานที่เสร็จสิ้นแล้ว (Closed)", value=f"{completed_tasks} Tasks")
with col3:
    st.metric(label="⚠️ งานที่เกินกำหนด (Overdue)", value=f"{overdue_tasks} Tasks")
with col4:
    st.metric(label="📈 On-time Performance", value=f"{on_time_perf:.1f}%")

st.markdown("---")


# 4. ส่วนแสดงผลกราฟสไตล์ Modern (แบ่งเป็น 2 คอลัมน์ซ้ายขวา)
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("🍕 สัดส่วนประเภทงาน (Task Ratio)")
    type_counts = filtered_df['Type'].value_counts().reset_index()
    type_counts.columns = ['Type', 'Count']
    
    fig_pie = px.pie(type_counts, values='Count', names='Type', hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

with chart_col2:
    st.subheader("📊 สถานะงานแยกตามแผนก (Task Progress by Type)")
    fig_bar = px.histogram(filtered_df, x='Type', color='Status', barmode='stack',
                           color_discrete_map={'Closed': '#22c55e', 'On process': '#3b82f6', 'Overdue': '#ef4444', 'On time': '#10b981'})
    st.plotly_chart(fig_bar, use_container_width=True)


st.markdown("---")

# 5. ส่วนแสดงตารางรายชื่องานที่ Overdue (งานที่เกินกำหนด)
st.subheader("🚨 รายชื่อ Task ที่เกินกำหนด (Overdue Task List)")

# ค้นหาคอลัมน์ที่มีอยู่ในข้อมูลจริงเพื่อป้องกัน Error กรณีชื่อคอลัมน์ไม่ตรงกับตาราง Excel
available_cols = filtered_df.columns.tolist()
desired_cols = ['Type', 'Task', 'PRODUCT', 'Target Date']
display_cols = [col for col in desired_cols if col in available_cols]

overdue_list = filtered_df[filtered_df['Status'].astype(str).str.lower().str.strip() == 'overdue'][display_cols]

if not overdue_list.empty:
    st.dataframe(overdue_list, use_container_width=True)
else:
    st.success("🎉 ยอดเยี่ยมมาก! ไม่มีงานที่เกินกำหนด (Overdue) ในขณะนี้")
