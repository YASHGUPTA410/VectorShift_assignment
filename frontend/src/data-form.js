
import { useState } from 'react';
import { Box, TextField, Button } from '@mui/material';
import axios from 'axios';
import logger from './services/logger';

// Maps integration types to API endpoints
const endpointMapping = {
  Notion: 'notion',
  Airtable: 'airtable',
  HubSpot: 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
  const [loadedData, setLoadedData] = useState(null);
  const endpoint = endpointMapping[integrationType];

  // Load data from the integration endpoint
  const handleLoad = async () => {
    const startTime = performance.now();
    try {
      logger.logUserInteraction('DataForm', 'LOAD_DATA_CLICK', { integration_type: integrationType });
      const formData = new FormData();
      formData.append('credentials', JSON.stringify(credentials));
      
      const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
      const data = response.data;
      
      logger.logApiCall(
        'DataForm',
        `/integrations/${endpoint}/load`,
        'POST',
        startTime,
        response.status,
        { integration_type: integrationType, items_count: Array.isArray(data) ? data.length : 0 }
      );
      setLoadedData(data);
      logger.info('DataForm', 'DATA_LOAD_SUCCESS', {
        integration_type: integrationType,
        items_count: Array.isArray(data) ? data.length : 0,
        duration_ms: performance.now() - startTime
      });
    } catch (e) {
      logger.error('DataForm', 'DATA_LOAD_ERROR', e, { integration_type: integrationType, endpoint });
      alert(e?.response?.data?.detail);
    }
  };

  // Clear the loaded data
  const handleClear = () => {
    logger.logUserInteraction('DataForm', 'CLEAR_DATA', { integration_type: integrationType });
    setLoadedData(null);
  };

  return (
    
    <div>
              <div className="text-row">
                <p style={{marginBottom:"-10px"}}>Loaded Data</p>
                <TextField
                 placeholder="Loaded Data"
                  value={loadedData || ''}
                  sx={{ mt: 2 }}
                  InputLabelProps={{ shrink: true }}
                  disabled
                />
                </div>
                <div className="button button2">
                <Button onClick={handleLoad} sx={{ mt: 2 }} variant="contained">
                  Load Data
                </Button>
                <Button onClick={handleClear} sx={{ mt: 1 }} variant="contained">
                  Clear Data
                </Button>
                </div>
                </div>
             
       
  );
};

