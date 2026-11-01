"""
========================================================================================
SOILVEDA ORGANICS - PERMUTATION DATASET GENERATOR
========================================================================================
Generates an exhaustive dataset of all possible question response combinations (2,916)
multiplied across all 11 acute symptoms (32,076 total permutations).

For each permutation, the dataset computes:
- Vata, Pitta, Kapha point tallies
- Dominant Prakriti (V, P, K, VP, PK, VK, VPK)
- Metabolic Fire State (Agni: Vishama, Tikshna, Manda, Sama)
- Prescribed Herbal Tea formulation (Tea A, B, C, D, E, F)
- Complete ingredients & clinical rationale
- Dedicated validation columns (Doctor_Verdict, Doctor_Corrected_Tea, Doctor_Clinical_Notes)
  specifically designed for model evaluation, error identification, and retraining.

Exports:
1. 'ayurveda_model_permutations.xlsx' (Multi-sheet styled Excel workbook)
2. 'ayurveda_model_permutations.csv' (Complete 32,076 row CSV dataset)
3. 'ayurveda_77_decision_matrix.csv' (Core 77-combination clinical matrix)
========================================================================================
"""

import itertools
import time
import os
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from ayurveda_engine import (
    calculate_prakriti_and_agni,
    RECOMMENDATION_MATRIX,
    SYMPTOMS_CATALOG,
    TEA_CATALOG,
    CONSTITUTIONAL_MAINTENANCE_DETAILS,
    SET_1_CORE_QUESTIONS,
    SET_2_QUESTION_POOL
)

# Text labels for options to make the spreadsheet readable
LABELS_Q1 = {
    0: "Thin / Slender (Vata)",
    1: "Medium / Muscular (Pitta)",
    2: "Broad / Heavy (Kapha)"
}

LABELS_Q2 = {
    0: "Dry / Rough (Vata)",
    1: "Warm / Sensitive (Pitta)",
    2: "Soft / Oily (Kapha)"
}

LABELS_Q3 = {
    0: "Irregular (Vishama Agni)",
    1: "Sharp / Intense (Tikshna Agni)",
    2: "Slow / Heavy (Manda Agni)",
    3: "Balanced (Sama Agni)"
}

LABELS_Q4 = {
    0: "Light / Interrupted (Vata)",
    1: "Moderate 6-7h (Pitta)",
    2: "Deep / Heavy 8h+ (Kapha)"
}

LABELS_DYNAMIC = {
    0: "Vata Trait (+1 V)",
    1: "Pitta Trait (+1 P)",
    2: "Kapha Trait (+1 K)"
}


def generate_all_datasets():
    print("Starting generation of Ayurvedic Permutations & Combinations dataset...")
    start_time = time.time()

    # 1. Generate all 2,916 question combinations
    # Q1: 3 options, Q2: 3 options, Q3: 4 options, Q4: 3 options, Q5: 3 options, Q6: 3 options, Q7: 3 options
    q_ranges = [
        [0, 1, 2],       # Q1 Body
        [0, 1, 2],       # Q2 Skin
        [0, 1, 2, 3],    # Q3 Agni
        [0, 1, 2],       # Q4 Sleep
        [0, 1, 2],       # Q5 Trait 1
        [0, 1, 2],       # Q6 Trait 2
        [0, 1, 2]        # Q7 Trait 3
    ]
    question_vectors = list(itertools.product(*q_ranges))
    print(f"Generated {len(question_vectors)} distinct question response vectors.")

    # Flatten symptoms
    symptom_list = []
    for cat, items in SYMPTOMS_CATALOG.items():
        for item in items:
            symptom_list.append((cat, item))
    print(f"Loaded {len(symptom_list)} acute symptoms.")

    total_expected_rows = len(question_vectors) * len(symptom_list)
    print(f"Total rows to generate: {total_expected_rows}")

    # Pre-compute Prakriti & Agni for each of the 2,916 question vectors
    profile_cache = []
    for q_idx, (q1, q2, q3, q4, q5, q6, q7) in enumerate(question_vectors):
        answers = {
            "body_frame": q1,
            "skin_texture": q2,
            "digestion_agni": q3,
            "sleep_pattern": q4,
            "temperament": q5,
            "energy_stamina": q6,
            "sweating_heat": q7
        }
        res = calculate_prakriti_and_agni(answers)
        profile_cache.append({
            "vector_id": f"VEC_{q_idx+1:04d}",
            "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5, "q6": q6, "q7": q7,
            "scores": res["scores"],
            "dominant_prakriti": res["dominant_prakriti"],
            "prakriti_label": res["prakriti_label"],
            "agni_type": res["agni"]["type"],
            "agni_desc": res["agni"]["description"]
        })

    # Build the full 32,076 row records
    full_rows = []
    row_counter = 1

    for prof in profile_cache:
        dom_prakriti = prof["dominant_prakriti"]

        for (sym_cat, sym_name) in symptom_list:
            tea_code = RECOMMENDATION_MATRIX.get((dom_prakriti, sym_name), "Tea A")
            tea_spec = TEA_CATALOG.get(tea_code, TEA_CATALOG["Tea A"])

            # Use tailored Swasthavritta maintenance action for No Issue consultations
            if sym_name == "No Issue / I am Fine":
                const_spec = CONSTITUTIONAL_MAINTENANCE_DETAILS.get(dom_prakriti, CONSTITUTIONAL_MAINTENANCE_DETAILS["VPK"])
                clinical_action = const_spec["action"]
            else:
                clinical_action = tea_spec["action"]

            full_rows.append({
                "Row_ID": row_counter,
                "Profile_ID": prof["vector_id"],
                "Q1_Body_Build": LABELS_Q1[prof["q1"]],
                "Q2_Skin_Texture": LABELS_Q2[prof["q2"]],
                "Q3_Appetite_Agni": LABELS_Q3[prof["q3"]],
                "Q4_Sleep_Habits": LABELS_Q4[prof["q4"]],
                "Q5_Dynamic_Trait_1": LABELS_DYNAMIC[prof["q5"]],
                "Q6_Dynamic_Trait_2": LABELS_DYNAMIC[prof["q6"]],
                "Q7_Dynamic_Trait_3": LABELS_DYNAMIC[prof["q7"]],
                "Vata_Score": prof["scores"]["V"],
                "Pitta_Score": prof["scores"]["P"],
                "Kapha_Score": prof["scores"]["K"],
                "Dominant_Prakriti": dom_prakriti,
                "Prakriti_Classification": prof["prakriti_label"],
                "Agni_State": prof["agni_type"],
                "Symptom_Category": sym_cat,
                "Selected_Symptom": sym_name,
                "Recommended_Tea_Code": tea_code,
                "Recommended_Tea_Name": tea_spec["name"],
                "Tea_Category": tea_spec["category"],
                "Herbal_Ingredients": ", ".join(tea_spec["ingredients"]),
                "Clinical_Action": clinical_action,
                "Doctor_Verdict": "APPROVED",
                "Doctor_Corrected_Tea": "",
                "Doctor_Clinical_Notes": ""
            })
            row_counter += 1

    df_full = pd.DataFrame(full_rows)

    # 2. Build the 84 Decision Rules Table (7 Prakritis x 12 Symptoms)
    rules_84 = []
    for (prakriti, symptom), tea_code in RECOMMENDATION_MATRIX.items():
        tea_spec = TEA_CATALOG.get(tea_code)
        # Find category
        sym_category = "General"
        for cat, items in SYMPTOMS_CATALOG.items():
            if symptom in items:
                sym_category = cat
                break

        prakriti_names = {
            "V": "Vata Dominant",
            "P": "Pitta Dominant",
            "K": "Kapha Dominant",
            "VP": "Vata-Pitta Dual",
            "PK": "Pitta-Kapha Dual",
            "VK": "Vata-Kapha Dual",
            "VPK": "Tridosha Balanced"
        }

        if symptom == "No Issue / I am Fine":
            const_spec = CONSTITUTIONAL_MAINTENANCE_DETAILS.get(prakriti, CONSTITUTIONAL_MAINTENANCE_DETAILS["VPK"])
            action_text = const_spec["action"]
        else:
            action_text = tea_spec["action"]

        rules_84.append({
            "Prakriti_Code": prakriti,
            "Prakriti_Name": prakriti_names.get(prakriti, prakriti),
            "Symptom_Category": sym_category,
            "Symptom": symptom,
            "Prescribed_Tea_Code": tea_code,
            "Prescribed_Tea_Name": tea_spec["name"],
            "Category_Description": tea_spec["category"],
            "Herbal_Ingredients": ", ".join(tea_spec["ingredients"]),
            "Therapeutic_Action": action_text,
            "Doctor_Validation": "VALIDATED"
        })
    df_rules = pd.DataFrame(rules_84)

    # 3. Build Unique 2,916 Question Profiles Table
    unique_profiles_rows = []
    for prof in profile_cache:
        unique_profiles_rows.append({
            "Profile_ID": prof["vector_id"],
            "Q1_Body_Build": LABELS_Q1[prof["q1"]],
            "Q2_Skin_Texture": LABELS_Q2[prof["q2"]],
            "Q3_Appetite_Agni": LABELS_Q3[prof["q3"]],
            "Q4_Sleep_Habits": LABELS_Q4[prof["q4"]],
            "Q5_Dynamic_Trait_1": LABELS_DYNAMIC[prof["q5"]],
            "Q6_Dynamic_Trait_2": LABELS_DYNAMIC[prof["q6"]],
            "Q7_Dynamic_Trait_3": LABELS_DYNAMIC[prof["q7"]],
            "Vata_Score": prof["scores"]["V"],
            "Pitta_Score": prof["scores"]["P"],
            "Kapha_Score": prof["scores"]["K"],
            "Dominant_Prakriti": prof["dominant_prakriti"],
            "Prakriti_Label": prof["prakriti_label"],
            "Agni_Type": prof["agni_type"],
            "Agni_Description": prof["agni_desc"]
        })
    df_profiles = pd.DataFrame(unique_profiles_rows)

    # 4. Build Tea Formulations Table
    tea_catalog_rows = []
    for code, spec in TEA_CATALOG.items():
        tea_catalog_rows.append({
            "Tea_Code": code,
            "Tea_Name": spec["name"],
            "Category": spec["category"],
            "Ingredients": ", ".join(spec["ingredients"]),
            "Clinical_Action": spec["action"],
            "Primary_Indication": spec["indication"],
            "Decoction_Ratio": "1 Part Powder : 16 Parts Water",
            "Boiling_Cycle": "Reduced to 1/4th volume in boiler",
            "Serving_Temp": "Warm (~55°C - 65°C)",
            "Standard_Serving_Size": "100 ml - 150 ml"
        })
    df_teas = pd.DataFrame(tea_catalog_rows)

    # Export CSVs
    csv_filename = "ayurveda_model_permutations.csv"
    print(f"Exporting full CSV dataset to {csv_filename}...")
    df_full.to_csv(csv_filename, index=False, encoding="utf-8")
    print(f"CSV exported successfully ({os.path.getsize(csv_filename) / 1024 / 1024:.2f} MB).")

    matrix_csv_filename = "ayurveda_84_decision_matrix.csv"
    print(f"Exporting 84 decision rules to {matrix_csv_filename}...")
    df_rules.to_csv(matrix_csv_filename, index=False, encoding="utf-8")
    df_rules.to_csv("ayurveda_77_decision_matrix.csv", index=False, encoding="utf-8")

    # Export Styled Excel Workbook with openpyxl
    excel_filename = "ayurveda_model_permutations.xlsx"
    print(f"Exporting styled Excel workbook to {excel_filename}...")

    with pd.ExcelWriter(excel_filename, engine="openpyxl") as writer:
        df_rules.to_excel(writer, sheet_name="The_84_Decision_Rules", index=False)
        df_profiles.to_excel(writer, sheet_name="2916_Question_Profiles", index=False)
        df_teas.to_excel(writer, sheet_name="Tea_Formulations_Catalog", index=False)
        df_full.to_excel(writer, sheet_name="All_34992_Permutations", index=False)

    # Style the Excel Workbook
    wb = openpyxl.load_workbook(excel_filename)

    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1B4332", end_color="1B4332", fill_type="solid")
    gold_header_fill = PatternFill(start_color="C8963E", end_color="C8963E", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='E0E0E0'),
        right=Side(style='thin', color='E0E0E0'),
        top=Side(style='thin', color='E0E0E0'),
        bottom=Side(style='thin', color='E0E0E0')
    )

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        is_rules_sheet = ("Decision_Rules" in sheet_name)
        
        # Style headers
        for col_idx in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = gold_header_fill if (is_rules_sheet or "Doctor" in str(cell.value)) else header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            # Sample first 200 rows for performance
            for cell in col[:200]:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        ws.freeze_panes = "A2"

    wb.save(excel_filename)
    wb.close()

    elapsed = time.time() - start_time
    print(f"Excel workbook exported successfully ({os.path.getsize(excel_filename) / 1024 / 1024:.2f} MB).")
    print(f"Dataset generation completed in {elapsed:.2f} seconds!")
    print(f"Files ready: '{excel_filename}', '{csv_filename}', and '{matrix_csv_filename}'.")


if __name__ == "__main__":
    generate_all_datasets()

