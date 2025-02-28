// // hubspot.js

// import { useState, useEffect } from 'react';
// import {
//     Box,
//     Button,
//     CircularProgress
// } from '@mui/material';
// import axios from 'axios';
// import logger from '../services/logger';

// export const HubSpotIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
//     const [isConnected, setIsConnected] = useState(false);
//     const [isConnecting, setIsConnecting] = useState(false);

//     // Function to open OAuth in a new window
//     const handleConnectClick = async () => {
//         const startTime = performance.now();
//         try {
//             logger.logUserInteraction('HubSpotIntegration', 'CONNECT_CLICK', {
//                 user_id: user,
//                 org_id: org
//             });

//             setIsConnecting(true);
//             const formData = new FormData();
//             formData.append('user_id', user);
//             formData.append('org_id', org);

//             const response = await axios.post(`http://localhost:8000/integrations/hubspot/authorize`, formData);
//             const authURL = response?.data;

//             logger.logApiCall(
//                 'HubSpotIntegration',
//                 '/integrations/hubspot/authorize',
//                 'POST',
//                 startTime,
//                 response.status,
//                 { user_id: user, org_id: org }
//             );

//             const newWindow = window.open(authURL, 'HubSpot Authorization', 'width=600, height=600');
//             logger.info('HubSpotIntegration', 'OAUTH_WINDOW_OPENED', {
//                 auth_url: authURL
//             });

//             // Polling for the window to close
//             const pollTimer = window.setInterval(() => {
//                 if (newWindow?.closed !== false) { 
//                     window.clearInterval(pollTimer);
//                     handleWindowClosed();
//                 }
//             }, 200);
//         } catch (e) {
//             logger.error('HubSpotIntegration', 'CONNECT_ERROR', e, {
//                 user_id: user,
//                 org_id: org
//             });
//             setIsConnecting(false);
//             alert(e?.response?.data?.detail);
//         }
//     }

//     // Function to handle logic when the OAuth window closes
//     const handleWindowClosed = async () => {
//         const startTime = performance.now();
//         try {
//             logger.info('HubSpotIntegration', 'OAUTH_WINDOW_CLOSED');

//             const formData = new FormData();
//             formData.append('user_id', user);
//             formData.append('org_id', org);
//             const response = await axios.post(`http://localhost:8000/integrations/hubspot/credentials`, formData);
//             const credentials = response.data;

//             logger.logApiCall(
//                 'HubSpotIntegration',
//                 '/integrations/hubspot/credentials',
//                 'POST',
//                 startTime,
//                 response.status,
//                 { user_id: user, org_id: org }
//             );

//             if (credentials) {
//                 setIsConnecting(false);
//                 setIsConnected(true);
//                 setIntegrationParams(prev => ({ ...prev, credentials: credentials, type: 'HubSpot' }));
//                 logger.info('HubSpotIntegration', 'CONNECTION_SUCCESS', {
//                     user_id: user,
//                     org_id: org
//                 });
//             }
//             setIsConnecting(false);
//         } catch (e) {
//             logger.error('HubSpotIntegration', 'CREDENTIALS_ERROR', e, {
//                 user_id: user,
//                 org_id: org
//             });
//             setIsConnecting(false);
//             alert(e?.response?.data?.detail);
//         }
//     }

//     useEffect(() => {
//         const hasCredentials = Boolean(integrationParams?.credentials);
//         setIsConnected(hasCredentials);
        
//         if (hasCredentials) {
//             logger.debug('HubSpotIntegration', 'CREDENTIALS_LOADED', {
//                 user_id: user,
//                 org_id: org
//             });
//         }
//     }, [integrationParams, user, org]);

//     return (
//         <>
//         <Box sx={{mt: 2}}>
//             Parameters
//             <Box display='flex' alignItems='center' justifyContent='center' sx={{mt: 2}}>
//                 <Button 
//                     variant='contained' 
//                     onClick={isConnected ? () => {} : handleConnectClick}
//                     color={isConnected ? 'success' : 'primary'}
//                     disabled={isConnecting}
//                     style={{
//                         pointerEvents: isConnected ? 'none' : 'auto',
//                         cursor: isConnected ? 'default' : 'pointer',
//                         opacity: isConnected ? 1 : undefined
//                     }}
//                 >
//                     {isConnected ? 'HubSpot Connected' : isConnecting ? <CircularProgress size={20} /> : 'Connect to HubSpot'}
//                 </Button>
//             </Box>
//         </Box>
//       </>
//     );
// }

// hubspot.js
import { useState, useEffect } from 'react';
import { Box, Button, CircularProgress } from '@mui/material';
import axios from 'axios';
import logger from '../services/logger';

// Helper to create form data
const createFormData = (user, org) => {
  const formData = new FormData();
  formData.append('user_id', user);
  formData.append('org_id', org);
  return formData;
};

// Helper to poll for window close event
const pollWindowClose = (newWindow, callback, interval = 200) => {
  const pollTimer = window.setInterval(() => {
    if (newWindow?.closed !== false) {
      window.clearInterval(pollTimer);
      callback();
    }
  }, interval);
};

export const HubSpotIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  // Initiates the OAuth process and opens the authorization window
  const handleConnectClick = async () => {
    const startTime = performance.now();
    try {
      logger.logUserInteraction('HubSpotIntegration', 'CONNECT_CLICK', { user_id: user, org_id: org });
      setIsConnecting(true);
      const response = await axios.post(
        'http://localhost:8000/integrations/hubspot/authorize',
        createFormData(user, org)
      );
      const authURL = response?.data;
      logger.logApiCall('HubSpotIntegration', '/integrations/hubspot/authorize', 'POST', startTime, response.status, { user_id: user, org_id: org });
      const newWindow = window.open(authURL, 'HubSpot Authorization', 'width=600, height=600');
      logger.info('HubSpotIntegration', 'OAUTH_WINDOW_OPENED', { auth_url: authURL });
      pollWindowClose(newWindow, handleWindowClosed);
    } catch (e) {
      logger.error('HubSpotIntegration', 'CONNECT_ERROR', e, { user_id: user, org_id: org });
      setIsConnecting(false);
      alert(e?.response?.data?.detail);
    }
  };

  // Fetches credentials once the OAuth window is closed
  const handleWindowClosed = async () => {
    const startTime = performance.now();
    try {
      logger.info('HubSpotIntegration', 'OAUTH_WINDOW_CLOSED');
      const response = await axios.post(
        'http://localhost:8000/integrations/hubspot/credentials',
        createFormData(user, org)
      );
      const credentials = response.data;
      logger.logApiCall('HubSpotIntegration', '/integrations/hubspot/credentials', 'POST', startTime, response.status, { user_id: user, org_id: org });
      if (credentials) {
        setIsConnected(true);
        setIntegrationParams(prev => ({ ...prev, credentials, type: 'HubSpot' }));
        logger.info('HubSpotIntegration', 'CONNECTION_SUCCESS', { user_id: user, org_id: org });
      }
    } catch (e) {
      logger.error('HubSpotIntegration', 'CREDENTIALS_ERROR', e, { user_id: user, org_id: org });
      alert(e?.response?.data?.detail);
    } finally {
      setIsConnecting(false);
    }
  };

  useEffect(() => {
    const hasCredentials = Boolean(integrationParams?.credentials);
    setIsConnected(hasCredentials);
    if (hasCredentials) {
      logger.debug('HubSpotIntegration', 'CREDENTIALS_LOADED', { user_id: user, org_id: org });
    }
  }, [integrationParams, user, org]);

  return (
    <Box sx={{ mt: 2 }}>
      <p>Parameters</p>
      <Box display="flex" alignItems="center" justifyContent="center" sx={{ mt: 2 }}>
        <Button
          variant="contained"
          onClick={isConnected ? undefined : handleConnectClick}
          color={isConnected ? 'success' : 'primary'}
          disabled={isConnecting}
          style={{
            pointerEvents: isConnected ? 'none' : 'auto',
            cursor: isConnected ? 'default' : 'pointer',
            opacity: isConnected ? 1 : undefined
          }}
        >
          {isConnected ? 'HubSpot Connected' : isConnecting ? <CircularProgress size={20} /> : 'Connect to HubSpot'}
        </Button>
      </Box>
    </Box>
  );
};
