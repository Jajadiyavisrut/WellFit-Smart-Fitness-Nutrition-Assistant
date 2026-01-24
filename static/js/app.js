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

// Register user
async function register(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('message', 'Registration successful! Redirecting to login...', 'success');
            setTimeout(() => window.location.href = '/login.html', 2000);
        } else {
            showMessage('message', data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showMessage('message', 'Network error: ' + error.message, 'error');
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
        monthly_budget: parseFloat(document.getElementById('monthly_budget').value)
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

// Display workout plan - UPDATED to show all days
function displayWorkoutPlan(workoutPlan) {
    if (!workoutPlan) return;

    const container = document.getElementById('workoutPlan');
    const plan = workoutPlan.plan;

    let html = `<p><strong>Split:</strong> ${plan.split_type}</p>`;

    if (plan.weekly_plan && plan.weekly_plan.length > 0) {
        // Show all days in the weekly plan
        plan.weekly_plan.forEach((day, index) => {
            html += `<div class="workout-day" style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <h4 style="color: #667eea; margin-bottom: 10px;">${day.day_name}</h4>`;

            if (day.exercises && day.exercises.length > 0) {
                day.exercises.forEach(ex => {
                    html += `<div class="exercise-item">
                        <strong>${ex.name}</strong>
                        <span>${ex.sets} sets × ${ex.reps} reps | Rest: ${ex.rest_seconds}s</span>
                    </div>`;
                });
            } else {
                html += `<p style="color: #666; font-style: italic;">Rest Day</p>`;
            }

            html += `</div>`;
        });
    }

    container.innerHTML = html;
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
        const response = await fetch(`${API_BASE}/api/adaptive-workout`, {
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
    typingDiv.className = 'chat-message bot typing';
    typingDiv.innerHTML = '<span>Typing...</span>';
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
    messageDiv.className = `chat-message ${sender}`;
    messageDiv.innerHTML = `<span>${message}</span>`;
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
