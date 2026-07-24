import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError } from './apiClient'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('apiClient', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('resolves with the parsed JSON body on success', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([{ id: 1, name: 'Hero' }]))
    vi.stubGlobal('fetch', fetchMock)

    const result = await api.listHeroes()

    expect(result).toEqual([{ id: 1, name: 'Hero' }])
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/heroes'),
      expect.objectContaining({ headers: expect.any(Object) }),
    )
  })

  it('throws an ApiError built from the backend error envelope on failure', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(
        { error: { type: 'not_found', message: 'Account 999 not found', details: null } },
        404,
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(api.getAccount(999)).rejects.toMatchObject({
      name: 'ApiError',
      type: 'not_found',
      status: 404,
      message: 'Account 999 not found',
    })
  })

  it('falls back to statusText/unknown_error when the body is not the error envelope', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response('not json', { status: 500, statusText: 'Internal Server Error' }),
    )
    vi.stubGlobal('fetch', fetchMock)

    try {
      await api.getAccount(1)
      expect.unreachable('expected getAccount to throw')
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError)
      const apiErr = err as ApiError
      expect(apiErr.status).toBe(500)
      expect(apiErr.type).toBe('unknown_error')
    }
  })

  it('resolves with undefined for a 204 No Content response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(api.removeHero(1, 2)).resolves.toBeUndefined()
  })

  it('sends a JSON-encoded body on POST requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: 1, display_name: 'carl' }))
    vi.stubGlobal('fetch', fetchMock)

    await api.createAccount({ display_name: 'carl' })

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('POST')
    expect(init.body).toBe(JSON.stringify({ display_name: 'carl' }))
  })
})
