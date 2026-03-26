from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# USER FUNCTIONS
# =========================
def create_user(email):
    existing = supabase.table("users").select("*").eq("email", email).execute()

    if not existing.data:
        supabase.table("users").insert({
            "email": email,
            "is_pro": False
        }).execute()


def is_pro_user(email):
    data = supabase.table("users").select("is_pro").eq("email", email).execute()

    if data.data:
        return data.data[0]["is_pro"]
    return False


# =========================
# CHAT FUNCTIONS
# =========================
def save_chat(email, conversation_id, message, response):
    supabase.table("chats").insert({
        "email": email,
        "conversation_id": conversation_id,
        "message": message,
        "response": response
    }).execute()


def get_conversations(email):
    return supabase.table("chats") \
        .select("*") \
        .eq("email", email) \
        .order("created_at") \
        .execute()


def get_chat_by_conversation(email, conversation_id):
    return supabase.table("chats") \
        .select("*") \
        .eq("email", email) \
        .eq("conversation_id", conversation_id) \
        .order("created_at") \
        .execute()

# =========================
# RENAME CHAT
# =========================
def rename_conversation(email, conversation_id, new_title):
    supabase.table("chats") \
        .update({"title": new_title}) \
        .eq("email", email) \
        .eq("conversation_id", conversation_id) \
        .execute()


# =========================
# DELETE CHAT
# =========================
def delete_conversation(email, conversation_id):
    supabase.table("chats") \
        .delete() \
        .eq("email", email) \
        .eq("conversation_id", conversation_id) \
        .execute()
