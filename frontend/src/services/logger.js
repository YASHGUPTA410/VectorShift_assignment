
// logger.js
const LOG_LEVELS = {
    INFO: 'INFO',
    ERROR: 'ERROR',
    DEBUG: 'DEBUG',
    WARN: 'WARN'
  };
  
  class Logger {
    constructor() {
      // Logger class for capturing metadata and logging events
      this.metadata = {
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: this.getTimestamp()
      };
    }
  
    // Returns the current timestamp as an ISO string
    getTimestamp() {
      return new Date().toISOString();
    }
  
    formatLogEntry(level, component, action, details = {}) {
      return {
        timestamp: this.getTimestamp(),
        level,
        component,
        action,
        details: {
          ...details,
          url: window.location.href
        },
        metadata: this.metadata
      };
    }
  
    info(component, action, details = {}) {
      const logEntry = this.formatLogEntry(LOG_LEVELS.INFO, component, action, details);
      console.info(`[${logEntry.timestamp}] ${component} - ${action}:`, details);
      this.sendToServer(logEntry);
    }
  
    error(component, action, error, details = {}) {
      const logEntry = this.formatLogEntry(LOG_LEVELS.ERROR, component, action, {
        ...details,
        error: {
          message: error.message,
          stack: error.stack,
          name: error.name
        }
      });
      console.error(`[${logEntry.timestamp}] ${component} - ${action}:`, error, details);
      this.sendToServer(logEntry);
    }
  
    debug(component, action, details = {}) {
      const logEntry = this.formatLogEntry(LOG_LEVELS.DEBUG, component, action, details);
      console.debug(`[${logEntry.timestamp}] ${component} - ${action}:`, details);
      this.sendToServer(logEntry);
    }
  
    warn(component, action, details = {}) {
      const logEntry = this.formatLogEntry(LOG_LEVELS.WARN, component, action, details);
      console.warn(`[${logEntry.timestamp}] ${component} - ${action}:`, details);
      this.sendToServer(logEntry);
    }
  
    // Utility logging functions for performance, API calls, and user interactions
    logPerformance(component, action, startTime, details = {}) {
      const duration = performance.now() - startTime;
      this.info(component, action, { ...details, duration_ms: duration });
    }
  
    logApiCall(component, endpoint, method, startTime, status, details = {}) {
      const duration = performance.now() - startTime;
      this.info(component, 'API_CALL', {
        endpoint,
        method,
        status,
        duration_ms: duration,
        ...details
      });
    }
  
    logUserInteraction(component, action, details = {}) {
      this.info(component, action, { ...details, timestamp: this.getTimestamp() });
    }
  
    // Sends log entry to server in production mode
    async sendToServer(logEntry) {
      if (process.env.NODE_ENV === 'development') return;
      try {
        await fetch('http://localhost:8000/logs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(logEntry)
        });
      } catch (error) {
        console.error('Failed to send log to server:', error);
      }
    }
  }
  
  // Singleton instance of Logger
  const logger = new Logger();
  export default logger;
  
