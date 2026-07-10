import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บให้แสดงผลเต็มจอแบบกว้าง (Wide Layout)
st.set_page_config(
    page_title="NPI Integration Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ฟังก์ชันดึงข้อมูลแบบปลอดภัยสูง ล้างข้อผิดพลาดจากช่องว่างและค่าว่างอัตโนมัติ
@st.cache_data(ttl=10)
def load_data_from_github():
    # บังคับให้อ่านแท็บแรกสุด (หรือเปลี่ยนเลข 0 เป็นชื่อแท็บ "Schedule2026" ได้ถ้าข้อมูลดิบไม่แสดง)
    df = pd.read_excel("data.xlsx", sheet_name=0, engine="openpyxl")
    
    # ล้างช่องว่างที่หัวคอลัมน์
    df.columns = df.columns.astype(str).str.strip()
    
    # ลบแถวหรือคอลัมน์ที่เป็นค่าว่างเปล่าจากการจองพื้นที่ตารางใน Excel ออกไปให้หมด
    df = df.dropna(how='all')
    
    return df

# โหลดข้อมูลเข้ามาเก็บไว้ในตัวแปรชื่อ df
try:
    df = load_data_from_github()
except Exception as e:
    st.error(f"❌ ระบบยังหาไฟล์ใน GitHub ไม่เจอ: {e}")
    st.stop()

# --- ค้นหาคอลัมน์ที่มีอยู่จริงในหน้างาน เพื่อป้องกัน Error คอลัมน์พิมพ์ไม่เหมือนกัน ---
available_cols = df.columns.tolist()

# ตรวจสอบหาคอลัมน์ Type
type_col = None
for col in ['Type', 'TYPE', 'type', 'Job Type']:
    if col in available_cols:
        type_col = col
        break
if not type_col:
    # ถ้าหาไม่เจอจริงๆ บังคับเอาคอลัมน์แรกที่มีข้อมูลที่ไม่ใช่ unnamed
    valid_cols = [c for c in available_cols if "Unnamed" not in c]
    type_col = valid_cols[0] if valid_cols else available_cols[0]

# ตรวจสอบหาคอลัมน์ Status
status_col = None
for col in ['Status', 'STATUS', 'status', 'งาน']:
    if col in available_cols:
        status_col = col
        break
if not status_col:
    valid_cols = [c for c in available_cols if "Unnamed" not in c and c != type_col]
    status_col = valid_cols[0] if valid_cols else available_cols[1]

# แปลงข้อมูลในคอลัมน์หลักเป็น String และล้างค่า nan ป้องกันการคำนวณพัง
df[type_col] = df[type_col].astype(str).str.strip()
df[status_col] = df[status_col].astype(str).str.strip()

# คัดกรองเอาบรรทัดที่คำว่า 'nan' หรือช่องว่างทิ้งไป
df = df[df[type_col].str.lower() != 'nan']
df = df[df[type_col] != '']
df = df[df[status_col].str.lower() != 'nan']
df = df[df[status_col] != '']

# --- SIDEBAR FILTERS (เมนูด้านซ้ายสำหรับกรองข้อมูล) ---
st.sidebar.header("🔍 คัดกรองข้อมูล Task")
all_types = sorted(df[type_col].unique().tolist())

if all_types:
    selected_types = st.sidebar.multiselect("เลือกประเภทงาน", options=all_types, default=all_types)
    filtered_df = df[df[type_col].isin(selected_types)]
else:
    st.sidebar.warning("⚠️ ไม่พบประเภทงานในตาราง Excel ของคุณ")
    filtered_df = df

# --- MAIN INTERFACE (ส่วนแสดงผลหลักตรงกลางหน้าเว็บ) ---
st.title("🚀 NPI Integration Task Dashboard")
st.write("ระบบดึงข้อมูลและประมวลผลความคืบหน้าของงานทีม NPI")
st.markdown("---")

# 3. ส่วนแสดง KPI Metrics (คำนวณแบบปลอดภัย)
total_tasks = len(filtered_df)
completed_tasks = len(filtered_df[filtered_df[status_col].str.lower() == 'closed'])
overdue_tasks = len(filtered_df[filtered_df[status_col].str.lower() == 'overdue'])

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
        type_counts = filtered_df[type_col].value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        fig_pie = px.pie(type_counts, values='Count', names='Type', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("ไม่มีข้อมูลสำหรับแสดงกราฟวงกลม")

with chart_col2:
    st.subheader("📊 สถานะงานแยกตามแผนก (Task Progress)")
    if total_tasks > 0:
        fig_bar = px.histogram(filtered_df, x=type_col, color=status_col, barmode='stack',
                               color_discrete_map={'closed': '#22c55e', 'on process': '#3b82f6', 'overdue': '#ef4444'})
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("ไม่มีข้อมูลสำหรับแสดงกราฟแท่ง")

st.markdown("---")

# 5. ส่วนแสดงตารางรายชื่องานที่ Overdue (งานที่เกินกำหนด)
st.subheader("🚨 รายชื่อ Task ที่เกินกำหนด (Overdue Task List)")
desired_cols = ['Type', 'Task', 'PRODUCT', 'Target Date', 'Target_Date', 'Product']
display_cols = [col for col in desired_cols if col in available_cols]

if not display_cols:
    display_cols = available_cols[:4]  # ดึง 4 คอลัมน์แรกมาแสดงกรณีชื่อไม่ตรงล็อก

if total_tasks > 0:
    overdue_list = filtered_df[filtered_df[status_col].str.lower() == 'overdue'][display_cols]
    if not overdue_list.empty:
        st.dataframe(overdue_list, use_container_width=True)
    else:
        st.success("🎉 ยอดเยี่ยมมาก! ไม่มีงานที่เกินกำหนด (Overdue) ในขณะนี้")
else:
    st.info("ไม่มีข้อมูลแสดงรายการงานล่าช้า")
