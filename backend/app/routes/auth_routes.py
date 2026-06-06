from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Temporary in-memory storage (you'll replace with database later)
users = []
next_id = 1

@auth_bp.route('/test', methods=['GET'])
def test():
    return {'message': 'Auth routes are working!'}, 200

@auth_bp.route('/register', methods=['POST'])
def register():
    global next_id
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'name', 'phone', 'date_of_birth', 'blood_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        for user in users:
            if user['email'] == data['email']:
                return jsonify({'error': 'Email already registered'}), 400
            if user['phone'] == data['phone']:
                return jsonify({'error': 'Phone already registered'}), 400
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        # Create user
        user = {
            'id': next_id,
            'email': data['email'],
            'password_hash': hashed_password,
            'name': data['name'],
            'phone': data['phone'],
            'date_of_birth': data['date_of_birth'],
            'blood_type': data['blood_type'],
            'role': data.get('role', 'donor'),
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        users.append(user)
        next_id += 1
        
        # Create tokens
        access_token = create_access_token(identity=user['id'])
        refresh_token = create_refresh_token(identity=user['id'])
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'phone': user['phone'],
                'blood_type': user['blood_type'],
                'role': user['role']
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Find user by email
        user = None
        for u in users:
            if u['email'] == data['email']:
                user = u
                break
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check password
        if not bcrypt.check_password_hash(user['password_hash'], data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create tokens
        access_token = create_access_token(identity=user['id'])
        refresh_token = create_refresh_token(identity=user['id'])
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'phone': user['phone'],
                'blood_type': user['blood_type'],
                'role': user['role']
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        
        # Find user by id
        user = None
        for u in users:
            if u['id'] == user_id:
                user = u
                break
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'phone': user['phone'],
                'blood_type': user['blood_type'],
                'role': user['role'],
                'date_of_birth': user['date_of_birth'],
                'created_at': user['created_at']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500