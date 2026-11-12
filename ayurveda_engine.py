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
# 2. AYURVEDIC QUESTIONNAIRE DEFINITIONS (SET 1 CORE + SET 2 POOL)
# ======================================================================================
# As specified in PRAKRITI & AGNI-1.docx:
# - SET 1: 4 Core Questions (Body Frame, Skin, Appetite/Agni, Sleep)
# - SET 2: 9 Questions Pool (Q5 - Q13 in docx). 3 questions are randomly picked for each user.

SET_1_CORE_QUESTIONS = [
    {
        "id": "body_frame",
        "title": "Body Frame & Build",
        "question": "How would you describe your natural body build and frame?",
        "options": [
            {"label": "Thin, lean, bony; difficulty gaining weight", "dosha": "V"},
            {"label": "Medium, well-proportioned, muscular athletic build", "dosha": "P"},
            {"label": "Broad, sturdy, heavy frame; tends to gain weight easily", "dosha": "K"}
        ]
    },
    {
        "id": "skin_texture",
        "title": "Skin Texture & Feel",
        "question": "How does your skin usually look and feel?",
        "options": [
            {"label": "Dry, rough, cool to touch; prone to chapping in dry weather", "dosha": "V"},
            {"label": "Warm, reddish, sensitive; easily reacts to heat and sun", "dosha": "P"},
            {"label": "Soft, smooth, or slightly oily; thick, cool, and well-hydrated", "dosha": "K"}
        ]
    },
    {
        "id": "digestion_agni",
        "title": "Appetite & Digestion (Agni Evaluator)",
        "question": "How is your daily appetite and digestive comfort?",
        "options": [
            {
                "label": "Irregular appetite; prone to gas, bloating, or variable hunger", 
                "dosha": "V", 
                "agni": "Vishama Agni",
                "agni_desc": "Erratic metabolic fire (Vata dominant). Digestion fluctuates unpredictably."
            },
            {
                "label": "Sharp, intense hunger; need meals on time or feel acidic/burning", 
                "dosha": "P", 
                "agni": "Tikshna Agni",
                "agni_desc": "Intense/sharp metabolic fire (Pitta dominant). High acid and enzymatic heat."
            },
            {
                "label": "Slow, mild appetite; feel heavy or sluggish for hours after meals", 
                "dosha": "K", 
                "agni": "Manda Agni",
                "agni_desc": "Slow/sluggish metabolic fire (Kapha dominant). Heavy digestion and slow clearance."
            },
            {
                "label": "Consistent, healthy appetite; digest food smoothly without distress", 
                "dosha": "VPK", 
                "agni": "Sama Agni",
                "agni_desc": "Equilibrated digestive fire. Optimal enzymatic activity and nutrient absorption."
            }
        ]
    },
    {
        "id": "sleep_pattern",
        "title": "Sleep Quality & Habits",
        "question": "How do you typically sleep through the night?",
        "options": [
            {"label": "Light or interrupted sleep; wake up easily with an active mind", "dosha": "V"},
            {"label": "Moderate sound sleep (6–7 hours); wake up feeling refreshed", "dosha": "P"},
            {"label": "Deep, heavy sleep (8+ hours); tend to feel slow or groggy in morning", "dosha": "K"}
        ]
    }
]

SET_2_QUESTION_POOL = [
    {
        "id": "temperament",
        "title": "Mind Under Stress (Docx Q5)",
        "question": "How do you generally respond to sudden pressure or stress?",
        "options": [
            {"label": "Tend to feel anxious, restless, or quick to worry", "dosha": "V"},
            {"label": "Tend to feel irritable, impatient, or intensely focused", "dosha": "P"},
            {"label": "Tend to stay calm, relaxed, patient, and slow to react", "dosha": "K"}
        ]
    },
    {
        "id": "energy_stamina",
        "title": "Energy Levels & Everyday Stamina (Docx Q6)",
        "question": "How would you describe your everyday physical energy and stamina?",
        "options": [
            {"label": "Comes in variable bursts; tire quickly and recharge with rest", "dosha": "V"},
            {"label": "Strong, focused stamina; work with intensity until exhausted", "dosha": "P"},
            {"label": "Steady, enduring stamina; keep moving at a consistent pace all day", "dosha": "K"}
        ]
    },
    {
        "id": "sweating_heat",
        "title": "Sweating & Temperature Sensitivity (Docx Q7)",
        "question": "How sensitive are you to temperature and changing weather?",
        "options": [
            {"label": "Minimal sweating; feel chilly easily and dislike cold/windy weather", "dosha": "V"},
            {"label": "Sweat easily and profusely; dislike heat and direct sun", "dosha": "P"},
            {"label": "Sweat moderately with exertion; dislike cold, damp, or rainy weather", "dosha": "K"}
        ]
    },
    {
        "id": "morning_feeling",
        "title": "Usual Morning Feeling (Docx Q8 / Part 2 Q1)",
        "question": "What is your usual morning feeling when you wake up?",
        "options": [
            {"label": "Energetic but sometimes restless or hurried", "dosha": "V"},
            {"label": "Active, motivated, and ready to start tasks immediately", "dosha": "P"},
            {"label": "Slow to wake up, prefers a relaxed pace, steady afterward", "dosha": "K"}
        ]
    },
    {
        "id": "eating_speed",
        "title": "Usual Eating Speed (Docx Q9 / Part 2 Q2)",
        "question": "What is your usual eating speed during meals?",
        "options": [
            {"label": "Fast, hurried, and sometimes irregular", "dosha": "V"},
            {"label": "Moderate, focused, and steady pace", "dosha": "P"},
            {"label": "Slow, relaxed, and deliberate pace", "dosha": "K"}
        ]
    },
    {
        "id": "body_movement",
        "title": "Body Activity & Movement (Docx Q10 / Part 2 Q3)",
        "question": "How would you describe your general body movements and walking pace?",
        "options": [
            {"label": "Fast movements; talk, walk, and gesture quickly", "dosha": "V"},
            {"label": "Moderate, purposeful, and coordinated movements", "dosha": "P"},
            {"label": "Slow, calm, graceful, and steady movements", "dosha": "K"}
        ]
    },
    {
        "id": "physical_stamina",
        "title": "Physical Stamina Under Exertion (Docx Q11 / Part 2 Q4)",
        "question": "How does your body hold up during sustained physical exertion?",
        "options": [
            {"label": "Gets tired or fatigued quickly after exertion", "dosha": "V"},
            {"label": "Moderate to strong stamina; determined and focused", "dosha": "P"},
            {"label": "High endurance and sustained stamina without feeling drained", "dosha": "K"}
        ]
    },
    {
        "id": "hunger_pattern",
        "title": "Daily Hunger Pattern (Docx Q12 / Part 2 Q5)",
        "question": "How does your hunger develop throughout the day?",
        "options": [
            {"label": "Hunger varies unpredictably throughout the day", "dosha": "V"},
            {"label": "Feels hungry at sharp, regular, and predictable intervals", "dosha": "P"},
            {"label": "Can comfortably delay or skip meals without distress", "dosha": "K"}
        ]
    },
    {
        "id": "memory_retention",
        "title": "Learning & Memory Retention (Docx Q13 / Part 2 Q6)",
        "question": "How do you naturally absorb and recall new information?",
        "options": [
            {"label": "Learns quickly but may forget quickly if not reinforced", "dosha": "V"},
            {"label": "Has sharp, precise, and well-organized memory", "dosha": "P"},
            {"label": "Learns gradually and deliberately, but retains for a very long time", "dosha": "K"}
        ]
    }
]

# Combined lookup map of all questions by ID
ALL_QUESTIONS_MAP = {q["id"]: q for q in (SET_1_CORE_QUESTIONS + SET_2_QUESTION_POOL)}

# Legacy reference for backward compatibility
PRAKRITI_QUESTIONS = SET_1_CORE_QUESTIONS + SET_2_QUESTION_POOL[:3]


# ======================================================================================
# 3. PRAKRITI CALCULATION ENGINE
# ======================================================================================
def calculate_prakriti_and_agni(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes Dosha scores and determines the dominant Prakriti profile and Agni state.
    Evaluates whichever 7 questions (4 core + 3 dynamic pool) were answered by the user.
    """
    scores = {"V": 0, "P": 0, "K": 0}
    agni_result = {
        "type": "Sama Agni",
        "description": "Equilibrated digestive fire (Optimal metabolism)."
    }

    # Evaluate each answered question against our comprehensive question map
    for q_id, chosen_index in answers.items():
        if q_id in ALL_QUESTIONS_MAP and chosen_index is not None and str(chosen_index).isdigit():
            idx = int(chosen_index)
            q_spec = ALL_QUESTIONS_MAP[q_id]
            if 0 <= idx < len(q_spec["options"]):
                chosen_opt = q_spec["options"][idx]
                dosha_tag = chosen_opt.get("dosha")

                # Update dosha points
                if dosha_tag in scores:
                    scores[dosha_tag] += 1
                elif dosha_tag == "VPK":
                    scores["V"] += 1
                    scores["P"] += 1
                    scores["K"] += 1

                # Extract Agni information from digestion_agni question
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
    "General Wellness": [
        "No Issue / I am Fine"
    ],
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
# 5. TEA FORMULATION CATALOG (ACTIVE FORMULATIONS: LEMONGRASS SIP & MEDOHAR SIP)
# ======================================================================================
TEA_CATALOG = {
    "Tea A": {
        "code": "Tea A",
        "name": "Lemongrass Sip",
        "category": "Category A (Soothing Carminative & Vata-Pitta Pacifying)",
        "ingredients": ["Lemongrass"],
        "action": "Gentle carminative & nervous-system calming. Relieves bloating, soothes acidity/heat, calms spasmodic nerve tension, and promotes smooth digestive comfort.",
        "indication": "Bloating, abdominal gas, hyperacidity/burning sensations, nerve discomfort, and calming daily balance."
    },
    "Tea C": {
        "code": "Tea C",
        "name": "MedoHar Sip",
        "category": "Category C (Metabolic Igniter, Scraping & Immunity Boost)",
        "ingredients": ["Jeera", "Sounf", "Lemongrass", "Ajwain", "Dry Ginger (Sunthi)", "Moringa"],
        "action": "Deepana-Pachana, Lekhana & Rasayana (ignites digestive fire, clears ama toxins, relieves congestion/constipation, and fortifies immunity with Moringa).",
        "indication": "Heavy stomach, sluggish digestion, constipation, morning stiffness, cold/cough congestion, low immunity, and energizing daily vitality."
    }
}


# ======================================================================================
# 6. EXACT 84 PERMUTATIONS & COMBINATIONS MATRIX (7 Prakritis x 12 Symptom States)
# ======================================================================================
# Exclusively routes every user assessment to either:
# - "Tea A": Lemongrass Sip (Container 1 / BO Motor 1)
# - "Tea C": MedoHar Sip (Container 2 / BO Motor 2)
RECOMMENDATION_MATRIX = {
    # ------------------ VATA (V) DOMINANT ------------------
    ("V", "No Issue / I am Fine"): "Tea A",
    ("V", "Bloating / Gas"): "Tea A",
    ("V", "Acidity / Burning"): "Tea A",
    ("V", "Heavy Stomach"): "Tea C",
    ("V", "Constipation"): "Tea C",
    ("V", "Back / Nerve Pain"): "Tea A",
    ("V", "Body Ache / Fatigue"): "Tea A",
    ("V", "Joint Swelling"): "Tea A",
    ("V", "Morning Stiffness"): "Tea A",
    ("V", "Cold / Allergies"): "Tea C",
    ("V", "Cough / Congestion"): "Tea C",
    ("V", "Low Immunity"): "Tea C",

    # ------------------ PITTA (P) DOMINANT ------------------
    ("P", "No Issue / I am Fine"): "Tea A",
    ("P", "Bloating / Gas"): "Tea A",
    ("P", "Acidity / Burning"): "Tea A",
    ("P", "Heavy Stomach"): "Tea C",
    ("P", "Constipation"): "Tea C",
    ("P", "Back / Nerve Pain"): "Tea A",
    ("P", "Body Ache / Fatigue"): "Tea A",
    ("P", "Joint Swelling"): "Tea A",
    ("P", "Morning Stiffness"): "Tea C",
    ("P", "Cold / Allergies"): "Tea C",
    ("P", "Cough / Congestion"): "Tea C",
    ("P", "Low Immunity"): "Tea C",

    # ------------------ KAPHA (K) DOMINANT ------------------
    ("K", "No Issue / I am Fine"): "Tea C",
    ("K", "Bloating / Gas"): "Tea C",
    ("K", "Acidity / Burning"): "Tea A",
    ("K", "Heavy Stomach"): "Tea C",
    ("K", "Constipation"): "Tea C",
    ("K", "Back / Nerve Pain"): "Tea C",
    ("K", "Body Ache / Fatigue"): "Tea C",
    ("K", "Joint Swelling"): "Tea C",
    ("K", "Morning Stiffness"): "Tea C",
    ("K", "Cold / Allergies"): "Tea C",
    ("K", "Cough / Congestion"): "Tea C",
    ("K", "Low Immunity"): "Tea C",

    # ------------------ VATA-PITTA (VP) DUAL ------------------
    ("VP", "No Issue / I am Fine"): "Tea A",
    ("VP", "Bloating / Gas"): "Tea A",
    ("VP", "Acidity / Burning"): "Tea A",
    ("VP", "Heavy Stomach"): "Tea C",
    ("VP", "Constipation"): "Tea C",
    ("VP", "Back / Nerve Pain"): "Tea A",
    ("VP", "Body Ache / Fatigue"): "Tea A",
    ("VP", "Joint Swelling"): "Tea A",
    ("VP", "Morning Stiffness"): "Tea A",
    ("VP", "Cold / Allergies"): "Tea C",
    ("VP", "Cough / Congestion"): "Tea C",
    ("VP", "Low Immunity"): "Tea C",

    # ------------------ PITTA-KAPHA (PK) DUAL ------------------
    ("PK", "No Issue / I am Fine"): "Tea A",
    ("PK", "Bloating / Gas"): "Tea C",
    ("PK", "Acidity / Burning"): "Tea A",
    ("PK", "Heavy Stomach"): "Tea C",
    ("PK", "Constipation"): "Tea C",
    ("PK", "Back / Nerve Pain"): "Tea A",
    ("PK", "Body Ache / Fatigue"): "Tea C",
    ("PK", "Joint Swelling"): "Tea A",
    ("PK", "Morning Stiffness"): "Tea C",
    ("PK", "Cold / Allergies"): "Tea C",
    ("PK", "Cough / Congestion"): "Tea C",
    ("PK", "Low Immunity"): "Tea C",

    # ------------------ VATA-KAPHA (VK) DUAL ------------------
    ("VK", "No Issue / I am Fine"): "Tea C",
    ("VK", "Bloating / Gas"): "Tea C",
    ("VK", "Acidity / Burning"): "Tea A",
    ("VK", "Heavy Stomach"): "Tea C",
    ("VK", "Constipation"): "Tea C",
    ("VK", "Back / Nerve Pain"): "Tea A",
    ("VK", "Body Ache / Fatigue"): "Tea C",
    ("VK", "Joint Swelling"): "Tea C",
    ("VK", "Morning Stiffness"): "Tea C",
    ("VK", "Cold / Allergies"): "Tea C",
    ("VK", "Cough / Congestion"): "Tea C",
    ("VK", "Low Immunity"): "Tea C",

    # ------------------ TRIDOSHA (VPK) BALANCED ------------------
    ("VPK", "No Issue / I am Fine"): "Tea C",
    ("VPK", "Bloating / Gas"): "Tea A",
    ("VPK", "Acidity / Burning"): "Tea A",
    ("VPK", "Heavy Stomach"): "Tea C",
    ("VPK", "Constipation"): "Tea C",
    ("VPK", "Back / Nerve Pain"): "Tea A",
    ("VPK", "Body Ache / Fatigue"): "Tea C",
    ("VPK", "Joint Swelling"): "Tea A",
    ("VPK", "Morning Stiffness"): "Tea C",
    ("VPK", "Cold / Allergies"): "Tea C",
    ("VPK", "Cough / Congestion"): "Tea C",
    ("VPK", "Low Immunity"): "Tea C"
}


# ======================================================================================
# CONSTITUTIONAL WELLNESS DETAILS (FOR USERS WITH NO ACUTE ISSUES / SWASTHAVRITTA)
# ======================================================================================
CONSTITUTIONAL_MAINTENANCE_DETAILS = {
    "V": {
        "action": "Lemongrass Vata-Shamana & Nervous Grounding. Delivers gentle carminative warmth to stabilize erratic Vata, calms nervous tension, and sustains smooth, relaxed digestion.",
        "indication": "Daily wellness for Vata constitution: Maintains grounded vitality, internal calm, and smooth digestive balance."
    },
    "P": {
        "action": "Lemongrass Soothing & Pitta Harmonization. Gently refreshes without adding spicy heat, keeps digestion calm, and prevents acid accumulation.",
        "indication": "Daily wellness for Pitta constitution: Maintains cool composure, light digestion, and balanced daily energy."
    },
    "K": {
        "action": "MedoHar Deepana-Pachana & Kapha-Shamana. Powered by Sunthi, Ajwain, Jeera, and Moringa to ignite metabolic Agni, prevent sluggishness, and keep energy vibrant and light.",
        "indication": "Daily wellness for Kapha constitution: Maintains active metabolism, cellular lightness, and sustained daily stamina."
    },
    "VP": {
        "action": "Lemongrass Dual-Dosha Harmonization. Gentle carminative action that pacifies erratic Vata while remaining soothing and light for sensitive Pitta.",
        "indication": "Daily wellness for Vata-Pitta constitution: Balances digestive rhythm, soothes nervous tension, and refreshes the mind."
    },
    "PK": {
        "action": "Lemongrass Pitta-Kapha Refreshment. Keeps digestive fire steady and prevents metabolic heat or stagnation without over-stimulating Pitta.",
        "indication": "Daily wellness for Pitta-Kapha constitution: Sustains clean circulation, digestive harmony, and calm vigor."
    },
    "VK": {
        "action": "MedoHar Warming & Metabolism Boost. Dispels internal coldness with Jeera, Ajwain, and Sunthi while nourishing tissues with Moringa.",
        "indication": "Daily wellness for Vata-Kapha constitution: Counteracts cold tendencies, prevents lethargy, and boosts digestive fire."
    },
    "VPK": {
        "action": "MedoHar Rasayana & Daily Metabolic Vitality. Delivers comprehensive Moringa nutrition paired with balanced digestive spices (Jeera, Sounf, Lemongrass) to fortify Ojas.",
        "indication": "Daily wellness for Sama Dosha (Balanced): Comprehensive cellular nourishment, immune fortification, and all-day vitality."
    }
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
    raw_symptom = payload.get("selected_symptom", "Bloating / Gas")
    
    # Normalize general wellness / no issue choices
    if str(raw_symptom).strip() in [
        "No Issue / I am Fine",
        "No Issue / Feeling Healthy",
        "No Issues / I'm Feeling Fine",
        "No Issues / I am Fine",
        "No Issue",
        "None",
        "Healthy Baseline",
        "I am fine",
        "i am fine"
    ]:
        selected_symptom = "No Issue / I am Fine"
    else:
        selected_symptom = raw_symptom
    
    # Retrieve recommended tea from matrix (84 combinations)
    tea_code = RECOMMENDATION_MATRIX.get((dominant_prakriti, selected_symptom))
    
    # Fallback safety default if unmatched
    if not tea_code:
        tea_code = "Tea A"

    tea_details = TEA_CATALOG.get(tea_code, TEA_CATALOG["Tea A"])

    # If user has no acute symptoms, tailor clinical action and indication for constitutional maintenance (Swasthavritta)
    if selected_symptom == "No Issue / I am Fine":
        const_info = CONSTITUTIONAL_MAINTENANCE_DETAILS.get(
            dominant_prakriti, 
            CONSTITUTIONAL_MAINTENANCE_DETAILS["VPK"]
        )
        clinical_action = const_info["action"]
        primary_indication = const_info["indication"]
    else:
        clinical_action = tea_details["action"]
        primary_indication = tea_details["indication"]

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
            "clinical_action": clinical_action,
            "primary_indication": primary_indication,
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

