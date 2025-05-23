import os
import logging
from flask import Flask, render_template, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler


# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "mentora_default_secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

def add_cors_headers(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        resp = make_response(f(*args, **kwargs))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp
    return decorated_function

# Apply CORS to all routes
@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///mentora.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Main route for the application
@app.route('/')
def index():
    # Get current date and day for the template
    from datetime import datetime
    current_date = datetime.utcnow().strftime("%B %d, %Y")
    current_day = datetime.utcnow().strftime("%A")
    
    # Render the index template with date info
    return render_template('index.html', 
                          current_date=current_date,
                          current_day=current_day)

# API route for progress data
@app.route('/api/progress/overall')
def overall_progress():
    from services.progress_service import get_overall_progress
    from flask import jsonify
    return jsonify(get_overall_progress())

# API route for recent activity
@app.route('/api/progress/recent')
def recent_activity():
    from services.progress_service import get_recent_progress
    from flask import jsonify
    return jsonify(get_recent_progress(7))  # Get last 7 days of progress

with app.app_context():
    # Import models
    import models  # noqa: F401

    # Create all tables
    db.create_all()

    # Register blueprints/routes
    from routes.goal_routes import goals_bp
    from routes.task_routes import tasks_bp
    from routes.category_routes import categories_bp
    from routes.reminder_routes import reminders_bp
    from routes.blueprint_routes import blueprint_bp
    from routes.mentor_routes import mentor_bp
    from routes.progress_routes import progress_bp
    from routes.reward_routes import reward_bp
    from routes.schedule_routes import schedule_bp

    app.register_blueprint(goals_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(blueprint_bp)
    app.register_blueprint(mentor_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(reward_bp)
    app.register_blueprint(schedule_bp)

    # Initialize reminder scheduler
    from utils.reminder_scheduler import initialize_reminders
    initialize_reminders(scheduler)
    
    # Initialize progress tracking scheduler
    from utils.progress_scheduler import initialize_progress_tracking
    initialize_progress_tracking(scheduler)
    
    # Initialize the scheduling engine
    from services.blueprint_import_service import load_blueprint_file, import_blueprint_to_database
    from services.schedule_engine import regenerate_schedule
    
    # Import any existing blueprint and generate schedule
    try:
        logger.info("Initializing scheduling engine...")
        blueprint_data = load_blueprint_file()
        if blueprint_data:
            import_blueprint_to_database(blueprint_data)
            regenerate_schedule()
        logger.info("Scheduling engine initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing scheduling engine: {str(e)}")

    logger.info("Mentora backend started successfully")