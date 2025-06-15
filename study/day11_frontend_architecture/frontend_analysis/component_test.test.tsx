
// 组件测试示例
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import Dashboard from './Dashboard';
import dashboardReducer from './dashboardSlice';

const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      dashboard: dashboardReducer,
    },
    preloadedState: initialState,
  });
};

const renderWithProvider = (component, { initialState = {} } = {}) => {
  const store = createMockStore(initialState);
  return {
    ...render(
      <Provider store={store}>
        {component}
      </Provider>
    ),
    store,
  };
};

describe('Dashboard Component', () => {
  const mockDashboard = {
    id: '1',
    title: 'Test Dashboard',
    layout: {},
  };

  it('renders dashboard title', () => {
    renderWithProvider(
      <Dashboard dashboardId="1" />,
      {
        initialState: {
          dashboard: {
            data: mockDashboard,
            loading: false,
            error: null,
          },
        },
      }
    );

    expect(screen.getByText('Test Dashboard')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    renderWithProvider(
      <Dashboard dashboardId="1" />,
      {
        initialState: {
          dashboard: {
            data: null,
            loading: true,
            error: null,
          },
        },
      }
    );

    expect(screen.getByTestId('loading')).toBeInTheDocument();
  });

  it('handles save action', async () => {
    const mockOnSave = jest.fn();
    
    renderWithProvider(
      <Dashboard dashboardId="1" onSave={mockOnSave} />,
      {
        initialState: {
          dashboard: {
            data: mockDashboard,
            loading: false,
            error: null,
          },
        },
      }
    );

    fireEvent.click(screen.getByText('Save'));
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith(mockDashboard);
    });
  });
});
            