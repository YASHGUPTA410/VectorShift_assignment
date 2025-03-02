
import { useState, useEffect } from 'react';
import { Box, Autocomplete, TextField } from '@mui/material';
import { AirtableIntegration } from './integrations/airtable';
import { NotionIntegration } from './integrations/notion';
import { HubSpotIntegration } from './integrations/hubspot';
import { DataForm } from './data-form';
import logger from './services/logger';

const integrationMapping = {
  Notion: NotionIntegration,
  Airtable: AirtableIntegration,
  HubSpot: HubSpotIntegration,
};

export const IntegrationForm = () => {
  const [integrationParams, setIntegrationParams] = useState({});
  const [user, setUser] = useState('');
  const [org, setOrg] = useState('');
  const [currType, setCurrType] = useState(null);
  const CurrIntegration = currType ? integrationMapping[currType] : null;

  // Log component mount and unmount
  useEffect(() => {
    logger.info('IntegrationForm', 'COMPONENT_MOUNT');
    return () => logger.info('IntegrationForm', 'COMPONENT_UNMOUNT');
  }, []);

  // Log changes to integration type, user, and org
  useEffect(() => {
    if (currType) {
      logger.info('IntegrationForm', 'INTEGRATION_TYPE_CHANGED', { type: currType, user_id: user, org_id: org });
    }
  }, [currType, user, org]);

  // Log updates to integration parameters
  useEffect(() => {
    if (integrationParams.type) {
      logger.info('IntegrationForm', 'INTEGRATION_PARAMS_UPDATED', { type: integrationParams.type, has_credentials: Boolean(integrationParams.credentials) });
    }
  }, [integrationParams]);

  const handleUserChange = (e) => {
    const newUser = e.target.value;
    logger.logUserInteraction('IntegrationForm', 'USER_CHANGE', { previous: user, new: newUser });
    setUser(newUser);
  };

  const handleOrgChange = (e) => {
    const newOrg = e.target.value;
    logger.logUserInteraction('IntegrationForm', 'ORG_CHANGE', { previous: org, new: newOrg });
    setOrg(newOrg);
  };

  const handleIntegrationTypeChange = (e, value) => {
    logger.logUserInteraction('IntegrationForm', 'INTEGRATION_TYPE_SELECT', { selected_type: value, user_id: user, org_id: org });
    setCurrType(value);
  };

  return (
    <div className="layout">
      <div className="content">
        <div className="page">
          <div className="bg_circle-wrapper">
            <div className="circle circle-one" />
            <div className="circle circle-two" />
            <div className="circle circle-three" />
          </div>
          <div className="page-content">
            <div className="center-div">
              <div className="text-row">
                <p>User</p>
                <TextField placeholder="Enter user" value={user} onChange={handleUserChange} />
              </div>
              <div className="text-row">
                <p>Organisation</p>
                <TextField placeholder="Enter Organisation" value={org} onChange={handleOrgChange} />
              </div>
              <div className="text-row1">
                <p>Integration Type</p>
                <Autocomplete
                  options={Object.keys(integrationMapping)}
                  renderInput={(params) => <TextField {...params} placeholder="Select Integration Type" />}
                  onChange={handleIntegrationTypeChange}
                />
              </div>
              {currType && (
                <div className="button ">
                  <CurrIntegration user={user} org={org} integrationParams={integrationParams} setIntegrationParams={setIntegrationParams} />
                </div>
              )}
              {integrationParams?.credentials && (
                <DataForm integrationType={integrationParams.type} credentials={integrationParams.credentials} />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
