# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import xlsxwriter
import pandas as pd
import hashlib
import random
from datetime import datetime

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect('LLHH.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, dept TEXT, type TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, dept TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, stage TEXT, grp TEXT, code TEXT UNIQUE, dept TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, teacher_id INTEGER, course_name TEXT, total_hours INTEGER, dept TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY, student_id INTEGER, course_id INTEGER, date TEXT,
                  hours_absent INTEGER, type TEXT, dept TEXT,
                  UNIQUE(student_id, course_id, date, type))''')
    
    p = hashlib.sha256("Garmian@2026".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO admins (email, password, dept, type) VALUES (?,?,?,?)",
              ('admin@gpu.edu.iq', p, 'ڕاگرایەتی', 'سوپەر ئەدمین'))
    conn.commit()
    conn.close()

def execute_query(q, p=(), fetch_all=False, fetch_one=False, commit=False):
    conn = sqlite3.connect('LLHH.db')
    c = conn.cursor()
    try:
        c.execute(q, p)
        if commit: conn.commit(); return True
        if fetch_one: return c.fetchone()
        if fetch_all: return c.fetchall()
    finally: conn.close()

# ================= UI & STYLE =================
def apply_theme():
    st.markdown("""
    <style>
    html, body, [data-testid="stSidebar"] {direction: rtl; text-align: right;}
    .stButton>button {background:#40E0D0; color:white; border-radius:10px; width: 100%; font-weight: bold;}
    .dev {position:fixed; bottom:10px; left:10px; color:gray; font-size: 10px;}
    </style>
    """, unsafe_allow_html=True)

# ================= PANELS =================

def super_admin_panel():
    st.header("بەشی ڕاگرایەتی")
    with st.form("new_dept"):
        e = st.text_input("ئیمەیڵی نوێ بۆ بەش")
        p = st.text_input("پاسۆرد", type="password")
        d = st.selectbox("ناوی بەش", ["ئەندازیاری کارەبا و کۆمپیوتەر", "شیکاری نەخۆشییەکان", "تەکنیکی پەرستاری", "تەکنەلۆجیای زانیاری", "دیزاینی ناوەوە", "کارگێڕی کار", "تەکنیکی ڤێتەنەری", "ڕووپێوی", "پەرستاری", "کارەبا"])
        if st.form_submit_button("دروستکردنی ئەکاونت"):
            hp = hashlib.sha256(p.encode()).hexdigest()
            execute_query("INSERT INTO admins (email, password, dept, type) VALUES (?,?,?,?)", (e, hp, d, "ئەدمینی بەش"), commit=True)
            st.success(f"ئەکاونت بۆ بەشی {d} دروستکرا")

def dept_admin_panel():
    dept = st.session_state.dept
    st.title(f"بەڕێوەبردنی بەشی {dept}")
    
    # خاڵی هەشتەم: دیاریکردنی جۆری خوێندن
    edu_type = st.sidebar.radio("جۆری خوێندن:", ["کۆلێج (4 ساڵ)", "پەیمانگا (2 ساڵ)"])
    stages = ["1", "2", "3", "4"] if "کۆلێج" in edu_type else ["1", "2"]
    
    menu = st.sidebar.selectbox("مەنیو", ["خوێندکاران", "مامۆستایان", "ڕاپۆرتی گشتی"])

    # خاڵی یەکەم و حەوتەم: خوێندکار و گروپ و ئیدیت
    if menu == "خوێندکاران":
        st.subheader("🔍 گەڕان و سڕینەوەی خوێندکار")
        search_q = st.text_input("ناو یان کۆدی خوێندکار بنووسە بۆ گەڕان:")
        
        if search_q:
            # گەڕان بەدوای ناو یان کۆد لەناو ئەو بەشەی (dept) کە ئەدمینەکەی تێدایە
            s_results = execute_query("SELECT id, name, stage, grp, code FROM students WHERE (name LIKE ? OR code LIKE ?) AND dept=?", 
                                     (f"%{search_q}%", f"%{search_q}%", dept), fetch_all=True)
            
            for sid, sname, sstage, sgrp, scode in s_results:
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f" {sname} - {scode}")
                col2.write(f"قۆناغی {sstage}")
                if col3.button("🗑️ سڕینەوە", key=f"del_search_{sid}"):
                    execute_query("DELETE FROM students WHERE id=?", (sid,), commit=True)
                    st.success(f"خوێندکار {sname} سڕایەوە")
                    st.rerun()

        st.subheader("تۆمارکردنی خوێندکار")
        c1, c2, c3 = st.columns(3)
        s_name = c1.text_input("ناوی سیانی")
        s_stage = c2.selectbox("قۆناغ", stages)
        s_grp = c3.selectbox("گروپی پراکتیکی", ["A", "B", "C", "D"])
        
        if st.button("پاشەکەوتکردن"):
            code = f"S{random.randint(1000, 9999)}"
            execute_query("INSERT INTO students (name, stage, grp, code, dept) VALUES (?,?,?,?,?)", (s_name, s_stage, s_grp, code, dept), commit=True)
            st.success(f"خوێندکار زیادکرا: {code}")

        st.markdown("---")
        # خاڵی شەشەم: ڕیزبەندی ئەلف و بێ
        st.subheader("لیستی خوێندکاران )")
        st_data = execute_query("SELECT id, name, stage, grp FROM students WHERE dept=? ORDER BY name COLLATE NOCASE", (dept,), fetch_all=True)
        for sid, name, stage, grp in st_data:
            with st.expander(f"{name} - قۆناغی {stage}"):
                new_n = st.text_input("ناو", value=name, key=f"n{sid}")
                new_g = st.selectbox("گروپ", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(grp), key=f"g{sid}")
                if st.button("گۆڕانکاری", key=f"u{sid}"):
                    execute_query("UPDATE students SET name=?, grp=? WHERE id=?", (new_n, new_g, sid), commit=True)
                    st.rerun()

    # خاڵی سێیەم: کاتژمێری وانە لە سمستەر
    elif menu == "مامۆستایان":
        st.subheader("تۆمارکردنی مامۆستا و وانە")
        t_name = st.text_input("ناوی مامۆستا")
        c_name = st.text_input("ناوی وانە")
        t_hours = st.number_input("کۆی کاتژمێری وانە لە سمستەردا", min_value=1, value=30)
        if st.button("تۆمارکردن"):
            t_code = f"T{random.randint(1000, 9999)}"
            execute_query("INSERT INTO teachers (name, code, dept) VALUES (?,?,?)", (t_name, t_code, dept), commit=True)
            tid = execute_query("SELECT id FROM teachers WHERE code=?", (t_code,), fetch_one=True)[0]
            execute_query("INSERT INTO courses (teacher_id, course_name, total_hours, dept) VALUES (?,?,?,?)", (tid, c_name, t_hours, dept), commit=True)
            st.info(f"کۆدی مامۆستا: {t_code}")
            st.subheader("لیستی مامۆستایان و کۆدی لۆگین")
        
        # یەکەم هەنگاو: هێنانەوەی داتاکان لە داتابەیس
        t_list = execute_query("""SELECT t.name, c.course_name, c.total_hours, t.code 
                                FROM teachers t 
                                JOIN courses c ON t.id = c.teacher_id 
                                WHERE t.dept=? 
                                ORDER BY t.name COLLATE NOCASE""", (dept,), fetch_all=True)
        
        # دووەم هەنگاو: پشکنین بۆ ئەوەی بزانین داتا هەیە یان نا
        if t_list:
            df_teachers = pd.DataFrame(t_list, columns=["ناوی مامۆستا", "ناوی وانە", "کۆی کاتژمێری وانە", "کۆدی لۆگین"])
            st.table(df_teachers)
        else:
            st.info("هیچ مامۆستایەک تۆمار نەکراوە.")


    # خاڵی دووەم و پێنجەم: ڕاپۆرتی گشتی و ڕێژەی غیابات
    elif menu == "ڕاپۆرتی گشتی":
        st.subheader("ڕاپۆرتی غیاباتی قۆناغەکان")
        sel_stage = st.selectbox("قۆناغ هەڵبژێرە:", stages)
        
        students = execute_query("SELECT id, name, grp FROM students WHERE stage=? AND dept=? ORDER BY name COLLATE NOCASE", (sel_stage, dept), fetch_all=True)
        courses = execute_query("SELECT id, course_name, total_hours FROM courses WHERE dept=?", (dept,), fetch_all=True)
        
        if students and courses:
            rep_list = []
            for sid, sname, sgrp in students:
                row = {"ناو": sname, "گروپ": sgrp}
                for cid, cname, thours in courses:
                    abs_sum = execute_query("SELECT SUM(hours_absent) FROM attendance WHERE student_id=? AND course_id=?", (sid, cid), fetch_one=True)[0] or 0
                    percent = (abs_sum / thours) * 100
                    row[cname] = f"{percent:.1f}%"
                rep_list.append(row)
            
            df_report = pd.DataFrame(rep_list)
            st.dataframe(df_report.style)

        elif menu == "ڕاپۆرتی گشتی":
            st.subheader("دابەزاندنی زانیارییەکان بۆ ئێکسڵ")
        
        # هێنانەوەی داتاکان لە داتابەیس
        data = execute_query("SELECT * FROM students WHERE dept=?", (dept,), fetch_all=True)
        
        if data:
            df = pd.DataFrame(data)
            
            # بەکارهێنانی io بۆ ئەوەی پێویستت بە خەزنکردن نەبێت لەسەر سێرڤەر
            import io
            buffer = io.BytesIO()
            
            # لێرەدا engine دیاری ناکەین بۆ ئەوەی پایتۆن خۆی باشترین هەڵبژێرێت
            with pd.ExcelWriter(buffer) as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            st.download_button(
                label="📥 داگرتنی فایلی ئێکسڵ",
                data=buffer.getvalue(),
                file_name=f"report_{dept}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("هیچ داتایەک نییە بۆ ناردن.")

            
            
        



def teacher_panel():
    tid, tname, dept = st.session_state.t_id, st.session_state.t_name, st.session_state.dept
    course = execute_query("SELECT id, course_name FROM courses WHERE teacher_id=?", (tid,), fetch_one=True)
    if not course: st.warning("هیچ وانەیەکت بۆ دیارینەکراوە"); return
    
    cid, cname = course
    st.subheader(f"مامۆستا: {tname} | وانە: {cname}")

    # خاڵی چوارەم: کاتژمێر، بەروار، جۆری وانە
    c1, c2, c3 = st.columns(3)
    k_hours = c1.number_input("کاتژمێری وانە (ئەمڕۆ)", min_value=1, max_value=6, value=2)
    bwar = c2.date_input("بەروار", datetime.now())
    jory_wana = c3.radio("جۆری وانە:", ["تیۆری", "پراکتیکی"], horizontal=True)

    if jory_wana == "پراکتیکی":
        grp_filter = st.selectbox("گروپ هەڵبژێرە:", ["A", "B", "C", "D"])
        st_data = execute_query("SELECT id, name FROM students WHERE dept=? AND grp=? ORDER BY name COLLATE NOCASE", (dept, grp_filter), fetch_all=True)
    else:
        st_data = execute_query("SELECT id, name FROM students WHERE dept=? ORDER BY name COLLATE NOCASE", (dept,), fetch_all=True)

    if st_data:
        results = {}
        for sid, name in st_data:
            col1, col2 = st.columns([3, 1])
            col1.write(name)
            status = col2.radio("حاڵەت", ["ئامادە", "نەهاتوو"], key=f"s{sid}", horizontal=True)
            results[sid] = k_hours if status == "نەهاتوو" else 0
        
        if st.button("ناردنی ئامادەبوون"):
            for sid, h in results.items():
                execute_query("INSERT OR REPLACE INTO attendance (student_id, course_id, date, hours_absent, type, dept) VALUES (?,?,?,?,?,?)",
                              (sid, cid, str(bwar), h, jory_wana, dept), commit=True)
            st.balloons(); st.success("تۆمارکرا")



# ================= MAIN =================
def main():
    st.set_page_config(page_title="Garmian Polytechnic", layout="wide")
    init_db()
    apply_theme()
    st.markdown("""
        <div style='text-align: center; margin-top: -50px;'>
            <h1 style='color: black; font-size: 45px; margin-bottom: 0;'>زانکۆی پۆلیتەکنیکی گەرمیان</h1>
            <h2 style='color: #40E0D0; font-size: 35px; margin-top: 0;'>سیستەمی تۆمارکردنی ئامادەبوون</h2>
        </div>
        <hr style='border: 1px solid #40E0D0;'>
    """, unsafe_allow_html=True)


    



    if 'logged_in' not in st.session_state:
        col1, col2 = st.sidebar.columns(2)
        mode = st.sidebar.radio("چوونەژوورەوە وەک:", ["ئەدمین", "مامۆستا"])
        u = st.sidebar.text_input("ئیمەیڵ یان کۆد")
        p = st.sidebar.text_input("پاسۆرد", type="password")
        if st.sidebar.button("داخڵبوون"):
            if mode == "ئەدمین":
                hp = hashlib.sha256(p.encode()).hexdigest()
                res = execute_query("SELECT dept, type FROM admins WHERE email=? AND password=?", (u, hp), fetch_one=True)
                if res:
                    st.session_state.logged_in = True
                    st.session_state.dept, st.session_state.role = res[0], res[1]
                    st.rerun()
            else:
                res = execute_query("SELECT id, name, dept FROM teachers WHERE code=?", (u,), fetch_one=True)
                if res:
                    st.session_state.logged_in = True
                    st.session_state.t_id, st.session_state.t_name, st.session_state.dept = res[0], res[1], res[2]
                    st.session_state.role = "مامۆستا"
                    st.rerun()
    else:
        if st.sidebar.button("چوونەدەرەوە"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        
        if st.session_state.role == "سوپەر ئەدمین": super_admin_panel()
        elif st.session_state.role == "ئەدمینی بەش": dept_admin_panel()
        else: teacher_panel()

    st.markdown("<div class='dev'>گەشەپێدەر: ئەندازیار لەنیا حازم کەریم</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
