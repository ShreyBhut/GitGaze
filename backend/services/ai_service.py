import os
import google.generativeai as genai
from fastapi import HTTPException

# Configuration happens inside the function to ensure it picks up env vars correctly

async def generate_code_summary(code_content: str, detail_level: str = "concise") -> str:
    """
    Generates a markdown summary of the provided code using Gemini.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY is not configured in the environment."
        )
        
    genai.configure(api_key=api_key)

    try:
        model = genai.GenerativeModel("gemini-flash-lite-latest")
        
        if detail_level == "detailed":
            prompt = f"""
You are an expert software architect analyzing code. 
Please provide a comprehensive and highly detailed summary of the following code file.

Rules:
1. Provide a thorough high-level overview.
2. List all key functions, classes, and variables with detailed explanations of their purpose and behavior.
3. Output the result in clean Markdown format.

Code:
```
{code_content}
```
"""
        else:
            prompt = f"""
You are an expert software architect analyzing code. 
Please provide a highly concise but technically accurate summary of the following code file.

Rules:
1. Provide a 1-sentence high-level overview.
2. If there are key functions or classes, list their primary purpose briefly using bullet points.
3. Output the result in clean Markdown format.
4. Keep the total output under 150 words.

Code:
```
{code_content}
```
"""
        
        # generate_content_async is the async wrapper provided by the library
        response = await model.generate_content_async(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error generating AI summary: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to generate AI summary. Ensure your Gemini API key is valid."
        )
