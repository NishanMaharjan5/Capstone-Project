import Plot from 'react-plotly.js'

export default function SpendingTrendChart({ figure }) {
  if (!figure) return <p>No monthly data yet.</p>

  return (
    <Plot
      data={figure.data}
      layout={{ ...figure.layout, autosize: true, height: 320 }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  )
}
