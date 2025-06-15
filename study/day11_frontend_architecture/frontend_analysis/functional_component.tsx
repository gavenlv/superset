
// 函数式组件示例
import React, { useState, useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';

interface DashboardProps {
  dashboardId: string;
  editMode?: boolean;
  onSave?: (data: any) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ 
  dashboardId, 
  editMode = false, 
  onSave 
}) => {
  // 本地状态
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Redux状态
  const dashboard = useSelector(state => state.dashboardState);
  const charts = useSelector(state => state.charts);
  const dispatch = useDispatch();
  
  // 副作用
  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        await dispatch(fetchDashboardData(dashboardId));
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboard();
  }, [dashboardId, dispatch]);
  
  // 事件处理
  const handleSave = useCallback(async () => {
    try {
      const data = await dispatch(saveDashboard(dashboard));
      onSave?.(data);
    } catch (err) {
      console.error('Save failed:', err);
    }
  }, [dashboard, dispatch, onSave]);
  
  // 渲染
  if (loading) return <Loading />;
  if (error) return <Error message={error} />;
  
  return (
    <div className="dashboard">
      <DashboardHeader 
        title={dashboard.title}
        editMode={editMode}
        onSave={handleSave}
      />
      <DashboardGrid 
        layout={dashboard.layout}
        charts={charts}
        editMode={editMode}
      />
    </div>
  );
};

export default Dashboard;
            