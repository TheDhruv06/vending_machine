"""
========================================================================================
SOILVEDA ORGANICS - AYURVEDIC INTELLIGENCE ENGINE (MODEL)
========================================================================================
This module serves as the core clinical decision engine for the AI-Driven Vending Machine.
It translates ancient Ayurvedic diagnostic principles (Prakriti, Agni, and Vikriti) 
into a deterministic, robust, and reproducible recommendation model.

Core Principles Implemented:
1. Phase 1: Screening & Safety Gates (Age < 5 lockout, Pregnancy lockout)
2. Phase 2: Prakriti (Dosha constitution) & Agni (Digestive Fire) Assessment
3. Phase 3: Vikriti (Acute symptom mapping across Stomach, Pain, Chest/Cold)
4. Phase 4: Deterministic 77-combination rule matrix dispensing Teas A through F
========================================================================================
"""

from typing import Dict, List, Tuple, Any, Optional

# ======================================================================================
# 1. SAFETY GATES & SCREENING RULES
# ======================================================================================
def check_safety_gates(age: int, is_pregnant: bool, is_lactating: bool) -> Tuple[bool, Optional[str]]:
    """
    Evaluates safety gates before allowing the user to proceed.
    
    Ayurvedic medicines and potent herbal decoctions (Kashayas) require direct 
    physician supervision during pregnancy and early childhood.
    
    Returns:
        (is_safe: bool, lockout_message: Optional[str])
    """
    # Safety Gate 1: Pregnancy Lockout
    if is_pregnant:
        return (
            False,
            "Safety Lockout: Active pregnancy detected. Potent herbal decoctions and "
            "active botanical compounds can stimulate uterine contractions or alter physiology. "
            "Please consult the clinical desk for specialized prenatal care."
        )

    # Safety Gate 2: Pediatric Age Restriction (Under 5 years)
    if age < 5:
        return (
            False,
            "Safety Lockout: Patient is under 5 years of age. Pediatric formulations require "
            "precise weight-adjusted dosing under direct medical supervision."
        )

    # All safety checks passed
    return (True, None)


# ======================================================================================
# 2. AYURVEDIC QUESTIONNAIRE DEFINITIONS (PRAKRITI & AGNI)
# ======================================================================================
# The questionnaire follows the standard 7-question clinical assessment covering:
# 1. Body Frame (Vata = lean, Pitta = medium, Kapha = broad)
# 2. Skin Texture (Vata = dry, Pitta = warm/oily, Kapha = soft/moist)
# 3. Appetite & Digestion (Identifies Agni: Vishama, Tikshna, Manda, Sama)
# 4. Sleep Pattern (Vata = light/erratic, Pitta = moderate, Kapha = deep/heavy)
# 5. Temperament / Stress Response (Vata = anxious, Pitta = irritable, Kapha = calm)
# 6. Physical Stamina & Energy (Vata = variable, Pitta = strong, Kapha = steady)
# 7. Sweating & Body Temperature (Vata = minimal/cold, Pitta = excessive/hot, Kapha = slow/cool)

PRAKRITI_QUESTIONS = [
    {
        "id": "body_frame",
        "title": "1. Body Frame & Build",
        "options": [
            {"label": "Thin, lean, bony, difficulties gaining weight", "dosha": "V"},
            {"label": "Medium, well-proportioned, muscular build", "dosha": "P"},
            {"label": "Broad, sturdy, heavy frame, tends to gain weight easily", "dosha": "K"}
        ]
    },
    {
        "id": "skin_texture",
        "title": "2. Skin Texture & Feel",
        "options": [
            {"label": "Dry, rough, cool to touch, prone to chapping", "dosha": "V"},
            {"label": "Warm, reddish, sensitive, prone to freckles/rashes", "dosha": "P"},
            {"label": "Soft, oily, smooth, cool, thick skin", "dosha": "K"}
        ]
    },
    {
        "id": "digestion_agni",
        "title": "3. Appetite & Digestion (Agni Type)",
        "description": "Crucial Ayurvedic parameter indicating the strength of your metabolic fire.",
        "options": [
            {
                "label": "Irregular appetite, gas/bloating, sometimes constipated", 
                "dosha": "V", 
                "agni": "Vishama Agni",
                "agni_desc": "Erratic metabolic fire (Vata dominant). Digestion fluctuates unpredictably."
            },
            {
                "label": "Intense/sharp appetite, must eat on time, acidic burning if meal missed", 
                "dosha": "P", 
                "agni": "Tikshna Agni",
                "agni_desc": "Intense/sharp metabolic fire (Pitta dominant). High acid and bile secretion."
            },
            {
                "label": "Slow appetite, can skip meals easily, feeling heavy or sluggish after eating", 
                "dosha": "K", 
                "agni": "Manda Agni",
                "agni_desc": "Slow/sluggish metabolic fire (Kapha dominant). Heavy digestion and slow clearance."
            },
            {
                "label": "Balanced, consistent appetite, comfortable digestion without distress", 
                "dosha": "VPK", 
                "agni": "Sama Agni",
                "agni_desc": "Equilibrated digestive fire. Optimal enzymatic activity and nutrient absorption."
            }
        ]
    },
    {
        "id": "sleep_pattern",
        "title": "4. Sleep Quality",
        "options": [
            {"label": "Light, interrupted, tends to wake up easily or think excessively", "dosha": "V"},
            {"label": "Moderate (6-7 hrs), sound sleep, wakes up alert", "dosha": "P"},
            {"label": "Deep, heavy, prolonged (8+ hrs), feels slow or groggy in morning", "dosha": "K"}
        ]
    },
    {
        "id": "temperament",
        "title": "5. Mind Under Stress & Temperament",
        "options": [
            {"label": "Anxious, restless, overthinking, quick to worry", "dosha": "V"},
            {"label": "Sharp, ambitious, irritable or impatient when challenged", "dosha": "P"},
            {"label": "Calm, patient, unbothered, takes time to react or change", "dosha": "K"}
        ]
    },
    {
        "id": "energy_stamina",
        "title": "6. Energy Levels & Stamina",
        "options": [
            {"label": "Variable in bursts; tires quickly and recovers with rest", "dosha": "V"},
            {"label": "Strong, focused, high endurance until exhausted", "dosha": "P"},
            {"label": "Steady, consistent, sustained endurance throughout the day", "dosha": "K"}
        ]
    },
    {
        "id": "sweating_heat",
        "title": "7. Sweating & Thermal Sensitivity",
        "options": [
            {"label": "Minimal sweating, dislikes cold and windy weather", "dosha": "V"},
            {"label": "Sweats easily and profusely, dislikes hot weather", "dosha": "P"},
            {"label": "Moderate sweat with exertion, dislikes cold and damp/rainy weather", "dosha": "K"}
        ]
    }
]


# ======================================================================================
# 3. PRAKRITI CALCULATION ENGINE
# ======================================================================================
def calculate_prakriti_and_agni(answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Computes Dosha scores and determines the dominant Prakriti profile and Agni state.
    
    Prakriti Classification:
      - Single Dosha: V (Vata), P (Pitta), K (Kapha)
      - Dual Dosha: VP (Vata-Pitta), PK (Pitta-Kapha), VK (Vata-Kapha)
      - Tridoshic: VPK (Vata-Pitta-Kapha equilibrium)
      
    Agni Classification:
      - Vishama Agni (Vata)
      - Tikshna Agni (Pitta)
      - Manda Agni (Kapha)
      - Sama Agni (Balanced)
    """
    # Tally scores
    scores = {"V": 0, "P": 0, "K": 0}
    agni_result = {
        "type": "Sama Agni",
        "description": "Equilibrated digestive fire (Optimal metabolism)."
    }

    # Evaluate each question answer
    for q in PRAKRITI_QUESTIONS:
        q_id = q["id"]
        chosen_index = answers.get(q_id)
        
        if chosen_index is not None and str(chosen_index).isdigit():
            idx = int(chosen_index)
            if 0 <= idx < len(q["options"]):
                chosen_opt = q["options"][idx]
                dosha_tag = chosen_opt.get("dosha")
                
                # Update dosha points
                if dosha_tag in scores:
                    scores[dosha_tag] += 1
                elif dosha_tag == "VPK":
                    # Balanced option contributes equally
                    scores["V"] += 1
                    scores["P"] += 1
                    scores["K"] += 1
                
                # Extract Agni information from Question 3
                if q_id == "digestion_agni":
                    agni_result["type"] = chosen_opt.get("agni", "Sama Agni")
                    agni_result["description"] = chosen_opt.get("agni_desc", "")

    # Calculate total and percentages
    v_score = scores["V"]
    p_score = scores["P"]
    k_score = scores["K"]

    # Determine dominant Prakriti tag
    # Sort descending
    sorted_doshas = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_dosha, top_val = sorted_doshas[0]
    second_dosha, second_val = sorted_doshas[1]
    third_dosha, third_val = sorted_doshas[2]

    # Classification logic:
    # 1. Tridosha if all three are equal or within 1 point of each other
    if (top_val - third_val) <= 1:
        dominant_prakriti = "VPK"
        prakriti_label = "Sama Dosha (Vata-Pitta-Kapha Balanced)"
    # 2. Dual dosha if top two are tied or within 1 point of each other
    elif (top_val - second_val) <= 1:
        pair = sorted([top_dosha, second_dosha])
        # Standardize representation: VP, PK, VK
        pair_code = "".join(pair)
        if pair_code == "PV":
            pair_code = "VP"
        elif pair_code == "KP":
            pair_code = "PK"
        elif pair_code == "KV":
            pair_code = "VK"
        dominant_prakriti = pair_code
        
        labels = {
            "VP": "Vata-Pitta Prakriti",
            "PK": "Pitta-Kapha Prakriti",
            "VK": "Vata-Kapha Prakriti"
        }
        prakriti_label = labels.get(dominant_prakriti, f"{dominant_prakriti} Prakriti")
    # 3. Single dominant dosha
    else:
        dominant_prakriti = top_dosha
        labels = {
            "V": "Vata Dominant Prakriti",
            "P": "Pitta Dominant Prakriti",
            "K": "Kapha Dominant Prakriti"
        }
        prakriti_label = labels.get(dominant_prakriti, f"{dominant_prakriti} Prakriti")

    return {
        "scores": scores,
        "dominant_prakriti": dominant_prakriti,
        "prakriti_label": prakriti_label,
        "agni": agni_result
    }


# ======================================================================================
# 4. VIKRITI (SYMPTOM MENU) DEFINITION
# ======================================================================================
SYMPTOMS_CATALOG = {
    "Stomach": [
        "Bloating / Gas",
        "Acidity / Burning",
        "Heavy Stomach",
        "Constipation"
    ],
    "Pain": [
        "Back / Nerve Pain",
        "Body Ache / Fatigue",
        "Joint Swelling",
        "Morning Stiffness"
    ],
    "Chest & Cold": [
        "Cold / Allergies",
        "Cough / Congestion",
        "Low Immunity"
    ]
}


# ======================================================================================
# 5. TEA FORMULATION CATALOG (6 TEAS)
# ======================================================================================
TEA_CATALOG = {
    "Tea A": {
        "code": "Tea A",
        "name": "Lemongrass Sip",
        "category": "Category A (Vata-Hara / Digestive & Carminative)",
        "ingredients": ["Lemongrass"],
        "action": "Carminative & Vata-pacifying. Calms gut spasms, expels trapped abdominal gas, and eases nervous tension.",
        "indication": "Bloating, abdominal distension, sharp spasmodic pains, and morning stiffness."
    },
    "Tea B": {
        "code": "Tea B",
        "name": "Vital Sip",
        "category": "Category B (Pitta-Hara / Cooling & Anti-inflammatory)",
        "ingredients": ["Arjun Bark (Terminalia arjuna)"],
        "action": "Deeply cooling (Sheeta Virya), cardiotonic (Hridya), and anti-inflammatory. Neutralizes pitta heat and soothes vascular inflammation.",
        "indication": "Hyperacidity, heartburn, burning sensations, inflammatory joint swelling, and excessive metabolic heat."
    },
    "Tea C": {
        "code": "Tea C",
        "name": "MedoHar Sip",
        "category": "Category C (Kapha-Hara / Stimulating & Scraping)",
        "ingredients": ["Jeera", "Sounf", "Lemongrass", "Ajwain", "Dry Ginger (Sunthi)", "Moringa"],
        "action": "Deepana-Pachana & Lekhana (metabolism stimulating and fat/toxin scraping). Clears ama (undigested toxins) and reduces heaviness.",
        "indication": "Sluggish digestion, heaviness in the stomach, lethargy, dull aches, and morning joint stiffness."
    },
    "Tea D": {
        "code": "Tea D",
        "name": "Mangalayu Tea",
        "category": "Category D (Vata-Anulomana / Mild Laxative & Gut Regularizer)",
        "ingredients": ["Tea Leaves", "Dry Ginger", "Elaichi", "Bay Leaf", "Rose Petals", "Aprajita", "Lemongrass"],
        "action": "Vata-Anulomana (directing Vata downwards). Softens stools, balances intestinal peristalsis, and restores regular bowel motility.",
        "indication": "Constipation, dry stool passage, and irregular downward elimination."
    },
    "Tea E": {
        "code": "Tea E",
        "name": "Moringa Sip",
        "category": "Category E (Rasayana / Immunity Boost & Vitalizer)",
        "ingredients": ["Moringa Leaf"],
        "action": "Rasayana (rejuvenative) & Dhatu-poshaka (tissue nourishing). Rich in micronutrients, enhances Ojas (vital immunity), and fights chronic exhaustion.",
        "indication": "Low immunity, generalized fatigue, body ache, and depleted vitality."
    },
    "Tea F": {
        "code": "Tea F",
        "name": "Green Sip",
        "category": "Category F (Pranavaha / Respiratory Support & Antitussive)",
        "ingredients": [
            "Jeera", "Sounf", "Lemongrass", "Ajwain", "Dry Ginger", 
            "Moringa", "Rose", "Elaichi", "Black Pepper", "Tulsi", "Bay Leaf"
        ],
        "action": "Pranavaha Srotas clearing (clears respiratory channels), liquefies kapha mucus, eases airway spasms, and boosts respiratory defenses.",
        "indication": "Acute cough, cold, nasal congestion, seasonal allergies, and chest heaviness."
    }
}


# ======================================================================================
# 6. EXACT 77 PERMUTATIONS & COMBINATIONS MATRIX
# ======================================================================================
# As defined in the official specification document:
# 7 Prakriti states (V, P, K, VP, PK, VK, VPK) x 11 Symptoms = 77 exact mappings
RECOMMENDATION_MATRIX = {
    # ------------------ VATA (V) DOMINANT ------------------
    ("V", "Bloating / Gas"): "Tea A",
    ("V", "Acidity / Burning"): "Tea B",
    ("V", "Heavy Stomach"): "Tea A",
    ("V", "Constipation"): "Tea D",
    ("V", "Back / Nerve Pain"): "Tea A",
    ("V", "Body Ache / Fatigue"): "Tea E",
    ("V", "Joint Swelling"): "Tea B",
    ("V", "Morning Stiffness"): "Tea A",
    ("V", "Cold / Allergies"): "Tea F",
    ("V", "Cough / Congestion"): "Tea F",
    ("V", "Low Immunity"): "Tea E",

    # ------------------ PITTA (P) DOMINANT ------------------
    ("P", "Bloating / Gas"): "Tea A",
    ("P", "Acidity / Burning"): "Tea B",
    ("P", "Heavy Stomach"): "Tea C",
    ("P", "Constipation"): "Tea D",
    ("P", "Back / Nerve Pain"): "Tea A",
    ("P", "Body Ache / Fatigue"): "Tea E",
    ("P", "Joint Swelling"): "Tea B",
    ("P", "Morning Stiffness"): "Tea C",
    ("P", "Cold / Allergies"): "Tea E",
    ("P", "Cough / Congestion"): "Tea F",
    ("P", "Low Immunity"): "Tea E",

    # ------------------ KAPHA (K) DOMINANT ------------------
    ("K", "Bloating / Gas"): "Tea C",
    ("K", "Acidity / Burning"): "Tea B",
    ("K", "Heavy Stomach"): "Tea C",
    ("K", "Constipation"): "Tea D",
    ("K", "Back / Nerve Pain"): "Tea C",
    ("K", "Body Ache / Fatigue"): "Tea C",
    ("K", "Joint Swelling"): "Tea C",
    ("K", "Morning Stiffness"): "Tea C",
    ("K", "Cold / Allergies"): "Tea F",
    ("K", "Cough / Congestion"): "Tea F",
    ("K", "Low Immunity"): "Tea E",

    # ------------------ VATA-PITTA (VP) DUAL ------------------
    ("VP", "Bloating / Gas"): "Tea A",
    ("VP", "Acidity / Burning"): "Tea B",
    ("VP", "Heavy Stomach"): "Tea A",
    ("VP", "Constipation"): "Tea D",
    ("VP", "Back / Nerve Pain"): "Tea A",
    ("VP", "Body Ache / Fatigue"): "Tea E",
    ("VP", "Joint Swelling"): "Tea B",
    ("VP", "Morning Stiffness"): "Tea A",
    ("VP", "Cold / Allergies"): "Tea F",
    ("VP", "Cough / Congestion"): "Tea F",
    ("VP", "Low Immunity"): "Tea E",

    # ------------------ PITTA-KAPHA (PK) DUAL ------------------
    ("PK", "Bloating / Gas"): "Tea C",
    ("PK", "Acidity / Burning"): "Tea B",
    ("PK", "Heavy Stomach"): "Tea C",
    ("PK", "Constipation"): "Tea D",
    ("PK", "Back / Nerve Pain"): "Tea B",
    ("PK", "Body Ache / Fatigue"): "Tea C",
    ("PK", "Joint Swelling"): "Tea B",
    ("PK", "Morning Stiffness"): "Tea C",
    ("PK", "Cold / Allergies"): "Tea F",
    ("PK", "Cough / Congestion"): "Tea F",
    ("PK", "Low Immunity"): "Tea E",

    # ------------------ VATA-KAPHA (VK) DUAL ------------------
    ("VK", "Bloating / Gas"): "Tea A",
    ("VK", "Acidity / Burning"): "Tea B",
    ("VK", "Heavy Stomach"): "Tea C",
    ("VK", "Constipation"): "Tea D",
    ("VK", "Back / Nerve Pain"): "Tea A",
    ("VK", "Body Ache / Fatigue"): "Tea C",
    ("VK", "Joint Swelling"): "Tea C",
    ("VK", "Morning Stiffness"): "Tea C",
    ("VK", "Cold / Allergies"): "Tea F",
    ("VK", "Cough / Congestion"): "Tea F",
    ("VK", "Low Immunity"): "Tea E",

    # ------------------ TRIDOSHA (VPK) BALANCED ------------------
    ("VPK", "Bloating / Gas"): "Tea A",
    ("VPK", "Acidity / Burning"): "Tea B",
    ("VPK", "Heavy Stomach"): "Tea C",
    ("VPK", "Constipation"): "Tea D",
    ("VPK", "Back / Nerve Pain"): "Tea A",
    ("VPK", "Body Ache / Fatigue"): "Tea E",
    ("VPK", "Joint Swelling"): "Tea B",
    ("VPK", "Morning Stiffness"): "Tea C",
    ("VPK", "Cold / Allergies"): "Tea F",
    ("VPK", "Cough / Congestion"): "Tea F",
    ("VPK", "Low Immunity"): "Tea E"
}


# ======================================================================================
# 7. MAIN CLINICAL EVALUATION PIPELINE
# ======================================================================================
def evaluate_user_consultation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Primary interface for the Vending Machine Model.
    
    Accepts:
      {
        "age": int,
        "gender": str ("Male", "Female", "Other"),
        "is_pregnant": bool,
        "is_lactating": bool,
        "prakriti_answers": {"body_frame": 0, "skin_texture": 1, ...},
        "selected_symptom": "Bloating / Gas"
      }
      
    Returns:
      Comprehensive evaluation payload containing safety status, 
      Prakriti breakdown, Agni diagnosis, and the prescribed Tea.
    """
    age = int(payload.get("age", 25))
    is_pregnant = bool(payload.get("is_pregnant", False))
    is_lactating = bool(payload.get("is_lactating", False))

    # Step 1: Safety Gate Check
    is_safe, lockout_reason = check_safety_gates(age, is_pregnant, is_lactating)
    if not is_safe:
        return {
            "status": "LOCKED",
            "is_safe": False,
            "lockout_message": lockout_reason,
            "prescription": None
        }

    # Step 2: Prakriti & Agni Assessment
    prakriti_answers = payload.get("prakriti_answers", {})
    prakriti_result = calculate_prakriti_and_agni(prakriti_answers)
    dominant_prakriti = prakriti_result["dominant_prakriti"]

    # Step 3: Vikriti (Symptom) & Recommendation Matrix Lookup
    selected_symptom = payload.get("selected_symptom", "Bloating / Gas")
    
    # Retrieve recommended tea from matrix
    tea_code = RECOMMENDATION_MATRIX.get((dominant_prakriti, selected_symptom))
    
    # Fallback safety default if unmatched
    if not tea_code:
        tea_code = "Tea A"

    tea_details = TEA_CATALOG.get(tea_code, TEA_CATALOG["Tea A"])

    # Step 4: Construct Full Prescriptive Output
    return {
        "status": "APPROVED",
        "is_safe": True,
        "lockout_message": None,
        "demographics": {
            "age": age,
            "gender": payload.get("gender", "Unspecified"),
            "is_lactating": is_lactating
        },
        "diagnosis": {
            "dominant_prakriti": dominant_prakriti,
            "prakriti_label": prakriti_result["prakriti_label"],
            "dosha_scores": prakriti_result["scores"],
            "agni": prakriti_result["agni"],
            "selected_symptom": selected_symptom
        },
        "prescription": {
            "tea_code": tea_code,
            "tea_name": tea_details["name"],
            "category": tea_details["category"],
            "ingredients": tea_details["ingredients"],
            "clinical_action": tea_details["action"],
            "primary_indication": tea_details["indication"],
            "vending_instructions": {
                "ratio": "1 Part Powder : 16 Parts Water (Standard Kashaya decoction)",
                "boiling_cycle": "Reduced to 1/4th volume in boiler",
                "dispense_temperature": "Warm (~55°C - 65°C)",
                "volume": "100 ml - 150 ml standard cup"
            }
        }
    }


if __name__ == "__main__":
    # Quick self-test demonstration
    test_payload = {
        "age": 28,
        "gender": "Female",
        "is_pregnant": False,
        "is_lactating": False,
        "prakriti_answers": {
            "body_frame": 0,      # Vata
            "skin_texture": 0,    # Vata
            "digestion_agni": 0,  # Vishama Agni (Vata)
            "sleep_pattern": 0,   # Vata
            "temperament": 1,     # Pitta
            "energy_stamina": 0,  # Vata
            "sweating_heat": 0    # Vata
        },
        "selected_symptom": "Bloating / Gas"
    }
    result = evaluate_user_consultation(test_payload)
    print("Self-Test Result:")
    print("Dominant Prakriti:", result["diagnosis"]["dominant_prakriti"])
    print("Agni State:", result["diagnosis"]["agni"]["type"])
    print("Prescribed Tea:", result["prescription"]["tea_name"])

