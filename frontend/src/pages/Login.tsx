import { Activity, ArrowRight, LockKeyhole, Mail } from 'lucide-react'
import { FormEvent, useState } from 'react'
import { login } from '../services/api'

export default function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  async function submit(event: FormEvent) { event.preventDefault(); setLoading(true); setError(''); try { await login(email, password); onLogin() } catch { setError('Login failed. Check your email and password.') } finally { setLoading(false) } }
  return <main className="login-page"><section className="login-visual"><div className="brand"><span className="brand-mark"><Activity size={18} /></span><span>MaternaSense</span></div><div><p className="section-kicker">Continuity intelligence</p><h1>One care journey.<br /><em>Many connected signals.</em></h1><p>Review maternal and newborn records as a timeline, with model-estimated risk that evolves as new information is recorded.</p></div><small>Research and educational decision support</small></section><section className="login-panel"><div className="login-form-wrap"><p className="section-kicker">Secure workspace</p><h2>Welcome back</h2><p>Sign in to continue to the continuity dashboard.</p><form onSubmit={submit}><label><span><Mail size={14} /> Email</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" /></label><label><span><LockKeyhole size={14} /> Password</span><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" /></label>{error && <div className="login-error">{error}</div>}<button className="primary-button" disabled={loading} type="submit">{loading ? 'Signing in...' : 'Sign in'}<ArrowRight size={15} /></button></form><p className="login-disclaimer">This system does not replace professional medical judgment or provide a medical diagnosis.</p></div></section></main>
}