import axios from 'axios'
import { message } from 'ant-design-vue'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

function showError(msg: string) {
  message.error(msg)
}

// 响应拦截器：统一错误处理，避免各页面卡在 loading 状态
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      showError('请求超时，请检查网络后重试')
    } else if (!error.response) {
      showError('无法连接到服务器，请确认后端已启动')
    } else {
      const status = error.response.status
      const detail = error.response.data?.detail
      if (status === 500) {
        showError(detail || '服务器内部错误，请稍后重试')
      } else if (status === 404) {
        showError(detail || '请求的资源不存在')
      } else if (status === 400) {
        showError(detail || '请求参数有误')
      } else {
        showError(detail || `请求失败 (${status})`)
      }
    }
    return Promise.reject(error)
  },
)

export default client
