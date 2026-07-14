import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. ตั้งค่าหน้าแดชบอร์ด
st.set_page_config(
    page_title="NPI Fronted Web Application", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. เชื่อมต่อ Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# ฟังก์ชันดึงข้อมูล
def load_data():
    df = conn.read(worksheet="Schedule2026", ttl="5s")
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(subset=['Type', 'Status'], how='any')
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ ไม่สามารถเชื่อมต่อกับ Google Sheets ได้: {e}")
    st.info("กรุณาตรวจสอบการตั้งค่าลับ (Secrets) ใน Streamlit Cloud")
    st.stop()

df['Status_Clean'] = df['Status'].astype(str).str.strip().str.lower()
df.loc[df['Status_Clean'] == 'close', 'Status_Clean'] = 'closed'

tab_dashboard, tab_management = st.tabs(["📊 Interactive Dashboard", "📝 Input & Edit Tasks"])

# ==========================================
# TAB 1: INTERACTIVE DASHBOARD
# ==========================================
with tab_dashboard:
    st.sidebar.header("🔍 ตัวกรองข้อมูลแดชบอร์ด")
    all_months = sorted([m for m in df['Month'].unique().astype(str).tolist() if m != 'nan' and m != ''])
    selected_months = st.sidebar.multiselect("📅 เลือกเดือน (Month)", options=all_months, default=all_months)
    
    all_weeks = sorted([w for w in df['WW'].unique().astype(str).tolist() if w != 'nan' and w != ''])
    selected_weeks = st.sidebar.multiselect("📆 เลือกสัปดาห์ (WW)", options=all_weeks, default=all_weeks)
    
    all_pics = sorted([p for p in df['PIC'].unique().astype(str).tolist() if p != 'nan' and p != ''])
    selected_pics = st.sidebar.multiselect("👨‍💻 เลือกผู้รับผิดชอบ (PIC)", options=all_pics, default=all_pics)
    
    all_types = sorted([t for t in df['Type'].unique().astype(str).tolist() if t != 'nan' and t != ''])
    selected_types = st.sidebar.multiselect("📂 เลือกประเภทงาน (Type)", options=all_types, default=all_types)
    
    filtered_df = df[
        (df['Month'].astype(str).isin(selected_months)) &
        (df['WW'].astype(str).isin(selected_weeks)) &
        (df['PIC'].astype(str).isin(selected_pics)) &
        (df['Type'].astype(str).isin(selected_types))
    ]
    
    st.title("🚀 NPI Integration Fronted Web System")
    st.write("ระบบวิเคราะห์และกรอกข้อมูลงานทีม NPI แบบเบ็ดเสร็จ (Real-time Database)")
    st.markdown("---")
    
    total_tasks = len(filtered_df)
    completed_tasks = len(filtered_df[filtered_df['Status_Clean'] == 'closed'])
    on_process_tasks = len(filtered_df[filtered_df['Status_Clean'] == 'on process'])
    overdue_tasks = len(filtered_df[filtered_df['Status_Clean'] == 'overdue'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(label="📊 งานทั้งหมด", value=f"{total_tasks} Tasks")
    with col2: st.metric(label="✅ งานที่เสร็จแล้ว", value=f"{completed_tasks} Tasks")
    with col3: st.metric(label="⏳ กำลังดำเนินการ", value=f"{on_process_tasks} Tasks")
    with col4: st.metric(label="🚨 งานค้างเกินกำหนด", value=f"{overdue_tasks} Tasks")
        
    st.markdown("---")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("🍕 สัดส่วนประเภทงาน")
        if total_tasks > 0:
            type_counts = filtered_df['Type'].value_counts().reset_index()
            type_counts.columns = ['Type', 'Count']
            fig_pie = px.pie(type_counts, values='Count', names='Type', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with chart_col2:
        st.subheader("👨‍💻 ปริมาณงานรายบุคคล")
        if total_tasks > 0:
            fig_bar = px.histogram(filtered_df, y='PIC', color='Status', barmode='stack', orientation='h',
                                   color_discrete_map={'Closed': '#22c55e', 'Close': '#22c55e', 'On process': '#3b82f6', 'Overdue': '#ef4444'})
            st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# TAB 2: INPUT & EDIT TASKS (เพิ่มข้อมูลลงชีตจริง)
# ==========================================
with tab_management:
    st.header("📝 จัดการข้อมูลและบันทึกงาน")
    col_add, col_edit = st.columns([1, 1])
    
    with col_add:
        st.subheader("➕ บันทึกภาระงานใหม่")
        # ใช้ st.form หุ้มทั้งหมดเพื่อล็อกค่า PIC/ลูกค้า ไม่ให้เด้งตอนพิมพ์หรือเลือก
        with st.form("add_task_form", clear_on_submit=True):
            new_ww = st.text_input("สัปดาห์ (WW เช่น 29)")
            new_month = st.selectbox("เดือน (Month)", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
            new_type = st.selectbox("ประเภทงาน (Type)", ["NPI", "DFM Mold", "Part DFM", "RFQ", "MEETING", "PACKING", "OTHER"])
            new_task = st.text_area("ชื่องาน (TASK Detail)")
            new_cust = st.selectbox("ลูกค้า (Customer)", ["Enersys", "Numworks", "JRI", "FONROCHE", "AEG", "Maatel", "Leach", "Fairland", "Atlantic", "General"])
            new_pic = st.selectbox("ผู้รับผิดชอบ (PIC)", ["Bunnarak", "Tae", "Thiti", "Chutiporn", "Nattachai", "Somchai", "All"])
            new_target = st.date_input("กำหนดส่ง (Target Date)")
            new_status = st.selectbox("สถานะแรกเริ่ม (Status)", ["On process", "Closed", "Overdue"])
            
            submitted = st.form_submit_button("💾 กดบันทึกลง Google Sheets", type="primary")
            
            if submitted:
                if not new_ww or not new_task:
                    st.error("❌ กรุณากรอกข้อมูลให้ครบถ้วน")
                else:
                    with st.spinner("⏳ กำลังบันทึกข้อมูล..."):
                        try:
                            current_df = conn.read(worksheet="Schedule2026", ttl="0s")
                            new_row = pd.DataFrame([{
                                "WW": str(new_ww).strip(), "Month": new_month, "Type": new_type,
                                "TASK": new_task.strip(), "Customer": new_cust, "PIC": new_pic,
                                "Target Date": str(new_target), "Status": new_status
                            }])
                            # รักษาโครงสร้างคอลัมน์อื่น ๆ ในไฟล์จริง
                            for col in current_df.columns:
                                if col not in new_row.columns: new_row[col] = ""
                                
                            updated_df = pd.concat([current_df, new_row], ignore_index=True)
                            conn.update(worksheet="Schedule2026", data=updated_df)
                            st.success("✅ บันทึกข้อมูลงานใหม่เรียบร้อย!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"❌ ไม่สามารถเขียนข้อมูลได้: {err}")

    with col_edit:
        st.subheader("✏️ อัปเดตสถานะงานปัจจุบัน")
        pending_tasks = df[df['Status_Clean'].isin(['on process', 'overdue'])].copy()
        
        if not pending_tasks.empty:
            pending_tasks['Display'] = pending_tasks['TASK'].astype(str).str.slice(0, 30) + "... (" + pending_tasks['PIC'].astype(str) + ")"
            selected_task_display = st.selectbox("เลือกงานที่จะเปลี่ยนสถานะ", options=pending_tasks['Display'].unique())
            
            selected_idx = pending_tasks[pending_tasks['Display'] == selected_task_display].index[0]
            task_detail = df.loc[selected_idx]
            
            st.info(f"📍 **ชื่องาน:** {task_detail['TASK']}\n\nผู้รับผิดชอบ: **{task_detail['PIC']}**")
            new_status_val = st.selectbox("เปลี่ยนสถานะเป็น:", ["Closed", "On process", "Overdue"])
            
            if st.button("🔄 อัปเดตสถานะลงตาราง"):
                with st.spinner("⏳ กำลังอัปเดตสถานะ..."):
                    try:
                        save_df = conn.read(worksheet="Schedule2026", ttl="0s")
                        save_df.at[selected_idx, 'Status'] = new_status_val
                        conn.update(worksheet="Schedule2026", data=save_df)
                        st.success("🎉 เปลี่ยนสถานะงานในตารางสำเร็จ!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"❌ อัปเดตไม่สำเร็จ: {err}")
        else:
            st.success("😎 ทุกงานปิดหมดแล้วครับ!")
