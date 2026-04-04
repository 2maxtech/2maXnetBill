import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Typography, Table, Button, Modal, Form, Input, Tabs, message, Space } from 'antd';
import { PlusOutlined, ReloadOutlined, SaveOutlined } from '@ant-design/icons';
import {
  getDhcpLeases,
  getDhcpConfig,
  applyDhcpConfig,
  getDnsConfig,
  addDnsEntry,
  getUpstreamDns,
} from '../../api/network';

const DhcpDns = () => {
  const queryClient = useQueryClient();
  const [dnsModal, setDnsModal] = useState(false);
  const [dhcpEditing, setDhcpEditing] = useState(false);
  const [dhcpConfigText, setDhcpConfigText] = useState('');
  const [dnsForm] = Form.useForm();

  const { data: leases, isLoading: leaseLoading } = useQuery({
    queryKey: ['dhcp-leases'],
    queryFn: () => getDhcpLeases().then((r) => r.data),
  });
  const { data: dhcpConfig } = useQuery({
    queryKey: ['dhcp-config'],
    queryFn: () => getDhcpConfig().then((r) => r.data),
  });
  const { data: dnsConfig } = useQuery({
    queryKey: ['dns-config'],
    queryFn: () => getDnsConfig().then((r) => r.data),
  });
  const { data: upstream } = useQuery({
    queryKey: ['dns-upstream'],
    queryFn: () => getUpstreamDns().then((r) => r.data),
  });

  const applyDhcpMut = useMutation({
    mutationFn: applyDhcpConfig,
    onSuccess: () => {
      message.success('DHCP config applied');
      setDhcpEditing(false);
      queryClient.invalidateQueries({ queryKey: ['dhcp-config'] });
    },
  });
  const addDnsMut = useMutation({
    mutationFn: addDnsEntry,
    onSuccess: () => {
      message.success('DNS entry added');
      setDnsModal(false);
      dnsForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['dns-config'] });
    },
  });

  const leaseColumns = [
    { title: 'IP Address', dataIndex: 'ip', key: 'ip' },
    { title: 'MAC Address', dataIndex: 'mac', key: 'mac' },
    { title: 'Hostname', dataIndex: 'hostname', key: 'host' },
    { title: 'Expires', dataIndex: 'expires', key: 'exp' },
  ];

  const items = [
    {
      key: 'leases',
      label: 'DHCP Leases',
      children: (
        <Table
          columns={leaseColumns}
          dataSource={leases || []}
          rowKey="mac"
          loading={leaseLoading}
          size="small"
        />
      ),
    },
    {
      key: 'dhcp-config',
      label: 'DHCP Config',
      children: (
        <div>
          {dhcpEditing ? (
            <>
              <Input.TextArea
                rows={15}
                value={dhcpConfigText}
                onChange={(e) => setDhcpConfigText(e.target.value)}
                style={{ fontFamily: 'monospace', fontSize: 13 }}
              />
              <Space style={{ marginTop: 8 }}>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  loading={applyDhcpMut.isPending}
                  onClick={() => applyDhcpMut.mutate(dhcpConfigText)}
                >
                  Apply
                </Button>
                <Button onClick={() => setDhcpEditing(false)}>Cancel</Button>
              </Space>
            </>
          ) : (
            <>
              <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, fontSize: 13 }}>
                {dhcpConfig?.config || 'No configuration'}
              </pre>
              <Button
                onClick={() => {
                  setDhcpConfigText(dhcpConfig?.config || '');
                  setDhcpEditing(true);
                }}
              >
                Edit
              </Button>
            </>
          )}
        </div>
      ),
    },
    {
      key: 'dns',
      label: 'DNS',
      children: (
        <div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setDnsModal(true)}
            style={{ marginBottom: 12 }}
          >
            Add DNS Entry
          </Button>
          <Typography.Text strong>Custom DNS Records:</Typography.Text>
          <pre
            style={{
              background: '#f5f5f5',
              padding: 12,
              borderRadius: 4,
              fontSize: 13,
              marginTop: 8,
            }}
          >
            {dnsConfig?.config || 'No custom DNS records'}
          </pre>
          <Typography.Text strong style={{ display: 'block', marginTop: 16 }}>
            Upstream DNS Servers:
          </Typography.Text>
          <ul>
            {(upstream || []).map((s: string, i: number) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>DHCP & DNS</Typography.Title>
        <Button
          icon={<ReloadOutlined />}
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['dhcp-leases'] });
            queryClient.invalidateQueries({ queryKey: ['dns-config'] });
          }}
        />
      </div>
      <Card>
        <Tabs items={items} />
      </Card>

      <Modal
        title="Add DNS Entry"
        open={dnsModal}
        onCancel={() => setDnsModal(false)}
        onOk={() => dnsForm.submit()}
        confirmLoading={addDnsMut.isPending}
      >
        <Form form={dnsForm} layout="vertical" onFinish={(v) => addDnsMut.mutate(v)}>
          <Form.Item name="domain" label="Domain" rules={[{ required: true }]}>
            <Input placeholder="example.local" />
          </Form.Item>
          <Form.Item name="ip" label="IP Address" rules={[{ required: true }]}>
            <Input placeholder="192.168.1.100" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DhcpDns;
