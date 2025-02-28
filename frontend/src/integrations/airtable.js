// airtable.js

import { useState, useEffect } from 'react';
import { Box, Button, CircularProgress } from '@mui/material';
import axios from 'axios';

export const AirtableIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
  // Local state to manage connection status
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  /**
   * Initiates the OAuth process by opening a new window
   * to handle Airtable authorization.
   */
  const handleConnectClick = async () => {
    try {
      console.log('Initiating Airtable connection...');
      setIsConnecting(true);

      // Create form data with user and organization info
      const formData = new FormData();
      formData.append('user_id', user);
      formData.append('org_id', org);

      // Request authorization URL from the server
      const response = await axios.post(
        'http://localhost:8000/integrations/airtable/authorize',
        formData
      );
      const authURL = response?.data;
      console.log('Received authorization URL:', authURL);

      // Open the authorization URL in a new window
      const newWindow = window.open(
        authURL,
        'Airtable Authorization',
        'width=600, height=600'
      );

      // Poll every 200ms to detect when the OAuth window is closed
      const pollTimer = window.setInterval(() => {
        if (newWindow?.closed !== false) {
          console.log('OAuth window closed. Proceeding to fetch credentials...');
          window.clearInterval(pollTimer);
          handleWindowClosed();
        }
      }, 200);
    } catch (e) {
      console.error('Error during authorization:', e);
      setIsConnecting(false);
      alert(e?.response?.data?.detail || 'Authorization failed');
    }
  };

  /**
   * Called when the OAuth window is closed.
   * This function fetches the Airtable credentials from the server.
   */
  const handleWindowClosed = async () => {
    try {
      console.log('Fetching Airtable credentials...');
      const formData = new FormData();
      formData.append('user_id', user);
      formData.append('org_id', org);

      const response = await axios.post(
        'http://localhost:8000/integrations/airtable/credentials',
        formData
      );
      const credentials = response.data;
      console.log('Received credentials:', credentials);

      // If credentials exist, update the connection state and integration parameters
      if (credentials) {
        setIsConnected(true);
        setIntegrationParams(prev => ({ ...prev, credentials, type: 'Airtable' }));
      }
    } catch (e) {
      console.error('Error fetching credentials:', e);
      alert(e?.response?.data?.detail || 'Failed to fetch credentials');
    } finally {
      setIsConnecting(false);
    }
  };

  // Check for existing credentials when the component mounts or integrationParams changes
  useEffect(() => {
    console.log('Checking initial connection status...');
    setIsConnected(!!integrationParams?.credentials);
  }, [integrationParams]);

  return (
    <Box sx={{ mt: 2 }}>
      <p>Parameters</p>
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        sx={{ mt: 2 }}
      >
        <Button
          variant="contained"
          onClick={isConnected ? undefined : handleConnectClick}
          color={isConnected ? 'success' : 'primary'}
          disabled={isConnecting}
          style={{
            pointerEvents: isConnected ? 'none' : 'auto',
            cursor: isConnected ? 'default' : 'pointer',
            opacity: isConnected ? 1 : undefined,
          }}
        >
          {isConnected ? (
            'Airtable Connected'
          ) : isConnecting ? (
            <CircularProgress size={20} />
          ) : (
            'Connect to Airtable'
          )}
        </Button>
      </Box>
    </Box>
  );
};
