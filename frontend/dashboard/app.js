// OrchestrAI Dashboard JavaScript
class OrchestrAIDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.internships = [];
        this.securityInsights = [];
        this.emailJobs = [];
        this.filters = {
            platform: '',
            role: '',
            score: 0,
            location: ''
        };
        
        // API Base URL - change this for production
        this.apiBaseUrl = window.location.origin; // Works for both local and Render
        
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupFilters();
        this.loadMockData();
        this.hideLoading();
        this.setupAnimations();
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                this.switchSection(section);
            });
        });
    }

    switchSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Update sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');

        this.currentSection = sectionName;

        // Load section-specific data
        if (sectionName === 'internships') {
            this.renderInternships();
        } else if (sectionName === 'github') {
            this.renderSecurityInsights();
        } else if (sectionName === 'email-report') {
            this.renderEmailReport();
        }
    }

    setupFilters() {
        const platformFilter = document.getElementById('platform-filter');
        const roleFilter = document.getElementById('role-filter');
        const scoreFilter = document.getElementById('score-filter');
        const locationFilter = document.getElementById('location-filter');
        const resetButton = document.querySelector('.filter-reset');

        platformFilter.addEventListener('change', (e) => {
            this.filters.platform = e.target.value;
            this.renderInternships();
        });

        roleFilter.addEventListener('change', (e) => {
            this.filters.role = e.target.value;
            this.renderInternships();
        });

        scoreFilter.addEventListener('input', (e) => {
            this.filters.score = parseInt(e.target.value);
            document.querySelector('.filter-value').textContent = `${this.filters.score}%`;
            this.renderInternships();
        });

        locationFilter.addEventListener('change', (e) => {
            this.filters.location = e.target.value;
            this.renderInternships();
        });

        resetButton.addEventListener('click', () => {
            this.filters = {
                platform: '',
                role: '',
                score: 0,
                location: ''
            };
            platformFilter.value = '';
            roleFilter.value = '';
            scoreFilter.value = 0;
            locationFilter.value = '';
            document.querySelector('.filter-value').textContent = '0%';
            this.renderInternships();
        });
    }

    loadMockData() {
        // Mock internship data
        this.internships = [
            {
                id: 1,
                company: 'TechCorp Solutions',
                role: 'Data Science Intern',
                location: 'Remote',
                platform: 'linkedin',
                matchScore: 92,
                probability: 'high',
                skillGap: ['Advanced SQL', 'Tableau', 'Communication'],
                requiredSkills: ['Python', 'Machine Learning', 'Statistics', 'Data Visualization']
            },
            {
                id: 2,
                company: 'DataMinds Inc',
                role: 'Machine Learning Intern',
                location: 'San Francisco, CA',
                platform: 'internshala',
                matchScore: 78,
                probability: 'medium',
                skillGap: ['Deep Learning', 'TensorFlow'],
                requiredSkills: ['Python', 'ML Algorithms', 'Data Preprocessing', 'Model Evaluation']
            },
            {
                id: 3,
                company: 'CloudTech Systems',
                role: 'Data Engineering Intern',
                location: 'Remote',
                platform: 'company',
                matchScore: 85,
                probability: 'high',
                skillGap: ['Apache Spark', 'Kubernetes'],
                requiredSkills: ['Python', 'SQL', 'ETL', 'Cloud Platforms']
            },
            {
                id: 4,
                company: 'Analytics Pro',
                role: 'Data Science Intern',
                location: 'New York, NY',
                platform: 'linkedin',
                matchScore: 71,
                probability: 'medium',
                skillGap: ['Business Acumen', 'Presentation Skills'],
                requiredSkills: ['R', 'Statistics', 'Data Analysis', 'Reporting']
            },
            {
                id: 5,
                company: 'AI Innovations',
                role: 'Machine Learning Intern',
                location: 'Remote',
                platform: 'company',
                matchScore: 88,
                probability: 'high',
                skillGap: ['Computer Vision', 'PyTorch'],
                requiredSkills: ['Python', 'Deep Learning', 'Neural Networks', 'Image Processing']
            },
            {
                id: 6,
                company: 'DataFlow Systems',
                role: 'Data Engineering Intern',
                location: 'Seattle, WA',
                platform: 'internshala',
                matchScore: 65,
                probability: 'low',
                skillGap: ['Apache Airflow', 'AWS Glue', 'Data Warehousing'],
                requiredSkills: ['Python', 'SQL', 'Data Modeling', 'Pipeline Design']
            }
        ];

        // Mock email jobs data (same as internships but with email format)
        this.emailJobs = [
            {
                idx: 1,
                company: 'TechCorp Solutions',
                role: 'Data Science Intern',
                location: 'Remote',
                role_keywords: ['Data Science', 'Analytics', 'Machine Learning'],
                technical_skills: ['Python', 'SQL', 'TensorFlow', 'Data Visualization'],
                source: 'LinkedIn',
                apply_link: 'https://linkedin.com/jobs/apply/1'
            },
            {
                idx: 2,
                company: 'DataMinds Inc',
                role: 'Machine Learning Intern',
                location: 'San Francisco, CA',
                role_keywords: ['Machine Learning', 'AI', 'Deep Learning'],
                technical_skills: ['Python', 'PyTorch', 'ML Algorithms', 'Statistics'],
                source: 'Internshala',
                apply_link: 'https://internshala.com/apply/2'
            },
            {
                idx: 3,
                company: 'CloudTech Systems',
                role: 'Data Engineering Intern',
                location: 'Remote',
                role_keywords: ['Data Engineering', 'ETL', 'Cloud'],
                technical_skills: ['Python', 'SQL', 'AWS', 'Apache Spark'],
                source: 'Company Website',
                apply_link: 'https://cloudtech.com/careers/3'
            },
            {
                idx: 4,
                company: 'Analytics Pro',
                role: 'Data Science Intern',
                location: 'New York, NY',
                role_keywords: ['Data Science', 'Analytics', 'Business Intelligence'],
                technical_skills: ['R', 'Python', 'Tableau', 'Statistics'],
                source: 'LinkedIn',
                apply_link: 'https://linkedin.com/jobs/apply/4'
            },
            {
                idx: 5,
                company: 'AI Innovations',
                role: 'Machine Learning Intern',
                location: 'Remote',
                role_keywords: ['Machine Learning', 'Computer Vision', 'AI'],
                technical_skills: ['Python', 'OpenCV', 'TensorFlow', 'Deep Learning'],
                source: 'Company Website',
                apply_link: 'https://aiinnovations.com/jobs/5'
            },
            {
                idx: 6,
                company: 'DataFlow Systems',
                role: 'Data Engineering Intern',
                location: 'Seattle, WA',
                role_keywords: ['Data Engineering', 'Pipeline', 'Big Data'],
                technical_skills: ['Python', 'SQL', 'Airflow', 'Docker'],
                source: 'Internshala',
                apply_link: 'https://internshala.com/apply/6'
            },
            {
                idx: 7,
                company: 'NeuralTech Labs',
                role: 'AI Research Intern',
                location: 'Remote',
                role_keywords: ['AI Research', 'Neural Networks', 'NLP'],
                technical_skills: ['Python', 'PyTorch', 'NLP', 'Research'],
                source: 'LinkedIn',
                apply_link: 'https://linkedin.com/jobs/apply/7'
            },
            {
                idx: 8,
                company: 'BigData Corp',
                role: 'Data Engineering Intern',
                location: 'Remote',
                role_keywords: ['Data Engineering', 'Big Data', 'Cloud'],
                technical_skills: ['Python', 'Hadoop', 'Spark', 'AWS'],
                source: 'Company Website',
                apply_link: 'https://bigdata.com/careers/8'
            },
            {
                idx: 9,
                company: 'ML Solutions',
                role: 'Machine Learning Intern',
                location: 'Boston, MA',
                role_keywords: ['Machine Learning', 'ML Ops', 'Deployment'],
                technical_skills: ['Python', 'Kubernetes', 'MLflow', 'Docker'],
                source: 'Internshala',
                apply_link: 'https://internshala.com/apply/9'
            },
            {
                idx: 10,
                company: 'Cloud Analytics',
                role: 'Data Science Intern',
                location: 'Remote',
                role_keywords: ['Data Science', 'Cloud Analytics', 'BI'],
                technical_skills: ['Python', 'Tableau', 'Power BI', 'SQL'],
                source: 'LinkedIn',
                apply_link: 'https://linkedin.com/jobs/apply/10'
            },
            {
                idx: 11,
                company: 'DeepMind AI',
                role: 'Deep Learning Intern',
                location: 'London, UK',
                role_keywords: ['Deep Learning', 'AI Research', 'Neural Networks'],
                technical_skills: ['Python', 'TensorFlow', 'Research', 'Mathematics'],
                source: 'Company Website',
                apply_link: 'https://deepmind.com/careers/11'
            },
            {
                idx: 12,
                company: 'DataOps Pro',
                role: 'Data Engineering Intern',
                location: 'Remote',
                role_keywords: ['DataOps', 'DevOps', 'Automation'],
                technical_skills: ['Python', 'CI/CD', 'Jenkins', 'Git'],
                source: 'Internshala',
                apply_link: 'https://internshala.com/apply/12'
            }
        ];

        // Mock security insights data
        this.securityInsights = [
            {
                id: 1,
                repoName: 'orchestrai-agent',
                riskLevel: 'high',
                riskScore: 13,
                vulnerabilities: [
                    { type: 'HIGH', description: 'SQL String Concat in `backend/agents/career_strategy_agent.py` line 134', fix: 'Use parameterized queries to prevent SQL injection' },
                    { type: 'HIGH', description: 'Unsafe eval() in `backend/agents/repo_security_scanner_agent.py` line 39', fix: 'Avoid eval(); use json.loads() or ast.literal_eval() instead' }
                ]
            },
            {
                id: 2,
                repoName: 'STST',
                riskLevel: 'medium',
                riskScore: 3,
                vulnerabilities: [
                    { type: 'MEDIUM', description: 'Unsafe exec() in `decorator.py` line 160', fix: 'Avoid exec(); refactor to use functions directly' },
                    { type: 'LOW', description: 'HTTP (not HTTPS) in `soundfile.py` line 1269', fix: 'Use HTTPS endpoints to ensure encrypted communication' }
                ]
            },
            {
                id: 3,
                repoName: 'Swathy1209',
                riskLevel: 'safe',
                riskScore: 0,
                vulnerabilities: []
            },
            {
                id: 4,
                repoName: 'orchestrai-db',
                riskLevel: 'safe',
                riskScore: 0,
                vulnerabilities: []
            },
            {
                id: 5,
                repoName: 'acia-cloud-deployment',
                riskLevel: 'safe',
                riskScore: 0,
                vulnerabilities: []
            },
            {
                id: 6,
                repoName: 'acia-playwright',
                riskLevel: 'safe',
                riskScore: 0,
                vulnerabilities: []
            }
        ];
    }

    renderInternships() {
        const container = document.getElementById('internships-container');
        
        // Filter internships
        let filteredInternships = this.internships.filter(internship => {
            if (this.filters.platform && internship.platform !== this.filters.platform) return false;
            if (this.filters.role && !internship.role.toLowerCase().includes(this.filters.role)) return false;
            if (this.filters.score > 0 && internship.matchScore < this.filters.score) return false;
            if (this.filters.location && !internship.location.toLowerCase().includes(this.filters.location)) return false;
            return true;
        });

        container.innerHTML = '';

        filteredInternships.forEach(internship => {
            const card = this.createInternshipCard(internship);
            container.appendChild(card);
        });

        if (filteredInternships.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 3rem; color: var(--text-dim);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                    <h3>No internships found</h3>
                    <p>Try adjusting your filters to see more opportunities</p>
                </div>
            `;
        }
    }

    createInternshipCard(internship) {
        const card = document.createElement('div');
        card.className = 'internship-card';
        
        const probabilityClass = `probability-${internship.probability}`;
        const locationIcon = internship.location.toLowerCase() === 'remote' ? '🏠' : '📍';
        
        card.innerHTML = `
            <div class="internship-header">
                <div class="company-name">${internship.company}</div>
                <div class="internship-role">${internship.role}</div>
                <div class="internship-location">
                    <span>${locationIcon}</span>
                    <span>${internship.location}</span>
                </div>
            </div>
            
            <div class="internship-details">
                <div class="detail-row">
                    <span class="detail-label">Match Score</span>
                    <span class="detail-value match-score">${internship.matchScore}%</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Probability</span>
                    <span class="detail-value">
                        <span class="probability-badge ${probabilityClass}">${internship.probability}</span>
                    </span>
                </div>
            </div>
            
            ${internship.skillGap.length > 0 ? `
                <div class="skill-gap">
                    <div class="skill-gap-title">Skill Gap (${internship.skillGap.length} skills)</div>
                    <div class="skill-gap-list">${internship.skillGap.join(' • ')}</div>
                </div>
            ` : ''}
            
            <div class="internship-actions">
                <button class="action-btn primary" onclick="dashboard.applyToInternship(${internship.id})">Apply Now</button>
                <button class="action-btn" onclick="dashboard.generateCoverLetter(${internship.id})">Cover Letter</button>
                <button class="action-btn" onclick="dashboard.generateResume(${internship.id})">Resume</button>
                <button class="action-btn" onclick="dashboard.startMockInterview(${internship.id})">Mock Interview</button>
            </div>
        `;
        
        return card;
    }

    renderSecurityInsights() {
        const container = document.getElementById('security-container');
        container.innerHTML = '';

        this.securityInsights.forEach(insight => {
            const card = this.createSecurityCard(insight);
            container.appendChild(card);
        });
    }

    createSecurityCard(insight) {
        const card = document.createElement('div');
        card.className = `security-card ${insight.riskLevel}-risk`;
        
        const riskClass = insight.riskLevel === 'high' ? 'high' : insight.riskLevel === 'medium' ? 'medium' : 'safe';
        const riskText = insight.riskLevel === 'high' ? 'High Risk' : insight.riskLevel === 'medium' ? 'Medium Risk' : 'Safe';
        
        card.innerHTML = `
            <div class="repo-header">
                <div class="repo-name">${insight.repoName}</div>
                <span class="risk-level ${riskClass}">${riskText}</span>
            </div>
            
            ${insight.vulnerabilities.length > 0 ? `
                <div class="vulnerability-list">
                    ${insight.vulnerabilities.map(vuln => `
                        <div class="vulnerability-item">
                            <strong>[${vuln.type}]</strong> ${vuln.description}
                        </div>
                    `).join('')}
                </div>
                
                <div class="suggested-fix">
                    <strong>💡 Suggested Fix:</strong> ${insight.vulnerabilities[0].fix}
                </div>
            ` : `
                <div style="color: var(--text-dim); font-style: italic;">
                    ✅ No critical issues detected.
                </div>
            `}
        `;
        
        return card;
    }

    renderEmailReport() {
        // Update email stats
        const totalJobs = this.emailJobs.length;
        const remoteJobs = this.emailJobs.filter(job => job.location.toLowerCase().includes('remote')).length;
        const sources = [...new Set(this.emailJobs.map(job => job.source))];
        const currentDate = new Date().toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });

        document.getElementById('total-jobs').textContent = totalJobs;
        document.getElementById('remote-jobs').textContent = remoteJobs;
        document.getElementById('sources-count').textContent = sources.length;
        document.getElementById('report-date').textContent = currentDate;
        document.getElementById('email-date').textContent = currentDate;
        document.getElementById('email-report-time').textContent = new Date().toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });

        // Render email table
        const tbody = document.getElementById('email-jobs-tbody');
        tbody.innerHTML = '';

        this.emailJobs.forEach(job => {
            const row = this.createEmailJobRow(job);
            tbody.appendChild(row);
        });
    }

    createEmailJobRow(job) {
        const row = document.createElement('tr');
        
        const keywordsHtml = job.role_keywords.map(keyword => 
            `<span class="email-badge">${keyword}</span>`
        ).join(' ');

        const skillsHtml = job.technical_skills.map(skill => 
            `<span class="email-badge">${skill}</span>`
        ).join(' ');

        row.innerHTML = `
            <td>${job.idx}</td>
            <td>
                <div class="company-cell">${job.company}</div>
                <span class="source-tag">via ${job.source}</span>
            </td>
            <td>${job.role}</td>
            <td>${job.location}</td>
            <td>${keywordsHtml}</td>
            <td>${skillsHtml}</td>
            <td>
                <a href="${job.apply_link}" class="email-apply-btn" target="_blank">
                    Apply →
                </a>
            </td>
        `;
        
        return row;
    }

    setupAnimations() {
        // Animate progress bars on scroll
        const observerOptions = {
            threshold: 0.5,
            rootMargin: '0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const progressBars = entry.target.querySelectorAll('.progress-bar, .skill-bar');
                    progressBars.forEach(bar => {
                        const width = bar.style.width;
                        bar.style.width = '0%';
                        setTimeout(() => {
                            bar.style.width = width;
                        }, 100);
                    });
                }
            });
        }, observerOptions);

        // Observe all sections
        document.querySelectorAll('.section').forEach(section => {
            observer.observe(section);
        });
    }

    showLoading() {
        document.getElementById('loading').classList.add('active');
    }

    hideLoading() {
        setTimeout(() => {
            document.getElementById('loading').classList.remove('active');
        }, 1000);
    }

    // Action methods
    applyToInternship(internshipId) {
        this.showLoading();
        setTimeout(() => {
            this.hideLoading();
            this.showNotification('Application submitted successfully!', 'success');
        }, 1500);
    }

    generateCoverLetter(internshipId) {
        this.showLoading();
        setTimeout(() => {
            this.hideLoading();
            this.showNotification('Cover letter generated!', 'success');
        }, 1500);
    }

    generateResume(internshipId) {
        this.showLoading();
        setTimeout(() => {
            this.hideLoading();
            this.showNotification('Optimized resume generated!', 'success');
        }, 1500);
    }

    startMockInterview(internshipId) {
        this.switchSection('interview');
        this.showNotification('Mock interview session ready!', 'info');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--danger)' : 'var(--primary)'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    // API integration methods (placeholder)
    async fetchFromAPI(endpoint) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${endpoint}`);
            if (!response.ok) throw new Error('API request failed');
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            this.showNotification('Failed to fetch data from API', 'error');
            return null;
        }
    }

    async loadDashboardData() {
        const data = await this.fetchFromAPI('dashboard');
        if (data) {
            // Update dashboard with real data
            this.updateDashboardMetrics(data);
        }
    }

    async loadInternshipData() {
        const data = await this.fetchFromAPI('internships');
        if (data) {
            this.internships = data;
            this.renderInternships();
        }
    }

    async loadSecurityData() {
        const data = await this.fetchFromAPI('security');
        if (data) {
            this.securityInsights = data;
            this.renderSecurityInsights();
        }
    }

    async loadEmailData() {
        const data = await this.fetchFromAPI('jobs');
        if (data && data.jobs) {
            this.emailJobs = data.jobs;
            this.renderEmailReport();
        }
    }

    updateDashboardMetrics(data) {
        // Update main score
        document.querySelector('.score-number').textContent = data.careerReadinessScore || '77.2';
        
        // Update metrics
        const metrics = data.metrics || {};
        this.updateMetric('Skill Coverage', metrics.skillCoverage || 82);
        this.updateMetric('Portfolio Strength', metrics.portfolioStrength || 75);
        this.updateMetric('Practice Score', metrics.practiceScore || 68);
        this.updateMetric('Security Score', metrics.securityScore || 91);
    }

    updateMetric(label, value) {
        const metricCards = document.querySelectorAll('.metric-card');
        metricCards.forEach(card => {
            const labelElement = card.querySelector('.metric-label');
            if (labelElement && labelElement.textContent === label) {
                card.querySelector('.metric-value').textContent = `${value}%`;
                card.querySelector('.progress-bar').style.width = `${value}%`;
            }
        });
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new OrchestrAIDashboard();
});

// Mock interview functionality
document.addEventListener('DOMContentLoaded', () => {
    const startInterviewBtn = document.querySelector('.interview-start-btn');
    if (startInterviewBtn) {
        startInterviewBtn.addEventListener('click', () => {
            const role = document.querySelector('.interview-select').value;
            const difficulty = document.querySelectorAll('.interview-select')[1].value;
            
            // Show loading
            document.getElementById('loading').classList.add('active');
            
            // Simulate interview setup
            setTimeout(() => {
                document.getElementById('loading').classList.remove('active');
                
                // Create interview interface
                const interviewCard = document.querySelector('.interview-card');
                interviewCard.innerHTML = `
                    <div class="interview-active">
                        <h2>Mock Interview Session</h2>
                        <p style="color: var(--text-dim); margin-bottom: 2rem;">
                            <strong>Role:</strong> ${role}<br>
                            <strong>Difficulty:</strong> ${difficulty}
                        </p>
                        
                        <div class="question-container" style="background: var(--surface); border-radius: 12px; padding: 2rem; margin-bottom: 2rem; text-align: left;">
                            <h3 style="color: var(--primary); margin-bottom: 1rem;">Question 1 of 5</h3>
                            <p style="font-size: 1.125rem; line-height: 1.6; margin-bottom: 1.5rem;">
                                Explain the difference between supervised and unsupervised machine learning. Provide examples of when you would use each approach.
                            </p>
                            <textarea 
                                placeholder="Type your answer here..." 
                                style="width: 100%; min-height: 120px; background: var(--bg-dark); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; color: var(--text-main); font-family: inherit; resize: vertical;"
                            ></textarea>
                        </div>
                        
                        <div style="display: flex; gap: 1rem; justify-content: center;">
                            <button onclick="dashboard.submitAnswer()" style="background: var(--gradient-primary); border: none; border-radius: 8px; padding: 0.75rem 2rem; color: white; font-weight: 600; cursor: pointer;">
                                Submit Answer
                            </button>
                            <button onclick="location.reload()" style="background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem 2rem; color: var(--text-main); font-weight: 600; cursor: pointer;">
                                End Interview
                            </button>
                        </div>
                    </div>
                `;
            }, 2000);
        });
    }
});

// Add submit answer method to dashboard
OrchestrAIDashboard.prototype.submitAnswer = function() {
    this.showNotification('Answer submitted! Moving to next question...', 'success');
    
    // Simulate moving to next question
    setTimeout(() => {
        const questionContainer = document.querySelector('.question-container p');
        const questions = [
            "Explain the difference between supervised and unsupervised machine learning. Provide examples of when you would use each approach.",
            "How would you handle missing data in a dataset? Describe at least three different approaches.",
            "What is overfitting in machine learning and how can you prevent it?",
            "Describe the bias-variance tradeoff and its implications for model selection.",
            "How would you evaluate the performance of a classification model? Discuss at least three metrics."
        ];
        
        const currentQuestion = parseInt(questionContainer.parentElement.querySelector('h3').textContent.match(/\d+/)[0]);
        if (currentQuestion < 5) {
            questionContainer.parentElement.querySelector('h3').textContent = `Question ${currentQuestion + 1} of 5`;
            questionContainer.textContent = questions[currentQuestion];
            questionContainer.nextElementSibling.value = '';
        } else {
            // Interview completed
            document.querySelector('.interview-card').innerHTML = `
                <div style="text-align: center;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">🎉</div>
                    <h2 style="color: var(--success); margin-bottom: 1rem;">Interview Completed!</h2>
                    <p style="color: var(--text-dim); margin-bottom: 2rem;">Great job! You've completed the mock interview session.</p>
                    <div style="background: var(--surface); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
                        <h3 style="color: var(--text-main); margin-bottom: 1rem;">Your Performance</h3>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; text-align: center;">
                            <div>
                                <div style="font-size: 2rem; font-weight: 800; color: var(--primary);">85%</div>
                                <div style="color: var(--text-dim); font-size: 0.875rem;">Overall Score</div>
                            </div>
                            <div>
                                <div style="font-size: 2rem; font-weight: 800; color: var(--success);">4/5</div>
                                <div style="color: var(--text-dim); font-size: 0.875rem;">Questions Answered</div>
                            </div>
                            <div>
                                <div style="font-size: 2rem; font-weight: 800; color: var(--secondary);">Good</div>
                                <div style="color: var(--text-dim); font-size: 0.875rem;">Performance</div>
                            </div>
                        </div>
                    </div>
                    <button onclick="location.reload()" style="background: var(--gradient-primary); border: none; border-radius: 8px; padding: 1rem 2rem; color: white; font-weight: 600; cursor: pointer;">
                        Start New Interview
                    </button>
                </div>
            `;
        }
    }, 1500);
};
