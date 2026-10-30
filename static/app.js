/**
 * ======================================================================================
 * SOILVEDA ORGANICS - VENDING MACHINE FRONTEND CONTROLLER
 * ======================================================================================
 * Manages user interactions, step navigation, safety gate checks, API communication,
 * and visual rendering of Prakriti, Agni, and Tea prescriptions.
 * ======================================================================================
 */

let currentStep = 1;

/**
 * Navigate between wizard steps (1: Screening, 2: Prakriti, 3: Symptom, 4: Result)
 */
function goToStep(stepNumber) {
    if (stepNumber < 1 || stepNumber > 4) return;

    // Hide all steps
    document.querySelectorAll('.step-content').forEach(el => el.classList.remove('active'));
    
    // Show target step
    const target = document.getElementById(`step-${stepNumber}`);
    if (target) {
        target.classList.add('active');
        currentStep = stepNumber;
    }

    // Update Stepper indicators
    for (let i = 1; i <= 4; i++) {
        const navItem = document.getElementById(`step-nav-${i}`);
        const line = document.getElementById(`line-${i}`);

        if (i < stepNumber) {
            navItem.className = 'step-item completed';
            if (line) line.classList.add('filled');
        } else if (i === stepNumber) {
            navItem.className = 'step-item active';
            if (line) line.classList.remove('filled');
        } else {
            navItem.className = 'step-item';
            if (line) line.classList.remove('filled');
        }
    }

    // Scroll smoothly to top of container
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Handle Gender change: Pregnancy & Lactation only apply to Female
 */
function toggleGenderFields() {
    const gender = document.getElementById('userGender').value;
    const femaleCard = document.getElementById('femaleSafetyCard');
    const isPregnant = document.getElementById('isPregnant');
    const isLactating = document.getElementById('isLactating');

    if (gender === 'Male') {
        femaleCard.style.opacity = '0.5';
        femaleCard.style.pointerEvents = 'none';
        isPregnant.checked = false;
        isLactating.checked = false;
    } else {
        femaleCard.style.opacity = '1';
        femaleCard.style.pointerEvents = 'auto';
    }
    checkRealtimeSafety();
}

/**
 * Real-time alert if user inputs dangerous parameters (Age < 5 or Pregnancy = Yes)
 */
function checkRealtimeSafety() {
    const age = parseInt(document.getElementById('userAge').value, 10) || 0;
    const isPregnant = document.getElementById('isPregnant').checked;
    const alertBanner = document.getElementById('realtimeSafetyAlert');
    const alertTitle = document.getElementById('safetyAlertTitle');
    const alertMsg = document.getElementById('safetyAlertMsg');

    if (isPregnant) {
        alertBanner.classList.remove('hidden');
        alertTitle.textContent = "Safety Gate Alert: Active Pregnancy";
        alertMsg.textContent = "Active pregnancy triggers an automatic machine safety lockout to prevent ingestion of uterine-stimulating or strong botanical Kashayas.";
        return false;
    }

    if (age < 5) {
        alertBanner.classList.remove('hidden');
        alertTitle.textContent = "Safety Gate Alert: Pediatric Restriction";
        alertMsg.textContent = "Children under 5 years require direct pediatric medical supervision and cannot receive standard machine-formulated Kashayas.";
        return false;
    }

    alertBanner.classList.add('hidden');
    return true;
}

// Attach listener to Age input for realtime check
document.getElementById('userAge').addEventListener('input', checkRealtimeSafety);

/**
 * Validates Step 1 before proceeding
 */
function validateStep1AndProceed() {
    const age = parseInt(document.getElementById('userAge').value, 10);
    const isPregnant = document.getElementById('isPregnant').checked;

    if (isNaN(age) || age <= 0) {
        alert("Please enter a valid age.");
        return;
    }

    // If locked by safety gate, proceed straight to Step 4 (Lockout display)
    if (isPregnant || age < 5) {
        submitConsultation();
        return;
    }

    goToStep(2);
}

/**
 * Gather all user responses from the form and submit to the backend engine
 */
async function submitConsultation() {
    // 1. Gather Step 1 data
    const age = parseInt(document.getElementById('userAge').value, 10) || 25;
    const gender = document.getElementById('userGender').value;
    const isPregnant = document.getElementById('isPregnant').checked;
    const isLactating = document.getElementById('isLactating').checked;

    // 2. Gather Step 2 answers (Prakriti & Agni 7 questions)
    const prakritiAnswers = {};
    const questionBoxes = document.querySelectorAll('.question-box');
    questionBoxes.forEach(box => {
        const qid = box.getAttribute('data-qid');
        const selectedRadio = box.querySelector(`input[name="${qid}"]:checked`);
        if (selectedRadio) {
            prakritiAnswers[qid] = parseInt(selectedRadio.value, 10);
        } else {
            prakritiAnswers[qid] = 0; // Default first option if unselected
        }
    });

    // 3. Gather Step 3 (Selected Symptom)
    const selectedSymptomRadio = document.querySelector('input[name="selected_symptom"]:checked');
    const selectedSymptom = selectedSymptomRadio ? selectedSymptomRadio.value : "Bloating / Gas";

    // 4. Construct payload
    const payload = {
        age: age,
        gender: gender,
        is_pregnant: isPregnant,
        is_lactating: isLactating,
        prakriti_answers: prakritiAnswers,
        selected_symptom: selectedSymptom
    };

    try {
        // Send to backend API
        const response = await fetch('/api/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const resData = await response.json();
        if (resData.success) {
            renderEvaluationResult(resData.data);
            goToStep(4);
        } else {
            alert("Error in evaluation: " + resData.error);
        }
    } catch (err) {
        console.error("Consultation evaluation failed:", err);
        alert("Failed to communicate with the Ayurveda engine server.");
    }
}

/**
 * Render the resulting evaluation (either safety lockout or approved prescription)
 */
function renderEvaluationResult(data) {
    const lockoutContainer = document.getElementById('safetyLockoutContainer');
    const prescriptionContainer = document.getElementById('prescriptionResultContainer');

    // Case 1: Machine Locked Out (Safety Gate Triggered)
    if (!data.is_safe || data.status === 'LOCKED') {
        prescriptionContainer.classList.add('hidden');
        lockoutContainer.classList.remove('hidden');
        document.getElementById('lockoutReasonText').textContent = data.lockout_message;
        return;
    }

    // Case 2: Approved Prescription
    lockoutContainer.classList.add('hidden');
    prescriptionContainer.classList.remove('hidden');

    const diag = data.diagnosis;
    const presc = data.prescription;

    // Render Prakriti & Agni
    document.getElementById('resPrakritiLabel').textContent = diag.prakriti_label;
    document.getElementById('resPrakritiCode').textContent = diag.dominant_prakriti;

    // Update V-P-K Meters
    const scores = diag.dosha_scores;
    const maxScore = Math.max(scores.V, scores.P, scores.K, 7);
    
    document.getElementById('scoreValV').textContent = scores.V;
    document.getElementById('scoreValP').textContent = scores.P;
    document.getElementById('scoreValK').textContent = scores.K;

    document.getElementById('meterV').style.width = `${(scores.V / maxScore) * 100}%`;
    document.getElementById('meterP').style.width = `${(scores.P / maxScore) * 100}%`;
    document.getElementById('meterK').style.width = `${(scores.K / maxScore) * 100}%`;

    // Agni details
    document.getElementById('resAgniType').textContent = diag.agni.type;
    document.getElementById('resAgniDesc').textContent = diag.agni.description;
    document.getElementById('resSymptomName').textContent = diag.selected_symptom;

    // Prescribed Tea
    document.getElementById('resTeaCode').textContent = presc.tea_code;
    document.getElementById('resTeaName').textContent = presc.tea_name;
    document.getElementById('resTeaCategory').textContent = presc.category;
    document.getElementById('resClinicalAction').textContent = presc.clinical_action;
    document.getElementById('resIndication').textContent = presc.primary_indication;

    // Ingredients badges
    const ingContainer = document.getElementById('resIngredientsList');
    ingContainer.innerHTML = '';
    presc.ingredients.forEach(ing => {
        const badge = document.createElement('span');
        badge.className = 'ingredient-badge';
        badge.textContent = ing;
        ingContainer.appendChild(badge);
    });

    // Vending instructions
    if (presc.vending_instructions) {
        document.getElementById('specRatio').textContent = presc.vending_instructions.ratio;
        document.getElementById('specBoil').textContent = presc.vending_instructions.boiling_cycle;
        document.getElementById('specTemp').textContent = presc.vending_instructions.dispense_temperature;
        document.getElementById('specVol').textContent = presc.vending_instructions.volume;
    }
}

/**
 * Load a pre-configured test profile for immediate testing
 */
async function loadPreset(presetKey) {
    try {
        const res = await fetch(`/api/preset/${presetKey}`);
        const data = await res.json();
        if (!data.success) {
            alert("Preset not found.");
            return;
        }

        const profile = data.profile.payload;

        // Populate Form Controls
        document.getElementById('userAge').value = profile.age;
        document.getElementById('userGender').value = profile.gender;
        toggleGenderFields();

        document.getElementById('isPregnant').checked = profile.is_pregnant;
        document.getElementById('isLactating').checked = profile.is_lactating;

        // Populate Prakriti Answers
        if (profile.prakriti_answers) {
            for (const [qid, val] of Object.entries(profile.prakriti_answers)) {
                const radio = document.querySelector(`input[name="${qid}"][value="${val}"]`);
                if (radio) radio.checked = true;
            }
        }

        // Populate Symptom
        if (profile.selected_symptom) {
            const symRadio = document.querySelector(`input[name="selected_symptom"][value="${profile.selected_symptom}"]`);
            if (symRadio) symRadio.checked = true;
        }

        // Run consultation directly
        await submitConsultation();

    } catch (err) {
        console.error("Failed to load preset:", err);
    }
}

/**
 * Simulate the physical vending machine pouring / dispensing cycle
 */
function simulateDispense() {
    const dispenseBtn = document.getElementById('dispenseBtn');
    const animationBox = document.getElementById('dispenseAnimation');

    dispenseBtn.disabled = true;
    dispenseBtn.textContent = "⏳ Dispensing in Progress...";
    animationBox.classList.remove('hidden');

    setTimeout(() => {
        dispenseBtn.disabled = false;
        dispenseBtn.textContent = "✅ Fresh Kashaya Ready! (Take Cup)";
        animationBox.classList.add('hidden');
        
        setTimeout(() => {
            dispenseBtn.textContent = "🚀 Trigger Machine Vending Dispense";
        }, 4000);
    }, 2500);
}

/**
 * Reset form and return to Step 1
 */
function resetToStep1() {
    document.getElementById('consultationForm').reset();
    document.getElementById('realtimeSafetyAlert').classList.add('hidden');
    document.getElementById('safetyLockoutContainer').classList.add('hidden');
    document.getElementById('prescriptionResultContainer').classList.add('hidden');
    goToStep(1);
}

