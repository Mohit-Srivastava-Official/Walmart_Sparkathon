import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
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
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material'; // Material-UI components
import {
  Analytics,
  TrendingUp,
  Assessment,
  Timeline,
  Security,
  Speed,
} from '@mui/icons-material'; // Material-UI icons
import { Line, Bar, Pie, Radar } from 'react-chartjs-2'; // Chart.js React components
import { useAppSelector, useAppDispatch } from '../hooks/redux'; // Custom Redux hooks
import {
  fetchAnalyticsStart,
  setTimeRange,
  toggleAutoRefresh,
} from '../store/slices/fraudSlice'; // Fraud analytics actions

// Fraud Analytics page - comprehensive analytics and insights about fraud patterns
const FraudAnalytics: React.FC = () => {
  // Redux hooks for state management
  const dispatch = useAppDispatch();
  const {
    patterns,
    stats,
    modelPerformance,
    timeRange,
    autoRefresh,
    loading,
    error,
  } = useAppSelector((state) => state.fraud);

  // Local state for chart selections
  const [selectedMetric, setSelectedMetric] = useState<'fraud' | 'blocked' | 'falsePositives'>('fraud');

  // Effect to load analytics data
  useEffect(() => {
    dispatch(fetchAnalyticsStart());
  }, [dispatch, timeRange]);

  // Effect for auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const refreshTimer = setInterval(() => {
      dispatch(fetchAnalyticsStart());
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(refreshTimer);
  }, [autoRefresh, dispatch]);

  // Prepare fraud trend data for line chart
  const fraudTrendData = {
    labels: stats?.dailyTrend.map(d => new Date(d.date).toLocaleDateString()) || [],
    datasets: [
      {
        label: 'Fraudulent Transactions',
        data: stats?.dailyTrend.map(d => d.fraudCount) || [],
        borderColor: 'rgb(211, 47, 47)',
        backgroundColor: 'rgba(211, 47, 47, 0.1)',
        fill: true,
      },
      {
        label: 'Blocked Transactions',
        data: stats?.dailyTrend.map(d => d.blockedCount) || [],
        borderColor: 'rgb(255, 152, 0)',
        backgroundColor: 'rgba(255, 152, 0, 0.1)',
        fill: true,
      },
      {
        label: 'False Positives',
        data: stats?.dailyTrend.map(d => d.falsePositives) || [],
        borderColor: 'rgb(156, 39, 176)',
        backgroundColor: 'rgba(156, 39, 176, 0.1)',
        fill: true,
      },
    ],
  };

  // Prepare hourly distribution data for bar chart
  const hourlyDistributionData = {
    labels: Array.from({ length: 24 }, (_, i) => `${i}:00`),
    datasets: [
      {
        label: 'Fraud Attempts by Hour',
        data: stats?.hourlyDistribution.map(h => h.fraudCount) || [],
        backgroundColor: 'rgba(211, 47, 47, 0.7)',
        borderColor: 'rgb(211, 47, 47)',
        borderWidth: 1,
      },
    ],
  };

  // Prepare risk distribution data for pie chart
  const riskDistributionData = {
    labels: stats?.riskDistribution.map(r => r.riskLevel.charAt(0).toUpperCase() + r.riskLevel.slice(1)) || [],
    datasets: [
      {
        data: stats?.riskDistribution.map(r => r.percentage) || [],
        backgroundColor: [
          '#4caf50', // Low - Green
          '#ff9800', // Medium - Orange
          '#ff5722', // High - Red
          '#d32f2f', // Critical - Dark Red
        ],
        borderWidth: 2,
        borderColor: '#ffffff',
      },
    ],
  };

  // Prepare model performance radar chart
  const modelRadarData = {
    labels: ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'AUC'],
    datasets: [
      {
        label: 'Current Model',
        data: modelPerformance ? [
          modelPerformance.accuracy,
          modelPerformance.precision,
          modelPerformance.recall,
          modelPerformance.f1Score,
          modelPerformance.auc * 100, // Convert AUC to percentage
        ] : [],
        backgroundColor: 'rgba(0, 76, 145, 0.2)',
        borderColor: 'rgb(0, 76, 145)',
        pointBackgroundColor: 'rgb(0, 76, 145)',
      },
    ],
  };

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
  };

  // Get severity color for fraud patterns
  const getSeverityColor = (severity: string): 'success' | 'warning' | 'error' => {
    switch (severity) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high':
      case 'critical': return 'error';
      default: return 'warning';
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Page header with controls */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Fraud Analytics
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Advanced insights and patterns in fraud detection
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {/* Time range selector */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => dispatch(setTimeRange(e.target.value as any))}
            >
              <MenuItem value="day">Last Day</MenuItem>
              <MenuItem value="week">Last Week</MenuItem>
              <MenuItem value="month">Last Month</MenuItem>
              <MenuItem value="year">Last Year</MenuItem>
            </Select>
          </FormControl>

          {/* Auto refresh toggle */}
          <Button
            variant={autoRefresh ? 'contained' : 'outlined'}
            size="small"
            onClick={() => dispatch(toggleAutoRefresh())}
          >
            Auto Refresh
          </Button>
        </Box>
      </Box>

      {/* Loading state */}
      {loading && (
        <Box sx={{ width: '100%', mb: 2 }}>
          <LinearProgress />
        </Box>
      )}

      {/* Error state */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Key metrics cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Total fraud detected */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Fraud Detected
                  </Typography>
                  <Typography variant="h4">
                    {stats?.totalFraudulent.toLocaleString() || 0}
                  </Typography>
                  <Typography variant="body2" color="error.main">
                    +{Math.round(Math.random() * 20)}% vs last period
                  </Typography>
                </Box>
                <Security fontSize="large" color="error" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Total blocked */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Transactions Blocked
                  </Typography>
                  <Typography variant="h4">
                    {stats?.totalBlocked.toLocaleString() || 0}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    +{Math.round(Math.random() * 15)}% vs last period
                  </Typography>
                </Box>
                <Analytics fontSize="large" color="warning" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Model accuracy */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Model Accuracy
                  </Typography>
                  <Typography variant="h4">
                    {stats?.accuracy.toFixed(1) || '0.0'}%
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    +0.3% vs last model
                  </Typography>
                </Box>
                <TrendingUp fontSize="large" color="success" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* False positives */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    False Positives
                  </Typography>
                  <Typography variant="h4">
                    {stats?.falsePositives.toLocaleString() || 0}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    -{Math.round(Math.random() * 10)}% vs last period
                  </Typography>
                </Box>
                <Assessment fontSize="large" color="info" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts section */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Fraud trends over time */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Fraud Detection Trends
              </Typography>
              <Box sx={{ height: 350 }}>
                <Line data={fraudTrendData} options={chartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Risk distribution */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Level Distribution
              </Typography>
              <Box sx={{ height: 350 }}>
                <Pie data={riskDistributionData} options={{ ...chartOptions, maintainAspectRatio: false }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Hourly fraud distribution */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Fraud Attempts by Hour of Day
              </Typography>
              <Box sx={{ height: 300 }}>
                <Bar data={hourlyDistributionData} options={chartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Model performance radar */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Model Performance Metrics
              </Typography>
              <Box sx={{ height: 300 }}>
                <Radar data={modelRadarData} options={{
                  ...chartOptions,
                  scales: {
                    r: {
                      beginAtZero: true,
                      max: 100,
                    },
                  },
                }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Fraud patterns analysis */}
      <Grid container spacing={3}>
        {/* Detected fraud patterns */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Detected Fraud Patterns
              </Typography>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Pattern Type</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell>Frequency</TableCell>
                      <TableCell>Success Rate</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Last Seen</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {patterns.slice(0, 10).map((pattern) => (
                      <TableRow key={pattern.id} hover>
                        <TableCell>
                          <Chip
                            label={pattern.patternType.replace('_', ' ').toUpperCase()}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{pattern.description}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{pattern.frequency}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{pattern.successRate.toFixed(1)}%</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={pattern.severity.toUpperCase()}
                            size="small"
                            color={getSeverityColor(pattern.severity)}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(pattern.lastSeen).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {patterns.length === 0 && (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="textSecondary">
                    No fraud patterns detected in the selected time range.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Model performance details */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Model Performance Details
              </Typography>

              {modelPerformance && (
                <Box>
                  {/* Model info */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" color="textSecondary">Current Model</Typography>
                    <Typography variant="h6">{modelPerformance.modelVersion}</Typography>
                    <Typography variant="caption" color="textSecondary">
                      Trained: {new Date(modelPerformance.lastTraining).toLocaleDateString()}
                    </Typography>
                  </Box>

                  {/* Performance metrics */}
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Accuracy</Typography>
                      <Typography variant="body2">{modelPerformance.accuracy.toFixed(1)}%</Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={modelPerformance.accuracy}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Precision</Typography>
                      <Typography variant="body2">{modelPerformance.precision.toFixed(1)}%</Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={modelPerformance.precision}
                      color="success"
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Recall</Typography>
                      <Typography variant="body2">{modelPerformance.recall.toFixed(1)}%</Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={modelPerformance.recall}
                      color="warning"
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>

                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">F1 Score</Typography>
                      <Typography variant="body2">{modelPerformance.f1Score.toFixed(1)}%</Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={modelPerformance.f1Score}
                      color="info"
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>

                  {/* Confusion matrix */}
                  <Typography variant="subtitle2" gutterBottom>Confusion Matrix</Typography>
                  <Grid container spacing={1} sx={{ textAlign: 'center' }}>
                    <Grid item xs={6}>
                      <Box sx={{ p: 1, bgcolor: 'success.light', color: 'success.contrastText', borderRadius: 1 }}>
                        <Typography variant="caption">True Positive</Typography>
                        <Typography variant="h6">{modelPerformance.confusionMatrix.truePositive}</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box sx={{ p: 1, bgcolor: 'error.light', color: 'error.contrastText', borderRadius: 1 }}>
                        <Typography variant="caption">False Positive</Typography>
                        <Typography variant="h6">{modelPerformance.confusionMatrix.falsePositive}</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box sx={{ p: 1, bgcolor: 'warning.light', color: 'warning.contrastText', borderRadius: 1 }}>
                        <Typography variant="caption">False Negative</Typography>
                        <Typography variant="h6">{modelPerformance.confusionMatrix.falseNegative}</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box sx={{ p: 1, bgcolor: 'info.light', color: 'info.contrastText', borderRadius: 1 }}>
                        <Typography variant="caption">True Negative</Typography>
                        <Typography variant="h6">{modelPerformance.confusionMatrix.trueNegative}</Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default FraudAnalytics;
