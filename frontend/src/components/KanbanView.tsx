import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import api from '../services/api';
import { KanbanColumnStatus, ProjectItem, TaskItem, TaskPriority, TeamMember, User } from '../types';
import { Badge, Modal, Notify, btnGhost, btnPrimary, errorMessage, fieldErrors, inputClass, shortDate } from '../lib/ui';

const COLUMNS: { key: KanbanColumnStatus; label: string; accent: string }[] = [
  { key: 'TODO', label: 'À faire', accent: 'border-t-slate-400' },
  { key: 'IN_PROGRESS', label: 'En cours', accent: 'border-t-indigo-500' },
  { key: 'IN_REVIEW', label: 'En revue', accent: 'border-t-amber-500' },
  { key: 'DONE', label: 'Terminé', accent: 'border-t-emerald-500' },
];
const PRIORITIES: { key: TaskPriority; label: string; tone: 'slate' | 'blue' | 'amber' | 'red' }[] = [
  { key: 'LOW', label: 'Basse', tone: 'slate' }, { key: 'MEDIUM', label: 'Moyenne', tone: 'blue' },
  { key: 'HIGH', label: 'Haute', tone: 'amber' }, { key: 'URGENT', label: 'Urgente', tone: 'red' },
];

/** Réplique côté client la logique serveur : déplace + réindexe les colonnes concernées. */
function moveLocally(tasks: TaskItem[], taskId: number, column: KanbanColumnStatus, index: number): TaskItem[] {
  const moving = tasks.find((t) => t.id === taskId);
  if (!moving) return tasks;
  const from = moving.column_status;
  const byCol = (c: KanbanColumnStatus) => tasks.filter((t) => t.column_status === c && t.id !== taskId).sort((a, b) => a.position - b.position);
  const target = byCol(column);
  target.splice(Math.min(index, target.length), 0, { ...moving, column_status: column });
  const result = new Map<number, TaskItem>();
  target.forEach((t, i) => result.set(t.id, { ...t, position: i }));
  if (from !== column) byCol(from).forEach((t, i) => result.set(t.id, { ...t, position: i }));
  return tasks.map((t) => result.get(t.id) ?? t);
}

export const KanbanView: React.FC<{ user: User; notify: Notify }> = ({ user, notify }) => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [dragId, setDragId] = useState<number | null>(null);
  const [overCol, setOverCol] = useState<KanbanColumnStatus | null>(null);
  const [taskModal, setTaskModal] = useState<KanbanColumnStatus | null>(null);
  const [projectModal, setProjectModal] = useState(false);
  const [form, setForm] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const draggingRef = useRef(false);
  const canManage = ['SUPER_ADMIN', 'ADMIN', 'MANAGER'].includes(user.role);

  const load = useCallback(async (silent = false) => {
    try {
      const res = await api.get<ProjectItem[]>('/projects');
      setProjects(res.data);
      setSelectedId((cur) => (cur && res.data.some((p) => p.id === cur) ? cur : res.data[0]?.id ?? null));
    } catch (err) {
      if (!silent) notify(errorMessage(err, 'Chargement des projets impossible.'), 'err');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    api.get('/team').then((r) => setTeam(r.data)).catch(() => undefined);
    // Synchronisation automatique : on recharge toutes les 8 s, sauf pendant un glisser-déposer.
    const id = setInterval(() => { if (!draggingRef.current) load(true); }, 8000);
    return () => clearInterval(id);
  }, [load]);

  const project = projects.find((p) => p.id === selectedId);
  const tasksOf = (c: KanbanColumnStatus) => (project?.tasks ?? []).filter((t) => t.column_status === c).sort((a, b) => a.position - b.position);

  const drop = async (column: KanbanColumnStatus, index: number) => {
    draggingRef.current = false;
    setOverCol(null);
    if (dragId === null || !project) return;
    const id = dragId;
    setDragId(null);
    const before = projects;
    setProjects(projects.map((p) => (p.id === project.id ? { ...p, tasks: moveLocally(p.tasks, id, column, index) } : p)));
    try {
      await api.patch(`/tasks/${id}/move`, { column_status: column, position: index });
    } catch (err) {
      setProjects(before);
      notify(errorMessage(err, 'Déplacement impossible.'), 'err');
    }
  };

  const removeTask = async (t: TaskItem) => {
    if (!window.confirm(`Supprimer la tâche « ${t.title} » ?`)) return;
    try { await api.delete(`/tasks/${t.id}`); load(true); } catch (err) { notify(errorMessage(err), 'err'); }
  };

  const submitTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!project || !taskModal) return;
    setErrors({});
    try {
      await api.post(`/projects/${project.id}/tasks`, {
        title: form.title, description: form.description || null, column_status: taskModal,
        priority: form.priority || 'MEDIUM', assignee_id: form.assignee_id ? Number(form.assignee_id) : null,
        due_date: form.due_date || null,
        tags: form.tags ? String(form.tags).split(',').map((s: string) => s.trim()).filter(Boolean) : [],
      });
      setTaskModal(null);
      load(true);
    } catch (err) { setErrors(fieldErrors(err)); notify(errorMessage(err), 'err'); }
  };

  const submitProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    try {
      const res = await api.post('/projects', {
        code: form.code, name: form.name, description: form.description || null,
        budget_hours: form.budget_hours || 0, hourly_rate: form.hourly_rate || 100, deadline: form.deadline || null,
      });
      setProjectModal(false);
      await load(true);
      setSelectedId(res.data.id);
      notify('Projet créé.');
    } catch (err) { setErrors(fieldErrors(err)); notify(errorMessage(err), 'err'); }
  };

  const deleteProject = async () => {
    if (!project || !window.confirm(`Supprimer le projet « ${project.name} » et toutes ses tâches ?`)) return;
    try { await api.delete(`/projects/${project.id}`); notify('Projet supprimé.'); load(true); } catch (err) { notify(errorMessage(err), 'err'); }
  };

  const err = (k: string) => errors[k] && <p className="text-[11px] text-rose-600 mt-1">{errors[k]}</p>;
  const lbl = 'block text-xs font-semibold text-slate-600 mb-1';

  if (loading) return <p className="text-sm text-slate-500 p-6">Chargement…</p>;

  return (
    <div className="space-y-5">
      <div className="bg-white p-5 rounded-2xl border border-slate-200 flex flex-wrap justify-between items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Projets &amp; tableau Kanban</h2>
          <p className="text-xs text-slate-500 mt-0.5">Glissez les cartes entre les colonnes — synchronisation automatique toutes les 8 s.</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {projects.length > 0 && (
            <select aria-label="Projet" value={selectedId ?? ''} onChange={(e) => setSelectedId(Number(e.target.value))} className={inputClass + ' w-auto'}>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}
            </select>
          )}
          <button onClick={() => { setForm({}); setErrors({}); setProjectModal(true); }} className={btnGhost}><Plus className="w-4 h-4" /> Projet</button>
          {project && canManage && <button onClick={deleteProject} aria-label="Supprimer le projet" className="p-2 text-rose-600 hover:bg-rose-50 rounded-xl"><Trash2 className="w-4 h-4" /></button>}
        </div>
      </div>

      {!project ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
          Aucun projet. Créez votre premier projet pour ouvrir un tableau Kanban.
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-500 px-1">
            <span>Budget : <b className="text-slate-700">{project.budget_hours} h</b></span>
            <span>Taux : <b className="text-slate-700">{project.hourly_rate} $/h</b></span>
            <span>Échéance : <b className="text-slate-700">{shortDate(project.deadline)}</b></span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 items-start">
            {COLUMNS.map((col) => {
              const list = tasksOf(col.key);
              return (
                <section key={col.key} aria-label={col.label}
                  onDragOver={(e) => { e.preventDefault(); setOverCol(col.key); }}
                  onDragLeave={() => setOverCol((c) => (c === col.key ? null : c))}
                  onDrop={(e) => { e.preventDefault(); drop(col.key, list.length); }}
                  className={`rounded-2xl border border-slate-200 border-t-4 ${col.accent} p-3 min-h-[14rem] transition ${overCol === col.key ? 'bg-indigo-50' : 'bg-slate-50'}`}>
                  <div className="flex items-center justify-between px-1 mb-3">
                    <h3 className="text-sm font-bold text-slate-700">{col.label} <span className="text-slate-400 font-medium">{list.length}</span></h3>
                    <button onClick={() => { setForm({ priority: 'MEDIUM' }); setErrors({}); setTaskModal(col.key); }} aria-label={`Ajouter une tâche dans ${col.label}`}
                      className="p-1 rounded-lg text-slate-500 hover:bg-white"><Plus className="w-4 h-4" /></button>
                  </div>
                  <div className="space-y-2.5">
                    {list.map((t, i) => {
                      const prio = PRIORITIES.find((p) => p.key === t.priority)!;
                      return (
                        <article key={t.id} draggable
                          onDragStart={(e) => { draggingRef.current = true; setDragId(t.id); e.dataTransfer.effectAllowed = 'move'; }}
                          onDragEnd={() => { draggingRef.current = false; setDragId(null); setOverCol(null); }}
                          onDragOver={(e) => e.preventDefault()}
                          onDrop={(e) => { e.preventDefault(); e.stopPropagation(); drop(col.key, i); }}
                          className={`bg-white rounded-xl border border-slate-200 p-3 cursor-grab active:cursor-grabbing space-y-2 ${dragId === t.id ? 'opacity-40' : ''}`}>
                          <div className="flex justify-between gap-2">
                            <p className="text-sm font-semibold text-slate-800 leading-snug">{t.title}</p>
                            <button onClick={() => removeTask(t)} aria-label="Supprimer la tâche" className="text-slate-300 hover:text-rose-600 h-fit"><Trash2 className="w-3.5 h-3.5" /></button>
                          </div>
                          <div className="flex flex-wrap gap-1.5 items-center">
                            <Badge tone={prio.tone}>{prio.label}</Badge>
                            {t.tags?.map((tag) => <span key={tag} className="text-[11px] text-slate-500 bg-slate-100 rounded px-1.5 py-0.5">#{tag}</span>)}
                          </div>
                          <div className="flex items-center justify-between text-[11px] text-slate-500">
                            <span>{t.due_date ? `Échéance ${shortDate(t.due_date)}` : ''}</span>
                            {t.assignee && (
                              <span className="flex items-center gap-1.5">
                                <img src={t.assignee.avatar} alt="" className="w-5 h-5 rounded-full object-cover bg-slate-200" />
                                {t.assignee.prenom}
                              </span>
                            )}
                          </div>
                        </article>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>
        </>
      )}

      {taskModal && (
        <Modal title={`Nouvelle tâche — ${COLUMNS.find((c) => c.key === taskModal)?.label}`} onClose={() => setTaskModal(null)}>
          <form onSubmit={submitTask} className="space-y-4">
            <div><label className={lbl} htmlFor="t-title">Titre *</label>
              <input id="t-title" required autoFocus className={inputClass} value={form.title ?? ''} onChange={(e) => setForm({ ...form, title: e.target.value })} />{err('title')}</div>
            <div><label className={lbl} htmlFor="t-desc">Description</label>
              <textarea id="t-desc" rows={2} className={inputClass} value={form.description ?? ''} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className={lbl} htmlFor="t-prio">Priorité</label>
                <select id="t-prio" className={inputClass} value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
                  {PRIORITIES.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}</select></div>
              <div><label className={lbl} htmlFor="t-assignee">Assignée à</label>
                <select id="t-assignee" className={inputClass} value={form.assignee_id ?? ''} onChange={(e) => setForm({ ...form, assignee_id: e.target.value })}>
                  <option value="">— Personne —</option>
                  {team.map((m) => <option key={m.id} value={m.id}>{m.prenom} {m.nom}</option>)}</select>{err('assignee_id')}</div>
              <div><label className={lbl} htmlFor="t-due">Échéance</label>
                <input id="t-due" type="date" className={inputClass} value={form.due_date ?? ''} onChange={(e) => setForm({ ...form, due_date: e.target.value })} /></div>
              <div><label className={lbl} htmlFor="t-tags">Étiquettes</label>
                <input id="t-tags" placeholder="design, backend" className={inputClass} value={form.tags ?? ''} onChange={(e) => setForm({ ...form, tags: e.target.value })} /></div>
            </div>
            <div className="flex justify-end gap-2"><button type="button" onClick={() => setTaskModal(null)} className={btnGhost}>Annuler</button>
              <button type="submit" className={btnPrimary}>Créer la tâche</button></div>
          </form>
        </Modal>
      )}

      {projectModal && (
        <Modal title="Nouveau projet" onClose={() => setProjectModal(false)}>
          <form onSubmit={submitProject} className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div><label className={lbl} htmlFor="p-code">Code *</label>
                <input id="p-code" required placeholder="PRJ-003" className={inputClass} value={form.code ?? ''} onChange={(e) => setForm({ ...form, code: e.target.value })} />{err('code')}</div>
              <div className="col-span-2"><label className={lbl} htmlFor="p-name">Nom *</label>
                <input id="p-name" required className={inputClass} value={form.name ?? ''} onChange={(e) => setForm({ ...form, name: e.target.value })} />{err('name')}</div>
            </div>
            <div><label className={lbl} htmlFor="p-desc">Description</label>
              <textarea id="p-desc" rows={2} className={inputClass} value={form.description ?? ''} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
            <div className="grid grid-cols-3 gap-3">
              <div><label className={lbl} htmlFor="p-bud">Budget (h)</label>
                <input id="p-bud" type="number" min={0} className={inputClass} value={form.budget_hours ?? ''} onChange={(e) => setForm({ ...form, budget_hours: e.target.value })} /></div>
              <div><label className={lbl} htmlFor="p-rate">Taux ($/h)</label>
                <input id="p-rate" type="number" min={0} className={inputClass} value={form.hourly_rate ?? ''} onChange={(e) => setForm({ ...form, hourly_rate: e.target.value })} /></div>
              <div><label className={lbl} htmlFor="p-dl">Échéance</label>
                <input id="p-dl" type="date" className={inputClass} value={form.deadline ?? ''} onChange={(e) => setForm({ ...form, deadline: e.target.value })} /></div>
            </div>
            <div className="flex justify-end gap-2"><button type="button" onClick={() => setProjectModal(false)} className={btnGhost}>Annuler</button>
              <button type="submit" className={btnPrimary}>Créer le projet</button></div>
          </form>
        </Modal>
      )}
    </div>
  );
};
