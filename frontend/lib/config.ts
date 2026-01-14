/**
 * Application configuration
 * Uses environment variables with sensible defaults
 */

export const config = {
  // API Endpoints
  api: {
    compliance: {
      base: process.env.NEXT_PUBLIC_COMPLIANCE_API_URL || 'http://localhost:5000',
      endpoints: {
        stream: '/api/compliance/stream',
        query: '/api/compliance/query',
        statistics: '/api/compliance/statistics',
        health: '/health'
      }
    },
    drift: {
      base: process.env.NEXT_PUBLIC_DRIFT_API_URL || 'http://localhost:5001',
      endpoints: {
        stream: '/api/drift/stream',
        alerts: '/api/drift/alerts',
        statistics: '/api/drift/statistics',
        health: '/health'
      }
    }
  },

  // Application Settings
  app: {
    name: process.env.NEXT_PUBLIC_APP_NAME || 'LLM Infrastructure',
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
    environment: process.env.NEXT_PUBLIC_ENVIRONMENT || 'development'
  },

  // Feature Flags
  features: {
    driftDetection: process.env.NEXT_PUBLIC_ENABLE_DRIFT_DETECTION !== 'false',
    compliance: process.env.NEXT_PUBLIC_ENABLE_COMPLIANCE !== 'false',
    auditLogs: process.env.NEXT_PUBLIC_ENABLE_AUDIT_LOGS !== 'false'
  },

  // Helper methods to build full URLs
  getComplianceUrl: (endpoint: keyof typeof config.api.compliance.endpoints) => {
    return `${config.api.compliance.base}${config.api.compliance.endpoints[endpoint]}`
  },

  getDriftUrl: (endpoint: keyof typeof config.api.drift.endpoints) => {
    return `${config.api.drift.base}${config.api.drift.endpoints[endpoint]}`
  }
}

export default config
