import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API方法
export const taskAPI = {
  // 获取任务列表
  getTasks(params = {}) {
    return api.get('/v1/tasks', { params })
  },
  
  // 获取任务详情
  getTask(taskId) {
    return api.get(`/v1/tasks/${taskId}`)
  },
  
  // 创建任务（上传文件）
  createTask(formData) {
    return api.post('/v1/tasks', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 更新任务状态
  updateTaskStatus(taskId, status) {
    return api.put(`/v1/tasks/${taskId}/status`, { status })
  },
  
  // 确认任务结果
  confirmTask(taskId, data) {
    return api.post(`/v1/tasks/${taskId}/confirm`, data)
  }
}

export default api
