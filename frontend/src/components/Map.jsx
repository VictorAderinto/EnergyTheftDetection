import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect } from 'react';

// Lagos coordinates
const LAGOS_CENTER = [6.5244, 3.3792];

// Component to handle map center changes
function MapController({ selectedBuilding }) {
  const map = useMap();
  
  useEffect(() => {
    if (selectedBuilding) {
      map.flyTo([selectedBuilding.lat, selectedBuilding.lng], 17, {
        duration: 1.5
      });
    }
  }, [selectedBuilding, map]);
  
  return null;
}

export default function Map({ buildings, selectedBuilding, onSelectBuilding }) {
  
  const getRiskColor = (score) => {
    if (score >= 75) return '#ef4444'; // Red for high risk
    if (score >= 40) return '#f59e0b'; // Orange/Yellow for medium
    return '#10b981'; // Green for normal
  };

  return (
    <MapContainer 
      center={LAGOS_CENTER} 
      zoom={14} 
      className="leaflet-container"
      zoomControl={false}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
      />
      
      <MapController selectedBuilding={selectedBuilding} />

      {buildings.map((building) => {
        const isSelected = selectedBuilding?.building_id === building.building_id;
        const color = getRiskColor(building.risk_score);
        
        return (
          <CircleMarker
            key={building.building_id}
            center={[building.lat, building.lng]}
            radius={isSelected ? 10 : 6}
            pathOptions={{
              fillColor: color,
              color: isSelected ? '#ffffff' : color,
              weight: isSelected ? 3 : 1,
              fillOpacity: 0.8
            }}
            eventHandlers={{
              click: () => onSelectBuilding(building)
            }}
          >
            <Popup>
              <strong>{building.building_id}</strong> - {building.property_tag || building.declared_type}<br />
              Risk Score: {building.risk_score}%
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
