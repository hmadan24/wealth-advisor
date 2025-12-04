# Wealth Advisor 💰

A modern portfolio intelligence platform that parses your NSDL CAS (Consolidated Account Statement) files to provide visual insights and actionable recommendations.

![Portfolio Dashboard](https://via.placeholder.com/800x400/18181b/22c55e?text=Wealth+Advisor)

## Features

- 📊 **Portfolio Visualization** - Interactive charts for asset allocation and AMC distribution
- 💡 **Smart Insights** - AI-powered analysis of your portfolio health
- 🛡️ **Risk Detection** - Identify concentration risks and fund overlaps
- 📈 **Performance Tracking** - Track returns across all your holdings
- 🔒 **Privacy First** - All processing happens locally, no data stored

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- NSDL CAS PDF file

### Backend Setup

```bash
cd "wealth advisor/backend"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd "wealth advisor/frontend"

# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Usage

1. **Upload CAS File** - Drag and drop your NSDL CAS PDF
2. **Enter Password** - Usually `PAN + DOB` (e.g., `ABCDE1234F01011990`)
3. **View Dashboard** - Explore your portfolio insights

### CAS Password Format

The NSDL CAS PDF is password protected. The password is typically:
- Your **PAN number** (10 characters)
- Followed by your **Date of Birth** in DDMMYYYY format

Example: If PAN is `ABCDE1234F` and DOB is `15th March 1990`, password is `ABCDE1234F15031990`

## Project Structure

```
wealth advisor/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI routes
│   │   ├── parser.py        # CAS PDF parsing
│   │   └── insights.py      # Portfolio analysis
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main app component
│   │   └── components/
│   │       ├── FileUpload.jsx
│   │       └── Dashboard.jsx
│   └── package.json
└── README.md
```

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **casparser** - NSDL CAS PDF parser
- **Pandas** - Data processing

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Recharts** - Charts
- **Lucide React** - Icons

## Insights Generated

- **Concentration Analysis** - Warns if single fund > 25% of portfolio
- **Over-diversification** - Flags if you have too many schemes
- **Asset Allocation** - Evaluates equity/debt balance
- **Fund Overlap** - Detects similar funds in same category
- **Performance** - Identifies underperformers for review
- **Health Score** - Overall portfolio grade (A-D)

## Privacy

Your portfolio data is processed securely. In local mode, everything runs on your machine. In production, data is stored encrypted in your Supabase PostgreSQL database, linked to your phone number.

## Deployment

Ready to deploy to production? See [DEPLOYMENT.md](./DEPLOYMENT.md) for a complete guide using:
- **Supabase** - PostgreSQL database (free tier)
- **Railway/Render** - Backend API hosting (free tier)
- **Firebase Hosting** - Frontend (free tier)

Quick start:
```bash
# Backend
cd "wealth advisor/backend"
cp env.template .env  # Edit with your values
# Deploy to Railway or Render

# Frontend
cd "wealth advisor/frontend"
cp env.template .env  # Add your backend URL
npm run build
npm run deploy  # Firebase
```

## License

MIT

# Trigger Vercel redeploy
