
// Redux Toolkit Slice示例
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { SupersetClient } from '@superset-ui/core';

interface DashboardState {
  data: Dashboard | null;
  loading: boolean;
  error: string | null;
  editMode: boolean;
  hasUnsavedChanges: boolean;
}

const initialState: DashboardState = {
  data: null,
  loading: false,
  error: null,
  editMode: false,
  hasUnsavedChanges: false,
};

// 异步Action
export const fetchDashboard = createAsyncThunk(
  'dashboard/fetchDashboard',
  async (dashboardId: string) => {
    const response = await SupersetClient.get({
      endpoint: `/api/v1/dashboard/${dashboardId}`
    });
    return response.json.result;
  }
);

export const saveDashboard = createAsyncThunk(
  'dashboard/saveDashboard',
  async (dashboard: Dashboard) => {
    const response = await SupersetClient.put({
      endpoint: `/api/v1/dashboard/${dashboard.id}`,
      postPayload: dashboard
    });
    return response.json.result;
  }
);

// Slice定义
const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    setEditMode: (state, action: PayloadAction<boolean>) => {
      state.editMode = action.payload;
    },
    setUnsavedChanges: (state, action: PayloadAction<boolean>) => {
      state.hasUnsavedChanges = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboard.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboard.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchDashboard.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch dashboard';
      })
      .addCase(saveDashboard.fulfilled, (state, action) => {
        state.data = action.payload;
        state.hasUnsavedChanges = false;
      });
  },
});

export const { setEditMode, setUnsavedChanges, clearError } = dashboardSlice.actions;
export default dashboardSlice.reducer;
            