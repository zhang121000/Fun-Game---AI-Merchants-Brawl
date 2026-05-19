import { useLocation, Link } from 'react-router-dom'

export default function Header() {
  const location = useLocation()

  const navLinks = [
    { path: '/', label: '产品总览' },
    { path: '/admin', label: 'AI 竞争控制台' },
    { path: '/admin/analytics', label: '数据看板' },
  ]

  return (
    <>
      {/* Global Nav — 纯黑顶栏 44px */}
      <nav style={{
        height: 44, background: '#000000', display: 'flex',
        alignItems: 'center', padding: '0 48px', gap: 24,
        position: 'sticky', top: 0, zIndex: 1000,
      }}>
        <Link to="/" style={{
          fontSize: 18, fontWeight: 600, color: '#f5f5f7',
          letterSpacing: '-0.01em', marginRight: 32, whiteSpace: 'nowrap',
        }}>
          AI 健康生活馆
        </Link>
        <div style={{ display: 'flex', gap: 24, flex: 1 }}>
          {navLinks.map(link => (
            <Link
              key={link.path}
              to={link.path}
              style={{
                fontSize: 12, color: location.pathname === link.path ? '#ffffff' : '#a1a1a6',
                fontWeight: 400, letterSpacing: '-0.01em',
                transition: 'color 0.2s',
              }}
            >
              {link.label}
            </Link>
          ))}
        </div>
        <span style={{ fontSize: 12, color: '#7a7a7a' }}>商家后台</span>
      </nav>

      {/* Sub Nav — 磨砂副导航 52px */}
      <div style={{
        height: 52, background: 'rgba(245, 245, 247, 0.8)',
        backdropFilter: 'saturate(180%) blur(20px)',
        WebkitBackdropFilter: 'saturate(180%) blur(20px)',
        display: 'flex', alignItems: 'center', padding: '0 48px',
        borderBottom: '1px solid #e0e0e0',
        position: 'sticky', top: 44, zIndex: 999,
      }}>
        <span style={{
          fontSize: 21, fontWeight: 600, color: '#1d1d1f',
          letterSpacing: '0.011em',
        }}>
          {location.pathname === '/' ? '产品总览' :
           location.pathname === '/admin' ? 'AI 竞争控制台' :
           location.pathname === '/admin/analytics' ? '数据看板' :
           location.pathname.startsWith('/product/') ? '产品详情' : ''}
        </span>
      </div>
    </>
  )
}
