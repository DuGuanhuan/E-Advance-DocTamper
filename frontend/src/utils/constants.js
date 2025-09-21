// 任务状态映射 - 高对比度配色方案
export const STATUS_MAP = {
  processing: {
    text: '处理中',
    color: '#1e40af',
    background: '#dbeafe',
    border: '#93c5fd',
    css_class: 'status-tag-processing'
  },
  pending_review: {
    text: '待核对',
    color: '#c2410c',
    background: '#fed7aa',
    border: '#fdba74',
    css_class: 'status-tag-pending'
  },
  confirmed_forgery: {
    text: '疑似伪造',
    color: '#b91c1c',
    background: '#fecaca',
    border: '#f87171',
    css_class: 'status-tag-forgery'
  },
  confirmed_safe: {
    text: '无风险',
    color: '#166534',
    background: '#bbf7d0',
    border: '#86efac',
    css_class: 'status-tag-safe'
  }
}

// 状态选项（用于筛选下拉框）
export const STATUS_OPTIONS = [
  { value: '', label: '所有状态' },
  { value: 'processing', label: '处理中' },
  { value: 'pending_review', label: '待核对' },
  { value: 'confirmed_forgery', label: '疑似伪造' },
  { value: 'confirmed_safe', label: '无风险' }
]

// 文件类型图标映射
export const FILE_TYPE_ICONS = {
  'image/jpeg': '🖼️',
  'image/png': '🖼️',
  'image/gif': '🖼️',
  'application/pdf': '📄',
  'default': '📄'
}

// 获取状态显示信息
export function getStatusInfo(status) {
  return STATUS_MAP[status] || {
    text: '未知状态',
    color_variable: 'var(--processing-color)',
    css_class: 'status-tag-processing'
  }
}

// 获取文件类型图标
export function getFileIcon(mimeType) {
  return FILE_TYPE_ICONS[mimeType] || FILE_TYPE_ICONS.default
}

// 格式化文件大小
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化日期时间
export function formatDateTime(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}