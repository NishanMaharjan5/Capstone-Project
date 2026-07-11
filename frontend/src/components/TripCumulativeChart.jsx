import Plot from 'react-plotly.js'

export default function TripCumulativeChart({ figure }) {
  if (!figure) return <p>Trend shows up once your trip spans more than one day.</p>

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
