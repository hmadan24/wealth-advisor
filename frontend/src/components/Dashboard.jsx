import { useState } from 'react'
import { 
  PieChart, Pie, Cell, ResponsiveContainer, 
  BarChart, Bar, XAxis, YAxis, Tooltip,
  Treemap
} from 'recharts'
import { 
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle2, 
  Lightbulb, ChevronRight, ArrowUpRight, ArrowDownRight,
  Wallet, Target, Shield, Sparkles, Plus, Trash2, X
} from 'lucide-react'
import { apiUrl } from '../config'

const COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

function Dashboard({ data, showManualEntry, setShowManualEntry, onRefresh }) {
  const [activeTab, setActiveTab] = useState('overview')
  
  const { summary, holdings = [], asset_allocation, amc_allocation, insights, investor } = data
  
  // Extract manual holdings from backend data (marked with source: "manual")
  const manualHoldings = holdings.filter(h => h.source === 'manual')

  const formatCurrency = (amount) => {
    if (amount >= 10000000) {
      return `₹${(amount / 10000000).toFixed(2)} Cr`
    } else if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(2)} L`
    }
    return `₹${amount.toLocaleString('en-IN')}`
  }

  // Calculate totals including manual holdings
  const manualTotalValue = manualHoldings.reduce((sum, h) => sum + (h.current_value || 0), 0)
  const totalPortfolioValue = (summary.total_value || 0) + manualTotalValue
  const totalSchemeCount = (summary.scheme_count || 0) + manualHoldings.length

  // Combine asset allocation with manual holdings
  const getCombinedAssetAllocation = () => {
    const allocationMap = {}
    
    // Add backend asset allocation
    asset_allocation.forEach(item => {
      const key = item.asset_class.toLowerCase()
      allocationMap[key] = {
        asset_class: item.asset_class,
        value: item.value || 0,
        scheme_count: item.scheme_count || 0
      }
    })
    
    // Add manual holdings
    manualHoldings.forEach(h => {
      const key = h.asset_class.toLowerCase()
      if (!allocationMap[key]) {
        allocationMap[key] = {
          asset_class: h.asset_class.charAt(0).toUpperCase() + h.asset_class.slice(1).replace('_', ' '),
          value: 0,
          scheme_count: 0
        }
      }
      allocationMap[key].value += h.current_value || 0
      allocationMap[key].scheme_count += 1
    })
    
    // Calculate percentages
    const total = Object.values(allocationMap).reduce((sum, item) => sum + item.value, 0)
    return Object.values(allocationMap)
      .map(item => ({
        ...item,
        percentage: total > 0 ? Math.round((item.value / total) * 10000) / 100 : 0
      }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value)
  }

  const combinedAssetAllocation = getCombinedAssetAllocation()

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Wallet },
    { id: 'holdings', label: 'Holdings', icon: Target },
    { id: 'insights', label: 'Insights', icon: Lightbulb },
  ]

  const handleAddManualHolding = async (holding) => {
    try {
      const response = await fetch(apiUrl('/api/manual-entry'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify(holding)
      })
      
      if (response.ok) {
        // Refresh portfolio data to show the new entry
        if (onRefresh) {
          await onRefresh()
        }
    setShowManualEntry(false)
      } else {
        console.error('Failed to add manual entry')
      }
    } catch (err) {
      console.error('Failed to add manual entry:', err)
    }
  }

  const handleDeleteManualHolding = async (schemeName) => {
    try {
      const response = await fetch(apiUrl(`/api/manual-entry/${encodeURIComponent(schemeName)}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      })
      
      if (response.ok) {
        // Refresh portfolio data to reflect deletion
        if (onRefresh) {
          await onRefresh()
        }
      } else {
        console.error('Failed to delete manual entry')
      }
    } catch (err) {
      console.error('Failed to delete manual entry:', err)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Manual Entry Modal - rendered at Dashboard level so it's always accessible */}
      {showManualEntry && (
        <ManualEntryModal
          onClose={() => setShowManualEntry(false)}
          onAdd={handleAddManualHolding}
          defaultAssetClass="equity"
        />
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4">
        <SummaryCard
          title="Portfolio Value"
          value={formatCurrency(totalPortfolioValue)}
          icon={Wallet}
          color="wealth"
        />
        <SummaryCard
          title="Schemes"
          value={totalSchemeCount}
          subtitle={`${summary.folio_count || 0} folios${manualHoldings.length > 0 ? ` + ${manualHoldings.length} manual` : ''}`}
          icon={Shield}
          color="purple"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-surface-800 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap
              border-b-2 transition-all
              ${activeTab === tab.id 
                ? 'border-wealth-500 text-wealth-400' 
                : 'border-transparent text-surface-200/60 hover:text-white'
              }
            `}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="animate-fade-in">
        {activeTab === 'overview' && (
          <OverviewTab 
            assetAllocation={combinedAssetAllocation} 
            amcAllocation={amc_allocation}
            holdings={holdings}
            manualHoldings={manualHoldings}
          />
        )}
        {activeTab === 'holdings' && (
          <HoldingsTab 
            holdings={holdings} 
            manualHoldings={manualHoldings}
            onDeleteManual={handleDeleteManualHolding}
            setShowManualEntry={setShowManualEntry}
          />
        )}
        {activeTab === 'insights' && (
          <InsightsTab insights={insights} />
        )}
      </div>
    </div>
  )
}

function SummaryCard({ title, value, change, subtitle, icon: Icon, color }) {
  const colorClasses = {
    wealth: 'from-wealth-500/20 to-wealth-600/10 border-wealth-500/30',
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30',
    red: 'from-red-500/20 to-red-600/10 border-red-500/30',
    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30',
  }

  const iconColors = {
    wealth: 'text-wealth-400',
    blue: 'text-blue-400',
    red: 'text-red-400',
    purple: 'text-purple-400',
  }

  return (
    <div className={`glass-card rounded-xl p-4 bg-gradient-to-br ${colorClasses[color]}`}>
      <div className="flex items-start justify-between mb-3">
        <Icon className={`w-5 h-5 ${iconColors[color]}`} />
        {change !== undefined && (
          <span className={`
            flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full
            ${change >= 0 ? 'bg-wealth-500/20 text-wealth-400' : 'bg-red-500/20 text-red-400'}
          `}>
            {change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
      <p className="text-surface-200/60 text-xs mb-1">{title}</p>
      <p className="font-display text-xl font-bold tabular-nums">{value}</p>
      {subtitle && <p className="text-surface-200/40 text-xs mt-1">{subtitle}</p>}
    </div>
  )
}

function HealthScore({ score }) {
  if (!score) return null

  const gradeColors = {
    A: 'from-wealth-500 to-wealth-600',
    B: 'from-blue-500 to-blue-600',
    C: 'from-yellow-500 to-orange-500',
    D: 'from-red-500 to-red-600',
  }

  return (
    <div className="flex items-center gap-3">
      <div className="text-right">
        <p className="text-xs text-surface-200/60">Portfolio Health</p>
        <p className="text-sm font-medium">{score.verdict}</p>
      </div>
      <div className={`
        w-14 h-14 rounded-xl bg-gradient-to-br ${gradeColors[score.grade]}
        flex items-center justify-center font-display text-2xl font-bold
      `}>
        {score.grade}
      </div>
    </div>
  )
}

function OverviewTab({ assetAllocation, amcAllocation, holdings, manualHoldings = [] }) {
  // Map asset class names to display names (same as Holdings tab)
  const getDisplayName = (assetClass) => {
    const nameMap = {
      'other': 'Mutual Funds',
      'equity': 'Equity',
      'mutual_funds': 'Mutual Funds',
      'us_equity': 'US Equity',
      'crypto': 'Crypto',
      'cash': 'Cash',
      'debt': 'Debt',
      'gold': 'Gold',
      'hybrid': 'Hybrid',
    }
    return nameMap[assetClass.toLowerCase()] || assetClass
  }

  // Normalize asset allocation data
  const normalizedAllocation = assetAllocation.map(item => ({
    ...item,
    asset_class: item.asset_class.toLowerCase() === 'other' ? 'Mutual Funds' : item.asset_class
  }))

  // All holdings already include manual entries from backend
  const allHoldings = [...holdings].sort((a, b) => 
    (b.current_value || 0) - (a.current_value || 0)
  )

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      {/* Asset Allocation Chart */}
      <div className="glass-card rounded-2xl p-6">
        <div className="flex items-start justify-between mb-4">
          <h3 className="font-display font-semibold">Asset Allocation</h3>
          <div className="flex flex-col gap-1">
            {normalizedAllocation.map((asset, index) => (
              <div key={asset.asset_class} className="flex items-center gap-2 text-sm">
                <div 
                  className="w-2.5 h-2.5 rounded-full" 
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-surface-200/70 text-xs">{asset.asset_class}</span>
                <span className="font-medium text-xs">{asset.percentage}%</span>
              </div>
            ))}
          </div>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={normalizedAllocation}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
                nameKey="asset_class"
              >
                {normalizedAllocation.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value) => `₹${value.toLocaleString('en-IN')}`}
                contentStyle={{ 
                  background: '#18181b', 
                  border: '1px solid #3f3f46',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AMC Distribution */}
      <div className="glass-card rounded-2xl p-6">
        <h3 className="font-display font-semibold mb-4">AMC Distribution</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={amcAllocation.slice(0, 6)} layout="vertical">
              <XAxis type="number" hide />
              <YAxis 
                type="category" 
                dataKey="amc" 
                width={100}
                tick={{ fill: '#a1a1aa', fontSize: 11 }}
                tickFormatter={(value) => value.length > 15 ? value.substring(0, 15) + '...' : value}
              />
              <Tooltip 
                formatter={(value) => `₹${value.toLocaleString('en-IN')}`}
                contentStyle={{ 
                  background: '#18181b', 
                  border: '1px solid #3f3f46',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Bar dataKey="value" fill="#22c55e" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Holdings */}
      <div className="glass-card rounded-2xl p-6 lg:col-span-2">
        <h3 className="font-display font-semibold mb-4">Top 5 Holdings</h3>
        <div className="space-y-3">
          {allHoldings.slice(0, 5).map((holding, index) => (
            <div 
              key={holding.isin || holding.scheme_name || index}
              className="flex items-center gap-4 p-3 rounded-xl bg-surface-900/50 hover:bg-surface-800/50 transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-wealth-500/20 flex items-center justify-center text-wealth-400 font-mono text-sm">
                {index + 1}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{holding.scheme_name}</p>
                <p className="text-xs text-surface-200/60">
                  {holding.amc || 'Manual'}
                  {holding.source === 'manual' && <span className="ml-2 text-surface-200/40">• manual</span>}
                </p>
              </div>
              <div className="text-right">
                <p className="font-mono font-medium">₹{(holding.current_value || 0).toLocaleString('en-IN')}</p>
                <p className={`text-xs ${(holding.percentage_return || 0) >= 0 ? 'text-wealth-400' : 'text-red-400'}`}>
                  {(holding.percentage_return || 0) >= 0 ? '+' : ''}{(holding.percentage_return || 0).toFixed(1)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function HoldingsTab({ holdings, manualHoldings, onDeleteManual, setShowManualEntry }) {
  const [sortBy, setSortBy] = useState('value')
  const [filterClass, setFilterClass] = useState('all')

  // Predefined asset class tabs with display names
  const assetClassTabs = [
    { key: 'all', label: 'All' },
    { key: 'equity', label: 'Equity' },
    { key: 'mutual_funds', label: 'Mutual Funds' },
    { key: 'us_equity', label: 'US Equity' },
    { key: 'crypto', label: 'Crypto' },
    { key: 'cash', label: 'Cash' },
    { key: 'debt', label: 'Debt' },
    { key: 'gold', label: 'Gold' },
  ]

  // Map old "other" to "mutual_funds"
  const normalizeAssetClass = (cls) => {
    if (cls === 'other') return 'mutual_funds'
    return cls
  }

  // All holdings already include manual entries (source: "manual") from backend
  // No need to add manualHoldings separately as they're already in holdings
  const allHoldings = holdings.map(h => ({ ...h, asset_class: normalizeAssetClass(h.asset_class) }))

  const filteredHoldings = allHoldings
    .filter(h => filterClass === 'all' || h.asset_class === filterClass)
    .sort((a, b) => {
      if (sortBy === 'value') return b.current_value - a.current_value
      if (sortBy === 'returns') return b.percentage_return - a.percentage_return
      return 0
    })

  // Get counts for each tab
  const getCounts = (key) => {
    if (key === 'all') return allHoldings.length
    return allHoldings.filter(h => h.asset_class === key).length
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-4 items-center">
        <div className="flex gap-2 flex-wrap">
          {assetClassTabs.map((tab) => {
            const count = getCounts(tab.key)
            return (
              <button
                key={tab.key}
                onClick={() => setFilterClass(tab.key)}
                className={`
                  px-3 py-1.5 rounded-lg text-sm transition-all flex items-center gap-1.5
                  ${filterClass === tab.key 
                    ? 'bg-wealth-500 text-white' 
                    : 'bg-surface-800 text-surface-200/70 hover:bg-surface-200/10'
                  }
                `}
              >
                {tab.label}
                {count > 0 && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                    filterClass === tab.key ? 'bg-white/20' : 'bg-surface-200/10'
                  }`}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Holdings Table */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="table-scroll">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-800 text-left text-xs text-surface-200/60 uppercase tracking-wider">
                <th className="px-4 py-3 font-medium">Scheme</th>
                <th className="px-4 py-3 font-medium text-right">Units</th>
                <th className="px-4 py-3 font-medium text-right">NAV</th>
                <th className="px-4 py-3 font-medium text-right">Value</th>
                <th className="px-4 py-3 font-medium text-right">Returns</th>
                <th className="px-4 py-3 font-medium text-right w-10"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-800/50">
              {filteredHoldings.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-4 py-12 text-center text-surface-200/50">
                    <p>No holdings in this category</p>
                    <button
                      onClick={() => setShowManualEntry(true)}
                      className="mt-2 text-blue-400 hover:underline"
                    >
                      Add manual entry
                    </button>
                  </td>
                </tr>
              ) : filteredHoldings.map((holding, index) => (
                <tr key={holding.isin || holding.scheme_name || index} className="hover:bg-surface-800/30 transition-colors">
                  <td className="px-4 py-4">
                    <div className="max-w-xs">
                      <p className="font-medium truncate">{holding.scheme_name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-surface-200/50">{holding.amc || 'Manual'}</span>
                        <span className={`
                          text-xs px-1.5 py-0.5 rounded capitalize
                          ${holding.asset_class === 'equity' ? 'bg-wealth-500/20 text-wealth-400' : ''}
                          ${holding.asset_class === 'mutual_funds' ? 'bg-purple-500/20 text-purple-400' : ''}
                          ${holding.asset_class === 'us_equity' ? 'bg-blue-500/20 text-blue-400' : ''}
                          ${holding.asset_class === 'crypto' ? 'bg-orange-500/20 text-orange-400' : ''}
                          ${holding.asset_class === 'cash' ? 'bg-green-500/20 text-green-400' : ''}
                          ${holding.asset_class === 'debt' ? 'bg-cyan-500/20 text-cyan-400' : ''}
                          ${holding.asset_class === 'gold' ? 'bg-yellow-500/20 text-yellow-400' : ''}
                          ${holding.asset_class === 'hybrid' ? 'bg-pink-500/20 text-pink-400' : ''}
                        `}>
                          {holding.asset_class === 'mutual_funds' ? 'MF' : 
                           holding.asset_class === 'us_equity' ? 'US' : 
                           holding.asset_class}
                        </span>
                        {holding.source === 'manual' && <span className="text-xs text-surface-200/30">manual</span>}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right font-mono text-sm">
                    {holding.units.toFixed(3)}
                  </td>
                  <td className="px-4 py-4 text-right font-mono text-sm text-surface-200/70">
                    ₹{holding.nav.toFixed(2)}
                  </td>
                  <td className="px-4 py-4 text-right font-mono font-medium">
                    ₹{holding.current_value.toLocaleString('en-IN')}
                  </td>
                  <td className="px-4 py-4 text-right">
                    <div className={`
                      inline-flex items-center gap-1 font-mono text-sm
                      ${holding.percentage_return >= 0 ? 'text-wealth-400' : 'text-red-400'}
                    `}>
                      {holding.percentage_return >= 0 
                        ? <ArrowUpRight className="w-3 h-3" /> 
                        : <ArrowDownRight className="w-3 h-3" />
                      }
                      {Math.abs(holding.percentage_return).toFixed(1)}%
                    </div>
                    <p className="text-xs text-surface-200/50 mt-0.5">
                      ₹{holding.absolute_return.toLocaleString('en-IN')}
                    </p>
                  </td>
                  <td className="px-4 py-4 text-right">
                    {holding.source === 'manual' && onDeleteManual && (
                      <button
                        onClick={() => onDeleteManual(holding.scheme_name)}
                        className="p-1.5 text-surface-200/40 hover:text-red-400 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function ManualEntryModal({ onClose, onAdd, defaultAssetClass }) {
  const [formData, setFormData] = useState({
    scheme_name: '',
    asset_class: defaultAssetClass,
    units: '',
    purchase_nav: '',
    current_nav: '',
    amc: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const assetClassOptions = [
    { key: 'equity', label: 'Equity (Indian)' },
    { key: 'mutual_funds', label: 'Mutual Funds' },
    { key: 'us_equity', label: 'US Equity' },
    { key: 'crypto', label: 'Crypto' },
    { key: 'cash', label: 'Cash / FD' },
    { key: 'debt', label: 'Debt / Bonds' },
    { key: 'gold', label: 'Gold' },
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Prevent double submission
    if (isSubmitting) return
    setIsSubmitting(true)
    
    const units = parseFloat(formData.units) || 0
    const purchaseNav = parseFloat(formData.purchase_nav) || 0
    const currentNav = parseFloat(formData.current_nav) || 0
    const invested = units * purchaseNav
    const currentValue = units * currentNav
    const absoluteReturn = currentValue - invested
    const pctReturn = invested > 0 ? (absoluteReturn / invested) * 100 : 0

    await onAdd({
      scheme_name: formData.scheme_name,
      asset_class: formData.asset_class,
      units: units,
      nav: currentNav,
      current_value: currentValue,
      invested_amount: invested,
      absolute_return: absoluteReturn,
      percentage_return: pctReturn,
      amc: formData.amc || 'Manual',
      isin: '',
      folio: '',
      valuation_date: new Date().toISOString().split('T')[0],
    })
    
    // Note: setIsSubmitting(false) not needed as modal closes after successful add
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="glass-card rounded-2xl p-6 w-full max-w-md relative animate-fade-in">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 text-surface-200/60 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>
        
        <h3 className="font-display text-xl font-semibold mb-4">Add Manual Entry</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-surface-200/70 mb-1">Name *</label>
            <input
              type="text"
              required
              value={formData.scheme_name}
              onChange={(e) => setFormData({ ...formData, scheme_name: e.target.value })}
              placeholder="e.g., Apple Inc, Bitcoin, SBI FD"
              className="w-full px-3 py-2 rounded-lg bg-surface-900 border border-surface-800 text-white placeholder-surface-200/40 focus:outline-none focus:border-wealth-500/50"
            />
          </div>

          <div>
            <label className="block text-sm text-surface-200/70 mb-1">Asset Class *</label>
            <select
              value={formData.asset_class}
              onChange={(e) => setFormData({ ...formData, asset_class: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-surface-900 border border-surface-800 text-white focus:outline-none focus:border-wealth-500/50"
            >
              {assetClassOptions.map(opt => (
                <option key={opt.key} value={opt.key}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-surface-200/70 mb-1">Units/Qty *</label>
              <input
                type="number"
                required
                step="any"
                value={formData.units}
                onChange={(e) => setFormData({ ...formData, units: e.target.value })}
                placeholder="10"
                className="w-full px-3 py-2 rounded-lg bg-surface-900 border border-surface-800 text-white placeholder-surface-200/40 focus:outline-none focus:border-wealth-500/50"
              />
            </div>
            <div>
              <label className="block text-sm text-surface-200/70 mb-1">Broker/Platform</label>
              <input
                type="text"
                value={formData.amc}
                onChange={(e) => setFormData({ ...formData, amc: e.target.value })}
                placeholder="e.g., Vested, Coinbase"
                className="w-full px-3 py-2 rounded-lg bg-surface-900 border border-surface-800 text-white placeholder-surface-200/40 focus:outline-none focus:border-wealth-500/50"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-surface-200/70 mb-1">Buy Price *</label>
              <input
                type="number"
                required
                step="any"
                value={formData.purchase_nav}
                onChange={(e) => setFormData({ ...formData, purchase_nav: e.target.value })}
                placeholder="150.00"
                className="w-full px-3 py-2 rounded-lg bg-surface-900 border border-surface-800 text-white placeholder-surface-200/40 focus:outline-none focus:border-wealth-500/50"
              />
            </div>
            <div>
              <label className="block text-sm text-surface-200/70 mb-1">Current Price *</label>
              <input
                type="number"
                required
                step="any"
                value={formData.current_nav}
                onChange={(e) => setFormData({ ...formData, current_nav: e.target.value })}
                placeholder="175.00"
                className="w-full px-3 py-2 rounded-lg bg-surface-900 border border-surface-800 text-white placeholder-surface-200/40 focus:outline-none focus:border-wealth-500/50"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded-lg bg-surface-800 text-surface-200 hover:bg-surface-200/10 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`flex-1 px-4 py-2 rounded-lg transition-colors ${
                isSubmitting 
                  ? 'bg-surface-700 text-surface-400 cursor-not-allowed' 
                  : 'bg-wealth-500 text-white hover:bg-wealth-600'
              }`}
            >
              {isSubmitting ? 'Adding...' : 'Add Entry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function InsightsTab({ insights }) {
  if (!insights) return null

  const { summary_insights, actionables, risks, opportunities } = insights

  return (
    <div className="space-y-6">
      {/* Actionables */}
      {actionables?.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-display font-semibold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-wealth-400" />
            Recommended Actions
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            {actionables.map((action, index) => (
              <div 
                key={index}
                className="glass-card rounded-xl p-4 border-l-4 border-wealth-500"
              >
                <div className="flex items-start gap-3">
                  <div className={`
                    px-2 py-1 rounded text-xs font-medium uppercase
                    ${action.priority === 'high' ? 'bg-red-500/20 text-red-400' : ''}
                    ${action.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' : ''}
                    ${action.priority === 'low' ? 'bg-blue-500/20 text-blue-400' : ''}
                  `}>
                    {action.priority}
                  </div>
                </div>
                <h4 className="font-medium mt-2">{action.action}</h4>
                <p className="text-sm text-surface-200/60 mt-1">{action.description}</p>
                {action.impact && (
                  <p className="text-xs text-wealth-400 mt-2">
                    Impact: {action.impact}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risks */}
      {risks?.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-display font-semibold flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            Risk Alerts
          </h3>
          <div className="space-y-3">
            {risks.map((risk, index) => (
              <div 
                key={index}
                className={`
                  glass-card rounded-xl p-4 border-l-4
                  ${risk.severity === 'high' ? 'border-red-500' : ''}
                  ${risk.severity === 'medium' ? 'border-yellow-500' : ''}
                  ${risk.severity === 'low' ? 'border-blue-500' : ''}
                `}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h4 className="font-medium">{risk.title}</h4>
                    <p className="text-sm text-surface-200/60 mt-1">{risk.description}</p>
                    {risk.recommendation && (
                      <p className="text-sm text-surface-200/80 mt-2 flex items-start gap-2">
                        <ChevronRight className="w-4 h-4 text-wealth-400 flex-shrink-0 mt-0.5" />
                        {risk.recommendation}
                      </p>
                    )}
                  </div>
                  <span className={`
                    text-xs px-2 py-1 rounded-full font-medium uppercase flex-shrink-0
                    ${risk.severity === 'high' ? 'bg-red-500/20 text-red-400' : ''}
                    ${risk.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' : ''}
                    ${risk.severity === 'low' ? 'bg-blue-500/20 text-blue-400' : ''}
                  `}>
                    {risk.severity}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary Insights */}
      {summary_insights?.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-display font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-blue-400" />
            Portfolio Summary
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            {summary_insights.map((insight, index) => (
              <div key={index} className="glass-card rounded-xl p-4">
                <h4 className="font-medium text-sm text-surface-200/80">{insight.title}</h4>
                <p className="text-sm text-surface-200/60 mt-1">{insight.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Opportunities */}
      {opportunities?.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-display font-semibold flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-purple-400" />
            Review Opportunities
          </h3>
          <div className="space-y-2">
            {opportunities.map((opp, index) => (
              <div key={index} className="glass-card rounded-xl p-4 flex items-center gap-4">
                <div className="flex-1">
                  <p className="font-medium text-sm">{opp.fund}</p>
                  <p className="text-xs text-surface-200/60 mt-0.5">{opp.suggestion}</p>
                </div>
                <span className={`
                  font-mono text-sm
                  ${parseFloat(opp.return) >= 0 ? 'text-wealth-400' : 'text-red-400'}
                `}>
                  {opp.return}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard

