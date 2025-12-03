import { useState } from 'react'
import { Phone, Loader2, Shield, Lock } from 'lucide-react'
import { apiUrl } from '../config'

function Login({ onLogin }) {
  const [step, setStep] = useState('phone') // 'phone' or 'otp'
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSendOTP = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await fetch(apiUrl('/api/auth/send-otp'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone })
      })

      const result = await response.json()

      if (result.success) {
        setStep('otp')
      } else {
        setError(result.message || 'Failed to send OTP')
      }
    } catch (err) {
      setError('Failed to connect to server')
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerifyOTP = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await fetch(apiUrl('/api/auth/verify-otp'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, otp })
      })

      if (response.ok) {
        const result = await response.json()
        onLogin(result.access_token, result.phone)
      } else {
        setError('Invalid OTP')
      }
    } catch (err) {
      setError('Failed to verify OTP')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-950 text-white bg-grid flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-wealth-500 to-wealth-700 flex items-center justify-center glow-green">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="font-display text-3xl font-bold mb-2">Wealth Advisor</h1>
          <p className="text-surface-200/60">Secure login to access your portfolio</p>
        </div>

        {/* Login Card */}
        <div className="glass-card rounded-2xl p-8 glow-green">
          {step === 'phone' ? (
            <form onSubmit={handleSendOTP} className="space-y-6">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-surface-200 mb-2">
                  <Phone className="w-4 h-4" />
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="7899021114"
                  className="w-full px-4 py-3 rounded-xl bg-surface-900 border border-surface-800 
                           text-white placeholder-surface-200/40 font-mono
                           focus:outline-none focus:ring-2 focus:ring-wealth-500/50 focus:border-wealth-500/50
                           transition-all"
                  required
                  pattern="[0-9]{10}"
                  maxLength="10"
                />
                <p className="text-xs text-surface-200/50 mt-2">
                  Enter your 10-digit mobile number
                </p>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || phone.length !== 10}
                className={`
                  w-full py-3 px-6 rounded-xl font-semibold text-white
                  transition-all duration-300 flex items-center justify-center gap-2
                  ${isLoading || phone.length !== 10
                    ? 'bg-surface-800 text-surface-200/40 cursor-not-allowed'
                    : 'bg-gradient-to-r from-wealth-500 to-wealth-600 hover:from-wealth-400 hover:to-wealth-500 glow-green'
                  }
                `}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Sending OTP...
                  </>
                ) : (
                  <>
                    <Lock className="w-5 h-5" />
                    Send OTP
                  </>
                )}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOTP} className="space-y-6">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-surface-200 mb-2">
                  <Lock className="w-4 h-4" />
                  Enter OTP
                </label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  placeholder="1234"
                  className="w-full px-4 py-3 rounded-xl bg-surface-900 border border-surface-800 
                           text-white placeholder-surface-200/40 font-mono text-2xl tracking-widest text-center
                           focus:outline-none focus:ring-2 focus:ring-wealth-500/50 focus:border-wealth-500/50
                           transition-all"
                  required
                  maxLength="6"
                  autoFocus
                />
                <p className="text-xs text-surface-200/50 mt-2 text-center">
                  OTP sent to {phone} • 
                  <button
                    type="button"
                    onClick={() => setStep('phone')}
                    className="text-wealth-400 hover:underline ml-1"
                  >
                    Change number
                  </button>
                </p>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div className="space-y-3">
                <button
                  type="submit"
                  disabled={isLoading || otp.length < 4}
                  className={`
                    w-full py-3 px-6 rounded-xl font-semibold text-white
                    transition-all duration-300 flex items-center justify-center gap-2
                    ${isLoading || otp.length !== 4
                      ? 'bg-surface-800 text-surface-200/40 cursor-not-allowed'
                      : 'bg-gradient-to-r from-wealth-500 to-wealth-600 hover:from-wealth-400 hover:to-wealth-500 glow-green'
                    }
                  `}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    'Verify & Login'
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => { setStep('phone'); setOtp(''); setError(''); }}
                  className="w-full py-2 text-sm text-surface-200/60 hover:text-white transition-colors"
                >
                  Back to phone number
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Demo credentials info */}
        <div className="mt-6 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
          <p className="text-sm text-blue-400 text-center">
            <strong>Demo Credentials:</strong> Phone: 7899021114 • OTP: 1234
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login

