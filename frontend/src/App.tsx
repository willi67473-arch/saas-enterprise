import React, { useCallback, useEffect, useState } from 'react';
import {
  Briefcase, Clock, CreditCard, Kanban, LayoutDashboard, LogOut, Package, UserCheck, Users, Wrench,
} from 'lucide-react';
import api from './services/api';
import { User } from './types';
import { LoginView } from './components/LoginView';
import { Dashboard } from './components/Dashboard';
import { CrudView } from './components/CrudView';
import { KanbanView } from './components/KanbanView';
import { TimeTrackingView } from './components/TimeTrackingView';
import { BillingView } from './components/BillingView';
import { NotificationBell } from './components/NotificationBell';
import { CLIENTS, EMPLOYEES, PRODUCTS, SERVICES, USERS } from './lib/modules';
import { Notify } from './lib/ui';

type TabKey = 'dashboard' | 'kanban' | 'time' | 'products' | 'services' | 'clients' | 'employees' | 'users' | 'billing';

const ADMINS = ['SUPER_ADMIN', 'ADMIN'];
const MANAGERS = ['SUPER_ADMIN', 'ADMIN', 'MANAGER'];

const NAV: { key: TabKey; label: string; icon: React.ElementType; roles?: string[]; group: string }[] = [
  { key: 'dashboard', label: 'Tableau de bord', icon: LayoutDashboard, group: 'Pilotage' },
  { key: 'kanban', label: 'Projets & Kanban', icon: Kanban, group: 'Pilotage' },
  { key: 'time', label: 'Suivi du temps', icon: Clock, group: 'Pilotage' },
  { key: 'products', label: 'Produits', icon: Package, group: 'Gestion' },
  { key: 'services', label: 'Services', icon: Wrench, group: 'Gestion' },
  { key: 'clients', label: 'Clients', icon: UserCheck, group: 'Gestion' },
  { key: 'employees', label: 'Employés', icon: Briefcase, roles: MANAGERS, group: 'Gestion' },
  { key: 'users', label: 'Utilisateurs', icon: Users, roles: ADMINS, group: 'Administration' },
  { key: 'billing', label: 'Abonnement & équipe', icon: CreditCard, group: 'Administration' },
];

export function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('saas_token'));
  const [user, setUser] = useState<User | null>(null);
  const [booting, setBooting] = useState<boolean>(!!localStorage.getItem('saas_token'));
  const [tab, setTab] = useState<TabKey>('dashboard');
  const [toast, setToast] = useState<{ message: string; kind: 'ok' | 'err' } | null>(null);

  const notify: Notify = useCallback((message, kind = 'ok') => {
    setToast({ message, kind });
    window.setTimeout(() => setToast((t) => (t?.message === message ? null : t)), 4500);
  }, []);

  const logout = useCallback((callApi = true) => {
    if (callApi && localStorage.getItem('saas_token')) api.post('/logout').catch(() => undefined);
    localStorage.removeItem('saas_token');
    setToken(null);
    setUser(null);
    setTab('dashboard');
  }, []);

  const refreshUser = useCallback(() => {
    api.get('/me').then((r) => setUser(r.data)).catch(() => undefined);
  }, []);

  // Restauration de la session
  useEffect(() => {
    if (!token) { setBooting(false); return; }
    if (user) return;
    api.get('/me')
      .then((r) => setUser(r.data))
      .catch(() => logout(false))
      .finally(() => setBooting(false));
  }, [token]);

  // Jeton rejeté par l'API (expiré / révoqué)
  useEffect(() => {
    const onUnauthorized = () => { logout(false); notify('Votre session a expiré. Veuillez vous reconnecter.', 'err'); };
    window.addEventListener('saas:unauthorized', onUnauthorized);
    return () => window.removeEventListener('saas:unauthorized', onUnauthorized);
  }, [logout, notify]);

  const handleLoginSuccess = (u: User, accessToken: string) => {
    localStorage.setItem('saas_token', accessToken);
    setUser(u);
    setToken(accessToken);
    setTab('dashboard');
  };

  if (booting) return <div className="min-h-screen flex items-center justify-center text-sm text-slate-500">Chargement…</div>;
  if (!token || !user) return <LoginView onLoginSuccess={handleLoginSuccess} />;

  const items = NAV.filter((n) => !n.roles || n.roles.includes(user.role));
  const groups = Array.from(new Set(items.map((i) => i.group)));
  const canWrite = MANAGERS.includes(user.role);

  const page = (() => {
    switch (tab) {
      case 'dashboard': return <Dashboard user={user} notify={notify} />;
      case 'kanban': return <KanbanView user={user} notify={notify} />;
      case 'time': return <TimeTrackingView user={user} notify={notify} />;
      case 'products': return <CrudView key="p" config={PRODUCTS} canWrite={canWrite} notify={notify} />;
      case 'services': return <CrudView key="s" config={SERVICES} canWrite={canWrite} notify={notify} />;
      case 'clients': return <CrudView key="c" config={CLIENTS} canWrite={canWrite} notify={notify} />;
      case 'employees': return <CrudView key="e" config={EMPLOYEES} canWrite={canWrite} notify={notify} />;
      case 'users': return <CrudView key="u" config={USERS} canWrite={ADMINS.includes(user.role)} notify={notify} />;
      case 'billing': return <BillingView user={user} notify={notify} onPlanChanged={refreshUser} />;
    }
  })();

  return (
    <div className="min-h-screen flex bg-slate-100">
      <aside className="hidden md:flex w-60 shrink-0 flex-col bg-slate-900 text-slate-300">
        <div className="h-16 px-5 flex items-center gap-3 border-b border-slate-800">
          <div className="w-9 h-9 bg-indigo-600 rounded-xl font-black text-white flex items-center justify-center">S</div>
          <div className="leading-tight"><p className="font-bold text-sm text-white">SaaS Enterprise</p><p className="text-[10px] text-slate-500">ERP &amp; Projets</p></div>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-5" aria-label="Navigation principale">
          {groups.map((g) => (
            <div key={g}>
              <p className="px-3 mb-1.5 text-[11px] text-slate-500 font-semibold">{g}</p>
              {items.filter((i) => i.group === g).map((i) => (
                <button key={i.key} onClick={() => setTab(i.key)} aria-current={tab === i.key ? 'page' : undefined}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition ${tab === i.key ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800 hover:text-white'}`}>
                  <i.icon className="w-4 h-4" />{i.label}
                </button>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-16 bg-slate-900 text-white px-4 md:px-8 flex items-center justify-between border-b border-slate-800">
          <p className="text-sm font-semibold truncate">{user.tenant?.name ?? 'Mon espace'}</p>
          <div className="flex items-center gap-3">
            <NotificationBell />
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold">{user.prenom} {user.nom}</p>
              <p className="text-[10px] text-indigo-300 font-mono">{user.role}</p>
            </div>
            <button onClick={() => logout()} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg border border-slate-700">
              <LogOut className="w-3.5 h-3.5" /> Quitter
            </button>
          </div>
        </header>

        {/* Navigation mobile */}
        <nav className="md:hidden flex gap-1 overflow-x-auto bg-white border-b border-slate-200 px-2" aria-label="Navigation mobile">
          {items.map((i) => (
            <button key={i.key} onClick={() => setTab(i.key)}
              className={`shrink-0 flex items-center gap-1.5 px-3 py-3 text-xs font-semibold border-b-2 ${tab === i.key ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500'}`}>
              <i.icon className="w-4 h-4" />{i.label}
            </button>
          ))}
        </nav>

        <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">{page}</main>
      </div>

      {toast && (
        <div role="status" className={`fixed bottom-5 right-5 z-[60] max-w-sm px-4 py-3 rounded-xl shadow-lg text-sm font-medium text-white ${toast.kind === 'ok' ? 'bg-emerald-600' : 'bg-rose-600'}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}

export default App;
