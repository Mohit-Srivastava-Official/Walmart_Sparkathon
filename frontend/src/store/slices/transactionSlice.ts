import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Define structure for individual transaction data
interface Transaction {
  id: string;
  userId: string;
  amount: number;
  currency: string;
  merchantName: string;
  merchantCategory: string;
  timestamp: string;
  location: {
    country: string;
    city: string;
    coordinates: [number, number]; // [latitude, longitude]
  };
  paymentMethod: 'card' | 'wallet' | 'bank_transfer';
  deviceInfo: {
    deviceId: string;
    ipAddress: string;
    userAgent: string;
  };
  status: 'pending' | 'approved' | 'declined' | 'flagged';
  riskScore: number; // 0-100, higher means more risky
  fraudProbability: number; // 0-1, AI-calculated fraud probability
  blockchainHash?: string; // Optional blockchain transaction hash
}

// Define real-time fraud alert structure
interface FraudAlert {
  id: string;
  transactionId: string;
  alertType: 'high_risk' | 'anomaly' | 'blocked' | 'suspicious_pattern';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: string;
  investigated: boolean;
  falsePositive: boolean;
}

// Define the transaction monitoring state
interface TransactionState {
  transactions: Transaction[]; // List of recent transactions
  realTimeTransactions: Transaction[]; // Live transaction feed
  alerts: FraudAlert[]; // Active fraud alerts
  totalTransactions: number; // Total count for pagination
  totalAmount: number; // Total transaction amount today
  averageRiskScore: number; // Average risk across all transactions
  loading: boolean; // Loading state for API calls
  error: string | null; // Error message if operations fail
  filters: {
    status: string[];
    riskLevel: string;
    timeRange: string;
    amountRange: [number, number];
  };
}

// Initial state when app starts
const initialState: TransactionState = {
  transactions: [],
  realTimeTransactions: [],
  alerts: [],
  totalTransactions: 0,
  totalAmount: 0,
  averageRiskScore: 0,
  loading: false,
  error: null,
  filters: {
    status: [],
    riskLevel: 'all',
    timeRange: 'today',
    amountRange: [0, 10000],
  },
};

// Create Redux slice for transaction management
const transactionSlice = createSlice({
  name: 'transactions',
  initialState,
  reducers: {
    // Action to start loading transactions (shows loading state)
    fetchTransactionsStart: (state) => {
      state.loading = true;
      state.error = null;
    },

    // Action when transactions are successfully loaded
    fetchTransactionsSuccess: (state, action: PayloadAction<{
      transactions: Transaction[];
      totalCount: number;
      totalAmount: number;
      averageRiskScore: number;
    }>) => {
      state.transactions = action.payload.transactions;
      state.totalTransactions = action.payload.totalCount;
      state.totalAmount = action.payload.totalAmount;
      state.averageRiskScore = action.payload.averageRiskScore;
      state.loading = false;
      state.error = null;
    },

    // Action when transaction loading fails
    fetchTransactionsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },

    // Action to add new real-time transaction (WebSocket update)
    addRealTimeTransaction: (state, action: PayloadAction<Transaction>) => {
      // Add to real-time feed at the beginning
      state.realTimeTransactions.unshift(action.payload);

      // Keep only last 50 real-time transactions for performance
      if (state.realTimeTransactions.length > 50) {
        state.realTimeTransactions = state.realTimeTransactions.slice(0, 50);
      }

      // Update statistics
      state.totalTransactions += 1;
      state.totalAmount += action.payload.amount;

      // Recalculate average risk score
      const allTransactions = [...state.transactions, ...state.realTimeTransactions];
      state.averageRiskScore = allTransactions.reduce((sum, t) => sum + t.riskScore, 0) / allTransactions.length;
    },

    // Action to add new fraud alert
    addFraudAlert: (state, action: PayloadAction<FraudAlert>) => {
      state.alerts.unshift(action.payload);

      // Keep only last 100 alerts for performance
      if (state.alerts.length > 100) {
        state.alerts = state.alerts.slice(0, 100);
      }
    },

    // Action to update transaction status (after manual review)
    updateTransactionStatus: (state, action: PayloadAction<{
      transactionId: string;
      status: Transaction['status'];
    }>) => {
      const { transactionId, status } = action.payload;

      // Update in main transactions list
      const transactionIndex = state.transactions.findIndex(t => t.id === transactionId);
      if (transactionIndex !== -1) {
        state.transactions[transactionIndex].status = status;
      }

      // Update in real-time transactions list
      const realtimeIndex = state.realTimeTransactions.findIndex(t => t.id === transactionId);
      if (realtimeIndex !== -1) {
        state.realTimeTransactions[realtimeIndex].status = status;
      }
    },

    // Action to mark alert as investigated
    markAlertInvestigated: (state, action: PayloadAction<{
      alertId: string;
      falsePositive: boolean;
    }>) => {
      const { alertId, falsePositive } = action.payload;
      const alertIndex = state.alerts.findIndex(a => a.id === alertId);

      if (alertIndex !== -1) {
        state.alerts[alertIndex].investigated = true;
        state.alerts[alertIndex].falsePositive = falsePositive;
      }
    },

    // Action to update transaction filters
    updateFilters: (state, action: PayloadAction<Partial<TransactionState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },

    // Action to clear all real-time data (useful for cleanup)
    clearRealTimeData: (state) => {
      state.realTimeTransactions = [];
      state.alerts = [];
    },
  },
});

// Export actions for use in components
export const {
  fetchTransactionsStart,
  fetchTransactionsSuccess,
  fetchTransactionsFailure,
  addRealTimeTransaction,
  addFraudAlert,
  updateTransactionStatus,
  markAlertInvestigated,
  updateFilters,
  clearRealTimeData,
} = transactionSlice.actions;

// Export reducer for store configuration
export default transactionSlice.reducer;

// Export types for use in other files
export type { Transaction, FraudAlert };
