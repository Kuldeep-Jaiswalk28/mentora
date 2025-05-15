// Mentora - AI Mentor and Goal Tracking Application
// Frontend JavaScript for interacting with the backend API

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    feather.replace();
    
    // Initialize global variables
    let currentView = 'dashboard';
    let currentGoals = [];
    let currentTasks = [];
    let currentCategories = [];
    let currentReminders = [];
    
    // ====================================================
    // Navigation and View Handling
    // ====================================================
    
    // Show the selected view and hide others
    function showView(viewName) {
        document.getElementById('dashboardView').style.display = viewName === 'dashboard' ? 'block' : 'none';
        document.getElementById('goalView').style.display = viewName === 'goals' ? 'block' : 'none';
        document.getElementById('tasksView').style.display = viewName === 'tasks' ? 'block' : 'none';
        document.getElementById('categoriesView').style.display = viewName === 'categories' ? 'block' : 'none';
        document.getElementById('remindersView').style.display = viewName === 'reminders' ? 'block' : 'none';
        document.getElementById('progressView').style.display = viewName === 'progress' ? 'block' : 'none';
        
        currentView = viewName;
        
        // Load content for the selected view
        if (viewName === 'dashboard') {
            loadDashboard();
        } else if (viewName === 'goals') {
            loadGoals();
        } else if (viewName === 'tasks') {
            loadTasks();
        } else if (viewName === 'categories') {
            loadCategories();
        } else if (viewName === 'reminders') {
            loadReminders();
        } else if (viewName === 'progress') {
            loadProgress();
        }
    }
    
    // Set up navigation event listeners
    document.querySelectorAll('.nav-link').forEach(navLink => {
        navLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all nav links
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Extract view name from href attribute
            const viewName = this.getAttribute('href').substring(1);
            showView(viewName);
        });
    });
    
    // ====================================================
    // API Functions
    // ====================================================
    
    // Handle API errors
    function handleApiError(error) {
        console.error('API Error:', error);
        // Show error toast or notification
        alert(`Error: ${error.message || 'An unexpected error occurred'}`);
    }
    
    // Fetch data from API
    async function fetchData(endpoint) {
        try {
            const response = await fetch(`/api/${endpoint}`);
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            handleApiError(error);
            return null;
        }
    }
    
    // Post data to API
    async function postData(endpoint, data) {
        try {
            const response = await fetch(`/api/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `API Error: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            handleApiError(error);
            return null;
        }
    }
    
    // Put data to API
    async function putData(endpoint, data) {
        try {
            const response = await fetch(`/api/${endpoint}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `API Error: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            handleApiError(error);
            return null;
        }
    }
    
    // Delete data from API
    async function deleteData(endpoint) {
        try {
            const response = await fetch(`/api/${endpoint}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `API Error: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            handleApiError(error);
            return null;
        }
    }
    
    // ====================================================
    // Dashboard View
    // ====================================================
    
    // Load dashboard content
    async function loadDashboard() {
        // Load categories (needed for other data)
        await loadCategoriesData();
        
        // Load next tasks
        loadNextTasks();
        
        // Load overall progress
        loadOverallProgress();
        
        // Load goals progress
        loadGoalsProgress();
        
        // Load categories list
        renderCategoriesList();
        
        // Load recent activity
        loadRecentActivity();
    }
    
    // Load and render next tasks
    async function loadNextTasks() {
        const nextTasksContainer = document.getElementById('nextTasksList');
        nextTasksContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const tasks = await fetchData('tasks/daily');
        
        if (!tasks || tasks.length === 0) {
            nextTasksContainer.innerHTML = '<div class="alert alert-info">No tasks for today! Add new tasks to get started.</div>';
            return;
        }
        
        let tasksHtml = '';
        tasks.forEach(task => {
            const priorityClass = task.priority === 1 ? 'priority-high' : 
                                  task.priority === 2 ? 'priority-medium' : 'priority-low';
            const priorityLabel = task.priority === 1 ? 'High' : 
                                  task.priority === 2 ? 'Medium' : 'Low';
            const deadlineDisplay = task.deadline ? new Date(task.deadline).toLocaleString() : 'No deadline';
            
            tasksHtml += `
                <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center ${priorityClass} task-card">
                    <div class="ms-2 me-auto">
                        <div class="fw-bold">${task.title}</div>
                        <small>${task.description || 'No description'}</small>
                        <div class="mt-2">
                            <span class="badge bg-secondary">${findGoalTitle(task.goal_id)}</span>
                            <span class="badge bg-${task.priority === 1 ? 'danger' : task.priority === 2 ? 'warning' : 'success'}">${priorityLabel}</span>
                            <small class="text-muted ms-2">${deadlineDisplay}</small>
                        </div>
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-success" onclick="completeTask(${task.id})">
                            <i data-feather="check"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-primary" onclick="editTask(${task.id})">
                            <i data-feather="edit"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        
        nextTasksContainer.innerHTML = tasksHtml;
        feather.replace();
    }
    
    // Load and render overall progress
    async function loadOverallProgress() {
        const progressContainer = document.getElementById('overallProgress');
        progressContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-secondary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const progress = await fetchData('progress/overall');
        
        if (!progress) {
            progressContainer.innerHTML = '<div class="alert alert-warning">Unable to load progress data.</div>';
            return;
        }
        
        const progressHtml = `
            <div class="text-center mb-4">
                <h1 class="display-4">${progress.task_completion_rate}%</h1>
                <p class="text-muted">Task Completion Rate</p>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" role="progressbar" style="width: ${progress.goal_completion_rate}%;" 
                     aria-valuenow="${progress.goal_completion_rate}" aria-valuemin="0" aria-valuemax="100">
                    Goals: ${progress.goal_completion_rate}%
                </div>
            </div>
            <div class="d-flex justify-content-between mt-3">
                <div>
                    <h5>${progress.completed_tasks} / ${progress.total_tasks}</h5>
                    <small class="text-muted">Tasks completed</small>
                </div>
                <div class="text-end">
                    <h5>${progress.completed_goals} / ${progress.total_goals}</h5>
                    <small class="text-muted">Goals completed</small>
                </div>
            </div>
            <div class="mt-3 alert ${progress.overdue_tasks > 0 ? 'alert-danger' : 'alert-success'}">
                ${progress.overdue_tasks > 0 ? `${progress.overdue_tasks} overdue tasks` : 'No overdue tasks'}
            </div>
        `;
        
        progressContainer.innerHTML = progressHtml;
    }
    
    // Load and render goals progress
    async function loadGoalsProgress() {
        const goalsContainer = document.getElementById('goalsProgress');
        goalsContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Fetch all goals
        currentGoals = await fetchData('goals');
        
        if (!currentGoals || currentGoals.length === 0) {
            goalsContainer.innerHTML = '<div class="alert alert-info">No goals yet! Add your first goal to get started.</div>';
            return;
        }
        
        let goalsHtml = '';
        currentGoals.forEach(goal => {
            // Find the category
            const category = currentCategories.find(c => c.id === goal.category_id) || { name: 'Unknown', color: '#6c757d' };
            
            goalsHtml += `
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="card task-card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h5 class="card-title mb-0">${goal.title}</h5>
                                <span class="badge" style="background-color: ${category.color}">${category.name}</span>
                            </div>
                            <p class="card-text small">${goal.description || 'No description'}</p>
                            <div class="progress goal-progress mb-2">
                                <div class="progress-bar" role="progressbar" style="width: ${goal.progress}%;" 
                                    aria-valuenow="${goal.progress}" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                            <div class="d-flex justify-content-between">
                                <small class="text-muted">${goal.progress}% complete</small>
                                <small class="text-muted">${goal.end_date ? `Due: ${new Date(goal.end_date).toLocaleDateString()}` : 'No deadline'}</small>
                            </div>
                            <div class="mt-3 d-flex justify-content-between">
                                <button class="btn btn-sm btn-outline-primary" onclick="viewGoal(${goal.id})">View Details</button>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="goalComplete-${goal.id}" 
                                        ${goal.completed ? 'checked' : ''} onchange="toggleGoalCompletion(${goal.id}, this.checked)">
                                    <label class="form-check-label" for="goalComplete-${goal.id}">Complete</label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        goalsContainer.innerHTML = goalsHtml;
    }
    
    // Render categories list
    function renderCategoriesList() {
        const categoriesContainer = document.getElementById('categoriesList');
        
        if (!currentCategories || currentCategories.length === 0) {
            categoriesContainer.innerHTML = '<div class="alert alert-info">No categories defined. Add categories to organize your goals.</div>';
            return;
        }
        
        let categoriesHtml = '<div class="list-group">';
        currentCategories.forEach(category => {
            const goalCount = currentGoals ? currentGoals.filter(g => g.category_id === category.id).length : 0;
            
            categoriesHtml += `
                <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center" 
                   onclick="filterByCategory(${category.id})">
                    <div>
                        <span class="badge me-2" style="background-color: ${category.color}">&nbsp;</span>
                        ${category.name}
                    </div>
                    <span class="badge bg-primary rounded-pill">${goalCount}</span>
                </a>
            `;
        });
        categoriesHtml += '</div>';
        
        categoriesContainer.innerHTML = categoriesHtml;
    }
    
    // Load and render recent activity
    async function loadRecentActivity() {
        const activityContainer = document.getElementById('recentActivity');
        activityContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-secondary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const activity = await fetchData('progress/recent');
        
        if (!activity) {
            activityContainer.innerHTML = '<div class="alert alert-warning">Unable to load activity data.</div>';
            return;
        }
        
        // Show last 5 completed tasks
        const recentTasks = activity.completed_tasks.slice(0, 5);
        let activityHtml = '<h6>Recently Completed Tasks</h6>';
        
        if (recentTasks.length === 0) {
            activityHtml += '<p class="text-muted small">No recently completed tasks</p>';
        } else {
            activityHtml += '<ul class="list-group list-group-flush small">';
            recentTasks.forEach(task => {
                const completionDate = new Date(task.completion_date).toLocaleString();
                activityHtml += `
                    <li class="list-group-item px-0">
                        <i data-feather="check-circle" class="text-success me-1"></i>
                        ${task.title}
                        <small class="d-block text-muted">${completionDate}</small>
                    </li>
                `;
            });
            activityHtml += '</ul>';
        }
        
        // Show recently added goals
        const recentGoals = activity.new_goals.slice(0, 3);
        activityHtml += '<h6 class="mt-3">Recently Added Goals</h6>';
        
        if (recentGoals.length === 0) {
            activityHtml += '<p class="text-muted small">No recently added goals</p>';
        } else {
            activityHtml += '<ul class="list-group list-group-flush small">';
            recentGoals.forEach(goal => {
                const creationDate = new Date(goal.created_at).toLocaleString();
                activityHtml += `
                    <li class="list-group-item px-0">
                        <i data-feather="target" class="text-primary me-1"></i>
                        ${goal.title}
                        <small class="d-block text-muted">${creationDate}</small>
                    </li>
                `;
            });
            activityHtml += '</ul>';
        }
        
        activityContainer.innerHTML = activityHtml;
        feather.replace();
    }
    
    // ====================================================
    // Goals View
    // ====================================================
    
    // Load goals view
    async function loadGoals() {
        const goalView = document.getElementById('goalView');
        goalView.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Load categories data first
        await loadCategoriesData();
        
        // Fetch all goals
        currentGoals = await fetchData('goals');
        
        let goalsHtml = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Goals</h2>
                <button class="btn btn-primary" onclick="openGoalModal()">
                    <i data-feather="plus"></i> Add Goal
                </button>
            </div>
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="input-group">
                        <span class="input-group-text">Category</span>
                        <select class="form-select" id="goalCategoryFilter" onchange="filterGoalsByCategory()">
                            <option value="">All Categories</option>
                            ${currentCategories.map(category => `
                                <option value="${category.id}">${category.name}</option>
                            `).join('')}
                        </select>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="input-group">
                        <span class="input-group-text">Status</span>
                        <select class="form-select" id="goalStatusFilter" onchange="filterGoalsByStatus()">
                            <option value="">All</option>
                            <option value="incomplete">In Progress</option>
                            <option value="completed">Completed</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="input-group">
                        <input type="text" class="form-control" id="goalSearchInput" placeholder="Search goals...">
                        <button class="btn btn-outline-secondary" type="button" onclick="searchGoals()">
                            <i data-feather="search"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="row" id="goalsGrid">
        `;
        
        if (!currentGoals || currentGoals.length === 0) {
            goalsHtml += `
                <div class="col-12">
                    <div class="alert alert-info">
                        No goals yet! Use the 'Add Goal' button to create your first goal.
                    </div>
                </div>
            `;
        } else {
            currentGoals.forEach(goal => {
                const category = currentCategories.find(c => c.id === goal.category_id) || { name: 'Unknown', color: '#6c757d' };
                
                goalsHtml += `
                    <div class="col-md-6 col-lg-4 mb-4 goal-item" 
                         data-category="${goal.category_id}" 
                         data-status="${goal.completed ? 'completed' : 'incomplete'}">
                        <div class="card h-100 task-card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <span class="badge" style="background-color: ${category.color}">${category.name}</span>
                                <div class="dropdown">
                                    <button class="btn btn-sm btn-link text-muted" data-bs-toggle="dropdown">
                                        <i data-feather="more-vertical"></i>
                                    </button>
                                    <ul class="dropdown-menu dropdown-menu-end">
                                        <li><a class="dropdown-item" href="#" onclick="editGoal(${goal.id})">Edit</a></li>
                                        <li><a class="dropdown-item" href="#" onclick="viewGoal(${goal.id})">View Details</a></li>
                                        <li><hr class="dropdown-divider"></li>
                                        <li><a class="dropdown-item text-danger" href="#" onclick="deleteGoal(${goal.id})">Delete</a></li>
                                    </ul>
                                </div>
                            </div>
                            <div class="card-body">
                                <h5 class="card-title">${goal.title}</h5>
                                <p class="card-text">${goal.description || 'No description'}</p>
                                <div class="progress mb-3 goal-progress">
                                    <div class="progress-bar" role="progressbar" style="width: ${goal.progress}%;" 
                                        aria-valuenow="${goal.progress}" aria-valuemin="0" aria-valuemax="100"></div>
                                </div>
                                <div class="d-flex justify-content-between">
                                    <small>${goal.progress}% complete</small>
                                    ${goal.completed ? '<span class="badge bg-success">Completed</span>' : ''}
                                </div>
                            </div>
                            <div class="card-footer text-muted">
                                <div class="row">
                                    <div class="col">
                                        <small>Started: ${new Date(goal.start_date).toLocaleDateString()}</small>
                                    </div>
                                    <div class="col text-end">
                                        <small>${goal.end_date ? `Due: ${new Date(goal.end_date).toLocaleDateString()}` : 'No deadline'}</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        goalsHtml += `
            </div>
        `;
        
        goalView.innerHTML = goalsHtml;
        feather.replace();
    }
    
    // Open goal modal to add a new goal
    window.openGoalModal = function() {
        // Reset form
        document.getElementById('goalForm').reset();
        document.getElementById('goalId').value = '';
        document.getElementById('goalModalLabel').textContent = 'Add New Goal';
        
        // Populate categories dropdown
        const categorySelect = document.getElementById('goalCategory');
        categorySelect.innerHTML = '';
        
        currentCategories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            categorySelect.appendChild(option);
        });
        
        // Set default dates
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('goalStartDate').value = today;
        
        // Show modal
        const goalModal = new bootstrap.Modal(document.getElementById('goalModal'));
        goalModal.show();
    };
    
    // Edit existing goal
    window.editGoal = function(goalId) {
        const goal = currentGoals.find(g => g.id === goalId);
        if (!goal) return;
        
        document.getElementById('goalId').value = goal.id;
        document.getElementById('goalTitle').value = goal.title;
        document.getElementById('goalDescription').value = goal.description || '';
        document.getElementById('goalCategory').value = goal.category_id;
        document.getElementById('goalStartDate').value = goal.start_date ? new Date(goal.start_date).toISOString().split('T')[0] : '';
        document.getElementById('goalEndDate').value = goal.end_date ? new Date(goal.end_date).toISOString().split('T')[0] : '';
        document.getElementById('goalCompleted').checked = goal.completed;
        
        document.getElementById('goalModalLabel').textContent = 'Edit Goal';
        
        // Populate categories dropdown
        const categorySelect = document.getElementById('goalCategory');
        categorySelect.innerHTML = '';
        
        currentCategories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            categorySelect.appendChild(option);
        });
        
        // Show modal
        const goalModal = new bootstrap.Modal(document.getElementById('goalModal'));
        goalModal.show();
    };
    
    // View goal details
    window.viewGoal = async function(goalId) {
        const goalView = document.getElementById('goalView');
        goalView.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Get goal progress info
        const progress = await fetchData(`goals/${goalId}/progress`);
        if (!progress) {
            goalView.innerHTML = '<div class="alert alert-warning">Unable to load goal details.</div>';
            return;
        }
        
        // Get goal details
        const goal = await fetchData(`goals/${goalId}`);
        if (!goal) {
            goalView.innerHTML = '<div class="alert alert-warning">Unable to load goal details.</div>';
            return;
        }
        
        // Get all tasks for this goal
        const tasks = await fetchData(`tasks?goal_id=${goalId}`);
        
        // Get category info
        const category = currentCategories.find(c => c.id === goal.category_id) || { name: 'Unknown', color: '#6c757d' };
        
        let goalHtml = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <button class="btn btn-sm btn-outline-secondary me-2" onclick="showView('goals')">
                        <i data-feather="arrow-left"></i> Back to Goals
                    </button>
                    <h2 class="d-inline-block">${goal.title}</h2>
                    <span class="badge ms-2" style="background-color: ${category.color}">${category.name}</span>
                </div>
                <div>
                    <button class="btn btn-outline-primary me-2" onclick="editGoal(${goal.id})">
                        <i data-feather="edit"></i> Edit Goal
                    </button>
                    <button class="btn btn-primary" onclick="openTaskModal(${goal.id})">
                        <i data-feather="plus"></i> Add Task
                    </button>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-8">
                    <div class="card mb-4">
                        <div class="card-body">
                            <h5 class="card-title">Description</h5>
                            <p class="card-text">${goal.description || 'No description provided.'}</p>
                            <div class="d-flex justify-content-between text-muted small">
                                <div>Created: ${new Date(goal.created_at).toLocaleDateString()}</div>
                                <div>Last updated: ${new Date(goal.updated_at).toLocaleDateString()}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Tasks list -->
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="mb-0">Tasks</h5>
                            <div class="form-check form-switch">
                                <input class="form-check-input" type="checkbox" id="showCompletedTasks" onchange="toggleCompletedTasks()">
                                <label class="form-check-label" for="showCompletedTasks">Show completed</label>
                            </div>
                        </div>
                        <div class="card-body">
                            <div id="tasksContainer">
        `;
        
        if (!tasks || tasks.length === 0) {
            goalHtml += '<div class="alert alert-info">No tasks yet. Add tasks to make progress on this goal.</div>';
        } else {
            goalHtml += '<div class="list-group">';
            
            // Sort tasks by priority and then by deadline
            const sortedTasks = [...tasks].sort((a, b) => {
                // First by completion status
                if (a.completed !== b.completed) {
                    return a.completed ? 1 : -1;
                }
                // Then by priority (lower number = higher priority)
                if (a.priority !== b.priority) {
                    return a.priority - b.priority;
                }
                // Then by deadline (if it exists)
                if (a.deadline && b.deadline) {
                    return new Date(a.deadline) - new Date(b.deadline);
                }
                // Tasks with deadlines come before those without
                if (a.deadline && !b.deadline) return -1;
                if (!a.deadline && b.deadline) return 1;
                
                // Finally by title
                return a.title.localeCompare(b.title);
            });
            
            sortedTasks.forEach(task => {
                const priorityClass = task.priority === 1 ? 'priority-high' : 
                                      task.priority === 2 ? 'priority-medium' : 'priority-low';
                const priorityLabel = task.priority === 1 ? 'High' : 
                                      task.priority === 2 ? 'Medium' : 'Low';
                const deadlineDisplay = task.deadline ? new Date(task.deadline).toLocaleString() : 'No deadline';
                const completedClass = task.completed ? 'task-completed bg-light' : '';
                
                goalHtml += `
                    <div class="list-group-item ${priorityClass} ${completedClass} task-item ${task.completed ? 'completed-task' : ''}" data-completed="${task.completed}">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="me-auto">
                                <div class="d-flex align-items-center">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" ${task.completed ? 'checked' : ''} 
                                               onchange="toggleTaskCompletion(${task.id}, this.checked)">
                                    </div>
                                    <div>
                                        <h6 class="mb-0 ms-2">${task.title}</h6>
                                        <p class="mb-1 ms-2 small">${task.description || 'No description'}</p>
                                    </div>
                                </div>
                                <div class="mt-2 ms-4">
                                    <span class="badge bg-${task.priority === 1 ? 'danger' : task.priority === 2 ? 'warning' : 'success'}">${priorityLabel}</span>
                                    <small class="text-muted ms-2">${deadlineDisplay}</small>
                                    ${task.is_overdue && !task.completed ? '<span class="badge bg-danger ms-2">Overdue</span>' : ''}
                                    ${task.recurrence_type ? `<span class="badge bg-info ms-2">Repeats ${task.recurrence_type}</span>` : ''}
                                </div>
                            </div>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-outline-primary" onclick="editTask(${task.id})">
                                    <i data-feather="edit-2"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteTask(${task.id})">
                                    <i data-feather="trash-2"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            goalHtml += '</div>';
        }
        
        goalHtml += `
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <!-- Progress info -->
                    <div class="card mb-4">
                        <div class="card-body">
                            <h5 class="card-title">Progress</h5>
                            <div class="text-center mb-3">
                                <h2 class="display-4">${progress.progress_percentage}%</h2>
                                <p class="text-muted">${progress.completed_tasks} of ${progress.total_tasks} tasks completed</p>
                            </div>
                            <div class="progress mb-4 goal-progress">
                                <div class="progress-bar" role="progressbar" style="width: ${progress.progress_percentage}%;" 
                                    aria-valuenow="${progress.progress_percentage}" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                            <div class="form-check form-switch mb-3">
                                <input class="form-check-input" type="checkbox" id="goalCompleteSwitch" 
                                    ${goal.completed ? 'checked' : ''} onchange="toggleGoalCompletion(${goal.id}, this.checked)">
                                <label class="form-check-label" for="goalCompleteSwitch">
                                    Mark goal as ${goal.completed ? 'incomplete' : 'complete'}
                                </label>
                            </div>
                            <div class="d-grid">
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteGoal(${goal.id})">
                                    <i data-feather="trash"></i> Delete Goal
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Dates info -->
                    <div class="card mb-4">
                        <div class="card-body">
                            <h5 class="card-title">Timeline</h5>
                            <div class="mb-3">
                                <label class="form-label">Start Date</label>
                                <p>${goal.start_date ? new Date(goal.start_date).toLocaleDateString() : 'Not set'}</p>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">End Date</label>
                                <p>${goal.end_date ? new Date(goal.end_date).toLocaleDateString() : 'Not set'}</p>
                            </div>
                            ${progress.days_left !== null ? `
                                <div class="alert ${progress.days_left < 0 ? 'alert-danger' : progress.days_left <= 7 ? 'alert-warning' : 'alert-info'}">
                                    ${progress.days_left < 0 ? `Overdue by ${Math.abs(progress.days_left)} days` : `${progress.days_left} days remaining`}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <!-- High priority tasks -->
                    ${progress.high_priority_tasks.length > 0 ? `
                        <div class="card mb-4">
                            <div class="card-body">
                                <h5 class="card-title">High Priority Tasks</h5>
                                <ul class="list-group list-group-flush">
                                    ${progress.high_priority_tasks.map(task => `
                                        <li class="list-group-item px-0">
                                            <div class="d-flex justify-content-between align-items-center">
                                                <div>
                                                    <i data-feather="alert-triangle" class="text-danger me-1"></i>
                                                    ${task.title}
                                                </div>
                                                <button class="btn btn-sm btn-outline-success" onclick="toggleTaskCompletion(${task.id}, true)">
                                                    <i data-feather="check"></i>
                                                </button>
                                            </div>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- Overdue tasks -->
                    ${progress.overdue_tasks.length > 0 ? `
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Overdue Tasks</h5>
                                <ul class="list-group list-group-flush">
                                    ${progress.overdue_tasks.map(task => `
                                        <li class="list-group-item px-0">
                                            <div class="d-flex justify-content-between align-items-center">
                                                <div>
                                                    <i data-feather="clock" class="text-danger me-1"></i>
                                                    ${task.title}
                                                    <small class="d-block text-danger">Due: ${new Date(task.deadline).toLocaleDateString()}</small>
                                                </div>
                                                <button class="btn btn-sm btn-outline-success" onclick="toggleTaskCompletion(${task.id}, true)">
                                                    <i data-feather="check"></i>
                                                </button>
                                            </div>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        goalView.innerHTML = goalHtml;
        feather.replace();
        
        // Initialize with completed tasks hidden
        toggleCompletedTasks();
        
        // Show goal view
        showView('goals');
    };
    
    // Delete a goal
    window.deleteGoal = async function(goalId) {
        if (!confirm('Are you sure you want to delete this goal? This will also delete all associated tasks and cannot be undone.')) {
            return;
        }
        
        const result = await deleteData(`goals/${goalId}`);
        if (result) {
            // Reload goals or redirect to goals list
            if (currentView === 'dashboard') {
                loadDashboard();
            } else {
                loadGoals();
            }
        }
    };
    
    // Handle goal form submission
    document.getElementById('saveGoalBtn').addEventListener('click', async function() {
        const goalId = document.getElementById('goalId').value;
        const title = document.getElementById('goalTitle').value;
        const description = document.getElementById('goalDescription').value;
        const categoryId = parseInt(document.getElementById('goalCategory').value);
        const startDate = document.getElementById('goalStartDate').value;
        const endDate = document.getElementById('goalEndDate').value;
        const completed = document.getElementById('goalCompleted').checked;
        
        if (!title) {
            alert('Please enter a goal title');
            return;
        }
        
        const goalData = {
            title,
            description,
            category_id: categoryId,
            start_date: startDate,
            end_date: endDate || null,
            completed
        };
        
        let result;
        
        if (goalId) {
            // Update existing goal
            result = await putData(`goals/${goalId}`, goalData);
        } else {
            // Create new goal
            result = await postData('goals/', goalData);
        }
        
        if (result) {
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('goalModal')).hide();
            
            // Reload goals or dashboard
            if (currentView === 'dashboard') {
                loadDashboard();
            } else {
                loadGoals();
            }
        }
    });
    
    // Toggle goal completion status
    window.toggleGoalCompletion = async function(goalId, completed) {
        const endpoint = completed ? `goals/${goalId}/complete` : `goals/${goalId}/incomplete`;
        const result = await postData(endpoint, {});
        
        if (result) {
            // Update goal in current goals list
            if (currentGoals) {
                const goalIndex = currentGoals.findIndex(g => g.id === goalId);
                if (goalIndex !== -1) {
                    currentGoals[goalIndex] = result;
                }
            }
            
            // Refresh current view
            if (currentView === 'dashboard') {
                loadGoalsProgress();
            } else if (currentView === 'goals') {
                // If we're in goal detail view, reload the entire view
                if (document.getElementById('goalCompleteSwitch')) {
                    viewGoal(goalId);
                } else {
                    loadGoals();
                }
            }
        }
    };
    
    // Filter goals by category
    window.filterGoalsByCategory = function() {
        const categoryId = document.getElementById('goalCategoryFilter').value;
        const statusFilter = document.getElementById('goalStatusFilter').value;
        
        filterGoals(categoryId, statusFilter);
    };
    
    // Filter goals by status
    window.filterGoalsByStatus = function() {
        const categoryId = document.getElementById('goalCategoryFilter').value;
        const statusFilter = document.getElementById('goalStatusFilter').value;
        
        filterGoals(categoryId, statusFilter);
    };
    
    // Combined filter function
    function filterGoals(categoryId, status) {
        const goalItems = document.querySelectorAll('.goal-item');
        
        goalItems.forEach(item => {
            let showItem = true;
            
            // Filter by category
            if (categoryId && item.dataset.category !== categoryId) {
                showItem = false;
            }
            
            // Filter by status
            if (status && item.dataset.status !== status) {
                showItem = false;
            }
            
            item.style.display = showItem ? 'block' : 'none';
        });
    }
    
    // Search goals
    window.searchGoals = function() {
        const searchTerm = document.getElementById('goalSearchInput').value.toLowerCase();
        const goalItems = document.querySelectorAll('.goal-item');
        
        goalItems.forEach(item => {
            const title = item.querySelector('.card-title').textContent.toLowerCase();
            const description = item.querySelector('.card-text').textContent.toLowerCase();
            
            const matchesSearch = title.includes(searchTerm) || description.includes(searchTerm);
            
            item.style.display = matchesSearch ? 'block' : 'none';
        });
    };
    
    // Toggle display of completed tasks
    window.toggleCompletedTasks = function() {
        const showCompleted = document.getElementById('showCompletedTasks').checked;
        const completedTasks = document.querySelectorAll('.completed-task');
        
        completedTasks.forEach(task => {
            task.style.display = showCompleted ? 'block' : 'none';
        });
    };
    
    // ====================================================
    // Tasks View
    // ====================================================
    
    // Load tasks view
    async function loadTasks() {
        const tasksView = document.getElementById('tasksView');
        tasksView.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Load goals and categories data first
        await loadCategoriesData();
        await loadGoalsData();
        
        // Fetch all tasks
        currentTasks = await fetchData('tasks');
        
        let tasksHtml = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Tasks</h2>
                <button class="btn btn-primary" onclick="openTaskModal()">
                    <i data-feather="plus"></i> Add Task
                </button>
            </div>
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="input-group">
                        <span class="input-group-text">Goal</span>
                        <select class="form-select" id="taskGoalFilter" onchange="filterTasksByGoal()">
                            <option value="">All Goals</option>
                            ${currentGoals.map(goal => `
                                <option value="${goal.id}">${goal.title}</option>
                            `).join('')}
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="input-group">
                        <span class="input-group-text">Priority</span>
                        <select class="form-select" id="taskPriorityFilter" onchange="filterTasksByPriority()">
                            <option value="">All</option>
                            <option value="1">High</option>
                            <option value="2">Medium</option>
                            <option value="3">Low</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="input-group">
                        <span class="input-group-text">Status</span>
                        <select class="form-select" id="taskStatusFilter" onchange="filterTasksByStatus()">
                            <option value="">All</option>
                            <option value="incomplete">Incomplete</option>
                            <option value="completed">Completed</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="input-group">
                        <input type="text" class="form-control" id="taskSearchInput" placeholder="Search tasks...">
                        <button class="btn btn-outline-secondary" type="button" onclick="searchTasks()">
                            <i data-feather="search"></i>
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <ul class="nav nav-tabs card-header-tabs" id="taskTabs">
                        <li class="nav-item">
                            <a class="nav-link active" data-bs-toggle="tab" href="#allTasks">All Tasks</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#todayTasks">Today</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#upcomingTasks">Upcoming</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#overdueTasks">Overdue</a>
                        </li>
                    </ul>
                </div>
                <div class="card-body">
                    <div class="tab-content">
                        <div class="tab-pane fade show active" id="allTasks">
                            <div id="allTasksList">
        `;
        
        if (!currentTasks || currentTasks.length === 0) {
            tasksHtml += `
                <div class="alert alert-info">
                    No tasks yet! Use the 'Add Task' button to create your first task.
                </div>
            `;
        } else {
            tasksHtml += renderTasksList(currentTasks);
        }
        
        tasksHtml += `
                            </div>
                        </div>
                        <div class="tab-pane fade" id="todayTasks">
                            <div id="todayTasksList">
                                <div class="text-center py-3">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="tab-pane fade" id="upcomingTasks">
                            <div id="upcomingTasksList">
                                <!-- Will be loaded when tab is clicked -->
                            </div>
                        </div>
                        <div class="tab-pane fade" id="overdueTasks">
                            <div id="overdueTasksList">
                                <!-- Will be loaded when tab is clicked -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        tasksView.innerHTML = tasksHtml;
        feather.replace();
        
        // Set up tab click handlers
        document.querySelectorAll('#taskTabs .nav-link').forEach(tab => {
            tab.addEventListener('click', function(e) {
                const tabId = this.getAttribute('href').substring(1);
                loadTaskTab(tabId);
            });
        });
        
        // Load today's tasks immediately
        loadTaskTab('todayTasks');
    }
    
    // Load task data for a specific tab
    async function loadTaskTab(tabId) {
        const tabContent = document.getElementById(tabId + 'List');
        
        if (tabId === 'allTasks') {
            // Already loaded in the main view
            return;
        }
        
        tabContent.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        let tasks = [];
        
        if (tabId === 'todayTasks') {
            // Load today's tasks
            tasks = await fetchData('tasks/daily');
        } else if (tabId === 'overdueTasks') {
            // Load overdue tasks
            tasks = await fetchData('tasks/overdue');
        } else if (tabId === 'upcomingTasks') {
            // For upcoming tasks, filter the current tasks for those with future deadlines
            const now = new Date();
            const tomorrow = new Date(now);
            tomorrow.setDate(now.getDate() + 1);
            tomorrow.setHours(0, 0, 0, 0);
            
            // Get upcoming tasks (not overdue, not completed, with deadline)
            tasks = currentTasks.filter(task => {
                if (task.completed || !task.deadline) return false;
                const deadline = new Date(task.deadline);
                return deadline >= tomorrow;
            });
            
            // Sort by deadline
            tasks.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
        }
        
        if (!tasks || tasks.length === 0) {
            tabContent.innerHTML = `<div class="alert alert-info">No ${tabId.replace('Tasks', '').toLowerCase()} tasks found.</div>`;
            return;
        }
        
        tabContent.innerHTML = renderTasksList(tasks);
        feather.replace();
    }
    
    // Render a list of tasks
    function renderTasksList(tasks) {
        let html = '<div class="list-group task-list">';
        
        tasks.forEach(task => {
            const goal = currentGoals.find(g => g.id === task.goal_id) || { title: 'Unknown Goal' };
            const priorityClass = task.priority === 1 ? 'priority-high' : 
                                  task.priority === 2 ? 'priority-medium' : 'priority-low';
            const priorityLabel = task.priority === 1 ? 'High' : 
                                  task.priority === 2 ? 'Medium' : 'Low';
            const deadlineDisplay = task.deadline ? new Date(task.deadline).toLocaleString() : 'No deadline';
            const isOverdue = task.is_overdue;
            const completedClass = task.completed ? 'task-completed bg-light' : '';
            
            html += `
                <div class="list-group-item ${priorityClass} ${completedClass} task-item" 
                     data-goal="${task.goal_id}" 
                     data-priority="${task.priority}" 
                     data-status="${task.completed ? 'completed' : 'incomplete'}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="me-auto">
                            <div class="d-flex align-items-center">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" ${task.completed ? 'checked' : ''} 
                                           onchange="toggleTaskCompletion(${task.id}, this.checked)">
                                </div>
                                <div>
                                    <h6 class="mb-0 ms-2">${task.title}</h6>
                                    <p class="mb-1 ms-2 small">${task.description || 'No description'}</p>
                                </div>
                            </div>
                            <div class="mt-2 ms-4">
                                <span class="badge bg-secondary">${goal.title}</span>
                                <span class="badge bg-${task.priority === 1 ? 'danger' : task.priority === 2 ? 'warning' : 'success'}">${priorityLabel}</span>
                                <small class="text-muted ms-2">${deadlineDisplay}</small>
                                ${isOverdue && !task.completed ? '<span class="badge bg-danger ms-2">Overdue</span>' : ''}
                                ${task.recurrence_type ? `<span class="badge bg-info ms-2">Repeats ${task.recurrence_type}</span>` : ''}
                            </div>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="editTask(${task.id})">
                                <i data-feather="edit-2"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteTask(${task.id})">
                                <i data-feather="trash-2"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    // Open task modal to add a new task
    window.openTaskModal = function(goalId = null) {
        // Reset form
        document.getElementById('taskForm').reset();
        document.getElementById('taskId').value = '';
        document.getElementById('taskModalLabel').textContent = 'Add New Task';
        
        // Show/hide recurrence value field based on recurrence type
        document.getElementById('taskRecurrenceType').addEventListener('change', toggleRecurrenceValue);
        
        // Populate goals dropdown
        const goalSelect = document.getElementById('taskGoal');
        goalSelect.innerHTML = '';
        
        currentGoals.forEach(goal => {
            const option = document.createElement('option');
            option.value = goal.id;
            option.textContent = goal.title;
            goalSelect.appendChild(option);
        });
        
        // If a goal ID is provided, select it
        if (goalId) {
            document.getElementById('taskGoal').value = goalId;
        }
        
        // Show modal
        const taskModal = new bootstrap.Modal(document.getElementById('taskModal'));
        taskModal.show();
    };
    
    // Edit existing task
    window.editTask = function(taskId) {
        const task = currentTasks.find(t => t.id === taskId);
        if (!task) return;
        
        document.getElementById('taskId').value = task.id;
        document.getElementById('taskTitle').value = task.title;
        document.getElementById('taskDescription').value = task.description || '';
        document.getElementById('taskGoal').value = task.goal_id;
        
        if (task.deadline) {
            // Convert ISO string to local datetime-local format
            const deadline = new Date(task.deadline);
            const year = deadline.getFullYear();
            const month = String(deadline.getMonth() + 1).padStart(2, '0');
            const day = String(deadline.getDate()).padStart(2, '0');
            const hours = String(deadline.getHours()).padStart(2, '0');
            const minutes = String(deadline.getMinutes()).padStart(2, '0');
            
            document.getElementById('taskDeadline').value = `${year}-${month}-${day}T${hours}:${minutes}`;
        } else {
            document.getElementById('taskDeadline').value = '';
        }
        
        document.getElementById('taskPriority').value = task.priority;
        document.getElementById('taskRecurrenceType').value = task.recurrence_type || '';
        document.getElementById('taskRecurrenceValue').value = task.recurrence_value || 1;
        document.getElementById('taskCompleted').checked = task.completed;
        
        // Show/hide recurrence value field based on recurrence type
        toggleRecurrenceValue();
        
        document.getElementById('taskModalLabel').textContent = 'Edit Task';
        
        // Show modal
        const taskModal = new bootstrap.Modal(document.getElementById('taskModal'));
        taskModal.show();
    };
    
    // Delete a task
    window.deleteTask = async function(taskId) {
        if (!confirm('Are you sure you want to delete this task? This action cannot be undone.')) {
            return;
        }
        
        const result = await deleteData(`tasks/${taskId}`);
        if (result) {
            // Remove from current tasks
            const taskIndex = currentTasks.findIndex(t => t.id === taskId);
            if (taskIndex !== -1) {
                currentTasks.splice(taskIndex, 1);
            }
            
            // Reload current view
            if (currentView === 'dashboard') {
                loadDashboard();
            } else if (currentView === 'tasks') {
                loadTasks();
            } else if (currentView === 'goals' && document.getElementById('tasksContainer')) {
                // We're in goal detail view, reload that goal
                const goalId = currentTasks[taskIndex].goal_id;
                viewGoal(goalId);
            }
        }
    };
    
    // Handle task form submission
    document.getElementById('saveTaskBtn').addEventListener('click', async function() {
        const taskId = document.getElementById('taskId').value;
        const title = document.getElementById('taskTitle').value;
        const description = document.getElementById('taskDescription').value;
        const goalId = parseInt(document.getElementById('taskGoal').value);
        const deadline = document.getElementById('taskDeadline').value;
        const priority = parseInt(document.getElementById('taskPriority').value);
        const recurrenceType = document.getElementById('taskRecurrenceType').value;
        const recurrenceValue = recurrenceType ? parseInt(document.getElementById('taskRecurrenceValue').value) : null;
        const completed = document.getElementById('taskCompleted').checked;
        
        if (!title) {
            alert('Please enter a task title');
            return;
        }
        
        const taskData = {
            title,
            description,
            goal_id: goalId,
            deadline: deadline || null,
            priority,
            completed,
            recurrence_type: recurrenceType || null,
            recurrence_value: recurrenceValue
        };
        
        let result;
        
        if (taskId) {
            // Update existing task
            result = await putData(`tasks/${taskId}`, taskData);
        } else {
            // Create new task
            result = await postData('tasks/', taskData);
        }
        
        if (result) {
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('taskModal')).hide();
            
            // Reload view
            if (currentView === 'dashboard') {
                loadDashboard();
            } else if (currentView === 'tasks') {
                loadTasks();
            } else if (currentView === 'goals' && document.getElementById('tasksContainer')) {
                // We're in goal detail view, reload that goal
                viewGoal(goalId);
            }
        }
    });
    
    // Toggle task completion status
    window.toggleTaskCompletion = async function(taskId, completed) {
        const endpoint = completed ? `tasks/${taskId}/complete` : `tasks/${taskId}/incomplete`;
        const result = await postData(endpoint, {});
        
        if (result) {
            // Update task in current tasks list
            if (currentTasks) {
                const taskIndex = currentTasks.findIndex(t => t.id === taskId);
                if (taskIndex !== -1) {
                    currentTasks[taskIndex] = result;
                }
            }
            
            // Refresh current view
            if (currentView === 'dashboard') {
                loadNextTasks();
                loadOverallProgress();
            } else if (currentView === 'tasks') {
                loadTasks();
            } else if (currentView === 'goals' && document.getElementById('tasksContainer')) {
                // We're in goal detail view, update the task item
                const taskItem = document.querySelector(`.task-item[data-id="${taskId}"]`);
                if (taskItem) {
                    if (completed) {
                        taskItem.classList.add('task-completed', 'bg-light', 'completed-task');
                        taskItem.dataset.completed = 'true';
                    } else {
                        taskItem.classList.remove('task-completed', 'bg-light', 'completed-task');
                        taskItem.dataset.completed = 'false';
                    }
                    
                    // Update checkbox
                    const checkbox = taskItem.querySelector('input[type="checkbox"]');
                    if (checkbox) {
                        checkbox.checked = completed;
                    }
                    
                    // Reload the goal progress
                    const goalId = result.goal_id;
                    viewGoal(goalId);
                }
            }
        }
    };
    
    // Toggle recurrence value field visibility
    function toggleRecurrenceValue() {
        const recurrenceType = document.getElementById('taskRecurrenceType').value;
        const recurrenceValueContainer = document.getElementById('recurrenceValueContainer');
        
        if (recurrenceType) {
            recurrenceValueContainer.style.display = 'block';
        } else {
            recurrenceValueContainer.style.display = 'none';
        }
    }
    
    // Filter tasks by goal
    window.filterTasksByGoal = function() {
        applyTaskFilters();
    };
    
    // Filter tasks by priority
    window.filterTasksByPriority = function() {
        applyTaskFilters();
    };
    
    // Filter tasks by status
    window.filterTasksByStatus = function() {
        applyTaskFilters();
    };
    
    // Apply all task filters at once
    function applyTaskFilters() {
        const goalId = document.getElementById('taskGoalFilter').value;
        const priority = document.getElementById('taskPriorityFilter').value;
        const status = document.getElementById('taskStatusFilter').value;
        
        const taskItems = document.querySelectorAll('.task-item');
        
        taskItems.forEach(item => {
            let showItem = true;
            
            // Filter by goal
            if (goalId && item.dataset.goal !== goalId) {
                showItem = false;
            }
            
            // Filter by priority
            if (priority && item.dataset.priority !== priority) {
                showItem = false;
            }
            
            // Filter by status
            if (status && item.dataset.status !== status) {
                showItem = false;
            }
            
            item.style.display = showItem ? 'block' : 'none';
        });
    }
    
    // Search tasks
    window.searchTasks = function() {
        const searchTerm = document.getElementById('taskSearchInput').value.toLowerCase();
        const taskItems = document.querySelectorAll('.task-item');
        
        taskItems.forEach(item => {
            const title = item.querySelector('h6').textContent.toLowerCase();
            const description = item.querySelector('p').textContent.toLowerCase();
            
            const matchesSearch = title.includes(searchTerm) || description.includes(searchTerm);
            
            item.style.display = matchesSearch ? 'block' : 'none';
        });
    };
    
    // ====================================================
    // Categories View
    // ====================================================
    
    // Load categories view
    async function loadCategories() {
        const categoriesView = document.getElementById('categoriesView');
        categoriesView.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Load categories data
        await loadCategoriesData();
        
        let categoriesHtml = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Categories</h2>
                <div>
                    <button class="btn btn-outline-secondary me-2" id="resetDefaultCategoriesBtn">
                        <i data-feather="refresh-cw"></i> Reset Defaults
                    </button>
                    <button class="btn btn-primary" id="addCategoryBtn">
                        <i data-feather="plus"></i> Add Category
                    </button>
                </div>
            </div>
            
            <div class="row" id="categoriesGrid">
        `;
        
        if (!currentCategories || currentCategories.length === 0) {
            categoriesHtml += `
                <div class="col-12">
                    <div class="alert alert-info">
                        No categories yet! Add categories to organize your goals.
                    </div>
                </div>
            `;
        } else {
            currentCategories.forEach(category => {
                categoriesHtml += `
                    <div class="col-md-4 mb-4">
                        <div class="card h-100 task-card">
                            <div class="card-header" style="background-color: ${category.color}; color: white;">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h5 class="mb-0">${category.name}</h5>
                                    <div class="dropdown">
                                        <button class="btn btn-sm btn-link text-white" data-bs-toggle="dropdown">
                                            <i data-feather="more-vertical"></i>
                                        </button>
                                        <ul class="dropdown-menu dropdown-menu-end">
                                            <li><a class="dropdown-item" href="#" onclick="editCategory(${category.id})">Edit</a></li>
                                            <li><hr class="dropdown-divider"></li>
                                            <li><a class="dropdown-item text-danger" href="#" onclick="deleteCategory(${category.id})">Delete</a></li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="card-body">
                                <p class="card-text">${category.description || 'No description'}</p>
                                
                                <div id="categoryGoals-${category.id}">
                                    <div class="text-center py-2">
                                        <div class="spinner-border spinner-border-sm text-secondary" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="card-footer">
                                <button class="btn btn-sm btn-outline-primary w-100" onclick="addGoalToCategory(${category.id})">
                                    <i data-feather="plus"></i> Add Goal
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        categoriesHtml += `
            </div>
            
            <!-- Modal for adding/editing categories -->
            <div class="modal fade" id="categoryModal" tabindex="-1" aria-labelledby="categoryModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="categoryModalLabel">Add New Category</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="categoryForm">
                                <input type="hidden" id="categoryId">
                                <div class="mb-3">
                                    <label for="categoryName" class="form-label">Name</label>
                                    <input type="text" class="form-control" id="categoryName" required>
                                </div>
                                <div class="mb-3">
                                    <label for="categoryDescription" class="form-label">Description</label>
                                    <textarea class="form-control" id="categoryDescription" rows="3"></textarea>
                                </div>
                                <div class="mb-3">
                                    <label for="categoryColor" class="form-label">Color</label>
                                    <input type="color" class="form-control form-control-color" id="categoryColor" value="#6c757d">
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveCategoryBtn">Save</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        categoriesView.innerHTML = categoriesHtml;
        feather.replace();
        
        // Load goals for each category
        await loadGoalsData();
        loadGoalsForCategories();
        
        // Set up event handlers
        document.getElementById('addCategoryBtn').addEventListener('click', openCategoryModal);
        document.getElementById('resetDefaultCategoriesBtn').addEventListener('click', resetDefaultCategories);
        document.getElementById('saveCategoryBtn').addEventListener('click', saveCategory);
    }
    
    // Load goals for all categories
    function loadGoalsForCategories() {
        currentCategories.forEach(category => {
            const goalsContainer = document.getElementById(`categoryGoals-${category.id}`);
            if (!goalsContainer) return;
            
            // Filter goals for this category
            const categoryGoals = currentGoals.filter(goal => goal.category_id === category.id);
            
            if (categoryGoals.length === 0) {
                goalsContainer.innerHTML = '<p class="text-muted small">No goals in this category</p>';
                return;
            }
            
            let goalsHtml = '<ul class="list-group list-group-flush">';
            
            // Show up to 5 goals per category
            categoryGoals.slice(0, 5).forEach(goal => {
                goalsHtml += `
                    <li class="list-group-item px-0">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="badge ${goal.completed ? 'bg-success' : 'bg-secondary'} me-1">
                                    ${goal.completed ? 'Completed' : `${goal.progress}%`}
                                </span>
                                ${goal.title}
                            </div>
                            <button class="btn btn-sm btn-link" onclick="viewGoal(${goal.id})">
                                <i data-feather="arrow-right"></i>
                            </button>
                        </div>
                    </li>
                `;
            });
            
            if (categoryGoals.length > 5) {
                goalsHtml += `
                    <li class="list-group-item px-0 text-center">
                        <a href="#" onclick="filterByCategory(${category.id})">
                            View all ${categoryGoals.length} goals
                        </a>
                    </li>
                `;
            }
            
            goalsHtml += '</ul>';
            goalsContainer.innerHTML = goalsHtml;
            feather.replace();
        });
    }
    
    // Open the category modal for adding a new category
    function openCategoryModal() {
        // Reset form
        document.getElementById('categoryForm').reset();
        document.getElementById('categoryId').value = '';
        document.getElementById('categoryColor').value = '#6c757d';
        document.getElementById('categoryModalLabel').textContent = 'Add New Category';
        
        // Show modal
        const categoryModal = new bootstrap.Modal(document.getElementById('categoryModal'));
        categoryModal.show();
    }
    
    // Edit an existing category
    window.editCategory = function(categoryId) {
        const category = currentCategories.find(c => c.id === categoryId);
        if (!category) return;
        
        document.getElementById('categoryId').value = category.id;
        document.getElementById('categoryName').value = category.name;
        document.getElementById('categoryDescription').value = category.description || '';
        document.getElementById('categoryColor').value = category.color;
        
        document.getElementById('categoryModalLabel').textContent = 'Edit Category';
        
        // Show modal
        const categoryModal = new bootstrap.Modal(document.getElementById('categoryModal'));
        categoryModal.show();
    };
    
    // Delete a category
    window.deleteCategory = async function(categoryId) {
        if (!confirm('Are you sure you want to delete this category? This will also delete all associated goals and tasks and cannot be undone.')) {
            return;
        }
        
        const result = await deleteData(`categories/${categoryId}`);
        if (result) {
            // Reload categories
            loadCategories();
        }
    };
    
    // Save a category (create or update)
    async function saveCategory() {
        const categoryId = document.getElementById('categoryId').value;
        const name = document.getElementById('categoryName').value;
        const description = document.getElementById('categoryDescription').value;
        const color = document.getElementById('categoryColor').value;
        
        if (!name) {
            alert('Please enter a category name');
            return;
        }
        
        const categoryData = {
            name,
            description,
            color
        };
        
        let result;
        
        if (categoryId) {
            // Update existing category
            result = await putData(`categories/${categoryId}`, categoryData);
        } else {
            // Create new category
            result = await postData('categories/', categoryData);
        }
        
        if (result) {
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
            
            // Reload categories
            loadCategories();
        }
    }
    
    // Reset to default categories
    async function resetDefaultCategories() {
        if (!confirm('Are you sure you want to reset to default categories? This will not affect existing categories.')) {
            return;
        }
        
        const result = await postData('categories/defaults', {});
        if (result) {
            // Reload categories
            loadCategories();
        }
    }
    
    // Add a goal to a specific category
    window.addGoalToCategory = function(categoryId) {
        openGoalModal();
        document.getElementById('goalCategory').value = categoryId;
    };
    
    // Filter goals by category
    window.filterByCategory = function(categoryId) {
        // Switch to goals view
        showView('goals');
        
        // Set category filter
        setTimeout(() => {
            document.getElementById('goalCategoryFilter').value = categoryId;
            filterGoalsByCategory();
        }, 100);
    };
    
    // ====================================================
    // Reminders View
    // ====================================================
    
    // Load reminders view
    async function loadReminders() {
        const remindersView = document.getElementById('remindersView');
        remindersView.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Load tasks data first (needed for reminder associations)
        await loadGoalsData();
        await loadTasksData();
        
        // Fetch all reminders
        currentReminders = await fetchData('reminders');
        
        let remindersHtml = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Reminders</h2>
                <button class="btn btn-primary" id="addReminderBtn">
                    <i data-feather="plus"></i> Add Reminder
                </button>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="input-group">
                        <span class="input-group-text">Task</span>
                        <select class="form-select" id="reminderTaskFilter" onchange="filterRemindersByTask()">
                            <option value="">All Tasks</option>
                            ${currentTasks.map(task => `
                                <option value="${task.id}">${task.title}</option>
                            `).join('')}
                        </select>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="input-group">
                        <span class="input-group-text">Status</span>
                        <select class="form-select" id="reminderStatusFilter" onchange="filterRemindersByStatus()">
                            <option value="">All</option>
                            <option value="pending">Pending</option>
                            <option value="triggered">Triggered</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <ul class="nav nav-tabs card-header-tabs">
                        <li class="nav-item">
                            <a class="nav-link active" data-bs-toggle="tab" href="#allReminders">All Reminders</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#upcomingReminders">Upcoming</a>
                        </li>
                    </ul>
                </div>
                <div class="card-body">
                    <div class="tab-content">
                        <div class="tab-pane fade show active" id="allReminders">
        `;
        
        if (!currentReminders || currentReminders.length === 0) {
            remindersHtml += `
                <div class="alert alert-info">
                    No reminders yet! Add reminders to get notified about important tasks.
                </div>
            `;
        } else {
            remindersHtml += '<div class="list-group reminder-list">';
            
            // Sort reminders by time (upcoming first)
            const sortedReminders = [...currentReminders].sort((a, b) => {
                // Triggered reminders come after pending ones
                if (a.triggered !== b.triggered) {
                    return a.triggered ? 1 : -1;
                }
                // Sort by reminder time
                return new Date(a.reminder_time) - new Date(b.reminder_time);
            });
            
            sortedReminders.forEach(reminder => {
                const task = currentTasks.find(t => t.id === reminder.task_id) || { title: 'Unknown Task' };
                const goal = task.goal_id ? currentGoals.find(g => g.id === task.goal_id) || { title: 'Unknown Goal' } : { title: 'Unknown Goal' };
                const reminderTime = new Date(reminder.reminder_time).toLocaleString();
                const isPast = new Date(reminder.reminder_time) < new Date();
                const statusClass = reminder.triggered ? 'bg-light text-muted' : (isPast ? 'border-danger' : '');
                
                remindersHtml += `
                    <div class="list-group-item ${statusClass} reminder-item" 
                         data-task="${reminder.task_id}" 
                         data-status="${reminder.triggered ? 'triggered' : 'pending'}">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1">
                                    ${reminder.triggered ? '<i data-feather="check-circle" class="text-success me-1"></i>' : '<i data-feather="bell" class="text-warning me-1"></i>'}
                                    ${reminder.message || `Reminder for: ${task.title}`}
                                </h6>
                                <div class="small">
                                    <div>Task: <span class="fw-bold">${task.title}</span> (${goal.title})</div>
                                    <div>Time: <span class="fw-bold">${reminderTime}</span> ${isPast ? '<span class="text-danger">(Past)</span>' : ''}</div>
                                </div>
                            </div>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-outline-primary" onclick="editReminder(${reminder.id})">
                                    <i data-feather="edit-2"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteReminder(${reminder.id})">
                                    <i data-feather="trash-2"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            remindersHtml += '</div>';
        }
        
        remindersHtml += `
                        </div>
                        <div class="tab-pane fade" id="upcomingReminders">
                            <div id="upcomingRemindersList">
                                <!-- Will be populated when tab is clicked -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Modal for adding/editing reminders -->
            <div class="modal fade" id="reminderModal" tabindex="-1" aria-labelledby="reminderModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="reminderModalLabel">Add New Reminder</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="reminderForm">
                                <input type="hidden" id="reminderId">
                                <div class="mb-3">
                                    <label for="reminderTask" class="form-label">Task</label>
                                    <select class="form-select" id="reminderTask" required>
                                        <!-- Tasks will be loaded here -->
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label for="reminderTime" class="form-label">Reminder Time</label>
                                    <input type="datetime-local" class="form-control" id="reminderTime" required>
                                </div>
                                <div class="mb-3">
                                    <label for="reminderMessage" class="form-label">Message (optional)</label>
                                    <textarea class="form-control" id="reminderMessage" rows="3"></textarea>
                                </div>
                                <div class="form-check mb-3">
                                    <input class="form-check-input" type="checkbox" id="reminderTriggered">
                                    <label class="form-check-label" for="reminderTriggered">
                                        Already triggered
                                    </label>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveReminderBtn">Save</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        remindersView.innerHTML = remindersHtml;
        feather.replace();
        
        // Set up event handlers
        document.getElementById('addReminderBtn').addEventListener('click', openReminderModal);
        document.getElementById('saveReminderBtn').addEventListener('click', saveReminder);
        
        // Set up tab change handlers
        document.querySelectorAll('.nav-tabs .nav-link').forEach(tab => {
            tab.addEventListener('click', function() {
                const tabId = this.getAttribute('href').substring(1);
                if (tabId === 'upcomingReminders') {
                    loadUpcomingReminders();
                }
            });
        });
    }
    
    // Load upcoming reminders tab
    function loadUpcomingReminders() {
        const upcomingContainer = document.getElementById('upcomingRemindersList');
        
        // Filter for upcoming, non-triggered reminders
        const now = new Date();
        const upcomingReminders = currentReminders.filter(reminder => 
            !reminder.triggered && new Date(reminder.reminder_time) > now
        );
        
        // Sort by time (soonest first)
        upcomingReminders.sort((a, b) => 
            new Date(a.reminder_time) - new Date(b.reminder_time)
        );
        
        if (upcomingReminders.length === 0) {
            upcomingContainer.innerHTML = '<div class="alert alert-info">No upcoming reminders.</div>';
            return;
        }
        
        let html = '<div class="list-group">';
        
        upcomingReminders.forEach(reminder => {
            const task = currentTasks.find(t => t.id === reminder.task_id) || { title: 'Unknown Task' };
            const reminderTime = new Date(reminder.reminder_time).toLocaleString();
            
            html += `
                <div class="list-group-item reminder-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">
                                <i data-feather="bell" class="text-warning me-1"></i>
                                ${reminder.message || `Reminder for: ${task.title}`}
                            </h6>
                            <div class="small">
                                <div>Task: <span class="fw-bold">${task.title}</span></div>
                                <div>Time: <span class="fw-bold">${reminderTime}</span></div>
                            </div>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="editReminder(${reminder.id})">
                                <i data-feather="edit-2"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteReminder(${reminder.id})">
                                <i data-feather="trash-2"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        upcomingContainer.innerHTML = html;
        feather.replace();
    }
    
    // Open the reminder modal for adding a new reminder
    function openReminderModal() {
        // Reset form
        document.getElementById('reminderForm').reset();
        document.getElementById('reminderId').value = '';
        document.getElementById('reminderModalLabel').textContent = 'Add New Reminder';
        
        // Populate task dropdown
        const taskSelect = document.getElementById('reminderTask');
        taskSelect.innerHTML = '';
        
        // Only show incomplete tasks
        const incompleteTasks = currentTasks.filter(task => !task.completed);
        
        incompleteTasks.forEach(task => {
            const option = document.createElement('option');
            option.value = task.id;
            option.textContent = task.title;
            taskSelect.appendChild(option);
        });
        
        // Set default reminder time (1 hour from now)
        const now = new Date();
        now.setHours(now.getHours() + 1);
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        
        document.getElementById('reminderTime').value = `${year}-${month}-${day}T${hours}:${minutes}`;
        
        // Show modal
        const reminderModal = new bootstrap.Modal(document.getElementById('reminderModal'));
        reminderModal.show();
    }
    
    // Edit an existing reminder
    window.editReminder = function(reminderId) {
        const reminder = currentReminders.find(r => r.id === reminderId);
        if (!reminder) return;
        
        document.getElementById('reminderId').value = reminder.id;
        document.getElementById('reminderTask').value = reminder.task_id;
        
        // Format reminder time for datetime-local input
        const reminderTime = new Date(reminder.reminder_time);
        const year = reminderTime.getFullYear();
        const month = String(reminderTime.getMonth() + 1).padStart(2, '0');
        const day = String(reminderTime.getDate()).padStart(2, '0');
        const hours = String(reminderTime.getHours()).padStart(2, '0');
        const minutes = String(reminderTime.getMinutes()).padStart(2, '0');
        
        document.getElementById('reminderTime').value = `${year}-${month}-${day}T${hours}:${minutes}`;
        document.getElementById('reminderMessage').value = reminder.message || '';
        document.getElementById('reminderTriggered').checked = reminder.triggered;
        
        document.getElementById('reminderModalLabel').textContent = 'Edit Reminder';
        
        // Populate task dropdown
        const taskSelect = document.getElementById('reminderTask');
        taskSelect.innerHTML = '';
        
        currentTasks.forEach(task => {
            const option = document.createElement('option');
            option.value = task.id;
            option.textContent = task.title;
            taskSelect.appendChild(option);
        });
        
        // Show modal
        const reminderModal = new bootstrap.Modal(document.getElementById('reminderModal'));
        reminderModal.show();
    };
    
    // Delete a reminder
    window.deleteReminder = async function(reminderId) {
        if (!confirm('Are you sure you want to delete this reminder?')) {
            return;
        }
        
        const result = await deleteData(`reminders/${reminderId}`);
        if (result) {
            // Remove reminder from list
            const reminderIndex = currentReminders.findIndex(r => r.id === reminderId);
            if (reminderIndex !== -1) {
                currentReminders.splice(reminderIndex, 1);
            }
            
            // Reload reminders view
            loadReminders();
        }
    };
    
    // Save a reminder (create or update)
    async function saveReminder() {
        const reminderId = document.getElementById('reminderId').value;
        const taskId = parseInt(document.getElementById('reminderTask').value);
        const reminderTime = document.getElementById('reminderTime').value;
        const message = document.getElementById('reminderMessage').value;
        const triggered = document.getElementById('reminderTriggered').checked;
        
        if (!taskId) {
            alert('Please select a task');
            return;
        }
        
        if (!reminderTime) {
            alert('Please set a reminder time');
            return;
        }
        
        const reminderData = {
            task_id: taskId,
            reminder_time: reminderTime,
            message: message,
            triggered: triggered
        };
        
        let result;
        
        if (reminderId) {
            // Update existing reminder
            result = await putData(`reminders/${reminderId}`, reminderData);
        } else {
            // Create new reminder
            result = await postData('reminders/', reminderData);
        }
        
        if (result) {
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('reminderModal')).hide();
            
            // Reload reminders
            loadReminders();
        }
    }
    
    // Filter reminders by task
    window.filterRemindersByTask = function() {
        applyReminderFilters();
    };
    
    // Filter reminders by status
    window.filterRemindersByStatus = function() {
        applyReminderFilters();
    };
    
    // Apply all reminder filters at once
    function applyReminderFilters() {
        const taskId = document.getElementById('reminderTaskFilter').value;
        const status = document.getElementById('reminderStatusFilter').value;
        
        const reminderItems = document.querySelectorAll('.reminder-item');
        
        reminderItems.forEach(item => {
            let showItem = true;
            
            // Filter by task
            if (taskId && item.dataset.task !== taskId) {
                showItem = false;
            }
            
            // Filter by status
            if (status && item.dataset.status !== status) {
                showItem = false;
            }
            
            item.style.display = showItem ? 'block' : 'none';
        });
    }
    
    // ====================================================
    // Progress View
    // ====================================================
    
    // Load progress view
    async function loadProgress() {
        const progressView = document.getElementById('progressView');
        progressView.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Load categories data first
        await loadCategoriesData();
        
        // Fetch progress data
        const overall = await fetchData('progress/overall');
        const byCategory = await fetchData('progress/by-category');
        const daily = await fetchData('progress/daily');
        const productivity = await fetchData('progress/productivity');
        
        if (!overall || !byCategory || !daily || !productivity) {
            progressView.innerHTML = '<div class="alert alert-warning">Unable to load progress data.</div>';
            return;
        }
        
        let progressHtml = `
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Progress Analytics</h2>
                <button class="btn btn-outline-secondary" onclick="refreshProgress()">
                    <i data-feather="refresh-cw"></i> Refresh Data
                </button>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body text-center">
                            <h5 class="card-title">Productivity Score</h5>
                            <div class="display-1 fw-bold mb-3">${productivity.productivity_score}</div>
                            <div class="progress mb-3" style="height: 10px;">
                                <div class="progress-bar" role="progressbar" style="width: ${productivity.productivity_score}%;" 
                                     aria-valuenow="${productivity.productivity_score}" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                            <p class="text-muted">Based on task completion, timeliness, and priority handling</p>
                        </div>
                        <div class="card-footer">
                            <div class="row text-center">
                                <div class="col">
                                    <small class="d-block text-muted">Completion</small>
                                    <span class="fw-bold">${productivity.factors.completion_rate}</span>
                                </div>
                                <div class="col">
                                    <small class="d-block text-muted">Timeliness</small>
                                    <span class="fw-bold">${productivity.factors.timeliness}</span>
                                </div>
                                <div class="col">
                                    <small class="d-block text-muted">Priority</small>
                                    <span class="fw-bold">${productivity.factors.high_priority_completion}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Overall Progress</h5>
                            <div class="row mb-4">
                                <div class="col-md-6">
                                    <h6>Goals</h6>
                                    <div class="progress mb-2" style="height: 20px;">
                                        <div class="progress-bar" role="progressbar" style="width: ${overall.goal_completion_rate}%;" 
                                             aria-valuenow="${overall.goal_completion_rate}" aria-valuemin="0" aria-valuemax="100">
                                            ${overall.goal_completion_rate}%
                                        </div>
                                    </div>
                                    <small class="text-muted">${overall.completed_goals} of ${overall.total_goals} goals completed</small>
                                </div>
                                <div class="col-md-6">
                                    <h6>Tasks</h6>
                                    <div class="progress mb-2" style="height: 20px;">
                                        <div class="progress-bar" role="progressbar" style="width: ${overall.task_completion_rate}%;" 
                                             aria-valuenow="${overall.task_completion_rate}" aria-valuemin="0" aria-valuemax="100">
                                            ${overall.task_completion_rate}%
                                        </div>
                                    </div>
                                    <small class="text-muted">${overall.completed_tasks} of ${overall.total_tasks} tasks completed</small>
                                </div>
                            </div>
                            <div class="mt-3">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h6>Overdue Tasks</h6>
                                    <span class="badge ${overall.overdue_tasks > 0 ? 'bg-danger' : 'bg-success'}">${overall.overdue_tasks}</span>
                                </div>
                                <div class="progress" style="height: 10px;">
                                    <div class="progress-bar bg-danger" role="progressbar" 
                                         style="width: ${Math.min(100, (overall.overdue_tasks / overall.total_tasks) * 100)}%;" 
                                         aria-valuenow="${overall.overdue_tasks}" aria-valuemin="0" aria-valuemax="${overall.total_tasks}"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Daily Task Completion</h5>
                        </div>
                        <div class="card-body">
                            <canvas id="dailyCompletionChart" height="250"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Progress by Category</h5>
                        </div>
                        <div class="card-body">
                            <canvas id="categoryProgressChart" height="300"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Categories Breakdown</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Category</th>
                                            <th>Goals</th>
                                            <th>Tasks</th>
                                            <th>Completion</th>
                                        </tr>
                                    </thead>
                                    <tbody>
        `;
        
        byCategory.forEach(category => {
            progressHtml += `
                <tr>
                    <td>
                        <span class="badge me-1" style="background-color: ${category.category_color}">&nbsp;</span>
                        ${category.category_name}
                    </td>
                    <td>${category.completed_goals}/${category.total_goals}</td>
                    <td>${category.completed_tasks}/${category.total_tasks}</td>
                    <td>
                        <div class="progress" style="height: 10px;">
                            <div class="progress-bar" role="progressbar" style="width: ${category.task_completion_rate}%;" 
                                 aria-valuenow="${category.task_completion_rate}" aria-valuemin="0" aria-valuemax="100"></div>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        progressHtml += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        progressView.innerHTML = progressHtml;
        feather.replace();
        
        // Initialize charts
        initDailyCompletionChart(daily);
        initCategoryProgressChart(byCategory);
    }
    
    // Refresh progress data
    window.refreshProgress = function() {
        loadProgress();
    };
    
    // Initialize daily task completion chart
    function initDailyCompletionChart(dailyData) {
        const ctx = document.getElementById('dailyCompletionChart').getContext('2d');
        
        // Extract data for chart
        const dates = dailyData.map(item => item.date);
        const completedTasks = dailyData.map(item => item.completed_tasks);
        const createdTasks = dailyData.map(item => item.created_tasks);
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Completed Tasks',
                        data: completedTasks,
                        backgroundColor: 'rgba(40, 167, 69, 0.2)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 2,
                        tension: 0.3
                    },
                    {
                        label: 'Created Tasks',
                        data: createdTasks,
                        backgroundColor: 'rgba(0, 123, 255, 0.2)',
                        borderColor: 'rgba(0, 123, 255, 1)',
                        borderWidth: 2,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }
    
    // Initialize category progress chart
    function initCategoryProgressChart(categoryData) {
        const ctx = document.getElementById('categoryProgressChart').getContext('2d');
        
        // Extract data for chart
        const categories = categoryData.map(item => item.category_name);
        const taskCompletionRates = categoryData.map(item => item.task_completion_rate);
        const categoryColors = categoryData.map(item => item.category_color);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: categories,
                datasets: [
                    {
                        label: 'Task Completion Rate (%)',
                        data: taskCompletionRates,
                        backgroundColor: categoryColors
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // ====================================================
    // Helper Functions
    // ====================================================
    
    // Load categories data
    async function loadCategoriesData() {
        currentCategories = await fetchData('categories');
        return currentCategories;
    }
    
    // Load goals data
    async function loadGoalsData() {
        currentGoals = await fetchData('goals');
        return currentGoals;
    }
    
    // Load tasks data
    async function loadTasksData() {
        currentTasks = await fetchData('tasks');
        return currentTasks;
    }
    
    // Find goal title by ID
    function findGoalTitle(goalId) {
        if (!currentGoals) return 'Unknown Goal';
        const goal = currentGoals.find(g => g.id === goalId);
        return goal ? goal.title : 'Unknown Goal';
    }
    
    // Handle refresh button click
    document.getElementById('refreshBtn').addEventListener('click', function() {
        if (currentView === 'dashboard') {
            loadDashboard();
        } else if (currentView === 'goals') {
            loadGoals();
        } else if (currentView === 'tasks') {
            loadTasks();
        } else if (currentView === 'categories') {
            loadCategories();
        } else if (currentView === 'reminders') {
            loadReminders();
        } else if (currentView === 'progress') {
            loadProgress();
        }
    });
    
    // Initialize the application
    loadDashboard();
});
