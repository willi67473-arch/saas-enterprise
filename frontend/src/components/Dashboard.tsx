import React, { useEffect, useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import api from '../services/api';
import { DashboardData, KanbanColumnStatus, User } from '../types';
import { Badge, Notify, errorMessage, shortDate } from '../lib/ui';

const LABELS: Record<KanbanColumnStatus, string> = { TODO: 'À faire', IN_PROGRESS: 'En cours', IN_REVIEW: 'En revue', DONE: 'Terminé' };
const BAR: Record<KanbanColumnStatus, string> = { TODO: 'bg-slate-400', IN_PROGRESS: 'bg-indigo-500', IN_REVIEW: 'bg-amber-500', DONE: 'bg-emerald-500' };

export const Dashboard: React.FC<{ user: User; notify: Notify }> = ({ user, notify }) => {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    api.get('/dashboard').then((r) => setData(r.data)).catch((e) => notify(errorMessage(e), 'err'));
  }, []);

  if (!data) return <p className="text-sm text-slate-500 p-6">Chargement du tableau de bord…</p>;

  const tenant = user.tenant;
  const totalTasks = Object.values(data.tasks_by_status).reduce((a, b) => a + (b ?? 0), 0);
  const cards: [string, number][] = [
    ['Projets', data.counts.projects], ['Clients', data.counts.clients], ['Produits', data.counts.products],
    ['Services', data.counts.services], ['Utilisateurs', data.counts.users],
  ];

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 text-white rounded-2xl p-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs text-slate-400">Espace de travail</p>
          <h2 className="text-2xl font-bold mt-0.5">{tenant?.name ?? 'Mon entreprise'}</h2>
          <p className="text-sm text-slate-300 mt-1">Bonjour {user.prenom}, voici l’état de votre activité.</p>
        </div>
        <div className="text-right space-y-1">
          <Badge tone="blue">Forfait {tenant?.plan?.name ?? user.plan}</Badge>
          {tenant?.subscription_status === 'TRIALING' && tenant.trial_ends_at && (
            <p className="text-xs text-amber-300">Essai jusqu’au {shortDate(tenant.trial_ends_at)}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {cards.map(([label, n]) => (
          <div key={label} className="bg-white rounded-2xl border border-slate-200 p-5">
            <p className="text-3xl font-black text-slate-900">{n}</p>
            <p className="text-xs text-slate-500 mt-1">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
          <h3 className="font-bold text-slate-800">Avancement des tâches <span className="text-slate-400 font-medium">({totalTasks})</span></h3>
          {totalTasks === 0 ? <p className="text-sm text-slate-500">Aucune tâche pour le moment.</p> : (
            (Object.keys(LABELS) as KanbanColumnStatus[]).map((k) => {
              const n = data.tasks_by_status[k] ?? 0;
              return (
                <div key={k}>
                  <div className="flex justify-between text-xs text-slate-600 mb-1"><span>{LABELS[k]}</span><span className="font-semibold">{n}</span></div>
                  <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full ${BAR[k]} rounded-full`} style={{ width: `${(n / totalTasks) * 100}%` }} />
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            <h3 className="font-bold text-slate-800 mb-3">Heures du mois</h3>
            <p className="text-3xl font-black text-slate-900">{data.hours_this_month.total} h</p>
            <p className="text-xs text-slate-500 mt-1">dont {data.hours_this_month.billable} h facturables</p>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            <h3 className="font-bold text-slate-800 mb-3 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-500" /> Stock faible</h3>
            {data.low_stock.length === 0 ? <p className="text-sm text-slate-500">Aucune alerte de stock.</p> : (
              <ul className="space-y-2">
                {data.low_stock.map((p) => (
                  <li key={p.id} className="flex justify-between text-xs">
                    <span className="text-slate-700 truncate pr-2">{p.nom}</span>
                    <span className={p.quantite_stock === 0 ? 'text-rose-600 font-bold' : 'text-amber-600 font-bold'}>{p.quantite_stock}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
