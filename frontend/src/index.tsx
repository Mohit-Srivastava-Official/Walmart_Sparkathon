import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux'; // Redux provider for state management
import { BrowserRouter } from 'react-router-dom'; // Router for navigation
import { ThemeProvider, createTheme } from '@mui/material/styles'; // Material-UI theming
import CssBaseline from '@mui/material/CssBaseline'; // CSS baseline for consistent styling
import App from './App';
import { store } from './store/store'; // Redux store configuration
import './index.css';

// Create Material-UI theme with Walmart branding colors
const theme = createTheme({
  palette: {
    primary: {
      main: '#004c91', // Walmart blue
      light: '#3d7bc7',
      dark: '#003366',
    },
    secondary: {
      main: '#ffc220', // Walmart yellow
      light: '#ffcf4d',
      dark: '#cc9b00',
    },
    background: {
      default: '#f5f5f5', // Light gray background
      paper: '#ffffff',
    },
    error: {
      main: '#d32f2f', // Red for fraud alerts
    },
    success: {
      main: '#2e7d32', // Green for secure transactions
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif', // Clean, modern font
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
  },
  components: {
    // Custom button styling to match Walmart design
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8, // Rounded corners
          textTransform: 'none', // Preserve text case
          fontWeight: 500,
        },
      },
    },
    // Custom card styling for transaction displays
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)', // Subtle shadow
          borderRadius: 12,
        },
      },
    },
  },
});

// Get the root element from DOM
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// Render the application with all providers
root.render(
  <React.StrictMode>
    {/* Redux Provider for state management across the app */}
    <Provider store={store}>
      {/* Router Provider for navigation between pages */}
      <BrowserRouter>
        {/* Material-UI Theme Provider for consistent styling */}
        <ThemeProvider theme={theme}>
          {/* CSS Baseline for consistent cross-browser styling */}
          <CssBaseline />
          {/* Main App component */}
          <App />
        </ThemeProvider>
      </BrowserRouter>
    </Provider>
  </React.StrictMode>
);
