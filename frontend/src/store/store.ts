import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice'; // Authentication state management
import transactionReducer from './slices/transactionSlice'; // Transaction monitoring state
import fraudReducer from './slices/fraudSlice'; // Fraud detection analytics state
import securityReducer from './slices/securitySlice'; // Security settings state

// Configure Redux store with all application slices
// This centralizes all state management for the application
export const store = configureStore({
  reducer: {
    // Authentication state - handles login, logout, user info
    auth: authReducer,

    // Transaction state - manages real-time transaction data
    transactions: transactionReducer,

    // Fraud detection state - stores fraud patterns and alerts
    fraud: fraudReducer,

    // Security settings state - configuration and preferences
    security: securityReducer,
  },

  // Redux DevTools configuration for development debugging
  devTools: process.env.NODE_ENV !== 'production',

  // Middleware configuration
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      // Disable serializable check for better performance with large datasets
      serializableCheck: {
        ignoredActions: ['transactions/updateRealtime'],
      },
    }),
});

// Export types for TypeScript support
// RootState type represents the entire Redux state tree
export type RootState = ReturnType<typeof store.getState>;

// AppDispatch type represents the store's dispatch function
export type AppDispatch = typeof store.dispatch;
