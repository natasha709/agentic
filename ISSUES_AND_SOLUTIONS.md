# Sentinel AI - Issues and Solutions

## Issue: AI Not Giving Feedback

### Root Cause
Your Gemini API key has been **blocked by Google** because it was reported as "leaked."

Error message:
```
403 PERMISSION_DENIED: {'error': {'code': 403, 'message': 'Your API key was reported as leaked.', 'status': 'PERMISSION_DENIED'}}
```

### Solution Steps

#### Option 1: Get New API Key (Recommended)
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account  
3. Click "Create API Key"
4. Copy the new key
5. Update `backend/.env`:
   
```
   GEMINI_API_KEY=your_new_key_here
   
```
6. Restart backend server

#### Option 2: Enable Mock Mode (Immediate Workaround)
Add this to `backend/.env`:
```
USE_MOCK_MODE=true
```

This allows testing without a working AI key.

---

## Code Improvement Added (main.py)

The following error handling improvements were made:

- Detects "leaked" API keys and shows helpful fix instructions  
- Detects invalid credentials (401 errors)
- Detects rate limit errors (429 errors)  
- Shows fallback tips when no valid API key is configured

These changes help users understand what's wrong when AI requests fail.
