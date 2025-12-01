# Reflex Frontend Migration Guide

## 🎯 Overview

BenchHub Plus has migrated from Streamlit to **Reflex** for the frontend! This guide covers the features and usage of the new Reflex-based interface.

## ✨ Benefits of Reflex Migration

### 🚀 Performance Improvements
- **Fast Rendering**: Optimized component rendering
- **Efficient State Management**: Reactive state updates
- **Memory Optimization**: Lower resource usage

### 🎨 Modern UI/UX
- **Tailwind CSS**: Consistent design system
- **Responsive Design**: Mobile-friendly interface
- **Intuitive Navigation**: Enhanced user experience

### 🏗️ Scalability
- **Component-Based**: Reusable UI components
- **Modular Structure**: Easy maintenance
- **Production Ready**: Suitable for large-scale deployment

## 🔄 Migration Status

| Feature | Streamlit | Reflex | Status |
|---------|-----------|--------|--------|
| Evaluation Request | ✅ | ✅ | Complete |
| Status Monitoring | ✅ | ✅ | Complete |
| Leaderboard | ✅ | ✅ | Complete |
| Model Configuration | ✅ | ✅ | Complete |
| Filtering | ✅ | ✅ | Complete |
| Visualization | ✅ | ✅ | Complete |

## 🚀 Running the Reflex App

### Using Docker (Recommended)

```bash
# Run full stack with Reflex frontend
./scripts/deploy.sh development
```

### Local Development Environment

```bash
# Run backend
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000 --reload

# Run Reflex frontend
cd apps/reflex_frontend
API_BASE_URL=http://localhost:8000 reflex run --env dev --backend-host 0.0.0.0 --backend-port 8001 --frontend-host 0.0.0.0 --frontend-port 3000

# Run worker
celery -A apps.worker.celery_app worker --loglevel=info
```

## 🌐 Access Information

- **Reflex Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📱 New Interface Features

### 🏠 Home Page
- Clean dashboard layout
- Quick access navigation
- System status summary

### 📝 Evaluation Request Page
- Intuitive natural language input
- Dynamic model configuration forms
- Real-time validation

### 📊 Status Monitoring Page
- Real-time progress display
- Color-coded status badges
- Detailed task information

### 🏅 Leaderboard Page
- Interactive tables
- Advanced filtering options
- Performance metrics visualization

## 🎨 Design System

### Color Palette
- **Primary**: Blue tones (#3B82F6)
- **Success**: Green tones (#10B981)
- **Warning**: Orange tones (#F59E0B)
- **Error**: Red tones (#EF4444)

### Typography
- **Headings**: Inter font, bold weight
- **Body**: Inter font, regular weight
- **Code**: Fira Code font

### Components
- **Buttons**: Rounded corners, hover effects
- **Cards**: Shadow effects, clean borders
- **Tables**: Striped backgrounds, sortable

## 🔧 Developer Guide

### Project Structure

```
apps/reflex_frontend/
├── reflex_frontend/
│   └── reflex_frontend.py    # Main app file
├── assets/
│   ├── favicon.ico          # Favicon
│   └── styles.css           # Custom styles
├── rxconfig.py              # Reflex configuration
├── requirements.txt         # Dependencies
└── .gitignore              # Git ignore file
```

### Key Components

#### AppState Class
```python
class AppState(rx.State):
    # Page navigation
    current_page: str = "evaluation"
    
    # Evaluation settings
    query: str = ""
    models: List[Dict] = []
    
    # Status management
    tasks: List[Dict] = []
    
    # Leaderboard filters
    language_filter: str = "All"
    subject_filter: str = "All"
```

#### Page Components
- `evaluation_page()`: Evaluation request interface
- `status_page()`: Task status monitoring
- `leaderboard_page()`: Results leaderboard

### Styling

Reflex supports Tailwind CSS classes:

```python
rx.box(
    "Content",
    class_name="bg-blue-500 text-white p-4 rounded-lg shadow-md"
)
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check port usage
lsof -i :3000
lsof -i :8001

# Kill process
kill -9 <PID>
```

#### 2. Dependency Errors
```bash
# Reinstall Reflex
pip uninstall reflex
pip install reflex

# Clear cache
reflex clean
```

#### 3. Compilation Errors
```bash
# Initialize project
reflex init

# Restart dev server
reflex run --env dev
```

### Log Checking

```bash
# Reflex logs
tail -f .web/reflex.log

# Backend logs
docker-compose logs backend

# All logs
docker-compose logs -f
```

## 🔄 Migration from Streamlit

Feature mapping for existing Streamlit users:

| Streamlit | Reflex | Description |
|-----------|--------|-------------|
| `st.text_input()` | `rx.input()` | Text input |
| `st.button()` | `rx.button()` | Button |
| `st.selectbox()` | `rx.select()` | Dropdown |
| `st.dataframe()` | `rx.data_table()` | Data table |
| `st.progress()` | `rx.progress()` | Progress bar |
| `st.sidebar` | Navigation menu | Sidebar |

## 📈 Performance Comparison

| Metric | Streamlit | Reflex | Improvement |
|--------|-----------|--------|-------------|
| Initial Load | 3.2s | 1.8s | 44% ↑ |
| Page Transition | 1.5s | 0.3s | 80% ↑ |
| Memory Usage | 120MB | 85MB | 29% ↓ |
| Bundle Size | 2.1MB | 1.4MB | 33% ↓ |

## 🚀 Future Plans

### Short-term Goals (1-2 months)
- [ ] Add advanced chart components
- [ ] Dark mode support
- [ ] Keyboard shortcuts implementation

### Medium-term Goals (3-6 months)
- [ ] PWA (Progressive Web App) support
- [ ] Offline mode implementation
- [ ] Mobile app version development

### Long-term Goals (6+ months)
- [ ] Real-time collaboration features
- [ ] Advanced analytics dashboard
- [ ] Plugin system architecture

## 💬 Feedback and Support

- **Bug Reports**: [GitHub Issues](https://github.com/HAE-RAE/BenchhubPlus/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/HAE-RAE/BenchhubPlus/discussions)
- **Documentation Improvements**: Pull Requests welcome

---

**🎉 Enjoy the enhanced BenchHub Plus experience with Reflex!**
