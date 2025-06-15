
// Hook测试示例
import { renderHook, act } from '@testing-library/react-hooks';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { useDashboard } from './useDashboard';

const wrapper = ({ children }) => {
  const store = configureStore({
    reducer: {
      dashboard: dashboardReducer,
    },
  });
  
  return <Provider store={store}>{children}</Provider>;
};

describe('useDashboard Hook', () => {
  it('fetches dashboard data', async () => {
    const { result, waitForNextUpdate } = renderHook(
      () => useDashboard('123'),
      { wrapper }
    );

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBe(null);

    await waitForNextUpdate();

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBeDefined();
  });

  it('handles fetch error', async () => {
    // Mock API error
    jest.spyOn(SupersetClient, 'get').mockRejectedValue(
      new Error('API Error')
    );

    const { result, waitForNextUpdate } = renderHook(
      () => useDashboard('invalid-id'),
      { wrapper }
    );

    await waitForNextUpdate();

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe('API Error');
  });

  it('refetches data when called', async () => {
    const { result, waitForNextUpdate } = renderHook(
      () => useDashboard('123'),
      { wrapper }
    );

    await waitForNextUpdate();

    act(() => {
      result.current.refetch();
    });

    expect(result.current.loading).toBe(true);
  });
});
            