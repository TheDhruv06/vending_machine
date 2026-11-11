"""
========================================================================================
SOILVEDA ORGANICS - AI-DRIVEN VENDING MACHINE WEB APPLICATION
========================================================================================
Flask-based interactive web simulator and API server for testing the 
Ayurvedic Prakriti, Agni, and Tea Recommendation Model.
========================================================================================
"""

import os
import time
from flask import Flask, render_template, request, jsonify
from ayurveda_engine import (
    SET_1_CORE_QUESTIONS,
    SET_2_QUESTION_POOL,
    ALL_QUESTIONS_MAP,
    PRAKRITI_QUESTIONS,
    SYMPTOMS_CATALOG,
    TEA_CATALOG,
    RECOMMENDATION_MATRIX,
    evaluate_user_consultation
)

# Explicitly resolve template and static folder absolute paths so Vercel serverless handles them seamlessly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(BASE_DIR, "templates")
static_dir = os.path.join(BASE_DIR, "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Pre-configured test profiles to make testing fast, repeatable, and interactive
PRESET_PROFILES = {
    "vata_bloating": {
        "name": "Profile 1: Vata Dominant + Bloating",
        "description": "Thin build, dry skin, erratic digestion, anxious -> Bloating / Gas -> Expects Tea A (Lemongrass Sip)",
        "payload": {
            "age": 29,
            "gender": "Female",
            "is_pregnant": False,
            "is_lactating": False,
            "prakriti_answers": {
                "body_frame": 0,      # Vata
                "skin_texture": 0,    # Vata
                "digestion_agni": 0,  # Vishama Agni (Vata)
                "sleep_pattern": 0,   # Vata
                "temperament": 0,     # Vata
                "energy_stamina": 0,  # Vata
                "sweating_heat": 0    # Vata
            },
            "selected_symptom": "Bloating / Gas"
        }
    },
    "pitta_acidity": {
        "name": "Profile 2: Pitta Dominant + Acidity",
        "description": "Medium build, warm skin, sharp digestion, irritable -> Acidity / Burning -> Expects Tea B (Vital Sip / Arjun Bark)",
        "payload": {
            "age": 34,
            "gender": "Male",
            "is_pregnant": False,
            "is_lactating": False,
            "prakriti_answers": {
                "body_frame": 1,      # Pitta
                "skin_texture": 1,    # Pitta
                "digestion_agni": 1,  # Tikshna Agni (Pitta)
                "sleep_pattern": 1,   # Pitta
                "temperament": 1,     # Pitta
                "energy_stamina": 1,  # Pitta
                "sweating_heat": 1    # Pitta
            },
            "selected_symptom": "Acidity / Burning"
        }
    },
    "kapha_heaviness": {
        "name": "Profile 3: Kapha Dominant + Heavy Stomach",
        "description": "Heavy build, oily skin, slow digestion, calm -> Heavy Stomach -> Expects Tea C (MedoHar Sip)",
        "payload": {
            "age": 42,
            "gender": "Male",
            "is_pregnant": False,
            "is_lactating": False,
            "prakriti_answers": {
                "body_frame": 2,      # Kapha
                "skin_texture": 2,    # Kapha
                "digestion_agni": 2,  # Manda Agni (Kapha)
                "sleep_pattern": 2,   # Kapha
                "temperament": 2,     # Kapha
                "energy_stamina": 2,  # Kapha
                "sweating_heat": 2    # Kapha
            },
            "selected_symptom": "Heavy Stomach"
        }
    },
    "vata_constipation": {
        "name": "Profile 4: Vata-Pitta + Constipation",
        "description": "Dual dosha -> Constipation -> Expects Tea D (Mangalayu Laxative & Gut Regularizer)",
        "payload": {
            "age": 31,
            "gender": "Female",
            "is_pregnant": False,
            "is_lactating": False,
            "prakriti_answers": {
                "body_frame": 0,      # Vata
                "skin_texture": 1,    # Pitta
                "digestion_agni": 0,  # Vishama Agni (Vata)
                "sleep_pattern": 1,   # Pitta
                "temperament": 0,     # Vata
                "energy_stamina": 1,  # Pitta
                "sweating_heat": 0    # Vata
            },
            "selected_symptom": "Constipation"
        }
    },
    "immunity_fatigue": {
        "name": "Profile 5: Low Immunity & Fatigue",
        "description": "Tridosha profile -> Low Immunity -> Expects Tea E (Moringa Sip / Rasayana Vitalizer)",
        "payload": {
            "age": 40,
            "gender": "Female",
            "is_pregnant": False,
            "is_lactating": False,
            "prakriti_answers": {
                "body_frame": 0,      # Vata
                "skin_texture": 1,    # Pitta
                "digestion_agni": 3,  # Sama Agni (Balanced)
                "sleep_pattern": 2,   # Kapha
                "temperament": 2,     # Kapha
                "energy_stamina": 1,  # Pitta
                "sweating_heat": 0    # Vata
            },
            "selected_symptom": "Low Immunity"
        }
    },
    "respiratory_cold": {
        "name": "Profile 6: Respiratory Congestion & Cold",
        "description": "Cold & Cough -> Expects Tea F (Green Sip / Pranavaha Respiratory Support)",
        "payload": {
            "age": 27,
            "gender": "Male",
            "is_pregnant": False,
            "is_lactating": False,
            "prakriti_answers": {
                "body_frame": 2,      # Kapha
                "skin_texture": 2,    # Kapha
                "digestion_agni": 2,  # Manda Agni (Kapha)
                "sleep_pattern": 2,   # Kapha
                "temperament": 2,     # Kapha
                "energy_stamina": 2,  # Kapha
                "sweating_heat": 2    # Kapha
            },
            "selected_symptom": "Cough / Congestion"
        }
    },
    "safety_pregnancy": {
        "name": "Safety Gate Test: Pregnant User",
        "description": "Pregnancy = True -> Expects immediate Safety Lockout and Clinical Desk Referral",
        "payload": {
            "age": 26,
            "gender": "Female",
            "is_pregnant": True,
            "is_lactating": False,
            "prakriti_answers": {},
            "selected_symptom": "Bloating / Gas"
        }
    },
    "safety_pediatric": {
        "name": "Safety Gate Test: Child Under 5",
        "description": "Age = 3 -> Expects immediate Safety Lockout (Pediatric restriction)",
        "payload": {
            "age": 3,
            "gender": "Male",
            "is_pregnant": False,
            "is_lactating": False,
            "prakriti_answers": {},
            "selected_symptom": "Cold / Allergies"
        }
    }
}


@app.route("/")
def index():
    """Renders the main simulation kiosk interface."""
    return render_template(
        "index.html",
        questions=PRAKRITI_QUESTIONS,
        symptoms=SYMPTOMS_CATALOG,
        teas=TEA_CATALOG,
        presets=PRESET_PROFILES
    )


@app.route("/api/config", methods=["GET"])
def get_config():
    """Returns configuration metadata for client interfaces."""
    return jsonify({
        "set1_core_questions": SET_1_CORE_QUESTIONS,
        "set2_question_pool": SET_2_QUESTION_POOL,
        "questions": PRAKRITI_QUESTIONS,
        "symptoms": SYMPTOMS_CATALOG,
        "teas": TEA_CATALOG,
        "presets": PRESET_PROFILES
    })


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """
    Evaluates incoming consultation data and runs the Ayurvedic engine.
    """
    try:
        data = request.get_json(force=True)
        result = evaluate_user_consultation(data)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/preset/<preset_id>", methods=["GET"])
def get_preset(preset_id):
    """Retrieves a specific preset profile."""
    if preset_id in PRESET_PROFILES:
        return jsonify({"success": True, "profile": PRESET_PROFILES[preset_id]})
    return jsonify({"success": False, "error": "Preset profile not found"}), 404


# ======================================================================================
# ESP32 HARDWARE DISPENSER QUEUE & BRIDGING ENDPOINTS
# ======================================================================================
DISPENSE_QUEUE = []
DISPENSE_HISTORY = []
JOB_COUNTER = 0

TEA_TO_CONTAINER_MAP = {
    "Tea A": 1,        # Lemongrass Sip / Container 1
    "Tea B": 2,        # Vital Sip / Container 2
    "Tea C": 3,        # MedoHar Sip / Container 3
    "Tea D": 4,        # Mangalayu Tea / Container 4
    "Tea E": 1,        # Moringa Sip / Container 1 (or 5 if equipped)
    "Tea F": 2,        # Green Sip / Container 2 (or 6 if equipped)
    "Regular Tea": 4,  # Standard Instant Tea / Container 4
    "Kashaya A": 1,
    "Kashaya B": 2,
    "Kashaya C": 3,
}

@app.route("/api/dispense", methods=["POST"])
def queue_dispense():
    """
    Called by the Web UI when user clicks 'Dispense'.
    Pushes a new hardware dispense job into the ESP32 queue.
    """
    global JOB_COUNTER
    try:
        data = request.get_json(force=True) or {}
        tea_code = data.get("tea_code", "")
        drink_name = data.get("drink_name", "Herbal Beverage")

        # Determine target container ID
        container_id = data.get("container_id")
        if not container_id:
            container_id = TEA_TO_CONTAINER_MAP.get(tea_code, TEA_TO_CONTAINER_MAP.get(drink_name, 1))

        JOB_COUNTER += 1
        job = {
            "job_id": JOB_COUNTER,
            "tea_code": tea_code,
            "drink_name": drink_name,
            "container_id": int(container_id),
            "duration_ms": int(data.get("duration_ms", 2500)),
            "status": "PENDING",
            "timestamp": time.time()
        }

        DISPENSE_QUEUE.append(job)
        return jsonify({
            "success": True,
            "message": f"Dispense job #{job['job_id']} queued for Container {job['container_id']} ({drink_name})",
            "job": job
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/dispense/poll", methods=["GET"])
def poll_dispense():
    """
    Called periodically by ESP32 over WiFi (e.g. every 1000ms).
    Returns the oldest pending job for the hardware to dispense.
    """
    for job in DISPENSE_QUEUE:
        if job["status"] == "PENDING":
            job["status"] = "IN_PROGRESS"
            return jsonify({
                "has_job": True,
                "job": job
            })
    return jsonify({
        "has_job": False,
        "job": None
    })


@app.route("/api/dispense/complete", methods=["POST"])
def complete_dispense():
    """
    Called by ESP32 after running the BO motor to confirm dispensing is complete.
    """
    try:
        data = request.get_json(force=True) or {}
        job_id = int(data.get("job_id", 0))
        for job in list(DISPENSE_QUEUE):
            if job["job_id"] == job_id:
                job["status"] = "COMPLETED"
                DISPENSE_HISTORY.append(job)
                DISPENSE_QUEUE.remove(job)
                return jsonify({"success": True, "message": f"Job #{job_id} completed successfully"})
        return jsonify({"success": True, "message": "Job acknowledged"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/dispense/status", methods=["GET"])
def dispense_status():
    """Returns queue status for diagnostic and monitoring dashboards."""
    return jsonify({
        "pending_count": len([j for j in DISPENSE_QUEUE if j["status"] == "PENDING"]),
        "in_progress_count": len([j for j in DISPENSE_QUEUE if j["status"] == "IN_PROGRESS"]),
        "queue": DISPENSE_QUEUE,
        "recent_history": DISPENSE_HISTORY[-5:]
    })


if __name__ == "__main__":
    # Run development server on port 5000
    print("Starting Soilveda Organics Ayurvedic Vending Machine Simulator...")
    print("Open http://127.0.0.1:5000 in your web browser.")
    app.run(host="127.0.0.1", port=5000, debug=True)

