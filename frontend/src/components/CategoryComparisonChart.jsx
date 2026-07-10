import Plot from 'react-plotly.js'

export default function CategoryComparisonChart({ figure }) {
  if (!figure) return <p>Not enough data yet to compare months.</p>

  return (
    <Plot
      data={figure.data}
      layout={{ ...figure.layout, autosize: true, height: 340 }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  )
}
