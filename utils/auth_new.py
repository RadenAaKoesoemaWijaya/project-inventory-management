import streamlit as st
from .sqlite_database import (
    get_user_by_username, 
    get_user_by_id, 
    update_user, 
    create_user,
    hash_password, 
    verify_password,
    get_all_users
)
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

def login_user(username, password):
    """Authenticate a user and return user data if successful"""
    try:
        # Get user from database
        user = get_user_by_username(username)
        
        if user and verify_password(user['password'], password):
            # Update last login
            update_user(user['id'], {"last_login": datetime.now().isoformat()})
            
            # Store user info in session state
            st.session_state['authenticated'] = True
            st.session_state['user'] = {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user['role'],
                'department': user.get('department', ''),
                'is_active': user.get('is_active', 1)
            }
            
            logger.info(f"User {username} logged in successfully")
            return True
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return False
            
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return False

def logout_user():
    """Log out the current user"""
    try:
        if 'user' in st.session_state:
            username = st.session_state['user']['username']
            logger.info(f"User {username} logged out")
            
        st.session_state['authenticated'] = False
        if 'user' in st.session_state:
            del st.session_state['user']
            
    except Exception as e:
        logger.error(f"Error during logout: {e}")

def require_auth():
    """Require authentication to access a page"""
    if not st.session_state.get('authenticated', False):
        st.warning('You need to log in to access this page.')
        st.stop()

def require_role(roles):
    """Require specific role(s) to access a page"""
    require_auth()
    user_role = st.session_state['user']['role']
    if isinstance(roles, str):
        roles = [roles]
    
    if user_role not in roles:
        st.error('You do not have permission to access this page.')
        st.stop()

def register_user(username, password, full_name, role, department=None):
    """
    Register a new user in the database
    
    Args:
        username (str): Username for the new user
        password (str): Password for the new user
        full_name (str): Full name of the new user
        role (str): Role of the new user (admin, staff, etc.)
        department (str, optional): Department for the new user
        
    Returns:
        tuple: (success, message)
    """
    try:
        success, message = create_user(username, password, full_name, role, department)
        
        if success:
            logger.info(f"User {username} registered successfully")
        else:
            logger.warning(f"Registration failed: {message}")
            
        return success, message
            
    except Exception as e:
        logger.error(f"Error registering user {username}: {e}")
        return False, f"Error: {str(e)}"

def get_user_by_username(username):
    """Get user by username"""
    try:
        from .sqlite_database import get_user_by_username as db_get_user_by_username
        return db_get_user_by_username(username)
    except Exception as e:
        logger.error(f"Error getting user {username}: {e}")
        return None

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        from .sqlite_database import get_user_by_id as db_get_user_by_id
        return db_get_user_by_id(user_id)
    except Exception as e:
        logger.error(f"Error getting user by ID {user_id}: {e}")
        return None

def update_user(user_id, update_data):
    """Update user data"""
    try:
        from .sqlite_database import update_user as db_update_user
        success = db_update_user(user_id, update_data)
        
        if success:
            logger.info(f"User {user_id} updated successfully")
        else:
            logger.warning(f"No changes made to user {user_id}")
            
        return success
            
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return False

def delete_user(user_id):
    """Delete user (soft delete by setting is_active to False)"""
    try:
        success = update_user(user_id, {"is_active": 0})
        
        if success:
            logger.info(f"User {user_id} deleted (soft delete) successfully")
        else:
            logger.warning(f"No changes made to user {user_id}")
            
        return success
            
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return False

def get_all_users(limit=100, skip=0, include_inactive=False):
    """Get all users with pagination"""
    try:
        from .sqlite_database import get_all_users as db_get_all_users
        users = db_get_all_users(limit, skip, include_inactive)
        return users
        
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

def check_user_permissions(required_roles=None, required_permissions=None):
    """Check if current user has required roles or permissions"""
    if not st.session_state.get('authenticated', False):
        return False
    
    user = st.session_state.get('user', {})
    
    if required_roles:
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        if user.get('role') not in required_roles:
            return False
    
    if required_permissions:
        # This can be extended to check specific permissions
        user_permissions = user.get('permissions', [])
        if not all(perm in user_permissions for perm in required_permissions):
            return False
    
    return True
