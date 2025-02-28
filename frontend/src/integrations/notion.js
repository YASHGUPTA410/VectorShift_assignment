// // notion.js

// import { useState, useEffect } from 'react';
// import {
//     Box,
//     Button,
//     CircularProgress
// } from '@mui/material';
// import axios from 'axios';

// export const NotionIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
//     const [isConnected, setIsConnected] = useState(false);
//     const [isConnecting, setIsConnecting] = useState(false);

//     // Function to open OAuth in a new window
//     const handleConnectClick = async () => {
//         try {
//             setIsConnecting(true);
//             const formData = new FormData();
//             formData.append('user_id', user);
//             formData.append('org_id', org);
//             const response = await axios.post(`http://localhost:8000/integrations/notion/authorize`, formData);
//             console.log(response);
//             const authURL = response?.data;

//             const newWindow = window.open(authURL, 'Notion Authorization', 'width=600, height=600');

//             // Polling for the window to close
//             const pollTimer = window.setInterval(() => {
//                 if (newWindow?.closed !== false) { 
//                     window.clearInterval(pollTimer);
//                     handleWindowClosed();
//                 }
//             }, 200);
//         } catch (e) {
//             setIsConnecting(false);
//             alert(e?.response?.data?.detail);
//         }
//     }

//     // Function to handle logic when the OAuth window closes
//     const handleWindowClosed = async () => {
//         try {
//             const formData = new FormData();
//             formData.append('user_id', user);
//             formData.append('org_id', org);
//             const response = await axios.post(`http://localhost:8000/integrations/notion/credentials`, formData);
//             const credentials = response.data; 
//             if (credentials) {
//                 setIsConnecting(false);
//                 setIsConnected(true);
//                 setIntegrationParams(prev => ({ ...prev, credentials: credentials, type: 'Notion' }));
//             }
//             setIsConnecting(false);
//         } catch (e) {
//             setIsConnecting(false);
//             alert(e?.response?.data?.detail);
//         }
//     }

//     useEffect(() => {
//         setIsConnected(integrationParams?.credentials ? true : false)
//     }, []);

//     return (
//         <>
//         <Box sx={{mt: 2}}>
//             Parameters
//             <Box display='flex' alignItems='center' justifyContent='center' sx={{mt: 2}}>
//                 <Button 
//                     variant='contained' 
//                     onClick={isConnected ? () => {} :handleConnectClick}
//                     color={isConnected ? 'success' : 'primary'}
//                     disabled={isConnecting}
//                     style={{
//                         pointerEvents: isConnected ? 'none' : 'auto',
//                         cursor: isConnected ? 'default' : 'pointer',
//                         opacity: isConnected ? 1 : undefined
//                     }}
//                 >
//                     {isConnected ? 'Notion Connected' : isConnecting ? <CircularProgress size={20} /> : 'Connect to Notion'}
//                 </Button>
//             </Box>
//         </Box>
//       </>
//     );
// }


// notion.js
import { useState, useEffect } from 'react';
import { Box, Button, CircularProgress } from '@mui/material';
import axios from 'axios';

// Helper: create form data from user and org
const createFormData = (user, org) => {
  const formData = new FormData();
  formData.append('user_id', user);
  formData.append('org_id', org);
  return formData;
};

// Helper: poll until the window closes, then call callback
const pollWindowClose = (newWindow, callback, interval = 200) => {
  const pollTimer = window.setInterval(() => {
    if (newWindow?.closed !== false) {
      window.clearInterval(pollTimer);
      callback();
    }
  }, interval);
};

export const NotionIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  // Initiates the OAuth flow
  const handleConnectClick = async () => {
    try {
      console.log('Starting Notion connection...');
      setIsConnecting(true);
      const response = await axios.post(
        'http://localhost:8000/integrations/notion/authorize',
        createFormData(user, org)
      );
      const authURL = response?.data;
      console.log('Received auth URL:', authURL);
      const newWindow = window.open(authURL, 'Notion Authorization', 'width=600, height=600');
      pollWindowClose(newWindow, handleWindowClosed);
    } catch (e) {
      console.error('Error in Notion connect:', e);
      setIsConnecting(false);
      alert(e?.response?.data?.detail);
    }
  };

  // Fetches credentials after the OAuth window closes
  const handleWindowClosed = async () => {
    try {
      console.log('Fetching Notion credentials...');
      const response = await axios.post(
        'http://localhost:8000/integrations/notion/credentials',
        createFormData(user, org)
      );
      const credentials = response.data;
      console.log('Received credentials:', credentials);
      if (credentials) {
        setIsConnected(true);
        setIntegrationParams(prev => ({ ...prev, credentials, type: 'Notion' }));
      }
    } catch (e) {
      console.error('Error fetching Notion credentials:', e);
      alert(e?.response?.data?.detail);
    } finally {
      setIsConnecting(false);
    }
  };

  useEffect(() => {
    setIsConnected(Boolean(integrationParams?.credentials));
  }, [integrationParams]);

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
          {isConnected ? 'Notion Connected' : isConnecting ? <CircularProgress size={20} /> : 'Connect to Notion'}
        </Button>
      </Box>
    </Box>
  );
};
