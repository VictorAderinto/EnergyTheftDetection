import { AlertTriangle, Activity } from 'lucide-react';

export default function Sidebar({ buildings, selectedBuilding, onSelectBuilding }) {
  
  // Sort buildings by risk score descending
  const sortedBuildings = [...buildings].sort((a, b) => b.risk_score - a.risk_score);

  return (
    <div className="sidebar glass-panel">
      <div className="sidebar-header">
        <h1><Activity className="text-blue-500" /> AI Energy Monitor</h1>
        <p>Lagos District - Anomaly Detection Queue</p>
      </div>
      
      <div className="building-list">
        {sortedBuildings.length === 0 ? (
          <div style={{ textAlign: 'center', marginTop: '2rem', color: 'var(--text-muted)' }}>
            Loading data...
          </div>
        ) : null}
        
        {sortedBuildings.map(building => {
          let riskClass = 'risk-low';
          if (building.risk_score >= 75) riskClass = 'risk-high';
          else if (building.risk_score >= 40) riskClass = 'risk-med';
          
          return (
            <div 
              key={building.building_id}
              className={`building-card ${selectedBuilding?.building_id === building.building_id ? 'selected' : ''}`}
              onClick={() => onSelectBuilding(building)}
            >
              <div className="card-header">
                <span className="building-id">{building.building_id}</span>
                <span className={`risk-badge ${riskClass}`}>
                  {building.risk_score}% RISK
                </span>
              </div>
              <div className="card-details">
                <span>{building.property_tag || building.declared_type}</span>
                <span>•</span>
                <span>{building.monthly_usage_kwh} kWh</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
