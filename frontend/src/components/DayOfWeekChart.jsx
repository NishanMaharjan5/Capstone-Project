import Plot from 'react-plotly.js'

export default function DayOfWeekChart({ figure }) {
  if (!figure) return <p>No day-of-week pattern yet.</p>

  return (
    <Plot
      data={figure.data}
      layout={{ ...figure.layout, autosize: true, height: 300 }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  )
}
