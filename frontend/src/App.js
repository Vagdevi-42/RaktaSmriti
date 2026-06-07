import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

function App() {
  const [stats, setStats] = useState(null);
  const [donors, setDonors] = useState([]);
  const [shortage, setShortage] = useState(null);
  const [patients, setPatients] = useState([]);
  const [urgentPatients, setUrgentPatients] = useState([]);
  const [selectedBloodGroup, setSelectedBloodGroup] = useState('O Positive');
  const [maxDistance, setMaxDistance] = useState(5);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [checkedInDonors, setCheckedInDonors] = useState({});
  const [ghostQr, setGhostQr] = useState(null);
  const [ghostLoading, setGhostLoading] = useState(false);
  const [demoTrigger, setDemoTrigger] = useState(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [liveTrigger, setLiveTrigger] = useState(null);
  const [liveTriggerLoading, setLiveTriggerLoading] = useState(false);

  const fetchStats = async () => {
    try {
      const res = await axios.get(API_URL + '/coordinator/statistics');
      setStats(res.data);
    } catch (error) {
      console.log('Error fetching stats:', error);
    }
  };

  const fetchNearbyDonors = async () => {
    setLoading(true);
    try {
      const res = await axios.get(API_URL + '/match/donors/nearby', {
        params: {
          blood_group: selectedBloodGroup,
          max_distance_km: maxDistance,
          limit: 20
        }
      });
      setDonors(res.data.donors || []);
      setMessage('Found ' + (res.data.total_nearby_donors || 0) + ' donors within ' + maxDistance + 'km');
    } catch (error) {
      console.log('Error fetching donors:', error);
      setMessage('Error fetching donors');
    }
    setLoading(false);
  };

  const fetchShortage = async () => {
    try {
      const res = await axios.get(API_URL + '/predict/shortage/' + selectedBloodGroup);
      setShortage(res.data);
    } catch (error) {
      console.log('Error fetching shortage:', error);
    }
  };

  const fetchPatients = async () => {
    try {
      const res = await axios.get(API_URL + '/predict/patients?days_ahead=7');
      setPatients(res.data.upcoming_list || []);
      setUrgentPatients(res.data.urgent_list || []);
    } catch (error) {
      console.log('Error fetching patients:', error);
    }
  };

  const markCheckin = async (donorId, showedUp) => {
    try {
      const response = await axios.post(
        API_URL + '/coordinator/donor/checkin',
        null,
        { params: { donor_id: donorId, showed_up: showedUp } }
      );
      
      if (response.data.success) {
        setCheckedInDonors(prev => ({ ...prev, [donorId]: true }));
        setMessage('Donor checked in. New score: ' + response.data.new_reliability_score);
        await fetchNearbyDonors();
        await fetchStats();
      }
    } catch (error) {
      console.log('Error marking checkin:', error);
      setMessage('Error marking check-in');
    }
  };

  const sendDonationRequest = async () => {
    setLoading(true);
    try {
      const res = await axios.post(API_URL + '/donation/send-to-nearby', null, {
        params: {
          blood_group: selectedBloodGroup,
          max_distance_km: maxDistance,
          donation_time: "Tomorrow, 10:00 AM"
        }
      });
      setMessage(res.data.message + ' Tier1: ' + (res.data.cascade?.tier1_count || 0) + ' donors notified');
      fetchNearbyDonors();
    } catch (error) {
      console.log('Error sending request:', error);
      setMessage('Error sending donation requests');
    }
    setLoading(false);
  };

  const fetchGhostQr = async () => {
    setGhostLoading(true);
    try {
      const res = await axios.get(API_URL + '/ghost/qr/demo-campaign');
      setGhostQr(res.data);
      await fetchStats();
    } catch (error) {
      console.log('Error fetching ghost donor QR:', error);
      setMessage('Error fetching ghost donor QR');
    }
    setGhostLoading(false);
  };

  const runDemoTrigger = async () => {
    setDemoLoading(true);
    try {
      const res = await axios.get(API_URL + '/predict/trigger/' + selectedBloodGroup + '?days_ahead=7&demo_mode=true');
      setDemoTrigger(res.data);
      setMessage('Demo auto-trigger executed. No real Twilio message was sent.');
    } catch (error) {
      console.log('Error running demo trigger:', error);
      setMessage('Error running demo trigger');
    }
    setDemoLoading(false);
  };

  const runLiveTrigger = async () => {
    setLiveTriggerLoading(true);
    try {
      const res = await axios.get(API_URL + '/predict/trigger/' + selectedBloodGroup + '?days_ahead=7&demo_mode=false');
      setLiveTrigger(res.data);
      setMessage('Live auto-trigger executed. Donor WhatsApp requests were sent if eligible donors were found.');
    } catch (error) {
      console.log('Error running live trigger:', error);
      setMessage('Error running live auto-trigger');
    }
    setLiveTriggerLoading(false);
  };

  useEffect(() => {
    fetchStats();
    fetchNearbyDonors();
    fetchShortage();
    fetchPatients();
    fetchGhostQr();

    const statsTimer = setInterval(() => {
      fetchStats();
    }, 10000);

    return () => clearInterval(statsTimer);
  }, []);

  const handleBloodGroupChange = (bg) => {
    setSelectedBloodGroup(bg);
    setTimeout(() => {
      fetchNearbyDonors();
      fetchShortage();
    }, 100);
  };

  const handleDistanceChange = (dist) => {
    setMaxDistance(dist);
    setTimeout(() => fetchNearbyDonors(), 100);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{ color: '#d32f2f', textAlign: 'center' }}>RaktaSmriti - Coordinator Dashboard</h1>
      
      {message && (
        <div style={{ backgroundColor: '#e8f5e9', padding: '10px', borderRadius: '5px', marginBottom: '20px', textAlign: 'center' }}>
          {message}
        </div>
      )}

      <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', marginBottom: '30px', flexWrap: 'wrap' }}>
        {stats && (
          <>
            <div style={{ backgroundColor: '#e3f2fd', padding: '20px', borderRadius: '10px', textAlign: 'center', minWidth: '150px' }}>
              <h3>Bridge Donors</h3>
              <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{stats.bridge_donors}</p>
            </div>
            <div style={{ backgroundColor: '#e8f5e9', padding: '20px', borderRadius: '10px', textAlign: 'center', minWidth: '150px' }}>
              <h3>Emergency Donors</h3>
              <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{stats.emergency_donors}</p>
            </div>
            <div style={{ backgroundColor: '#fff3e0', padding: '20px', borderRadius: '10px', textAlign: 'center', minWidth: '150px' }}>
              <h3>Patients</h3>
              <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{stats.patients}</p>
            </div>
            <div style={{ backgroundColor: '#f3e5f5', padding: '20px', borderRadius: '10px', textAlign: 'center', minWidth: '150px' }}>
              <h3>Ghost Donors</h3>
              <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{stats.ghost_donors}</p>
            </div>
          </>
        )}
      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', marginBottom: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <label>Blood Group: </label>
            <select value={selectedBloodGroup} onChange={(e) => handleBloodGroupChange(e.target.value)} style={{ padding: '8px', marginLeft: '10px' }}>
              <option>O Positive</option>
              <option>A Positive</option>
              <option>B Positive</option>
              <option>AB Positive</option>
              <option>O Negative</option>
              <option>A Negative</option>
              <option>B Negative</option>
              <option>AB Negative</option>
            </select>
          </div>
          <div>
            <label>Max Distance (km): </label>
            <input type="number" value={maxDistance} onChange={(e) => handleDistanceChange(e.target.value)} style={{ padding: '8px', width: '70px', marginLeft: '10px' }} />
          </div>
          <button onClick={sendDonationRequest} style={{ backgroundColor: '#d32f2f', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer' }}>
            Send Donation Request
          </button>
          <button
            onClick={async () => {
              await fetchNearbyDonors();
              await fetchStats();
            }}
            style={{ backgroundColor: '#2196f3', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '5px', cursor: 'pointer' }}
          >
            Refresh Donors
          </button>
        </div>
      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', marginBottom: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <h3>Ghost Donor QR Registration</h3>
        <p style={{ color: '#555' }}>Generate a WhatsApp registration QR for emergency donor signup.</p>
        <button onClick={fetchGhostQr} style={{ backgroundColor: '#7b1fa2', color: 'white', border: 'none', padding: '10px 16px', borderRadius: '5px', cursor: 'pointer', marginBottom: '12px' }}>
          Refresh QR
        </button>
        {ghostLoading ? <p>Loading QR...</p> : ghostQr?.qr_code_base64 ? (
          <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start', flexWrap: 'wrap' }}>
            <img
              src={`data:image/png;base64,${ghostQr.qr_code_base64}`}
              alt="Ghost donor registration QR"
              style={{ width: '220px', height: '220px', border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}
            />
            <div style={{ maxWidth: '420px' }}>
              <p><strong>Registration ID:</strong> {ghostQr.registration_id}</p>
              <p><strong>WhatsApp link:</strong></p>
              <a href={ghostQr.whatsapp_link} target="_blank" rel="noreferrer" style={{ color: '#1565c0', wordBreak: 'break-all' }}>
                {ghostQr.whatsapp_link}
              </a>
              <p style={{ color: '#666', marginTop: '8px' }}>{ghostQr.instructions}</p>
            </div>
          </div>
        ) : <p>No QR generated yet.</p>}

      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', marginBottom: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <h3>AI Auto-Trigger</h3>
        <p style={{ color: '#555' }}>Use this to show the prediction → donor alert flow in the dashboard. The demo button keeps Twilio disabled; the live button uses the real trigger path.</p>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '10px' }}>
          <button onClick={runDemoTrigger} style={{ backgroundColor: '#0d47a1', color: 'white', border: 'none', padding: '10px 16px', borderRadius: '5px', cursor: 'pointer' }}>
            {demoLoading ? 'Running Demo...' : 'Run Demo Auto-Trigger'}
          </button>
          <button onClick={runLiveTrigger} style={{ backgroundColor: '#d32f2f', color: 'white', border: 'none', padding: '10px 16px', borderRadius: '5px', cursor: 'pointer' }}>
            {liveTriggerLoading ? 'Running Live Trigger...' : 'Run Live Auto-Trigger'}
          </button>
        </div>

        {demoTrigger && (
          <div style={{ backgroundColor: '#eef4ff', padding: '10px', borderRadius: '6px', marginBottom: '10px' }}>
            <p><strong>Demo message:</strong> {demoTrigger.message}</p>
            <p><strong>Patients needing:</strong> {demoTrigger.patients_needing}</p>
            <p><strong>Urgent count:</strong> {demoTrigger.urgent_count}</p>
            <p><strong>Action:</strong> {demoTrigger.action}</p>
          </div>
        )}

        {liveTrigger && (
          <div style={{ backgroundColor: '#fff3e0', padding: '10px', borderRadius: '6px' }}>
            <p><strong>Live trigger result:</strong> {liveTrigger.message}</p>
            <p><strong>Patients needing:</strong> {liveTrigger.patients_needing}</p>
            <p><strong>Urgent count:</strong> {liveTrigger.urgent_count}</p>
            <p><strong>Twilio action:</strong> {liveTrigger.action}</p>
          </div>
        )}
      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', marginBottom: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <h3>Shortage Risk Prediction</h3>
        {shortage && (
          <div>
            <p>Patients Need: <strong>{shortage.patients_need}</strong></p>
            <p>Donors Available: <strong>{shortage.donors_available}</strong></p>
            <p style={{ 
              color: shortage.shortage_risk === 'HIGH' ? 'red' : shortage.shortage_risk === 'MEDIUM' ? 'orange' : 'green',
              fontWeight: 'bold',
              fontSize: '18px'
            }}>
              Risk Level: {shortage.shortage_risk}
            </p>
            <p>{shortage.recommendation}</p>
          </div>
        )}
      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', marginBottom: '20px', overflowX: 'auto' }}>
        <h3>Nearby Donors - {selectedBloodGroup} (within {maxDistance}km)</h3>
        {loading ? <p>Loading...</p> : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f5f5f5', borderBottom: '1px solid #ddd' }}>
                <th style={{ padding: '10px', textAlign: 'left' }}>Donor ID</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Distance</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Reliability Score</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Donations</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Phone</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Actions</th>
               </tr>
            </thead>
            <tbody>
              {donors.map((donor, index) => (
                <tr key={index} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '10px' }}>{(donor.user_id || '').substring(0, 20)}...</td>
                  <td style={{ padding: '10px' }}>{donor.distance_km || '?'} km</td>
                  <td style={{ padding: '10px' }}>
                    <span style={{ 
                      backgroundColor: donor.reliability_score >= 80 ? '#4caf50' : donor.reliability_score >= 60 ? '#ff9800' : '#f44336',
                      color: 'white',
                      padding: '4px 8px',
                      borderRadius: '4px'
                    }}>
                      {donor.reliability_score || 0}
                    </span>
                  </td>
                  <td style={{ padding: '10px' }}>{donor.donations_till_date || 0}</td>
                  <td style={{ padding: '10px' }}>{donor.phone_number || 'N/A'}</td>
                  <td style={{ padding: '10px' }}>
                    {checkedInDonors[donor.user_id] ? (
                      <span style={{ backgroundColor: '#4caf50', color: 'white', padding: '5px 10px', borderRadius: '3px' }}>
                        Done
                      </span>
                    ) : (
                      <div>
                        <button 
                          onClick={() => markCheckin(donor.user_id, true)} 
                          style={{ backgroundColor: '#4caf50', color: 'white', border: 'none', padding: '5px 10px', marginRight: '5px', borderRadius: '3px', cursor: 'pointer' }}
                        >
                          Showed Up
                        </button>
                        <button 
                          onClick={() => markCheckin(donor.user_id, false)} 
                          style={{ backgroundColor: '#f44336', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '3px', cursor: 'pointer' }}
                        >
                          No Show
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {donors.length === 0 && !loading && <p>No nearby donors found</p>}
      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px' }}>
        <h3>Patients Needing Blood</h3>
        {patients.length === 0 && urgentPatients.length === 0 ? (
          <p>No patients predicted to need blood.</p>
        ) : (
          <div>
            {urgentPatients.length > 0 && (
              <div>
                <h4 style={{ color: 'red' }}>URGENT - Overdue Patients ({urgentPatients.length})</h4>
                <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#ffebee' }}>
                      <th style={{ padding: '10px', textAlign: 'left' }}>Patient ID</th>
                      <th style={{ padding: '10px', textAlign: 'left' }}>Blood Group</th>
                      <th style={{ padding: '10px', textAlign: 'left' }}>Days Overdue</th>
                      <th style={{ padding: '10px', textAlign: 'left' }}>Expected Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {urgentPatients.map((patient, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #eee', backgroundColor: '#fff5f5' }}>
                        <td style={{ padding: '10px' }}>{(patient.patient_id || '').substring(0, 20)}...</td>
                        <td style={{ padding: '10px' }}>{patient.blood_group}</td>
                        <td style={{ padding: '10px', color: 'red', fontWeight: 'bold' }}>
                          {Math.abs(patient.days_until)} days overdue
                        </td>
                        <td style={{ padding: '10px' }}>{patient.expected_date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {patients.length > 0 && (
              <div>
                <h4>Upcoming Patients ({patients.length})</h4>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f5f5f5' }}>
                      <th style={{ padding: '10px', textAlign: 'left' }}>Patient ID</th>
                      <th style={{ padding: '10px', textAlign: 'left' }}>Blood Group</th>
                      <th style={{ padding: '10px', textAlign: 'left' }}>Days Until</th>
                      <th style={{ padding: '10px', textAlign: 'left' }}>Expected Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patients.map((patient, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '10px' }}>{(patient.patient_id || '').substring(0, 20)}...</td>
                        <td style={{ padding: '10px' }}>{patient.blood_group}</td>
                        <td style={{ padding: '10px', color: patient.days_until <= 2 ? 'red' : 'orange' }}>
                          {patient.days_until} days
                        </td>
                        <td style={{ padding: '10px' }}>{patient.expected_date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;