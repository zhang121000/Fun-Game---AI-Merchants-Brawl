import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import Header from './components/layout/Header'
import Home from './pages/Home'
import ProductDetail from './pages/ProductDetail'
import AnalyticsBoard from './pages/AnalyticsBoard'
import AdminDashboard from './pages/AdminDashboard'

const { Content } = Layout

export default function App() {
  return (
    <Layout style={{ minHeight: '100vh', background: '#ffffff' }}>
      <Header />
      <Content style={{ padding: '0 48px', background: '#ffffff' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/admin/marketing" element={<Navigate to="/admin" replace />} />
          <Route path="/admin/analytics" element={<AnalyticsBoard />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Routes>
      </Content>
    </Layout>
  )
}
