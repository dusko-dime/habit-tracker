import { useEffect, useState, type FormEvent } from 'react'

type Habit = {
  id: number
  name: string
  created_at: string
  done_today: boolean
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) throw new Error(`Request failed: ${res.status}`)
  return res.json() as Promise<T>
}

function App() {
  const [habits, setHabits] = useState<Habit[]>([])
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    request<Habit[]>('/api/habits')
      .then(setHabits)
      .catch((e: Error) => setError(e.message))
  }, [])

  async function addHabit(e: FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    try {
      const habit = await request<Habit>('/api/habits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmed }),
      })
      setHabits((prev) => [...prev, habit])
      setName('')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function checkHabit(id: number) {
    try {
      const updated = await request<Habit>(`/api/habits/${id}/check`, {
        method: 'POST',
      })
      setHabits((prev) => prev.map((h) => (h.id === id ? updated : h)))
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <main>
      <h1>Habit Tracker</h1>
      {error && <p role="alert">{error}</p>}
      <form onSubmit={addHabit}>
        <input
          aria-label="Habit name"
          placeholder="New habit"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button type="submit">Add</button>
      </form>
      <ul>
        {habits.map((habit) => (
          <li key={habit.id}>
            <span>{habit.name}</span>{' '}
            <button
              onClick={() => checkHabit(habit.id)}
              disabled={habit.done_today}
            >
              {habit.done_today ? 'Done ✓' : 'Done today'}
            </button>
          </li>
        ))}
      </ul>
    </main>
  )
}

export default App
