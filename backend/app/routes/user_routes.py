from flask import Blueprint, jsonify
from ..services.dynamodb_service import UserModel

user_bp = Blueprint('users', __name__)

@user_bp.route('/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello from user routes!'}), 200

@user_bp.route('/donors/<blood_group>', methods=['GET'])
def get_donors_by_blood(blood_group):
    """Get all donors by blood group"""
    try:
        donors = UserModel.get_donors_by_blood_group(blood_group)
        
        # Remove sensitive info and format response
        safe_donors = []
        for donor in donors:
            safe_donors.append({
                'user_id': donor.get('user_id'),
                'blood_group': donor.get('blood_group'),
                'role': donor.get('role'),
                'status': donor.get('status'),
                'eligibility_status': donor.get('eligibility_status'),
                'latitude': donor.get('latitude'),
                'longitude': donor.get('longitude')
            })
        
        return jsonify({
            'blood_group': blood_group,
            'count': len(safe_donors),
            'donors': safe_donors
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users', methods=['GET'])
def get_all_users():
    """Get all users (for testing)"""
    try:
        users = UserModel.get_all(limit=50)
        
        safe_users = []
        for user in users:
            safe_users.append({
                'user_id': user.get('user_id'),
                'role': user.get('role'),
                'blood_group': user.get('blood_group'),
                'status': user.get('status'),
                'eligibility_status': user.get('eligibility_status')
            })
        
        return jsonify({
            'count': len(safe_users),
            'users': safe_users
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/user/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Get a specific user by ID"""
    try:
        user = UserModel.find_by_user_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'user_id': user.get('user_id'),
                'role': user.get('role'),
                'blood_group': user.get('blood_group'),
                'status': user.get('status'),
                'eligibility_status': user.get('eligibility_status'),
                'latitude': user.get('latitude'),
                'longitude': user.get('longitude')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500