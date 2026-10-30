# Soilveda Organics - AI-Driven Ayurvedic Vending Machine (Model & UI)

This repository contains the **Ayurvedic Diagnostic Intelligence Engine (Model)** and an interactive **Touch-Friendly Web Simulator UI** for the Automated Kashaya and Herbal Tea Vending Machine.

---

## 🌟 Architecture Overview

```
VENDING_MACHINE_CODE/
├── ayurveda_engine.py      # Core Clinical Intelligence Engine (Prakriti, Agni, & 77-combination rule matrix)
├── test_engine.py         # Unit tests validating safety gates, dosha scoring, and all 77 tea mappings
├── app.py                 # Flask server providing Web UI & REST API (/api/evaluate, /api/config)
├── templates/
│   └── index.html         # Kiosk UI with 4-phase clinical workflow
├── static/
│   ├── style.css          # Modern Ayurvedic aesthetic & touch-responsive styling
│   └── app.js             # Client-side validation, realtime safety checks, and API calls
└── DOCUMENTS/             # Original specifications, PRD, and machine renders
```

---

## 🌿 How the Model Works

### Phase 1: Screening & Safety Gates
* **Pregnancy Lockout:** If `Pregnancy = True`, the machine locks out immediately to prevent ingestion of strong botanical compounds without prenatal supervision.
* **Pediatric Restriction:** If `Age < 5`, locks out and refers the patient to direct medical consultation.

### Phase 2: Prakriti & Agni Assessment
* **7 Classical Diagnostic Parameters:**
  1. Body Frame (Lean/Vata, Muscular/Pitta, Broad/Kapha)
  2. Skin Texture (Dry/Vata, Warm/Pitta, Oily/Kapha)
  3. **Appetite & Digestion (Evaluates Agni):**
     * *Vishama Agni* (Erratic, Vata-dominant)
     * *Tikshna Agni* (Sharp/intense, Pitta-dominant)
     * *Manda Agni* (Sluggish, Kapha-dominant)
     * *Sama Agni* (Equilibrated, Balanced)
  4. Sleep Quality (Light, Moderate, Heavy)
  5. Mind under Stress / Temperament (Anxious, Irritable, Calm)
  6. Stamina & Energy (Variable, Strong, Steady)
  7. Sweating & Thermal Preference (Cold-sensitive, Heat-sensitive, Damp-sensitive)
* **Prakriti Classification:** V, P, K, VP, PK, VK, or VPK (Tridosha).

### Phase 3: The 10-Second Acute Symptom Menu (Vikriti)
* **Gastrointestinal:** Bloating/Gas, Acidity/Burning, Heavy Stomach, Constipation
* **Musculoskeletal:** Back/Nerve Pain, Body Ache/Fatigue, Joint Swelling, Morning Stiffness
* **Respiratory & Immune:** Cold/Allergies, Cough/Congestion, Low Immunity

### Phase 4: Deterministic 77-Combination Rule Engine
The model matches the user's `(Prakriti, Symptom)` pair against the exact 77 permutations to dispense one of the 6 targeted formulations:

| Code | Formulation Name | Category & Action | Key Herbal Ingredients |
|---|---|---|---|
| **Tea A** | Lemongrass Sip | Vata-Hara (Carminative & Digestive) | Lemongrass |
| **Tea B** | Vital Sip | Pitta-Hara (Cooling & Anti-inflammatory) | Arjun Bark (*Terminalia arjuna*) |
| **Tea C** | MedoHar Sip | Kapha-Hara (Scraping & Metabolism Booster) | Jeera, Sounf, Lemongrass, Ajwain, Dry Ginger, Moringa |
| **Tea D** | Mangalayu Tea | Vata-Anulomana (Mild Laxative & Gut Regularizer) | Tea leaves, Dry Ginger, Elaichi, Bay Leaf, Rose, Aprajita, Lemongrass |
| **Tea E** | Moringa Sip | Rasayana (Immunity & Deep Tissue Vitalizer) | Moringa Leaf |
| **Tea F** | Green Sip | Pranavaha (Respiratory Channel Clearing & Antitussive) | Tulsi, Black Pepper, Dry Ginger, Jeera, Ajwain, Bay Leaf, Rose, etc. |

---

## 🚀 How to Run and Test

### 1. Run the Unit Test Suite
```bash
python test_engine.py
```
*Verifies all safety gates and confirms all 77 combinations resolve to valid recipes.*

### 2. Start the Web Simulator
```bash
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in any web browser.

### 3. Interactive Quick-Test Presets
The UI includes one-click buttons to instantly test:
* **Vata Bloating** $\rightarrow$ Tea A
* **Pitta Acidity** $\rightarrow$ Tea B
* **Kapha Heaviness** $\rightarrow$ Tea C
* **Constipation** $\rightarrow$ Tea D
* **Immunity & Fatigue** $\rightarrow$ Tea E
* **Respiratory / Cough** $\rightarrow$ Tea F
* **Safety Gate 1:** Pregnancy Lockout
* **Safety Gate 2:** Child Under 5 Lockout

