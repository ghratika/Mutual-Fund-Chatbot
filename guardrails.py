import os
import re
import json
from groq import Groq
from prompts import SYSTEM_PROMPT

# Design Aesthetics: Log printing with professional styling
def log_info(msg):
    print(f"\033[94m[INFO]\033[0m {msg}")

def log_success(msg):
    print(f"\033[92m[SUCCESS]\033[0m {msg}")

def log_warn(msg):
    print(f"\033[93m[WARN]\033[0m {msg}")

def log_error(msg):
    print(f"\033[91m[ERROR]\033[0m {msg}")

def load_env():
    """
    Manually loads key-value pairs from .env or .env.local in the workspace directory.
    """
    for env_file in [".env", ".env.local"]:
        if os.path.exists(env_file):
            log_info(f"Loading environment variables from {env_file}...")
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        try:
                            key, val = line.split("=", 1)
                            os.environ[key.strip()] = val.strip().strip('"').strip("'")
                        except Exception as e:
                            pass

# Load environment on import
load_env()

def count_sentences(text: str) -> int:
    """
    Counts the number of sentences in the response, ignoring common abbreviations
    like 'Rs.' or 'Mr.' and number decimals.
    """
    # Replace common abbreviations with custom placeholders
    processed = text
    abbreviations = [
        "Rs.", "rs.", "Mr.", "Mrs.", "Dr.", "co.", "inc.", "vs.", 
        "Jan.", "Feb.", "Mar.", "Apr.", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."
    ]
    for abbr in abbreviations:
        processed = re.sub(rf"\b{re.escape(abbr)}", abbr.replace(".", "_"), processed)
    
    # Split sentences by period, question mark, or exclamation mark followed by whitespace or end of string
    raw_sentences = re.split(r'[.!?](?:\s+|$)', processed)
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return len(sentences)

def validate_response(text: str, target_url: str) -> tuple[bool, str]:
    """
    Validates that:
    1. Sentence count is <= 3.
    2. Exactly one citation (matching target_url) is present.
    Returns (is_valid, reason)
    """
    # Check sentence count
    num_sentences = count_sentences(text)
    if num_sentences > 3:
        return False, f"Sentence count exceeds limit: {num_sentences} sentences found (limit: 3)."
        
    # Check URL citations
    # Find all URLs in the text
    urls = re.findall(r'https?://[^\s)]+', text)
    # Strip common trailing punctuations from URLs
    cleaned_urls = [url.rstrip('.,;)!?') for url in urls]
    
    if len(cleaned_urls) != 1:
        return False, f"Expected exactly one URL citation, but found {len(cleaned_urls)}: {cleaned_urls}"
        
    if cleaned_urls[0] != target_url:
        return False, f"URL citation mismatch. Expected '{target_url}', but found '{cleaned_urls[0]}'"
        
    return True, "Success"

def get_template_fallback_response(metrics: dict) -> str:
    """
    Generates a highly structured, fully compliant fallback response using the database metrics.
    Guarantees exactly 3 sentences and a single citation.
    """
    scheme_name = metrics.get("scheme_name", "the fund")
    nav = metrics.get("nav", "N/A")
    nav_date = metrics.get("nav_date", "N/A")
    aum = metrics.get("aum", "N/A")
    return_1m = metrics.get("return_1m", "N/A")
    return_6m = metrics.get("return_6m", "N/A")
    return_1y = metrics.get("return_1y", "N/A")
    expense_ratio = metrics.get("expense_ratio", "N/A")
    exit_load = metrics.get("exit_load", "N/A")
    min_sip = metrics.get("min_sip", "N/A")
    riskometer = metrics.get("riskometer", "N/A")
    benchmark = metrics.get("benchmark", "N/A")
    url = metrics.get("url", "")
    
    # Construct exact 3-sentence compliant factual response
    s1 = f"The {scheme_name} has a Net Asset Value (NAV) of Rs.{nav} (as of {nav_date}) and Assets Under Management (AUM) of Rs.{aum} Crores."
    s2 = f"It has generated return rates of {return_1m}% over 1 month, {return_6m}% over 6 months, and {return_1y}% over 1 year."
    s3 = f"For official information, please visit {url}."
    
    return f"{s1} {s2} {s3}"

class GroqGuardrailClient:
    def __init__(self, model_name="llama-3.3-70b-versatile"):
        self.model_name = model_name
        self.api_key = os.environ.get("GROQ_API_KEY")
        
        if not self.api_key:
            log_warn("GROQ_API_KEY environment variable is not set. Live LLM calls will fail and trigger fallbacks.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.api_key)
                log_success(f"Groq client initialized with model '{self.model_name}'.")
            except Exception as e:
                log_error(f"Error initializing Groq client: {e}")
                self.client = None

    def generate_response(self, query: str, context: str, metrics: dict) -> str:
        """
        Queries Groq LLM, validates output, and returns either LLM output or fallback.
        Appends the standardized update date footer at the end.
        """
        target_url = metrics.get("url", "")
        update_date = metrics.get("nav_date", "N/A")
        
        llm_response = None
        
        if self.client:
            try:
                log_info("Submitting query to Groq LLM...")
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Context Information:\n{context}\n\nQuery: {query}"}
                    ],
                    model=self.model_name,
                    temperature=0.0, # Greedy decoding for maximum reliability
                    max_tokens=256
                )
                llm_response = chat_completion.choices[0].message.content.strip()
                log_success("Groq LLM response received.")
            except Exception as e:
                log_error(f"Error during Groq API call: {e}. Falling back to template.")
        else:
            log_warn("No active Groq client available. Bypassing to template fallback.")

        # If LLM returned a response, perform programmatic post-validation
        if llm_response:
            is_valid, reason = validate_response(llm_response, target_url)
            if is_valid:
                log_success("LLM response passed all guardrail checks.")
                final_response = f"{llm_response}\n\nLast updated from sources: {update_date}"
                return final_response
            else:
                log_warn(f"LLM response failed validation. Reason: {reason}")
                
        # Trigger Fallback Handler
        log_info("Executing template fallback handler...")
        fallback_text = get_template_fallback_response(metrics)
        final_response = f"{fallback_text}\n\nLast updated from sources: {update_date}"
        return final_response
