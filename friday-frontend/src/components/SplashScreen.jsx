import React, { useEffect, useState } from 'react';
import Spline from '@splinetool/react-spline';
import { ChevronDown } from 'lucide-react';

const GREETINGS = [
  "Welcome back, Parth.",
  "Ready to build?",
  "Good to see you, Parth.",
  "Let's create something.",
  "Hello, Parth. System online."
];

class SplineErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="spline-placeholder">
          <div className="placeholder-content">
            <h3>🌌 3D Space Ready</h3>
            <p>Paste your exported <code>.splinecode</code> URL in <code>SplashScreen.jsx</code> to see the Aether Shard effect!</p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function SplashScreen({ onScrollDown }) {
  const [greeting, setGreeting] = useState('');

  useEffect(() => {
    setGreeting(GREETINGS[Math.floor(Math.random() * GREETINGS.length)]);
  }, []);

  return (
    <div className="splash-screen">
      <div className="spline-container">
        <SplineErrorBoundary>
          {/*
            IMPORTANT: Replace this URL with your exported Spline URL.
            To get yours: Open your Spline community file -> Duplicate -> Export -> Code -> React -> copy the .splinecode URL.
          */}
          <Spline scene="https://prod.spline.design/6Wq1Q7YGyMvqFlYp/scene.splinecode" />
        </SplineErrorBoundary>
      </div>

      <div className="splash-overlay">
        <h1 className="splash-greeting">{greeting}</h1>
        
        <button className="splash-scroll-btn" onClick={onScrollDown} aria-label="Scroll to chat">
          <span className="splash-scroll-text">Scroll or Click to Chat</span>
          <ChevronDown size={28} className="animate-bounce mt-2" />
        </button>
      </div>
    </div>
  );
}
