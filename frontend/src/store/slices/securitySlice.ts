import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Define structure for security rule configuration
interface SecurityRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  ruleType: 'threshold' | 'pattern' | 'ml_model' | 'blacklist' | 'whitelist';
  parameters: {
    [key: string]: any; // Flexible parameters for different rule types
  };
  priority: number; // 1-10, higher priority rules are checked first
  actions: ('block' | 'flag' | 'review' | 'alert')[];
  lastModified: string;
  createdBy: string;
}

// Define structure for notification preferences
interface NotificationSettings {
  email: {
    enabled: boolean;
    addresses: string[];
    severity: ('low' | 'medium' | 'high' | 'critical')[];
  };
  sms: {
    enabled: boolean;
    phoneNumbers: string[];
    severity: ('high' | 'critical')[];
  };
  slack: {
    enabled: boolean;
    webhookUrl: string;
    channel: string;
    severity: ('medium' | 'high' | 'critical')[];
  };
  inApp: {
    enabled: boolean;
    showPopups: boolean;
    severity: ('low' | 'medium' | 'high' | 'critical')[];
  };
}

// Define structure for ML model configuration
interface ModelSettings {
  currentModel: string;
  availableModels: string[];
  threshold: number; // 0-1, fraud probability threshold
  retirningEnabled: boolean;
  retrainingSchedule: 'daily' | 'weekly' | 'monthly';
  features: {
    name: string;
    enabled: boolean;
    weight: number;
  }[];
  autoTuning: boolean;
  performanceTarget: {
    minAccuracy: number;
    maxFalsePositives: number;
  };
}

// Define structure for API and integration settings
interface ApiSettings {
  rateLimit: {
    enabled: boolean;
    requestsPerMinute: number;
    burstLimit: number;
  };
  authentication: {
    tokenExpiry: number; // in hours
    requireMFA: boolean;
    ipWhitelist: string[];
  };
  blockchain: {
    enabled: boolean;
    network: 'mainnet' | 'testnet';
    gasLimit: number;
    confirmations: number;
  };
  webhooks: {
    fraudDetected: string;
    transactionBlocked: string;
    modelRetrained: string;
  };
}

// Define the security settings state
interface SecurityState {
  rules: SecurityRule[]; // List of configured security rules
  notifications: NotificationSettings; // Notification preferences
  modelSettings: ModelSettings; // ML model configuration
  apiSettings: ApiSettings; // API and integration settings
  loading: boolean; // Loading state for settings operations
  error: string | null; // Error message if operations fail
  unsavedChanges: boolean; // Whether there are unsaved changes
  lastSaved: string | null; // Timestamp of last save
}

// Initial state when app starts
const initialState: SecurityState = {
  rules: [],
  notifications: {
    email: {
      enabled: true,
      addresses: [],
      severity: ['high', 'critical'],
    },
    sms: {
      enabled: false,
      phoneNumbers: [],
      severity: ['critical'],
    },
    slack: {
      enabled: false,
      webhookUrl: '',
      channel: '#security-alerts',
      severity: ['medium', 'high', 'critical'],
    },
    inApp: {
      enabled: true,
      showPopups: true,
      severity: ['low', 'medium', 'high', 'critical'],
    },
  },
  modelSettings: {
    currentModel: 'fraud_detector_v2.1',
    availableModels: ['fraud_detector_v2.1', 'fraud_detector_v2.0'],
    threshold: 0.7,
    retirningEnabled: true,
    retrainingSchedule: 'weekly',
    features: [],
    autoTuning: false,
    performanceTarget: {
      minAccuracy: 95,
      maxFalsePositives: 5,
    },
  },
  apiSettings: {
    rateLimit: {
      enabled: true,
      requestsPerMinute: 1000,
      burstLimit: 1500,
    },
    authentication: {
      tokenExpiry: 24,
      requireMFA: true,
      ipWhitelist: [],
    },
    blockchain: {
      enabled: false,
      network: 'testnet',
      gasLimit: 21000,
      confirmations: 6,
    },
    webhooks: {
      fraudDetected: '',
      transactionBlocked: '',
      modelRetrained: '',
    },
  },
  loading: false,
  error: null,
  unsavedChanges: false,
  lastSaved: null,
};

// Create Redux slice for security settings management
const securitySlice = createSlice({
  name: 'security',
  initialState,
  reducers: {
    // Action to start loading security settings
    fetchSettingsStart: (state) => {
      state.loading = true;
      state.error = null;
    },

    // Action when security settings are successfully loaded
    fetchSettingsSuccess: (state, action: PayloadAction<{
      rules: SecurityRule[];
      notifications: NotificationSettings;
      modelSettings: ModelSettings;
      apiSettings: ApiSettings;
    }>) => {
      state.rules = action.payload.rules;
      state.notifications = action.payload.notifications;
      state.modelSettings = action.payload.modelSettings;
      state.apiSettings = action.payload.apiSettings;
      state.loading = false;
      state.error = null;
      state.unsavedChanges = false;
    },

    // Action when settings loading fails
    fetchSettingsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },

    // Action to add new security rule
    addSecurityRule: (state, action: PayloadAction<SecurityRule>) => {
      state.rules.push(action.payload);
      state.unsavedChanges = true;
    },

    // Action to update existing security rule
    updateSecurityRule: (state, action: PayloadAction<SecurityRule>) => {
      const index = state.rules.findIndex(rule => rule.id === action.payload.id);
      if (index !== -1) {
        state.rules[index] = action.payload;
        state.unsavedChanges = true;
      }
    },

    // Action to delete security rule
    deleteSecurityRule: (state, action: PayloadAction<string>) => {
      state.rules = state.rules.filter(rule => rule.id !== action.payload);
      state.unsavedChanges = true;
    },

    // Action to toggle rule enabled/disabled status
    toggleSecurityRule: (state, action: PayloadAction<string>) => {
      const rule = state.rules.find(r => r.id === action.payload);
      if (rule) {
        rule.enabled = !rule.enabled;
        state.unsavedChanges = true;
      }
    },

    // Action to update notification settings
    updateNotificationSettings: (state, action: PayloadAction<Partial<NotificationSettings>>) => {
      state.notifications = { ...state.notifications, ...action.payload };
      state.unsavedChanges = true;
    },

    // Action to update ML model settings
    updateModelSettings: (state, action: PayloadAction<Partial<ModelSettings>>) => {
      state.modelSettings = { ...state.modelSettings, ...action.payload };
      state.unsavedChanges = true;
    },

    // Action to update API settings
    updateApiSettings: (state, action: PayloadAction<Partial<ApiSettings>>) => {
      state.apiSettings = { ...state.apiSettings, ...action.payload };
      state.unsavedChanges = true;
    },

    // Action to save all settings (called after successful API save)
    saveSettingsSuccess: (state) => {
      state.unsavedChanges = false;
      state.lastSaved = new Date().toISOString();
      state.error = null;
    },

    // Action when settings save fails
    saveSettingsFailure: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
    },

    // Action to reset unsaved changes (discard changes)
    discardChanges: (state) => {
      state.unsavedChanges = false;
      // Note: This would typically trigger a reload of settings from server
    },

    // Action to clear any error messages
    clearError: (state) => {
      state.error = null;
    },

    // Action to update fraud threshold (quick access)
    updateFraudThreshold: (state, action: PayloadAction<number>) => {
      state.modelSettings.threshold = action.payload;
      state.unsavedChanges = true;
    },
  },
});

// Export actions for use in components
export const {
  fetchSettingsStart,
  fetchSettingsSuccess,
  fetchSettingsFailure,
  addSecurityRule,
  updateSecurityRule,
  deleteSecurityRule,
  toggleSecurityRule,
  updateNotificationSettings,
  updateModelSettings,
  updateApiSettings,
  saveSettingsSuccess,
  saveSettingsFailure,
  discardChanges,
  clearError,
  updateFraudThreshold,
} = securitySlice.actions;

// Export reducer for store configuration
export default securitySlice.reducer;

// Export types for use in other files
export type { SecurityRule, NotificationSettings, ModelSettings, ApiSettings };
