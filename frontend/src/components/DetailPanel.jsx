import { useState, useEffect } from 'react';
import { X, Sparkles, AlertTriangle } from 'lucide-react';

export default function DetailPanel({ building, onClose }) {
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setExplanation('');
    
    // Fetch AI explanation from backend
    fetch(`/api/analyze-building/${building.building_id}`, {
      method: 'POST'
    })
      .then(async res => {
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "Error connecting to Gemini API.");
        }
        return data;
      })
      .then(data => {
        setExplanation(data.explanation);
        setLoading(false);
      })
      .catch(err => {
        setExplanation(err.message);
        setLoading(false);
      });
  }, [building.building_id]);

  return (
    <div className="detail-panel glass-panel">
      <div className="detail-header">
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Building {building.building_id}</h2>
        <button className="close-btn" onClick={onClose}>
          <X size={20} />
        </button>
      </div>
      
      <div className="detail-body">
        <div className="data-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
          <div className="data-item">
            <div className="data-label">Property Tag</div>
            <div className="data-value">{building.property_tag || building.declared_type}</div>
          </div>
          <div className="data-item">
            <div className="data-label">Risk Score</div>
            <div className="data-value" style={{ color: building.risk_score > 75 ? 'var(--risk-high)' : 'var(--text-primary)' }}>
              {building.risk_score}%
            </div>
          </div>
          <div className="data-item">
            <div className="data-label">Size Category</div>
            <div className="data-value">{building.building_size_category || 'N/A'}</div>
          </div>
          <div className="data-item">
            <div className="data-label">Neighborhood</div>
            <div className="data-value">{building.neighborhood_type || 'N/A'}</div>
          </div>
          <div className="data-item">
            <div className="data-label">Monthly Usage</div>
            <div className="data-value">{building.monthly_usage_kwh} kWh</div>
          </div>
          <div className="data-item">
            <div className="data-label">Load Profile</div>
            <div className="data-value">{building.load_type || 'N/A'}</div>
          </div>
          <div className="data-item">
            <div className="data-label">Blackout Freq.</div>
            <div className="data-value">{building.blackout_frequency ? `${building.blackout_frequency} / mo` : 'N/A'}</div>
          </div>
          <div className="data-item">
            <div className="data-label">Avg Blackout Dur.</div>
            <div className="data-value">{building.average_blackout_duration_hrs ? `${building.average_blackout_duration_hrs} hrs` : 'N/A'}</div>
          </div>
        </div>
        
        <div className="ai-reasoning">
          <div className="ai-header">
            <Sparkles size={16} /> Gemini Reasoning Layer
          </div>
          <div className="ai-content">
            {loading ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div className="loading-spinner"></div>
                <span style={{ color: 'var(--text-muted)' }}>Analyzing usage patterns...</span>
              </div>
            ) : (
              <p>{explanation}</p>
            )}
          </div>
        </div>
        
        {building.risk_score > 75 && (
          <div style={{ marginTop: '20px', padding: '16px', background: 'var(--risk-high-bg)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '12px', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <AlertTriangle color="var(--risk-high)" size={20} style={{ flexShrink: 0 }} />
            <div>
              <div style={{ color: 'var(--risk-high)', fontWeight: 600, fontSize: '0.875rem', marginBottom: '4px' }}>Recommended Action</div>
              <div style={{ fontSize: '0.875rem', color: 'rgba(255,255,255,0.8)' }}>
                Flagged for physical inspection. Usage deviates significantly from expected baseline for property size.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
