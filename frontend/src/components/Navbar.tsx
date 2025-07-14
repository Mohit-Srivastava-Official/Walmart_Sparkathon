import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Box,
  Badge,
  Tooltip,
} from '@mui/material'; // Material-UI components for navigation
import {
  AccountCircle,
  Notifications,
  Security,
  Dashboard,
  Analytics,
  Settings,
  Logout,
} from '@mui/icons-material'; // Material-UI icons
import { useNavigate, useLocation } from 'react-router-dom'; // React Router for navigation
import { useAppSelector, useAppDispatch } from '../hooks/redux'; // Custom Redux hooks
import { logout } from '../store/slices/authSlice'; // Logout action

// Navigation bar component that appears on all authenticated pages
const Navbar: React.FC = () => {
  // React Router hooks for navigation and current location
  const navigate = useNavigate();
  const location = useLocation();

  // Redux hooks for state management
  const dispatch = useAppDispatch();
  const user = useAppSelector((state) => state.auth.user); // Current user info
  const alerts = useAppSelector((state) => state.transactions.alerts); // Fraud alerts

  // Local state for user menu dropdown
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);

  // Count unread alerts (not investigated)
  const unreadAlerts = alerts.filter(alert => !alert.investigated).length;

  // Handle user menu open
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  // Handle user menu close
  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // Handle navigation to different pages
  const handleNavigate = (path: string) => {
    navigate(path);
  };

  // Handle user logout
  const handleLogout = () => {
    dispatch(logout()); // Clear authentication state
    handleMenuClose();
  };

  // Determine if a navigation button should be highlighted (current page)
  const isCurrentPage = (path: string) => {
    return location.pathname === path;
  };

  return (
    <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        {/* Logo and application title */}
        <Security sx={{ mr: 2, color: 'secondary.main' }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 0, mr: 4 }}>
          SecureCart AI
        </Typography>

        {/* Navigation buttons */}
        <Box sx={{ flexGrow: 1, display: 'flex', gap: 1 }}>
          {/* Dashboard button */}
          <Button
            color="inherit"
            startIcon={<Dashboard />}
            onClick={() => handleNavigate('/')}
            sx={{
              backgroundColor: isCurrentPage('/') ? 'rgba(255,255,255,0.1)' : 'transparent',
              '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
            }}
          >
            Dashboard
          </Button>

          {/* Transaction Monitor button */}
          <Button
            color="inherit"
            startIcon={<Security />}
            onClick={() => handleNavigate('/transactions')}
            sx={{
              backgroundColor: isCurrentPage('/transactions') ? 'rgba(255,255,255,0.1)' : 'transparent',
              '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
            }}
          >
            Transactions
          </Button>

          {/* Analytics button */}
          <Button
            color="inherit"
            startIcon={<Analytics />}
            onClick={() => handleNavigate('/analytics')}
            sx={{
              backgroundColor: isCurrentPage('/analytics') ? 'rgba(255,255,255,0.1)' : 'transparent',
              '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
            }}
          >
            Analytics
          </Button>

          {/* Settings button */}
          <Button
            color="inherit"
            startIcon={<Settings />}
            onClick={() => handleNavigate('/settings')}
            sx={{
              backgroundColor: isCurrentPage('/settings') ? 'rgba(255,255,255,0.1)' : 'transparent',
              '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
            }}
          >
            Settings
          </Button>
        </Box>

        {/* Right side actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Notification bell with alert count */}
          <Tooltip title="Fraud Alerts">
            <IconButton
              color="inherit"
              onClick={() => handleNavigate('/transactions')}
            >
              <Badge badgeContent={unreadAlerts} color="error">
                <Notifications />
              </Badge>
            </IconButton>
          </Tooltip>

          {/* User menu */}
          <Tooltip title="User Menu">
            <IconButton
              color="inherit"
              onClick={handleMenuOpen}
              aria-controls={menuOpen ? 'user-menu' : undefined}
              aria-haspopup="true"
              aria-expanded={menuOpen ? 'true' : undefined}
            >
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </Avatar>
            </IconButton>
          </Tooltip>

          {/* User dropdown menu */}
          <Menu
            id="user-menu"
            anchorEl={anchorEl}
            open={menuOpen}
            onClose={handleMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
          >
            {/* User info header */}
            <MenuItem disabled>
              <Box>
                <Typography variant="subtitle2">{user?.name}</Typography>
                <Typography variant="caption" color="textSecondary">
                  {user?.email}
                </Typography>
                <Typography variant="caption" color="textSecondary" display="block">
                  Role: {user?.role}
                </Typography>
              </Box>
            </MenuItem>

            {/* Profile menu item */}
            <MenuItem onClick={handleMenuClose}>
              <AccountCircle sx={{ mr: 1 }} />
              Profile
            </MenuItem>

            {/* Settings menu item */}
            <MenuItem onClick={() => { handleNavigate('/settings'); handleMenuClose(); }}>
              <Settings sx={{ mr: 1 }} />
              Settings
            </MenuItem>

            {/* Logout menu item */}
            <MenuItem onClick={handleLogout}>
              <Logout sx={{ mr: 1 }} />
              Logout
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
