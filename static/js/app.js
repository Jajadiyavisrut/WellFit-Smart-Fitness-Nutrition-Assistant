// WellFit JavaScript - API Integration

const API_BASE = '';

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

// ── Step 1: Send OTP ────────────────────────────────────────────────────────
async function sendOtp(event) {
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

    const btn = document.getElementById('sendOtpBtn');
    btn.disabled = true;
    btn.textContent = 'Sending OTP…';

    try {
        const res = await fetch(`${API_BASE}/api/send-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok) {
            showMessage('message', '✅ OTP sent! Check your inbox.', 'success');
            document.getElementById('emailDisplay').textContent = email;
            document.getElementById('registerSection').style.display = 'none';
            document.getElementById('otpSection').style.display = 'block';
            document.getElementById('step2bar').classList.add('active');
            document.getElementById('otpInput').focus();
        } else {
            showMessage('message', data.error || 'Failed to send OTP', 'error');
        }
    } catch (err) {
        showMessage('message', 'Network error: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Send OTP';
    }
}

// ── Step 2: Verify OTP ──────────────────────────────────────────────────────
async function verifyOtp(event) {
    event.preventDefault();
    const otp = document.getElementById('otpInput').value.trim();

    if (!/^\d{6}$/.test(otp)) {
        showMessage('message', 'Enter a valid 6-digit OTP', 'error');
        return;
    }

    const btn = document.getElementById('verifyBtn');
    btn.disabled = true;
    btn.textContent = 'Verifying…';

    try {
        const res = await fetch(`${API_BASE}/api/verify-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ otp })
        });
        const data = await res.json();

        if (res.ok) {
            showMessage('message', '🎉 Account created! Redirecting to login…', 'success');
            setTimeout(() => window.location.href = '/login.html', 2000);
        } else {
            showMessage('message', data.error || 'OTP verification failed', 'error');
        }
    } catch (err) {
        showMessage('message', 'Network error: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Verify OTP';
    }
}

// ── Go back to step 1 ───────────────────────────────────────────────────────
function goBack() {
    document.getElementById('otpSection').style.display = 'none';
    document.getElementById('registerSection').style.display = 'block';
    document.getElementById('step2bar').classList.remove('active');
    document.getElementById('otpInput').value = '';
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

    const profileData = {
        user_id: parseInt(userId),
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
            showMessage('message', 'Plans generated successfully!', 'success');
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
    const meals = dietPlan.meals;

    let html = `<div class="stats">
        <div class="stat-box">
            <h3>${dietPlan.total_cost.toFixed(2)}</h3>
            <p>Cost (Rs.)</p>
        </div>
    </div>`;

    meals.forEach(meal => {
        html += `<div class="plan-item">
            <h4>${meal.meal_type || 'Meal'}</h4>
            <p><strong>${meal.food_name}</strong></p>
            <p>Quantity: ${meal.quantity_g}g | Calories: ${meal.calories.toFixed(0)} | Protein: ${meal.protein_g.toFixed(1)}g</p>
            <p>Cost: Rs.${meal.cost.toFixed(2)}</p>
        </div>`;
    });

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
            loadTodayPlan();
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

// Show pain adaptation alert
// Show pain adaptation alert and modified workout
function showPainAlert(data) {
    // Show the result container
    document.getElementById('painResult').style.display = 'block';

    const alert = document.getElementById('painAlert');
    alert.innerHTML = `
        <strong>Workout Adapted for ${data.affected_body_part || 'Pain'}</strong>
        <p>Severity: ${data.severity} | Medical Attention: ${data.medical_attention_needed ? 'Yes' : 'No'}</p>
        <p>${data.modification_summary}</p>
        <p><em>${data.immediate_action}</em></p>
    `;
    alert.style.display = 'block';

    // Render the exercises
    const listContainer = document.getElementById('adaptedExercises');
    if (data.modified_workout && data.modified_workout.length > 0) {
        let html = '';
        data.modified_workout.forEach(ex => {
            html += `<div class="exercise-item" style="border-left: 4px solid #48bb78; background: #f0fff4;">
                <strong>${ex.name}</strong>
                <span>${ex.sets} sets × ${ex.reps} reps | Rest: ${ex.rest_seconds}s</span>
                ${ex.instructions ? `<p style="font-size:0.85rem; color:#666; margin-top:5px;">${ex.instructions}</p>` : ''}
            </div>`;
        });
        listContainer.innerHTML = html;
    } else {
        listContainer.innerHTML = '<p>No exercises for today (Rest Day).</p>';
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
        window.location.href = '/login.html';
    } catch (error) {
        console.error('Logout error:', error);
        localStorage.removeItem('user_id');
        window.location.href = '/login.html';
    }
}

// Chatbot for workout modifications
let chatHistory = [];

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addChatMessage('user', message);
    input.value = '';


    // Show typing indicator
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.style.cssText = 'display: flex; gap: 10px; margin-bottom: 16px;';
    typingDiv.innerHTML = `
        <div style="background: white; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0;">
            💪
        </div>
        <div style="background: white; padding: 12px 16px; border-radius: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
            <div style="display: flex; gap: 4px; align-items: center;">
                <div style="width: 8px; height: 8px; background: #999; border-radius: 50%; animation: typing 1.4s infinite;"></div>
                <div style="width: 8px; height: 8px; background: #999; border-radius: 50%; animation: typing 1.4s infinite 0.2s;"></div>
                <div style="width: 8px; height: 8px; background: #999; border-radius: 50%; animation: typing 1.4s infinite 0.4s;"></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;


    try {
        const response = await fetch(`${API_BASE}/api/chat-workout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ message: message, history: chatHistory })
        });

        const data = await response.json();

        // Remove typing indicator
        typingDiv.remove();

        if (response.ok) {
            addChatMessage('bot', data.response);
            chatHistory.push({ user: message, bot: data.response });

            // If workout was modified, reload the plan
            if (data.workout_modified) {
                loadTodayPlan();
            }
        } else {
            addChatMessage('bot', 'Sorry, I encountered an error. Please try again.');
        }
    } catch (error) {
        typingDiv.remove();
        addChatMessage('bot', 'Network error. Please check your connection.');
    }
}

function addChatMessage(sender, message) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');

    if (sender === 'bot') {
        messageDiv.style.cssText = 'display: flex; gap: 10px; margin-bottom: 16px;';
        messageDiv.innerHTML = `
            <div style="background: white; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0;">
                💪
            </div>
            <div style="background: white; padding: 12px 16px; border-radius: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); max-width: 75%;">
                <p style="margin: 0; color: #333; line-height: 1.5;">${message}</p>
            </div>
        `;
    } else {
        messageDiv.style.cssText = 'display: flex; gap: 10px; margin-bottom: 16px; justify-content: flex-end;';
        messageDiv.innerHTML = `
            <div style="background: #1e88e5; padding: 12px 16px; border-radius: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); max-width: 75%;">
                <p style="margin: 0; color: white; line-height: 1.5;">${message}</p>
            </div>
        `;
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function toggleChat() {
    const chatbot = document.getElementById('chatbot');
    chatbot.style.display = chatbot.style.display === 'none' ? 'flex' : 'none';
}

// Handle Enter key in chat input
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
});

// Toggle between diet, workout, and pain plans
function showPlan(planType) {
    const dietSection = document.getElementById('dietPlanSection');
    const workoutSection = document.getElementById('workoutPlanSection');
    const painSection = document.getElementById('painPlanSection');
    const dietToggle = document.getElementById('dietToggle');
    const workoutToggle = document.getElementById('workoutToggle');
    const painToggle = document.getElementById('painToggle');

    // Hide all sections
    dietSection.style.display = 'none';
    workoutSection.style.display = 'none';
    painSection.style.display = 'none';

    // Reset all button styles
    dietToggle.style.background = 'transparent';
    dietToggle.style.color = '#666';
    workoutToggle.style.background = 'transparent';
    workoutToggle.style.color = '#666';
    painToggle.style.background = 'transparent';
    painToggle.style.color = '#666';

    // Show selected section and highlight button
    if (planType === 'diet') {
        dietSection.style.display = 'block';
        dietToggle.style.background = '#667eea';
        dietToggle.style.color = 'white';
    } else if (planType === 'workout') {
        workoutSection.style.display = 'block';
        workoutToggle.style.background = '#667eea';
        workoutToggle.style.color = 'white';
    } else if (planType === 'pain') {
        painSection.style.display = 'block';
        painToggle.style.background = '#667eea';
        painToggle.style.color = 'white';
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
                'age', 'gender', 'height_cm', 'weight_kg', 'fitness_goal',
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
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}