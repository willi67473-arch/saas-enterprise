import React, { useCallback, useEffect, useState } from 'react';
import { Play, Square } from 'lucide-react';
import api from '../services/api';
import { ProjectItem, TimeEntryItem, User } from '../types';
import { Badge, Notify, btnPrimary, errorMessage, formatClock, hoursLabel, inputClass, money, shortDate } from '../lib/ui';

export const TimeTrackingView: React.FC<{ user: User; notify: Notify }> = ({ user, notify }) => {
  const [entries, setEntries] = useState<TimeEntryItem[]>([]);
  const [summary, setSummary] = useState({ total_hours: 0, billable_hours: 0, non_billable_hours: 0 });
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [projectId, setProjectId] = useState<number | ''>('');
  const [description, setDescription] = useState('');
  const [billable, setBillable] = useState(true);
  const [elapsed, setElapsed] = useState(0);
  const isManager = ['SUPER_ADMIN', 'ADMIN', 'MANAGER'].includes(user.role);

  const load = useCallback(async () => {
    try {
      const [t, p] = await Promise.all([api.get('/time-entries'), api.get('/projects')]);
      setEntries(t.data.entries);
      setSummary(t.data.summary);
      setProjects(p.data);
      setProjectId((cur) => (cur === '' && p.data.length ? p.data[0].id : cur));
    } catch (err) {
      notify(errorMessage(err, 'Chargement impossible.'), 'err');
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const running = entries.find((e) => e.is_running && e.user_id === user.id);

  useEffect(() => {
    if (!running) { setElapsed(0); return; }
    const tick = () => setElapsed(Math.max(0, Math.floor((Date.now() - new Date(running.started_at).getTime()) / 1000)));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [running?.id, running?.started_at]);

  const start = async () => {
    if (projectId === '') return;
    try {
      await api.post('/time-entries/start', { project_id: projectId, description: description || null, is_billable: billable });
      setDescription('');
      load();
    } catch (err) { notify(errorMessage(err), 'err'); }
  };

  const stop = async (id: number) => {
    try { await api.patch(`/time-entries/${id}/stop`); load(); } catch (err) { notify(errorMessage(err), 'err'); }
  };

  const amount = (e: TimeEntryItem) =>
    e.is_billable && e.project?.hourly_rate ? money((e.duration_seconds / 3600) * e.project.hourly_rate) : '—';

  return (
    <div className="space-y-5">
      <div className="bg-white p-5 rounded-2xl border border-slate-200">
        <h2 className="text-xl font-bold text-slate-800">Suivi du temps</h2>
        <p className="text-xs text-slate-500 mt-0.5">Un seul chronomètre actif par personne : en démarrer un nouveau arrête le précédent.</p>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {([['Total', summary.total_hours], ['Facturable', summary.billable_hours], ['Non facturable', summary.non_billable_hours]] as const).map(([l, v]) => (
          <div key={l} className="bg-white rounded-2xl border border-slate-200 p-5">
            <p className="text-3xl font-black text-slate-900">{v} h</p><p className="text-xs text-slate-500 mt-1">{l}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-5">
        {running ? (
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs text-slate-500">En cours — {running.project?.code} {running.project?.name}</p>
              <p className="text-4xl font-black font-mono text-indigo-600 mt-1" aria-live="off">{formatClock(elapsed)}</p>
              <p className="text-xs text-slate-500 mt-1">{running.description}</p>
            </div>
            <button onClick={() => stop(running.id)} className="inline-flex items-center gap-2 px-5 py-3 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-sm font-bold">
              <Square className="w-4 h-4" /> Arrêter
            </button>
          </div>
        ) : projects.length === 0 ? (
          <p className="text-sm text-slate-500">Créez d’abord un projet dans l’onglet Projets &amp; Kanban pour pouvoir suivre du temps.</p>
        ) : (
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[12rem]">
              <label htmlFor="tt-desc" className="block text-xs font-semibold text-slate-600 mb-1">Sur quoi travaillez-vous ?</label>
              <input id="tt-desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Session de travail" className={inputClass} />
            </div>
            <div>
              <label htmlFor="tt-proj" className="block text-xs font-semibold text-slate-600 mb-1">Projet</label>
              <select id="tt-proj" value={projectId} onChange={(e) => setProjectId(Number(e.target.value))} className={inputClass}>
                {projects.map((p) => <option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}
              </select>
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-600 pb-2">
              <input type="checkbox" checked={billable} onChange={(e) => setBillable(e.target.checked)} /> Facturable
            </label>
            <button onClick={start} className={btnPrimary}><Play className="w-4 h-4" /> Démarrer</button>
          </div>
        )}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="px-5 py-3 font-semibold">Date</th>
              {isManager && <th className="px-5 py-3 font-semibold">Membre</th>}
              <th className="px-5 py-3 font-semibold">Projet / description</th>
              <th className="px-5 py-3 font-semibold">Durée</th>
              <th className="px-5 py-3 font-semibold text-right">Montant</th>
              <th className="px-5 py-3 font-semibold">Type</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {entries.length === 0 && <tr><td colSpan={6} className="px-5 py-8 text-center text-slate-500">Aucune entrée de temps.</td></tr>}
            {entries.map((e) => (
              <tr key={e.id}>
                <td className="px-5 py-3 text-xs text-slate-600 whitespace-nowrap">{shortDate(e.started_at)}</td>
                {isManager && <td className="px-5 py-3 text-xs">{e.user ? `${e.user.prenom} ${e.user.nom}` : '—'}</td>}
                <td className="px-5 py-3"><p className="font-semibold text-slate-800 text-xs">{e.project?.code} {e.project?.name}</p><p className="text-xs text-slate-500">{e.description}</p></td>
                <td className="px-5 py-3 font-mono text-xs">{e.is_running ? <Badge tone="blue">En cours</Badge> : hoursLabel(e.duration_seconds)}</td>
                <td className="px-5 py-3 text-right text-xs font-semibold">{amount(e)}</td>
                <td className="px-5 py-3"><Badge tone={e.is_billable ? 'green' : 'slate'}>{e.is_billable ? 'Facturable' : 'Interne'}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
