import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './index.css'

const appleTheme = {
  token: {
    colorPrimary: '#0066cc',
    colorInfo: '#0066cc',
    colorSuccess: '#30d158',
    colorWarning: '#ff9f0a',
    colorError: '#ff453a',
    colorText: '#1d1d1f',
    colorTextSecondary: '#7a7a7a',
    colorBgContainer: '#ffffff',
    colorBgLayout: '#f5f5f7',
    colorBorder: '#e0e0e0',
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif",
    fontSize: 17,
    borderRadius: 11,
    borderRadiusLG: 18,
    borderRadiusSM: 8,
    controlHeight: 44,
    colorLink: '#0066cc',
  },
  components: {
    Button: {
      primaryShadow: 'none',
      defaultShadow: 'none',
      borderRadius: 9999,
      controlHeight: 44,
      paddingInline: 22,
    },
    Card: {
      borderRadiusLG: 18,
    },
    Input: {
      borderRadius: 9999,
      controlHeight: 44,
    },
    Select: {
      borderRadius: 9999,
    },
    Tag: {
      borderRadiusSM: 9999,
    },
    Menu: {
      itemColor: '#7a7a7a',
      itemSelectedColor: '#1d1d1f',
      itemHoverColor: '#1d1d1f',
      inkBarColor: '#0066cc',
    },
  },
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN} theme={appleTheme}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <App />
      </BrowserRouter>
    </ConfigProvider>
  </React.StrictMode>,
)
