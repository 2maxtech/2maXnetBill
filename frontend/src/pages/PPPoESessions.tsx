import { Table, Card, Badge, Button, Popconfirm, Typography, message } from 'antd';
import { ReloadOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSessions, killSession, type PPPoESession } from '../api/pppoe';

const PPPoESessions = () => {
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['pppoe-sessions'],
    queryFn: getSessions,
    refetchInterval: 10000,
  });

  const killMut = useMutation({
    mutationFn: killSession,
    onSuccess: () => { message.success('Session terminated'); queryClient.invalidateQueries({ queryKey: ['pppoe-sessions'] }); },
    onError: () => message.error('Failed to kill session'),
  });

  const columns = [
    { title: 'Interface', dataIndex: 'ifname', key: 'ifname' },
    { title: 'Username', dataIndex: 'username', key: 'username' },
    { title: 'IP Address', dataIndex: 'ip', key: 'ip' },
    { title: 'MAC', dataIndex: 'calling-sid', key: 'mac' },
    { title: 'State', key: 'state', render: (_: unknown, r: PPPoESession) => <Badge status="success" text={r.state} /> },
    { title: 'Uptime', dataIndex: 'uptime', key: 'uptime' },
    { title: 'Rate Limit', dataIndex: 'rate-limit', key: 'rate', render: (v: string) => v || '-' },
    {
      title: 'Action', key: 'action',
      render: (_: unknown, record: PPPoESession) => (
        <Popconfirm title="Kill this session?" onConfirm={() => killMut.mutate(record.sid)}>
          <Button size="small" danger icon={<CloseCircleOutlined />}>Kill</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>PPPoE Sessions</Typography.Title>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Refresh</Button>
      </div>
      <Card>
        <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          {data?.data?.length ?? 0} active session(s) — auto-refreshes every 10s
        </Typography.Text>
        <Table dataSource={data?.data} columns={columns} rowKey="sid" loading={isLoading} pagination={false} />
      </Card>
    </div>
  );
};

export default PPPoESessions;
