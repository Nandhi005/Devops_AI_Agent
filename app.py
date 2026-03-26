import streamlit as st
from streamlit_oauth import OAuth2Component
from agent import devops_agent
from db import (
    save_chat,
    get_conversations,
    get_chat_by_conversation,
    create_user,
    is_pro_user,
    rename_conversation,
    delete_conversation
)
from email_utils import send_payment_email
from jose import jwt
import os, uuid, time
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="DevOps AI", layout="wide")

# =====================
# 🎨 GLOBAL CSS
# =====================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: white;
}

/* Chat bubbles */
.user-msg {
    background: #2563eb;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 8px 0;
    width: fit-content;
    margin-left: auto;
}

.bot-msg {
    background: #1e293b;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 8px 0;
    width: fit-content;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #020617;
}
</style>
""", unsafe_allow_html=True)

# =====================
# SESSION
# =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = {}

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_plans" not in st.session_state:
    st.session_state.show_plans = False


# =====================
# LOGIN
# =====================
oauth2 = OAuth2Component(
    os.getenv("GOOGLE_CLIENT_ID"),
    os.getenv("GOOGLE_CLIENT_SECRET"),
    "https://accounts.google.com/o/oauth2/auth",
    "https://oauth2.googleapis.com/token"
)

def get_user_info(token):
    return jwt.get_unverified_claims(token.get("id_token"))

if not st.session_state.logged_in:

    st.markdown("""
    <style>
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 80vh;
    }
    .login-card {
        background: rgba(255,255,255,0.05);
        padding: 40px;
        border-radius: 16px;
        backdrop-filter: blur(10px);
        text-align: center;
        width: 400px;
        box-shadow: 0 0 30px rgba(0,0,0,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-container">
        <div class="login-card">
            <h1>🚀 DevOps AI Agent</h1>
            <p style="color:gray;">Kubernetes • Docker • CI/CD</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2,2,2])
    with col2:
        result = oauth2.authorize_button(
            name="🔐 Continue with Google",
            redirect_uri="https://devopsaiagen.streamlit.app/",
            scope="openid email profile",
            key="google"
        )

    if result and "token" in result:
        st.session_state.user = get_user_info(result["token"])
        st.session_state.logged_in = True
        st.rerun()

    st.stop()


# =====================
# USER
# =====================
email = st.session_state.user.get("email", "unknown")
name = st.session_state.user.get("name", "User")

create_user(email)
is_pro = is_pro_user(email)

# =====================
# LIMIT
# =====================
MAX_FREE = 5
user_chats = get_conversations(email).data
remaining = MAX_FREE - len(user_chats)


# =====================
# SIDEBAR
# =====================
with st.sidebar:

    st.markdown(f"👤 {email}")

    if is_pro:
        st.success("🚀 PRO USER")
    else:
        st.info(f"🆓 Free ({remaining} left)")

    if st.button("➕ New Chat"):
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.markdown("### 💬 Conversations")

    data = get_conversations(email).data
    conversations = {}

    for chat in data:
        cid = chat["conversation_id"]
        if cid not in conversations:
            title = chat.get("title") or chat["message"]
            conversations[cid] = title

    for cid, title in conversations.items():

        col1, col2, col3 = st.columns([5,1,1])

        with col1:
            if st.button(title[:25], key=cid):
                st.session_state.conversation_id = cid
                chats = get_chat_by_conversation(email, cid).data

                st.session_state.messages = []
                for c in chats:
                    st.session_state.messages.append(("user", c["message"]))
                    st.session_state.messages.append(("bot", c["response"]))

                st.rerun()

        with col2:
            if st.button("✏️", key=f"rename_{cid}"):
                new_title = st.text_input("Rename", key=f"input_{cid}")
                if new_title:
                    rename_conversation(email, cid, new_title)
                    st.rerun()

        with col3:
            if st.button("🗑️", key=f"delete_{cid}"):
                delete_conversation(email, cid)
                st.rerun()


# =====================
# TOP BAR
# =====================
col1, col2 = st.columns([6,1])

with col1:
    st.markdown("""
    <div style="text-align:center;">
        <h2>🤖 DevOps AI Assistant</h2>
        <p style="color:gray;">Fix Kubernetes • Debug Docker • CI/CD</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    with st.expander("👤"):
        st.markdown(f"**{name}**")
        st.write(email)

        if is_pro:
            st.success("🚀 PRO PLAN")
        else:
            st.info(f"{remaining} free queries left")

        if st.button("💳 Plans"):
            st.session_state.show_plans = not st.session_state.show_plans

        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user = {}
            st.session_state.messages = []
            st.rerun()


# =====================
# PLANS
# =====================
if st.session_state.show_plans:

    st.markdown("## 💳 Upgrade to Pro")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 🚀 Pro Plan - ₹299
        Unlimited queries
        """)

    with col2:
        st.image("qr.png", width=200)

    if st.button("✅ I Paid"):
        send_payment_email(email)
        st.success("📧 Request sent!")


# =====================
# LIMIT BLOCK
# =====================
if not is_pro and remaining <= 0:
    st.warning("Free limit reached. Upgrade to Pro 💳")
    st.stop()


# =====================
# CHAT DISPLAY
# =====================
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; margin-top:120px;">
        <h1>🚀 DevOps AI Assistant</h1>
        <p style="color:gray;">Ask anything about DevOps</p>
    </div>
    """, unsafe_allow_html=True)

else:
    for role, msg in st.session_state.messages:
        if role == "user":
            st.markdown(f"<div class='user-msg'>🧑 {msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bot-msg'>🤖 {msg}</div>", unsafe_allow_html=True)


# =====================
# CHAT INPUT + STREAM
# =====================
user_input = st.chat_input("Ask DevOps question...")

if user_input:

    st.session_state.messages.append(("user", user_input))

    placeholder = st.empty()
    full_text = ""

    response = devops_agent(user_input)

    for char in response:
        full_text += char
        placeholder.markdown(f"<div class='bot-msg'>🤖 {full_text}</div>", unsafe_allow_html=True)
        time.sleep(0.01)

    st.session_state.messages.append(("bot", response))

    save_chat(
        email,
        st.session_state.conversation_id,
        user_input,
        response
    )

    st.rerun()
