import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Table, Card, Typography, Button, Tag, Space, Badge, Statistic, Row, Col } from 'antd';
import { ReloadOutlined, WifiOutlined, UserOutlined, LaptopOutlined } from '@ant-design/icons';
import { getActiveSessions, getNetworkStatus } from '../api/network';
import type { PppoeSession } from '../api/network';

const ActiveUsers = () => {
  const queryClient = useQueryClient();

  const { data: status } = useQuery({
    queryKey: ['network-status'],
    queryFn: () => getNetworkStatus().then((r) => r.data),
    refetchInterval: 30000,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['active-sessions'],
    queryFn: () => getActiveSessions().then((r) => r.data),
    refetchInterval: 15000,
  });

  const sessions = data?.sessions || [];

  const columns = [
    {
      title: 'Username',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <span style={{ fontWeight: 500 }}>{name}</span>,
    },
    {
      title: 'IP Address',
      dataIndex: 'address',
      key: 'address',
      width: 140,
      render: (ip: string) => ip || '-',
    },
    {
      title: 'Caller ID',
      key: 'caller-id',
      width: 160,
      render: (_: unknown, r: PppoeSession) => (
        <code style={{ fontSize: 12 }}>{r['caller-id'] || '-'}</code>
      ),
    },
    {
      title: 'Service',
      dataIndex: 'service',
      key: 'service',
      width: 100,
      render: (s: string) => <Tag>{s || 'pppoe'}</Tag>,
    },
    {
      title: 'Uptime',
      dataIndex: 'uptime',
      key: 'uptime',
      width: 120,
    },
    {
      title: 'Status',
      key: 'status',
      width: 100,
      render: () => <Badge status="success" text="Online" />,
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          <WifiOutlined style={{ color: '#e8700a', marginRight: 8 }} />
          Active Users
        </Typography.Title>
        <Button
          icon={<ReloadOutlined />}
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['active-sessions'] });
            queryClient.invalidateQueries({ queryKey: ['network-status'] });
          }}
        >
          Refresh
        </Button>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="MikroTik"
              valueRender={() => (
                <Space direction="vertical" size={0}>
                  <Tag color={status?.connected ? 'green' : 'red'}>
                    {status?.connected ? 'Connected' : 'Disconnected'}
                  </Tag>
                  {status?.identity && (
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {status.identity}
                    </Typography.Text>
                  )}
                </Space>
              )}
              prefix={<LaptopOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="PPPoE Sessions"
              value={sessions.length}
              prefix={<UserOutlined style={{ color: '#e8700a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Router Uptime"
              valueRender={() => (
                <Typography.Text>{status?.uptime || '-'}</Typography.Text>
              )}
              prefix={<WifiOutlined style={{ color: '#f9a825' }} />}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          {sessions.length} active PPPoE session(s) — auto-refreshes every 15s
        </Typography.Text>
        <Table
          columns={columns}
          dataSource={sessions}
          rowKey=".id"
          loading={isLoading}
          pagination={false}
          size="middle"
        />
      </Card>
    </div>
  );
};

export default ActiveUsers;
