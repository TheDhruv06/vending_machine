"""
Unit test suite to verify the Ayurveda Engine rules, safety lockouts, and 77 combinations.
"""
import unittest
from ayurveda_engine import (
    check_safety_gates,
    calculate_prakriti_and_agni,
    evaluate_user_consultation,
    RECOMMENDATION_MATRIX,
    PRAKRITI_QUESTIONS,
    SYMPTOMS_CATALOG,
    TEA_CATALOG
)

class TestAyurvedaEngine(unittest.TestCase):
    
    def test_safety_gate_pregnancy(self):
        """Test that pregnancy triggers an immediate safety lockout."""
        safe, reason = check_safety_gates(age=28, is_pregnant=True, is_lactating=False)
        self.assertFalse(safe)
        self.assertIn("Safety Lockout: Active pregnancy detected", reason)

    def test_safety_gate_pediatric(self):
        """Test that age under 5 triggers pediatric lockout."""
        safe, reason = check_safety_gates(age=4, is_pregnant=False, is_lactating=False)
        self.assertFalse(safe)
        self.assertIn("under 5 years of age", reason)

    def test_safety_gate_pass(self):
        """Test normal adult passes safety gates."""
        safe, reason = check_safety_gates(age=25, is_pregnant=False, is_lactating=False)
        self.assertTrue(safe)
        self.assertIsNone(reason)

    def test_all_77_combinations_exist_and_resolve(self):
        """Verify that all 77 documented combinations map cleanly to valid teas."""
        prakritis = ["V", "P", "K", "VP", "PK", "VK", "VPK"]
        all_symptoms = []
        for cat, syms in SYMPTOMS_CATALOG.items():
            all_symptoms.extend(syms)
        
        self.assertEqual(len(all_symptoms), 11, "Must have exactly 11 symptoms")
        self.assertEqual(len(RECOMMENDATION_MATRIX), 77, "Must have exactly 77 combinations")

        for prakriti in prakritis:
            for symptom in all_symptoms:
                tea_code = RECOMMENDATION_MATRIX.get((prakriti, symptom))
                self.assertIsNotNone(tea_code, f"Missing mapping for ({prakriti}, {symptom})")
                self.assertIn(tea_code, TEA_CATALOG, f"Invalid tea code {tea_code} returned")

    def test_agni_classification(self):
        """Test that question 3 correctly sets Agni."""
        # 0 -> Vishama Agni
        res = calculate_prakriti_and_agni({"digestion_agni": 0})
        self.assertEqual(res["agni"]["type"], "Vishama Agni")

        # 1 -> Tikshna Agni
        res = calculate_prakriti_and_agni({"digestion_agni": 1})
        self.assertEqual(res["agni"]["type"], "Tikshna Agni")

        # 2 -> Manda Agni
        res = calculate_prakriti_and_agni({"digestion_agni": 2})
        self.assertEqual(res["agni"]["type"], "Manda Agni")

        # 3 -> Sama Agni
        res = calculate_prakriti_and_agni({"digestion_agni": 3})
        self.assertEqual(res["agni"]["type"], "Sama Agni")

if __name__ == "__main__":
    unittest.main()

