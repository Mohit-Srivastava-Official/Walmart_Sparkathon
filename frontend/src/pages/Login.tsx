import React, { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  Avatar,
  Container,
  CircularProgress,
  FormControlLabel,
  Checkbox,
} from '@mui/material'; // Material-UI components
import { Security, Login as LoginIcon } from '@mui/icons-material'; // Material-UI icons
import { useAppDispatch, useAppSelector } from '../hooks/redux'; // Custom Redux hooks
import { loginStart, loginSuccess, loginFailure } from '../store/slices/authSlice'; // Auth actions
import axios from 'axios'; // HTTP client for API calls

// Login page component for user authentication
const Login: React.FC = () => {
  // Redux hooks for state management
  const dispatch = useAppDispatch();
  const { loading, error } = useAppSelector((state) => state.auth);

  // Local state for form data
  const [formData, setFormData] = useState({
    email: '', // User email address
    password: '', // User password
    rememberMe: false, // Remember login checkbox
  });

  // Local state for form validation errors
  const [formErrors, setFormErrors] = useState({
    email: '',
    password: '',
  });

  // Handle input field changes
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked } = event.target;

    // Update form data based on input type
    setFormData(prev => ({
      ...prev,
      [name]: name === 'rememberMe' ? checked : value,
    }));

    // Clear validation error when user starts typing
    if (formErrors[name as keyof typeof formErrors]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  // Validate form inputs
  const validateForm = (): boolean => {
    const errors = {
      email: '',
      password: '',
    };

    // Email validation
    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Email format is invalid';
    }

    // Password validation
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    setFormErrors(errors);

    // Return true if no errors
    return !errors.email && !errors.password;
  };

  // Handle form submission
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); // Prevent default form submission

    // Validate form before submission
    if (!validateForm()) {
      return;
    }

    // Start login process (show loading state)
    dispatch(loginStart());

    try {
      // Make API call to authenticate user
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
      const response = await axios.post(`${apiUrl}/auth/login`, {
        email: formData.email,
        password: formData.password,
        rememberMe: formData.rememberMe,
      });

      // Extract user data and token from response
      const { user, token } = response.data;

      // Dispatch success action with user data
      dispatch(loginSuccess({ user, token }));

      // Note: App component will automatically redirect to dashboard
      // when isAuthenticated becomes true

    } catch (error: any) {
      // Handle login errors
      let errorMessage = 'Login failed. Please try again.';

      if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.response?.status === 401) {
        errorMessage = 'Invalid email or password';
      } else if (error.response?.status >= 500) {
        errorMessage = 'Server error. Please try again later.';
      }

      // Dispatch failure action with error message
      dispatch(loginFailure(errorMessage));
    }
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          py: 4,
        }}
      >
        {/* Login form container */}
        <Paper
          elevation={3}
          sx={{
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
            maxWidth: 400,
          }}
        >
          {/* Application logo and title */}
          <Avatar sx={{ m: 1, bgcolor: 'primary.main', width: 56, height: 56 }}>
            <Security fontSize="large" />
          </Avatar>

          <Typography component="h1" variant="h4" gutterBottom>
            SecureCart AI
          </Typography>

          <Typography variant="body2" color="textSecondary" textAlign="center" sx={{ mb: 3 }}>
            Advanced Fraud Detection System
          </Typography>

          {/* Error message display */}
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Login form */}
          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
            {/* Email input field */}
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              autoFocus
              value={formData.email}
              onChange={handleInputChange}
              error={Boolean(formErrors.email)}
              helperText={formErrors.email}
              disabled={loading}
            />

            {/* Password input field */}
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={handleInputChange}
              error={Boolean(formErrors.password)}
              helperText={formErrors.password}
              disabled={loading}
            />

            {/* Remember me checkbox */}
            <FormControlLabel
              control={
                <Checkbox
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleInputChange}
                  color="primary"
                  disabled={loading}
                />
              }
              label="Remember me"
              sx={{ mt: 1 }}
            />

            {/* Submit button */}
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2, py: 1.5 }}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <LoginIcon />}
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </Button>

            {/* Demo credentials helper */}
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="caption" color="textSecondary" component="div" textAlign="center">
                Demo Credentials:
              </Typography>
              <Typography variant="caption" component="div" textAlign="center">
                Email: admin@walmart.com
              </Typography>
              <Typography variant="caption" component="div" textAlign="center">
                Password: securepass123
              </Typography>
            </Box>
          </Box>

          {/* Footer information */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="caption" color="textSecondary">
              Walmart Sparkathon 2025 - Cybersecurity Innovation
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
