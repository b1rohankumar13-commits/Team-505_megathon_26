import { afterEach, describe, expect, it, vi } from 'vitest';

afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); vi.resetModules(); });

describe('Live-only API client', () => {
  it('fails explicitly when the backend URL is missing', async () => {
    vi.stubEnv('VITE_GREEN_API_URL', '');
    const { getPortfolio } = await import('@/lib/api/client');
    await expect(getPortfolio()).rejects.toThrow('not configured');
  });
  it('never replaces a backend failure with fixtures', async () => {
    vi.stubEnv('VITE_GREEN_API_URL', 'http://localhost:8001');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({detail: 'Models unavailable'}), {status:503})));
    const { getPortfolio } = await import('@/lib/api/client');
    await expect(getPortfolio()).rejects.toThrow('Models unavailable');
  });
  it('uses backend values unchanged', async () => {
    vi.stubEnv('VITE_GREEN_API_URL', 'http://localhost:8001');
    const payload = {customers:1000, potential:{co2eKg:null}};
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), {status:200})));
    const { getPortfolio } = await import('@/lib/api/client');
    expect(await getPortfolio()).toEqual({source:'live', data:payload});
  });
});

describe('Compose API routing', () => {
  it.each([true, false])('selects the correct URL for SSR=%s', async (ssr) => {
    vi.stubEnv('SSR', ssr);
    vi.stubEnv('VITE_GREEN_API_URL', 'http://localhost:8002');
    vi.stubEnv('VITE_GREEN_SSR_API_URL', 'http://backend:8000');
    const { API_BASE_URL } = await import('@/lib/api/client');
    expect(API_BASE_URL).toBe(ssr ? 'http://backend:8000' : 'http://localhost:8002');
  });
});
