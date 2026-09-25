import { Plus, Search, UserRound, ChevronRight, X } from 'lucide-react'
import { FormEvent, useEffect, useState } from 'react'
import { createMother, loadMothers, MotherRecord } from '../services/api'

export default function PatientDirectory() {
  const [mothers, setMothers] = useState<MotherRecord[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ mother_code: '', name: '', age: '', blood_group: '' })

  async function refresh(term = '') {
    setLoading(true)
    try { setMothers(await loadMothers(term)); setError('') } catch { setError('Unable to load patients. Start the Flask API and try again.') } finally { setLoading(false) }
  }
  useEffect(() => { void refresh() }, [])
  function submitSearch(event: FormEvent) { event.preventDefault(); void refresh(search) }
  async function submitMother(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError('')
    try { await createMother({ mother_code: form.mother_code.trim(), name: form.name.trim(), age: Number(form.age) || undefined, blood_group: form.blood_group.trim() || undefined }); setForm({ mother_code: '', name: '', age: '', blood_group: '' }); setShowForm(false); await refresh(search) } catch { setError('Mother could not be created. Check the code is unique and all required fields are valid.') } finally { setSaving(false) }
  }

  return <section className="page-section"><div className="page-heading"><div><p className="section-kicker">Continuity registry</p><h2>Patients</h2><p>Search mothers, create a record, and open the full care journey.</p></div><button className="primary-button add-mother-button" onClick={() => setShowForm((visible) => !visible)}>{showForm ? <X size={15} /> : <Plus size={15} />}{showForm ? 'Close' : 'Add mother'}</button></div>{showForm && <form className="panel mother-form" onSubmit={submitMother}><div><p className="section-kicker">New maternal record</p><h3>Create mother</h3></div><div className="form-two"><label>Mother ID<input value={form.mother_code} onChange={(event) => setForm({ ...form, mother_code: event.target.value })} placeholder="M005" required /></label><label>Patient name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Synthetic High Risk Mother" required /></label></div><div className="form-two"><label>Age<input type="number" min="10" max="65" value={form.age} onChange={(event) => setForm({ ...form, age: event.target.value })} /></label><label>Blood group<input value={form.blood_group} onChange={(event) => setForm({ ...form, blood_group: event.target.value })} placeholder="O+" /></label></div><button className="primary-button" disabled={saving} type="submit">{saving ? 'Creating record...' : 'Create mother record'}</button></form>}<form className="search-bar" onSubmit={submitSearch}><Search size={17} /><input aria-label="Search patients" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search mother ID or name" /><button type="submit">Search</button></form><div className="patient-table panel"><div className="table-header"><span>Mother</span><span>Visits</span><span>Current model risk</span><span>Source</span><span /></div>{loading && <div className="empty-state">Loading patient records...</div>}{!loading && error && <div className="empty-state error-state">{error}</div>}{!loading && !error && mothers.map((mother) => <a className="patient-row" href={`#patient/${mother.id}`} key={mother.id}><span className="patient-name"><span className="patient-avatar"><UserRound size={16} /></span><span><strong>{mother.mother_code}</strong><small>{mother.name}</small></span></span><span>{mother.antenatal_visit_count}</span><span>{mother.current_prediction ? <b className={`risk-text ${mother.current_prediction.risk_level.toLowerCase()}`}>{Math.round(mother.current_prediction.risk_score * 100)}% · {mother.current_prediction.risk_level}</b> : <small>Not analyzed</small>}</span><span className="source-badge">{mother.source_type}</span><ChevronRight size={16} /></a>)}{!loading && !error && mothers.length === 0 && <div className="empty-state">No patients match this search.</div>}</div></section>
}
