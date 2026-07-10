import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บแบบกว้างเต็มจอ
st.set_page_config(
    page_title="NPI Fronted Task Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ฟังก์ชันโหลดข้อมูล เจาะจงแท็บ Schedule2026 เท่านั้น
@st.cache_data(ttl=10)
def load_npi_data():
    # โหลดไฟล์ data.xlsx เจาะแท็บข้อมูลดิบหลัก
    df = pd.read_excel("data.xlsx", sheet_name="Schedule2026", engine="openpyxl")
    
    # ล้างช่องว่างหัวคอลัมน์
    df.columns = df.columns.astype(str).str.strip()
    
    # ดึงคอลัมน์สำคัญที่ต้องใช้ และลบแถวที่ไม่มีข้อมูลจริงทิ้ง
    important_cols = ['Type', 'TASK', 'Customer', 'PIC', 'Target Date', 'Status']
    # คืนค่ากลับเฉพาะคอลัมน์ที่มีอยู่จริง
    existing_cols = [c for c in important_cols if c in df.columns]
    df = df.dropna(subset=['Type', 'Status'], how='any')
    
    # แปลงข้อมูลเป็นข้อความสะอาดๆ
    for col in existing_cols:
        df[col] = df[col].astype(str).str.strip()
        
    # กรองแถวที่เป็นค่าว่างหรือหัวตารางจำลองออก
    df = df[df['Type'].str.lower() != 'nan']
    df = df[df['Status'].str.lower() != 'nan']
    
    return df

# เรียกใช้งานฟังก์ชัน
try:
    df = load_npi_data()
except Exception as e:
    st.error(f"❌ โครงสร้างข้อมูลไม่ถูกต้องหรือหาแท็บ 'Schedule2026' ไม่เจอ: {e}")
    st.stop()

# --- SIDEBAR FILTERS (แถบควบคุมด้านซ้าย) ---
st.sidebar.header("🔍 ตัวกรองแดชบอร์ด")

# 1. ตัวกรองผู้รับผิดชอบ (PIC)
all_pics = sorted(df['PIC'].unique().tolist())
selected_pics = st.sidebar.multiselect("👨‍💻 เลือกผู้รับผิดชอบ (PIC)", options=all_pics, default=all_pics)

# 2. ตัวกรองประเภทงาน (Type)
all_types = sorted(df['Type'].unique().tolist())
selected_types = st.sidebar.multiselect("📂 เลือกประเภทงาน (Type)", options=all_types, default=all_types)

# กรองข้อมูลตามเงื่อนไขที่เลือก
filtered_df = df[(df['PIC'].isin(selected_pics)) & (df['Type'].isin(selected_types))]


# --- MAIN INTERFACE (ส่วนแสดงผลหลัก) ---
st.title("🚀 NPI Integration Fronted Task Dashboard")
st.write("ข้อมูลวิเคราะห์ความคืบหน้าแบบเรียลไทม์ ดึงจากแท็บข้อมูลดิบ Schedule2026")
st.markdown("---")

# 3. ส่วนแสดง KPI Metrics
total_tasks = len(filtered_df)
# นับตามสถานะ (ปรับตัวอักษรเล็กใหญ่ให้ยืดหยุ่น)
completed_tasks = len(filtered_df[filtered_df['Status'].str.lower() == 'closed'])
on_process_tasks = len(filtered_df[filtered_df['Status'].str.lower() == 'on process'])
overdue_tasks = len(filtered_df[filtered_df['Status'].str.lower() == 'overdue'])

on_time_perf = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 100.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="📊 งานทั้งหมดในเงื่อนไข", value=f"{total_tasks} Tasks")
with col2:
    st.metric(label="✅ เสร็จสิ้น (Closed)", value=f"{completed_tasks} Tasks")
with col3:
    st.metric(label="⏳ กำลังดำเนินการ", value=f"{on_process_tasks} Tasks")
with col4:
    st.metric(label="🚨 เกินกำหนด (Overdue)", value=f"{overdue_tasks} Tasks", delta=f"{overdue_tasks} งานค้าง", delta_color="inverse")

st.markdown("---")


# 4. ส่วนแสดงผลกราฟชั้นสูง
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("🍕 สัดส่วนปริมาณงานแยกตามประเภท (Task Type)")
    if total_tasks > 0:
        type_counts = filtered_df['Type'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        fig_pie = px.pie(type_counts, values='Count', names='Type', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Safe)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("ไม่มีข้อมูลสำหรับแสดงกราฟวงกลม")

with chart_col2:
    st.subheader("👨‍💻 ปริมาณงานและสถานะแยกตามรายบุคคล (PIC Progress)")
    if total_tasks > 0:
        # สร้างกราฟแท่งแนวนอนแจกแจงตาม PIC และซ้อนด้วยสถานะงาน
        fig_bar = px.histogram(filtered_df, y='PIC', color='Status', barmode='stack', orientation='h',
                               color_discrete_map={'closed': '#22c55e', 'on process': '#3b82f6', 'overdue': '#ef4444', 'on time': '#10b981'})
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="จำนวนงาน (Tasks)")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("ไม่มีข้อมูลสำหรับแสดงกราฟแท่ง")

st.markdown("---")


# 5. ส่วนแสดงตารางรายชื่องานที่ค้างเกินกำหนด (Overdue) ปัดคอลัมน์สวยงาม
st.subheader("🚨 รายการงานเกินกำหนดอย่างละเอียด (Overdue Task List)")

overdue_df = filtered_df[filtered_df['Status'].str.lower() == 'overdue']

if not overdue_df.empty:
    # เลือกเฉพาะคอลัมน์สำคัญมาโชว์ให้คนในทีมตามงานง่าย
    display_cols = ['Type', 'TASK', 'Customer', 'PIC', 'Target Date']
    available_display = [c for c in display_cols if c in overdue_df.columns]
    
    st.dataframe(overdue_df[available_display].reset_index(drop=True), use_container_width=True)
else:
    st.success("🎉 ยอดเยี่ยม! ไม่พบงานค้างที่เกินกำหนดส่งในระบบสำหรับเงื่อนไขนี้")
