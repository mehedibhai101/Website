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
NOTIF_FILE = 'notification_db.csv' # <--- NEW DB FILE
ADMIN_PASS = "@Dm1n-OnE_22-Tree-E1eV@#" 

for folder in [PROJECTS_DIR, PROFILES_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

if 'current_page' not in st.session_state:
    st.session_state.current_page = "📊 Dashboard"

# --- DATABASE ENGINE ---
def init_db():
    # Projects DB
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            "id", "username", "student_name", "category", "project_title", "description",
            "filename", "upload_time", "is_private", "instructor_grade", "instructor_review", 
            "likes", "comments"])
        df.to_csv(DATA_FILE, index=False)
    # Users DB
    if not os.path.exists(USER_FILE):
        df = pd.DataFrame(columns=["username", "password", "full_name", "role", "profile_pic"])
        df.to_csv(USER_FILE, index=False)
    # Notifications DB (NEW)
    if not os.path.exists(NOTIF_FILE):
        df = pd.DataFrame(columns=["recipient", "message", "timestamp", "is_read"])
        df.to_csv(NOTIF_FILE, index=False)

def load_data(file="project"):
    if file == "project": path = DATA_FILE
    elif file == "user": path = USER_FILE
    else: path = NOTIF_FILE # Handle notification load
    
    try:
        df = pd.read_csv(path)
        if file == "project":
            df['likes'] = df['likes'].apply(lambda x: eval(x) if pd.notna(x) and str(x).startswith('[') else [])
        return df
    except: return pd.DataFrame()

def save_data(df, file="project"):
    if file == "project": path = DATA_FILE
    elif file == "user": path = USER_FILE
    else: path = NOTIF_FILE
    df.to_csv(path, index=False)

# --- NOTIFICATION LOGIC (NEW) ---
def send_notification(recipient_username, message):
    """Adds a new notification to the database."""
    ndf = load_data("notification")
    new_notif = {
        "recipient": recipient_username,
        "message": message,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "is_read": False
    }
    ndf = pd.concat([ndf, pd.DataFrame([new_notif])], ignore_index=True)
    save_data(ndf, "notification")

def get_my_notifications(username):
    """Fetches unread notifications for the sidebar."""
    ndf = load_data("notification")
    if ndf.empty: return []
    # Filter for this user and unread status
    my_notifs = ndf[(ndf['recipient'] == username) & (ndf['is_read'] == False)]
    return my_notifs.to_dict('records')

def clear_notifications(username):
    """Marks all notifications as read for the user."""
    ndf = load_data("notification")
    if not ndf.empty:
        ndf.loc[ndf['recipient'] == username, 'is_read'] = True
        save_data(ndf, "notification")

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
        # LOGO & BRANDING
        st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=50)
            
        # --- IF USER IS LOGGED IN ---
        if 'user' in st.session_state:
            st.title("Arena Menu")
            u = st.session_state.user
            
            # --- NOTIFICATION CENTER ---
            notifs = get_my_notifications(u['username'])
            count = len(notifs)
            
            bell_icon = "🔔" if count > 0 else "🔕"
            label = f"Notifications ({count})" if count > 0 else "Notifications"
            
            with st.popover(f"{bell_icon} {label}", use_container_width=True):
                if count == 0:
                    st.caption("No new updates, warrior.")
                else:
                    st.write(f"**You have {count} new alerts!**")
                    for n in notifs:
                        st.info(f"{n['message']}\n\n_Example: {n['timestamp']}_")
                    
                    if st.button("Mark all as Read", key="clear_notifs"):
                        clear_notifications(u['username'])
                        st.rerun()
            
            st.markdown("---")
            # ---------------------------

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
                    with st.popover("🗑️", help="Remove custom photo"):
                        st.warning("Delete photo?")
                        if st.button("Confirm Delete", key="confirm_pic_del", type="primary"):
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
        
        # --- IF USER IS NOT LOGGED IN (SHOW LOGIN IN SIDEBAR) ---
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
                        # --- FIX: ENSURE ADMIN IS IN THE DATABASE ---
                        udf = load_data("user")
                        if "admin" not in udf['username'].values:
                            new_admin = {
                                "username": "admin", 
                                "password": hash_pass(admin_key), 
                                "full_name": "Lead Instructor", 
                                "role": "Instructor", 
                                "profile_pic": None
                            }
                            udf = pd.concat([udf, pd.DataFrame([new_admin])], ignore_index=True)
                            save_data(udf, "user")
                        # --------------------------------------------
                        
                        st.session_state.user = {"username": "admin", "full_name": "Lead Instructor", "role": "Instructor", "profile_pic": None}
                        st.session_state.current_page = "📊 Dashboard"
                        st.rerun()
                    else:
                        st.error("Wrong Key")

# --- PAGE: LANDING (Home Description) ---
def page_landing():
    st.markdown("""
    # ⚔️ Welcome to the Battle of Insights
    ### *Sharpen your data skills. Prepare for the Final Battle.*
    
    **The Arena is Open.** This platform is your dedicated training ground designed to bridge the gap between learning and performing.
    
    **Why participate?**
    * **🚀 Deploy Real Projects:** Apply your Excel and PowerBI skills to real-world scenarios.
    * **👨‍🏫 Receive Expert Assessment:** Get graded and reviewed by expert instructors.
    * **📈 Evolve:** Use personalized feedback to improve your analytics game before the main event.
    * **🏆 Compete:** Climb the leaderboard and earn your rank among warriors.
    
    ---
    **👈 Please use the sidebar to Login or Register.**
    """)

# --- PAGE: DASHBOARD ---
def page_dashboard():
    st.title("📊 Battlefield Intelligence")
    
    df = load_data()
    u = st.session_state.user
    st.caption(f"#### Welcome back, **{u['full_name']}**! Here is the current situation.")
    st.markdown("#### ")
    
    if df.empty:
        st.info("The battlefield is empty. Be the first to deploy!"); return

    # Global Calculations
    total_projects = len(df)
    total_warriors = df['username'].nunique()
    global_avg = df['instructor_grade'].mean()
    global_avg_display = f"{global_avg:.1f}" if pd.notna(global_avg) else "0.0"
    
    # Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛡️ Active Warriors", total_warriors)
    c2.metric("🚀 Total Deployments", total_projects)

    # Personalized / Role-Based Stats
    if u['role'] == "Student":
        my_projects = df[df['username'] == u['username']]
        my_avg = my_projects['instructor_grade'].mean()
        my_count = len(my_projects)
        
        delta_val = None
        if pd.notna(my_avg) and pd.notna(global_avg):
            diff = my_avg - global_avg
            delta_val = f"{diff:.1f} vs Avg"

        c3.metric("My Average Score", f"{my_avg:.1f}" if pd.notna(my_avg) else "N/A", delta=delta_val)
        c4.metric("My Deployments", my_count)
        
        if my_count == 0:
            st.warning("⚠️ You haven't deployed any projects yet. Go to 'Submit Project' to start!")
            
    else: # Instructor View
        graded_count = df['instructor_grade'].count()
        pending_count = total_projects - graded_count
        c3.metric("Class Avg Score", global_avg_display)
        c4.metric("📝 Pending Reviews", pending_count, delta=-pending_count if pending_count > 0 else 0, delta_color="inverse")

    st.divider()

    # Visual Insights
    col_chart1, col_chart2 = st.columns([1, 1])
    
    with col_chart1:
        st.subheader("📈 Deployment Velocity")
        try:
            df['date'] = pd.to_datetime(df['upload_time']).dt.date
            daily_counts = df['date'].value_counts().sort_index()
            st.line_chart(daily_counts, color="#FF4B4B")
            st.caption("Daily project submission volume.")
        except:
            st.error("Timeline data unavailable.")

    # --- REVERTED: CATEGORY BAR CHART ---
    with col_chart2:
        st.subheader("🏷️ Category Distribution")
        if 'category' in df.columns:
            cat_counts = df['category'].value_counts()
            st.bar_chart(cat_counts)
            st.caption("Breakdown of project types submitted.")
        else:
            st.info("No category data available.")

def page_submit():
    st.title("🚀 Submit Project")
    st.caption("#### Showcase your skills by uploading your latest analysis for review.")
    st.markdown("#### ")
    
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
                # 1. Save the physical file
                fname = f"{int(time.time())}_{file.name}"
                if not os.path.exists(PROJECTS_DIR):
                    os.makedirs(PROJECTS_DIR)
                with open(os.path.join(PROJECTS_DIR, fname), "wb") as f: 
                    f.write(file.getbuffer())
                
                # 2. Save Project Data (Explicitly load 'project')
                df = load_data("project") 
                new_row = {
                    "id": int(time.time()), 
                    "username": u['username'], 
                    "student_name": u['full_name'],
                    "category": cat, 
                    "project_title": title, 
                    "description": desc,
                    "filename": fname, 
                    "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "is_private": private, 
                    "instructor_grade": None, 
                    "instructor_review": "",
                    "likes": []
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df, "project") # Added "project" label
                
                # ---------------------------------------------------------
                # ### 🔔 NOTIFY INSTRUCTORS ###
                # ---------------------------------------------------------
                all_users = load_data("user")
                
                # Make sure we compare strings correctly
                instructors = all_users[all_users['role'].str.strip() == "Instructor"]
                
                notif_msg = f"🚀 New Submission: '{title}' by {u['full_name']}"
                
                if not instructors.empty:
                    for _, inst in instructors.iterrows():
                        # We pass the username of the instructor to the helper
                        add_notification(inst['username'], notif_msg)
                else:
                    # Fallback to hardcoded admin if no one has the role
                    add_notification("admin", notif_msg)
                # ---------------------------------------------------------

                st.success("Deployed!"); time.sleep(1)
                st.session_state.current_page = "📂 My Projects"
                st.rerun()
            else:
                st.error("Please provide both a title and a file!")

# --- PAGE: MY PROJECTS ---
def page_my_projects():
    st.title("📂 My Projects")
    st.caption("#### Manage your portfolio and view instructor feedback.")
    st.markdown("#### ")
    
    df = load_data()
    u = st.session_state.user
    
    my_df = df[df['username'] == u['username']].copy()
    
    if my_df.empty:
        st.info("You haven't deployed any projects yet.")
        return

    col1, col2 = st.columns([1, 2])
    with col1:
        categories = ["All Projects", "Excel", "Power BI", "Others"]
        selected_cat = st.selectbox("Filter by Category", categories, key="my_cat_filter")
    with col2:
        search_query = st.text_input("Search my titles", placeholder="Enter keywords...", key="my_search_filter")

    display_df = my_df.copy()
    if selected_cat != "All Projects":
        display_df = display_df[display_df['category'] == selected_cat]
    if search_query:
        display_df = display_df[display_df['project_title'].str.contains(search_query, case=False, na=False)]

    for idx, row in display_df.iterrows():
        with st.container(border=True):
            col_text, col_score, col_menu = st.columns([10, 2, 1])
            with col_text:
                st.subheader(row['project_title'])
                status = "🔒 Private" if row['is_private'] else "🌍 Public"
                st.caption(f"Status: {status} | Category: {row['category']}")
            with col_score:
                score = row['instructor_grade']
                if pd.notna(score): st.success(f"**Score: {score}/50**")
                else: st.info("**Score: Pending**")
            with col_menu:
                with st.popover("⋮"):
                    new_privacy = not row['is_private']
                    p_label = "Make Public 🌍" if row['is_private'] else "Make Private 🔒"
                    if st.button(p_label, key=f"p_{row['id']}", use_container_width=True):
                        df.at[idx, 'is_private'] = new_privacy
                        save_data(df); st.rerun()
                    if st.button("Edit 📝", key=f"e_{row['id']}", use_container_width=True):
                        st.session_state[f"editing_{row['id']}"] = True
                        st.rerun()
                    if st.button("Delete 🗑️", key=f"d_init_{row['id']}", use_container_width=True, type="primary"):
                        st.session_state[f"confirm_delete_{row['id']}"] = True
                    if st.session_state.get(f"confirm_delete_{row['id']}", False):
                        st.error("⚠️ Are you sure?")
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("Confirm", key=f"conf_del_{row['id']}", type="primary", use_container_width=True):
                                if os.path.exists(os.path.join(PROJECTS_DIR, row['filename'])):
                                    os.remove(os.path.join(PROJECTS_DIR, row['filename']))
                                df = df.drop(idx)
                                save_data(df)
                                del st.session_state[f"confirm_delete_{row['id']}"]
                                st.rerun()
                        with col_cancel:
                            if st.button("Cancel", key=f"canc_del_{row['id']}", use_container_width=True):
                                del st.session_state[f"confirm_delete_{row['id']}"]
                                st.rerun()

            if st.session_state.get(f"editing_{row['id']}", False):
                with st.form(f"f_{row['id']}"):
                    et = st.text_input("Edit Title", row['project_title'])
                    ed = st.text_area("Edit Insights", row['description'])
                    if st.form_submit_button("Save Changes"):
                        df.at[idx, 'project_title'] = et
                        df.at[idx, 'description'] = ed
                        save_data(df)
                        st.session_state[f"editing_{row['id']}"] = False
                        st.rerun()
                    if st.form_submit_button("Cancel"):
                        st.session_state[f"editing_{row['id']}"] = False
                        st.rerun()

            t1, t2, t3 = st.tabs(["📄 Details", "💬 Feedback & Comments", "👨‍🏫 Assessment"])
            with t1:
                with st.expander("📖 View Project Description"):
                    st.write(row['description'])
                path = os.path.join(PROJECTS_DIR, row['filename'])
                if os.path.exists(path):
                    st.image(path, use_container_width=True)
            with t2:
                raw_comments = row['comments']
                all_cmts = [] if pd.isna(raw_comments) or raw_comments == "" or raw_comments == "[]" else ast.literal_eval(str(raw_comments))
                likes_count = len(row['likes']) if isinstance(row['likes'], list) else 0
                st.write(f"❤️ **{likes_count} Likes**")
                st.markdown("---")
                if not all_cmts: st.caption("No comments yet.")
                else:
                    for c in all_cmts:
                        with st.chat_message("user"):
                            st.write(f"**{c['user']}** • <small>{c.get('time', '')}</small>", unsafe_allow_html=True)
                            st.write(c['text'])
            with t3:
                if row['instructor_review']: st.info(row['instructor_review'])
                else: st.write("No detailed assessment yet.")
    
# --- PAGE: ARENA ---
def page_arena():
    st.title("⚔️ Battle Arena")
    st.caption("#### Explore work from your peers and engage in constructive discussion.")
    st.markdown("#### ")
    
    df = load_data()
    u = st.session_state.user
    if df.empty: st.info("The arena is quiet."); return

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_cat = st.selectbox("Filter by Category", ["All Projects", "Excel", "Power BI", "Others"])
    with col2:
        search_query = st.text_input("Search by Title or Warrior Name", placeholder="Enter keywords...")

    display_df = df.copy()
    if selected_cat != "All Projects": display_df = display_df[display_df['category'] == selected_cat]
    if search_query:
        display_df = display_df[display_df['project_title'].str.contains(search_query, case=False, na=False) | 
                                display_df['student_name'].str.contains(search_query, case=False, na=False)]

    for idx, row in display_df.iterrows():
        if row['is_private'] and (u['username'] != row['username'] and u['role'] != "Instructor"): continue
        with st.container(border=True):
            col_main, col_score = st.columns([4, 1.2])
            with col_main:
                prefix = "🔒 " if row['is_private'] else ""
                st.subheader(f"{prefix}{row['project_title']}")
                st.caption(f"Warrior: **{row['student_name']}** | Category: **{row['category']}**")
            with col_score:
                score = row['instructor_grade']
                if pd.notna(score): st.success(f"**Score: {score}/50**")
                else: st.info("**Score: Pending**")
            
            t1, t2, t3 = st.tabs(["📄 Details", "💬 Feedback & Discussion", "👨‍🏫 Assessment"])
            with t1:
                with st.expander("📖 View Project Description"): st.write(row['description'])
                path = os.path.join(PROJECTS_DIR, row['filename'])
                if os.path.exists(path):
                    ext = row['filename'].lower().split('.')[-1]
                    if ext in ['png', 'jpg', 'jpeg']: st.image(path, use_container_width=True)
                    st.download_button("📥 Download", open(path, "rb"), file_name=row['filename'], key=f"dl_{row['id']}")
            
            with t2:
                likes = row['likes'] if isinstance(row['likes'], list) else []
                liked = u['username'] in likes
                if st.button(f"{'❤️' if liked else '🤍'} {len(likes)} Likes", key=f"l_{row['id']}"):
                    if liked: 
                        likes.remove(u['username'])
                    else: 
                        likes.append(u['username'])
                        # --- NOTIFY PROJECT OWNER (IF NOT SELF) ---
                        if row['username'] != u['username']:
                            send_notification(row['username'], f"❤️ {u['full_name']} liked your project: '{row['project_title']}'")
                        # ------------------------------------------

                    df.at[idx, 'likes'] = likes 
                    save_data(df); st.rerun()

                st.markdown("---")
                raw_comments = row['comments']
                all_cmts = [] if pd.isna(raw_comments) or raw_comments == "" or raw_comments == "[]" else ast.literal_eval(str(raw_comments))

                with st.form(key=f"cmt_form_{row['id']}", clear_on_submit=True):
                    new_cmt_text = st.text_input("Share your thoughts...")
                    if st.form_submit_button("Post Comment") and new_cmt_text:
                        all_cmts.append({"user": u['full_name'], "text": new_cmt_text, "time": datetime.now().strftime("%b %d, %H:%M")})
                        df.at[idx, 'comments'] = str(all_cmts)
                        save_data(df)
                        
                        # --- NOTIFY PROJECT OWNER (IF NOT SELF) ---
                        if row['username'] != u['username']:
                            send_notification(row['username'], f"💬 {u['full_name']} commented on: '{row['project_title']}'")
                        # ------------------------------------------
                        
                        st.rerun()

                for c in all_cmts:
                    with st.chat_message("user"):
                        st.write(f"**{c['user']}** • <small>{c['time']}</small>", unsafe_allow_html=True)
                        st.write(c['text'])

            with t3:
                if u['role'] == "Instructor":
                    current_grade = int(row['instructor_grade']) if pd.notna(row['instructor_grade']) else 0
                    ng = st.number_input("Mark (0-50)", 0, 50, current_grade, key=f"g_{row['id']}")
                    nr = st.text_area("Instructor Feedback", str(row['instructor_review']) if pd.notna(row['instructor_review']) else "", key=f"r_{row['id']}")
                    if st.button("Submit Grade", key=f"s_{row['id']}"):
                        df.at[idx, 'instructor_grade'] = ng
                        df.at[idx, 'instructor_review'] = nr
                        save_data(df)
                        
                        # --- NOTIFY STUDENT ---
                        send_notification(row['username'], f"👨‍🏫 Your project '{row['project_title']}' has been graded! Score: {ng}/50")
                        # ----------------------

                        st.toast("Grade Saved!"); st.rerun()
                else:
                    st.info(row['instructor_review'] if row['instructor_review'] else "No instructor feedback yet.")

# --- PAGE: LEADERBOARD ---
def page_leaderboard():
    st.title("🏆 Warrior Leaderboard")
    st.caption("#### Recognizing consistency and excellence in data analysis.")
    st.markdown("#### ")
    
    df = load_data()
    
    if df.empty:
        st.info("No projects submitted yet.")
        return

    # Filter graded projects
    graded_df = df[df['instructor_grade'].notna()].copy()
    
    if graded_df.empty:
        st.info("Waiting for the instructor to finalize grades...")
        return

    # Aggregate by student
    student_leaderboard = graded_df.groupby('username').agg({
        'student_name': 'first',
        'project_title': 'count',
        'instructor_grade': ['mean', 'max'],
        'likes': lambda x: sum(len(l) if isinstance(l, list) else 0 for l in x)
    }).reset_index()

    student_leaderboard.columns = ['Username', 'Warrior Name', 'Projects', 'Avg Score', 'Best Score', 'Total Likes']
    
    # Rounding and Type conversion
    student_leaderboard['Avg Score'] = student_leaderboard['Avg Score'].round(1)
    student_leaderboard['Best Score'] = student_leaderboard['Best Score'].astype(float)

    # Sorting Logic (Volume -> Quality)
    student_leaderboard = student_leaderboard.sort_values(
        by=['Projects', 'Avg Score'], 
        ascending=[False, False]
    )

    # Dense Ranking
    student_leaderboard['Rank'] = student_leaderboard[['Projects', 'Avg Score']].apply(tuple, axis=1).rank(
        method='dense', 
        ascending=False
    ).astype(int)

    student_leaderboard = student_leaderboard.sort_values('Rank')

    if not student_leaderboard.empty:
        top_warrior = student_leaderboard.iloc[0]
        st.success(f"🎊 **Current Leader:** {top_warrior['Warrior Name']} | **{top_warrior['Projects']}** Projects | Avg: **{top_warrior['Avg Score']}**")
    
    st.divider()

    st.dataframe(
        student_leaderboard[['Rank', 'Warrior Name', 'Projects', 'Avg Score', 'Best Score', 'Total Likes']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="%d 🏅"),
            "Projects": st.column_config.NumberColumn("Deployments", format="%d 🚀"),
            "Avg Score": st.column_config.ProgressColumn(
                "Avg Marks",
                help="Average marks across all graded projects.",
                format="%.1f",
                min_value=0,
                max_value=50,
            ),
            "Best Score": st.column_config.NumberColumn("Best Score", format="%.1f"),
            "Total Likes": st.column_config.NumberColumn("Total Likes", format="%d ❤️")
        }
    )

# --- PAGE: INSTRUCTOR CONTROL ---
def page_instructor_table():
    if st.session_state.user['role']
