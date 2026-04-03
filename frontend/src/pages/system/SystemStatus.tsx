import { Row, Col, Card, Progress, Typography, Alert } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { getSystemStats } from '../../api/gateway';

const color = (pct: number) => (pct < 60 ? '#10b981' : pct < 80 ? '#f59e0b' : '#ef4444');

const SystemStatus = () => {
  const { data, error } = useQuery({
    queryKey: ['system-stats'],
    queryFn: getSystemStats,
    refetchInterval: 5000,
  });

  const stats = data?.data;

  return (
    <div>
      <Typography.Title level={4}>System Status</Typography.Title>
      {error ? (
        <Alert type="error" message="Gateway Unreachable" description="Cannot connect to the ISP Gateway agent. Check if the Gateway is online." showIcon />
      ) : stats ? (
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Card title="CPU Usage">
              <div style={{ textAlign: 'center' }}>
                <Progress type="dashboard" percent={Math.round(stats.cpu_percent)} strokeColor={color(stats.cpu_percent)} />
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card title="Memory Usage">
              <div style={{ textAlign: 'center' }}>
                <Progress type="dashboard" percent={Math.round(stats.memory_percent)} strokeColor={color(stats.memory_percent)} />
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card title="Disk Usage">
              <div style={{ textAlign: 'center' }}>
                <Progress type="dashboard" percent={Math.round(stats.disk_percent)} strokeColor={color(stats.disk_percent)} />
              </div>
            </Card>
          </Col>
        </Row>
      ) : (
        <Card loading />
      )}
      <Typography.Text type="secondary" style={{ display: 'block', marginTop: 12 }}>Auto-refreshes every 5 seconds</Typography.Text>
    </div>
  );
};

export default SystemStatus;
