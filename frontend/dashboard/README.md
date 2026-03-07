# OrchestrAI Dashboard

A modern, interactive web dashboard for the OrchestrAI Career Intelligence System that transforms email-based reports into a stunning visual experience.

## 🚀 Features

### **Career Readiness Dashboard**
- Animated circular progress indicator showing overall career readiness score
- Four key metrics with animated progress bars:
  - Skill Coverage
  - Portfolio Strength  
  - Practice Score
  - Security Score
- Quick stats grid with key performance indicators

### **Email Report Section**
- Complete email content displayed in modern dashboard format
- Interactive table with all internship opportunities
- Real-time statistics (Total Jobs, Remote, Sources, Report Date)
- Modern card-based layout with hover effects
- Direct apply buttons for each opportunity

### **Internship Explorer**
- Advanced filtering system:
  - Platform (LinkedIn, Internshala, Company Website)
  - Role Type (Data Science, Machine Learning, Data Engineering)
  - Match Score (slider filter)
  - Location (Remote, On-site)
- Modern card layout with detailed information
- Probability badges with color coding
- Skill gap analysis for each opportunity
- Action buttons for Apply, Cover Letter, Resume, Mock Interview

### **Career Strategy**
- Target career goal display
- Skill gap analysis with priority levels (High/Medium/Low)
- Weekly action plan with progress tracking
- Visual timeline of career development steps

### **GitHub Security Insights**
- Security risk cards with color-coded severity
- Vulnerability details and suggested fixes
- Repository-by-repository analysis

### **Mock Interview System**
- Interactive interview setup
- Role and difficulty selection
- Live Q&A interface with performance tracking
- Results dashboard with scoring

## 🎨 Design Features

- **Dark futuristic theme** with gradient backgrounds
- **Glassmorphism effects** with backdrop blur
- **Smooth animations** and micro-interactions
- **Responsive design** for all screen sizes
- **Modern typography** using Inter and Outfit fonts
- **Color-coded elements** for better UX

## 📁 Project Structure

```
frontend/dashboard/
├── index.html          # Main dashboard HTML
├── styles.css          # Modern CSS with glassmorphism design
├── app.js             # Interactive JavaScript functionality
└── README.md          # This file
```

## 🚀 Deployment

### Render Static Site Deployment

1. **Push to GitHub**
   ```bash
   git add frontend/dashboard/
   git commit -m "Add OrchestrAI Dashboard"
   git push origin main
   ```

2. **Deploy on Render**
   - Go to Render Dashboard
   - Click "New +" → "Static Site"
   - Connect your GitHub repository
   - Set Build Command: `echo "No build required"`
   - Set Publish Directory: `frontend/dashboard`
   - Click "Create Static Site"

### Local Development

1. **Start a local server**
   ```bash
   cd frontend/dashboard
   python -m http.server 8000
   # or
   npx serve .
   ```

2. **Open in browser**
   ```
   http://localhost:8000
   ```

## 🔗 Integration

### Email Integration

The dashboard integrates with the existing email system:

1. **Email Content**: All email content is displayed in the "Email Report" section
2. **Navigation**: Users can access the dashboard via the "View Career Analytics Dashboard" button in the portfolio
3. **Real-time Data**: Dashboard can fetch real-time data from backend APIs

### API Integration

The dashboard includes methods for API integration:

```javascript
// Fetch dashboard data
await dashboard.loadDashboardData();

// Fetch internship data
await dashboard.loadInternshipData();

// Fetch security data
await dashboard.loadSecurityData();
```

## 🎯 Usage

1. **Access Dashboard**: Click "View Career Analytics Dashboard" from the portfolio
2. **Navigate Sections**: Use the navigation bar to switch between sections
3. **Filter Internships**: Use the filter panel to find relevant opportunities
4. **Track Progress**: Monitor career readiness and skill development
5. **Apply for Jobs**: Use direct apply buttons from internship cards

## 🛠️ Technologies Used

- **HTML5** - Semantic markup
- **CSS3** - Modern styling with glassmorphism
- **Vanilla JavaScript** - Interactive functionality
- **Chart.js** - Data visualization (via CDN)
- **Google Fonts** - Typography (Inter, Outfit)

## 📱 Responsive Design

The dashboard is fully responsive and works on:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (< 768px)

## 🎨 Color Scheme

- **Background**: Deep navy / dark purple gradient
- **Primary**: Electric blue (#3b82f6)
- **Secondary**: Neon violet (#8b5cf6)
- **Accent**: Teal (#06b6d4)
- **Cards**: Glassmorphism with blur and glow

## 🔄 Future Enhancements

- [ ] Real-time API integration
- [ ] User authentication
- [ ] Personalized recommendations
- [ ] Advanced analytics
- [ ] Export functionality
- [ ] Email subscription management

## 🤝 Contributing

This dashboard is part of the OrchestrAI system. For contributions:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is part of the OrchestrAI Career Intelligence System.

---

**Built with ❤️ for the OrchestrAI Career Intelligence System**
