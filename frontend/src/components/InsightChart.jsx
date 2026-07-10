import Plot from 'react-plotly.js'

export default function InsightChart({ figure }) {
  return (
    <Plot
      data={figure.data}
      layout={{ ...figure.layout, autosize: true, height: 280 }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  )
}
