
// 自定义Hook示例
import { useState, useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { SupersetClient } from '@superset-ui/core';

interface UseApiResourceResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useApiResource<T>(endpoint: string): UseApiResourceResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await SupersetClient.get({ endpoint });
      setData(response.json.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [endpoint]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  return { data, loading, error, refetch: fetchData };
}

// 使用示例
export function useDashboard(dashboardId: string) {
  return useApiResource<Dashboard>(`/api/v1/dashboard/${dashboardId}`);
}

export function useCharts() {
  return useApiResource<Chart[]>('/api/v1/chart/');
}
            