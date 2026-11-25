import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lists, adds and checks habits', async () => {
    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url === '/api/habits' && !init?.method) {
        return Promise.resolve(
          jsonResponse([
            { id: 1, name: 'Read', created_at: '2026-11-25T00:00:00Z', done_today: false },
          ]),
        )
      }
      if (url === '/api/habits' && init?.method === 'POST') {
        return Promise.resolve(
          jsonResponse(
            { id: 2, name: 'Run', created_at: '2026-11-25T00:00:00Z', done_today: false },
            201,
          ),
        )
      }
      if (url === '/api/habits/1/check') {
        return Promise.resolve(
          jsonResponse({ id: 1, name: 'Read', created_at: '2026-11-25T00:00:00Z', done_today: true }),
        )
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`))
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()

    render(<App />)

    expect(await screen.findByText('Read')).toBeInTheDocument()

    await user.type(screen.getByLabelText('Habit name'), 'Run')
    await user.click(screen.getByRole('button', { name: 'Add' }))
    expect(await screen.findByText('Run')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/habits',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ name: 'Run' }) }),
    )

    const [readButton] = screen.getAllByRole('button', { name: 'Done today' })
    await user.click(readButton)
    expect(await screen.findByRole('button', { name: 'Done ✓' })).toBeDisabled()
    expect(fetchMock).toHaveBeenCalledWith('/api/habits/1/check', { method: 'POST' })
  })
})
