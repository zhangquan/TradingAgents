import { api } from './index'
import { ConversationDetail, ChatMessage, ConversationSession, ConversationFullDetail } from './types'

export const conversationApi = {
  // Conversation Memory API
  async createConversationSession(data: {
    ticker: string
    analysis_date: string
    analysts: string[]
    research_depth?: number
    user_id?: string
  }) {
    const response = await api.post('/api/conversation/create', data)
    return response.data
  },

  async restoreConversationSession(sessionId: string): Promise<ConversationDetail> {
    const response = await api.get(`/api/conversation/restore/${sessionId}`)
    return response.data
  },

  async getConversationState(sessionId: string) {
    const response = await api.get(`/api/conversation/${sessionId}/state`)
    return response.data
  },

  async getConversationChatHistory(sessionId: string, limit: number = 100): Promise<ChatMessage[]> {
    const response = await api.get(`/api/conversation/${sessionId}/chat-history?limit=${limit}`)
    return response.data
  },

  async addChatMessage(sessionId: string, message: {
    role: string
    content: string
    agent_name?: string
    message_type?: string
    metadata?: any
  }) {
    const response = await api.post(`/api/conversation/${sessionId}/message`, message)
    return response.data
  },

  async listUserConversations(userId: string = 'demo_user', limit: number = 20): Promise<ConversationSession[]> {
    const response = await api.get(`/api/conversation/list?user_id=${userId}&limit=${limit}`)
    return response.data
  },

  async getConversationsByStockAndUser(userId: string, ticker: string, limit: number = 20): Promise<ConversationFullDetail[]> {
    const response = await api.get(`/api/conversation/by-stock?user_id=${userId}&ticker=${ticker}&limit=${limit}`)
    return response.data
  },

  async getNewestConversationByStock(userId: string, ticker: string): Promise<ConversationFullDetail | null> {
    const response = await api.get(`/api/conversation/newest-by-stock?user_id=${userId}&ticker=${ticker}`)
    return response.data
  },

  async updateAgentStatus(sessionId: string, agentName: string, status: string) {
    const response = await api.post(`/api/conversation/${sessionId}/agent-status`, {
      agent_name: agentName,
      status: status
    })
    return response.data
  },

  async updateReportSection(sessionId: string, sectionName: string, content: string) {
    const response = await api.post(`/api/conversation/${sessionId}/report`, {
      section_name: sectionName,
      content: content
    })
    return response.data
  },

  async finalizeConversation(sessionId: string, finalState?: any, processedSignal?: any) {
    const response = await api.post(`/api/conversation/${sessionId}/finalize`, {
      final_state: finalState,
      processed_signal: processedSignal
    })
    return response.data
  },

  async archiveConversation(sessionId: string) {
    const response = await api.delete(`/api/conversation/${sessionId}`)
    return response.data
  },
}
