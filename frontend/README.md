# MARS Frontend

**Mission for Astrobiology and Research Support** - Frontend application for the AI chatbot supporting astrobiology research

## Project Overview

MARS is an AI chatbot service based on NASA's astrobiology research data. This frontend provides an interface where users can easily ask questions about space environment life research, microgravity experiments, and astrobiology data, and receive expert answers.

## Technology Stack

- **React 18.2** - User interface development
- **TypeScript** - Type safety assurance
- **Vite** - Fast development environment and build tool
- **Tailwind CSS** - Utility-based styling
- **Lucide React** - Icon library
- **React Markdown** - Markdown rendering
- **Remark GFM** - GitHub Flavored Markdown support

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ChatArea.tsx     # Main chat interface
│   │   ├── Sidebar.tsx      # Sidebar and conversation history
│   │   └── Dashboard.tsx    # Real-time statistics dashboard
│   ├── config/
│   │   └── api.ts          # API configuration
│   ├── styles/
│   │   └── globals.css     # Global styles
│   ├── App.tsx             # Main app component
│   └── main.tsx           # App entry point
├── dist/                   # Built files
├── public/                 # Static files
├── package.json           # Dependencies and scripts
├── tailwind.config.js     # Tailwind configuration
├── tsconfig.json          # TypeScript configuration
└── vite.config.ts         # Vite configuration
```

## Getting Started

### Requirements

- **Node.js** 18+ 
- **npm** 9+

### Installation and Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Run development server**
   ```bash
   npm run dev
   ```
   Access `http://localhost:5173` in your browser

3. **Build for production**
   ```bash
   npm run build
   ```

4. **Preview build files**
   ```bash
   npm run preview
   ```

## Key Features

### Chat Interface
- **Real-time Conversation**: Live chat with MARS AI
- **Markdown Support**: Rich text format for displaying answers
- **Language Detection**: Automatic language detection and multi-language support
- **Conversation Storage**: Automatic saving of conversation history to local storage

### Dashboard
- **Real-time Statistics**: Message count, response time, language distribution
- **Popular Topics**: Visualization of frequently asked topics
- **User Activity**: Recent activity log display

### User Interface
- **Responsive Design**: Optimized from mobile to desktop
- **Dark Sidebar**: Professional and modern design
- **Intuitive Navigation**: Easy switching between chat and dashboard

## Configuration

### API Settings
Configure the backend API URL in `src/config/api.ts`:

```typescript
const getBaseUrl = () => {
  // Development environment uses local server
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  
  // Check for environment variable
  const envApiUrl = import.meta.env.VITE_API_URL;
  if (envApiUrl && envApiUrl.startsWith('http')) {
    return envApiUrl;
  }
  
  // Fallback: Production backend URL
  return 'https://nasa-msg.onrender.com';
};

export const API_CONFIG = {
  BASE_URL: getBaseUrl(),
  // ... other configurations
};
```

### Environment Variables
Create a `.env` file if needed for development environment variables.

## Component Guide

### ChatArea.tsx
- Main chat interface
- Message rendering and input handling
- Conversation history management

### Sidebar.tsx
- Navigation and branding
- Conversation history list
- Real-time statistics summary

### Dashboard.tsx
- Detailed statistics dashboard
- Charts and data visualization
- User activity logs

## Styling

The project uses **Tailwind CSS** for styling:

- **Utility-first**: Fast development and consistency
- **Responsive Design**: Optimized for all devices
- **Custom Configuration**: Theme extensions in `tailwind.config.js`

## Build and Deployment

### Vercel Deployment
The project is configured for deployment on Vercel:

```bash
# Deploy with Vercel CLI
vercel --prod
```

### Manual Deployment
For deployment to other platforms:

1. Run build: `npm run build`
2. Upload the `dist/` folder to your web server

## Development Guide

### Code Style
- **TypeScript**: Type safety ensured in all components
- **Functional Components**: Using React Hooks
- **Naming Convention**: camelCase (variables), PascalCase (components)

### State Management
- **React useState**: Local state management
- **Local Storage**: Persistent storage for conversation history
- **API Communication**: Using fetch API

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Use different port
   npm run dev -- --port 3000
   ```

2. **Build errors**
   ```bash
   # Reinstall dependencies
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **TypeScript errors**
   ```bash
   # Type checking
   npm run type-check
   ```

## Team Information

**Team MSG** - NASA Astrobiology Data-based AI Chatbot Development Team

---

### Special Features

- **15+ Language Support**: Multi-language support for researchers worldwide
- **Real-time Statistics**: Live monitoring of usage patterns and popular topics
- **Conversation History**: Privacy protection through local storage
- **Responsive Design**: Perfect user experience on all devices

**Explore the world of astrobiology with MARS!**