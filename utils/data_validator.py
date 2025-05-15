"""
Data validation utilities for the Mentora application
"""
import re
from datetime import datetime
from functools import wraps
from flask import request, jsonify
from config import PRIORITY_LEVELS, RECURRENCE_TYPES


def validate_request(schema):
    """
    Decorator for validating request data against a schema
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400
            
            data = request.get_json()
            validation_result = validate_data(data, schema)
            
            if validation_result.get('valid', False):
                return f(*args, **kwargs)
            else:
                return jsonify({"error": validation_result.get('errors')}), 400
        return wrapper
    return decorator


def validate_data(data, schema):
    """
    Validate data against a schema definition
    Returns dict with valid (bool) and errors (list)
    """
    errors = []
    
    # Check for required fields
    for field, rules in schema.items():
        if rules.get('required', False) and field not in data:
            errors.append(f"Field '{field}' is required")
    
    # Validate field values
    for field, value in data.items():
        if field in schema:
            field_errors = validate_field(field, value, schema[field])
            errors.extend(field_errors)
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def validate_field(field, value, rules):
    """
    Validate a single field value against its rules
    Returns a list of error messages (empty if valid)
    """
    errors = []
    
    # Check field type
    if 'type' in rules:
        type_error = validate_type(field, value, rules['type'])
        if type_error:
            errors.append(type_error)
    
    # Check min length for strings
    if rules.get('type') == 'string' and 'min_length' in rules and len(value) < rules['min_length']:
        errors.append(f"Field '{field}' must be at least {rules['min_length']} characters long")
    
    # Check max length for strings
    if rules.get('type') == 'string' and 'max_length' in rules and len(value) > rules['max_length']:
        errors.append(f"Field '{field}' cannot exceed {rules['max_length']} characters")
    
    # Check pattern for strings
    if rules.get('type') == 'string' and 'pattern' in rules and not re.match(rules['pattern'], value):
        errors.append(f"Field '{field}' does not match the required pattern")
    
    # Check min value for numbers
    if rules.get('type') in ('integer', 'number') and 'min' in rules and value < rules['min']:
        errors.append(f"Field '{field}' must be at least {rules['min']}")
    
    # Check max value for numbers
    if rules.get('type') in ('integer', 'number') and 'max' in rules and value > rules['max']:
        errors.append(f"Field '{field}' cannot exceed {rules['max']}")
    
    # Check enum values
    if 'enum' in rules and value not in rules['enum']:
        errors.append(f"Field '{field}' must be one of: {', '.join(map(str, rules['enum']))}")
    
    # Check date format
    if rules.get('type') == 'date' and value:
        try:
            if isinstance(value, str):
                datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            errors.append(f"Field '{field}' must be a valid ISO date format")
    
    # Custom validations
    if 'custom' in rules and callable(rules['custom']):
        custom_error = rules['custom'](value)
        if custom_error:
            errors.append(custom_error)
    
    return errors


def validate_type(field, value, expected_type):
    """
    Validate the type of a field value
    Returns error message if invalid, None if valid
    """
    if expected_type == 'string':
        if not isinstance(value, str):
            return f"Field '{field}' must be a string"
    elif expected_type == 'integer':
        if not isinstance(value, int) or isinstance(value, bool):
            return f"Field '{field}' must be an integer"
    elif expected_type == 'number':
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return f"Field '{field}' must be a number"
    elif expected_type == 'boolean':
        if not isinstance(value, bool):
            return f"Field '{field}' must be a boolean"
    elif expected_type == 'array':
        if not isinstance(value, list):
            return f"Field '{field}' must be an array"
    elif expected_type == 'object':
        if not isinstance(value, dict):
            return f"Field '{field}' must be an object"
    elif expected_type == 'date':
        # For dates, we accept string representations that can be parsed
        if isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return f"Field '{field}' must be a valid ISO date string"
        elif not isinstance(value, datetime):
            return f"Field '{field}' must be a date"
    
    return None


# Schemas for validation
category_schema = {
    'name': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 64
    },
    'description': {
        'type': 'string',
        'max_length': 256
    },
    'color': {
        'type': 'string',
        'pattern': r'^#[0-9A-Fa-f]{6}$'  # Hex color code
    }
}

goal_schema = {
    'title': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 128
    },
    'description': {
        'type': 'string'
    },
    'category_id': {
        'type': 'integer',
        'required': True
    },
    'start_date': {
        'type': 'date'
    },
    'end_date': {
        'type': 'date'
    },
    'completed': {
        'type': 'boolean'
    }
}

task_schema = {
    'title': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 128
    },
    'description': {
        'type': 'string'
    },
    'goal_id': {
        'type': 'integer',
        'required': True
    },
    'deadline': {
        'type': 'date'
    },
    'priority': {
        'type': 'integer',
        'enum': list(PRIORITY_LEVELS.keys())
    },
    'completed': {
        'type': 'boolean'
    },
    'recurrence_type': {
        'type': 'string',
        'enum': RECURRENCE_TYPES
    },
    'recurrence_value': {
        'type': 'integer',
        'min': 1
    },
    'parent_task_id': {
        'type': 'integer'
    }
}

reminder_schema = {
    'task_id': {
        'type': 'integer',
        'required': True
    },
    'reminder_time': {
        'type': 'date',
        'required': True
    },
    'message': {
        'type': 'string',
        'max_length': 256
    }
}

blueprint_schema = {
    'name': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 64
    },
    'description': {
        'type': 'string',
        'max_length': 256
    },
    'day_of_week': {
        'type': 'string',
        'enum': [None, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    },
    'is_active': {
        'type': 'boolean'
    }
}

time_slot_schema = {
    'title': {
        'type': 'string',
        'required': True,
        'min_length': 1,
        'max_length': 128
    },
    'description': {
        'type': 'string'
    },
    'category_id': {
        'type': 'integer',
        'required': True
    },
    'start_time': {
        'type': 'string',
        'required': True,
        'pattern': r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'  # HH:MM format
    },
    'end_time': {
        'type': 'string',
        'required': True,
        'pattern': r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'  # HH:MM format
    },
    'goal_id': {
        'type': 'integer'
    }
}

user_preference_schema = {
    'theme': {
        'type': 'string',
        'enum': ['dark', 'light', 'focus', 'study']
    },
    'font_size': {
        'type': 'string',
        'enum': ['small', 'medium', 'large']
    },
    'enable_voice': {
        'type': 'boolean'
    },
    'daily_review_time': {
        'type': 'string',
        'pattern': r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'  # HH:MM format
    },
    'do_not_disturb': {
        'type': 'boolean'
    }
}
