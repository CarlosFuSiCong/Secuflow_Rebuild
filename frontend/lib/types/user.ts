export type User = {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
  last_login: string | null;
  contact_email?: string | null;
  display_name?: string | null;
  avatar?: string | null;
  updated_at?: string;
};

export type UpdateProfilePayload = {
  contact_email?: string;
  first_name?: string;
  last_name?: string;
  avatar?: File | Blob | null;
};


