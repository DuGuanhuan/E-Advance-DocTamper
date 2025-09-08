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
    // 允许通过 config.__silent 来静默错误提示
    const silent = error.config?.__silent === true
    if (!silent) {
      let message = error.response?.data?.detail || error.message || '请求失败'
      // 兼容 FastAPI/Pydantic 的 422 错误数组结构
      if (Array.isArray(message)) {
        const first = message[0]
        if (first && typeof first === 'object') {
          const loc = Array.isArray(first.loc) ? first.loc.join('.') : ''
          message = `${loc ? loc + ': ' : ''}${first.msg || '参数校验失败'}`
        } else {
          message = '参数校验失败'
        }
      } else if (typeof message === 'object') {
        message = message.msg || message.error || JSON.stringify(message)
      }
      ElMessage.error(String(message))
    }
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
  },
  
  // 标记任务为无风险
  markTaskSafe(taskId) {
    return api.post(`/v1/tasks/${taskId}/mark-safe`)
  },
  
  // 标记任务为违规/伪造
  markTaskViolation(taskId) {
    return api.post(`/v1/tasks/${taskId}/mark-violation`)
  }
}

// 案例库 API
export const caseAPI = {
  // 获取案例列表
  getCases(params = {}) {
    return api.get('/v1/cases', { params })
  },
  // 获取案例详情
  getCaseDetail(caseId, config = {}) {
    return api.get(`/v1/cases/${caseId}`, { ...config })
  },
  // 获取统计
  getStatistics() {
    return api.get('/v1/cases/statistics')
  },
  // 获取伪造类型
  getForgeryTypes() {
    return api.get('/v1/cases/forgery-types')
  }
}

export default api
