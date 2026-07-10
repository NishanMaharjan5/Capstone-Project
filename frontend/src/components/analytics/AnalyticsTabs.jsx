const TABS = [
  { key: 'overview', label: 'Overview' },
  { key: 'time', label: 'Time-based' },
  { key: 'category', label: 'Category breakdown' },
  { key: 'vendor', label: 'Vendor' },
]

export default function AnalyticsTabs({ active, onChange }) {
  return (
    <div className="tab-bar" role="tablist">
      {TABS.map((tab) => (
        <button
          key={tab.key}
          type="button"
          role="tab"
          aria-selected={active === tab.key}
          className={`tab-button ${active === tab.key ? 'active' : ''}`}
          onClick={() => onChange(tab.key)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
