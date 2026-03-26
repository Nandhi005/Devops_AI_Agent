from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.1-8b-instant"
)

def devops_agent(user_input):
    prompt = f"""
You are a Senior DevOps Engineer.

Give:
- Root cause
- Fix
- Commands

User:
{user_input}
"""
    response = llm.invoke(prompt)
    return response.content