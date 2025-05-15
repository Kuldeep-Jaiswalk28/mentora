import os
import logging
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
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
    return render_template('index.html')

# API route for progress data
@app.route('/api/progress/overall')
def overall_progress():
    from services.progress_service import get_overall_progress
    from flask import jsonify
    return jsonify(get_overall_progress())

# API route for recent activity
@app.route('/api/progress/recent')
def recent_activity():
    from services.progress_service import get_recent_activity
    from flask import jsonify
    return jsonify(get_recent_activity())

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
    
    app.register_blueprint(goals_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(reminders_bp)
    
    # Initialize reminder scheduler
    from utils.reminder_scheduler import initialize_reminders
    initialize_reminders(scheduler)

    logger.info("Mentora backend started successfully")
