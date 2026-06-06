// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function App() {
  const [stats, setStats] = useState(null);
  const [donors, setDonors] = useState([]);
  const [shortage, setShortage] = useState(null);
  const [patients, setPatients] = useState([]);
  const [selectedBloodGroup, setSelectedBloodGroup] = useState('O Positive');
  const [loading, setLoading] = useState(false);

  // Fetch statistics
  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_URL}/coordinator/statistics`);
      setStats(res.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  // Fetch donors by blood group
  const fetchDonors = async (bloodGroup) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/match/donors?blood_group=${bloodGroup}&limit=10`);
      setDonors(res.data.donors || []);
    } catch (error) {
      console.error('Error fetching donors:', error);
    }
    setLoading(false);
  };

  // Fetch shortage prediction
  const fetchShortage = async (bloodGroup) => {
    try {
      const res = await axios.get(`${API_URL}/predict/shortage/${bloodGroup}`);
      setShortage(res.data);
    } catch (error) {
      console.error('Error fetching shortage:', error);
    }
  };

  // Fetch patients needing blood
  const fetchPatients = async () => {
    try {
      const res = await axios.get(`${API_URL}/predict/patients/need-blood?days_ahead=7`);
      setPatients(res.data.upcoming_list || []);
    } catch (error) {
      console.error('Error fetching patients:', error);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchDonors(selectedBloodGroup);
    fetchShortage(selectedBloodGroup);
    fetchPatients();
  }, []);

  const handleBloodGroupChange = (bg) => {
    setSelectedBloodGroup(bg);
    fetchDonors(bg);
    fetchShortage(bg);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1 style={{ color: '#d32f2f', textAlign: 'center' }}>🩸 RaktaSmriti - Coordinator Dashboard</h1>
      
      {/* Stats Cards */}
      <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', marginBottom: '30px' }}>
        {stats && (
          <>
            <div style={{ backgroundColor: '#e3f2fd', padding: '20px', borderRadius: '10px', textAlign: 'center', flex: 1 }}>
              <h3>Bridge Donors</h3>
              <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{stats.bridge_donors}</p>
            </div>
            <div style={{ backgroundColor: '#e8f5e9', padding: '20px', borderRadius: '10px', textAlign: 'center', flex: 1 }}>
              <h3>Emergency Donors</h3>
              <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{stats.emergency_donors}</p>
            </div>
            <div style={{ backgroundColor: '#fff3e0', padding: '20px', borderRadius: '10px', textAlign: 'center', flex: 1 }}>
              <h3>Patients</h3>
              <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{stats.patients}</p>
            </div>
            <div style={{ backgroundColor: '#f3e5f5', padding: '20px', borderRadius: '10px', textAlign: 'center', flex: 1 }}>
              <h3>Ghost Donors</h3>
              <p style={{ fontSize: '32px', fontWeight: 'bold', margin: 0 }}>{stats.ghost_donors}</p>
            </div>
          </>
        )}
      </div>

      {/* Shortage Risk */}
      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', marginBottom: '30px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <h3>Shortage Risk Prediction</h3>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          <select value={selectedBloodGroup} onChange={(e) => handleBloodGroupChange(e.target.value)} style={{ padding: '8px' }}>
            <option>O Positive</option>
            <option>A Positive</option>
            <option>B Positive</option>
            <option>AB Positive</option>
            <option>O Negative</option>
            <option>A Negative</option>
            <option>B Negative</option>
            <option>AB Negative</option>
          </select>
          {shortage && (
            <div>
              <p>Patients Need: <strong>{shortage.patients_need}</strong></p>
              <p>Donors Available: <strong>{shortage.donors_available}</strong></p>
              <p style={{ 
                color: shortage.shortage_risk === 'HIGH' ? 'red' : shortage.shortage_risk === 'MEDIUM' ? 'orange' : 'green',
                fontWeight: 'bold'
              }}>
                Risk Level: {shortage.shortage_risk}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Donors Table */}
      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', marginBottom: '30px' }}>
        <h3>Top Donors - {selectedBloodGroup}</h3>
        {loading ? <p>Loading...</p> : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f5f5f5' }}>
                <th style={{ padding: '10px', textAlign: 'left' }}>Donor ID</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Reliability Score</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Donations</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Status</th>
               </tr>
            </thead>
            <tbody>
              {donors.map((donor, index) => (
                <tr key={index} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '10px' }}>{donor.user_id?.substring(0, 30)}...</td>
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
                  <td style={{ padding: '10px' }}>{donor.status || 'active'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Patients Needing Blood */}
      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px' }}>
        <h3>Patients Needing Blood (Next 7 Days)</h3>
        {patients.length === 0 ? (
          <p>No patients predicted to need blood in the next 7 days.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f5f5f5' }}>
                <th style={{ padding: '10px', textAlign: 'left' }}>Patient ID</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Blood Group</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Days Until</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient, index) => (
                <tr key={index} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '10px' }}>{patient.patient_id?.substring(0, 30)}...</td>
                  <td style={{ padding: '10px' }}>{patient.blood_group}</td>
                  <td style={{ padding: '10px', color: patient.days_until <= 2 ? 'red' : 'orange' }}>
                    {patient.days_until} days
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default App;