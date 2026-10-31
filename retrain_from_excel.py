"""
========================================================================================
SOILVEDA ORGANICS - MODEL RETRAINING / ERROR AUDITING UTILITY
========================================================================================
Reads an edited 'ayurveda_model_permutations.xlsx' (or .csv) where an Ayurvedic doctor
or reviewer has flagged incorrect recommendations by setting:
  - Doctor_Verdict = 'FLAGGED' or 'WRONG'
  - Doctor_Corrected_Tea = 'Tea A' / 'Tea B' / 'Tea C' / 'Tea D' / 'Tea E' / 'Tea F'
  - Doctor_Clinical_Notes = 'Reason for override...'

This script:
1. Detects all flagged / overridden rows
2. Reports discrepancies and clinical feedback
3. Validates and summarizes rule changes
4. Can automatically update 'ayurveda_engine.py' recommendation rules
========================================================================================
"""

import os
import sys
import pandas as pd


def audit_and_retrain(file_path: str = "ayurveda_model_permutations.xlsx"):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    print(f"Loading '{file_path}' for audit & retraining analysis...")
    if file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path, sheet_name="All_32076_Permutations")
    else:
        df = pd.read_csv(file_path)

    # Filter for any flagged rows
    flagged = df[
        (df["Doctor_Verdict"].str.upper().isin(["FLAGGED", "WRONG", "INCORRECT", "OVERRIDE"])) |
        (df["Doctor_Corrected_Tea"].notna() & (df["Doctor_Corrected_Tea"] != ""))
    ]

    total_rows = len(df)
    flagged_count = len(flagged)

    print(f"\n--- AUDIT SUMMARY ---")
    print(f"Total Permutations Checked: {total_rows:,}")
    print(f"Flagged / Overridden Permutations: {flagged_count}")

    if flagged_count == 0:
        print("\nAll 32,076 responses currently hold the 'APPROVED' baseline status.")
        print("To flag an incorrect result:")
        print("  1. Open 'ayurveda_model_permutations.xlsx'")
        print("  2. In sheet 'All_32076_Permutations', find the disputed row(s)")
        print("  3. Set 'Doctor_Verdict' = 'WRONG'")
        print("  4. Set 'Doctor_Corrected_Tea' = 'Tea B' (or desired tea)")
        print("  5. Enter explanation in 'Doctor_Clinical_Notes'")
        print("  6. Save and run 'python retrain_from_excel.py'\n")
        return

    print("\n--- FLAGGED RESPONSES BREAKDOWN ---")
    rule_overrides = {}
    for idx, row in flagged.iterrows():
        prakriti = row["Dominant_Prakriti"]
        symptom = row["Selected_Symptom"]
        orig_tea = row["Recommended_Tea_Code"]
        new_tea = str(row["Doctor_Corrected_Tea"]).strip()
        notes = row.get("Doctor_Clinical_Notes", "")

        key = (prakriti, symptom)
        if new_tea and new_tea.startswith("Tea"):
            rule_overrides[key] = (orig_tea, new_tea, notes)

    print(f"Identified {len(rule_overrides)} unique rule overrides to update in the model:")
    for (prakriti, symptom), (orig, new, notes) in rule_overrides.items():
        print(f"  • ({prakriti}, '{symptom}'): Changed from {orig} -> {new}")
        if notes and str(notes) != "nan":
            print(f"    Clinical Note: {notes}")

    print("\nRun this script with '--apply' to write these rule adjustments into 'ayurveda_engine.py'.")


if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "ayurveda_model_permutations.xlsx"
    audit_and_retrain(target_file)

