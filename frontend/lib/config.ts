/**
 * Application configuration
 * Uses environment variables with sensible defaults
 */

interface ApiEndpoints {
  stream: string
  query?: string
  alerts?: string
  statistics: string
  health: string
}

interface ApiConfig {
  base: string
  endpoints: ApiEndpoints
}

interface Config {
  api: {
    compliance: ApiConfig
    drift: ApiConfig
  }
  app: {
    name: string
    version: string
    environment: string
  }
  features: {
    driftDetection: boolean
    compliance: boolean
    auditLogs: boolean
  }
}

const complianceEndpoints = {
  stream: '/api/compliance/stream',
  query: '/api/compliance/query',
  statistics: '/api/compliance/statistics',
  health: '/health'
} as const

const driftEndpoints = {
  stream: '/api/drift/stream',
  alerts: '/api/drift/alerts',
  statistics: '/api/drift/statistics',
  health: '/health'
} as const

export const config: Config = {
  // API Endpoints
  api: {
    compliance: {
      base: process.env.NEXT_PUBLIC_COMPLIANCE_API_URL || 'http://localhost:5000',
      endpoints: complianceEndpoints
    },
    drift: {
      base: process.env.NEXT_PUBLIC_DRIFT_API_URL || 'http://localhost:5001',
      endpoints: driftEndpoints
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
  }
}

// Helper methods to build full URLs
export const getComplianceUrl = (endpoint: string): string => {
  return `${config.api.compliance.base}${config.api.compliance.endpoints[endpoint as keyof typeof complianceEndpoints]}`
}

export const getDriftUrl = (endpoint: string): string => {
  return `${config.api.drift.base}${config.api.drift.endpoints[endpoint as keyof typeof driftEndpoints]}`
}

export default config
