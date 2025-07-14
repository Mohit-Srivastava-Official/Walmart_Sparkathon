import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Avatar,
  Chip,
  LinearProgress,
} from '@mui/material'; // Material-UI components
import {
  Security,
  TrendingUp,
  Block,
  CheckCircle,
  Warning,
  Speed,
  AccountBalance,
  Analytics,
} from '@mui/icons-material'; // Material-UI icons
import { Line, Doughnut, Bar } from 'react-chartjs-2'; // Chart.js React components
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
} from 'chart.js'; // Chart.js components
import { useAppSelector, useAppDispatch } from '../hooks/redux'; // Custom Redux hooks
import { fetchTransactionsStart } from '../store/slices/transactionSlice'; // Transaction actions

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
);

// Dashboard page component - main overview of fraud detection system
const Dashboard: React.FC = () => {
  // Redux hooks for state management
  const dispatch = useAppDispatch();
  const user = useAppSelector((state) => state.auth.user); // Current user
  const { transactions, alerts, totalAmount, averageRiskScore, loading } = useAppSelector(
    (state) => state.transactions
  ); // Transaction data
  const fraudStats = useAppSelector((state) => state.fraud.stats); // Fraud statistics

  // Local state for real-time updates
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Effect to load initial data and set up real-time updates
  useEffect(() => {
    // Load transactions on component mount
    dispatch(fetchTransactionsStart());

    // Set up real-time update timer
    const updateTimer = setInterval(() => {
      setLastUpdate(new Date());
      // In real app, this would trigger WebSocket updates
    }, 5000); // Update every 5 seconds

    // Cleanup timer on component unmount
    return () => clearInterval(updateTimer);
  }, [dispatch]);

  // Calculate dashboard metrics
  const todayTransactions = transactions.filter(t => {
    const today = new Date().toDateString();
    return new Date(t.timestamp).toDateString() === today;
  });

  const blockedTransactions = transactions.filter(t => t.status === 'declined').length;
  const flaggedTransactions = transactions.filter(t => t.status === 'flagged').length;
  const approvedTransactions = transactions.filter(t => t.status === 'approved').length;

  // Prepare chart data for transaction trends
  const transactionTrendData = {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'], // Time labels
    datasets: [
      {
        label: 'Transactions',
        data: [45, 23, 67, 123, 98, 76], // Sample data - would come from API
        borderColor: 'rgb(0, 76, 145)', // Walmart blue
        backgroundColor: 'rgba(0, 76, 145, 0.1)',
        fill: true,
      },
      {
        label: 'Fraud Detected',
        data: [2, 1, 3, 8, 5, 4], // Sample fraud data
        borderColor: 'rgb(211, 47, 47)', // Red for fraud
        backgroundColor: 'rgba(211, 47, 47, 0.1)',
        fill: true,
      },
    ],
  };

  // Risk distribution data for doughnut chart
  const riskDistributionData = {
    labels: ['Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk'],
    datasets: [
      {
        data: [65, 25, 8, 2], // Percentage distribution
        backgroundColor: [
          '#4caf50', // Green for low risk
          '#ff9800', // Orange for medium risk
          '#ff5722', // Red for high risk
          '#d32f2f', // Dark red for critical risk
        ],
        borderWidth: 2,
        borderColor: '#ffffff',
      },
    ],
  };

  // Chart options for consistent styling
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Page header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Security Dashboard
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Welcome back, {user?.name}. Here's your fraud detection overview.
        </Typography>
        <Typography variant="caption" color="textSecondary">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </Typography>
      </Box>

      {/* Loading state */}
      {loading && (
        <Box sx={{ width: '100%', mb: 2 }}>
          <LinearProgress />
        </Box>
      )}

      {/* Key metrics cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Total transactions today */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <AccountBalance />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Transactions Today
                  </Typography>
                  <Typography variant="h4">
                    {todayTransactions.length.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    +12% from yesterday
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Total amount processed */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <TrendingUp />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Amount Processed
                  </Typography>
                  <Typography variant="h4">
                    ${totalAmount.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    +8% from yesterday
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Blocked transactions */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                  <Block />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Blocked Transactions
                  </Typography>
                  <Typography variant="h4">
                    {blockedTransactions}
                  </Typography>
                  <Typography variant="body2" color="error.main">
                    {flaggedTransactions} flagged for review
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Average risk score */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <Speed />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Average Risk Score
                  </Typography>
                  <Typography variant="h4">
                    {averageRiskScore.toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    -2.1 from yesterday
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts and detailed analytics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Transaction trend chart */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Transaction Trends (24 Hours)
              </Typography>
              <Box sx={{ height: 300 }}>
                <Line data={transactionTrendData} options={chartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Risk distribution chart */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Distribution
              </Typography>
              <Box sx={{ height: 300 }}>
                <Doughnut data={riskDistributionData} options={{ responsive: true, maintainAspectRatio: false }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent alerts and system status */}
      <Grid container spacing={3}>
        {/* Recent fraud alerts */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Alerts
              </Typography>
              {alerts.slice(0, 5).map((alert) => (
                <Box key={alert.id} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Warning color={alert.severity === 'critical' ? 'error' : 'warning'} sx={{ mr: 1 }} />
                    <Chip
                      label={alert.severity.toUpperCase()}
                      size="small"
                      color={alert.severity === 'critical' ? 'error' : 'warning'}
                      sx={{ mr: 1 }}
                    />
                    <Typography variant="caption" color="textSecondary">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </Typography>
                  </Box>
                  <Typography variant="body2">
                    {alert.message}
                  </Typography>
                </Box>
              ))}

              {alerts.length === 0 && (
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <CheckCircle color="success" sx={{ fontSize: 48, mb: 1 }} />
                  <Typography variant="body2" color="textSecondary">
                    No active alerts. System is secure.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* System performance */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Performance
              </Typography>

              {/* Model accuracy */}
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Model Accuracy</Typography>
                  <Typography variant="body2">96.8%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={96.8} sx={{ height: 8, borderRadius: 4 }} />
              </Box>

              {/* Detection speed */}
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Avg Detection Speed</Typography>
                  <Typography variant="body2">47ms</Typography>
                </Box>
                <LinearProgress variant="determinate" value={85} color="success" sx={{ height: 8, borderRadius: 4 }} />
              </Box>

              {/* System uptime */}
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">System Uptime</Typography>
                  <Typography variant="body2">99.9%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={99.9} color="success" sx={{ height: 8, borderRadius: 4 }} />
              </Box>

              {/* API response time */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">API Response Time</Typography>
                  <Typography variant="body2">120ms</Typography>
                </Box>
                <LinearProgress variant="determinate" value={75} color="warning" sx={{ height: 8, borderRadius: 4 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
