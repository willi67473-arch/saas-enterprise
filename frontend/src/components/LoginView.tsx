import React, { useEffect, useState } from 'react';
import { ArrowRight, Building2, Lock, Mail, ShieldCheck } from 'lucide-react';
import api from '../services/api';
import { Plan, User } from '../types';
import { errorMessage, fieldErrors, inputClass } from '../lib/ui';

interface Props {
  onLoginSuccess: (user: User, token: string) => void;
}

type Mode = 'login' | 'register' | 'invite';

const dark =
  'w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500';

const DEMOS = [
  { label: 'Propriétaire', email: 'admin@enterprise.ca' },
  { label: 'Manager', email: 'manager@enterprise.ca' },
  { label: 'Utilisateur', email: 'user@enterprise.ca' },
];

export const LoginView: React.FC<Props> = ({ onLoginSuccess }) => {
  const inviteToken = new URLSearchParams(window.location.search).get('invite');
  const [mode, setMode] = useState<Mode>(inviteToken ? 'invite' : 'login');
  const [form, setForm] = useState<Record<string, string>>({ email: 'admin@enterprise.ca', password: 'password', plan_slug: 'free' });
  const [plans, setPlans] = useState<Plan[]>([]);
  const [inviteInfo, setInviteInfo] = useState<{ email: string; role: string; tenant_name: string } | null>(null);
  const [error, setError] = useState('');
  const [fields, setFields] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  useEffect(() => {
    if (mode === 'register' && plans.length === 0) api.get('/plans').then((r) => setPlans(r.data)).catch(() => undefined);
  }, [mode]);

  useEffect(() => {
    if (mode !== 'invite' || !inviteToken) return;
    api.get(`/invitations/${inviteToken}`)
      .then((r) => setInviteInfo(r.data))
      .catch((err) => setError(errorMessage(err, 'Invitation invalide.')));
  }, [mode, inviteToken]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setFields({});
    setLoading(true);
    try {
      let res;
      if (mode === 'login') {
        res = await api.post('/login', { email: form.email, password: form.password });
      } else if (mode === 'register') {
        res = await api.post('/tenants/register', form);
      } else {
        res = await api.post('/invitations/accept', {
          token: inviteToken, nom: form.nom, prenom: form.prenom, password: form.password,
        });
        window.history.replaceState({}, '', window.location.pathname);
      }
      onLoginSuccess(res.data.user, res.data.access_token);
    } catch (err) {
      setError(errorMessage(err, 'Erreur de connexion au serveur.'));
      setFields(fieldErrors(err));
    } finally {
      setLoading(false);
    }
  };

  const field = (k: string, label: string, type = 'text', placeholder?: string) => (
    <div className="space-y-1">
      <label htmlFor={`l-${k}`} className="text-xs font-semibold text-slate-300">{label}</label>
      <input id={`l-${k}`} type={type} required value={form[k] ?? ''} onChange={set(k)} placeholder={placeholder} className={dark} />
      {fields[k] && <p className="text-[11px] text-rose-400">{fields[k]}</p>}
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-800 border border-slate-700 rounded-3xl p-8 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-indigo-600 rounded-2xl mx-auto flex items-center justify-center text-white font-black text-xl">S</div>
          <h1 className="text-xl font-bold text-white">SaaS Enterprise Platform</h1>
          <p className="text-xs text-slate-400">
            {mode === 'login' && 'Connectez-vous à votre espace ERP & projets'}
            {mode === 'register' && 'Créez votre espace entreprise (14 jours d’essai)'}
            {mode === 'invite' && (inviteInfo ? `Rejoindre « ${inviteInfo.tenant_name} »` : 'Invitation')}
          </p>
        </div>

        {error && <div role="alert" className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 text-center">{error}</div>}

        <form onSubmit={submit} className="space-y-4">
          {mode === 'login' && (
            <>
              <div className="space-y-1">
                <label htmlFor="l-email" className="text-xs font-semibold text-slate-300">Adresse courriel</label>
                <div className="relative"><Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input id="l-email" type="email" required value={form.email} onChange={set('email')} className={dark + ' pl-10'} /></div>
              </div>
              <div className="space-y-1">
                <label htmlFor="l-password" className="text-xs font-semibold text-slate-300">Mot de passe</label>
                <div className="relative"><Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input id="l-password" type="password" required value={form.password} onChange={set('password')} className={dark + ' pl-10'} /></div>
              </div>
              <div className="flex flex-wrap gap-2 items-center text-[11px] text-slate-400">
                Comptes de démo :
                {DEMOS.map((d) => (
                  <button key={d.email} type="button" onClick={() => setForm({ ...form, email: d.email, password: 'password' })}
                    className="px-2 py-1 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200">{d.label}</button>
                ))}
              </div>
            </>
          )}

          {mode === 'register' && (
            <>
              {field('company_name', "Nom de l'entreprise")}
              {field('subdomain', 'Sous-domaine', 'text', 'ma-societe')}
              <div className="grid grid-cols-2 gap-3">{field('prenom', 'Prénom')}{field('nom', 'Nom')}</div>
              {field('email', 'Courriel', 'email')}
              {field('password', 'Mot de passe (8 caractères min.)', 'password')}
              <div className="space-y-1">
                <label htmlFor="l-plan" className="text-xs font-semibold text-slate-300">Forfait</label>
                <select id="l-plan" value={form.plan_slug} onChange={set('plan_slug')} className={dark}>
                  {(plans.length ? plans : [{ slug: 'free', name: 'FREE', price_monthly: 0 } as Plan]).map((p) => (
                    <option key={p.slug} value={p.slug}>{p.name} — {p.price_monthly} $/mois</option>
                  ))}
                </select>
              </div>
            </>
          )}

          {mode === 'invite' && inviteInfo && (
            <>
              <p className="text-xs text-slate-300 text-center">Compte : <span className="font-mono text-white">{inviteInfo.email}</span> · rôle {inviteInfo.role}</p>
              <div className="grid grid-cols-2 gap-3">{field('prenom', 'Prénom')}{field('nom', 'Nom')}</div>
              {field('password', 'Choisissez un mot de passe (8 caractères min.)', 'password')}
            </>
          )}

          {(mode !== 'invite' || inviteInfo) && (
            <button type="submit" disabled={loading}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold transition flex items-center justify-center gap-2 disabled:opacity-50">
              {loading ? 'Veuillez patienter…' : mode === 'login' ? 'Se connecter' : mode === 'register' ? 'Créer mon espace' : 'Rejoindre l’équipe'}
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </form>

        {mode !== 'invite' && (
          <p className="text-center text-xs text-slate-400">
            {mode === 'login' ? 'Nouvelle entreprise ?' : 'Déjà inscrit ?'}{' '}
            <button type="button" onClick={() => { setError(''); setFields({}); setForm(mode === 'login' ? { plan_slug: 'free' } : { email: 'admin@enterprise.ca', password: 'password', plan_slug: 'free' }); setMode(mode === 'login' ? 'register' : 'login'); }}
              className="text-indigo-400 hover:text-indigo-300 font-semibold inline-flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5" />{mode === 'login' ? 'Créer un espace' : 'Se connecter'}
            </button>
          </p>
        )}

        <div className="pt-4 border-t border-slate-700/60 flex items-center justify-center gap-2 text-[11px] text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400" /> Sécurisé par Laravel Sanctum
        </div>
      </div>
    </div>
  );
};
