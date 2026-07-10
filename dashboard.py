import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บให้แสดงผลเต็มจอแบบกว้าง (Wide Layout)
st.set_page_config(
    page_title="NPI Integration Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ฟังก์ชันสำหรับดึงข้อมูลจากไฟล์ Excel ที่อยู่คู่กันบน GitHub
@st.cache_data(ttl=60)  # รีเฟรชและตรวจสอบไฟล์ใหม่ทุกๆ 1 นาที
def load_data_local():
    # อ่านไฟล์ดิบที่ชื่อ data.xlsx ในโฟลเดอร์เดียวกัน
    # ดึงข้อมูลจากแท็บแรกสุด (Index 0) เพื่อความชัวร์ หรือเปลี่ยนเป็น "Schedule2026"
    df = pd.read_excel("data.xlsx", sheet_name=0, engine="openpyxl")
    
    # ล้างช่องว่างที่หัวคอลัมน์ออกทั้งหมดเพื่อป้องกันการเรียกชื่อคอลลัมน์พลาด
    df.columns = df.columns.astype(str).str.strip()
    
    # ดึงคอลัมน์สำคัญมาแปลงเป็นข้อความธรรมดา ล้างช่องว่าง และคัดแถวว่างทิ้ง
    df['Type'] = df['Type'].astype(str).str.strip()
    df['Status'] = df['Status'].astype(str).str.strip()
    df = df[df['Type'] != 'nan']
    df = df[df['Status'] != 'nan']
    
    return df

# โหลดข้อมูลเข้ามาเก็บไว้ในตัวแปรชื่อ df
try:
    df = load_data_local()
except Exception as e:
    st.error(f"❌ ไม่สามารถเปิดไฟล์ข้อมูลใน GitHub ได้: {e}")
    st.info("💡 คำแนะนำ: โปรดตรวจสอบว่าคุณได้ลากไฟล์ Excel ขึ้นไปวางบน GitHub โดยตั้งชื่อว่า 'data.xlsx' เรียบร้อยแล้วหรือยัง")
    st.stop()

# --- SIDEBAR FILTERS (เมนูด้านซ้ายสำหรับกรองข้อมูล) ---
st.sidebar.header("🔍 คัดกรองข้อมูล Task")

# สร้างตัวเลือกประเภทงาน (Type) บนเมนูซ้าย
all_types = sorted(df['Type'].unique().tolist())
selected_types = st.sidebar.multiselect("เลือกประเภทงาน (Type)", options=all_types, default=all_types)

# กรองข้อมูลตามที่ User เลือก
filtered_df = df[df['Type'].isin(selected_types)]


# --- MAIN INTERFACE (ส่วนแสดงผลหลักตรงกลางหน้าเว็บ) ---
st.title("🚀 NPI Integration Task Dashboard")
st.write("ระบบดึงข้อมูลและประมวลผลความคืบหน้าของงานทีม NPI (GitHub Storage System)")
st.markdown("---")

# 3. ส่วนแสดง KPI Metrics (ตัวเลขสำคัญด้านบนสุด)
total_tasks = len(filtered_df)
completed_tasks = len(filtered_df[filtered_df['Status'].str.lower() == 'closed'])
overdue_tasks = len(filtered_df[filtered_df['Status'].str.lower() == 'overdue'])

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
    if total_tasks > 0:
        type_counts = filtered_df['Type'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        
        fig_pie = px.pie(type_counts, values='Count', names='Type', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("ไม่มีข้อมูลที่จะแสดงกราฟวงกลม")

with chart_col2:
    st.subheader("📊 สถานะงานแยกตามแผนก (Task Progress by Type)")
    if total_tasks > 0:
        fig_bar = px.histogram(filtered_df, x='Type', color='Status', barmode='stack',
                               color_discrete_map={'Closed': '#22c55e', 'On process': '#3b82f6', 'Overdue': '#ef4444', 'On time': '#10b981'})
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("ไม่มีข้อมูลที่จะแสดงกราฟแท่ง")


st.markdown("---")

# 5. ส่วนแสดงตารางรายชื่องานที่ Overdue (งานที่เกินกำหนด)
st.subheader("🚨 รายชื่อ Task ที่เกินกำหนด (Overdue Task List)")

# ค้นหาคอลัมน์ที่มีอยู่ในข้อมูลจริงเพื่อป้องกัน Error กรณีชื่อคอลัมน์พิมพ์เล็ก-ใหญ่ไม่ตรงกัน
available_cols = filtered_df.columns.tolist()
desired_cols = ['Type', 'Task', 'PRODUCT', 'Target Date']
display_cols = [col for col in desired_cols if col in available_cols]

overdue_list = filtered_df[filtered_df['Status'].str.lower() == 'overdue'][display_cols]

if not overdue_list.empty:
    st.dataframe(overdue_list, use_container_width=True)
else:
    st.success("🎉 ยอดเยี่ยมมาก! ไม่มีงานที่เกินกำหนด (Overdue) ในขณะนี้")
