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

# 2. เชื่อมต่อ Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# ฟังก์ชันดึงข้อมูลจาก Google Sheets
def load_data():
    # ดึงข้อมูลจากแท็บแรกสุดของไฟล์โดยอัตโนมัติ
    df = conn.read(ttl="5s")
    
    # ล้างช่องว่างหัวคอลัมน์
    df.columns = df.columns.astype(str).str.strip()
    
    # ลบแถวที่ไม่มีข้อมูลสำคัญออกเพื่อความเสถียร
    df = df.dropna(subset=['Type', 'Status'], how='any')
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ ไม่สามารถเชื่อมต่อกับ Google Sheets ได้: {e}")
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
    
    with col_add:
        st.subheader("➕ บันทึกภาระงานใหม่ (Add New Task)")
        
        # ป้องกันฟอร์มเด้ง: กำหนดตัวเลือกหลักไว้คงที่
        static_types = ["NPI", "DFM Mold", "Part DFM", "RFQ", "MEETING", "PACKING", "OTHER"]
        static_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        static_pics = ["Bunnarak", "Tae", "Thiti", "Chutiporn", "Nattachai", "Somchai", "All"]
        static_customers = ["Enersys", "Numworks", "JRI", "FONROCHE", "AEG", "Maatel", "Leach", "Fairland", "Atlantic", "General"]

        # สร้างกลไกนอกฟอร์มเพื่อป้องกันอาการเด้งกลับตอนกำลังพิมพ์หรือคลิกเลือกตัวเลือก
        new_ww = st.text_input("สัปดาห์ (WW เช่น 29)", placeholder="ระบุเลขสัปดาห์", key="input_ww")
        new_month = st.selectbox("เดือน (Month)", options=static_months, key="input_month")
        new_type = st.selectbox("ประเภทงาน (Type)", options=static_types, key="input_type")
        new_task = st.text_area("ชื่องาน (TASK Detail)", placeholder="กรอกรายละเอียดงาน", key="input_task")
        new_cust = st.selectbox("ลูกค้า (Customer)", options=static_customers, key="input_cust")
        new_pic = st.selectbox("ผู้รับผิดชอบ (PIC)", options=static_pics, key="input_pic")
        new_target = st.date_input("กำหนดส่ง (Target Date)", key="input_target")
        new_status = st.selectbox("สถานะแรกเริ่ม (Status)", ["On process", "Closed", "Overdue"], key="input_status")
        
        # ปุ่มกดบันทึกจริงแยกออกมาอิสระ
        if st.button("💾 บันทึกข้อมูลงานใหม่ลง Google Sheets", type="primary"):
            if not new_ww or not new_task:
                st.error("❌ กรุณากรอกเลขสัปดาห์ (WW) และรายละเอียดงาน (TASK) ด้วยครับ")
            else:
                with st.spinner("⏳ กำลังส่งข้อมูลไปยัง Google Sheets..."):
                    try:
                        # 1. ดึงข้อมูลปัจจุบันมาตั้งต้น
                        current_df = conn.read()
                        current_df.columns = current_df.columns.astype(str).str.strip()
                        
                        # 2. สร้างแถวใหม่ตามโครงสร้างคอลัมน์เดิมใน Google Sheets เป๊ะ ๆ
                        new_row_data = {
                            "WW": str(new_ww).strip(),
                            "Month": str(new_month),
                            "Type": str(new_type),
                            "TASK": str(new_task).strip(),
                            "Customer": str(new_cust),
                            "PIC": str(new_pic),
                            "Target Date": str(new_target),
                            "Status": str(new_status)
                        }
                        
                        # เติมคอลัมน์อื่น ๆ ในแผ่นงานให้เป็นค่าว่างเพื่อไม่ให้โครงสร้างตารางพัง
                        for col in current_df.columns:
                            if col not in new_row_data:
                                new_row_data[col] = ""
                                
                        new_row_df = pd.DataFrame([new_row_data])
                        
                        # 3. ต่อข้อมูลเข้าตารางหลัก
                        updated_df = pd.concat([current_df, new_row_df], ignore_index=True)
                        
                        # 4. สั่งเขียนทับกลับไปที่หน้าแรกสุดของ Google Sheets ตัวจริง
                        conn.update(data=updated_df)
                        
                        st.success("🎉 บันทึกข้อมูลงานใหม่ลง Google Sheets เรียบร้อยแล้วครับ!")
                        st.balloons()
                        st.cache_data.clear()
                    except Exception as err:
                        st.error(f"❌ เกิดข้อผิดพลาดขณะเขียนข้อมูล: {err}")
                        st.info("โปรดตรวจสอบว่าสิทธิ์การแชร์ลิงก์ Google Sheets ตั้งเป็น 'Anyone with link' -> 'Editor' แล้วหรือยัง")

    with col_edit:
        st.subheader("✏️ อัปเดตสถานะงานปัจจุบัน (Update Task Status)")
        pending_tasks = df[df['Status_Clean'].isin(['on process', 'overdue'])].copy()
        
        if not pending_tasks.empty:
            pending_tasks['Display'] = pending_tasks['TASK'].astype(str).str.slice(0, 30) + "... (" + pending_tasks['PIC'].astype(str) + ")"
            selected_task_display = st.selectbox("เลือกงานที่จะเปลี่ยนสถานะ", options=pending_tasks['Display'].unique(), key="edit_select_task")
            
            selected_idx = pending_tasks[pending_tasks['Display'] == selected_task_display].index[0]
            task_detail = df.loc[selected_idx]
            
            st.info(f"📍 **รายละเอียดงาน:** \n{task_detail['TASK']} \n\n(ผู้รับผิดชอบ: **{task_detail['PIC']}**)")
            new_status_val = st.selectbox("เปลี่ยนสถานะเป็น:", ["Closed", "On process", "Overdue"], index=0, key="edit_new_status")
            
            if st.button("🔄 อัปเดตสถานะลงตาราง"):
                with st.spinner("⏳ กำลังเปลี่ยนสถานะในตาราง..."):
                    try:
                        # ดึงข้อมูลล่าสุดมาแก้ไขเฉพาะแถว
                        save_df = conn.read()
                        save_df.columns = save_df.columns.astype(str).str.strip()
                        
                        save_df.at[selected_idx, 'Status'] = new_status_val
                        
                        conn.update(data=save_df)
                        st.success(f"🎉 อัปเดตงานเป็นสถานะ '{new_status_val}' สำเร็จ!")
                        st.cache_data.clear()
                    except Exception as err:
                        st.error(f"❌ ไม่สามารถอัปเดตสถานะได้: {err}")
        else:
            st.success("😎 ไม่มีงานคงค้างอยู่ในระบบให้แก้ไขแล้วครับ ทุกงานปิดหมดแล้ว!")
