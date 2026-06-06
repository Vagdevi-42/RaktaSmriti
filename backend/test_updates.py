# backend/test_updates.py
from app.services.update_service import update_donor_after_donation, mark_donor_response

# Test marking a donor's response
print("Testing mark_donor_response...")
result = mark_donor_response('test_donor_123', 'yes')
print(result)

# Test donor after donation (use a real donor_id from your table)
# result = update_donor_after_donation('your_real_donor_id_here')
# print(result)