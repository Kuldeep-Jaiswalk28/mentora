from datetime import datetime
from app import db
from sqlalchemy.ext.hybrid import hybrid_property


class Category(db.Model):
    """Model for goal categories like study, freelancing, etc."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    color = db.Column(db.String(7), default="#6c757d")  # Default to secondary Bootstrap color
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    goals = db.relationship('Goal', backref='category', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Category {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Goal(db.Model):
    """Model for user goals across different categories"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='goal', lazy='dynamic', cascade="all, delete-orphan")
    
    @hybrid_property
    def progress(self):
        """Calculate progress percentage based on completed tasks"""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter_by(completed=True).count()
        return int((completed_tasks / total_tasks) * 100)
    
    def __repr__(self):
        return f"<Goal {self.title}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'progress': self.progress,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Task(db.Model):
    """Model for individual tasks within goals"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    goal_id = db.Column(db.Integer, db.ForeignKey('goal.id'), nullable=False)
    deadline = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.Integer, default=2)  # 1=High, 2=Medium, 3=Low
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    recurrence_type = db.Column(db.String(20), nullable=True)  # daily, weekly, monthly, etc.
    recurrence_value = db.Column(db.Integer, nullable=True)  # How many days/weeks/months
    parent_task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referential relationship for task dependencies
    subtasks = db.relationship(
        'Task', 
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    
    # Relationship with reminders
    reminders = db.relationship('Reminder', backref='task', lazy='dynamic', cascade="all, delete-orphan")
    
    @hybrid_property
    def is_overdue(self):
        """Check if the task is overdue"""
        if not self.deadline or self.completed:
            return False
        return datetime.utcnow() > self.deadline
    
    def __repr__(self):
        return f"<Task {self.title}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'goal_id': self.goal_id,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'priority': self.priority,
            'completed': self.completed,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'recurrence_type': self.recurrence_type,
            'recurrence_value': self.recurrence_value,
            'parent_task_id': self.parent_task_id,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Reminder(db.Model):
    """Model for task reminders"""
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    reminder_time = db.Column(db.DateTime, nullable=False)
    message = db.Column(db.String(256))
    triggered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Reminder for Task {self.task_id} at {self.reminder_time}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
            'message': self.message,
            'triggered': self.triggered,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
