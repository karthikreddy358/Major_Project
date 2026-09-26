import { useEffect, useState } from 'react'
import { Activity, BarChart3, Bell, ChevronRight, CircleAlert, FileText, HeartPulse, Info, LayoutDashboard, LogOut, Network, Users } from 'lucide-react'
import Alerts from './pages/Alerts'
import Architecture from './pages/Architecture'
import Login from './pages/Login'
import ModelPerformance from './pages/ModelPerformance'
import PatientDirectory from './pages/PatientDirectory'
import PatientProfile from './pages/PatientProfile'
import ProjectInfo from './pages/ProjectInfo'
import Reports from './pages/Reports'
import RiskMonitoring from './pages/RiskMonitoring'
import { AlertRecord, DashboardStats, hasSession, logout, loadDashboard, PredictionRecord, validateSession } from './services/api'

type DashboardData = { stats: DashboardStats; alerts: AlertRecord[]; featuredPredictions: PredictionRecord[] }

function Dashboard({ data, apiError }: { data: DashboardData | null; apiError: boolean }) {
  const stats = data ? [
    { label: 'Mothers monitored', value: data.stats.total_mothers, note: 'Across active care journeys', icon: Users },
    { label: 'High model risk', value: data.stats.high_risk_cases, note: 'Requires record review', icon: CircleAlert },
    { label: 'Newborns followed', value: data.stats.newborns_monitored, note: 'Linked to maternal records', icon: HeartPulse },
  ] : []
  const trajectory = data?.featuredPredictions.slice().reverse() || []
  return <>
    <section className="intro"><div><p className="section-kicker">Care journey overview</p><h2>See the whole story, not a single visit.</h2><p>MaternaSense connects maternal, delivery, newborn and postnatal records so model-estimated risk can be followed over time.</p></div><div className="intro-badge"><span>CONTINUITY VIEW</span><strong>Connected records</strong><small>Timeline-based review</small></div></section>
    <section className="stats-grid">{stats.length ? stats.map(({ label, value, note, icon: Icon }) => <article className="stat-card" key={label}><div className="stat-icon"><Icon size={18} /></div><p>{label}</p><strong>{value}</strong><small>{note}</small></article>) : <article className="stat-card loading-card"><p>Connecting to continuity API</p><strong>--</strong><small>{apiError ? 'Start Flask to load live dashboard data' : 'Loading live dashboard data'}</small></article>}</section>
    <section className="workspace-grid"><article className="panel journey-panel"><div className="panel-heading"><div><p className="section-kicker">Latest trajectory</p><h3>{trajectory.length ? 'M003 · Recorded model history' : 'No recorded trajectory'}</h3></div>{trajectory.length > 0 && <span className={`risk-pill ${trajectory[trajectory.length - 1].risk_level.toLowerCase()}`}>{Math.round(trajectory[trajectory.length - 1].risk_score * 100)}% · {trajectory[trajectory.length - 1].risk_level}</span>}</div>{trajectory.length ? <><div className="risk-line"><div className="line-track"><span className="line-progress" style={{ width: `${trajectory[trajectory.length - 1].risk_score * 100}%` }} /></div><div className="risk-points">{trajectory.map((prediction, index) => <span className={index === trajectory.length - 1 ? 'current' : ''} key={prediction.id}>{Math.round(prediction.risk_score * 100)}%<small>Update {index + 1}</small></span>)}</div></div><div className="journey-footer"><span><i className="trend-up">↗</i> Updated from prediction history</span><a href="#patient/3">Open patient profile <ChevronRight size={15} /></a></div></> : <div className="empty-state">Add a care record to begin longitudinal monitoring.</div>}</article><article className="panel alert-panel"><div className="panel-heading"><div><p className="section-kicker">Needs review</p><h3>Recent alerts</h3></div><a className="text-link" href="#alerts">View all</a></div>{data?.alerts.slice(0, 3).map((alert) => <div className="alert-row" key={alert.id}><span className={`alert-marker ${alert.risk_level === 'HIGH' ? 'high-marker' : 'moderate-marker'}`} /><div><strong>Mother #{alert.mother_id} · {alert.risk_level} model risk</strong><small>Status: {alert.status.toLowerCase()}</small></div><span className="alert-time">{new Date(alert.created_at).toLocaleDateString()}</span></div>) || <div className="empty-alerts">{apiError ? 'Alerts unavailable until the API is running.' : 'Loading recent alerts...'}</div>}</article></section>
  </>
}

function App() {
  const [authenticated, setAuthenticated] = useState(false)
  const [sessionChecked, setSessionChecked] = useState(false)
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [apiError, setApiError] = useState(false)
  const [view, setView] = useState(window.location.hash.slice(1) || 'dashboard')
  useEffect(() => {
    const onUnauthorized = () => { logout(); setAuthenticated(false); setDashboard(null) }
    window.addEventListener('maternasense:unauthorized', onUnauthorized)
    if (!hasSession()) setSessionChecked(true)
    else validateSession().then(() => setAuthenticated(true)).catch(() => logout()).finally(() => setSessionChecked(true))
    return () => window.removeEventListener('maternasense:unauthorized', onUnauthorized)
  }, [])
  useEffect(() => { if (authenticated) loadDashboard().then(setDashboard).catch(() => setApiError(true)) }, [authenticated])
  useEffect(() => { const onHashChange = () => setView(window.location.hash.slice(1) || 'dashboard'); window.addEventListener('hashchange', onHashChange); return () => window.removeEventListener('hashchange', onHashChange) }, [])
  if (!sessionChecked) return <main className="login-page"><div className="empty-state">Checking your session...</div></main>
  if (!authenticated) return <Login onLogin={() => setAuthenticated(true)} />
  const page = view === 'patients' ? <PatientDirectory /> : view.startsWith('patient/') ? <PatientProfile id={Number(view.split('/')[1])} /> : view === 'risk' ? <RiskMonitoring /> : view === 'alerts' ? <Alerts /> : view === 'performance' ? <ModelPerformance /> : view === 'reports' ? <Reports /> : view === 'architecture' ? <Architecture /> : view === 'info' ? <ProjectInfo /> : <Dashboard data={dashboard} apiError={apiError} />
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><span className="brand-mark"><Activity size={18} /></span><span>MaternaSense</span></div><p className="eyebrow">Continuity intelligence</p><nav aria-label="Primary navigation"><a className="nav-item" href="#dashboard"><LayoutDashboard size={17} />Dashboard</a><a className="nav-item" href="#patients"><Users size={17} />Patients</a><a className="nav-item" href="#risk"><Activity size={17} />Risk monitoring</a><a className="nav-item" href="#alerts"><Bell size={17} />Alerts</a><a className="nav-item" href="#performance"><BarChart3 size={17} />Model performance</a><a className="nav-item" href="#reports"><FileText size={17} />Reports</a><a className="nav-item" href="#architecture"><Network size={17} />Architecture</a><a className="nav-item" href="#info"><Info size={17} />Project information</a></nav><div className="sidebar-note"><span className="status-dot" />Connected workspace<br /><small>Continuity records</small></div></aside><main className="main-content"><header className="topbar"><div><p className="eyebrow">Care continuity workspace</p></div><div className="user-chip"><span className="avatar">CW</span><span><strong>Healthcare worker</strong><small>Signed-in workspace</small></span><button className="logout-button" aria-label="Log out" onClick={() => { logout(); setAuthenticated(false) }}><LogOut size={15} /></button></div></header>{page}<footer className="disclaimer">Research / educational decision support · Not a Medical Diagnosis · Review all records with professional judgment.</footer></main></div>
}

export default App
