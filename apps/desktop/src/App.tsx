import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

const apiBaseUrl = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'
const conversationStorageKey = 'orbit.activeConversationId'

type DraftTask = {
  title: string | null
  description: string | null
  priority: 'low' | 'medium' | 'high' | null
  deadline: string | null
}

type AgentResponse = {
  conversation_id?: string | null
  proposal?: { draft_task: DraftTask; requires_approval: boolean } | null
  clarification?: { question: string; missing_fields: string[] } | null
  status?: string
  executed_task_id?: number | null
  error?: string
}

type ChatMessage = {
  role: 'assistant' | 'user'
  text: string
}

function formatDeadline(deadline: string | null) {
  if (!deadline) return 'No deadline'

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(deadline))
}

function formatRequestError(error: unknown) {
  if (error instanceof TypeError) {
    return 'Orbit\'s local API is unavailable. Restart Orbit and try again.'
  }
  return error instanceof Error ? error.message : 'Unable to reach Orbit.'
}

function App() {
  const restorationStarted = useRef(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      text: 'What would you like to accomplish?',
    },
  ])
  const [input, setInput] = useState('')
  const [proposal, setProposal] = useState<DraftTask | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(() =>
    localStorage.getItem(conversationStorageKey),
  )
  const [isSending, setIsSending] = useState(false)

  const addAssistantMessage = (text: string) => {
    setMessages((current) => [...current, { role: 'assistant', text }])
  }

  const clearConversation = () => {
    localStorage.removeItem(conversationStorageKey)
    setConversationId(null)
    setProposal(null)
  }

  useEffect(() => {
    if (!conversationId || restorationStarted.current) return
    restorationStarted.current = true

    const restoreConversation = async () => {
      try {
        const response = await fetch(
          `${apiBaseUrl}/agent/conversations/${conversationId}`,
        )
        if (response.status === 404) {
          clearConversation()
          return
        }

        const data = (await response.json()) as AgentResponse
        if (!response.ok) throw new Error('Orbit could not restore the draft.')

        if (data.status === 'cancelled' || data.status === 'executed') {
          clearConversation()
          return
        }
        if (data.proposal) {
          setProposal(data.proposal.draft_task)
          addAssistantMessage('I restored your unfinished task for review.')
        } else if (data.clarification) {
          addAssistantMessage(
            `I restored your unfinished task. ${data.clarification.question}`,
          )
        }
      } catch (error) {
        addAssistantMessage(formatRequestError(error))
      }
    }

    void restoreConversation()
    // Restore only the conversation captured when the application starts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const sendMessage = async (message: string) => {
    setMessages((current) => [...current, { role: 'user', text: message }])
    setIsSending(true)

    try {
      const response = await fetch(`${apiBaseUrl}/agent/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, conversation_id: conversationId }),
      })
      const data = (await response.json()) as AgentResponse

      if (!response.ok || data.error) {
        if (response.status === 404) clearConversation()
        throw new Error(
          data.error ??
            (data as { detail?: string }).detail ??
            'Orbit could not process that message.',
        )
      }

      if (data.conversation_id) {
        localStorage.setItem(conversationStorageKey, data.conversation_id)
        setConversationId(data.conversation_id)
      }

      if (data.clarification) {
        addAssistantMessage(data.clarification.question)
      }

      if (data.proposal) {
        const wasModification = proposal !== null
        setProposal(data.proposal.draft_task)
        addAssistantMessage(
          wasModification
            ? 'I updated the task. Please review it again.'
            : 'I have a task ready for your confirmation.',
        )
      }

      if (data.status === 'cancelled') {
        clearConversation()
        addAssistantMessage('Okay, I will not create that task.')
      }

      if (data.executed_task_id) {
        clearConversation()
        addAssistantMessage(`Task created (ID ${data.executed_task_id}).`)
      }
    } catch (error) {
      addAssistantMessage(formatRequestError(error))
    } finally {
      setIsSending(false)
    }
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const message = input.trim()
    if (!message || isSending) return

    setInput('')
    await sendMessage(message)
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <p className="eyebrow">Orbit</p>
        <h1>Your planning partner</h1>
        <p className="subtitle">Tell Orbit what you want to accomplish.</p>
      </header>

      <section className="conversation" aria-label="Conversation with Orbit">
        {messages.map((message, index) => (
          <p className={`message ${message.role}`} key={`${message.role}-${index}`}>
            {message.text}
          </p>
        ))}

        {proposal && (
          <section className="proposal" aria-label="Task awaiting confirmation">
            <p className="proposal-label">Ready to create</p>
            <h2>{proposal.title}</h2>
            <dl>
              <div>
                <dt>Due</dt>
                <dd>{formatDeadline(proposal.deadline)}</dd>
              </div>
              {proposal.priority && (
                <div>
                  <dt>Priority</dt>
                  <dd>{proposal.priority}</dd>
                </div>
              )}
            </dl>
            <div className="proposal-actions">
              <button type="button" onClick={() => void sendMessage('yes')} disabled={isSending}>
                Approve task
              </button>
              <button
                className="secondary"
                type="button"
                onClick={() => void sendMessage('cancel')}
                disabled={isSending}
              >
                Cancel
              </button>
            </div>
            <p className="proposal-help">Need a change? Describe it in the message box.</p>
          </section>
        )}
      </section>

      <form className="composer" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="message">Message Orbit</label>
        <input
          id="message"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="e.g. Remind me to revise Dijkstra"
          disabled={isSending}
        />
        <button type="submit" disabled={!input.trim() || isSending}>
          {isSending ? 'Sending…' : 'Send'}
        </button>
      </form>
    </main>
  )
}

export default App
