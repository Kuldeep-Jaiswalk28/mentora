document.addEventListener('DOMContentLoaded', function() {
    // Initialize the app
    initApp();
});

// Global state for the application
const appState = {
    schedule: null,
    progress: null,
    categories: [],
    goals: [],
    tasks: [],
    messages: []
};

// Initialize the application
function initApp() {
    // Load all data
    loadSchedule();
    loadProgress();
    loadCategories();
    loadGoals();
    loadTasks();
    loadChatHistory();

    // Set up event listeners
    setupEventListeners();
    
    // Set up auto-refresh for schedule and progress
    setInterval(loadSchedule, 60000); // Refresh schedule every minute
    setInterval(loadProgress, 60000); // Refresh progress every minute
}

// Load today's schedule
function loadSchedule() {
    fetch('/api/blueprints/today_schedule')
        .then(response => response.json())
        .then(data => {
            appState.schedule = data;
            renderSchedule(data);
        })
        .catch(error => {
            console.error('Error loading schedule:', error);
            document.getElementById('schedule-container').innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Could not load your schedule. Please try again later.
                </div>
            `;
        });
}

// Render the schedule on the page
function renderSchedule(data) {
    const container = document.getElementById('schedule-container');
    
    if (!data.has_schedule) {
        container.innerHTML = `
            <div class="text-center p-4">
                <p class="mb-3">No schedule blueprint for today.</p>
                <button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#blueprintModal">
                    <i class="bi bi-calendar-plus me-1"></i> Create Schedule
                </button>
            </div>
        `;
        return;
    }
    
    // Start building the schedule HTML
    let html = `
        <div class="schedule-header mb-3">
            <h6 class="text-muted mb-0">Following "${data.blueprint_name}" blueprint</h6>
        </div>
        <div class="schedule-timeline">
    `;
    
    // Add time slots
    if (data.time_slots.length === 0) {
        html += `
            <p class="text-center text-muted">No time slots in this blueprint.</p>
        `;
    } else {
        // Get current time to identify current slot
        const now = new Date();
        const currentHour = now.getHours();
        const currentMinute = now.getMinutes();
        
        // Sort time slots by start time
        const sortedSlots = [...data.time_slots].sort((a, b) => {
            return a.start_time.localeCompare(b.start_time);
        });
        
        // Add each time slot
        sortedSlots.forEach(slot => {
            // Parse start and end times
            const [startHour, startMinute] = slot.start_time.split(':').map(Number);
            const [endHour, endMinute] = slot.end_time.split(':').map(Number);
            
            // Check if this is the current slot
            const isCurrent = 
                (currentHour > startHour || (currentHour === startHour && currentMinute >= startMinute)) && 
                (currentHour < endHour || (currentHour === endHour && currentMinute < endMinute));
            
            // Create HTML for the slot
            html += `
                <div class="time-slot ${isCurrent ? 'current-slot' : ''}" style="border-left-color: ${slot.category_color || '#6c757d'}">
                    <div class="time-slot-header">
                        <span class="time-label">${slot.start_time} - ${slot.end_time}</span>
                        <span class="badge" style="background-color: ${slot.category_color || '#6c757d'}">
                            ${slot.category_name || 'Uncategorized'}
                        </span>
                    </div>
                    <div class="time-slot-title">${slot.title}</div>
                    ${slot.description ? `<div class="time-slot-description">${slot.description}</div>` : ''}
                    ${slot.goal_title ? `
                        <div class="time-slot-goal mt-2">
                            <span class="badge bg-secondary">
                                <i class="bi bi-flag-fill me-1"></i> ${slot.goal_title}
                            </span>
                        </div>
                    ` : ''}
                </div>
            `;
        });
    }
    
    html += `</div>`;
    container.innerHTML = html;
}

// Load progress data
function loadProgress() {
    fetch('/api/progress/overall')
        .then(response => response.json())
        .then(data => {
            appState.progress = data;
            renderProgress(data);
        })
        .catch(error => {
            console.error('Error loading progress:', error);
        });
}

// Render progress data on the page
function renderProgress(data) {
    // Update today's tasks progress
    const todayCompletion = document.getElementById('today-completion');
    const todayProgress = document.getElementById('today-progress');
    
    if (data.today_total_tasks > 0) {
        todayCompletion.textContent = `${data.today_completed_tasks}/${data.today_total_tasks}`;
        todayProgress.style.width = `${data.today_completion_rate}%`;
        todayProgress.setAttribute('aria-valuenow', data.today_completion_rate);
    } else {
        todayCompletion.textContent = '0/0';
        todayProgress.style.width = '0%';
        todayProgress.setAttribute('aria-valuenow', 0);
    }
    
    // Update streak count
    const streakCount = document.getElementById('streak-count');
    streakCount.textContent = `${data.streak} days`;
    
    // Update streak calendar
    updateStreakCalendar(data.recent_progress);
    
    // Update categories progress
    renderCategoriesProgress(data.category_stats);
}

// Update the streak calendar
function updateStreakCalendar(recentProgress) {
    if (!recentProgress || recentProgress.length === 0) return;
    
    const today = new Date();
    const dayOfWeek = today.getDay(); // 0 = Sunday, 1 = Monday, etc.
    const daysOfWeek = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
    
    // Adjust to start with Monday (index 1)
    const adjustedDayOfWeek = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    
    // Get all streak circles
    const streakCircles = document.querySelectorAll('.streak-circle');
    
    // Reset all circles
    streakCircles.forEach(circle => {
        circle.classList.remove('completed', 'today');
    });
    
    // Mark today's circle
    streakCircles[adjustedDayOfWeek].classList.add('today');
    
    // Mark completed days based on recent progress
    recentProgress.slice(-7).forEach((dayProgress, index) => {
        const dayDate = new Date(dayProgress.date);
        const dayIndex = dayDate.getDay() === 0 ? 6 : dayDate.getDay() - 1;
        
        if (dayProgress.completion_rate > 0) {
            streakCircles[dayIndex].classList.add('completed');
        }
    });
}

// Render categories progress
function renderCategoriesProgress(categories) {
    if (!categories || categories.length === 0) return;
    
    const container = document.getElementById('categories-container');
    let html = '';
    
    categories.forEach(category => {
        html += `
            <div class="category-item">
                <div class="category-color" style="background-color: ${category.color}"></div>
                <div class="category-info">
                    <div class="category-name">
                        <span>${category.name}</span>
                        <small>${category.completed_tasks}/${category.total_tasks}</small>
                    </div>
                    <div class="category-progress-bar">
                        <div class="category-progress-value" style="width: ${category.completion_rate}%; background-color: ${category.color}"></div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Load categories
function loadCategories() {
    fetch('/api/categories')
        .then(response => response.json())
        .then(data => {
            appState.categories = data.categories;
        })
        .catch(error => {
            console.error('Error loading categories:', error);
        });
}

// Load goals
function loadGoals() {
    fetch('/api/goals')
        .then(response => response.json())
        .then(data => {
            appState.goals = data.goals;
            
            // Populate goal dropdown in the add task form
            const goalSelect = document.getElementById('task-goal');
            if (goalSelect) {
                let options = '<option value="" disabled selected>Select a goal</option>';
                
                data.goals.forEach(goal => {
                    options += `<option value="${goal.id}">${goal.title}</option>`;
                });
                
                goalSelect.innerHTML = options;
            }
        })
        .catch(error => {
            console.error('Error loading goals:', error);
        });
}

// Load tasks
function loadTasks() {
    fetch('/api/tasks?prioritized=true')
        .then(response => response.json())
        .then(data => {
            appState.tasks = data.tasks;
        })
        .catch(error => {
            console.error('Error loading tasks:', error);
        });
}

// Load chat history
function loadChatHistory() {
    fetch('/api/mentor/chat')
        .then(response => response.json())
        .then(data => {
            if (data.messages && Array.isArray(data.messages)) {
                appState.messages = data.messages;
                renderChatMessages(data.messages);
            }
        })
        .catch(error => {
            console.error('Error loading chat history:', error);
            document.getElementById('chat-messages').innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Could not load chat history. Please try again later.
                </div>
            `;
        });
}

// Render chat messages
function renderChatMessages(messages) {
    if (!messages || messages.length === 0) {
        document.getElementById('chat-messages').innerHTML = `
            <div class="text-center p-4">
                <p class="mb-3">No messages yet. Start chatting with your mentor!</p>
            </div>
        `;
        return;
    }
    
    const container = document.getElementById('chat-messages');
    let html = '';
    
    messages.forEach(message => {
        const time = new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        html += `
            <div class="message ${message.is_from_user ? 'user-message' : 'ai-message'}">
                <div class="message-content">${message.message}</div>
                <div class="message-time">${time}</div>
                ${!message.is_from_user ? `
                    <div class="message-feedback">
                        <button class="feedback-btn feedback-helpful" data-message-id="${message.id}">
                            <i class="bi bi-hand-thumbs-up"></i>
                        </button>
                        <button class="feedback-btn feedback-unhelpful" data-message-id="${message.id}">
                            <i class="bi bi-hand-thumbs-down"></i>
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Scroll to the bottom
    container.scrollTop = container.scrollHeight;
}

// Send a message to the AI mentor
function sendMessage(message) {
    // Disable the input and button while sending
    const messageInput = document.getElementById('message-input');
    const sendButton = document.querySelector('#chat-form button[type="submit"]');
    
    messageInput.disabled = true;
    sendButton.disabled = true;
    
    // Add the user message to the chat
    const userMessage = {
        id: Date.now(), // Temporary ID
        is_from_user: true,
        message: message,
        timestamp: new Date().toISOString()
    };
    
    appState.messages.push(userMessage);
    renderChatMessages(appState.messages);
    
    // Send the message to the backend
    fetch('/api/mentor/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        // Add the AI response to the chat
        const aiMessage = {
            id: Date.now() + 1, // Temporary ID
            is_from_user: false,
            message: data.response,
            timestamp: new Date().toISOString()
        };
        
        appState.messages.push(aiMessage);
        renderChatMessages(appState.messages);
        
        // Re-enable the input and button
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.value = '';
        messageInput.focus();
    })
    .catch(error => {
        console.error('Error sending message:', error);
        
        // Show error in the chat
        const errorMessage = {
            id: Date.now() + 1,
            is_from_user: false,
            message: 'Sorry, I encountered an error processing your request. Please try again.',
            timestamp: new Date().toISOString()
        };
        
        appState.messages.push(errorMessage);
        renderChatMessages(appState.messages);
        
        // Re-enable the input and button
        messageInput.disabled = false;
        sendButton.disabled = false;
    });
}

// Set up event listeners
function setupEventListeners() {
    // Chat form submission
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const messageInput = document.getElementById('message-input');
            const message = messageInput.value.trim();
            
            if (message) {
                sendMessage(message);
            }
        });
    }
    
    // Quick chat buttons
    document.getElementById('focus-btn')?.addEventListener('click', () => {
        sendMessage('What should I focus on next?');
    });
    
    document.getElementById('motivate-btn')?.addEventListener('click', () => {
        sendMessage('I need some motivation right now.');
    });
    
    document.getElementById('progress-btn')?.addEventListener('click', () => {
        sendMessage('How am I doing on my goals?');
    });
    
    // Settings form
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        document.getElementById('save-settings')?.addEventListener('click', function() {
            // Collect settings and send to backend
            const settings = {
                theme: document.getElementById('theme-select').value,
                font_size: document.getElementById('font-size-select').value,
                enable_voice: document.getElementById('enable-voice').checked,
                daily_review_time: document.getElementById('daily-review-time').value,
                do_not_disturb: document.getElementById('do-not-disturb').checked
            };
            
            fetch('/api/preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
                modal.hide();
                
                // Apply theme changes immediately
                document.documentElement.setAttribute('data-bs-theme', settings.theme);
                
                // Show success toast
                alert('Settings saved successfully!');
            })
            .catch(error => {
                console.error('Error saving settings:', error);
                alert('Error saving settings. Please try again.');
            });
        });
    }
    
    // Task form
    const taskForm = document.getElementById('task-form');
    if (taskForm) {
        document.getElementById('save-task')?.addEventListener('click', function() {
            // Collect task data and send to backend
            const taskData = {
                title: document.getElementById('task-title').value,
                description: document.getElementById('task-description').value,
                goal_id: parseInt(document.getElementById('task-goal').value, 10),
                deadline: document.getElementById('task-deadline').value,
                priority: parseInt(document.getElementById('task-priority').value, 10),
                recurrence_type: document.getElementById('task-recurrence').value || null,
                recurrence_value: document.getElementById('task-recurrence').value ? 1 : null
            };
            
            fetch('/api/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(taskData)
            })
            .then(response => response.json())
            .then(data => {
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addTaskModal'));
                modal.hide();
                
                // Refresh tasks
                loadTasks();
                loadProgress();
                
                // Show success toast
                alert('Task created successfully!');
            })
            .catch(error => {
                console.error('Error creating task:', error);
                alert('Error creating task. Please try again.');
            });
        });
    }
    
    // Blueprint form
    const blueprintForm = document.getElementById('blueprint-form');
    if (blueprintForm) {
        document.getElementById('save-blueprint')?.addEventListener('click', function() {
            // Collect blueprint data and send to backend
            const blueprintData = {
                name: document.getElementById('blueprint-name').value,
                description: document.getElementById('blueprint-description').value,
                day_of_week: document.getElementById('blueprint-day').value || null,
                is_active: document.getElementById('blueprint-active').checked
            };
            
            fetch('/api/blueprints', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(blueprintData)
            })
            .then(response => response.json())
            .then(data => {
                // Switch to the view tab
                const viewTab = document.querySelector('#blueprintTabs button[data-bs-target="#view-tab-pane"]');
                bootstrap.Tab.getInstance(viewTab).show();
                
                // Refresh blueprints list
                loadBlueprints();
                
                // Show success toast
                alert('Blueprint created successfully!');
            })
            .catch(error => {
                console.error('Error creating blueprint:', error);
                alert('Error creating blueprint. Please try again.');
            });
        });
    }
}

// Load blueprint list
function loadBlueprints() {
    fetch('/api/blueprints')
        .then(response => response.json())
        .then(data => {
            renderBlueprints(data.blueprints);
        })
        .catch(error => {
            console.error('Error loading blueprints:', error);
            document.getElementById('blueprints-list').innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Could not load blueprints. Please try again later.
                </div>
            `;
        });
}

// Render blueprints list
function renderBlueprints(blueprints) {
    if (!blueprints || blueprints.length === 0) {
        document.getElementById('blueprints-list').innerHTML = `
            <div class="text-center p-4">
                <p class="mb-3">No blueprints created yet.</p>
            </div>
        `;
        return;
    }
    
    const container = document.getElementById('blueprints-list');
    let html = '<div class="list-group">';
    
    blueprints.forEach(blueprint => {
        html += `
            <div class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${blueprint.name}</h5>
                    <small>${blueprint.day_of_week || 'Any day'}</small>
                </div>
                <p class="mb-1">${blueprint.description || 'No description'}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="badge ${blueprint.is_active ? 'bg-success' : 'bg-secondary'}">
                        ${blueprint.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary view-slots-btn" data-blueprint-id="${blueprint.id}">
                            <i class="bi bi-clock"></i> View Slots
                        </button>
                        <button type="button" class="btn btn-outline-secondary edit-blueprint-btn" data-blueprint-id="${blueprint.id}">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger delete-blueprint-btn" data-blueprint-id="${blueprint.id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
    
    // Add event listeners to the buttons
    document.querySelectorAll('.view-slots-btn').forEach(button => {
        button.addEventListener('click', function() {
            const blueprintId = this.getAttribute('data-blueprint-id');
            loadTimeSlots(blueprintId);
        });
    });
    
    document.querySelectorAll('.edit-blueprint-btn').forEach(button => {
        button.addEventListener('click', function() {
            const blueprintId = this.getAttribute('data-blueprint-id');
            editBlueprint(blueprintId);
        });
    });
    
    document.querySelectorAll('.delete-blueprint-btn').forEach(button => {
        button.addEventListener('click', function() {
            const blueprintId = this.getAttribute('data-blueprint-id');
            deleteBlueprint(blueprintId);
        });
    });
}

// Function to provide feedback on mentor messages
function provideFeedback(messageId, isHelpful) {
    fetch(`/api/mentor/feedback/${messageId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_helpful: isHelpful })
    })
    .then(response => response.json())
    .then(data => {
        // Show a small notification that feedback was recorded
        alert(isHelpful ? 'Feedback recorded: Helpful' : 'Feedback recorded: Not helpful');
    })
    .catch(error => {
        console.error('Error providing feedback:', error);
    });
}