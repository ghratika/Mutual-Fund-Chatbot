import sys
from intent_classifier import IntentClassifier, log_info, log_success, UserIntent

def run_tests():
    log_info("Starting IntentClassifier test suite...")
    
    try:
        classifier = IntentClassifier()
    except Exception as e:
        print(f"[ERROR] Failed to initialize IntentClassifier: {e}")
        sys.exit(1)
        
    test_cases = [
        # (Query, Expected Route)
        ("should I invest in mid cap or large cap?", UserIntent.ADVISORY),
        ("Which HDFC fund is best for me?", UserIntent.ADVISORY),
        ("What is the NAV of HDFC Mid Cap?", UserIntent.FACTUAL),
        ("Who is managing HDFC Small Cap?", UserIntent.FACTUAL),
        ("HDFC vs SBI", UserIntent.ADVISORY),
        ("give me investment advice", UserIntent.ADVISORY),
        ("What is the expense ratio of gold fund?", UserIntent.FACTUAL),
        ("What is the exit load details for HDFC Defence?", UserIntent.FACTUAL),
        ("Which fund will give me the highest returns next year?", UserIntent.ADVISORY),
        ("Tell me about Chirag Setalvad's experience and education", UserIntent.FACTUAL),
        ("Is it safe to invest in small cap?", UserIntent.ADVISORY),
        ("What is the riskometer of Gold ETF?", UserIntent.FACTUAL),
        ("Recommend a fund for short term growth", UserIntent.ADVISORY),
        ("Write a python quicksort script", UserIntent.OUT_OF_SCOPE),
        ("Make a chocolate cake recipe", UserIntent.OUT_OF_SCOPE)
    ]
    
    failures = 0
    
    print("\n" + "="*80)
    print(f"{'TEST CASE':<50} | {'EXPECTED':<12} | {'ACTUAL':<12} | {'STATUS'}")
    print("="*80)
    
    for query, expected in test_cases:
        try:
            intent, score, matched = classifier.classify(query)
            status = "\033[92mPASS\033[0m" if intent == expected else "\033[91mFAIL\033[0m"
            if intent != expected:
                failures += 1
            print(f"{query[:48]:<50} | {expected.value:<12} | {intent.value:<12} | {status}")
            print(f"  Score: {score:.4f} | Matched Anchor: {matched}")
            print("-"*80)
        except Exception as e:
            print(f"[ERROR] Error testing query '{query}': {e}")
            failures += 1
            
    print("\n" + "="*80)
    if failures == 0:
        log_success("All intent routing test cases passed successfully!")
    else:
        print(f"[ERROR] Test suite finished with {failures} failures.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
