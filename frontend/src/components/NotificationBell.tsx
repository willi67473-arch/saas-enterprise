import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Bell } from 'lucide-react';
import api from '../services/api';
import { RealtimeNotif } from '../types';

export const NotificationBell: React.FC = () => {
  const [items, setItems] = useState<RealtimeNotif[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const load = useCallback(() => {
    api.get('/notifications').then((r) => setItems(r.data)).catch(() => undefined);
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 15000); // rafraîchissement périodique (voir README pour le WebSocket)
    return () => clearInterval(id);
  }, [load]);

  useEffect(() => {
    const close = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const unread = items.filter((n) => !n.is_read).length;

  const read = async (n: RealtimeNotif) => {
    if (n.is_read) return;
    setItems((cur) => cur.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
    api.patch(`/notifications/${n.id}/read`).catch(load);
  };
  const readAll = async () => {
    setItems((cur) => cur.map((x) => ({ ...x, is_read: true })));
    api.post('/notifications/read-all').catch(load);
  };

  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(!open)} aria-label={`Notifications (${unread} non lues)`} aria-expanded={open}
        className="relative p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300">
        <Bell className="w-4 h-4" />
        {unread > 0 && <span className="absolute -top-1 -right-1 min-w-[1.1rem] h-[1.1rem] px-1 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">{unread}</span>}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white text-slate-800 rounded-2xl shadow-2xl border border-slate-200 z-40 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <p className="text-sm font-bold">Notifications</p>
            {unread > 0 && <button onClick={readAll} className="text-xs font-semibold text-indigo-600 hover:underline">Tout marquer comme lu</button>}
          </div>
          <ul className="max-h-80 overflow-y-auto divide-y divide-slate-100">
            {items.length === 0 && <li className="px-4 py-6 text-center text-xs text-slate-500">Aucune notification.</li>}
            {items.map((n) => (
              <li key={n.id}>
                <button onClick={() => read(n)} className={`w-full text-left px-4 py-3 hover:bg-slate-50 ${n.is_read ? '' : 'bg-indigo-50/50'}`}>
                  <p className="text-xs font-bold flex items-center gap-2">{!n.is_read && <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />}{n.title}</p>
                  <p className="text-xs text-slate-600 mt-0.5">{n.message}</p>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
