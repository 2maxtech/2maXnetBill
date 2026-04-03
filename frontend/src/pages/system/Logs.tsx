import { Card, Typography, Result } from 'antd';
import { ClockCircleOutlined } from '@ant-design/icons';

const Logs = () => (
  <div>
    <Typography.Title level={4}>Logs</Typography.Title>
    <Card>
      <Result icon={<ClockCircleOutlined />} title="Coming Soon" subTitle="System and authentication logs will be available in a future update." />
    </Card>
  </div>
);

export default Logs;
