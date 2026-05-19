import { Tag } from 'antd'
import { RobotOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const AI_LABELS: Record<string, string> = {
  deepseek: 'DeepSeek', gpt: 'GPT', doubao: '豆包', mimo: 'MiMo', qwen: '通义千问',
}
const AI_COLORS: Record<string, string> = {
  deepseek: '#1677ff', gpt: '#722ed1', doubao: '#ff4d4f', mimo: '#ff6600', qwen: '#52c41a',
}

interface Product {
  id: number; name: string; description: string;
  ai_model: string; category: string;
  price: number; original_price: number; stock: number
}

export default function ProductCard({ product }: { product: Product }) {
  const navigate = useNavigate()
  const discount = product.original_price > product.price
    ? Math.round((1 - product.price / product.original_price) * 100) : 0

  return (
    <div
      onClick={() => navigate(`/product/${product.id}`)}
      style={{
        background: '#ffffff', border: '1px solid #e0e0e0',
        borderRadius: 18, padding: 24, cursor: 'pointer',
        transition: 'border-color 0.2s',
      }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = '#0066cc')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = '#e0e0e0')}
    >
      <div style={{
        height: 160, background: '#f5f5f7', borderRadius: 8,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 56, marginBottom: 20,
        boxShadow: 'rgba(0, 0, 0, 0.22) 3px 5px 30px 0',
      }}>
        💊
      </div>

      <div style={{ marginBottom: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        <Tag style={{
          background: AI_COLORS[product.ai_model] + '15', color: AI_COLORS[product.ai_model],
          border: 'none', borderRadius: 9999, fontSize: 12, padding: '2px 10px',
        }}>
          <RobotOutlined /> {AI_LABELS[product.ai_model]}
        </Tag>
        <Tag style={{
          background: '#f5f5f7', color: '#7a7a7a', border: 'none',
          borderRadius: 9999, fontSize: 12, padding: '2px 10px',
        }}>
          {product.category}
        </Tag>
      </div>

      <h3 style={{
        fontSize: 17, fontWeight: 600, color: '#1d1d1f',
        letterSpacing: '-0.022em', lineHeight: 1.24, marginBottom: 4,
      }}>
        {product.name}
      </h3>

      <p style={{
        fontSize: 14, color: '#7a7a7a', lineHeight: 1.43,
        letterSpacing: '-0.016em', marginBottom: 16,
        display: '-webkit-box', WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical', overflow: 'hidden', minHeight: 40,
      }}>
        {product.description}
      </p>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: 21, fontWeight: 600, color: '#1d1d1f', letterSpacing: '-0.016em' }}>
          ¥{product.price}
        </span>
        {discount > 0 && (
          <>
            <span style={{ fontSize: 14, color: '#7a7a7a', textDecoration: 'line-through' }}>
              ¥{product.original_price}
            </span>
            <span style={{ fontSize: 12, color: '#0066cc', fontWeight: 600 }}>省{discount}%</span>
          </>
        )}
        <span style={{ marginLeft: 'auto', fontSize: 12, color: '#7a7a7a' }}>库存 {product.stock}</span>
      </div>
    </div>
  )
}
