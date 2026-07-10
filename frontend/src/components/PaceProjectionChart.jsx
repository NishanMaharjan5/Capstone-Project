import Plot from 'react-plotly.js'

export default function PaceProjectionChart({ figure }) {
  if (!figure) return <p>Not enough data yet this month to project a pace.</p>

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
