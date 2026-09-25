import { Bell, Check, CircleAlert } from 'lucide-react'
import { useEffect, useState } from 'react'
import { AlertRecord, loadAlerts, updateAlert } from '../services/api'

export default function Alerts() {
  const [alerts, setAlerts] = useState<AlertRecord[]>([])
  const [message, setMessage] = useState('')
  async function refresh() { try { setAlerts(await loadAlerts()) } catch { setMessage('Alerts are unavailable until the API is running.') } }
  useEffect(() => { void refresh() }, [])
  async function changeStatus(id: number, status: 'REVIEWED' | 'RESOLVED') { await updateAlert(id, status); await refresh() }
  return <section className="page-section"><div className="page-heading"><div><p className="section-kicker">Review queue</p><h2>Alerts</h2><p>Model-generated review signals from recorded patient timelines.</p></div><span className="source-badge">Not a diagnosis</span></div>{message && <div className="form-message">{message}</div>}<div className="alert-list panel">{alerts.length ? alerts.map((alert) => <div className="alert-card" key={alert.id}><span className={`alert-icon ${alert.risk_level.toLowerCase()}`}><CircleAlert size={18} /></span><div className="alert-card-copy"><div><strong>Mother #{alert.mother_id} · {alert.risk_level} model risk</strong><span className={`status-badge ${alert.status.toLowerCase()}`}>{alert.status}</span></div><p>Risk score {Math.round(alert.risk_score * 100)}% · Created {new Date(alert.created_at).toLocaleString()}</p><small>Review the patient timeline and model feature contributions before updating the alert status.</small></div><div className="alert-actions">{alert.status === 'NEW' && <button onClick={() => void changeStatus(alert.id, 'REVIEWED')}><Check size={14} /> Review</button>}{alert.status !== 'RESOLVED' && <button onClick={() => void changeStatus(alert.id, 'RESOLVED')}><Check size={14} /> Resolve</button>}</div></div>) : <div className="empty-state"><Bell size={20} /><br />No high-risk alerts.</div>}</div></section>
}