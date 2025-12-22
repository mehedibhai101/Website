import streamlit as st
import pandas as pd
import os
import time
import hashlib
from datetime import datetime
import ast

# --- CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="Battle of Insights",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
PROJECTS_DIR = 'uploaded_projects'
PROFILES_DIR = 'user_profiles'
DATA_FILE = 'project_db_v2.csv'
USER_FILE = 'user_db_v2.csv'
ADMIN_PASS = "@Dm1n-OnE_22-Tree-E1eV@#" 

for folder in [PROJECTS_DIR, PROFILES_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

if 'current_page' not in st.session_state:
    st.session_state.current_page = "📊 Dashboard"

# --- DATABASE ENGINE ---
def init_db():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            "id", "username", "student_name", "category", "project_title", "description",
            "filename", "upload_time", "is_private", "instructor_grade", "instructor_review", 
            "likes", "comments"
        ])
        df.to_csv(DATA_FILE, index=False)
    if not os.path.exists(USER_FILE):
        df = pd.DataFrame(columns=["username", "password", "full_name", "role", "profile_pic"])
        df.to_csv(USER_FILE, index=False)

def load_data(file="project"):
    path = DATA_FILE if file == "project" else USER_FILE
    try:
        df = pd.read_csv(path)
        if file == "project":
            df['likes'] = df['likes'].apply(lambda x: eval(x) if pd.notna(x) and str(x).startswith('[') else [])
        return df
    except: return pd.DataFrame()

def save_data(df, file="project"):
    path = DATA_FILE if file == "project" else USER_FILE
    df.to_csv(path, index=False)

# --- AUTHENTICATION ---
def hash_pass(password): return hashlib.sha256(password.encode()).hexdigest()

def register_user(user, pw, name):
    df = load_data("user")
    if user in df['username'].values: return False, "Username taken!"
    new_user = {"username": user, "password": hash_pass(pw), "full_name": name, "role": "Student", "profile_pic": None}
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
    save_data(df, "user")
    return True, "Account created!"

def login_user(user, pw):
    df = load_data("user")
    match = df[(df['username'] == user) & (df['password'] == hash_pass(pw))]
    return match.iloc[0].to_dict() if not match.empty else None

# --- SIDEBAR NAV & LOGIN ---
def sidebar_nav():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=50)
        
        if 'user' in st.session_state:
            st.title("Arena Menu")
            u = st.session_state.user
            pic = u.get('profile_pic')
            has_custom_pic = pic and isinstance(pic, str) and os.path.exists(os.path.join(PROFILES_DIR, pic))
            
            col_img, col_del = st.columns([2, 1])
            with col_img:
                if has_custom_pic: st.image(os.path.join(PROFILES_DIR, pic), width=100)
                else:
                    icon = "https://cdn-icons-png.flaticon.com/512/1077/1077114.png" if u['role'] == "Instructor" else "https://cdn-icons-png.flaticon.com/512/1995/1995531.png"
                    st.image(icon, width=100)
            
            with col_del:
                if has_custom_pic:
                    if st.button("🗑️", help="Remove custom photo"):
                        os.remove(os.path.join(PROFILES_DIR, pic))
                        udf = load_data("user")
                        udf.loc[udf['username'] == u['username'], 'profile_pic'] = None
                        save_data(udf, "user")
                        st.session_state.user['profile_pic'] = None
                        st.session_state['uploader_key'] = st.session_state.get('uploader_key', 0) + 1
                        st.rerun()

            with st.expander("⚙️ Edit Profile"):
                new_name = st.text_input("Display Name", value=u['full_name'])
                if st.button("Update Name"):
                    udf = load_data("user")
                    udf.loc[udf['username'] == u['username'], 'full_name'] = new_name
                    save_data(udf, "user")
                    st.session_state.user['full_name'] = new_name
                    st.rerun()
                
                up_key = f"pic_up_{st.session_state.get('uploader_key', 0)}"
                up_pic = st.file_uploader("Upload Photo", type=['png','jpg','jpeg'], key=up_key)
                if up_pic:
                    fname = f"{u['username']}_{int(time.time())}.{up_pic.name.split('.')[-1]}"
                    with open(os.path.join(PROFILES_DIR, fname), "wb") as f: f.write(up_pic.getbuffer())
                    udf = load_data("user")
                    udf.loc[udf['username'] == u['username'], 'profile_pic'] = fname
                    save_data(udf, "user")
                    st.session_state.user['profile_pic'] = fname
                    st.rerun()

            st.write(f"### {u['full_name']}")
            st.caption(f"🛡️ Role: {u['role']}")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()
            
            st.markdown("---")
            
            if u['role'] == "Instructor":
                menu_items = [
                    ("📊 Dashboard", "📊 Dashboard"), 
                    ("⚔️ Battle Arena", "⚔️ Battle Arena"), 
                    ("🏆 Leaderboard", "🏆 Leaderboard"),
                    ("📋 Instructor Table", "📋 Instructor Table")
                ]
            else:
                menu_items = [
                    ("📊 Dashboard", "📊 Dashboard"), 
                    ("🚀 Submit Project", "🚀 Submit Project"), 
                    ("📂 My Projects", "📂 My Projects"), 
                    ("⚔️ Battle Arena", "⚔️ Battle Arena"), 
                    ("🏆 Leaderboard", "🏆 Leaderboard")
                ]

            for label, page_key in menu_items:
                btn_type = "primary" if st.session_state.current_page == page_key else "secondary"
                if st.button(label, use_container_width=True, key=f"nav_{page_key}", type=btn_type):
                    st.session_state.current_page = page_key
                    st.rerun()
        
        else:
            st.title("Enter the Arena")
            st.info("Sign in to submit projects and view the battlefield.")
            
            t_log, t_reg, t_inst = st.tabs(["🔑 Login", "📝 Register", "👨‍🏫 Instructor"])
            
            with t_log:
                u_in = st.text_input("Username")
                p_in = st.text_input("Password", type="password")
                if st.button("Sign In", use_container_width=True):
                    user_data = login_user(u_in, p_in)
                    if user_data:
                        st.session_state.user = user_data
                        st.rerun()
                    else: st.error("Wrong credentials")
            
            with t_reg:
                r_name = st.text_input("Full Name")
                r_u = st.text_input("New Username")
                r_p = st.text_input("New Password", type="password")
                if st.button("Create Account", use_container_width=True):
                    success, msg = register_user(r_u, r_p, r_name)
                    if success: st.success(msg)
                    else: st.error(msg)
            
            with t_inst:
                admin_key = st.text_input("Put Master Key", type="password")
                if st.button("Unlock Instructor Mode", use_container_width=True):
                    if admin_key == ADMIN_PASS:
                        st.session_state.user = {"username": "admin", "full_name": "Lead Instructor", "role": "Instructor", "profile_pic": None}
                        st.session_state.current_page = "📊 Dashboard"
                        st.rerun()
                    else:
                        st.error("Wrong Key")

# --- PAGES ---
def page_landing():
    st.markdown("""
    # ⚔️ Welcome to the Battle of Insights
    ### *Sharpen your data skills. Prepare for the Final Battle.*
    **The Arena is Open.** This platform is your dedicated training ground.
    ---
    **👈 Please use the sidebar to Login or Register.**
    """)

def page_dashboard():
    st.title("📊 Battlefield Intelligence")
    df = load_data()
    u = st.session_state.user
    st.caption(f"#### Welcome back, **{u['full_name']}**!")
    
    if df.empty:
        st.info("The battlefield is empty. Be the first to deploy!"); return

    total_projects = len(df)
    total_warriors = df['username'].nunique()
    global_avg = df['instructor_grade'].mean()
    global_avg_display = f"{global_avg:.1f}" if pd.notna(global_avg) else "0.0"
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛡️ Active Warriors", total_warriors)
    c2.metric("🚀 Total Deployments", total_projects)

    if u['role'] == "Student":
        my_projects = df[df['username'] == u['username']]
        my_avg = my_projects['instructor_grade'].mean()
        my_count = len(my_projects)
        delta_val = f"{my_avg - global_avg:.1f} vs Avg" if pd.notna(my_avg) and pd.notna(global_avg) else None
        c3.metric("My Average Score", f"{my_avg:.1f}" if pd.notna(my_avg) else "N/A", delta=delta_val)
        c4.metric("My Deployments", my_count)
    else:
        graded_count = df['instructor_grade'].count()
        pending_count = total_projects - graded_count
        c3.metric("Class Avg Score", global_avg_display)
        c4.metric("📝 Pending Reviews", pending_count)

    st.divider()
    col_chart1, col_chart2 = st.columns([1, 1])
    with col_chart1:
        st.subheader("📈 Deployment Velocity")
        df['date'] = pd.to_datetime(df['upload_time']).dt.date
        st.line_chart(df['date'].value_counts().sort_index())
    with col_chart2:
        st.subheader("🏷️ Category Distribution")
        st.bar_chart(df['category'].value_counts())

def page_submit():
    st.title("🚀 Submit Project")
    u = st.session_state.user
    with st.form("up_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        cat = col1.selectbox("Category", ["Excel", "Power BI", "Others"])
        title = col2.text_input("Project Title *")
        desc = st.text_area("Key Insights / Summary")
        file = st.file_uploader("Upload File", type=['csv','xlsx','pdf','png','jpg','jpeg'])
        private = st.checkbox("Instructor Only (Private Submission)")
        
        if st.form_submit_button("⚔️ Deploy Insight"):
            if title and file:
                fname = f"{int(time.time())}_{file.name}"
                with open(os.path.join(PROJECTS_DIR, fname), "wb") as f: f.write(file.getbuffer())
                df = load_data()
                new_row = {
                    "id": int(time.time()), "username": u['username'], "student_name": u['full_name'],
                    "category": cat, "project_title": title, "description": desc,
                    "filename": fname, "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "is_private": private, "instructor_grade": None, "instructor_review": "",
                    "likes": []
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("Deployed!")
                time.sleep(1)
                st.session_state.current_page = "📂 My Projects"
                st.rerun()

def page_my_projects():
    st.title("📂 My Projects")
    df = load_data()
    u = st.session_state.user
    my_df = df[df['username'] == u['username']].copy()
    if my_df.empty:
        st.info("No projects yet.")
        return
    for idx, row in my_df.iterrows():
        with st.container(border=True):
            st.subheader(row['project_title'])
            if pd.notna(row['instructor_grade']): st.success(f"Score: {row['instructor_grade']}/50")
            else: st.info("Score: Pending")
            with st.expander("Details"):
                st.write(row['description'])
                if row['instructor_review']: st.warning(f"Instructor: {row['instructor_review']}")

def page_arena():
    st.title("⚔️ Battle Arena")
    df = load_data()
    u = st.session_state.user
    for idx, row in df.iterrows():
        if row['is_private'] and (u['username'] != row['username'] and u['role'] != "Instructor"): continue
        with st.container(border=True):
            st.subheader(row['project_title'])
            st.caption(f"By: {row['student_name']} | {row['category']}")
            t1, t2, t3 = st.tabs(["📄 Details", "💬 Discussion", "👨‍🏫 Grading"])
            with t1: st.write(row['description'])
            with t2: st.write(f"❤️ {len(row['likes'])} Likes")
            with t3:
                if u['role'] == "Instructor":
                    g = st.number_input("Grade", 0, 50, int(row['instructor_grade']) if pd.notna(row['instructor_grade']) else 0, key=f"g_{row['id']}")
                    r = st.text_area("Review", row['instructor_review'], key=f"r_{row['id']}")
                    if st.button("Save", key=f"s_{row['id']}"):
                        df.at[idx, 'instructor_grade'] = g
                        df.at[idx, 'instructor_review'] = r
                        save_data(df); st.rerun()
                else: st.write(f"Grade: {row['instructor_grade'] if pd.notna(row['instructor_grade']) else 'Pending'}")

def page_leaderboard():
    st.title("🏆 Leaderboard")
    df = load_data()
    if df.empty: return
    ld = df.groupby('student_name')['instructor_grade'].mean().sort_values(ascending=False).reset_index()
    st.dataframe(ld, use_container_width=True)

def page_instructor_table():
    if st.session_state.user['role'] == "Instructor":
        st.title("📋 Master Control Panel")
        df = load_data()
        
        col_dummy, col_export = st.columns([6, 2])
        with col_export:
            st.download_button("📥 Export CSV", df.to_csv(index=False).encode('utf-8'), "battle_data.csv", "text/csv")

        display_cols = ["student_name", "category", "project_title", "upload_time", "instructor_grade", "is_private"]
        
        if df.empty:
            st.info("No data available.")
        else:
            table_df = df[display_cols].copy()
            # Replace empty grades with "Pending"
            table_df['instructor_grade'] = table_df['instructor_grade'].fillna("Pending")

            # Apply blue color styling to "Pending" text
            st.dataframe(
                table_df.style.map(lambda x: "color: #0068c9; font-weight: bold" if x == "Pending" else "", subset=['instructor_grade']),
                use_container_width=True,
                column_config={
                    "student_name": "Warrior Name",
                    "project_title": "Project Title",
                    "category": st.column_config.TextColumn("Category"),
                    "upload_time": st.column_config.DatetimeColumn("Deployed At", format="D MMM, HH:mm"),
                    "instructor_grade": st.column_config.Column("Grade", help="Blue 'Pending' indicates project needs marking."),
                    "is_private": st.column_config.CheckboxColumn("Private?")
                },
                hide_index=True
            )

# --- ROUTER ---
init_db()
sidebar_nav()

if 'user' in st.session_state:
    pg = st.session_state.current_page
    u_role = st.session_state.user['role']
    if pg == "📊 Dashboard": page_dashboard()
    elif pg == "🚀 Submit Project" and u_role != "Instructor": page_submit()
    elif pg == "📂 My Projects" and u_role != "Instructor": page_my_projects()
    elif pg == "⚔️ Battle Arena": page_arena()
    elif pg == "🏆 Leaderboard": page_leaderboard()
    elif pg == "📋 Instructor Table" and u_role == "Instructor": page_instructor_table()
    else:
        st.session_state.current_page = "📊 Dashboard"
        st.rerun()
else:
    page_landing()
