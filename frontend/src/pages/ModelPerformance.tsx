import { BarChart3, Database, ShieldAlert } from 'lucide-react'
import { useEffect, useState } from 'react'
import axios from 'axios'

type ModelResult = { name: string; status?: string; accuracy?: number; precision?: number; recall?: number; f1?: number; roc_auc?: number; note?: string }
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api'

export default function ModelPerformance() {
  const [models, setModels] = useState<{ baseline: ModelResult; sequential: ModelResult } | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    async function load() {
      try {
        const login = await axios.post(`${API_URL}/auth/login`, { email: 'demo@maternasense.local', password: 'demo-password' })
        const response = await axios.get(`${API_URL}/model/performance`, { headers: { Authorization: `Bearer ${login.data.access_token as string}` } })
        setModels(response.data)
      } catch { setError('Model performance is unavailable until the API is running.') }
    }
    void load()
  }, [])
  const metric = (value?: number) => value === undefined ? 'Pending Evaluation' : `${(value * 100).toFixed(1)}%`
  const metricGrid = (model: ModelResult) => <div className="metric-grid">{[['Accuracy', model.accuracy], ['Precision', model.precision], ['Recall', model.recall], ['F1', model.f1], ['ROC-AUC', model.roc_auc]].map(([label, value]) => <div key={String(label)}><small>{label}</small><strong>{metric(value as number | undefined)}</strong></div>)}</div>
  const illustrativeMetrics = [['Accuracy', '83%'], ['Precision', '80%'], ['Recall', '78%'], ['F1', '80%'], ['ROC-AUC', '86%']]
  const illustrativeGrid = <div className="metric-grid">{illustrativeMetrics.map(([label, value]) => <div key={label}><small>Illustrative {label}</small><strong>{value}</strong></div>)}</div>
  return <section className="page-section"><div className="page-heading"><div><p className="section-kicker">Research evaluation</p><h2>Model performance</h2><p>Observed baseline results and sequential-model readiness.</p></div><span className="source-badge">No clinical validation claim</span></div>{error ? <div className="empty-state error-state">{error}</div> : !models ? <div className="empty-state">Loading evaluation results...</div> : <><div className="model-cards"><article className="panel model-card"><div className="model-card-heading"><span className="model-icon"><BarChart3 size={19} /></span><div><p className="section-kicker">Single-visit baseline</p><h3>{models.baseline.name}</h3></div><span className="source-badge">{models.baseline.status || 'Evaluated'}</span></div>{metricGrid(models.baseline)}<p className="model-note"><Database size={14} /> Trained from `Maternal_Risk.csv` after exact duplicate removal. Evaluation uses a row-level split because no patient identifier exists.</p></article><article className="panel model-card pending-model"><div className="model-card-heading"><span className="model-icon"><ShieldAlert size={19} /></span><div><p className="section-kicker">Sequential model</p><h3>{models.sequential.name}</h3></div><span className="source-badge">Illustrative display</span></div>{illustrativeGrid}<p className="model-note">Synthetic research demonstration only; the sequential model was not trained on real linked patient trajectories. Actual evaluation remains documented separately.</p></article></div><div className="comparison-note panel"><strong>Single-Visit Baseline vs Longitudinal Sequential Model</strong><span>Illustrative targets are not measured metrics or clinical validation.</span></div></>}</section>
}
