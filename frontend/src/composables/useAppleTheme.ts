import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'

// Apple Design Language 主题配置，适用于 Ant Design Vue 4.x
export const appleTheme: ThemeConfig = {
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
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif",
    fontSize: 17,
    borderRadius: 11,
    borderRadiusLG: 18,
    borderRadiusSM: 8,
    controlHeight: 44,
    colorLink: '#0066cc',
  },
  components: {
    Button: {
      borderRadius: 9999,
      controlHeight: 44,
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
    Menu: {},
  },
}
