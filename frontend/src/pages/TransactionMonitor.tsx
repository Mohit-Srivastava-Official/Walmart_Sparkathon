import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Badge,
  Tooltip,
  Alert,
} from '@mui/material'; // Material-UI components
import {
  Visibility,
  Block,
  CheckCircle,
  Warning,
  LocationOn,
  CreditCard,
  Refresh,
  FilterList,
} from '@mui/icons-material'; // Material-UI icons
import { useAppSelector, useAppDispatch } from '../hooks/redux'; // Custom Redux hooks
import {
  updateTransactionStatus,
  markAlertInvestigated,
  updateFilters,
} from '../store/slices/transactionSlice'; // Transaction actions
import type { Transaction, FraudAlert } from '../store/slices/transactionSlice'; // Type imports

// Transaction Monitor page - real-time monitoring of transactions and fraud alerts
const TransactionMonitor: React.FC = () => {
  // Redux hooks for state management
  const dispatch = useAppDispatch();
  const { transactions, realTimeTransactions, alerts, filters, loading } = useAppSelector(
    (state) => state.transactions
  );

  // Local state for UI interactions
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [filtersDialogOpen, setFiltersDialogOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Effect to set up real-time updates
  useEffect(() => {
    if (!autoRefresh) return;

    // Set up auto-refresh timer (in real app, this would be WebSocket)
    const refreshTimer = setInterval(() => {
      // Simulate real-time transaction updates
      console.log('Refreshing real-time data...');
    }, 2000); // Update every 2 seconds

    return () => clearInterval(refreshTimer);
  }, [autoRefresh]);

  // Combine regular and real-time transactions
  const allTransactions = [...realTimeTransactions, ...transactions];

  // Filter transactions based on current filters
  const filteredTransactions = allTransactions.filter((transaction) => {
    // Status filter
    if (filters.status.length > 0 && !filters.status.includes(transaction.status)) {
      return false;
    }

    // Risk level filter
    if (filters.riskLevel !== 'all') {
      const riskThresholds = { low: 30, medium: 70, high: 90 };
      const maxRisk = riskThresholds[filters.riskLevel as keyof typeof riskThresholds];
      if (transaction.riskScore > maxRisk) {
        return false;
      }
    }

    // Amount range filter
    if (transaction.amount < filters.amountRange[0] || transaction.amount > filters.amountRange[1]) {
      return false;
    }

    return true;
  });

  // Get risk level color based on score
  const getRiskColor = (riskScore: number): 'success' | 'warning' | 'error' => {
    if (riskScore < 30) return 'success';
    if (riskScore < 70) return 'warning';
    return 'error';
  };

  // Get status color for transaction status
  const getStatusColor = (status: Transaction['status']): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'approved': return 'success';
      case 'flagged': return 'warning';
      case 'declined': return 'error';
      default: return 'default';
    }
  };

  // Handle transaction details view
  const handleViewDetails = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setDetailsDialogOpen(true);
  };

  // Handle transaction status update
  const handleStatusUpdate = (transactionId: string, newStatus: Transaction['status']) => {
    dispatch(updateTransactionStatus({ transactionId, status: newStatus }));
    setDetailsDialogOpen(false);
  };

  // Handle alert investigation
  const handleInvestigateAlert = (alertId: string, falsePositive: boolean = false) => {
    dispatch(markAlertInvestigated({ alertId, falsePositive }));
  };

  // Handle filter updates
  const handleFilterChange = (newFilters: Partial<typeof filters>) => {
    dispatch(updateFilters(newFilters));
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Page header with controls */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Transaction Monitor
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Real-time fraud detection and transaction monitoring
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {/* Auto-refresh toggle */}
          <Button
            variant={autoRefresh ? 'contained' : 'outlined'}
            startIcon={<Refresh />}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            Auto Refresh
          </Button>

          {/* Filters button */}
          <Button
            variant="outlined"
            startIcon={<FilterList />}
            onClick={() => setFiltersDialogOpen(true)}
          >
            Filters
          </Button>
        </Box>
      </Box>

      {/* Active alerts section */}
      {alerts.filter(alert => !alert.investigated).length > 0 && (
        <Card sx={{ mb: 3, border: '2px solid', borderColor: 'error.main' }}>
          <CardContent>
            <Typography variant="h6" color="error" gutterBottom>
              Active Security Alerts ({alerts.filter(alert => !alert.investigated).length})
            </Typography>

            <Grid container spacing={2}>
              {alerts.filter(alert => !alert.investigated).slice(0, 3).map((alert) => (
                <Grid item xs={12} md={4} key={alert.id}>
                  <Alert
                    severity={alert.severity === 'critical' ? 'error' : 'warning'}
                    action={
                      <Box>
                        <Button
                          size="small"
                          onClick={() => handleInvestigateAlert(alert.id)}
                        >
                          Investigate
                        </Button>
                        <Button
                          size="small"
                          onClick={() => handleInvestigateAlert(alert.id, true)}
                        >
                          False Positive
                        </Button>
                      </Box>
                    }
                  >
                    <Typography variant="subtitle2">{alert.alertType.replace('_', ' ').toUpperCase()}</Typography>
                    <Typography variant="body2">{alert.message}</Typography>
                    <Typography variant="caption" color="textSecondary">
                      {new Date(alert.timestamp).toLocaleString()}
                    </Typography>
                  </Alert>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Real-time transaction feed */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Live Transactions ({filteredTransactions.length})
            </Typography>

            {/* Live indicator */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: autoRefresh ? 'success.main' : 'grey.400',
                  animation: autoRefresh ? 'pulse 2s infinite' : 'none',
                }}
              />
              <Typography variant="caption" color="textSecondary">
                {autoRefresh ? 'LIVE' : 'PAUSED'}
              </Typography>
            </Box>
          </Box>

          {/* Transactions table */}
          <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Transaction ID</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Merchant</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell>Risk Score</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredTransactions.slice(0, 50).map((transaction) => (
                  <TableRow key={transaction.id} hover>
                    {/* Timestamp */}
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(transaction.timestamp).toLocaleTimeString()}
                      </Typography>
                    </TableCell>

                    {/* Transaction ID */}
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {transaction.id.slice(-8)}
                      </Typography>
                    </TableCell>

                    {/* Amount */}
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        ${transaction.amount.toLocaleString()} {transaction.currency}
                      </Typography>
                    </TableCell>

                    {/* Merchant */}
                    <TableCell>
                      <Box>
                        <Typography variant="body2">{transaction.merchantName}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          {transaction.merchantCategory}
                        </Typography>
                      </Box>
                    </TableCell>

                    {/* Location */}
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <LocationOn fontSize="small" color="action" />
                        <Typography variant="body2">
                          {transaction.location.city}, {transaction.location.country}
                        </Typography>
                      </Box>
                    </TableCell>

                    {/* Risk Score */}
                    <TableCell>
                      <Chip
                        label={`${transaction.riskScore}%`}
                        size="small"
                        color={getRiskColor(transaction.riskScore)}
                        variant="outlined"
                      />
                    </TableCell>

                    {/* Status */}
                    <TableCell>
                      <Chip
                        label={transaction.status.toUpperCase()}
                        size="small"
                        color={getStatusColor(transaction.status)}
                        variant="filled"
                      />
                    </TableCell>

                    {/* Actions */}
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => handleViewDetails(transaction)}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>

                        {transaction.status === 'flagged' && (
                          <>
                            <Tooltip title="Approve">
                              <IconButton
                                size="small"
                                color="success"
                                onClick={() => handleStatusUpdate(transaction.id, 'approved')}
                              >
                                <CheckCircle />
                              </IconButton>
                            </Tooltip>

                            <Tooltip title="Block">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleStatusUpdate(transaction.id, 'declined')}
                              >
                                <Block />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {filteredTransactions.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="textSecondary">
                No transactions match the current filters.
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Transaction Details Dialog */}
      <Dialog
        open={detailsDialogOpen}
        onClose={() => setDetailsDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Transaction Details
          {selectedTransaction && (
            <Chip
              label={selectedTransaction.status.toUpperCase()}
              size="small"
              color={getStatusColor(selectedTransaction.status)}
              sx={{ ml: 2 }}
            />
          )}
        </DialogTitle>

        <DialogContent>
          {selectedTransaction && (
            <Grid container spacing={2}>
              {/* Basic transaction info */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Transaction Information</Typography>
                <Typography variant="body2"><strong>ID:</strong> {selectedTransaction.id}</Typography>
                <Typography variant="body2"><strong>Amount:</strong> ${selectedTransaction.amount} {selectedTransaction.currency}</Typography>
                <Typography variant="body2"><strong>Timestamp:</strong> {new Date(selectedTransaction.timestamp).toLocaleString()}</Typography>
                <Typography variant="body2"><strong>Risk Score:</strong> {selectedTransaction.riskScore}%</Typography>
                <Typography variant="body2"><strong>Fraud Probability:</strong> {(selectedTransaction.fraudProbability * 100).toFixed(1)}%</Typography>
              </Grid>

              {/* Merchant info */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Merchant Information</Typography>
                <Typography variant="body2"><strong>Name:</strong> {selectedTransaction.merchantName}</Typography>
                <Typography variant="body2"><strong>Category:</strong> {selectedTransaction.merchantCategory}</Typography>
                <Typography variant="body2"><strong>Location:</strong> {selectedTransaction.location.city}, {selectedTransaction.location.country}</Typography>
                <Typography variant="body2"><strong>Coordinates:</strong> {selectedTransaction.location.coordinates.join(', ')}</Typography>
              </Grid>

              {/* Payment info */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Payment Information</Typography>
                <Typography variant="body2"><strong>Method:</strong> {selectedTransaction.paymentMethod.replace('_', ' ').toUpperCase()}</Typography>
                <Typography variant="body2"><strong>User ID:</strong> {selectedTransaction.userId}</Typography>
                {selectedTransaction.blockchainHash && (
                  <Typography variant="body2"><strong>Blockchain Hash:</strong> {selectedTransaction.blockchainHash}</Typography>
                )}
              </Grid>

              {/* Device info */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Device Information</Typography>
                <Typography variant="body2"><strong>Device ID:</strong> {selectedTransaction.deviceInfo.deviceId}</Typography>
                <Typography variant="body2"><strong>IP Address:</strong> {selectedTransaction.deviceInfo.ipAddress}</Typography>
                <Typography variant="body2"><strong>User Agent:</strong> {selectedTransaction.deviceInfo.userAgent.slice(0, 50)}...</Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>

        <DialogActions>
          {selectedTransaction?.status === 'flagged' && (
            <>
              <Button
                color="success"
                variant="contained"
                onClick={() => handleStatusUpdate(selectedTransaction.id, 'approved')}
              >
                Approve Transaction
              </Button>

              <Button
                color="error"
                variant="contained"
                onClick={() => handleStatusUpdate(selectedTransaction.id, 'declined')}
              >
                Block Transaction
              </Button>
            </>
          )}

          <Button onClick={() => setDetailsDialogOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Filters Dialog */}
      <Dialog
        open={filtersDialogOpen}
        onClose={() => setFiltersDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Filter Transactions</DialogTitle>

        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {/* Status filter */}
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  multiple
                  value={filters.status}
                  onChange={(e) => handleFilterChange({ status: e.target.value as string[] })}
                >
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="approved">Approved</MenuItem>
                  <MenuItem value="declined">Declined</MenuItem>
                  <MenuItem value="flagged">Flagged</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Risk level filter */}
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Risk Level</InputLabel>
                <Select
                  value={filters.riskLevel}
                  onChange={(e) => handleFilterChange({ riskLevel: e.target.value })}
                >
                  <MenuItem value="all">All Risk Levels</MenuItem>
                  <MenuItem value="low">Low Risk (0-30%)</MenuItem>
                  <MenuItem value="medium">Medium Risk (31-70%)</MenuItem>
                  <MenuItem value="high">High Risk (71-100%)</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Amount range filter */}
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Min Amount"
                type="number"
                value={filters.amountRange[0]}
                onChange={(e) => handleFilterChange({
                  amountRange: [Number(e.target.value), filters.amountRange[1]]
                })}
              />
            </Grid>

            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Max Amount"
                type="number"
                value={filters.amountRange[1]}
                onChange={(e) => handleFilterChange({
                  amountRange: [filters.amountRange[0], Number(e.target.value)]
                })}
              />
            </Grid>
          </Grid>
        </DialogContent>

        <DialogActions>
          <Button onClick={() => handleFilterChange({
            status: [],
            riskLevel: 'all',
            amountRange: [0, 10000]
          })}>
            Clear Filters
          </Button>

          <Button onClick={() => setFiltersDialogOpen(false)} variant="contained">
            Apply Filters
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TransactionMonitor;
