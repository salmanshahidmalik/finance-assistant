import axios from 'axios'

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export const createApi = (userId: string) => {
  return axios.create({
    baseURL: BASE_URL,
    headers: {
      'x-user-id': userId,
      'Content-Type': 'application/json',
    },
  })
}

export const sendMessage = async (userId: string, message: string, imageData?: string) => {
  const api = createApi(userId)
  const response = await api.post('/chat/message', {
    message,
    image_data: imageData || null,
  })
  return response.data
}

export const getChatHistory = async (userId: string) => {
  const api = createApi(userId)
  const response = await api.get('/chat/history')
  return response.data
}

export const uploadCSV = async (userId: string, file: File) => {
  const api = createApi(userId)
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/upload/csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export const getBudgets = async (userId: string) => {
  const api = createApi(userId)
  const response = await api.get('/budget/')
  return response.data
}

export const createBudget = async (userId: string, category: string, amount: number) => {
  const api = createApi(userId)
  const response = await api.post('/budget/', { category, amount })
  return response.data
}