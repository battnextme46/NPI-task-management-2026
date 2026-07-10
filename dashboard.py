import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บแบบกว้างเต็มจอ
st.set_page_config(
    page_title="NPI Fronted Task Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ฟังก์ชันโหลดข้อมูล - สั่งข้ามไปอ่านที่หัวตารางแถวที่ 12 (header=11) ของแท็บ Schedule2026
@st.cache_data(ttl=10)
def load_npi_data():
    # header=11 หมายถึง แถวที่ 12 ของ Excel เพื่อจับหัวตารางตัวจริงพอดีเป๊ะ
    df = pd.read_excel("data.xlsx", sheet_name="Schedule2026", header=11, engine="openpyxl")
    
    # ล้างช่องว่างที่หัวคอลัมน์
    df.columns = df.columns.astype(str).str.strip()
    
    # ลบแถวที่เป็นค่าว่างเปล่าจากการจองพื้นที่ตารางออก
    df = df.dropna(subset=['Type', 'Status'], how='any')
    
    # แปลงคอลัมน์สำคัญเป็นข้อความสะอาดๆ ล้างช่องว่างซ้ายขวา
    important_cols = ['WW', 'Type', 'TASK', 'Customer', 'PIC', 'Status']
    for col in important_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    # กรองเอาแถวที่เป็นค่า nan ออกทิ้งไป
    df = df[df['Type'].str.lower() != 'nan']
    df = df[df['Status'].str.lower() != 'nan']
    
    # ปรับจูนสถานะให้เป็นมาตรฐานเดียวกัน (เช่น ตัวพิมพ์เล็ก-ใหญ่)
    df['Status_Clean'] = df['Status'].str.lower()
    df.loc[df['Status_Clean'] == 'close', 'Status_Clean'] = 'closed'
    
    return df

# เรียกใช้งานฟังก์ชัน
try:
    df = load_npi_data()
except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการอ่านแถวที่ 12: {e}")
    st.info("💡 คำแนะนำ: โปรดตรวจสอบว่าในไฟล์ Excel แถวที่ 12 มีคอลัมน์ Type และ Status ตรงกันข้ามหรือไม่")
    st.stop()

# --- SIDEBAR FILTERS (แถบกรองข้อมูลด้านซ้าย) ---
st.sidebar.header("🔍 ตัวกรองข้อมูลแดชบอร์ด")

# 1. ตัวกรองผู้รับผิดชอบ (PIC)
all_pics = sorted([p for p in df['PIC'].unique().tolist() if p.lower() != 'nan' and p != ''])
selected_pics = st.sidebar.multiselect("👨‍💻 เลือกผู้รับผิดชอบ (PIC)", options=all_pics, default=all_pics)

# 2. ตัวกรองประเภทงาน (Type)
all_types = sorted([t for t in df['Type'].unique().tolist() if t.lower() != 'nan' and t != ''])
selected_types = st.sidebar.multiselect("📂 เลือกประเภทงาน (Type)", options=all_types, default=all_types)

# กรองตารางข้อมูลหลักตามเงื่อนไขที่คลิกเลือก
filtered_df = df[(df['PIC'].isin(selected_pics)) & (df['Type'].isin(selected_types))]


# --- MAIN INTERFACE (ส่วนกระดานแสดงผลหลัก) ---
st.title("🚀 NPI Integration Fronted Task Dashboard")
st.write("ระบบวิเคราะห์และติดตามสถานะงานของทีม NPI ดึงจากแถวที่ 12 ของตารางข้อมูลดิบ")
st.markdown("---")

# 3. ส่วนแสดง KPI Metrics คำนวณยอด
total_tasks = len(filtered_df)
completed_tasks = len(filtered_df[filtered_df['Status_Clean'] == 'closed'])
on_process_tasks = len(filtered_df[filtered_df['Status_Clean'] == 'on process'])
overdue_tasks = len(filtered_df[filtered_df['Status_Clean'] == 'overdue'])

# คำนวณร้อยละความสำเร็จ (On-time Performance)
on_time_perf = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 100.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="📊 งานทั้งหมดในเงื่อนไข", value=f"{total_tasks} Tasks")
with col2:
    st.metric(label="✅ งานที่เสร็จแล้ว (Closed)", value=f"{completed_tasks} Tasks")
with col3:
    st.metric(label="⏳ กำลังดำเนินการ (On Process)", value=f"{on_process_tasks} Tasks")
with col4:
    st.metric(label="🚨 งานค้างเกินกำหนด (Overdue)", value=f"{overdue_tasks} Tasks")

st.markdown("---")


# 4. ส่วนกางแผนภูมิเวทีวิเคราะห์ (Charts Area)
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("🍕 สัดส่วนปริมาณงานแยกตามประเภท (Task Type Ratio)")
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
    st.subheader("👨‍💻 สรุปจำนวนงานและสถานะรายบุคคล (PIC Progress)")
    if total_tasks > 0:
        fig_bar = px.histogram(filtered_df, y='PIC', color='Status', barmode='stack', orientation='h',
                               color_discrete_map={'Closed': '#22c55e', 'Close': '#22c55e', 'On process': '#3b82f6', 'Overdue': '#ef4444'})
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="จำนวนงาน (Tasks)", yaxis_title="รายชื่อ PIC")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("ไม่มีข้อมูลสำหรับแสดงกราฟแท่ง")

st.markdown("---")


# 5. ส่วนแสดงตารางรายชื่องานที่ค้างเกินกำหนด (Overdue)
st.subheader("🚨 รายรายการงานเกินกำหนดอย่างละเอียด (Overdue Task List)")

overdue_df = filtered_df[filtered_df['Status_Clean'] == 'overdue']

if not overdue_df.empty:
    display_cols = ['WW', 'Type', 'TASK', 'Customer', 'PIC', 'Target Date']
    available_display = [c for c in display_cols if c in overdue_df.columns]
    st.dataframe(overdue_df[available_display].reset_index(drop=True), use_container_width=True)
else:
    st.success("🎉 ยอดเยี่ยมมาก! สมาชิกทุกคนเคลียร์งานตามกำหนดเรียบร้อย ไม่พบงานค้าง Overdue ในขณะนี้")
