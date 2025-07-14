import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Define the structure of user data
interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'analyst' | 'viewer'; // Different permission levels
  lastLogin: string;
}

// Define the authentication state structure
interface AuthState {
  isAuthenticated: boolean; // Whether user is logged in
  user: User | null; // Current user information
  token: string | null; // JWT token for API authentication
  loading: boolean; // Loading state for login/logout operations
  error: string | null; // Error message for failed operations
}

// Initial state when app starts
const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  loading: false,
  error: null,
};

// Create Redux slice for authentication management
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    // Action to start login process (shows loading state)
    loginStart: (state) => {
      state.loading = true;
      state.error = null;
    },

    // Action when login succeeds (stores user data and token)
    loginSuccess: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.isAuthenticated = true;
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.loading = false;
      state.error = null;

      // Store token in localStorage for persistence across browser sessions
      localStorage.setItem('auth_token', action.payload.token);
    },

    // Action when login fails (stores error message)
    loginFailure: (state, action: PayloadAction<string>) => {
      state.isAuthenticated = false;
      state.user = null;
      state.token = null;
      state.loading = false;
      state.error = action.payload;
    },

    // Action to log out user (clears all auth data)
    logout: (state) => {
      state.isAuthenticated = false;
      state.user = null;
      state.token = null;
      state.loading = false;
      state.error = null;

      // Remove token from localStorage
      localStorage.removeItem('auth_token');
    },

    // Action to clear any error messages
    clearError: (state) => {
      state.error = null;
    },

    // Action to restore authentication from localStorage (on app reload)
    restoreAuth: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.isAuthenticated = true;
      state.user = action.payload.user;
      state.token = action.payload.token;
    },
  },
});

// Export actions for use in components
export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  clearError,
  restoreAuth,
} = authSlice.actions;

// Export reducer for store configuration
export default authSlice.reducer;
