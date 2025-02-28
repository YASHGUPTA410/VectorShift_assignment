# VectorShift Unified Integrations API

This project provides a seamless way to connect with and retrieve data from popular services like HubSpot, Notion, and Airtable using OAuth 2.0. It leverages a modern, decoupled architecture with a FastAPI backend and a React-powered frontend, ensuring a robust and user-friendly experience.

## Project Overview

The architecture is designed for clarity and maintainability:
```

├── backend/
│   ├── integrations/        # Service-specific OAuth and data retrieval logic
│   │   ├── airtable.py
│   │   ├── notion.py
│   │   ├── hubspot.py
│   │   └── integration_item.py # Base class for integrations
│   ├── routes/              # API endpoint definitions
│   │   └── logs.py          # Centralized logging route
│   ├── config.py            # Application configuration
│   ├── logger.py            # Custom logging setup
│   ├── main.py              # FastAPI application entry point
│   ├── redis_client.py      # Redis interaction layer
│   └── requirements.txt     # Backend dependencies
└── frontend/
├── public/             # Static assets
└── src/                # React application source
├── integrations/    # UI components for each integration
│   ├── airtable.js
│   ├── notion.js
│   └── hubspot.js
├── services/        # Reusable utility functions
│   └── logger.js     # Frontend logging service
├── App.js             # Root component
├── data-form.js        # Component for displaying and submitting data
└── integration-form.js # Component for selecting integrations
```


## Getting Started

### Backend Setup

1.  **Environment Setup:**
    ```bash
    cd backend
    python3 -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

2.  **Redis:** Ensure Redis is running:
    ```bash
    redis-server
    ```

3.  **Launch the API:**
    ```bash
    uvicorn main:app --reload
    ```
    (Accessible at `http://localhost:8000`)

### Frontend Setup

1.  **Dependencies:**
    ```bash
    cd frontend
    npm install
    ```

2.  **Start Development Server:**
    ```bash
    npm start
    ```
    (Accessible at `http://localhost:3000`)

## Key Features

* **Simplified OAuth:** Streamlined OAuth 2.0 flows for HubSpot, Notion, and Airtable.
* **Unified Logging:** Comprehensive logging across both frontend and backend for easy debugging and monitoring.
* **State Management:** Redis utilized for secure and efficient OAuth state handling.
* **Robust Error Handling:** Proactive error management at both the client and server levels.
* **Performance Monitoring:** Built-in mechanisms for API call tracking.
* **User Activity Logging:** Detailed logs of user interactions.

## API Exploration

The API documentation is available at `http://localhost:8000/docs` when the backend is running.

### Core API Endpoints

* `POST /integrations/{service}/authorize`: Initiate the OAuth authentication process.
* `GET /integrations/{service}/oauth2callback`: Handle the OAuth callback.
* `POST /integrations/{service}/credentials`: Retrieve stored credentials.
* `POST /integrations/{service}/load`: Fetch data from the connected service.

## Logging Practices

* **Backend:** Logs are organized in `backend/logs/` with separate files for application, errors, and integration-specific logs.
* **Frontend:** Development logs are visible in the browser console. Production logs are forwarded to the backend.

## Error Prevention & Management

* **Frontend:** Error boundaries and Axios interceptors for robust error handling.
* **Backend:** Exception handlers and detailed log entries.
* **OAuth:** State verification and token management safeguards.

## Security Considerations

* CORS configuration to control cross-origin requests.
* OAuth state token validation.
* Redis for secure token storage with expiration.
* Environment variable configuration to protect sensitive data.

## License

This project is released under the MIT License. Refer to the `LICENSE` file for full details.



