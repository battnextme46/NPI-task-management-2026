import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. ตั้งค่าหน้าแดชบอร์ดกว้างแบบ Responsive
st.set_page_config(
    page_title="NPI Fronted Web Application", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ทำการเชื่อมต่อ Google Sheets ผ่าน Streamlit Connector
conn = st.connection("gsheets", type=GSheetsConnection)

# ฟังก์ชันดึงข้อมูลจาก Google Sheets
def load_data():
    # ดึงข้อมูลจากแท็บ Schedule2026
    df = conn.read(worksheet="Schedule2026", ttl="5s") # อัปเดตข้อมูลทุกๆ 5 วินาทีเมื่อเปลี่ยนหน้า
    
    # ล้างช่องว่างหัวคอลัมน์
    df.columns = df.columns.astype(str).str.strip()
    
    # ลบแถวที่ว่างทั้งหมดออกเพื่อไม่ให้เปลืองหน่วยความจำ
    df = df.dropna(subset=['Type', 'Status'], how='any')
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ ไม่สามารถเชื่อมต่อกับ Google Sheets ได้: {e}")
    st.info("กรุณาตรวจสอบการตั้งค่า Spreadsheet ID ในหน้า Secrets")
    st.stop()

# เคลียร์ค่า nan ในฐานข้อมูลเบื้องต้น
df['Status_Clean'] = df['Status'].astype(str).str.strip().str.lower()
df.loc[df['Status_Clean'] == 'close', 'Status_Clean'] = 'closed'

# สร้างหน้าต่างแท็บเมนูหลักบนหน้าเว็บแอป
tab_dashboard, tab_management = st.tabs(["📊 Interactive Dashboard", "📝 Input & Edit Tasks"])

# ==========================================
# TAB 1: INTERACTIVE DASHBOARD (แสดงผลแดชบอร์ด)
# ==========================================
with tab_dashboard:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🔍 ตัวกรองข้อมูลแดชบอร์ด")
    
    all_months = sorted([m for m in df['Month'].unique().astype(str).tolist() if m != 'nan' and m != ''])
    selected_months = st.sidebar.multiselect("📅 เลือกเดือน (Month)", options=all_months, default=all_months)
    
    all_weeks = sorted([w for w in df['WW'].unique().astype(str).tolist() if w != 'nan' and w != ''])
    selected_weeks = st.sidebar.multiselect("📆 เลือกสัปดาห์ (WW)", options=all_weeks, default=all_weeks)
    
    all_pics = sorted([p for p in df['PIC'].unique().astype(str).tolist() if p != 'nan' and p != ''])
    selected_pics = st.sidebar.multiselect("👨‍💻 เลือกผู้รับผิดชอบ (PIC)", options=all_pics, default=all_pics)
    
    all_types = sorted([t for t in df['Type'].unique().astype(str).tolist() if t != 'nan' and t != ''])
    selected_types = st.sidebar.multiselect("📂 เลือกประเภทงาน (Type)", options=all_types, default=all_types)
    
    # ประมวลผลกรองข้อมูลหลัก
    filtered_df = df[
        (df['Month'].astype(str).isin(selected_months)) &
        (df['WW'].astype(str).isin(selected_weeks)) &
        (df['PIC'].astype(str).isin(selected_pics)) &
        (df['Type'].astype(str).isin(selected_types))
    ]
    
    st.title("🚀 NPI Integration Fronted Web System")
    st.write("ระบบวิเคราะห์และกรอกข้อมูลงานทีม NPI แบบเบ็ดเสร็จ (Real-time Database)")
    st.markdown("---")
    
    # ส่วนแสดงยอด KPI
    total_tasks = len(filtered_df)
    completed_tasks = len(filtered_df[filtered_df['Status_Clean'] == 'closed'])
    on_process_tasks = len(filtered_df[filtered_df['Status_Clean'] == 'on process'])
    overdue_tasks = len(filtered_df[filtered_df['Status_Clean'] == 'overdue'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="📊 งานทั้งหมดในช่วงที่เลือก", value=f"{total_tasks} Tasks")
    with col2:
        st.metric(label="✅ งานที่เสร็จแล้ว (Closed)", value=f"{completed_tasks} Tasks")
    with col3:
        st.metric(label="⏳ กำลังดำเนินการ (On Process)", value=f"{on_process_tasks} Tasks")
    with col4:
        st.metric(label="🚨 งานค้างเกินกำหนด (Overdue)", value=f"{overdue_tasks} Tasks")
        
    st.markdown("---")
    
    # ส่วนกางแผนภูมิเวทีวิเคราะห์
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("🍕 สัดส่วนประเภทงาน (Task Type)")
        if total_tasks > 0:
            type_counts = filtered_df['Type'].value_counts().reset_index()
            type_counts.columns = ['Type', 'Count']
            fig_pie = px.pie(type_counts, values='Count', names='Type', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("⚠️ ไม่มีข้อมูลสัดส่วนงาน")
            
    with chart_col2:
        st.subheader("👨‍💻 ปริมาณงานรายบุคคล (PIC Progress)")
        if total_tasks > 0:
            fig_bar = px.histogram(filtered_df, y='PIC', color='Status', barmode='stack', orientation='h',
                                   color_discrete_map={'Closed': '#22c55e', 'Close': '#22c55e', 'On process': '#3b82f6', 'Overdue': '#ef4444'})
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("⚠️ ไม่มีข้อมูลผลงานราย PIC")

    st.markdown("---")
    
    # แสดงตาราง Overdue รายละเอียดด้านล่าง
    st.subheader("🚨 รายการงานเกินกำหนด (Overdue Task List)")
    overdue_df = filtered_df[filtered_df['Status_Clean'] == 'overdue']
    if not overdue_df.empty:
        st.dataframe(overdue_df[['Month', 'WW', 'Type', 'TASK', 'Customer', 'PIC', 'Target Date']], use_container_width=True)
    else:
        st.success("🎉 สุดยอด! ไม่มีงานค้าง Overdue ในช่วงเวลานี้")


# ==========================================
# TAB 2: INPUT & EDIT TASKS (ฟอร์มบันทึกข้อมูล)
# ==========================================
with tab_management:
    st.header("📝 จัดการข้อมูลและบันทึกงาน")
    st.write("น้องสามารถเพิ่มข้อมูลแถวใหม่ หรือแก้ไขสถานะงานปัจจุบันจากตรงนี้ได้เลย")
    
    col_add, col_edit = st.columns([1, 1])
    
    # ------------------ ส่วนเพิ่มงานใหม่ (Add Task) ------------------
    with col_add:
        st.subheader("➕ บันทึกภาระงานใหม่ (Add New Task)")
        with st.form("add_task_form", clear_on_submit=True):
            new_ww = st.text_input("สัปดาห์ (WW เช่น 29)", placeholder="ระบุเลขสัปดาห์")
            new_month = st.selectbox("เดือน (Month)", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
            
            # ดึงประเภทและลูกค้าเดิมที่มีในฐานข้อมูลมาเป็นตัวเลือก
            type_options = list(df['Type'].dropna().unique())
            customer_options = list(df['Customer'].dropna().unique())
            pic_options = list(df['PIC'].dropna().unique())
            
            new_type = st.selectbox("ประเภทงาน (Type)", options=type_options)
            new_task = st.text_area("ชื่องาน (TASK Detail)", placeholder="กรอกรายละเอียดงาน")
            new_cust = st.selectbox("ลูกค้า (Customer)", options=customer_options)
            new_pic = st.selectbox("ผู้รับผิดชอบ (PIC)", options=pic_options)
            new_target = st.date_input("กำหนดส่ง (Target Date)")
            new_status = st.selectbox("สถานะแรกเริ่ม (Status)", ["On process", "Closed", "Overdue"])
            
            submitted = st.form_submit_with_button("💾 กดบันทึกลง Google Sheets")
            
            if submitted:
                if not new_ww or not new_task:
                    st.error("❌ กรุณากรอกเลขสัปดาห์ (WW) และรายละเอียดงาน (TASK) ด้วยครับ")
                else:
                    # สร้างตาราง Row ใหม่เตรียมนำไปต่อท้าย
                    new_row = pd.DataFrame([{
                        "WW": str(new_ww).strip(),
                        "Month": new_month,
                        "Type": new_type,
                        "TASK": new_task.strip(),
                        "Customer": new_cust,
                        "PIC": new_pic,
                        "Target Date": str(new_target),
                        "Status": new_status,
                    }])
                    
                    # นำข้อมูลใหม่ไปต่อท้ายก้อนเก่า
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    # ลบคอลัมน์คำนวณเบื้องต้นที่สร้างขึ้นชั่วคราวออกก่อนเซฟ
                    if 'Status_Clean' in updated_df.columns:
                        updated_df = updated_df.drop(columns=['Status_Clean'])
                        
                    # สั่งเขียนทับลง Google Sheets
                    conn.update(worksheet="Schedule2026", data=updated_df)
                    st.success("✅ บันทึกข้อมูลงานใหม่ลง Google Sheets เรียบร้อย! กรุณารีเฟรชเพื่ออัปเดต")
                    st.cache_data.clear() # สั่งล้าง Cache เพื่อดึงค่าใหม่
                    
    # ------------------ ส่วนแก้ไขสถานะงานที่มีอยู่แล้ว (Update Task Status) ------------------
    with col_edit:
        st.subheader("✏️ อัปเดตสถานะงานปัจจุบัน (Update Status)")
        
        # ค้นหางานที่ยังไม่เสร็จ (On process / Overdue) เพื่อเอามาแสดงให้เลือกอัปเดต
        pending_tasks = df[df['Status_Clean'].isin(['on process', 'overdue'])]
        
        if not pending_tasks.empty:
            # สร้างตัวเลือกแสดงในรูปแบบ "ชื่องาน - โดย PIC"
            pending_tasks['Display'] = pending_tasks['TASK'].str[:30] + "..." + " (" + pending_tasks['PIC'] + ")"
            selected_task_display = st.selectbox("เลือกงานที่จะอัปเดตสถานะ", options=pending_tasks['Display'].unique())
            
            # ค้นหาแถวที่ตรงกับที่ผู้ใช้เลือกในฐานข้อมูลหลัก
            selected_idx = pending_tasks[pending_tasks['Display'] == selected_task_display].index[0]
            task_detail = df.loc[selected_idx]
            
            st.info(f"📍 **รายละเอียดงานที่เลือก:** \n{task_detail['TASK']} \n\n(รับผิดชอบโดย: **{task_detail['PIC']}**)")
            
            # มีกล่อง Dropdown ให้เปลี่ยนสถานะ
            new_status_val = st.selectbox("เปลี่ยนสถานะเป็น:", ["Closed", "On process", "Overdue"], index=0)
            
            # วันที่เสร็จงานจริง
            actual_date = st.date_input("วันที่จบงานจริง (หากต้องการระบุ)")
            
            if st.button("🔄 อัปเดตสถานะ"):
                # เปลี่ยนค่าในตารางหลัก
                df.at[selected_idx, 'Status'] = new_status_val
                
                # ลบคอลัมน์คำนวณเบื้องต้นออกก่อนเซฟทับ
                save_df = df.copy()
                if 'Status_Clean' in save_df.columns:
                    save_df = save_df.drop(columns=['Status_Clean'])
                if 'Display' in save_df.columns:
                    save_df = save_df.drop(columns=['Display'])
                    
                # ส่งอัปเดตทับลง Google Sheets
                conn.update(worksheet="Schedule2026", data=save_df)
                st.success(f"🎉 อัปเดตงานเป็นสถานะ '{new_status_val}' เรียบร้อยแล้วบน Google Sheets!")
                st.cache_data.clear() # ล้าง Cache
        else:
            st.success("😎 ไม่มีงานคงค้างอยู่ในระบบให้แก้ไขแล้วครับ ทุกงานปิดหมดแล้ว!")
