# MARS: Mission for Astrobiology and Research Support

MARS is a specialized AI chatbot service powered by NASA's astrobiology research data. It's designed to provide expert answers to questions about everything from microgravity experiments to the study of life in space environments.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-nasamsg.vercel.app-blue?style=for-the-badge&logo=vercel)](https://nasamsg.vercel.app/)
[![Backend](https://img.shields.io/badge/Backend-Render-green?style=for-the-badge&logo=render)](https://nasa-msg.onrender.com)

## Project Overview

**Live Service**: [nasamsg.vercel.app](https://nasamsg.vercel.app/)

MARS is an AI chatbot that has been trained on 607 NASA astrobiology research papers. It serves as a knowledge platform, making complex scientific information easily accessible to researchers, students, and anyone interested in the field of astrobiology.

### Key Features

- **Specialized Data**: Trained on 607 NASA astrobiology papers
- **Intelligent RAG**: Utilizes FAISS vector search and OpenAI's GPT for accurate responses
- **Multi-language Support**: Automatic language detection and response in 15 languages
- **Real-time Dashboard**: Provides user statistics and popular topic analysis
- **Conversation History**: Stored locally in the user's browser to protect privacy
- **Responsive Design**: Optimized for a seamless experience on all devices

## Live Service

### Access the service at [nasamsg.vercel.app](https://nasamsg.vercel.app/)

The MARS chatbot is currently live. You can start a conversation with a specialized AI trained on NASA's astrobiology data right now.

**Features**:
- **Free to Use**: No registration or sign-up required
- **Web Browser Access**: No app installation needed
- **Expert AI Consultation**: Trained on 607 NASA papers
- **Multi-language Support**: Automatically detects and responds in 15 languages

#### Example Questions
- "How does microgravity affect plant growth?"
- "Tell me about microbial research on the International Space Station"
- "What is the impact of the space environment on human bone density?"
- "Discuss Mars missions and astrobiology research"

## Architecture

```
NASA_MSG/
├── frontend/          # React + TypeScript Frontend
├── backend/           # FastAPI + Python Backend
├── README.md          # This file
└── Other configuration files
```

### Frontend (Vercel)
- **React 18.2** + **TypeScript**
- **Vite** build system
- **Tailwind CSS** styling
- **Real-time chat interface**
- **Statistics dashboard**

### Backend (Render)
- **FastAPI** + **Python 3.10**
- **SQLite** database
- **FAISS** vector search
- **OpenAI GPT** API
- **LangChain** RAG pipeline

## Data & AI

### Training Data
- **Source**: 607 NASA astrobiology research papers
- **Coverage**: Microgravity, space environment, life in space, ISS experiments
- **Processing**: Chunking and vector embedding with FAISS index

### AI System
- **RAG (Retrieval-Augmented Generation)**: Precise information retrieval and natural language generation
- **Vector Search**: High-speed semantic search via FAISS
- **Language Model**: OpenAI GPT-4 for response generation
- **Multi-language**: Automatic language detection and translation

## Technology Stack

### Frontend
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind%20CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white)

### AI & Data
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-FF6B6B?style=flat-square&logo=meta&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)

### Deployment
![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=white)

## Getting Started

### Local Development Setup

#### 1. Clone the repository
```bash
git clone https://github.com/ricky5530/NASA_MSG.git
cd NASA_MSG
```

#### 2. Set up the backend
```bash
cd backend
pip install -r requirements.txt

# Configure environment variables (.env file)
echo "OPENAI_API_KEY=your_openai_api_key" > .env

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Set up the frontend
```bash
cd frontend
npm install
npm run dev
```

#### 4. View in your browser
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## API Documentation

Once the backend is running, you can access the API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rag/md` | POST | RAG-based question and answer |
| `/dashboard/summary` | GET | Usage statistics summary |
| `/dashboard/activity` | GET | Recent activity log |
| `/health` | GET | Server status check |

## Monitoring & Analytics

### Real-time Dashboard
- **Total Messages**: Cumulative conversation statistics
- **Recent Activity**: Real-time usage monitoring
- **Average Response Time**: AI performance tracking
- **Language Distribution**: Multi-language usage patterns
- **Popular Topics**: Top discussion themes

### Data Management
- **Automatic Cleanup**: Data older than 24 hours is automatically deleted
- **Size Monitoring**: SQLite database size monitoring and optimization
- **Backup**: Key configurations and index files managed with Git LFS

## Security & Privacy

- **Local Storage**: Conversation history is stored only in the user's browser
- **Anonymous Usage**: No registration required for anonymous use
- **Data Deletion**: Server-side data is automatically deleted after 24 hours
- **CORS Configuration**: Secure cross-domain communication

## Contributing

### Bug Reports
Please report any issues you find on [GitHub Issues](https://github.com/ricky5530/NASA_MSG/issues).

### Feature Suggestions
We welcome ideas for new features.

### Development
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Team

**Team MSG** - Developers of the NASA Astrobiology AI Chatbot

## Acknowledgements

- **NASA**: For providing the astrobiology research data
- **OpenAI**: For the GPT API service
- **Vercel & Render**: For providing stable hosting services
- **Open Source Community**: For the invaluable tools and libraries

---

## Explore the Future of Astrobiology with MARS

### [Start Now → nasamsg.vercel.app](https://nasamsg.vercel.app/)

NASA's specialized AI trained on 607 astrobiology research papers is ready to answer your questions about space science.

---

<div align="center">

**Made with care by Team MSG**

*"Bridging the gap between space science and humanity"*

</div>