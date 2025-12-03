import { useState, useRef } from 'react'
import { Upload, FileText, AlertCircle, Loader2 } from 'lucide-react'

function FileUpload({ onUpload, isLoading, error }) {
  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile?.name?.toLowerCase().endsWith('.pdf')) {
      setFile(droppedFile)
    }
  }

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (file) {
      onUpload(file)
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* File Drop Zone */}
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            relative cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center
            transition-all duration-300 ease-out
            ${isDragging 
              ? 'border-wealth-500 bg-wealth-500/10 scale-[1.02]' 
              : file 
                ? 'border-wealth-500/50 bg-wealth-500/5' 
                : 'border-surface-800 hover:border-surface-200/30 bg-surface-900/50'
            }
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            className="hidden"
          />
          
          {file ? (
            <div className="space-y-3">
              <div className="w-16 h-16 mx-auto rounded-xl bg-wealth-500/20 flex items-center justify-center">
                <FileText className="w-8 h-8 text-wealth-400" />
              </div>
              <div>
                <p className="font-medium text-white">{file.name}</p>
                <p className="text-sm text-surface-200/60">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  setFile(null)
                }}
                className="text-sm text-surface-200/60 hover:text-wealth-400 transition-colors"
              >
                Change file
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="w-16 h-16 mx-auto rounded-xl bg-surface-800 flex items-center justify-center group-hover:bg-surface-200/10 transition-colors">
                <Upload className={`w-8 h-8 ${isDragging ? 'text-wealth-400' : 'text-surface-200/60'}`} />
              </div>
              <div>
                <p className="font-medium text-white">Drop your PDF file here</p>
                <p className="text-sm text-surface-200/60">NSDL CAS or Vested Statement</p>
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium">Failed to parse file</p>
              <p className="text-red-400/70 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!file || isLoading}
          className={`
            w-full py-4 px-6 rounded-xl font-semibold text-white
            transition-all duration-300 flex items-center justify-center gap-2
            ${!file || isLoading
              ? 'bg-surface-800 text-surface-200/40 cursor-not-allowed'
              : 'bg-gradient-to-r from-wealth-500 to-wealth-600 hover:from-wealth-400 hover:to-wealth-500 glow-green'
            }
          `}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing Portfolio...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Add to Portfolio
            </>
          )}
        </button>

        {/* Supported files info */}
        <div className="text-center text-xs text-surface-200/40 space-y-1">
          <p>Supported formats:</p>
          <p>• NSDL CAS PDF (Indian Mutual Funds & Equity)</p>
          <p>• Vested/VF Securities PDF (US Equity)</p>
        </div>
      </form>
    </div>
  )
}

export default FileUpload
