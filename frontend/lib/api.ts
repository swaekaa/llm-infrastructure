import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

const COMPLIANCE_API_URL = process.env.NEXT_PUBLIC_COMPLIANCE_API_URL || 'http://localhost:5000'
const DRIFT_API_URL = process.env.NEXT_PUBLIC_DRIFT_API_URL || 'http://localhost:5001'

class APIClient {
  private complianceClient: AxiosInstance
  private driftClient: AxiosInstance

  constructor() {
    this.complianceClient = axios.create({
      baseURL: COMPLIANCE_API_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.driftClient = axios.create({
      baseURL: DRIFT_API_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }

  // Audit Logs (Compliance API)
  async getAuditStats() {
    const response = await this.complianceClient.get('/api/compliance/statistics')
    return response.data
  }

  async queryAuditLogs(filters: any) {
    const response = await this.complianceClient.post('/api/compliance/query', filters)
    return response.data
  }

  async exportAuditLogs(format: 'csv' | 'json' = 'csv', filters?: any) {
    const response = await this.complianceClient.post(
      '/api/compliance/export',
      {
        format,
        ...filters,
      },
      {
        responseType: format === 'csv' ? 'blob' : 'json',
      }
    )
    return response.data
  }

  // Drift Detection (Drift API)
  async getDriftStats() {
    const response = await this.driftClient.get('/api/drift/statistics')
    return response.data
  }

  async getDriftAlerts(params?: any) {
    const response = await this.driftClient.get('/api/drift/alerts', { params })
    return response.data
  }

  async resetDriftBaseline() {
    const response = await this.driftClient.post('/api/drift/reset-baseline')
    return response.data
  }

  // Health Check
  async healthCheck() {
    try {
      const [compliance, drift] = await Promise.all([
        this.complianceClient.get('/health'),
        this.driftClient.get('/health')
      ])
      return {
        compliance: compliance.data,
        drift: drift.data
      }
    } catch (error) {
      throw error
    }
  }

  // Generic request wrapper
  async request(config: AxiosRequestConfig) {
    try {
      const response = await this.complianceClient(config)
      return response.data
    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }
}

export const apiClient = new APIClient()
