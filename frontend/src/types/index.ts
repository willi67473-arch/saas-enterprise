export type Role = 'SUPER_ADMIN' | 'ADMIN' | 'MANAGER' | 'USER';
export type SubscriptionStatus = 'ACTIVE' | 'TRIALING' | 'PAST_DUE' | 'CANCELED';

export interface Plan {
  id: number;
  name: string;
  slug: string;
  price_monthly: number;
  max_projects: number;
  max_users: number;
  has_time_tracking: boolean;
  has_realtime_ws: boolean;
  features: string[];
}

export interface Tenant {
  id: string;
  name: string;
  subdomain: string;
  subscription_status: SubscriptionStatus;
  trial_ends_at?: string | null;
  plan?: Plan | null;
}

export interface User {
  id: number;
  tenant_id: string;
  nom: string;
  prenom: string;
  email: string;
  role: Role;
  plan: string;
  status: 'ACTIVE' | 'SUSPENDED';
  avatar: string;
  tenant?: Tenant;
}

export interface TeamMember {
  id: number;
  nom: string;
  prenom: string;
  role: Role;
  avatar: string;
}

export type KanbanColumnStatus = 'TODO' | 'IN_PROGRESS' | 'IN_REVIEW' | 'DONE';
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface TaskItem {
  id: number;
  project_id: number;
  assignee_id?: number | null;
  assignee?: Pick<User, 'id' | 'nom' | 'prenom' | 'avatar'> | null;
  title: string;
  description?: string | null;
  column_status: KanbanColumnStatus;
  position: number;
  priority: TaskPriority;
  tags?: string[] | null;
  due_date?: string | null;
}

export interface ProjectItem {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  status: 'PLANNING' | 'ACTIVE' | 'ON_HOLD' | 'COMPLETED';
  budget_hours: number;
  hourly_rate: number;
  deadline?: string | null;
  tasks: TaskItem[];
}

export interface TimeEntryItem {
  id: number;
  user_id: number;
  project_id: number;
  task_id?: number | null;
  project?: { id: number; code: string; name: string; hourly_rate?: number };
  task?: { id: number; title: string } | null;
  user?: { id: number; nom: string; prenom: string };
  description: string;
  started_at: string;
  ended_at?: string | null;
  duration_seconds: number;
  is_billable: boolean;
  is_running: boolean;
}

export interface RealtimeNotif {
  id: number;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface Invitation {
  id: number;
  email: string;
  role: string;
  token: string;
  expires_at: string;
  accepted_at?: string | null;
}

export interface DashboardData {
  counts: Record<'clients' | 'employees' | 'products' | 'services' | 'users' | 'projects', number>;
  tasks_by_status: Partial<Record<KanbanColumnStatus, number>>;
  hours_this_month: { total: number; billable: number };
  low_stock: { id: number; identifiant: string; nom: string; quantite_stock: number; disponibilite: string }[];
}
