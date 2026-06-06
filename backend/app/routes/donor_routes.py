from flask import Blueprint, jsonify
from ..services.dynamodb_service import UserModel

donor_bp = Blueprint('donors', __name__)

@donor_bp.route('/donors/debug', methods=['GET'])
def debug_donors():
    """Debug endpoint to see actual donors"""
    try:
        users = UserModel.get_all_users(50)
        
        all_donors = []
        blood_groups_found = set()
        
        for user in users:
            if user.get('role') == 'Emergency Donor':
                all_donors.append({
                    'user_id': user.get('user_id'),
                    'blood_group': user.get('blood_group'),
                    'role': user.get('role'),
                    'eligibility_status': user.get('eligibility_status')
                })
                blood_groups_found.add(user.get('blood_group'))
        
        return jsonify({
            'total_donors_found': len(all_donors),
            'blood_groups_in_db': list(blood_groups_found),
            'sample_donors': all_donors[:5]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@donor_bp.route('/donors', methods=['GET'])
def get_all_donors():
    """Get all donors"""
    try:
        users = UserModel.get_all_users(100)
        
        donors = []
        for user in users:
            if user.get('role') == 'Emergency Donor':
                donors.append({
                    'user_id': user.get('user_id'),
                    'blood_group': user.get('blood_group'),
                    'eligibility_status': user.get('eligibility_status'),
                    'status': user.get('status')
                })
        
        return jsonify({
            'count': len(donors),
            'donors': donors
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@donor_bp.route('/donors/blood/<blood_group>', methods=['GET'])
def get_donors_by_blood(blood_group):
    """Get donors by blood group - Direct scan approach"""
    try:
        # Direct scan without using the service method first
        users = UserModel.get_all_users(500)
        
        result = []
        for user in users:
            if user.get('role') == 'Emergency Donor' and user.get('blood_group') == blood_group:
                result.append({
                    'user_id': user.get('user_id'),
                    'blood_group': user.get('blood_group'),
                    'eligibility_status': user.get('eligibility_status'),
                    'status': user.get('status')
                })
        
        return jsonify({
            'blood_group': blood_group,
            'count': len(result),
            'donors': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500