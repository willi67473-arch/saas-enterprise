import React, { useCallback, useEffect, useState } from 'react';
import { Check, Copy } from 'lucide-react';
import api from '../services/api';
import { Invitation, Plan, Tenant, User } from '../types';
import { Badge, Notify, btnPrimary, errorMessage, inputClass, shortDate, statusTone } from '../lib/ui';

interface BillingData {
  tenant: Tenant;
  usage: { users: number; projects: number; pending_invitations: number };
  plans: Plan[];
}

const Meter: React.FC<{ label: string; value: number; max: number }> = ({ label, value, max }) => {
  const pct = Math.min(100, (value / Math.max(1, max)) * 100);
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-600 mb-1"><span>{label}</span><span className="font-semibold">{value} / {max}</span></div>
      <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden"><div className={`h-full rounded-full ${pct >= 90 ? 'bg-rose-500' : 'bg-indigo-500'}`} style={{ width: `${pct}%` }} /></div>
    </div>
  );
};

export const BillingView: React.FC<{ user: User; notify: Notify; onPlanChanged: () => void }> = ({ user, notify, onPlanChanged }) => {
  const [data, setData] = useState<BillingData | null>(null);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('USER');
  const [link, setLink] = useState('');
  const [copied, setCopied] = useState(false);
  const isAdmin = ['SUPER_ADMIN', 'ADMIN'].includes(user.role);

  const load = useCallback(async () => {
    try {
      const b = await api.get('/billing');
      setData(b.data);
      if (isAdmin) setInvitations((await api.get('/tenants/invitations')).data);
    } catch (err) { notify(errorMessage(err), 'err'); }
  }, [isAdmin]);

  useEffect(() => { load(); }, [load]);

  const subscribe = async (plan: Plan) => {
    if (!window.confirm(`Passer au forfait ${plan.name} (${plan.price_monthly} $/mois) ?`)) return;
    try {
      const res = await api.post('/billing/subscribe', { plan_id: plan.id });
      notify(res.data.message);
      await load();
      onPlanChanged();
    } catch (err) { notify(errorMessage(err), 'err'); }
  };

  const invite = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post('/tenants/invite', { email, role });
      setLink(res.data.invitation_link);
      setEmail('');
      setCopied(false);
      load();
    } catch (err) { notify(errorMessage(err), 'err'); }
  };

  const copy = async () => {
    try { await navigator.clipboard.writeText(link); setCopied(true); } catch { notify('Copie impossible : sélectionnez le lien manuellement.', 'err'); }
  };

  if (!data) return <p className="text-sm text-slate-500 p-6">Chargement…</p>;
  const current = data.tenant.plan;

  return (
    <div className="space-y-6">
      <div className="bg-white p-5 rounded-2xl border border-slate-200 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Abonnement &amp; équipe</h2>
          <p className="text-xs text-slate-500 mt-0.5">Forfait actuel : <b>{current?.name ?? '—'}</b> · espace « {data.tenant.name} »</p>
        </div>
        <div className="text-right">
          <Badge tone={statusTone(data.tenant.subscription_status)}>{data.tenant.subscription_status}</Badge>
          {data.tenant.subscription_status === 'TRIALING' && data.tenant.trial_ends_at && (
            <p className="text-xs text-amber-600 mt-1">Essai jusqu’au {shortDate(data.tenant.trial_ends_at)}</p>
          )}
        </div>
      </div>

      {current && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 grid md:grid-cols-2 gap-6">
          <Meter label="Utilisateurs" value={data.usage.users} max={current.max_users} />
          <Meter label="Projets" value={data.usage.projects} max={current.max_projects} />
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-5">
        {data.plans.map((p) => {
          const active = p.id === current?.id;
          return (
            <div key={p.id} className={`bg-white rounded-2xl border p-6 flex flex-col ${active ? 'border-indigo-500 ring-2 ring-indigo-500/20' : 'border-slate-200'}`}>
              <div className="flex justify-between items-start"><h3 className="font-bold text-slate-800">{p.name}</h3>{active && <Badge tone="blue">Actuel</Badge>}</div>
              <p className="mt-2"><span className="text-3xl font-black text-slate-900">{p.price_monthly} $</span><span className="text-xs text-slate-500"> /mois</span></p>
              <ul className="mt-4 space-y-2 text-sm text-slate-600 flex-1">
                {(p.features ?? []).map((f) => <li key={f} className="flex gap-2"><Check className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />{f}</li>)}
              </ul>
              {isAdmin && <button disabled={active} onClick={() => subscribe(p)} className={btnPrimary + ' mt-5'}>{active ? 'Forfait actuel' : 'Choisir ce forfait'}</button>}
            </div>
          );
        })}
      </div>
      <p className="text-xs text-slate-500 -mt-2">Mode démonstration : le changement de forfait est appliqué immédiatement, sans paiement réel.</p>

      {isAdmin && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
          <h3 className="font-bold text-slate-800">Inviter un membre</h3>
          <form onSubmit={invite} className="flex flex-wrap gap-3 items-end">
            <div className="flex-1 min-w-[14rem]">
              <label htmlFor="inv-email" className="block text-xs font-semibold text-slate-600 mb-1">Courriel</label>
              <input id="inv-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={inputClass} placeholder="collegue@entreprise.com" />
            </div>
            <div>
              <label htmlFor="inv-role" className="block text-xs font-semibold text-slate-600 mb-1">Rôle</label>
              <select id="inv-role" value={role} onChange={(e) => setRole(e.target.value)} className={inputClass}>
                <option value="USER">USER</option><option value="MANAGER">MANAGER</option><option value="ADMIN">ADMIN</option>
              </select>
            </div>
            <button type="submit" className={btnPrimary}>Générer le lien</button>
          </form>
          {link && (
            <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-xl p-3">
              <input readOnly value={link} onFocus={(e) => e.target.select()} aria-label="Lien d'invitation" className="flex-1 bg-transparent text-xs font-mono text-emerald-900 outline-none" />
              <button onClick={copy} className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700"><Copy className="w-3.5 h-3.5" />{copied ? 'Copié !' : 'Copier'}</button>
            </div>
          )}
          {invitations.length > 0 && (
            <table className="w-full text-xs text-left">
              <thead className="text-slate-500"><tr><th className="py-2 font-semibold">Courriel</th><th className="font-semibold">Rôle</th><th className="font-semibold">Expire</th><th className="font-semibold">État</th></tr></thead>
              <tbody className="divide-y divide-slate-100">
                {invitations.map((i) => {
                  const expired = new Date(i.expires_at) < new Date();
                  return (
                    <tr key={i.id}><td className="py-2">{i.email}</td><td>{i.role}</td><td>{shortDate(i.expires_at)}</td>
                      <td>{i.accepted_at ? <Badge tone="green">Acceptée</Badge> : expired ? <Badge tone="red">Expirée</Badge> : <Badge tone="amber">En attente</Badge>}</td></tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};
