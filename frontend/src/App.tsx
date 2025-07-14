import React from 'react';
import { Routes, Route } from 'react-router-dom'; // React Router for navigation
import { Box } from '@mui/material'; // Material-UI layout component
import Navbar from './components/Navbar'; // Navigation bar component
import Dashboard from './pages/Dashboard'; // Main dashboard page
import TransactionMonitor from './pages/TransactionMonitor'; // Real-time transaction monitoring
import FraudAnalytics from './pages/FraudAnalytics'; // Fraud analytics and reports
import SecuritySettings from './pages/SecuritySettings'; // Security configuration
import Login from './pages/Login'; // Authentication page
import { useAppSelector } from './hooks/redux'; // Custom hook for Redux state
import './App.css';

// Main App component that handles routing and layout
const App: React.FC = () => {
  // Get authentication state from Redux store
  // This determines if user is logged in and can access protected routes
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);

  // If user is not authenticated, show login page
  if (!isAuthenticated) {
    return <Login />;
  }

  // Main application layout with navigation and routing
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Navigation bar - shown on all authenticated pages */}
      <Navbar />

      {/* Main content area with padding for proper spacing */}
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        {/* Router configuration - defines which component to show for each URL */}
        <Routes>
          {/* Default route - shows main dashboard */}
          <Route path="/" element={<Dashboard />} />

          {/* Transaction monitoring page - real-time fraud detection */}
          <Route path="/transactions" element={<TransactionMonitor />} />

          {/* Analytics page - fraud patterns and statistics */}
          <Route path="/analytics" element={<FraudAnalytics />} />

          {/* Security settings page - configure detection parameters */}
          <Route path="/settings" element={<SecuritySettings />} />

          {/* Fallback route - redirects unknown URLs to dashboard */}
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </Box>
    </Box>
  );
};

export default App;
