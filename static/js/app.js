// WellFit JavaScript - API Integration

const API_BASE = '';
const WF_NAME_KEY = 'wellfit_full_name';

/** Sync optional display name from profile API to localStorage and [data-wf-display-name] nodes */
function syncDisplayNameFromProfile(profile) {
    if (!profile) return;
    const n = profile.full_name != null && String(profile.full_name).trim()
        ? String(profile.full_name).trim()
        : '';
    if (n) localStorage.setItem(WF_NAME_KEY, n);
    else localStorage.removeItem(WF_NAME_KEY);
    document.querySelectorAll('[data-wf-display-name]').forEach((el) => {
        el.textContent = n || 'there';
    });
}

// Utility function to show messages
function showMessage(elementId, message, type) {
    const msgEl = document.getElementById(elementId);
    msgEl.textContent = message;
    msgEl.className = `message ${type}`;
    msgEl.style.display = 'block';
    setTimeout(() => {
        msgEl.style.display = 'none';
    }, 5000);
}

let _budgetHintTimer = null;

function _profileField(id) {
    return document.getElementById(id);
}

function _toNumber(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
}

function _setBudgetHint(html, isLow = false) {
    const hint = _profileField('budgetRecommendation');
    if (!hint) return;

    if (!html) {
        hint.style.display = 'none';
        hint.classList.remove('low');
        hint.innerHTML = '';
        return;
    }

    hint.innerHTML = html;
    hint.style.display = 'block';
    hint.classList.toggle('low', !!isLow);
}

function scheduleBudgetRecommendation() {
    if (_budgetHintTimer) clearTimeout(_budgetHintTimer);
    _budgetHintTimer = setTimeout(updateBudgetRecommendation, 350);
}

async function updateBudgetRecommendation() {
    const age = _toNumber(_profileField('age')?.value);
    const gender = _profileField('gender')?.value;
    const heightCm = _toNumber(_profileField('height_cm')?.value);
    const weightKg = _toNumber(_profileField('weight_kg')?.value);
    const fitnessGoal = _profileField('fitness_goal')?.value;
    const workoutDays = _toNumber(_profileField('workout_days')?.value);
    const dietType = _profileField('diet_type')?.value;
    const monthlyBudget = _toNumber(_profileField('monthly_budget')?.value);

    if (
        age == null || !gender || heightCm == null || weightKg == null ||
        !fitnessGoal || workoutDays == null || !dietType || monthlyBudget == null
    ) {
        _setBudgetHint('');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/budget-guidance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                age: parseInt(age, 10),
                gender,
                height_cm: parseFloat(heightCm),
                weight_kg: parseFloat(weightKg),
                fitness_goal: fitnessGoal,
                workout_days_per_week: parseInt(workoutDays, 10),
                diet_type: dietType,
                monthly_budget: parseFloat(monthlyBudget)
            })
        });

        if (!response.ok) {
            _setBudgetHint('');
            return;
        }

        const data = await response.json();
        const g = data?.budget_guidance;
        if (!g) {
            _setBudgetHint('');
            return;
        }

        const currentMonthly = Number(monthlyBudget).toFixed(2);
        const minMonthly = Number(g.estimated_min_monthly_budget).toFixed(2);
        const minDaily = Number(g.estimated_min_daily_budget).toFixed(2);
        const currentDaily = Number(g.daily_budget).toFixed(2);

        let html = `<strong>Recommended minimum budget:</strong> Rs.${minMonthly}/month (about Rs.${minDaily}/day).`;
        html += `<br><strong>Your current budget:</strong> Rs.${currentMonthly}/month (about Rs.${currentDaily}/day).`;

        if (g.is_budget_low) {
            html += '<br>Current budget may give lower calories/protein than target.';
        } else {
            html += '<br>Your current budget looks adequate for target planning.';
        }

        _setBudgetHint(html, g.is_budget_low);
    } catch (_) {
        _setBudgetHint('');
    }
}

function initProfileBudgetGuidance() {
    if (!_profileField('monthly_budget')) return;

    const watchedIds = [
        'age', 'gender', 'height_cm', 'weight_kg',
        'fitness_goal', 'workout_days', 'diet_type', 'monthly_budget'
    ];

    watchedIds.forEach((id) => {
        const el = _profileField(id);
        if (!el) return;
        el.addEventListener('input', scheduleBudgetRecommendation);
        el.addEventListener('change', scheduleBudgetRecommendation);
    });

    scheduleBudgetRecommendation();
}

// ── Toggle password visibility ───────────────────────────────────────────────
const EYE_OPEN = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>`;
const EYE_OFF = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.477 0-8.268-2.943-9.542-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.477 0 8.268 2.943 9.542 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>`;

function togglePw(inputId, btn) {
    const input = document.getElementById(inputId);
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    btn.innerHTML = show ? EYE_OFF : EYE_OPEN;
    btn.style.color = show ? '#667eea' : '#999';
}

// ── Register User ────────────────────────────────────────────────────────
async function registerUser(event) {
    event.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirm = document.getElementById('confirm_password').value;

    if (password !== confirm) {
        showMessage('message', 'Passwords do not match', 'error');
        return;
    }
    const strengthRegex = /(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}/;
    if (!strengthRegex.test(password)) {
        showMessage('message', 'Password must be ≥8 chars with upper, lower and a digit', 'error');
        return;
    }

    const btn = document.getElementById('registerBtn');
    btn.disabled = true;
    btn.textContent = 'Registering…';

    try {
        const res = await fetch(`${API_BASE}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok) {
            showMessage('message', '🎉 Account created! Redirecting to login…', 'success');
            setTimeout(() => window.location.href = '/login.html', 2000);
        } else {
            showMessage('message', data.error || 'Registration failed', 'error');
        }
    } catch (err) {
        showMessage('message', 'Network error: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Register';
    }
}

// Login user
async function login(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('message', 'Login successful! Redirecting...', 'success');
            localStorage.setItem('user_id', data.user.id);
            try {
                const pr = await fetch(`${API_BASE}/api/profile/${data.user.id}`, {
                    credentials: 'include'
                });
                if (pr.ok) {
                    const pd = await pr.json();
                    syncDisplayNameFromProfile(pd.profile);
                }
            } catch (_) { /* optional profile fetch */ }
            setTimeout(() => window.location.href = '/dashboard.html', 1500);
        } else {
            showMessage('message', data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage('message', 'Network error: ' + error.message, 'error');
    }
}

// Save profile
async function saveProfile(event) {
    event.preventDefault();

    const userId = localStorage.getItem('user_id') || 1;

    const fullNameEl = document.getElementById('full_name');
    const profileData = {
        user_id: parseInt(userId),
        full_name: fullNameEl ? fullNameEl.value.trim() : '',
        age: parseInt(document.getElementById('age').value),
        gender: document.getElementById('gender').value,
        height_cm: parseFloat(document.getElementById('height_cm').value),
        weight_kg: parseFloat(document.getElementById('weight_kg').value),
        fitness_goal: document.getElementById('fitness_goal').value,
        experience_level: document.getElementById('experience_level').value,
        workout_days_per_week: parseInt(document.getElementById('workout_days').value),
        workout_time_minutes: parseInt(document.getElementById('workout_time').value),
        diet_type: document.getElementById('diet_type').value,
        monthly_budget: parseFloat(document.getElementById('monthly_budget').value),
        workout_split_preference: document.getElementById('split_preference').value
    };

    try {
        const response = await fetch(`${API_BASE}/api/profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(profileData)
        });

        const data = await response.json();

        if (response.ok) {
            if (data.profile) syncDisplayNameFromProfile(data.profile);
            showMessage('message', 'Profile saved! Redirecting to dashboard...', 'success');
            setTimeout(() => window.location.href = '/dashboard.html', 1500);
        } else {
            if (response.status === 401) {
                showMessage('message', 'Session expired. Please login again.', 'error');
                setTimeout(() => window.location.href = '/login.html', 2000);
            } else {
                showMessage('message', data.error || 'Failed to save profile', 'error');
            }
        }
    } catch (error) {
        showMessage('message', 'Network error: ' + error.message, 'error');
    }
}

// Check if user has profile and load dashboard data
async function initDashboard() {
    try {
        const stored = localStorage.getItem(WF_NAME_KEY);
        if (stored && stored.trim()) {
            document.querySelectorAll('[data-wf-display-name]').forEach((el) => {
                el.textContent = stored.trim();
            });
        }

        const userId = localStorage.getItem('user_id') || 1;

        // Check if profile exists
        const profileResponse = await fetch(`${API_BASE}/api/profile/${userId}`, {
            credentials: 'include'
        });

        if (profileResponse.status === 401) {
            window.location.href = '/login.html';
            return;
        }

        if (profileResponse.status === 404) {
            showMessage('message', 'Please create your profile first', 'error');
            setTimeout(() => window.location.href = '/profile.html', 2000);
            return;
        }

        if (profileResponse.ok) {
            const profileData = await profileResponse.json();
            displayUserProfile(profileData.profile);
        }

        loadTodayPlan();

    } catch (error) {
        console.error('Dashboard init error:', error);
        showMessage('message', 'Failed to load dashboard. Please try again.', 'error');
    }
}

// Display user profile info in dashboard
function displayUserProfile(profile) {
    if (!profile) return;

    syncDisplayNameFromProfile(profile);

    const profileInfo = document.getElementById('profileInfo');
    if (profileInfo) {
        profileInfo.innerHTML = `
            <strong>${profile.age}y, ${profile.gender}</strong> |
            Goal: ${profile.fitness_goal.replace('_', ' ')} |
            ${profile.workout_days_per_week} days/week
        `;
    }
}

// Generate plans
async function generatePlans() {
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.textContent = 'Generating...';

    try {
        const response = await fetch(`${API_BASE}/api/generate-plan`, {
            method: 'POST',
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            if (data?.diet_plan?.warning) {
                showMessage('message', data.diet_plan.warning, 'warning');
            } else {
                showMessage('message', 'Plans generated successfully!', 'success');
            }
            loadTodayPlan();
        } else {
            if (response.status === 401) {
                showMessage('message', 'Session expired. Please login again.', 'error');
                setTimeout(() => window.location.href = '/login.html', 2000);
            } else {
                showMessage('message', data.error || 'Failed to generate plans', 'error');
            }
        }
    } catch (error) {
        showMessage('message', 'Network error: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate New Plan';
    }
}

// Load today's plan
async function loadTodayPlan() {
    try {
        const response = await fetch(`${API_BASE}/api/today-plan`, {
            credentials: 'include'
        });

        if (response.status === 401) {
            window.location.href = '/login.html';
            return;
        }

        const data = await response.json();

        if (response.ok && data.success) {
            displayDietPlan(data.diet_plan);
            displayWorkoutPlan(data.workout_plan);
        } else {
            document.getElementById('dietPlan').innerHTML = '<p>No diet plan for today. Generate a new plan!</p>';
            document.getElementById('workoutPlan').innerHTML = '<p>No workout plan for today. Generate a new plan!</p>';
        }
    } catch (error) {
        console.error('Error loading plan:', error);
    }
}

// Display diet plan
function displayDietPlan(dietPlan) {
    if (!dietPlan) return;

    const container = document.getElementById('dietPlan');
    const meals = dietPlan.meals || [];
    const totalCalories = Number(
        dietPlan.total_calories ?? meals.reduce((sum, m) => sum + (Number(m.calories) || 0), 0)
    );
    const totalProtein = Number(
        dietPlan.total_protein ?? meals.reduce((sum, m) => sum + (Number(m.protein_g) || 0), 0)
    );
    const totalCost = Number(
        dietPlan.total_cost ?? meals.reduce((sum, m) => sum + (Number(m.cost) || 0), 0)
    );
    const totalItems = Number(dietPlan.total_items ?? meals.length);

    let html = `<div class="stats">
        <div class="stat-box">
            <h3>${totalCost.toFixed(2)}</h3>
            <p>Cost (Rs.)</p>
        </div>
        <div class="stat-box">
            <h3>${totalCalories.toFixed(0)}</h3>
            <p>Total Calories</p>
        </div>
        <div class="stat-box">
            <h3>${totalProtein.toFixed(1)}g</h3>
            <p>Total Protein</p>
        </div>
        <div class="stat-box">
            <h3>${totalItems}</h3>
            <p>Total Items</p>
        </div>
    </div>`;

    if (dietPlan.warning) {
        html += `<div class="pain-alert" style="margin-top:8px;">
            <strong>Budget Guidance</strong>
            <p style="margin-top:6px;">${dietPlan.warning}</p>
            ${dietPlan.budget_guidance && dietPlan.budget_guidance.estimated_min_monthly_budget
                ? `<p style="margin-top:6px;"><strong>Recommended minimum monthly budget:</strong> Rs.${Number(dietPlan.budget_guidance.estimated_min_monthly_budget).toFixed(2)}</p>`
                : ''}
        </div>`;
    }

    const mealCard = (meal) => {
        const quantity = Number(meal.quantity_g) || 0;
        const calories = Number(meal.calories) || 0;
        const protein = Number(meal.protein_g) || 0;
        const cost = Number(meal.cost) || 0;

        return `<div class="plan-item">
            <p><strong>${meal.food_name}</strong></p>
            <p>Quantity: ${quantity.toFixed(0)}g | Calories: ${calories.toFixed(0)} | Protein: ${protein.toFixed(1)}g</p>
            <p>Cost: Rs.${cost.toFixed(2)}</p>
        </div>`;
    };

    const mealOrder = ['Breakfast', 'Lunch', 'Snack', 'Dinner'];
    const normalizeMealName = (meal) => {
        const raw = String(meal?.meal || meal?.meal_type || '').trim().toLowerCase();
        if (raw === 'breakfast') return 'Breakfast';
        if (raw === 'lunch') return 'Lunch';
        if (raw === 'snack' || raw === 'snacks') return 'Snack';
        if (raw === 'dinner') return 'Dinner';
        return 'Snack';
    };

    if (!meals || meals.length === 0) {
        container.innerHTML = `${html}<p class="loading">No meals in this plan.</p>`;
        return;
    }

    const groupedMeals = { Breakfast: [], Lunch: [], Snack: [], Dinner: [] };
    meals.forEach((meal) => {
        groupedMeals[normalizeMealName(meal)].push(meal);
    });

    html += '<div class="wf-diet-meals-scroll" role="region" aria-label="Meals list">';
    mealOrder.forEach((mealName) => {
        const items = groupedMeals[mealName];
        if (!items || items.length === 0) return;

        html += `<div class="plan-item"><h4>${mealName}</h4></div>`;
        items.forEach((meal) => {
            html += mealCard(meal);
        });
    });
    html += `<div class="plan-item">
        <h4>Diet Summary</h4>
        <p><strong>Total Calories:</strong> ${totalCalories.toFixed(0)} kcal</p>
        <p><strong>Total Protein:</strong> ${totalProtein.toFixed(1)} g</p>
        <p><strong>Total Items:</strong> ${totalItems}</p>
        <p><strong>Total Cost:</strong> Rs.${totalCost.toFixed(2)}</p>
    </div>`;
    html += '</div>';

    container.innerHTML = html;
}

// Display workout plan - accordion collapsible GIF cards
function displayWorkoutPlan(workoutPlan) {
    if (!workoutPlan) return;

    const container = document.getElementById('workoutPlan');
    const plan = workoutPlan.plan;
    const days = plan.weekly_plan || [];

    if (days.length === 0) {
        container.innerHTML = '<p>No workout days found. Generate a new plan!</p>';
        return;
    }

    // ---- Build day selector tabs ----
    let tabsHtml = `<div class="wb-split-label">💪 ${plan.split_type || ''}</div>
    <div class="wb-day-tabs" id="wbDayTabs">`;
    days.forEach((day, i) => {
        const shortName = `Day ${i + 1}`;
        tabsHtml += `<button class="wb-day-tab${i === 0 ? ' active' : ''}" onclick="showWorkoutDay(${i})">${shortName}</button>`;
    });
    tabsHtml += `</div>`;

    // ---- Build day panels with accordion cards ----
    let panelsHtml = '';
    days.forEach((day, dayIdx) => {
        panelsHtml += `<div class="wb-day-panel" id="wbPanel${dayIdx}" style="display:${dayIdx === 0 ? 'block' : 'none'}">`;

        if (day.exercises && day.exercises.length > 0) {
            day.exercises.forEach((ex, exIdx) => {
                const gifHtml = ex.gif_url
                    ? `<img src="${ex.gif_url}" alt="${ex.name}" class="wb-ex-gif" loading="lazy"
                         onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
                       <div class="wb-ex-gif-placeholder" style="display:none">🏋️</div>`
                    : `<div class="wb-ex-gif-placeholder">🏋️</div>`;

                // First card of each day starts expanded (class 'open')
                const isOpen = exIdx === 0;
                panelsHtml += `
                <div class="wb-ex-card${isOpen ? ' open' : ''}" id="wbCard${dayIdx}_${exIdx}">
                    <div class="wb-ex-card-header" onclick="toggleExCard(${dayIdx}, ${exIdx})">
                        <span class="wb-ex-card-name">${ex.name}</span>
                        <span class="wb-ex-card-meta">${ex.sets}×${ex.reps}</span>
                        <span class="wb-ex-chevron">${isOpen ? '▲' : '▼'}</span>
                    </div>
                    <div class="wb-ex-card-body" style="display:${isOpen ? 'flex' : 'none'}">
                        <div class="wb-ex-details">
                            <div class="wb-ex-stat"><span class="wb-ex-stat-label">Sets</span><span class="wb-ex-stat-value">${ex.sets}</span></div>
                            <div class="wb-ex-stat"><span class="wb-ex-stat-label">Reps</span><span class="wb-ex-stat-value">${ex.reps}</span></div>
                            <div class="wb-ex-stat"><span class="wb-ex-stat-label">Rest</span><span class="wb-ex-stat-value">${ex.rest_seconds}s</span></div>
                            <div class="wb-ex-muscle">${ex.muscle_groups || ex.category || ''}</div>
                            <div class="wb-ex-equip">🏷️ ${ex.equipment || 'bodyweight'}</div>
                        </div>
                        <div class="wb-ex-gif-wrap">${gifHtml}</div>
                    </div>
                </div>`;
            });
        } else {
            panelsHtml += `<p class="wb-rest-day">😴 Rest Day — recover and recharge!</p>`;
        }

        panelsHtml += `</div>`;
    });

    container.innerHTML = tabsHtml + panelsHtml;
}

// Toggle a single exercise card (accordion: collapse others in same day)
function toggleExCard(dayIdx, exIdx) {
    const clickedCard = document.getElementById(`wbCard${dayIdx}_${exIdx}`);
    const clickedBody = clickedCard.querySelector('.wb-ex-card-body');
    const clickedChevron = clickedCard.querySelector('.wb-ex-chevron');
    const isCurrentlyOpen = clickedCard.classList.contains('open');

    // Collapse ALL cards in this day panel first
    const panel = document.getElementById(`wbPanel${dayIdx}`);
    panel.querySelectorAll('.wb-ex-card').forEach(card => {
        card.classList.remove('open');
        card.querySelector('.wb-ex-card-body').style.display = 'none';
        card.querySelector('.wb-ex-chevron').textContent = '▼';
    });

    // If it was closed, now open it; if it was open, leave it collapsed
    if (!isCurrentlyOpen) {
        clickedCard.classList.add('open');
        clickedBody.style.display = 'flex';
        clickedChevron.textContent = '▲';
    }
}

// Switch visible workout day panel
function showWorkoutDay(index) {
    document.querySelectorAll('.wb-day-panel').forEach((p, i) => {
        p.style.display = i === index ? 'block' : 'none';
    });
    document.querySelectorAll('.wb-day-tab').forEach((t, i) => {
        t.classList.toggle('active', i === index);
    });
}





// Adapt workout for pain
async function adaptWorkout(event) {
    event.preventDefault();
    const painText = document.getElementById('painText').value;

    if (!painText.trim()) {
        showMessage('message', 'Please describe your pain', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/adapt-workout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ pain_text: painText })
        });

        const data = await response.json();

        if (response.ok) {
            showPainAlert(data);
            document.getElementById('painText').value = '';
        } else {
            if (response.status === 401) {
                window.location.href = '/login.html';
            } else {
                showMessage('message', data.error || 'Failed to adapt workout', 'error');
            }
        }
    } catch (error) {
        showMessage('message', 'Network error: ' + error.message, 'error');
    }
}

// Show pain adaptation alert and modified / mobility exercises
function showPainAlert(data) {
    const painResult = document.getElementById('painResult');
    if (painResult) painResult.style.display = 'block';

    const alert = document.getElementById('painAlert');
    const mobility = data.mobility_only === true;
    const title = mobility
        ? (data.no_workout_today ? 'No workout saved for today' : 'Recovery & mobility guidance')
        : `Pain guidance for ${data.affected_body_part || 'your feedback'}`;

    const msgBlock = data.message
        ? `<p style="margin:10px 0 0; line-height:1.5; color: inherit;">${data.message}</p>`
        : '';

    const separationNote = data.preview_only
        ? `<p style="margin:8px 0 0; font-size:0.88rem; opacity:0.9;">This pain/discomfort section is separate. Main workout tab remains unchanged.</p>`
        : '';

    alert.innerHTML = `
        <strong>${title}</strong>
        ${data.affected_body_part ? `<p style="margin:8px 0 0; opacity:0.95;">Area noted: ${data.affected_body_part}</p>` : ''}
        <p style="margin:8px 0 0; font-size:0.9rem; opacity:0.9;">
            ${data.severity ? `Severity: ${data.severity}` : ''}
            ${data.medical_attention_needed ? ' · If pain is severe or worsening, seek professional care.' : ''}
        </p>
        ${separationNote}
        ${msgBlock}
        ${data.modification_summary ? `<p style="margin:10px 0 0; font-size:0.88rem; opacity:0.9;">${data.modification_summary}</p>` : ''}
        ${data.immediate_action ? `<p style="margin:10px 0 0;"><em>${data.immediate_action}</em></p>` : ''}
    `;
    alert.style.display = 'block';

    const listContainer = document.getElementById('adaptedExercises');
    if (!listContainer) return;

    const cardStyle =
        'border-left:4px solid #a855f7; background:rgba(255,255,255,0.08); padding:12px; border-radius:8px; margin-bottom:10px;';
    const textStyle = 'color:rgba(255,255,255,0.88);';
    const subStyle = 'color:rgba(255,255,255,0.65); font-size:0.88rem;';

    if (data.modified_workout && data.modified_workout.length > 0) {
        let html = '';
        data.modified_workout.forEach((ex) => {
            html += `<div class="exercise-item" style="${cardStyle}">
                <strong style="${textStyle}">${ex.name}</strong>
                <span style="${subStyle}"> ${ex.sets} × ${ex.reps} · Rest ${ex.rest_seconds}s</span>
                ${ex.instructions ? `<p style="font-size:0.85rem; margin-top:6px; color:rgba(255,255,255,0.75);">${ex.instructions}</p>` : ''}
            </div>`;
        });
        listContainer.innerHTML = html;
    } else {
        listContainer.innerHTML = `<p style="${textStyle}">${data.message || 'Listen to your body — rest or very light movement if that feels better.'}</p>`;
    }
}

// Toggle profile dropdown
function toggleProfileMenu() {
    const dropdown = document.getElementById('profileDropdown');
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

// Close dropdown when clicking outside
document.addEventListener('click', function (event) {
    const dropdown = document.getElementById('profileDropdown');
    const profileIcon = document.querySelector('.profile-icon');

    if (dropdown && profileIcon && !profileIcon.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});

// Logout
async function logout() {
    try {
        await fetch(`${API_BASE}/api/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        localStorage.removeItem('user_id');
        localStorage.removeItem(WF_NAME_KEY);
        window.location.href = '/login.html';
    } catch (error) {
        console.error('Logout error:', error);
        localStorage.removeItem('user_id');
        localStorage.removeItem(WF_NAME_KEY);
        window.location.href = '/login.html';
    }
}



// Toggle between combined diet+workout view and pain tab
function showPlan(planType) {
    const plansTab = document.getElementById('plansTab');
    const painSection = document.getElementById('painPlanSection');
    const tabPlans = document.getElementById('tabPlans');
    const tabPain = document.getElementById('tabPain');

    if (!plansTab || !painSection) return;

    const showPlans = planType === 'plans' || planType === 'diet' || planType === 'workout';

    if (showPlans) {
        plansTab.style.display = 'block';
        painSection.style.display = 'none';
        tabPlans?.classList.add('wf-tab-active');
        tabPain?.classList.remove('wf-tab-active');
    } else if (planType === 'pain') {
        plansTab.style.display = 'none';
        painSection.style.display = 'block';
        tabPlans?.classList.remove('wf-tab-active');
        tabPain?.classList.add('wf-tab-active');
    }
}

// Load profile data into form (new function)
async function loadProfileData() {
    console.log("Loading profile data...");
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        return; // Not logged in, do nothing (user might be registering)
    }

    try {
        const response = await fetch(`${API_BASE}/api/profile/${userId}`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            const profile = data.profile;

            // Populate form fields
            const fields = [
                'full_name', 'age', 'gender', 'height_cm', 'weight_kg', 'fitness_goal',
                'experience_level', 'workout_days', 'workout_time',
                'diet_type', 'monthly_budget', 'split_preference'
            ];

            // Map specific fields if names differ from HTML IDs
            // HTML IDs: workout_days, workout_time, split_preference
            // API Keys: workout_days_per_week, workout_time_minutes, workout_split_preference
            const map = {
                'workout_days': 'workout_days_per_week',
                'workout_time': 'workout_time_minutes',
                'split_preference': 'workout_split_preference'
            };

            fields.forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    const key = map[id] || id;
                    if (profile[key] !== undefined) {
                        el.value = profile[key];
                    }
                }
            });

            console.log("Profile loaded successfully");
            scheduleBudgetRecommendation();
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}