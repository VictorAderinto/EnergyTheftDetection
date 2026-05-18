import { useState, useEffect } from 'react';
import Map from './components/Map';
import Sidebar from './components/Sidebar';
import DetailPanel from './components/DetailPanel';
import './index.css';

function App() {
  const [buildings, setBuildings] = useState([]);
  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/buildings')
      .then(res => res.json())
      .then(data => {
        setBuildings(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch buildings:', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="app-container">
      <Sidebar 
        buildings={buildings} 
        selectedBuilding={selectedBuilding}
        onSelectBuilding={setSelectedBuilding} 
      />
      
      <div className="map-container">
        <Map 
          buildings={buildings} 
          selectedBuilding={selectedBuilding}
          onSelectBuilding={setSelectedBuilding} 
        />
        
        {selectedBuilding && (
          <DetailPanel 
            building={selectedBuilding} 
            onClose={() => setSelectedBuilding(null)} 
          />
        )}
      </div>
    </div>
  );
}

export default App;
