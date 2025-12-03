import { useState, useEffect, useRef } from 'react'
import Login from './components/Login'
import FileUpload from './components/FileUpload'
import Dashboard from './components/Dashboard'
import { TrendingUp, Sparkles, LogOut, User, Plus, FolderOpen, Loader2, Upload, PenLine, ChevronDown, FileText, Trash2 } from 'lucide-react'
import { apiUrl } from './config'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [portfolioData, setPortfolioData] = useState(null)
  const [segments, setSegments] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingPortfolio, setIsLoadingPortfolio] = useState(false)
  const [error, setError] = useState(null)
  const [showUpload, setShowUpload] = useState(false)
  const [showAddMenu, setShowAddMenu] = useState(false)
  const [showManualEntry, setShowManualEntry] = useState(false)
  const addMenuRef = useRef(null)

  // Check for existing auth token on mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    const phone = localStorage.getItem('user_phone')
    if (token && phone) {
      setIsAuthenticated(true)
      setUser({ phone })
      // Load user's portfolio
      loadPortfolio(token)
    }
  }, [])

  const getAuthHeaders = () => {
    const token = localStorage.getItem('auth_token')
    return token ? { 'Authorization': `Bearer ${token}` } : {}
  }

  const loadPortfolio = async (token) => {
    setIsLoadingPortfolio(true)
    try {
      const authToken = token || localStorage.getItem('auth_token')
      
      // Load aggregated portfolio
      const response = await fetch(apiUrl('/api/portfolio'), {
        headers: { 'Authorization': `Bearer ${authToken}` }
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          setPortfolioData(result.data)
          setSegments(Object.keys(result.data.segments || {}))
        }
      }
      
      // Load segments info
      const segmentsResponse = await fetch(apiUrl('/api/portfolio/segments'), {
        headers: { 'Authorization': `Bearer ${authToken}` }
      })
      
      if (segmentsResponse.ok) {
        const segmentsData = await segmentsResponse.json()
        setSegments(segmentsData.segments || [])
      }
    } catch (err) {
      console.error('Failed to load portfolio:', err)
    } finally {
      setIsLoadingPortfolio(false)
    }
  }

  const handleLogin = async (token, phone) => {
    localStorage.setItem('auth_token', token)
    localStorage.setItem('user_phone', phone)
    setIsAuthenticated(true)
    setUser({ phone })
    // Load user's portfolio after login
    await loadPortfolio(token)
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_phone')
    setIsAuthenticated(false)
    setUser(null)
    setPortfolioData(null)
    setSegments([])
    setShowUpload(false)
  }

  const handleUpload = async (file) => {
    setIsLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('password', '')

    try {
      const response = await fetch(apiUrl('/api/upload-cas'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData,
      })

      const result = await response.json()

      if (result.success) {
        setPortfolioData(result.data)
        setSegments(Object.keys(result.data.segments || {}))
        setShowUpload(false)
        setError(null)
      } else {
        setError(result.error || 'Failed to parse file')
      }
    } catch (err) {
      setError('Failed to connect to server. Make sure the backend is running.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleShowUpload = () => {
    setShowUpload(true)
    setError(null)
  }

  const handleResetPortfolio = async () => {
    if (!confirm('Are you sure you want to reset your portfolio? This will delete all uploaded data.')) {
      return
    }
    
    setIsLoading(true)
    try {
      const response = await fetch(apiUrl('/api/portfolio/reset'), {
        method: 'POST',
        headers: getAuthHeaders(),
      })
      
      if (response.ok) {
        setPortfolioData(null)
        setSegments([])
        setShowUpload(false)
        setError(null)
      }
    } catch (err) {
      console.error('Failed to reset portfolio:', err)
    } finally {
      setIsLoading(false)
    }
  }

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />
  }

  // Show loading while fetching portfolio after login
  if (isLoadingPortfolio) {
    return (
      <div className="min-h-screen bg-surface-950 text-white bg-grid flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-wealth-500 animate-spin mx-auto mb-4" />
          <p className="text-surface-200/60">Loading your portfolio...</p>
        </div>
      </div>
    )
  }

  const hasPortfolio = portfolioData && portfolioData.holdings && portfolioData.holdings.length > 0

  return (
    <div className="min-h-screen bg-surface-950 text-white bg-grid">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-card border-b border-surface-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-wealth-500 to-wealth-700 flex items-center justify-center glow-green">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="font-display text-xl font-semibold tracking-tight">
                  Wealth Advisor
                </h1>
                <p className="text-xs text-surface-200/60">Portfolio Intelligence</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Portfolio actions */}
              {hasPortfolio && !showUpload && (
                <div className="flex items-center gap-3">
                  {/* Segments indicator */}
                  <div className="hidden sm:flex items-center gap-2 text-xs text-surface-200/60">
                    <FileText className="w-3.5 h-3.5" />
                    <span>{segments.length} source{segments.length !== 1 ? 's' : ''}</span>
                  </div>
                  
                  {/* Add menu */}
                  <div className="relative" ref={addMenuRef}>
                    <button
                      onClick={() => setShowAddMenu(!showAddMenu)}
                      className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg bg-wealth-500/20 text-wealth-400 hover:bg-wealth-500/30 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                      Add
                      <ChevronDown className={`w-3 h-3 transition-transform ${showAddMenu ? 'rotate-180' : ''}`} />
                    </button>
                    
                    {showAddMenu && (
                      <>
                        <div className="fixed inset-0 z-40" onClick={() => setShowAddMenu(false)} />
                        <div className="absolute right-0 top-full mt-2 w-52 glass-card rounded-xl border border-surface-800 shadow-xl z-50 overflow-hidden">
                          <button
                            onClick={() => {
                              handleShowUpload()
                              setShowAddMenu(false)
                            }}
                            className="w-full flex items-center gap-3 px-4 py-3 text-left text-sm hover:bg-surface-800/50 transition-colors"
                          >
                            <Upload className="w-4 h-4 text-blue-400" />
                            <div>
                              <p className="font-medium">Upload PDF</p>
                              <p className="text-xs text-surface-200/50">CAS or Vested statement</p>
                            </div>
                          </button>
                          <button
                            onClick={() => {
                              setShowManualEntry(true)
                              setShowAddMenu(false)
                            }}
                            className="w-full flex items-center gap-3 px-4 py-3 text-left text-sm hover:bg-surface-800/50 transition-colors border-t border-surface-800"
                          >
                            <PenLine className="w-4 h-4 text-purple-400" />
                            <div>
                              <p className="font-medium">Manual Entry</p>
                              <p className="text-xs text-surface-200/50">Add holding manually</p>
                            </div>
                          </button>
                          <button
                            onClick={() => {
                              handleResetPortfolio()
                              setShowAddMenu(false)
                            }}
                            className="w-full flex items-center gap-3 px-4 py-3 text-left text-sm hover:bg-red-500/10 transition-colors border-t border-surface-800 text-red-400"
                          >
                            <Trash2 className="w-4 h-4" />
                            <div>
                              <p className="font-medium">Reset Portfolio</p>
                              <p className="text-xs text-red-400/50">Delete all data</p>
                            </div>
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
              
              {/* User info & logout */}
              <div className="flex items-center gap-3 pl-4 border-l border-surface-800">
                <div className="flex items-center gap-2 text-sm text-surface-200">
                  <User className="w-4 h-4" />
                  <span className="font-mono">{user?.phone}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 text-surface-200/60 hover:text-red-400 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-wealth-500 animate-spin mx-auto mb-4" />
              <p className="text-surface-200/60">Analyzing portfolio...</p>
            </div>
          </div>
        ) : hasPortfolio && !showUpload ? (
          <Dashboard 
            data={portfolioData} 
            showManualEntry={showManualEntry}
            setShowManualEntry={setShowManualEntry}
            segments={segments}
          />
        ) : (
          <div className="animate-fade-in">
            {/* Hero Section */}
            <div className="text-center mb-12 pt-8">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-wealth-500/10 border border-wealth-500/20 text-wealth-400 text-sm mb-6">
                <Sparkles className="w-4 h-4" />
                <span>AI-Powered Portfolio Analysis</span>
              </div>
              <h2 className="font-display text-4xl sm:text-5xl font-bold mb-4 tracking-tight">
                {hasPortfolio ? 'Add to Your' : 'Understand Your'}
                <span className="text-wealth-400 glow-text"> {hasPortfolio ? 'Portfolio' : 'Wealth'}</span>
              </h2>
              <p className="text-surface-200/70 text-lg max-w-xl mx-auto">
                {hasPortfolio 
                  ? 'Upload another PDF to add more holdings to your portfolio. All sources are automatically aggregated.'
                  : 'Upload your NSDL CAS or Vested statement to get instant insights, actionable recommendations, and a complete view of your investments.'
                }
              </p>
              
              {/* Show existing portfolio option */}
              {hasPortfolio && showUpload && (
                <button
                  onClick={() => setShowUpload(false)}
                  className="mt-4 inline-flex items-center gap-2 text-sm text-wealth-400 hover:text-wealth-300 transition-colors"
                >
                  <FolderOpen className="w-4 h-4" />
                  Back to portfolio
                </button>
              )}
            </div>

            {/* Upload Section */}
            <FileUpload onUpload={handleUpload} isLoading={isLoading} error={error} />

            {/* Features - only show for new users */}
            {!hasPortfolio && (
              <div className="grid md:grid-cols-3 gap-6 mt-16">
                {[
                  {
                    title: 'Unified View',
                    description: 'Aggregate holdings from multiple sources - Indian MF, Equity, and US stocks in one place.',
                    icon: '🎯'
                  },
                  {
                    title: 'Smart Insights',
                    description: 'Get AI-powered recommendations to optimize your portfolio.',
                    icon: '💡'
                  },
                  {
                    title: 'Risk Analysis',
                    description: 'Identify concentration risks, fund overlaps, and rebalancing needs.',
                    icon: '🛡️'
                  }
                ].map((feature, i) => (
                  <div 
                    key={i} 
                    className="glass-card rounded-2xl p-6 hover:border-wealth-500/30 transition-all duration-300"
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    <div className="text-3xl mb-4">{feature.icon}</div>
                    <h3 className="font-display font-semibold text-lg mb-2">{feature.title}</h3>
                    <p className="text-surface-200/60 text-sm">{feature.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-800 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-surface-200/40 text-sm">
            Your data is stored securely and linked to your account.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
