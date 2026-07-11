import { useState } from 'react'
import Plot from 'react-plotly.js'
import { formatMoney } from '../utils/receiptMath'

export default function TripDayBreakdown({ figure, receipts }) {
  const [selectedDate, setSelectedDate] = useState(null)

  if (!figure) return <p>Shows up once your trip spans more than one day.</p>

  function handleClick(event) {
    const point = event.points?.[0]
    if (!point) return
    setSelectedDate((prev) => (prev === point.customdata ? null : point.customdata))
  }

  const dayReceipts = selectedDate ? receipts.filter((r) => r.date === selectedDate) : []

  return (
    <div>
      <Plot
        data={figure.data}
        layout={{ ...figure.layout, autosize: true, height: 320 }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
        useResizeHandler
        onClick={handleClick}
      />

      {selectedDate ? (
        <div className="trip-day-drilldown">
          <div className="trip-day-drilldown-header">
            <strong>{selectedDate}</strong>
            <button type="button" className="link-button" onClick={() => setSelectedDate(null)}>
              Clear
            </button>
          </div>
          {dayReceipts.length === 0 ? (
            <p>No receipts on this day.</p>
          ) : (
            <div className="recent-list">
              {dayReceipts.map((r) => (
                <div className="recent-card" key={r._id}>
                  <div>
                    <strong>{r.vendor || 'Unknown vendor'}</strong>
                    <p className="recent-meta">{r.category}</p>
                  </div>
                  <span>{formatMoney(r.total)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <p className="recent-meta">Click a day above to see its receipts.</p>
      )}
    </div>
  )
}
