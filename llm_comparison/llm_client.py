import os
import re
import json

# Global backend
_CURRENT_BACKEND = "local"  # default

def set_llm_backend(backend: str):
    global _CURRENT_BACKEND
    _CURRENT_BACKEND = backend
    print(f"Backend set to: {backend.upper()}")

# Optional: Gemini
try:
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    GEMINI_AVAILABLE = True
except:
    GEMINI_AVAILABLE = False

# Local Ollama
try:
    from ollama import Client # type: ignore
    ollama = Client(host=os.getenv("OLLAMA_HOST", "127.0.0.1:11434"))
    os.environ["OLLAMA_NUM_GPU_LAYERS"] = "999"
    os.environ["OLLAMA_FLASH_ATTENTION"] = "1"
    OLLAMA_AVAILABLE = True
except:
    OLLAMA_AVAILABLE = False

from .prompts import build_comparative_analysis_prompt
from .formatters import format_candidates_for_llm
from .response_cleaner import clean_llm_response

LLM_TIMEOUT = 120
MAX_RETRIES = 2

def _extract_candidate_id(raw_value: str, candidate_ids: list[str]) -> str:
    if not raw_value:
        return ""
    text = str(raw_value).strip()
    digit_match = re.search(r"\d{5,}", text)
    if digit_match:
        cid = digit_match.group(0)
        if cid in candidate_ids:
            return cid
    stripped = text.lstrip("#").strip()
    if stripped in candidate_ids:
        return stripped
    return ""

def llm_comparative_analysis(candidates: list, job_query: str, show_progress: bool = True) -> dict:
    candidates = candidates[:3]
    prompt = build_comparative_analysis_prompt(format_candidates_for_llm(candidates), job_query)
    candidate_ids = [str(c.get("id")) for c in candidates]
    result = {}

    if _CURRENT_BACKEND == "gemini" and GEMINI_AVAILABLE:
        if show_progress:
            print("   Using model: gemini-2.5-flash...", end="", flush=True)
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2, 
                    "max_output_tokens": 8192  # this prevents truncation
                }
            )
            
            # Check finish_reason before accessing text
            if response.candidates and response.candidates[0].finish_reason == 2:
                raise ValueError("Max tokens still reached — try simplifying prompt or use local fallback.")
            
            if not response.text or not response.text.strip():
                raise ValueError("Empty response from Gemini")
            
            text = response.text.strip()
            cleaned = clean_llm_response(text)
            data = json.loads(cleaned)

            for item in data:
                cid = _extract_candidate_id(item.get("candidate_id", ""), candidate_ids)
                if cid:
                    result[cid] = item
            if show_progress:
                print(" Success!")
            return result
        except Exception as e:
            if show_progress:
                print(f" Gemini failed: {str(e)[:100]}")

    # Local fallback
    if OLLAMA_AVAILABLE:
        model_name = "qwen2.5:1.5b-instruct"
        if show_progress:
            print(f"   Using model: {model_name} (GPU)...", end="", flush=True)
        try:
            resp = ollama.generate(
                model=model_name,
                prompt=prompt,
                options={"temperature": 0.1, "num_predict": 1200, "num_ctx": 4096}
            )
            text = resp["response"].strip()
            cleaned = clean_llm_response(text)
            data = json.loads(cleaned)

            temp = {}
            unmatched = []
            for item in data:
                cid = _extract_candidate_id(item.get("candidate_id", ""), candidate_ids)
                if cid:
                    temp[cid] = item
                else:
                    unmatched.append(item)
            for cid in candidate_ids:
                if cid not in temp and unmatched:
                    temp[cid] = unmatched.pop(0)
            result.update(temp)
            if show_progress:
                print(" Success!")
            return result
        except Exception as e:
            if show_progress:
                print(f" Error: {e}")

    if show_progress:
        print(" All backends failed")
    return {}


# Async LLM wrapper for AI agents
# import asyncio

# class LLMModel:
#     """Simple async wrapper for LLM calls used by AI agents"""
    
#     async def generate(self, prompt: str) -> str:
#         """Generate text from prompt using available backend"""
#         # Try Gemini first if available and selected
#         if _CURRENT_BACKEND == "gemini" and GEMINI_AVAILABLE:
#             try:
#                 # Run in thread pool since Gemini is sync
#                 loop = asyncio.get_event_loop()
#                 model = genai.GenerativeModel("gemini-2.5-flash")
#                 response = await loop.run_in_executor(
#                     None,
#                     lambda: model.generate_content(
#                         prompt,
#                         generation_config={
#                             "temperature": 0.2,
#                             "max_output_tokens": 4096
#                         }
#                     )
#                 )
#                 if response.text:
#                     return response.text.strip()
#             except Exception:
#                 pass  # Fall through to Ollama
        
#         # Use Ollama (free, local) - run in thread pool since it's sync
#         if OLLAMA_AVAILABLE:
#             try:
#                 loop = asyncio.get_event_loop()
#                 resp = await loop.run_in_executor(
#                     None,
#                     lambda: ollama.generate(
#                         model="qwen2.5:1.5b-instruct",
#                         prompt=prompt,
#                         options={"temperature": 0.1, "num_predict": 800, "num_ctx": 2048}
#                     )
#                 )
#                 return resp.get("response", "").strip()
#             except Exception as e:
#                 raise RuntimeError(f"LLM generation failed: {e}")
        
#         raise RuntimeError("No LLM backend available. Please install Ollama or configure Gemini API key.")


# # Export model instance for agents
# model = LLMModel()