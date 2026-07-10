import Plot from 'react-plotly.js'

export default function CategoryBreakdownChart({ figure }) {
  if (!figure) return <p>No category data yet.</p>

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
