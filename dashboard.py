import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ตั้งค่าหน้าเว็บให้แสดงผลเต็มจอแบบกว้าง (Wide Layout)
st.set_page_config(
    page_title="NPI Integration Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ฟังก์ชันสำหรับดึงข้อมูลจากไฟล์ data.xlsx บน GitHub โดยตรง
@st.cache_data(ttl=10)  # ตั้งให้เช็คไฟล์ใหม่ไวขึ้นทุกๆ 10 วินาที
def load_data_from_github():
    # สั่งอ่านไฟล์ชื่อ data.xlsx ที่อยู่ข้างกันบน GitHub
    # sheet_name=0 หมายถึง บังคับให้อ่านแท็บแรกสุดจากซ้ายของไฟล์เสมอ ป้องกันปัญหาชื่อแท็บไม่ตรง
    df = pd.read_excel("data.xlsx", sheet_name=0, engine="openpyxl")
    
    # ล้างช่องว่างที่หัวคอลัมน์ออกทั้งหมด
    df.columns = df.columns.astype(str).str.strip()
    
    # คัดกรองและเคลียร์แถวที่ไม่มีข้อมูลสำคัญออก ป้องกันข้อมูลเพี้ยน
    if 'Type' in df.columns and 'Status' in df.columns:
        df['Type'] = df['Type'].astype(str).str.strip()
        df['Status'] = df['Status'].astype(str).str.strip()
        df = df[df['Type'] != 'nan']
        df = df[df['Status'] != 'nan']
    return df

# โหลดข้อมูลเข้ามาเก็บไว้ในตัวแปรชื่อ df
try:
    df = load_data_from_github()
except Exception as e:
    st.error(f"❌ ระบบยังหาไฟล์ใน GitHub ไม่เจอ: {e}")
    st.info("💡 รหัสตรวจสอบ: โปรดตรวจสอบว่าใน GitHub มีไฟล์ชื่อ data.xlsx อยู่คู่กับไฟล์ dashboard.py ในโฟลเดอร์หลักแล้ว")
    st.stop()

# --- ตรวจสอบโครงสร้างคอลัมน์ใน Excel ---
# หาก Excel ของน้องใช้ตัวพิมพ์เล็กหรือพิมพ์ใหญ่ โค้ดส่วนนี้จะปรับให้เข้ากับหน้างานอัตโนมัติ
available_cols = df.columns.tolist()
type_col = 'Type' if 'Type' in available_cols else ('TYPE' if 'TYPE' in available_cols else available_cols[0])
status_col = 'Status' if 'Status' in available_cols else ('STATUS' if 'STATUS' in available_cols else available_cols[1])


# --- SIDEBAR FILTERS (เมนูด้านซ้ายสำหรับกรองข้อมูล) ---
st.sidebar.header("🔍 คัดกรองข้อมูล Task")
all_types = sorted(df[type_col].unique().tolist())
selected_types = st.sidebar.multiselect("เลือกประเภทงาน", options=all_types, default=all_types)

# กรองข้อมูลตามที่ User เลือก
filtered_df = df[df[type_col].isin(selected_types)]


# --- MAIN INTERFACE (ส่วนแสดงผลหลักตรงกลางหน้าเว็บ) ---
st.title("🚀 NPI Integration Task Dashboard")
st.write("ระบบดึงข้อมูลและประมวลผลความคืบหน้าของงานทีม NPI (GitHub Local Storage)")
st.markdown("---")

# 3. ส่วนแสดง KPI Metrics (ตัวเลขสำคัญด้านบนสุด)
total_tasks = len(filtered_df)
completed_tasks = len(filtered_df[filtered_df[status_col].str.lower() == 'closed'])
overdue_tasks = len(filtered_df[filtered_df[status_col].str.lower() == 'overdue'])

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
                               color_discrete_map={'Closed': '#22c55e', 'On process': '#3b82f6', 'Overdue': '#ef4444'})
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("ไม่มีข้อมูลสำหรับแสดงกราฟแท่ง")

st.markdown("---")

# 5. ส่วนแสดงตารางรายชื่องานที่ Overdue (งานที่เกินกำหนด)
st.subheader("🚨 รายชื่อ Task ที่เกินกำหนด (Overdue Task List)")
desired_cols = ['Type', 'Task', 'PRODUCT', 'Target Date', 'Type', 'Task', 'PRODUCT', 'Target Date'.lower()]
display_cols = [col for col in desired_cols if col in available_cols]

if display_cols:
    overdue_list = filtered_df[filtered_df[status_col].str.lower() == 'overdue'][display_cols]
    if not overdue_list.empty:
        st.dataframe(overdue_list, use_container_width=True)
    else:
        st.success("🎉 ยอดเยี่ยมมาก! ไม่มีงานที่เกินกำหนด (Overdue) ในขณะนี้")
