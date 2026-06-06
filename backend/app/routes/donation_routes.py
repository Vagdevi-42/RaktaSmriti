from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.dynamodb_service import DonationModel, UserModel

donation_bp = Blueprint('donations', __name__)

@donation_bp.route('/donations', methods=['POST'])
@jwt_required()
def create_donation():
    """Record a new blood donation"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Verify donor exists
        donor = UserModel.find_by_user_id(user_id)
        if not donor:
            return jsonify({'error': 'Donor not found'}), 404
        
        # Check if donor is eligible
        if donor.get('eligibility_status') != 'eligible':
            return jsonify({'error': 'Donor is not eligible to donate'}), 400
        
        donation_data = {
            'donor_id': user_id,
            'blood_group': donor.get('blood_group'),
            'quantity_ml': data.get('quantity_ml', 450),
            'hospital_name': data.get('hospital_name')
        }
        
        donation = DonationModel.create(donation_data)
        
        return jsonify({
            'message': 'Donation recorded successfully',
            'donation': donation
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@donation_bp.route('/donations/my-donations', methods=['GET'])
@jwt_required()
def get_my_donations():
    """Get donation history of logged-in user"""
    try:
        user_id = get_jwt_identity()
        donations = DonationModel.get_by_donor(user_id)
        
        return jsonify({
            'count': len(donations),
            'donations': donations
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@donation_bp.route('/donations/stats', methods=['GET'])
def get_donation_stats():
    """Get donation statistics (public)"""
    try:
        stats = DonationModel.get_stats()
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500