import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Define structure for fraud pattern analytics
interface FraudPattern {
  id: string;
  patternType: 'velocity' | 'location' | 'amount' | 'merchant' | 'device';
  description: string;
  frequency: number; // How often this pattern appears
  successRate: number; // Percentage of successful fraud attempts
  averageAmount: number; // Average transaction amount for this pattern
  lastSeen: string; // When this pattern was last detected
  severity: 'low' | 'medium' | 'high' | 'critical';
  geographicDistribution: {
    country: string;
    count: number;
  }[];
}

// Define structure for fraud statistics
interface FraudStats {
  totalFraudulent: number; // Total fraudulent transactions detected
  totalBlocked: number; // Total transactions blocked
  falsePositives: number; // Incorrectly flagged transactions
  accuracy: number; // Model accuracy percentage
  precision: number; // Model precision percentage
  recall: number; // Model recall percentage
  f1Score: number; // F1 score for model performance
  dailyTrend: {
    date: string;
    fraudCount: number;
    blockedCount: number;
    falsePositives: number;
  }[];
  hourlyDistribution: {
    hour: number;
    fraudCount: number;
  }[];
  riskDistribution: {
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
    count: number;
    percentage: number;
  }[];
}

// Define ML model performance metrics
interface ModelPerformance {
  modelVersion: string;
  lastTraining: string;
  trainingDataSize: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  auc: number; // Area Under Curve
  confusionMatrix: {
    truePositive: number;
    falsePositive: number;
    trueNegative: number;
    falseNegative: number;
  };
  featureImportance: {
    feature: string;
    importance: number;
  }[];
}

// Define the fraud analytics state
interface FraudState {
  patterns: FraudPattern[]; // Detected fraud patterns
  stats: FraudStats | null; // Overall fraud statistics
  modelPerformance: ModelPerformance | null; // ML model metrics
  timeRange: 'day' | 'week' | 'month' | 'year'; // Selected time range for analytics
  loading: boolean; // Loading state for data fetching
  error: string | null; // Error message if operations fail
  autoRefresh: boolean; // Whether to auto-refresh analytics data
  refreshInterval: number; // Refresh interval in seconds
}

// Initial state when app starts
const initialState: FraudState = {
  patterns: [],
  stats: null,
  modelPerformance: null,
  timeRange: 'day',
  loading: false,
  error: null,
  autoRefresh: true,
  refreshInterval: 30, // 30 seconds default
};

// Create Redux slice for fraud analytics management
const fraudSlice = createSlice({
  name: 'fraud',
  initialState,
  reducers: {
    // Action to start loading fraud analytics (shows loading state)
    fetchAnalyticsStart: (state) => {
      state.loading = true;
      state.error = null;
    },

    // Action when fraud patterns are successfully loaded
    fetchPatternsSuccess: (state, action: PayloadAction<FraudPattern[]>) => {
      state.patterns = action.payload;
      state.loading = false;
      state.error = null;
    },

    // Action when fraud statistics are successfully loaded
    fetchStatsSuccess: (state, action: PayloadAction<FraudStats>) => {
      state.stats = action.payload;
      state.loading = false;
      state.error = null;
    },

    // Action when ML model performance data is loaded
    fetchModelPerformanceSuccess: (state, action: PayloadAction<ModelPerformance>) => {
      state.modelPerformance = action.payload;
      state.loading = false;
      state.error = null;
    },

    // Action when analytics loading fails
    fetchAnalyticsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },

    // Action to update time range for analytics
    setTimeRange: (state, action: PayloadAction<FraudState['timeRange']>) => {
      state.timeRange = action.payload;
    },

    // Action to toggle auto-refresh functionality
    toggleAutoRefresh: (state) => {
      state.autoRefresh = !state.autoRefresh;
    },

    // Action to update refresh interval
    setRefreshInterval: (state, action: PayloadAction<number>) => {
      state.refreshInterval = action.payload;
    },

    // Action to add new fraud pattern (real-time detection)
    addNewPattern: (state, action: PayloadAction<FraudPattern>) => {
      // Check if pattern already exists
      const existingIndex = state.patterns.findIndex(p => p.id === action.payload.id);

      if (existingIndex !== -1) {
        // Update existing pattern with new data
        state.patterns[existingIndex] = action.payload;
      } else {
        // Add new pattern at the beginning
        state.patterns.unshift(action.payload);

        // Keep only last 50 patterns for performance
        if (state.patterns.length > 50) {
          state.patterns = state.patterns.slice(0, 50);
        }
      }
    },

    // Action to update fraud statistics incrementally (real-time updates)
    updateStatsIncremental: (state, action: PayloadAction<{
      newFraudulent?: number;
      newBlocked?: number;
      newFalsePositive?: number;
    }>) => {
      if (state.stats) {
        const { newFraudulent = 0, newBlocked = 0, newFalsePositive = 0 } = action.payload;

        // Update counters
        state.stats.totalFraudulent += newFraudulent;
        state.stats.totalBlocked += newBlocked;
        state.stats.falsePositives += newFalsePositive;

        // Recalculate accuracy (avoid division by zero)
        const total = state.stats.totalFraudulent + state.stats.falsePositives;
        if (total > 0) {
          state.stats.accuracy = (state.stats.totalFraudulent / total) * 100;
        }
      }
    },

    // Action to clear all analytics data
    clearAnalytics: (state) => {
      state.patterns = [];
      state.stats = null;
      state.modelPerformance = null;
      state.error = null;
    },
  },
});

// Export actions for use in components
export const {
  fetchAnalyticsStart,
  fetchPatternsSuccess,
  fetchStatsSuccess,
  fetchModelPerformanceSuccess,
  fetchAnalyticsFailure,
  setTimeRange,
  toggleAutoRefresh,
  setRefreshInterval,
  addNewPattern,
  updateStatsIncremental,
  clearAnalytics,
} = fraudSlice.actions;

// Export reducer for store configuration
export default fraudSlice.reducer;

// Export types for use in other files
export type { FraudPattern, FraudStats, ModelPerformance };
