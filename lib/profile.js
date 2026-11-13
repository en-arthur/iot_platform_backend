import { createClient } from '@/lib/supabase/client';

export const ROLE_LABELS = {
  hardware_engineer: 'Hardware Engineer',
  software_developer: 'Software Developer',
  founder: 'Founder / Product Lead',
  other: 'Member',
};

export function roleLabel(role) {
  if (!role) return '';
  return ROLE_LABELS[role] || role;
}

export function initialsOf(value) {
  const words = (value || '').trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return '';
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[words.length - 1][0]).toUpperCase();
}

/**
 * Resolve the signed-in user's display identity from Supabase auth plus the
 * profiles row written during onboarding. Returns null when nobody is signed in.
 */
export async function loadIdentity() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return null;

  const email = user.email || '';
  let name = user.user_metadata?.full_name || user.user_metadata?.name || '';
  let role = user.user_metadata?.role || '';

  try {
    const { data: profile } = await supabase
      .from('profiles')
      .select('full_name, role')
      .eq('id', user.id)
      .maybeSingle();
    if (profile?.full_name) name = profile.full_name;
    if (profile?.role) role = profile.role;
  } catch {
    // Profile row is optional; fall back to auth metadata.
  }

  if (!name && email) name = email.split('@')[0];

  return {
    name: name || 'Account',
    role: roleLabel(role) || 'Signed in',
    email,
  };
}
