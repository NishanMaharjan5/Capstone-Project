import { lazy, Suspense, useState } from 'react'

// Lazy-loaded: pulls in Plotly, which is large — InsightsPanel is used from
// Dashboard (not otherwise a Plotly page), so this must not join the main bundle.
const InsightChart = lazy(() => import('./InsightChart'))

export default function InsightsPanel({ insights, figures, expandable = true }) {
  const [expandedIndex, setExpandedIndex] = useState(null)

  if (!insights || insights.length === 0) {
    return <p>Not enough data yet for insights — add a few more receipts.</p>
  }

  const figureFor = (insight) => (insight.chart && figures ? figures[insight.chart] : null)

  if (!expandable) {
    return (
      <div className="insights-list">
        {insights.map((insight, index) => (
          <div className="alert info" key={index}>
            {insight.message}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="insights-list">
      {insights.map((insight, index) => {
        const isOpen = expandedIndex === index
        const figure = figureFor(insight)

        return (
          <div className="insight-item" key={index}>
            <div className="alert info insight-row">
              <span>{insight.message}</span>
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
                <p>{insight.detail || insight.message}</p>
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
