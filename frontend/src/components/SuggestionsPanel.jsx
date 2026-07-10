import { lazy, Suspense, useState } from 'react'

// Lazy-loaded: pulls in Plotly, same reasoning as InsightsPanel/InsightChart —
// this panel is used from Analytics, which is already lazy-loaded, but keeping
// the split consistent avoids surprises if that ever changes.
const InsightChart = lazy(() => import('./InsightChart'))

export default function SuggestionsPanel({ suggestions, figures }) {
  const [expandedIndex, setExpandedIndex] = useState(null)

  if (!suggestions || suggestions.length === 0) {
    return <p>No suggestions right now — set a few category budgets to unlock these.</p>
  }

  return (
    <div className="insights-list">
      {suggestions.map((suggestion, index) => {
        const isOpen = expandedIndex === index
        const figure = suggestion.chart && figures ? figures[suggestion.chart] : null

        return (
          <div className="insight-item" key={index}>
            <div className="alert info insight-row">
              <span>{suggestion.headline}</span>
              <button
                type="button"
                className="link-button"
                onClick={() => setExpandedIndex(isOpen ? null : index)}
              >
                {isOpen ? 'Hide details' : 'View details'}
              </button>
            </div>

            {isOpen ? (
              <div className="insight-detail">
                <p>{suggestion.reasoning}</p>
                {figure ? (
                  <Suspense fallback={<p>Loading chart...</p>}>
                    <InsightChart figure={figure} />
                  </Suspense>
                ) : null}
              </div>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
