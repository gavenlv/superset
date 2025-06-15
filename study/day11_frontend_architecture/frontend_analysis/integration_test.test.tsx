
// 集成测试示例
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { setupStore } from '../store';
import App from '../App';

const renderApp = (initialState = {}) => {
  const store = setupStore(initialState);
  
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Provider>
  );
};

describe('App Integration Tests', () => {
  beforeEach(() => {
    // Mock API calls
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('navigates to dashboard page', async () => {
    // Mock dashboard API response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        result: {
          id: '1',
          title: 'Test Dashboard',
          layout: {},
        },
      }),
    });

    renderApp();

    // Navigate to dashboard
    fireEvent.click(screen.getByText('Dashboards'));
    fireEvent.click(screen.getByText('Test Dashboard'));

    await waitFor(() => {
      expect(screen.getByText('Test Dashboard')).toBeInTheDocument();
    });
  });

  it('handles authentication flow', async () => {
    renderApp({
      user: {
        isAuthenticated: false,
      },
    });

    expect(screen.getByText('Login')).toBeInTheDocument();

    // Simulate login
    fireEvent.click(screen.getByText('Login'));

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });
});
            