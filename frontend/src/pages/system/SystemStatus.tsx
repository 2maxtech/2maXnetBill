import { Card, Typography } from 'antd';

const SystemStatus = () => {
  return (
    <div>
      <Typography.Title level={4}>System Status</Typography.Title>
      <Card>
        <Typography.Text type="secondary">MikroTik integration active. System metrics are available via the network status endpoint.</Typography.Text>
      </Card>
    </div>
  );
};

export default SystemStatus;
