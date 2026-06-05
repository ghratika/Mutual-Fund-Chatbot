import sys
import unittest
from unittest.mock import MagicMock, patch
from guardrails import count_sentences, validate_response, get_template_fallback_response, GroqGuardrailClient

class TestGuardrails(unittest.TestCase):
    def test_count_sentences(self):
        # Test basic cases
        self.assertEqual(count_sentences("This is sentence one. This is sentence two. This is sentence three."), 3)
        self.assertEqual(count_sentences("Only one sentence here."), 1)
        
        # Test abbreviation bypass
        self.assertEqual(count_sentences("The fund has a NAV of Rs. 10.50. It tracks the index. Contact Mr. Gupta."), 3)
        self.assertEqual(count_sentences("The NAV of Rs.123.45 is updated. This is sentence two."), 2)
        
        # Test decimals in numbers
        self.assertEqual(count_sentences("The expense ratio is 0.73% and it tracks the index."), 1)
        self.assertEqual(count_sentences("The exit load is 1.0% if redeemed within 1 year. The NAV is Rs. 15.3."), 2)
        
    def test_validate_response(self):
        target_url = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        
        # Valid case: <= 3 sentences, exactly one citation matching target_url
        valid_text = (
            "The HDFC Mid Cap Fund has a NAV of Rs.218.882. "
            "Its expense ratio is 0.73%. "
            f"For details, visit {target_url}."
        )
        is_valid, reason = validate_response(valid_text, target_url)
        self.assertTrue(is_valid, f"Failed valid test: {reason}")
        
        # Invalid case: > 3 sentences
        too_long_text = (
            "Sentence one. "
            "Sentence two. "
            "Sentence three. "
            "Sentence four. "
            f"Check details at {target_url}."
        )
        is_valid, reason = validate_response(too_long_text, target_url)
        self.assertFalse(is_valid)
        self.assertIn("exceeds limit", reason)
        
        # Invalid case: no citation
        no_citation = "The fund has a NAV of Rs.218.882. The expense ratio is 0.73%."
        is_valid, reason = validate_response(no_citation, target_url)
        self.assertFalse(is_valid)
        self.assertIn("Expected exactly one URL citation", reason)
        
        # Invalid case: multiple citations
        multiple_citations = (
            f"Check {target_url} and also see {target_url}."
        )
        is_valid, reason = validate_response(multiple_citations, target_url)
        self.assertFalse(is_valid)
        self.assertIn("Expected exactly one URL citation", reason)
        
        # Invalid case: wrong citation
        wrong_citation = "Check details at https://groww.in/mutual-funds/other-fund."
        is_valid, reason = validate_response(wrong_citation, target_url)
        self.assertFalse(is_valid)
        self.assertIn("URL citation mismatch", reason)

    def test_fallback_response(self):
        metrics = {
            "scheme_name": "HDFC Mid Cap Fund Direct Growth",
            "nav": "218.882",
            "nav_date": "04-Jun-2026",
            "expense_ratio": "0.73",
            "exit_load": "1% for redemption within 1 year",
            "min_sip": "100",
            "riskometer": "Very High",
            "benchmark": "NIFTY Midcap 150 TRI",
            "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "aum": "94744.7175",
            "return_1m": "0.65",
            "return_6m": "-1.93",
            "return_1y": "5.51"
        }
        fallback = get_template_fallback_response(metrics)
        
        # Verify sentence count
        self.assertEqual(count_sentences(fallback), 3)
        
        # Verify validation pass
        is_valid, reason = validate_response(fallback, metrics["url"])
        self.assertTrue(is_valid, f"Fallback validation failed: {reason}")
        
    @patch('guardrails.Groq')
    def test_groq_client_fallback_on_api_error(self, mock_groq_class):
        # Force API call error
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_groq_class.return_value = mock_client
        
        metrics = {
            "scheme_name": "HDFC Mid Cap Fund Direct Growth",
            "nav": "218.882",
            "nav_date": "04-Jun-2026",
            "expense_ratio": "0.73",
            "exit_load": "1% for redemption within 1 year",
            "min_sip": "100",
            "riskometer": "Very High",
            "benchmark": "NIFTY Midcap 150 TRI",
            "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "aum": "94744.7175",
            "return_1m": "0.65",
            "return_6m": "-1.93",
            "return_1y": "5.51"
        }
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'dummy_key'}):
            client = GroqGuardrailClient()
            response = client.generate_response("What is the NAV?", "Context", metrics)
            
            # The response should include the fallback text and last updated footer
            self.assertIn("218.882", response)
            self.assertIn("Last updated from sources: 04-Jun-2026", response)
            
    @patch('guardrails.Groq')
    def test_groq_client_validation_pass(self, mock_groq_class):
        target_url = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        llm_output = f"The NAV is Rs.218.882. The expense ratio is 0.73%. More details at {target_url}."
        
        # Setup mock client
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = llm_output
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq_class.return_value = mock_client
        
        metrics = {
            "scheme_name": "HDFC Mid Cap Fund Direct Growth",
            "nav": "218.882",
            "nav_date": "04-Jun-2026",
            "expense_ratio": "0.73",
            "exit_load": "1% for redemption within 1 year",
            "min_sip": "100",
            "riskometer": "Very High",
            "benchmark": "NIFTY Midcap 150 TRI",
            "url": target_url,
            "aum": "94744.7175",
            "return_1m": "0.65",
            "return_6m": "-1.93",
            "return_1y": "5.51"
        }
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'dummy_key'}):
            client = GroqGuardrailClient()
            response = client.generate_response("What is the NAV?", "Context", metrics)
            
            self.assertIn("Last updated from sources: 04-Jun-2026", response)
            self.assertIn("218.882", response)
            self.assertIn(target_url, response)

if __name__ == '__main__':
    unittest.main()
