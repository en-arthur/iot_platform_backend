import { createServerClient } from '@supabase/ssr';
import { NextResponse } from 'next/server';

/**
 * Updates the user session in middleware
 * @param {import('next/server').NextRequest} request
 */
export async function updateSession(request) {
  let supabaseResponse = NextResponse.next({
    request,
  });

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://mock.supabase.co';
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'mock-anon-key';

  // If using mocks, pass through with simulated session or bypass
  const useMocks = process.env.NEXT_PUBLIC_USE_MOCKS === 'true';

  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        supabaseResponse = NextResponse.next({
          request,
        });
        cookiesToSet.forEach(({ name, value, options }) =>
          supabaseResponse.cookies.set(name, value, options)
        );
      },
    },
  });

  const path = request.nextUrl.pathname;
  const isAuthRoute = path.startsWith('/sign-in') || path.startsWith('/sign-up') || path.startsWith('/forgot-password') || path.startsWith('/reset-password');
  const isProtectedRoute = path.startsWith('/app');

  let user = null;
  if (!useMocks) {
    const { data } = await supabase.auth.getUser();
    user = data?.user;
  } else {
    // When in mock mode, check if a mock auth cookie exists
    const mockAuth = request.cookies.get('ai_iot_mock_auth')?.value;
    if (mockAuth) {
      user = { id: 'mock-user-123', email: 'engineer@example.com' };
    }
  }

  // Redirect signed-in users away from auth pages
  if (user && isAuthRoute) {
    const redirectUrl = request.nextUrl.searchParams.get('redirect') || '/app/projects';
    return NextResponse.redirect(new URL(redirectUrl, request.url));
  }

  // Protect /app/* routes
  if (!user && isProtectedRoute) {
    const redirectUrl = new URL('/sign-in', request.url);
    redirectUrl.searchParams.set('redirect', path);
    return NextResponse.redirect(redirectUrl);
  }

  return supabaseResponse;
}
