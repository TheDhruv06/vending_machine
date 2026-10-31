/**
 * ======================================================================================
 * SOILVEDA ORGANICS - KIOSK CONTROLLER (6-SCREEN MULTI-PAGE FLOW)
 * ======================================================================================
 * Manages screen routing, safety checks, clean questionnaire rendering,
 * Ayurvedic engine API evaluation, and animated drink dispensing with lifestyle tips.
 * ======================================================================================
 */

// State variables
let currentScreenId = 'screen-welcome';
let latestConsultationResult = null;
let currentDispensingDrink = null;
let dispenseInterval = null;
let tipRotationInterval = null;
let activeTipIndex = 0;

// Clean 7 Questions (Everyday language without technical dosha/agni abbreviations)
const CLEAN_QUESTIONS = [
    {
        id: "body_frame",
        number: 1,
        question: "How would you describe your natural body build and frame?",
        options: [
            { text: "Slender, light, or lean build; difficulty gaining weight", val: 0 },
            { text: "Medium, well-proportioned, or muscular athletic build", val: 1 },
            { text: "Broad, sturdy, or heavier build; tends to gain weight easily", val: 2 }
        ]
    },
    {
        id: "skin_texture",
        number: 2,
        question: "How does your skin usually look and feel?",
        options: [
            { text: "Dry, rough, or cool to touch; tends to chap in dry weather", val: 0 },
            { text: "Warm, reddish, or sensitive; easily reacts to heat and sun", val: 1 },
            { text: "Soft, smooth, or slightly oily; thick, cool, and well-hydrated", val: 2 }
        ]
    },
    {
        id: "digestion_agni",
        number: 3,
        question: "How is your daily appetite and digestive comfort?",
        options: [
            { text: "Irregular appetite; prone to gas, bloating, or variable hunger", val: 0 },
            { text: "Sharp, intense hunger; need meals on time or feel acidic/burning", val: 1 },
            { text: "Slow, mild appetite; feel heavy or sluggish for hours after meals", val: 2 },
            { text: "Consistent, healthy appetite; digest food smoothly without distress", val: 3 }
        ]
    },
    {
        id: "sleep_pattern",
        number: 4,
        question: "How do you typically sleep through the night?",
        options: [
            { text: "Light or interrupted sleep; wake up easily with an active mind", val: 0 },
            { text: "Moderate sound sleep (6–7 hours); wake up feeling refreshed", val: 1 },
            { text: "Deep, heavy sleep (8+ hours); tend to feel slow or groggy in morning", val: 2 }
        ]
    },
    {
        id: "temperament",
        number: 5,
        question: "How do you generally respond to sudden pressure or stress?",
        options: [
            { text: "Tend to feel anxious, restless, or quick to worry", val: 0 },
            { text: "Tend to feel irritable, impatient, or fiercely goal-driven", val: 1 },
            { text: "Tend to stay calm, relaxed, patient, and slow to get upset", val: 2 }
        ]
    },
    {
        id: "energy_stamina",
        number: 6,
        question: "How would you describe your everyday physical energy and stamina?",
        options: [
            { text: "Comes in variable bursts; tire quickly and recharge with rest", val: 0 },
            { text: "Strong, focused stamina; work with intensity until exhausted", val: 1 },
            { text: "Steady, enduring stamina; keep moving at a consistent pace all day", val: 2 }
        ]
    },
    {
        id: "sweating_heat",
        number: 7,
        question: "How sensitive are you to temperature and changing weather?",
        options: [
            { text: "Dislike cold and drafty winds; feel chilly easily", val: 0 },
            { text: "Dislike heat and direct sun; sweat easily and feel hot quickly", val: 1 },
            { text: "Dislike cold, wet, or rainy weather; comfortable in warm dry air", val: 2 }
        ]
    }
];

// Daily Ayurvedic Lifestyle Tips to show while preparing drink
const WELLNESS_TIPS = [
    {
        title: "Sip Warm Water Throughout the Day",
        body: "Drinking warm water or herbal teas stimulates your digestive fire (Agni), clears metabolic toxins (Ama), and prevents gut sluggishness."
    },
    {
        title: "Daily Yoga & Stretch",
        body: "Practicing 15 minutes of gentle yoga or Surya Namaskar in the morning opens your body's energy channels, enhances lung capacity, and relieves joint stiffness."
    },
    {
        title: "Mindful Deep Breathing (Pranayama)",
        body: "Taking 5 minutes for alternate-nostril breathing (Anulom Vilom) calms nervous tension, stabilizes heart rate, and harmonizes Vata energy."
    },
    {
        title: "Eat Fresh, Warm Meals in Moderation",
        body: "Freshly prepared, lightly spiced warm foods are easiest for your stomach to break down. Avoid ice-cold drinks right with your meals."
    }
];


// ======================================================================================
// 1. SCREEN NAVIGATION CONTROLLER
// ======================================================================================

/**
 * Transitions smoothly between screens
 */
function navigateTo(targetScreenId) {
    // Hide all screens
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });

    // Show target screen
    const targetScreen = document.getElementById(targetScreenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
        currentScreenId = targetScreenId;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}


// ======================================================================================
// 2. PAGE 1: WELCOME SCREEN ACTIONS
// ======================================================================================

/**
 * Initiates the AI Health Assessment Track
 */
function startAssessment() {
    // Reset inputs
    document.getElementById('inputAge').value = 28;
    document.getElementById('inputGender').value = "Female";
    document.getElementById('checkPregnant').checked = false;
    document.getElementById('checkLactating').checked = false;
    handleGenderChange();

    renderQuestions();
    navigateTo('screen-screening');
}

/**
 * Direct Instant Dispense Track (For Regular Tea & Classical Kashaya)
 */
function startDirectDispense(drinkName, subtitle, description, ingredients) {
    currentDispensingDrink = {
        name: drinkName,
        subtitle: subtitle,
        description: description,
        ingredients: ingredients
    };

    // Begin dispensing animation immediately
    beginDispensingAnimation(drinkName, subtitle);
}


// ======================================================================================
// 3. SCREEN 2: BASIC SCREENING & SAFETY GATES
// ======================================================================================

/**
 * Handles Gender field changes (pregnancy/lactation only relevant for Female)
 */
function handleGenderChange() {
    const gender = document.getElementById('inputGender').value;
    const femaleBox = document.getElementById('femaleSafetyBox');
    const isPregnant = document.getElementById('checkPregnant');
    const isLactating = document.getElementById('checkLactating');

    if (gender === 'Male') {
        femaleBox.style.opacity = '0.4';
        femaleBox.style.pointerEvents = 'none';
        isPregnant.checked = false;
        isLactating.checked = false;
    } else {
        femaleBox.style.opacity = '1';
        femaleBox.style.pointerEvents = 'auto';
    }
    evaluateSafetyGate();
}

/**
 * Real-time safety gate evaluation (Age < 5 or Pregnancy = true)
 */
function evaluateSafetyGate() {
    const age = parseInt(document.getElementById('inputAge').value, 10) || 0;
    const isPregnant = document.getElementById('checkPregnant').checked;
    const alertBox = document.getElementById('screeningAlert');
    const alertTitle = document.getElementById('screeningAlertTitle');
    const alertMsg = document.getElementById('screeningAlertMsg');

    if (isPregnant) {
        alertBox.classList.remove('hidden');
        alertTitle.textContent = "Safety Gate: Active Pregnancy Detected";
        alertMsg.textContent = "Herbal Kashayas contain active botanical principles. Machine is locked for prenatal protection.";
        return false;
    }

    if (age < 5) {
        alertBox.classList.remove('hidden');
        alertTitle.textContent = "Safety Gate: Pediatric Restriction";
        alertMsg.textContent = "Children under 5 years require direct medical supervision and weight-adjusted pediatric care.";
        return false;
    }

    alertBox.classList.add('hidden');
    return true;
}

// Attach listener to Age input
document.getElementById('inputAge').addEventListener('input', evaluateSafetyGate);

/**
 * Validates screening inputs and advances to Questions
 */
function proceedFromScreening() {
    const age = parseInt(document.getElementById('inputAge').value, 10);
    const isPregnant = document.getElementById('checkPregnant').checked;

    if (isNaN(age) || age <= 0) {
        alert("Please enter a valid age.");
        return;
    }

    // Check safety gates
    if (isPregnant) {
        document.getElementById('lockoutDetails').textContent = 
            "Active pregnancy detected. Potent herbal decoctions can alter maternal physiology. Please consult the clinical wellness desk.";
        navigateTo('screen-lockout');
        return;
    }

    if (age < 5) {
        document.getElementById('lockoutDetails').textContent = 
            "Patient is under 5 years old. Pediatric dosing requires direct physician consultation.";
        navigateTo('screen-lockout');
        return;
    }

    navigateTo('screen-questions');
}


// ======================================================================================
// 4. SCREEN 3: 7 SIMPLE QUESTIONS (NO DOSHA JARGON)
// ======================================================================================

/**
 * Renders the 7 questions with clean, everyday natural language options
 */
function renderQuestions() {
    const container = document.getElementById('questionsContainer');
    container.innerHTML = '';

    CLEAN_QUESTIONS.forEach((q, qIndex) => {
        const card = document.createElement('div');
        card.className = 'question-card-item';

        let optionsHtml = '';
        q.options.forEach((opt, optIndex) => {
            const isChecked = optIndex === 0 ? 'checked' : '';
            optionsHtml += `
                <label class="clean-option-card">
                    <input type="radio" name="${q.id}" value="${opt.val}" ${isChecked}>
                    <span class="option-indicator"></span>
                    <span class="option-desc">${opt.text}</span>
                </label>
            `;
        });

        card.innerHTML = `
            <div class="q-title-row">
                <span class="q-number">${q.number}</span>
                <span class="q-question-text">${q.question}</span>
            </div>
            <div class="clean-options-grid">
                ${optionsHtml}
            </div>
        `;

        container.appendChild(card);
    });
}

function proceedFromQuestions() {
    navigateTo('screen-symptoms');
}


// ======================================================================================
// 5. SCREEN 4: SUBMIT ASSESSMENT & API CALL
// ======================================================================================

/**
 * Submits consultation data to the Ayurvedic engine API
 */
async function submitAssessment() {
    const age = parseInt(document.getElementById('inputAge').value, 10) || 28;
    const gender = document.getElementById('inputGender').value;
    const isPregnant = document.getElementById('checkPregnant').checked;
    const isLactating = document.getElementById('checkLactating').checked;

    // Collect 7 answers
    const answers = {};
    CLEAN_QUESTIONS.forEach(q => {
        const selected = document.querySelector(`input[name="${q.id}"]:checked`);
        answers[q.id] = selected ? parseInt(selected.value, 10) : 0;
    });

    // Collect selected symptom
    const symRadio = document.querySelector('input[name="symptom_choice"]:checked');
    const selectedSymptom = symRadio ? symRadio.value : "Bloating / Gas";

    const payload = {
        age: age,
        gender: gender,
        is_pregnant: isPregnant,
        is_lactating: isLactating,
        prakriti_answers: answers,
        selected_symptom: selectedSymptom
    };

    try {
        const res = await fetch('/api/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const json = await res.json();
        if (json.success && json.data.is_safe) {
            latestConsultationResult = json.data;
            populateResultScreen(json.data);
            navigateTo('screen-result');
        } else if (json.data && !json.data.is_safe) {
            document.getElementById('lockoutDetails').textContent = json.data.lockout_message;
            navigateTo('screen-lockout');
        } else {
            alert("Could not process evaluation: " + (json.error || "Unknown error"));
        }
    } catch (e) {
        console.error("API error:", e);
        alert("Failed to connect to the Ayurveda Engine.");
    }
}


// ======================================================================================
// 6. SCREEN 5: RESULT & PRESCRIPTION PAGE
// ======================================================================================

/**
 * Populates the result screen with the model's findings
 */
function populateResultScreen(data) {
    const diag = data.diagnosis;
    const presc = data.prescription;

    // Display Constitution and Metabolism
    document.getElementById('resConstitution').textContent = diag.prakriti_label;
    document.getElementById('resMetabolism').textContent = diag.agni.type;
    document.getElementById('resSelectedSymptom').textContent = diag.selected_symptom;

    // Drink Card
    document.getElementById('resTeaCode').textContent = presc.tea_code;
    document.getElementById('resDrinkName').textContent = presc.tea_name;
    document.getElementById('resCategory').textContent = presc.category;
    document.getElementById('resAction').textContent = presc.clinical_action;
    document.getElementById('resIndication').textContent = presc.primary_indication;

    // Ingredients
    const ingList = document.getElementById('resIngredientsList');
    ingList.innerHTML = '';
    presc.ingredients.forEach(ing => {
        const chip = document.createElement('span');
        chip.className = 'ingredient-pill';
        chip.textContent = ing;
        ingList.appendChild(chip);
    });

    currentDispensingDrink = {
        name: presc.tea_name,
        subtitle: presc.category,
        ingredients: presc.ingredients
    };
}

/**
 * Retake assessment - resets back to step 1
 */
function retakeAssessment() {
    startAssessment();
}

/**
 * Trigger Dispense from the Result Page
 */
function triggerDispenseFromAssessment() {
    if (currentDispensingDrink) {
        beginDispensingAnimation(currentDispensingDrink.name, currentDispensingDrink.subtitle);
    }
}


// ======================================================================================
// 7. SCREEN 6: PREPARING & DISPENSING (ANIMATION + ROTATING WELLNESS TIPS)
// ======================================================================================

/**
 * Controls the animated dispensing sequence and lifestyle tips rotation
 */
function beginDispensingAnimation(drinkName, subtitle) {
    navigateTo('screen-dispensing');

    // Set titles
    document.getElementById('dispenseDrinkTitle').textContent = `Dispensing: ${drinkName}`;
    document.getElementById('dispenseDrinkSub').textContent = subtitle || "Freshly preparing and filtering your herbal beverage...";

    // Reset progress UI
    const progressFill = document.getElementById('dispenseProgress');
    const percentLabel = document.getElementById('dispensePercent');
    const stepLabel = document.getElementById('dispenseStepText');
    const liquid = document.getElementById('cupLiquid');
    const completeBox = document.getElementById('dispenseCompleteBox');

    progressFill.style.width = '0%';
    liquid.style.height = '0%';
    percentLabel.textContent = '0%';
    stepLabel.textContent = 'Heating water & weighing botanicals...';
    completeBox.classList.add('hidden');

    // Reset tips
    activeTipIndex = 0;
    updateActiveTipDisplay(activeTipIndex);

    // Clear any previous intervals
    if (dispenseInterval) clearInterval(dispenseInterval);
    if (tipRotationInterval) clearInterval(tipRotationInterval);

    // Rotate tips every 3 seconds
    tipRotationInterval = setInterval(() => {
        activeTipIndex = (activeTipIndex + 1) % WELLNESS_TIPS.length;
        updateActiveTipDisplay(activeTipIndex);
    }, 2800);

    // Progress animation (0 to 100% over ~6 seconds)
    let currentPct = 0;
    const stages = [
        { at: 15, text: "Adding 1:16 ratio purified water to extraction chamber..." },
        { at: 40, text: "Active boiling & Ayurvedic volume reduction in progress..." },
        { at: 70, text: "Continuous stirring & deep botanical extraction..." },
        { at: 90, text: "Precision filtration & routing through dispensing nozzle..." },
        { at: 100, text: "Fresh brew complete!" }
    ];

    dispenseInterval = setInterval(() => {
        currentPct += 2;
        if (currentPct > 100) currentPct = 100;

        progressFill.style.width = `${currentPct}%`;
        liquid.style.height = `${currentPct * 0.9}%`;
        percentLabel.textContent = `${currentPct}%`;

        // Update stage text
        for (let i = 0; i < stages.length; i++) {
            if (currentPct <= stages[i].at) {
                stepLabel.textContent = stages[i].text;
                break;
            }
        }

        // Completion
        if (currentPct >= 100) {
            clearInterval(dispenseInterval);
            clearInterval(tipRotationInterval);
            stepLabel.textContent = "✅ Freshly dispensed! Ready to drink.";
            completeBox.classList.remove('hidden');
        }
    }, 120);
}

/**
 * Updates the wellness tip card and indicator dots
 */
function updateActiveTipDisplay(index) {
    const tip = WELLNESS_TIPS[index];
    document.getElementById('tipTitle').textContent = tip.title;
    document.getElementById('tipBody').textContent = tip.body;

    // Update indicator dots
    for (let i = 0; i < WELLNESS_TIPS.length; i++) {
        const dot = document.getElementById(`dot-${i}`);
        if (dot) {
            dot.className = (i === index) ? 'tip-dot active' : 'tip-dot';
        }
    }
}


// ======================================================================================
// 8. INITIALIZATION ON PAGE LOAD
// ======================================================================================
window.addEventListener('DOMContentLoaded', () => {
    // Render initial questions in background
    renderQuestions();
});
