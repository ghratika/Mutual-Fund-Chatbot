import sys
from retrieval import MutualFundRetrievalEngine, log_info, log_success, log_error

def test_engine():
    log_info("Initializing MutualFundRetrievalEngine test suite...")
    try:
        engine = MutualFundRetrievalEngine()
    except Exception as e:
        log_error(f"Failed to initialize retrieval engine: {e}")
        sys.exit(1)

    queries = [
        ("What is the exit load of HDFC Small Cap Fund?", "HDFC Small Cap Fund Direct Growth"),
        ("Who manages the HDFC Defence Fund?", "HDFC Defence Fund Direct Growth"),
        ("What is the investment objective of the Gold ETF fund?", "HDFC Gold ETF Fund of Fund Direct Plan Growth"),
        ("What is the expense ratio and NAV of HDFC Mid Cap?", "HDFC Mid Cap Fund Direct Growth")
    ]

    print("\n" + "="*80)
    print(f"{'QUERY':<50} | {'TARGET FUND':<25}")
    print("="*80)

    all_passed = True
    for query, expected_fund in queries:
        print(f"\nQuery: '{query}'")
        print(f"Targeting Scheme: '{expected_fund}'")
        
        # Build prompt context
        context, items = engine.build_prompt_context(query, limit=2)
        
        # Verify isolation: none of the retrieved documents should have metadata of any other scheme
        is_isolated = True
        for item in items:
            ref_scheme = item["metadata"]["scheme_name"]
            if ref_scheme != expected_fund:
                is_isolated = False
                log_error(f"Cross-talk detected! Retrieved chunk from '{ref_scheme}' when expecting '{expected_fund}'")
        
        if is_isolated and len(items) > 0:
            log_success(f"Verification Passed: Chunks correctly isolated to '{expected_fund}'.")
        else:
            log_error("Verification Failed.")
            all_passed = False
            
        print("\n--- SAMPLE CONTEXT PREVIEW ---")
        preview_lines = context.split("\n")[:15]
        for line in preview_lines:
            # Replace rupee symbols for safe console printing on Windows
            safe_line = line.replace("₹", "Rs.")
            print(f"  {safe_line}")
        print("...")
        print("-"*80)

    print("\n" + "="*80)
    if all_passed:
        log_success("All retrieval pre-filtering and isolation tests passed successfully!")
    else:
        log_error("Retrieval test suite finished with errors.")
        sys.exit(1)

if __name__ == "__main__":
    test_engine()
