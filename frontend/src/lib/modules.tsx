import React from 'react';
import { Badge, money, shortDate, statusTone } from './ui';

export interface FieldDef {
  key: string;
  label: string;
  type?: 'text' | 'email' | 'number' | 'date' | 'select' | 'textarea' | 'password' | 'url';
  options?: string[];
  required?: boolean;
  placeholder?: string;
  full?: boolean;
  hint?: string;
}

export type Row = Record<string, any>;

export interface CrudConfig {
  key: string;
  endpoint: string;
  title: string;
  subtitle: string;
  singular: string;
  layout: 'table' | 'cards';
  fields: FieldDef[];
  defaults: Row;
  searchKeys: string[];
  columns: { label: string; render: (row: Row) => React.ReactNode; align?: 'right' }[];
}

const fullName = (r: Row) => `${r.prenom} ${r.nom}`;

export const CLIENTS: CrudConfig = {
  key: 'clients', endpoint: '/clients', title: 'Clients', singular: 'client', layout: 'table',
  subtitle: 'Portefeuille clients et prospects de votre espace.',
  searchKeys: ['identifiant', 'nom', 'prenom', 'email', 'entreprise'],
  defaults: { statut: 'ACTIF' },
  fields: [
    { key: 'identifiant', label: 'Identifiant', required: true, placeholder: 'CLT-1003' },
    { key: 'statut', label: 'Statut', type: 'select', options: ['ACTIF', 'INACTIF', 'PROSPECT'], required: true },
    { key: 'prenom', label: 'Prénom', required: true },
    { key: 'nom', label: 'Nom', required: true },
    { key: 'email', label: 'Courriel', type: 'email', required: true },
    { key: 'telephone', label: 'Téléphone', required: true },
    { key: 'entreprise', label: 'Entreprise' },
    { key: 'adresse', label: 'Adresse', full: true },
  ],
  columns: [
    { label: 'Client', render: (r) => (<div><p className="font-semibold text-slate-800">{fullName(r)}</p><p className="text-xs text-slate-500 font-mono">{r.identifiant}</p></div>) },
    { label: 'Entreprise', render: (r) => r.entreprise || '—' },
    { label: 'Contact', render: (r) => (<div className="text-xs"><p>{r.email}</p><p className="text-slate-500">{r.telephone}</p></div>) },
    { label: 'Statut', render: (r) => <Badge tone={statusTone(r.statut)}>{r.statut}</Badge> },
  ],
};

export const EMPLOYEES: CrudConfig = {
  key: 'employees', endpoint: '/employees', title: 'Employés', singular: 'employé', layout: 'table',
  subtitle: 'Ressources humaines : postes, départements et rémunération.',
  searchKeys: ['matricule', 'nom', 'prenom', 'email', 'poste', 'departement'],
  defaults: { statut: 'ACTIF' },
  fields: [
    { key: 'matricule', label: 'Matricule', required: true, placeholder: 'EMP-003' },
    { key: 'statut', label: 'Statut', type: 'select', options: ['ACTIF', 'EN CONGÉ', 'INACTIF'], required: true },
    { key: 'prenom', label: 'Prénom', required: true },
    { key: 'nom', label: 'Nom', required: true },
    { key: 'email', label: 'Courriel', type: 'email', required: true },
    { key: 'telephone', label: 'Téléphone', required: true },
    { key: 'poste', label: 'Poste', required: true },
    { key: 'departement', label: 'Département', required: true },
    { key: 'salaire', label: 'Salaire annuel ($)', type: 'number', required: true },
    { key: 'date_embauche', label: "Date d'embauche", type: 'date', required: true },
  ],
  columns: [
    { label: 'Employé', render: (r) => (<div><p className="font-semibold text-slate-800">{fullName(r)}</p><p className="text-xs text-slate-500 font-mono">{r.matricule}</p></div>) },
    { label: 'Poste', render: (r) => (<div className="text-xs"><p className="font-semibold text-slate-700">{r.poste}</p><p className="text-slate-500">{r.departement}</p></div>) },
    { label: 'Embauche', render: (r) => shortDate(r.date_embauche) },
    { label: 'Salaire', align: 'right', render: (r) => <span className="font-semibold">{money(r.salaire)}</span> },
    { label: 'Statut', render: (r) => <Badge tone={statusTone(r.statut)}>{r.statut}</Badge> },
  ],
};

export const PRODUCTS: CrudConfig = {
  key: 'products', endpoint: '/products', title: 'Produits & stock', singular: 'produit', layout: 'cards',
  subtitle: 'Fiche produit : image, identifiant, prix et disponibilité.',
  searchKeys: ['identifiant', 'nom', 'categorie'],
  defaults: { disponibilite: 'EN STOCK', quantite_stock: 0, prix: 0 },
  fields: [
    { key: 'identifiant', label: 'Identifiant', required: true, placeholder: 'PRD-503' },
    { key: 'categorie', label: 'Catégorie', required: true },
    { key: 'nom', label: 'Nom du produit', required: true, full: true },
    { key: 'prix', label: 'Prix ($)', type: 'number', required: true },
    { key: 'quantite_stock', label: 'Quantité en stock', type: 'number', required: true, hint: '0 = passe automatiquement en rupture' },
    { key: 'disponibilite', label: 'Disponibilité', type: 'select', options: ['EN STOCK', 'EN RUPTURE'], required: true },
    { key: 'image', label: "URL de l'image", type: 'url', placeholder: 'https://…' },
    { key: 'description', label: 'Description', type: 'textarea', full: true },
  ],
  columns: [],
};

export const SERVICES: CrudConfig = {
  key: 'services', endpoint: '/services', title: 'Services', singular: 'service', layout: 'table',
  subtitle: 'Catalogue de prestations facturables.',
  searchKeys: ['identifiant', 'nom', 'description'],
  defaults: { statut: 'DISPONIBLE' },
  fields: [
    { key: 'identifiant', label: 'Identifiant', required: true, placeholder: 'SRV-203' },
    { key: 'statut', label: 'Statut', type: 'select', options: ['DISPONIBLE', 'INDISPONIBLE'], required: true },
    { key: 'nom', label: 'Nom du service', required: true, full: true },
    { key: 'prix_tarif', label: 'Tarif ($)', type: 'number', required: true },
    { key: 'duree_estimee', label: 'Durée estimée', required: true, placeholder: '3 Jours' },
    { key: 'description', label: 'Description', type: 'textarea', required: true, full: true },
  ],
  columns: [
    { label: 'Service', render: (r) => (<div><p className="font-semibold text-slate-800">{r.nom}</p><p className="text-xs text-slate-500 font-mono">{r.identifiant}</p></div>) },
    { label: 'Description', render: (r) => <span className="text-xs text-slate-600 line-clamp-2">{r.description}</span> },
    { label: 'Durée', render: (r) => r.duree_estimee },
    { label: 'Tarif', align: 'right', render: (r) => <span className="font-semibold">{money(r.prix_tarif)}</span> },
    { label: 'Statut', render: (r) => <Badge tone={statusTone(r.statut)}>{r.statut}</Badge> },
  ],
};

export const USERS: CrudConfig = {
  key: 'users', endpoint: '/users', title: 'Utilisateurs du système', singular: 'utilisateur', layout: 'table',
  subtitle: 'Comptes ayant accès à votre espace, avec leur rôle.',
  searchKeys: ['nom', 'prenom', 'email', 'role'],
  defaults: { role: 'USER', status: 'ACTIVE' },
  fields: [
    { key: 'prenom', label: 'Prénom', required: true },
    { key: 'nom', label: 'Nom', required: true },
    { key: 'email', label: 'Courriel', type: 'email', required: true, full: true },
    { key: 'role', label: 'Rôle', type: 'select', options: ['ADMIN', 'MANAGER', 'USER'], required: true },
    { key: 'status', label: 'Statut', type: 'select', options: ['ACTIVE', 'SUSPENDED'], required: true },
    { key: 'password', label: 'Mot de passe', type: 'password', full: true, hint: 'Laisser vide : un mot de passe temporaire sera généré (création) ou conservé (modification).' },
  ],
  columns: [
    { label: 'Utilisateur', render: (r) => (
      <div className="flex items-center gap-3">
        <img src={r.avatar} alt="" className="w-9 h-9 rounded-full object-cover bg-slate-200" />
        <div><p className="font-semibold text-slate-800">{fullName(r)}</p><p className="text-xs text-slate-500">{r.email}</p></div>
      </div>) },
    { label: 'Rôle', render: (r) => <Badge tone={r.role === 'SUPER_ADMIN' ? 'blue' : 'slate'}>{r.role}</Badge> },
    { label: 'Forfait', render: (r) => r.plan },
    { label: 'Statut', render: (r) => <Badge tone={statusTone(r.status)}>{r.status}</Badge> },
  ],
};
