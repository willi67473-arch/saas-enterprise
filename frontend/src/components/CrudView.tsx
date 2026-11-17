import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Edit3, Plus, Search, Trash2 } from 'lucide-react';
import api from '../services/api';
import { CrudConfig, FieldDef, Row } from '../lib/modules';
import {
  Badge, Modal, Notify, btnGhost, btnPrimary, errorMessage, fieldErrors, inputClass, money, statusTone,
} from '../lib/ui';

interface Props {
  config: CrudConfig;
  canWrite: boolean;
  notify: Notify;
}

export const CrudView: React.FC<Props> = ({ config, canWrite, notify }) => {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState<Row | null>(null); // null = fermé ; {} = création
  const [form, setForm] = useState<Row>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [credentials, setCredentials] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(config.endpoint);
      setRows(res.data);
    } catch (err) {
      notify(errorMessage(err, 'Chargement impossible.'), 'err');
    } finally {
      setLoading(false);
    }
  }, [config.endpoint]);

  useEffect(() => {
    setSearch('');
    load();
  }, [load]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => config.searchKeys.some((k) => String(r[k] ?? '').toLowerCase().includes(q)));
  }, [rows, search, config.searchKeys]);

  const openCreate = () => {
    setForm({ ...config.defaults });
    setErrors({});
    setEditing({});
  };
  const openEdit = (row: Row) => {
    const values: Row = {};
    config.fields.forEach((f) => {
      values[f.key] = f.type === 'password' ? '' : row[f.key] ?? '';
    });
    setForm(values);
    setErrors({});
    setEditing(row);
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    setSaving(true);
    setErrors({});
    const payload: Row = { ...form };
    Object.keys(payload).forEach((k) => {
      if (payload[k] === '') payload[k] = null;
    });
    try {
      const isEdit = editing.id !== undefined;
      const res = isEdit
        ? await api.put(`${config.endpoint}/${editing.id}`, payload)
        : await api.post(config.endpoint, payload);
      notify(res.data.message ?? 'Enregistré.');
      if (res.data.temporary_password) setCredentials(res.data.temporary_password);
      setEditing(null);
      load();
    } catch (err) {
      setErrors(fieldErrors(err));
      notify(errorMessage(err, 'Enregistrement impossible.'), 'err');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (row: Row) => {
    const label = row.nom ?? row.identifiant ?? `#${row.id}`;
    if (!window.confirm(`Supprimer « ${label} » ? Cette action est définitive.`)) return;
    try {
      const res = await api.delete(`${config.endpoint}/${row.id}`);
      notify(res.data.message ?? 'Supprimé.');
      load();
    } catch (err) {
      notify(errorMessage(err, 'Suppression impossible.'), 'err');
    }
  };

  const renderField = (f: FieldDef) => {
    const common = {
      id: `f-${f.key}`,
      required: f.required && f.type !== 'password',
      value: form[f.key] ?? '',
      onChange: (e: React.ChangeEvent<any>) => setForm({ ...form, [f.key]: e.target.value }),
      className: inputClass + (errors[f.key] ? ' border-rose-400' : ''),
      placeholder: f.placeholder,
    };
    return (
      <div key={f.key} className={f.full ? 'sm:col-span-2' : ''}>
        <label htmlFor={`f-${f.key}`} className="block text-xs font-semibold text-slate-600 mb-1">
          {f.label}{f.required && f.type !== 'password' && <span className="text-rose-500"> *</span>}
        </label>
        {f.type === 'select' ? (
          <select {...common}>{f.options!.map((o) => <option key={o} value={o}>{o}</option>)}</select>
        ) : f.type === 'textarea' ? (
          <textarea {...common} rows={3} />
        ) : (
          <input {...common} type={f.type ?? 'text'} step={f.type === 'number' ? '0.01' : undefined} min={f.type === 'number' ? 0 : undefined} />
        )}
        {f.hint && <p className="text-[11px] text-slate-500 mt-1">{f.hint}</p>}
        {errors[f.key] && <p className="text-[11px] text-rose-600 mt-1">{errors[f.key]}</p>}
      </div>
    );
  };

  const actions = (row: Row) =>
    canWrite && (
      <div className="flex gap-1 justify-end">
        <button onClick={() => openEdit(row)} aria-label="Modifier" className="p-1.5 text-amber-600 hover:bg-amber-50 rounded-lg"><Edit3 className="w-4 h-4" /></button>
        {row.role !== 'SUPER_ADMIN' && (
          <button onClick={() => remove(row)} aria-label="Supprimer" className="p-1.5 text-rose-600 hover:bg-rose-50 rounded-lg"><Trash2 className="w-4 h-4" /></button>
        )}
      </div>
    );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-5 rounded-2xl border border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-800">{config.title} <span className="text-slate-400 font-medium">({rows.length})</span></h2>
          <p className="text-xs text-slate-500 mt-0.5">{config.subtitle}</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Rechercher…" aria-label="Rechercher"
              className={inputClass + ' pl-9 w-52'} />
          </div>
          {canWrite && <button onClick={openCreate} className={btnPrimary}><Plus className="w-4 h-4" /> Nouveau</button>}
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-slate-500 p-6">Chargement…</p>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
          {rows.length === 0 ? `Aucun(e) ${config.singular} pour le moment.` : 'Aucun résultat pour cette recherche.'}
        </div>
      ) : config.layout === 'cards' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filtered.map((p) => (
            <div key={p.id} className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
              <div className="h-40 bg-slate-100 relative">
                {p.image && <img src={p.image} alt={p.nom} className="w-full h-full object-cover" />}
                <span className="absolute top-3 right-3"><Badge tone={statusTone(p.disponibilite)}>{p.disponibilite}</Badge></span>
                <span className="absolute bottom-3 left-3 bg-slate-900/80 text-white text-[10px] font-mono px-2 py-1 rounded-lg">ID : {p.identifiant}</span>
              </div>
              <div className="p-4 space-y-2">
                <div className="flex justify-between items-start gap-3">
                  <div>
                    <p className="text-[11px] font-semibold text-indigo-600">{p.categorie}</p>
                    <h3 className="font-bold text-slate-800 leading-snug">{p.nom}</h3>
                  </div>
                  <p className="text-lg font-black text-slate-900 whitespace-nowrap">{money(p.prix)}</p>
                </div>
                <p className="text-xs text-slate-500 line-clamp-2 min-h-[2rem]">{p.description}</p>
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className={p.quantite_stock <= 5 ? 'text-amber-600 font-semibold' : 'text-slate-600'}>
                    Stock : {p.quantite_stock} unité(s)
                  </span>
                  {actions(p)}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr>
                {config.columns.map((c) => <th key={c.label} className={`px-5 py-3 font-semibold ${c.align === 'right' ? 'text-right' : ''}`}>{c.label}</th>)}
                {canWrite && <th className="px-5 py-3"><span className="sr-only">Actions</span></th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/60">
                  {config.columns.map((c) => <td key={c.label} className={`px-5 py-3.5 ${c.align === 'right' ? 'text-right' : ''}`}>{c.render(r)}</td>)}
                  {canWrite && <td className="px-5 py-3.5">{actions(r)}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <Modal title={`${editing.id !== undefined ? 'Modifier' : 'Nouveau'} ${config.singular}`} onClose={() => setEditing(null)} wide>
          <form onSubmit={save} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">{config.fields.map(renderField)}</div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setEditing(null)} className={btnGhost}>Annuler</button>
              <button type="submit" disabled={saving} className={btnPrimary}>{saving ? 'Enregistrement…' : 'Enregistrer'}</button>
            </div>
          </form>
        </Modal>
      )}

      {credentials && (
        <Modal title="Mot de passe temporaire" onClose={() => setCredentials(null)}>
          <p className="text-sm text-slate-600">Transmettez ce mot de passe à l'utilisateur. Il ne sera plus affiché.</p>
          <p className="my-4 px-4 py-3 bg-slate-100 rounded-xl font-mono text-base text-center select-all">{credentials}</p>
          <button onClick={() => setCredentials(null)} className={btnPrimary + ' w-full'}>J'ai noté le mot de passe</button>
        </Modal>
      )}
    </div>
  );
};
