import re
from enum import Enum
import numpy as np
from sentence_transformers import SentenceTransformer

# Design Aesthetics: Log printing with professional styling
def log_info(msg):
    print(f"\033[94m[INFO]\033[0m {msg}")

def log_success(msg):
    print(f"\033[92m[SUCCESS]\033[0m {msg}")

def log_warn(msg):
    print(f"\033[93m[WARN]\033[0m {msg}")

class UserIntent(Enum):
    FACTUAL = "factual"
    ADVISORY = "advisory"
    OUT_OF_SCOPE = "out_of_scope"

class IntentClassifier:
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        log_info("Initializing Intent Classifier with advanced heuristics...")
        # Use sentence-transformers (cached from Phase 2)
        self.model = SentenceTransformer(model_name)
        
        # Subjective & Advisory Anchor Sentences (Strictly non-factual)
        self.advisory_anchors = [
            "Should I invest in HDFC Mid-Cap Fund?",
            "Which is the best fund to buy right now?",
            "Will HDFC Defence Fund give good returns next year?",
            "Can you recommend a mutual fund for me?",
            "HDFC Small Cap vs HDFC Mid Cap which is a better investment?",
            "Is HDFC Top 100 Fund a safe investment option?",
            "Which of these funds should I purchase for long term?",
            "Can you recommend a good financial asset?",
            "give me investment advice or tips",
            "is this fund good for investing?",
            "which fund has highest returns?"
        ]

        # Factual & Informational Anchor Sentences (Safe to answer)
        self.factual_anchors = [
            "What is the NAV of HDFC Mid Cap?",
            "Who is the fund manager of HDFC Defence Fund?",
            "What is the expense ratio of HDFC Small Cap?",
            "Show me the exit load for HDFC Large Cap.",
            "Tell me about the fund manager's experience.",
            "What is the benchmark index of the gold fund?",
            "Who is managing the portfolio?",
            "What is the minimum SIP amount?",
            "Provide the details of HDFC Defence Fund.",
            "Tell me about HDFC Large Cap Fund.",
            "What is the description of HDFC Mid Cap?",
            "Tell me about HDFC Large Cap Fund Direct Growth",
            "What is the expense ratio and benchmark of HDFC Defence Fund?"
        ]
        
        log_info("Pre-computing anchor embeddings...")
        self.advisory_embeddings = self.model.encode(self.advisory_anchors, normalize_embeddings=True)
        self.factual_embeddings = self.model.encode(self.factual_anchors, normalize_embeddings=True)
        log_success("Pre-computation completed. Classifier is ready.")

        # Heuristic rules
        self.financial_keywords = [
            "fund", "hdfc", "scheme", "nav", "sip", "expense", "exit", "load", "manager", 
            "benchmark", "portfolio", "invest", "equity", "growth", "gold", "defence", 
            "opportunities", "cap", "amc", "sebi", "amfi", "return", "ratio", "fee", 
            "charge", "allotment", "tax", "gains", "report", "statement", "money", 
            "buy", "sell", "growth", "experience", "education", "background", "profile",
            "chirag", "setalvad", "dhruv", "muchhal", "rahul", "baijal", 
            "arun", "agarwal", "nandita", "menezes", "priya", "ranjan"
        ]
        self.greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "help"]

    def classify(self, query):
        """
        Classifies user query into FACTUAL, ADVISORY, or OUT_OF_SCOPE.
        Returns:
            UserIntent enum, similarity_score, matched_anchor_text
        """
        cleaned_query = query.strip().lower()
        
        # --- Layer 1: Greeting Override ---
        # Allow basic greetings so the chatbot can reply with the welcome message/options
        if cleaned_query in self.greetings or cleaned_query.replace("!", "") in self.greetings:
            return UserIntent.FACTUAL, 1.0, "Greeting Heuristic"

        # --- Layer 2: Out-Of-Scope Heuristic Gate ---
        # Check if the query has ANY relevance to mutual funds / finance
        has_financial_keyword = any(kw in cleaned_query for kw in self.financial_keywords)
        if not has_financial_keyword:
            log_warn(f"Query contains zero financial keywords. Tagged OUT_OF_SCOPE: '{query}'")
            return UserIntent.OUT_OF_SCOPE, 1.0, "No Financial Context Heuristic"

        # --- Layer 3: Rule-Based Keyword Checks for Advisory ---
        advisory_regexes = [
            r"\b(should i invest|recommend|suggest|advise|buy or sell|which is better|is it good|is it safe|investment advice|portfolio tips)\b",
            r"\b(which (one |fund )?is better|better than|returns comparison)\b",
            r"\b(suggest some|recommend some)\b"
        ]
        
        for reg in advisory_regexes:
            if re.search(reg, cleaned_query):
                log_warn(f"Advisory intent flagged by rule-based match (regex: '{reg}')")
                return UserIntent.ADVISORY, 1.0, f"Rule Match: {reg}"

        if " vs " in cleaned_query or " versus " in cleaned_query:
            log_warn("Advisory comparison intent flagged by rule-based match ('vs/versus')")
            return UserIntent.ADVISORY, 1.0, "Rule Match: Comparison (vs)"

        # --- Layer 4: Semantic Similarity Check for Advisory vs Factual ---
        query_embedding = self.model.encode([query], normalize_embeddings=True)[0]
        
        advisory_similarities = np.dot(self.advisory_embeddings, query_embedding)
        max_advisory_idx = np.argmax(advisory_similarities)
        max_advisory_score = advisory_similarities[max_advisory_idx]
        
        factual_similarities = np.dot(self.factual_embeddings, query_embedding)
        max_factual_idx = np.argmax(factual_similarities)
        max_factual_score = factual_similarities[max_factual_idx]
        
        # We classify as ADVISORY only if the query is closer to an advisory anchor than a factual one
        # and has a minimum threshold of similarity.
        if max_advisory_score > max_factual_score and max_advisory_score > 0.80:
            matched_anchor = self.advisory_anchors[max_advisory_idx]
            log_warn(f"Advisory semantic similarity score: {max_advisory_score:.4f} (Factual score: {max_factual_score:.4f}) matched to anchor: '{matched_anchor}'")
            return UserIntent.ADVISORY, max_advisory_score, matched_anchor
            
        # Fallback to factual
        return UserIntent.FACTUAL, max_factual_score, "N/A"

    def get_refusal_response(self, intent):
        """
        Returns compliance-approved refusal messaging based on intent classification.
        """
        if intent == UserIntent.ADVISORY:
            return (
                "I am a facts-only assistant and do not provide investment advice, comparisons, or recommendations. "
                "For educational guidelines on investing, please visit the SEBI Investor Education Portal "
                "(https://investor.sebi.gov.in) or AMFI India (https://www.amfiindia.com)."
            )
        elif intent == UserIntent.OUT_OF_SCOPE:
            return (
                "I am a dedicated Mutual Fund FAQ Assistant trained on 5 specific HDFC schemes. "
                "I cannot assist with unrelated queries. Please ask factual questions like: "
                "'What is the exit load of HDFC Small Cap Fund?'"
            )
        return ""

if __name__ == "__main__":
    # Test suite for intent classification verification
    print("[INFO] Running IntentClassifier test suite...")
    classifier = IntentClassifier()
    
    test_cases = [
        # Factual queries (Expected: FACTUAL)
        "What is the exit load of HDFC Small Cap Fund?",
        "Who manages the HDFC Defence Fund?",
        "What is the minimum SIP amount for the large cap fund?",
        "hi",
        
        # Advisory / Subjective queries (Expected: ADVISORY)
        "Should I invest in HDFC Mid-Cap Opportunities Fund?",
        "Which of these funds should I buy for my daughter?",
        "Can you recommend the best HDFC fund?",
        "HDFC Small Cap vs HDFC Mid Cap - which gives better returns?",
        "Is HDFC Defence Fund a safe choice to invest in?",
        
        # Out of Scope queries (Expected: OUT_OF_SCOPE)
        "Write a python quicksort script",
        "Make a chocolate cake recipe",
        "Who wrote Hamlet?"
    ]
    
    print("\n--- Test Verification Results ---")
    for q in test_cases:
        intent, score, matched = classifier.classify(q)
        print(f"\nQuery: '{q}'")
        print(f"  Classification: \033[1m{intent.value.upper()}\033[0m (Score: {score:.4f})")
        print(f"  Matched Anchor: {matched}")
        if intent != UserIntent.FACTUAL:
            print(f"  Response: {classifier.get_refusal_response(intent)}")
