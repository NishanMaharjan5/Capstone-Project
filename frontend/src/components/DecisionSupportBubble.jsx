import { useEffect, useState } from 'react'
import SuggestionsPanel from './SuggestionsPanel'
import { getDecisionSupport } from '../api/budgets'

export default function DecisionSupportBubble() {
  const [isOpen, setIsOpen] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [figures, setFigures] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false

    async function load() {
      try {
        const data = await getDecisionSupport()
        if (ignore || !data.success) return
        setSuggestions(data.decision_support.suggestions || [])
        setFigures(data.decision_support.figures || null)
      } catch (err) {
        if (!ignore) setError(err.message || 'Could not load decision support')
      }
    }

    load()
    return () => {
      ignore = true
    }
  }, [])

  return (
    <div className="chat-head-wrapper">
      <button
        type="button"
        className={`chat-head-bubble${isOpen ? ' hidden' : ''}`}
        onClick={() => setIsOpen(true)}
        aria-label="Open decision support"
      >
        <span>💡</span>
        {suggestions.length > 0 ? <span className="chat-head-badge">{suggestions.length}</span> : null}
      </button>

      <div className={`chat-head-panel${isOpen ? ' open' : ''}`}>
        <div className="chat-head-panel-header">
          <h2>Decision support</h2>
          <button type="button" className="link-button" onClick={() => setIsOpen(false)} aria-label="Hide decision support">
            Hide
          </button>
        </div>
        <div className="chat-head-panel-body">
          {error ? <div className="alert error">{error}</div> : <SuggestionsPanel suggestions={suggestions} figures={figures} />}
        </div>
      </div>
    </div>
  )
}
