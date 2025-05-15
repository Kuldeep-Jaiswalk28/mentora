import os

class Config:
    """Base configuration class for the application"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SESSION_SECRET", "mentora_default_secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///mentora.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

class ProductionConfig(Config):
    """Production configuration"""
    pass

# Configuration dictionary
config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Default categories
DEFAULT_CATEGORIES = [
    {
        'name': 'Study',
        'description': 'Academic and learning goals',
        'color': '#0d6efd'  # Bootstrap primary
    },
    {
        'name': 'Freelancing',
        'description': 'Freelance work and projects',
        'color': '#6610f2'  # Bootstrap purple
    },
    {
        'name': 'AI Tools',
        'description': 'AI learning and development goals',
        'color': '#6f42c1'  # Bootstrap indigo
    },
    {
        'name': 'Certifications',
        'description': 'Professional certifications and courses',
        'color': '#d63384'  # Bootstrap pink
    },
    {
        'name': 'Career Planning',
        'description': 'Career development and planning',
        'color': '#198754'  # Bootstrap success
    }
]

# Task priority levels
PRIORITY_LEVELS = {
    1: {
        'name': 'High',
        'description': 'Urgent and important tasks',
        'color': '#dc3545'  # Bootstrap danger
    },
    2: {
        'name': 'Medium',
        'description': 'Important but not urgent tasks',
        'color': '#fd7e14'  # Bootstrap orange
    },
    3: {
        'name': 'Low',
        'description': 'Tasks that can be delayed',
        'color': '#20c997'  # Bootstrap teal
    }
}

# Recurrence types for tasks
RECURRENCE_TYPES = [
    'daily',
    'weekly',
    'monthly',
    'yearly',
    'custom'
]
