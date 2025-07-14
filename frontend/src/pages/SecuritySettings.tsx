import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Switch,
  FormControlLabel,
  Slider,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Snackbar,
} from '@mui/material'; // Material-UI components
import {
  Settings,
  Save,
  Add,
  Edit,
  Delete,
  Security,
  Notifications,
  Tune,
  SettingsApplications,
  Warning,
  CheckCircle,
} from '@mui/icons-material'; // Material-UI icons
import { useAppSelector, useAppDispatch } from '../hooks/redux'; // Custom Redux hooks
import {
  updateNotificationSettings,
  updateModelSettings,
  updateApiSettings,
  addSecurityRule,
  updateSecurityRule,
  deleteSecurityRule,
  toggleSecurityRule,
  saveSettingsSuccess,
  updateFraudThreshold,
} from '../store/slices/securitySlice'; // Security settings actions
import type { SecurityRule, NotificationSettings } from '../store/slices/securitySlice'; // Type imports

// Security Settings page - comprehensive configuration for fraud detection system
const SecuritySettings: React.FC = () => {
  // Redux hooks for state management
  const dispatch = useAppDispatch();
  const {
    rules,
    notifications,
    modelSettings,
    apiSettings,
    loading,
    error,
    unsavedChanges,
    lastSaved,
  } = useAppSelector((state) => state.security);

  // Local state for UI interactions
  const [activeTab, setActiveTab] = useState<'rules' | 'notifications' | 'model' | 'api'>('rules');
  const [ruleDialogOpen, setRuleDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<SecurityRule | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // New rule form state
  const [newRule, setNewRule] = useState<Partial<SecurityRule>>({
    name: '',
    description: '',
    enabled: true,
    ruleType: 'threshold',
    parameters: {},
    priority: 5,
    actions: ['flag'],
  });

  // Handle rule creation/editing
  const handleSaveRule = () => {
    if (!newRule.name || !newRule.description) {
      setSnackbarMessage('Please fill in all required fields');
      setSnackbarOpen(true);
      return;
    }

    const ruleData: SecurityRule = {
      id: editingRule?.id || `rule_${Date.now()}`,
      name: newRule.name!,
      description: newRule.description!,
      enabled: newRule.enabled!,
      ruleType: newRule.ruleType!,
      parameters: newRule.parameters!,
      priority: newRule.priority!,
      actions: newRule.actions!,
      lastModified: new Date().toISOString(),
      createdBy: 'current_user', // Would be actual user ID
    };

    if (editingRule) {
      dispatch(updateSecurityRule(ruleData));
      setSnackbarMessage('Rule updated successfully');
    } else {
      dispatch(addSecurityRule(ruleData));
      setSnackbarMessage('Rule created successfully');
    }

    setRuleDialogOpen(false);
    setEditingRule(null);
    setNewRule({
      name: '',
      description: '',
      enabled: true,
      ruleType: 'threshold',
      parameters: {},
      priority: 5,
      actions: ['flag'],
    });
    setSnackbarOpen(true);
  };

  // Handle rule editing
  const handleEditRule = (rule: SecurityRule) => {
    setEditingRule(rule);
    setNewRule(rule);
    setRuleDialogOpen(true);
  };

  // Handle rule deletion
  const handleDeleteRule = (ruleId: string) => {
    dispatch(deleteSecurityRule(ruleId));
    setSnackbarMessage('Rule deleted successfully');
    setSnackbarOpen(true);
  };

  // Handle notification settings update
  const handleNotificationUpdate = (updates: Partial<NotificationSettings>) => {
    dispatch(updateNotificationSettings(updates));
  };

  // Handle model settings update
  const handleModelUpdate = (field: string, value: any) => {
    dispatch(updateModelSettings({ [field]: value }));
  };

  // Handle API settings update
  const handleApiUpdate = (field: string, value: any) => {
    dispatch(updateApiSettings({ [field]: value }));
  };

  // Handle save all settings
  const handleSaveAllSettings = () => {
    // In real app, this would make API call to save all settings
    dispatch(saveSettingsSuccess());
    setSnackbarMessage('All settings saved successfully');
    setSnackbarOpen(true);
  };

  // Get rule type color
  const getRuleTypeColor = (ruleType: string): 'primary' | 'secondary' | 'success' | 'warning' | 'error' => {
    switch (ruleType) {
      case 'threshold': return 'primary';
      case 'pattern': return 'secondary';
      case 'ml_model': return 'success';
      case 'blacklist': return 'error';
      case 'whitelist': return 'warning';
      default: return 'primary';
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Page header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Security Settings
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Configure fraud detection rules, notifications, and system parameters
          </Typography>
          {lastSaved && (
            <Typography variant="caption" color="textSecondary">
              Last saved: {new Date(lastSaved).toLocaleString()}
            </Typography>
          )}
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {unsavedChanges && (
            <Alert severity="warning" sx={{ mr: 2 }}>
              You have unsaved changes
            </Alert>
          )}

          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSaveAllSettings}
            disabled={!unsavedChanges || loading}
          >
            Save All Changes
          </Button>
        </Box>
      </Box>

      {/* Error display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Tab navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {[
            { key: 'rules', label: 'Security Rules', icon: <Security /> },
            { key: 'notifications', label: 'Notifications', icon: <Notifications /> },
            { key: 'model', label: 'Model Settings', icon: <Tune /> },
            { key: 'api', label: 'API & Integration', icon: <SettingsApplications /> },
          ].map((tab) => (
            <Button
              key={tab.key}
              variant={activeTab === tab.key ? 'contained' : 'text'}
              startIcon={tab.icon}
              onClick={() => setActiveTab(tab.key as any)}
              sx={{ mb: 1 }}
            >
              {tab.label}
            </Button>
          ))}
        </Box>
      </Box>

      {/* Security Rules Tab */}
      {activeTab === 'rules' && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Security Rules ({rules.length})</Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setRuleDialogOpen(true)}
                  >
                    Add Rule
                  </Button>
                </Box>

                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Priority</TableCell>
                        <TableCell>Actions</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Controls</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {rules.map((rule) => (
                        <TableRow key={rule.id} hover>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {rule.name}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                {rule.description}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={rule.ruleType.replace('_', ' ').toUpperCase()}
                              size="small"
                              color={getRuleTypeColor(rule.ruleType)}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">{rule.priority}</Typography>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              {rule.actions.map((action) => (
                                <Chip
                                  key={action}
                                  label={action.toUpperCase()}
                                  size="small"
                                  variant="outlined"
                                />
                              ))}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <FormControlLabel
                              control={
                                <Switch
                                  checked={rule.enabled}
                                  onChange={() => dispatch(toggleSecurityRule(rule.id))}
                                  size="small"
                                />
                              }
                              label={rule.enabled ? 'Enabled' : 'Disabled'}
                            />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              <Tooltip title="Edit Rule">
                                <IconButton size="small" onClick={() => handleEditRule(rule)}>
                                  <Edit />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Delete Rule">
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => handleDeleteRule(rule.id)}
                                >
                                  <Delete />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <Grid container spacing={3}>
          {/* Email notifications */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Email Notifications
                </Typography>

                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications.email.enabled}
                      onChange={(e) => handleNotificationUpdate({
                        email: { ...notifications.email, enabled: e.target.checked }
                      })}
                    />
                  }
                  label="Enable Email Notifications"
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  label="Email Addresses (comma separated)"
                  value={notifications.email.addresses.join(', ')}
                  onChange={(e) => handleNotificationUpdate({
                    email: {
                      ...notifications.email,
                      addresses: e.target.value.split(',').map(email => email.trim())
                    }
                  })}
                  disabled={!notifications.email.enabled}
                  sx={{ mb: 2 }}
                />

                <FormControl fullWidth disabled={!notifications.email.enabled}>
                  <InputLabel>Severity Levels</InputLabel>
                  <Select
                    multiple
                    value={notifications.email.severity}
                    onChange={(e) => handleNotificationUpdate({
                      email: {
                        ...notifications.email,
                        severity: e.target.value as any
                      }
                    })}
                  >
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="critical">Critical</MenuItem>
                  </Select>
                </FormControl>
              </CardContent>
            </Card>
          </Grid>

          {/* SMS notifications */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  SMS Notifications
                </Typography>

                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications.sms.enabled}
                      onChange={(e) => handleNotificationUpdate({
                        sms: { ...notifications.sms, enabled: e.target.checked }
                      })}
                    />
                  }
                  label="Enable SMS Notifications"
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  label="Phone Numbers (comma separated)"
                  value={notifications.sms.phoneNumbers.join(', ')}
                  onChange={(e) => handleNotificationUpdate({
                    sms: {
                      ...notifications.sms,
                      phoneNumbers: e.target.value.split(',').map(phone => phone.trim())
                    }
                  })}
                  disabled={!notifications.sms.enabled}
                  sx={{ mb: 2 }}
                />

                <FormControl fullWidth disabled={!notifications.sms.enabled}>
                  <InputLabel>Severity Levels</InputLabel>
                  <Select
                    multiple
                    value={notifications.sms.severity}
                    onChange={(e) => handleNotificationUpdate({
                      sms: {
                        ...notifications.sms,
                        severity: e.target.value as any
                      }
                    })}
                  >
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="critical">Critical</MenuItem>
                  </Select>
                </FormControl>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Model Settings Tab */}
      {activeTab === 'model' && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Fraud Detection Model
                </Typography>

                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>Current Model</InputLabel>
                  <Select
                    value={modelSettings.currentModel}
                    onChange={(e) => handleModelUpdate('currentModel', e.target.value)}
                  >
                    {modelSettings.availableModels.map((model) => (
                      <MenuItem key={model} value={model}>{model}</MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <Typography gutterBottom>
                  Fraud Threshold: {(modelSettings.threshold * 100).toFixed(0)}%
                </Typography>
                <Slider
                  value={modelSettings.threshold * 100}
                  onChange={(_, value) => dispatch(updateFraudThreshold((value as number) / 100))}
                  min={0}
                  max={100}
                  step={1}
                  marks={[
                    { value: 0, label: '0%' },
                    { value: 50, label: '50%' },
                    { value: 100, label: '100%' },
                  ]}
                  sx={{ mb: 3 }}
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={modelSettings.retirningEnabled}
                      onChange={(e) => handleModelUpdate('retirningEnabled', e.target.checked)}
                    />
                  }
                  label="Enable Automatic Retraining"
                  sx={{ mb: 2 }}
                />

                <FormControl fullWidth>
                  <InputLabel>Retraining Schedule</InputLabel>
                  <Select
                    value={modelSettings.retrainingSchedule}
                    onChange={(e) => handleModelUpdate('retrainingSchedule', e.target.value)}
                    disabled={!modelSettings.retirningEnabled}
                  >
                    <MenuItem value="daily">Daily</MenuItem>
                    <MenuItem value="weekly">Weekly</MenuItem>
                    <MenuItem value="monthly">Monthly</MenuItem>
                  </Select>
                </FormControl>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Targets
                </Typography>

                <Typography gutterBottom>
                  Minimum Accuracy: {modelSettings.performanceTarget.minAccuracy}%
                </Typography>
                <Slider
                  value={modelSettings.performanceTarget.minAccuracy}
                  onChange={(_, value) => handleModelUpdate('performanceTarget', {
                    ...modelSettings.performanceTarget,
                    minAccuracy: value as number
                  })}
                  min={80}
                  max={99}
                  step={1}
                  marks={[
                    { value: 80, label: '80%' },
                    { value: 90, label: '90%' },
                    { value: 99, label: '99%' },
                  ]}
                  sx={{ mb: 3 }}
                />

                <Typography gutterBottom>
                  Max False Positives: {modelSettings.performanceTarget.maxFalsePositives}%
                </Typography>
                <Slider
                  value={modelSettings.performanceTarget.maxFalsePositives}
                  onChange={(_, value) => handleModelUpdate('performanceTarget', {
                    ...modelSettings.performanceTarget,
                    maxFalsePositives: value as number
                  })}
                  min={1}
                  max={20}
                  step={1}
                  marks={[
                    { value: 1, label: '1%' },
                    { value: 10, label: '10%' },
                    { value: 20, label: '20%' },
                  ]}
                  sx={{ mb: 3 }}
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={modelSettings.autoTuning}
                      onChange={(e) => handleModelUpdate('autoTuning', e.target.checked)}
                    />
                  }
                  label="Enable Auto-tuning"
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* API Settings Tab */}
      {activeTab === 'api' && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Rate Limiting
                </Typography>

                <FormControlLabel
                  control={
                    <Switch
                      checked={apiSettings.rateLimit.enabled}
                      onChange={(e) => handleApiUpdate('rateLimit', {
                        ...apiSettings.rateLimit,
                        enabled: e.target.checked
                      })}
                    />
                  }
                  label="Enable Rate Limiting"
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  label="Requests Per Minute"
                  type="number"
                  value={apiSettings.rateLimit.requestsPerMinute}
                  onChange={(e) => handleApiUpdate('rateLimit', {
                    ...apiSettings.rateLimit,
                    requestsPerMinute: Number(e.target.value)
                  })}
                  disabled={!apiSettings.rateLimit.enabled}
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  label="Burst Limit"
                  type="number"
                  value={apiSettings.rateLimit.burstLimit}
                  onChange={(e) => handleApiUpdate('rateLimit', {
                    ...apiSettings.rateLimit,
                    burstLimit: Number(e.target.value)
                  })}
                  disabled={!apiSettings.rateLimit.enabled}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Blockchain Integration
                </Typography>

                <FormControlLabel
                  control={
                    <Switch
                      checked={apiSettings.blockchain.enabled}
                      onChange={(e) => handleApiUpdate('blockchain', {
                        ...apiSettings.blockchain,
                        enabled: e.target.checked
                      })}
                    />
                  }
                  label="Enable Blockchain Integration"
                  sx={{ mb: 2 }}
                />

                <FormControl fullWidth sx={{ mb: 2 }} disabled={!apiSettings.blockchain.enabled}>
                  <InputLabel>Network</InputLabel>
                  <Select
                    value={apiSettings.blockchain.network}
                    onChange={(e) => handleApiUpdate('blockchain', {
                      ...apiSettings.blockchain,
                      network: e.target.value
                    })}
                  >
                    <MenuItem value="mainnet">Mainnet</MenuItem>
                    <MenuItem value="testnet">Testnet</MenuItem>
                  </Select>
                </FormControl>

                <TextField
                  fullWidth
                  label="Confirmations Required"
                  type="number"
                  value={apiSettings.blockchain.confirmations}
                  onChange={(e) => handleApiUpdate('blockchain', {
                    ...apiSettings.blockchain,
                    confirmations: Number(e.target.value)
                  })}
                  disabled={!apiSettings.blockchain.enabled}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Rule Dialog */}
      <Dialog
        open={ruleDialogOpen}
        onClose={() => setRuleDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingRule ? 'Edit Security Rule' : 'Add New Security Rule'}
        </DialogTitle>

        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Rule Name"
                value={newRule.name || ''}
                onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                required
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={3}
                value={newRule.description || ''}
                onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                required
              />
            </Grid>

            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Rule Type</InputLabel>
                <Select
                  value={newRule.ruleType || 'threshold'}
                  onChange={(e) => setNewRule({ ...newRule, ruleType: e.target.value as any })}
                >
                  <MenuItem value="threshold">Threshold</MenuItem>
                  <MenuItem value="pattern">Pattern</MenuItem>
                  <MenuItem value="ml_model">ML Model</MenuItem>
                  <MenuItem value="blacklist">Blacklist</MenuItem>
                  <MenuItem value="whitelist">Whitelist</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Priority (1-10)"
                type="number"
                value={newRule.priority || 5}
                onChange={(e) => setNewRule({ ...newRule, priority: Number(e.target.value) })}
                inputProps={{ min: 1, max: 10 }}
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={newRule.enabled || true}
                    onChange={(e) => setNewRule({ ...newRule, enabled: e.target.checked })}
                  />
                }
                label="Enabled"
              />
            </Grid>
          </Grid>
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setRuleDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSaveRule} variant="contained">
            {editingRule ? 'Update Rule' : 'Create Rule'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default SecuritySettings;
