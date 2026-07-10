import Plot from 'react-plotly.js'

export default function BudgetComparisonChart({ figure }) {
  if (!figure) return <p>Set a budget for at least one category to see this chart.</p>

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
