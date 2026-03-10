import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

print("=== Environment Variables Test ===")
print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')}")
print(f"USE_MOCK_MODE: {os.getenv('USE_MOCK_MODE')}")

if os.getenv('GEMINI_API_KEY'):
    print("\n=== Testing API Key ===")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
        response = llm.invoke("Say 'API works!' in 3 words")
        print(f"API Response: {response.content}")
    except Exception as e:
        print(f"API Error: {str(e)[:200]}")
