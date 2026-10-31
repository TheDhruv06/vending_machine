/**
 * ======================================================================================
 * SOILVEDA ORGANICS - KIOSK CONTROLLER (MULTI-SCREEN & DYNAMIC 7-QUESTION SYSTEM)
 * ======================================================================================
 * Features:
 * 1. Screen navigation controller
 * 2. Dedicated Kashaya Selection Menu (Kashaya A, B, and C)
 * 3. 7-Question Engine:
 *    - Set 1: 4 Core Questions (Body, Skin, Digestion/Agni, Sleep) with order randomized
 *    - Set 2: 3 Dynamic Questions chosen at random from the 9-question pool (Q5 - Q13 in docx)
 *    - All questions displayed in clean, everyday language without dosha jargon
 * 4. Real-time safety gates (Pregnancy and Age < 5 lockout)
 * 5. Full API evaluation with dominant Prakriti, Agni state, and recommended tea
 * 6. Animated preparing & dispensing cup with rotating daily Ayurvedic wellness tips
 * ======================================================================================
 */

// State tracking
let currentScreenId = 'screen-welcome';
let activeConsultationQuestions = [];
let latestConsultationResult = null;
let currentDispensingDrink = null;
let dispenseInterval = null;
let tipRotationInterval = null;
let activeTipIndex = 0;

// ======================================================================================
// QUESTION BANK: SET 1 (CORE 4) & SET 2 (POOL OF 9 QUESTIONS FROM Q5 TO Q13)
// ======================================================================================

// SET 1: Always included for every user, but its order is randomized each time
const SET_1_CORE_QUESTIONS = [
    {
        id: "body_frame",
        title: "Body Build & Frame",
        question: "How would you describe your natural body build and frame?",
        options: [
            { text: "Slender, light, or lean build; difficulty gaining weight", val: 0 },
            { text: "Medium, well-proportioned, or muscular athletic build", val: 1 },
            { text: "Broad, sturdy, or heavier build; tends to gain weight easily", val: 2 }
        ]
    },
    {
        id: "skin_texture",
        title: "Skin Feel & Texture",
        question: "How does your skin usually look and feel?",
        options: [
            { text: "Dry, rough, or cool to touch; tends to chap in dry weather", val: 0 },
            { text: "Warm, reddish, or sensitive; easily reacts to heat and sun", val: 1 },
            { text: "Soft, smooth, or slightly oily; thick, cool, and well-hydrated", val: 2 }
        ]
    },
    {
        id: "digestion_agni",
        title: "Appetite & Digestion",
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
        title: "Sleep Habits",
        question: "How do you typically sleep through the night?",
        options: [
            { text: "Light or interrupted sleep; wake up easily with an active mind", val: 0 },
            { text: "Moderate sound sleep (6–7 hours); wake up feeling refreshed", val: 1 },
            { text: "Deep, heavy sleep (8+ hours); tend to feel slow or groggy in morning", val: 2 }
        ]
    }
];

// SET 2: Pool of 9 questions (Q5 - Q13 in docx). Exactly 3 are selected at random for each new user
const SET_2_QUESTION_POOL = [
    {
        id: "temperament",
        title: "Mind Under Pressure (Docx Q5)",
        question: "How do you generally respond to sudden pressure or stress?",
        options: [
            { text: "Tend to feel anxious, restless, or quick to worry", val: 0 },
            { text: "Tend to feel irritable, impatient, or intensely focused", val: 1 },
            { text: "Tend to stay calm, relaxed, patient, and slow to react", val: 2 }
        ]
    },
    {
        id: "energy_stamina",
        title: "Daily Energy & Stamina (Docx Q6)",
        question: "How would you describe your everyday physical energy and stamina?",
        options: [
            { text: "Comes in variable bursts; tire quickly and recharge with rest", val: 0 },
            { text: "Strong, focused stamina; work with intensity until exhausted", val: 1 },
            { text: "Steady, enduring stamina; keep moving at a consistent pace all day", val: 2 }
        ]
    },
    {
        id: "sweating_heat",
        title: "Weather & Temperature Sensitivity (Docx Q7)",
        question: "How sensitive are you to temperature and changing weather?",
        options: [
            { text: "Minimal sweating; feel chilly easily and dislike cold/windy weather", val: 0 },
            { text: "Sweat easily and profusely; dislike heat and direct sun", val: 1 },
            { text: "Sweat moderately with exertion; dislike cold, damp, or rainy weather", val: 2 }
        ]
    },
    {
        id: "morning_feeling",
        title: "Morning Feeling (Docx Q8 / Part 2 Q1)",
        question: "What is your usual morning feeling when you wake up?",
        options: [
            { text: "Energetic but sometimes restless or hurried", val: 0 },
            { text: "Active, motivated, and ready to start tasks immediately", val: 1 },
            { text: "Slow to wake up, prefers a relaxed pace, steady afterward", val: 2 }
        ]
    },
    {
        id: "eating_speed",
        title: "Eating Speed (Docx Q9 / Part 2 Q2)",
        question: "What is your usual eating speed during meals?",
        options: [
            { text: "Fast, hurried, and sometimes irregular", val: 0 },
            { text: "Moderate, focused, and steady pace", val: 1 },
            { text: "Slow, relaxed, and deliberate pace", val: 2 }
        ]
    },
    {
        id: "body_movement",
        title: "Body Movement Pace (Docx Q10 / Part 2 Q3)",
        question: "How would you describe your general body movements and walking pace?",
        options: [
            { text: "Fast movements; talk, walk, and gesture quickly", val: 0 },
            { text: "Moderate, purposeful, and coordinated movements", val: 1 },
            { text: "Slow, calm, graceful, and steady movements", val: 2 }
        ]
    },
    {
        id: "physical_stamina",
        title: "Exertion & Physical Stamina (Docx Q11 / Part 2 Q4)",
        question: "How does your body hold up during sustained physical exertion?",
        options: [
            { text: "Gets tired or fatigued quickly after exertion", val: 0 },
            { text: "Moderate to strong stamina; determined and focused", val: 1 },
            { text: "High endurance and sustained stamina without feeling drained", val: 2 }
        ]
    },
    {
        id: "hunger_pattern",
        title: "Daily Hunger Pattern (Docx Q12 / Part 2 Q5)",
        question: "How does your hunger develop throughout the day?",
        options: [
            { text: "Hunger varies unpredictably throughout the day", val: 0 },
            { text: "Feels hungry at sharp, regular, and predictable intervals", val: 1 },
            { text: "Can comfortably delay or skip meals without distress", val: 2 }
        ]
    },
    {
        id: "memory_retention",
        title: "Learning & Memory Retention (Docx Q13 / Part 2 Q6)",
        question: "How do you naturally absorb and recall new information?",
        options: [
            { text: "Learns quickly but may forget quickly if not reinforced", val: 0 },
            { text: "Has sharp, clear, and well-organized memory", val: 1 },
            { text: "Learns gradually and deliberately, but retains for a very long time", val: 2 }
        ]
    }
];

// Daily Ayurvedic Lifestyle Tips for the Dispensing Screen
const WELLNESS_TIPS = [
    {
        title: "Sip Warm Water Throughout the Day",
        body: "Drinking warm water or herbal teas stimulates your digestive fire (Agni), clears metabolic toxins (Ama), and prevents gut sluggishness."
    },
    {
        title: "Daily Gentle Yoga & Asanas",
        body: "Practicing 15 minutes of gentle yoga or Surya Namaskar in the morning opens your body's energy channels, enhances lung capacity, and relieves joint stiffness."
    },
    {
        title: "Mindful Deep Breathing (Pranayama)",
        body: "Taking 5 minutes for alternate-nostril breathing (Anulom Vilom) calms nervous tension, stabilizes blood pressure, and harmonizes Vata energy."
    },
    {
        title: "Eat Fresh, Warm Meals in Moderation",
        body: "Freshly prepared, lightly spiced warm foods are easiest for your stomach to break down. Avoid ice-cold drinks right with your meals."
    }
];


// ======================================================================================
// 1. SCREEN NAVIGATION CONTROLLER
// ======================================================================================
function navigateTo(targetScreenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });

    const targetScreen = document.getElementById(targetScreenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
        currentScreenId = targetScreenId;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}


// ======================================================================================
// 2. WELCOME SCREEN & KASHAYA MENU ACTIONS
// ======================================================================================

/**
 * Opens the dedicated Kashaya Menu screen (Kashaya A, B, and C)
 */
function openKashayaMenu() {
    navigateTo('screen-kashaya-menu');
}

/**
 * Initiates the AI Health Assessment Track:
 * - Resets screening inputs (no default options selected)
 * - Generates a fresh randomized set of 7 questions (4 core randomized + 3 from pool)
 * - Transitions to Step 1: Screening
 */
function startAssessment() {
    document.getElementById('inputAge').value = 28;
    
    // Clear gender selection by default - user must choose!
    document.getElementById('inputGender').value = "";
    document.querySelectorAll('.gender-pill').forEach(pill => pill.classList.remove('active'));
    
    // Hide female safety box by default
    const femaleBox = document.getElementById('femaleSafetyBox');
    if (femaleBox) femaleBox.classList.add('hidden');
    
    document.getElementById('checkPregnant').checked = false;
    document.getElementById('checkLactating').checked = false;

    // Reset symptom selection - no default symptom!
    document.querySelectorAll('input[name="symptom_choice"]').forEach(r => r.checked = false);

    generateDynamicSevenQuestions();
    navigateTo('screen-screening');
}

/**
 * Direct Instant Dispense Track (For Regular Tea & Selected Kashayas)
 */
function startDirectDispense(drinkName, subtitle, description, ingredients) {
    currentDispensingDrink = {
        name: drinkName,
        subtitle: subtitle,
        description: description,
        ingredients: ingredients
    };

    beginDispensingAnimation(drinkName, subtitle);
}


// ======================================================================================
// 3. THE DYNAMIC 7-QUESTION GENERATION ENGINE
// ======================================================================================

/**
 * Utility: Standard Fisher-Yates array shuffle
 */
function shuffleArray(array) {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

/**
 * Generates the exact 7 questions:
 * - Set 1: 4 core questions with their order randomized
 * - Set 2: 3 questions selected at random from the 9-question pool (Q5 - Q13)
 */
function generateDynamicSevenQuestions() {
    // 1. Shuffle Set 1 (4 core questions)
    const randomizedSet1 = shuffleArray(SET_1_CORE_QUESTIONS);

    // 2. Pick 3 random questions from Set 2 pool
    const shuffledSet2Pool = shuffleArray(SET_2_QUESTION_POOL);
    const selected3FromSet2 = shuffledSet2Pool.slice(0, 3);

    // 3. Combine to form the exact 7 questions for this user
    activeConsultationQuestions = [...randomizedSet1, ...selected3FromSet2];

    // 4. Render into DOM with NO pre-selected options
    renderActiveQuestions();
}

/**
 * Renders the active 7 questions into the UI with clean numbering and options.
 * BY DEFAULT NO OPTIONS ARE SELECTED - THE USER MUST CHOOSE EACH ONE!
 */
function renderActiveQuestions() {
    const container = document.getElementById('questionsContainer');
    container.innerHTML = '';

    activeConsultationQuestions.forEach((q, index) => {
        const card = document.createElement('div');
        card.className = 'question-card-item';

        let optionsHtml = '';
        q.options.forEach((opt) => {
            // NO 'checked' attribute: all options start unselected
            optionsHtml += `
                <label class="clean-option-card">
                    <input type="radio" name="${q.id}" value="${opt.val}">
                    <span class="option-indicator"></span>
                    <span class="option-desc">${opt.text}</span>
                </label>
            `;
        });

        card.innerHTML = `
            <div class="q-title-row">
                <span class="q-number">${index + 1}</span>
                <span class="q-question-text">${q.question}</span>
            </div>
            <div class="clean-options-grid">
                ${optionsHtml}
            </div>
        `;

        container.appendChild(card);
    });
}


// ======================================================================================
// 4. ASSESSMENT STEP 1: SCREENING & SAFETY GATES
// ======================================================================================

/**
 * Adjust age with stepper buttons
 */
function adjustAge(delta) {
    const ageInput = document.getElementById('inputAge');
    let currentAge = parseInt(ageInput.value, 10) || 28;
    currentAge = Math.max(1, Math.min(110, currentAge + delta));
    ageInput.value = currentAge;
    evaluateSafetyGate();
}

/**
 * Select gender via touch pills
 */
function selectGender(genderVal) {
    document.getElementById('inputGender').value = genderVal;

    document.querySelectorAll('.gender-pill').forEach(pill => {
        pill.classList.remove('active');
    });

    const activePill = document.getElementById(`pill-${genderVal}`);
    if (activePill) {
        activePill.classList.add('active');
    }

    const femaleBox = document.getElementById('femaleSafetyBox');
    if (genderVal === 'Female') {
        if (femaleBox) femaleBox.classList.remove('hidden');
    } else {
        if (femaleBox) {
            femaleBox.classList.add('hidden');
            document.getElementById('checkPregnant').checked = false;
            document.getElementById('checkLactating').checked = false;
        }
    }

    evaluateSafetyGate();
}

function handleGenderChange() {
    const gender = document.getElementById('inputGender').value;
    const femaleBox = document.getElementById('femaleSafetyBox');
    const isPregnant = document.getElementById('checkPregnant');
    const isLactating = document.getElementById('checkLactating');

    if (gender === 'Male' || gender === 'Other') {
        if (femaleBox) femaleBox.classList.add('hidden');
        if (isPregnant) isPregnant.checked = false;
        if (isLactating) isLactating.checked = false;
    } else if (gender === 'Female') {
        if (femaleBox) femaleBox.classList.remove('hidden');
    }
    evaluateSafetyGate();
}

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

document.getElementById('inputAge').addEventListener('input', evaluateSafetyGate);

function proceedFromScreening() {
    const age = parseInt(document.getElementById('inputAge').value, 10);
    const gender = document.getElementById('inputGender').value;
    const isPregnant = document.getElementById('checkPregnant').checked;

    if (isNaN(age) || age <= 0) {
        alert("Please enter a valid age.");
        return;
    }

    if (!gender) {
        alert("Please select your gender before proceeding.");
        return;
    }

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

/**
 * Validates that all 7 questions have been answered before moving to symptoms
 */
function proceedFromQuestions() {
    let unansweredCount = 0;
    activeConsultationQuestions.forEach(q => {
        const selected = document.querySelector(`input[name="${q.id}"]:checked`);
        if (!selected) {
            unansweredCount++;
        }
    });

    if (unansweredCount > 0) {
        alert(`Please answer all 7 questions to proceed (${unansweredCount} remaining).`);
        return;
    }

    navigateTo('screen-symptoms');
}


// ======================================================================================
// 5. ASSESSMENT STEP 3: SUBMIT CONSULTATION & API CALL
// ======================================================================================
async function submitAssessment() {
    const age = parseInt(document.getElementById('inputAge').value, 10) || 28;
    const gender = document.getElementById('inputGender').value || "Female";
    const isPregnant = document.getElementById('checkPregnant').checked;
    const isLactating = document.getElementById('checkLactating').checked;

    // Verify all 7 questions are answered
    const answers = {};
    let unansweredCount = 0;
    activeConsultationQuestions.forEach(q => {
        const selected = document.querySelector(`input[name="${q.id}"]:checked`);
        if (selected) {
            answers[q.id] = parseInt(selected.value, 10);
        } else {
            unansweredCount++;
        }
    });

    if (unansweredCount > 0) {
        alert("Please complete all questions before submitting.");
        navigateTo('screen-questions');
        return;
    }

    // Verify a symptom is chosen
    const symRadio = document.querySelector('input[name="symptom_choice"]:checked');
    if (!symRadio) {
        alert("Please tap a symptom to choose your health focus.");
        return;
    }
    const selectedSymptom = symRadio.value;

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
        alert("Failed to connect to the Ayurveda Engine. Please verify server connection.");
    }
}


// ======================================================================================
// 6. ASSESSMENT STEP 4: RESULT PAGE
// ======================================================================================
function setTextSafely(elementId, textValue) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = textValue || "";
    }
}

function populateResultScreen(data) {
    const diag = data.diagnosis;
    const presc = data.prescription;

    setTextSafely('resConstitution', diag.prakriti_label);
    setTextSafely('resMetabolism', diag.agni.type);
    setTextSafely('resSelectedSymptom', diag.selected_symptom);

    setTextSafely('resTeaCode', presc.tea_code);
    setTextSafely('resDrinkName', presc.tea_name);
    setTextSafely('resCategory', presc.category);
    setTextSafely('resAction', presc.clinical_action);
    setTextSafely('resIndication', presc.primary_indication);

    const ingList = document.getElementById('resIngredientsList');
    if (ingList) {
        ingList.innerHTML = '';
        presc.ingredients.forEach(ing => {
            const chip = document.createElement('span');
            chip.className = 'ingredient-pill';
            chip.textContent = ing;
            ingList.appendChild(chip);
        });
    }

    currentDispensingDrink = {
        name: presc.tea_name,
        subtitle: presc.category,
        ingredients: presc.ingredients
    };
}

function retakeAssessment() {
    startAssessment();
}

function triggerDispenseFromAssessment() {
    if (currentDispensingDrink) {
        beginDispensingAnimation(currentDispensingDrink.name, currentDispensingDrink.subtitle);
    }
}


// ======================================================================================
// 7. DISPENSING SCREEN: ANIMATION & ROTATING WELLNESS TIPS
// ======================================================================================
function beginDispensingAnimation(drinkName, subtitle) {
    navigateTo('screen-dispensing');

    document.getElementById('dispenseDrinkTitle').textContent = `Dispensing: ${drinkName}`;
    document.getElementById('dispenseDrinkSub').textContent = subtitle || "Freshly preparing and filtering your herbal beverage...";

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

    activeTipIndex = 0;
    updateActiveTipDisplay(activeTipIndex);

    if (dispenseInterval) clearInterval(dispenseInterval);
    if (tipRotationInterval) clearInterval(tipRotationInterval);

    tipRotationInterval = setInterval(() => {
        activeTipIndex = (activeTipIndex + 1) % WELLNESS_TIPS.length;
        updateActiveTipDisplay(activeTipIndex);
    }, 2800);

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

        for (let i = 0; i < stages.length; i++) {
            if (currentPct <= stages[i].at) {
                stepLabel.textContent = stages[i].text;
                break;
            }
        }

        if (currentPct >= 100) {
            clearInterval(dispenseInterval);
            clearInterval(tipRotationInterval);
            stepLabel.textContent = "✅ Freshly dispensed! Ready to drink.";
            completeBox.classList.remove('hidden');
        }
    }, 120);
}

function updateActiveTipDisplay(index) {
    const tip = WELLNESS_TIPS[index];
    document.getElementById('tipTitle').textContent = tip.title;
    document.getElementById('tipBody').textContent = tip.body;

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
    generateDynamicSevenQuestions();
});
