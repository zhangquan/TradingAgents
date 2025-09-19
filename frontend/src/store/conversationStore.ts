import { create } from 'zustand'
import { conversationApi } from '../api/conversation'
import { 
  ConversationDetail, 
  ChatMessage, 
  ConversationSession, 
  ConversationFullDetail 
} from '../api/types'

interface ConversationState {
  // State
  sessions: ConversationSession[]
  currentSession: ConversationDetail | null
  currentSessionId: string | null
  chatHistory: ChatMessage[]
  conversationsByStock: Record<string, ConversationFullDetail[]>
  isLoading: boolean
  error: string | null
  userId: string
  
  // Actions
  createSession: (data: {
    ticker: string
    analysis_date: string
    analysts: string[]
    research_depth?: number
    user_id?: string
  }) => Promise<{ session_id: string }>
  restoreSession: (sessionId: string) => Promise<void>
  getSessionState: (sessionId: string) => Promise<any>
  loadChatHistory: (sessionId: string, limit?: number) => Promise<void>
  addChatMessage: (sessionId: string, message: {
    role: string
    content: string
    agent_name?: string
    message_type?: string
    metadata?: any
  }) => Promise<void>
  loadUserSessions: (userId?: string, limit?: number) => Promise<void>
  getConversationsByStock: (userId: string, ticker: string, limit?: number) => Promise<void>
  updateAgentStatus: (sessionId: string, agentName: string, status: string) => Promise<void>
  updateReportSection: (sessionId: string, sectionName: string, content: string) => Promise<void>
  finalizeConversation: (sessionId: string, finalState?: any, processedSignal?: any) => Promise<void>
  archiveConversation: (sessionId: string) => Promise<void>
  
  // Real-time updates
  addMessageToHistory: (message: ChatMessage) => void
  updateSessionStatus: (sessionId: string, updates: Partial<ConversationDetail>) => void
  
  // Utilities
  setCurrentSession: (sessionId: string | null) => void
  setUserId: (userId: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  clearSessions: () => void
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  // Initial state
  sessions: [],
  currentSession: null,
  currentSessionId: null,
  chatHistory: [],
  conversationsByStock: {},
  isLoading: false,
  error: null,
  userId: 'demo_user',

  // Actions
  createSession: async (data) => {
    set({ isLoading: true, error: null })
    try {
      const response = await conversationApi.createConversationSession({
        ...data,
        user_id: data.user_id || get().userId
      })
      
      // Add to sessions list if response includes session info
      if (response.session_id) {
        await get().loadUserSessions()
      }
      
      set({ isLoading: false })
      return response
    } catch (error: any) {
      set({ error: error.message || 'Failed to create session', isLoading: false })
      throw error
    }
  },

  restoreSession: async (sessionId: string) => {
    set({ isLoading: true, error: null, currentSessionId: sessionId })
    try {
      const session = await conversationApi.restoreConversationSession(sessionId)
      set({ 
        currentSession: session,
        chatHistory: session.chat_history || [],
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to restore session', isLoading: false })
    }
  },

  getSessionState: async (sessionId: string) => {
    try {
      const state = await conversationApi.getConversationState(sessionId)
      return state
    } catch (error: any) {
      set({ error: error.message || 'Failed to get session state' })
      throw error
    }
  },

  loadChatHistory: async (sessionId: string, limit = 100) => {
    set({ isLoading: true, error: null })
    try {
      const history = await conversationApi.getConversationChatHistory(sessionId, limit)
      set({ chatHistory: history, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load chat history', isLoading: false })
    }
  },

  addChatMessage: async (sessionId: string, message) => {
    try {
      const response = await conversationApi.addChatMessage(sessionId, message)
      
      // Add to local chat history if current session
      if (sessionId === get().currentSessionId && response.message) {
        const { chatHistory } = get()
        set({ chatHistory: [...chatHistory, response.message] })
      }
      
      return response
    } catch (error: any) {
      set({ error: error.message || 'Failed to add chat message' })
      throw error
    }
  },

  loadUserSessions: async (userId, limit = 20) => {
    const currentUserId = userId || get().userId
    set({ isLoading: true, error: null })
    try {
      const sessions = await conversationApi.listUserConversations(currentUserId, limit)
      set({ sessions, isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load user sessions', isLoading: false })
    }
  },

  getConversationsByStock: async (userId: string, ticker: string, limit = 20) => {
    set({ isLoading: true, error: null })
    try {
      const conversations = await conversationApi.getConversationsByStockAndUser(userId, ticker, limit)
      set({ 
        conversationsByStock: { 
          ...get().conversationsByStock, 
          [ticker]: conversations 
        },
        isLoading: false 
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to get conversations by stock', isLoading: false })
    }
  },

  updateAgentStatus: async (sessionId: string, agentName: string, status: string) => {
    try {
      await conversationApi.updateAgentStatus(sessionId, agentName, status)
      
      // Update current session if it matches
      if (sessionId === get().currentSessionId && get().currentSession) {
        const { currentSession } = get()
        set({ 
          currentSession: {
            ...currentSession,
            agent_status: {
              ...currentSession.agent_status,
              [agentName]: status
            }
          }
        })
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to update agent status' })
      throw error
    }
  },

  updateReportSection: async (sessionId: string, sectionName: string, content: string) => {
    try {
      await conversationApi.updateReportSection(sessionId, sectionName, content)
      
      // Update current session if it matches
      if (sessionId === get().currentSessionId && get().currentSession) {
        const { currentSession } = get()
        set({ 
          currentSession: {
            ...currentSession,
            reports: {
              ...currentSession.reports,
              sections: {
                ...currentSession.reports.sections,
                [sectionName]: content
              }
            }
          }
        })
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to update report section' })
      throw error
    }
  },

  finalizeConversation: async (sessionId: string, finalState?, processedSignal?) => {
    set({ isLoading: true, error: null })
    try {
      await conversationApi.finalizeConversation(sessionId, finalState, processedSignal)
      
      // Update current session if it matches
      if (sessionId === get().currentSessionId && get().currentSession) {
        const { currentSession } = get()
        set({ 
          currentSession: {
            ...currentSession,
            final_results: {
              final_state: finalState,
              processed_signal: processedSignal
            }
          }
        })
      }
      
      set({ isLoading: false })
    } catch (error: any) {
      set({ error: error.message || 'Failed to finalize conversation', isLoading: false })
      throw error
    }
  },

  archiveConversation: async (sessionId: string) => {
    set({ isLoading: true, error: null })
    try {
      await conversationApi.archiveConversation(sessionId)
      
      // Remove from sessions list
      const { sessions } = get()
      set({ 
        sessions: sessions.filter(session => session.session_id !== sessionId),
        isLoading: false 
      })
      
      // Clear current session if it matches
      if (sessionId === get().currentSessionId) {
        set({ currentSession: null, currentSessionId: null, chatHistory: [] })
      }
    } catch (error: any) {
      set({ error: error.message || 'Failed to archive conversation', isLoading: false })
      throw error
    }
  },

  // Real-time updates
  addMessageToHistory: (message: ChatMessage) => {
    const { chatHistory, currentSessionId } = get()
    if (message.session_id === currentSessionId) {
      set({ chatHistory: [...chatHistory, message] })
    }
  },

  updateSessionStatus: (sessionId: string, updates: Partial<ConversationDetail>) => {
    if (sessionId === get().currentSessionId && get().currentSession) {
      const { currentSession } = get()
      set({ currentSession: { ...currentSession, ...updates } })
    }
  },

  // Utilities
  setCurrentSession: (sessionId: string | null) => set({ currentSessionId: sessionId }),
  setUserId: (userId: string) => set({ userId }),
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  clearError: () => set({ error: null }),
  clearSessions: () => set({ 
    sessions: [], 
    currentSession: null, 
    currentSessionId: null, 
    chatHistory: [],
    conversationsByStock: {}
  }),
}))
