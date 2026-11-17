import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export type Notify = (message: string, kind?: 'ok' | 'err') => void;

export const money = (n: number | string) =>
  new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD' }).format(Number(n) || 0);

export const hoursLabel = (seconds: number) => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h} h ${String(m).padStart(2, '0')}`;
};

export const formatClock = (sec: number) => {
  const h = String(Math.floor(sec / 3600)).padStart(2, '0');
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
  const s = String(sec % 60).padStart(2, '0');
  return `${h}:${m}:${s}`;
};

export const shortDate = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleDateString('fr-CA', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';

/** Extrait un message lisible d'une erreur axios (Laravel : message + errors par champ). */
export function errorMessage(err: any, fallback = 'Une erreur est survenue.'): string {
  const data = err?.response?.data;
  if (data?.errors) {
    const first = Object.values(data.errors as Record<string, string[]>)[0];
    if (first?.[0]) return first[0];
  }
  if (data?.message) return data.message;
  if (err?.code === 'ERR_NETWORK') return "Impossible de joindre l'API Laravel (http://127.0.0.1:8000). Est-elle démarrée ?";
  return fallback;
}

export function fieldErrors(err: any): Record<string, string> {
  const out: Record<string, string> = {};
  const errors = err?.response?.data?.errors as Record<string, string[]> | undefined;
  if (errors) for (const [k, v] of Object.entries(errors)) out[k] = v[0];
  return out;
}

export const Modal: React.FC<{ title: string; onClose: () => void; children: React.ReactNode; wide?: boolean }> = ({
  title, onClose, children, wide,
}) => {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60" role="dialog" aria-modal="true">
      <div className={`bg-white rounded-2xl shadow-2xl w-full ${wide ? 'max-w-2xl' : 'max-w-md'} max-h-[90vh] overflow-y-auto`}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h3 className="font-bold text-slate-800">{title}</h3>
          <button onClick={onClose} aria-label="Fermer" className="p-1 rounded-lg text-slate-500 hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

const TONES: Record<string, string> = {
  green: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  red: 'bg-rose-50 text-rose-700 border-rose-200',
  amber: 'bg-amber-50 text-amber-700 border-amber-200',
  blue: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  slate: 'bg-slate-100 text-slate-600 border-slate-200',
};

export const Badge: React.FC<{ tone?: keyof typeof TONES; children: React.ReactNode }> = ({ tone = 'slate', children }) => (
  <span className={`inline-block px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${TONES[tone]}`}>{children}</span>
);

export const statusTone = (s: string): keyof typeof TONES => {
  if (['ACTIF', 'ACTIVE', 'DISPONIBLE', 'EN STOCK'].includes(s)) return 'green';
  if (['INACTIF', 'INDISPONIBLE', 'EN RUPTURE', 'SUSPENDED', 'CANCELED'].includes(s)) return 'red';
  if (['PROSPECT', 'EN CONGÉ', 'TRIALING', 'PAST_DUE'].includes(s)) return 'amber';
  return 'slate';
};

export const inputClass =
  'w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500';

export const btnPrimary =
  'inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold transition disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-500/50';

export const btnGhost =
  'inline-flex items-center justify-center gap-2 px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl text-sm font-semibold transition';
