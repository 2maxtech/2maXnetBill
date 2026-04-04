import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Typography, Table, Tag, Button, Modal, Form, Input, Select, Space, message, Tabs } from 'antd';
import { PlusOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons';
import {
  getInterfaces,
  getRoutes,
  addRoute,
  deleteRoute,
  getNatRules,
  addNatMasquerade,
  addPortForward,
} from '../../api/network';

const Interfaces = () => {
  const queryClient = useQueryClient();
  const [routeModal, setRouteModal] = useState(false);
  const [natModal, setNatModal] = useState(false);
  const [portFwdModal, setPortFwdModal] = useState(false);
  const [routeForm] = Form.useForm();
  const [natForm] = Form.useForm();
  const [fwdForm] = Form.useForm();

  const { data: interfaces, isLoading: ifLoading } = useQuery({
    queryKey: ['interfaces'],
    queryFn: () => getInterfaces().then((r) => r.data),
  });
  const { data: routes, isLoading: rtLoading } = useQuery({
    queryKey: ['routes'],
    queryFn: () => getRoutes().then((r) => r.data),
  });
  const { data: nat } = useQuery({
    queryKey: ['nat-rules'],
    queryFn: () => getNatRules().then((r) => r.data),
  });

  const addRouteMut = useMutation({
    mutationFn: addRoute,
    onSuccess: () => {
      message.success('Route added');
      setRouteModal(false);
      routeForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['routes'] });
    },
  });
  const delRouteMut = useMutation({
    mutationFn: deleteRoute,
    onSuccess: () => {
      message.success('Route deleted');
      queryClient.invalidateQueries({ queryKey: ['routes'] });
    },
  });
  const masqMut = useMutation({
    mutationFn: addNatMasquerade,
    onSuccess: () => {
      message.success('Masquerade added');
      setNatModal(false);
      queryClient.invalidateQueries({ queryKey: ['nat-rules'] });
    },
  });
  const fwdMut = useMutation({
    mutationFn: addPortForward,
    onSuccess: () => {
      message.success('Port forward added');
      setPortFwdModal(false);
      queryClient.invalidateQueries({ queryKey: ['nat-rules'] });
    },
  });

  const ifColumns = [
    { title: 'Name', dataIndex: 'ifname', key: 'name' },
    {
      title: 'State',
      dataIndex: 'operstate',
      key: 'state',
      render: (s: string) => <Tag color={s === 'UP' ? 'green' : 'red'}>{s}</Tag>,
    },
    { title: 'MAC', key: 'mac', render: (_: unknown, r: any) => r.address || '-' },
    {
      title: 'IP Addresses',
      key: 'addrs',
      render: (_: unknown, r: any) =>
        (r.addr_info || []).map((a: any) => `${a.local}/${a.prefixlen}`).join(', ') || '-',
    },
    { title: 'MTU', dataIndex: 'mtu', key: 'mtu' },
  ];

  const rtColumns = [
    { title: 'Destination', dataIndex: 'dst', key: 'dst', render: (d: string) => d || 'default' },
    { title: 'Gateway', dataIndex: 'gateway', key: 'gw', render: (g: string) => g || '-' },
    { title: 'Device', dataIndex: 'dev', key: 'dev' },
    { title: 'Protocol', dataIndex: 'protocol', key: 'proto' },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, r: any) =>
        r.dst ? (
          <Button
            type="link"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => delRouteMut.mutate({ destination: r.dst })}
          />
        ) : null,
    },
  ];

  const items = [
    {
      key: 'interfaces',
      label: 'Interfaces',
      children: (
        <Table
          columns={ifColumns}
          dataSource={interfaces || []}
          rowKey="ifname"
          loading={ifLoading}
          size="small"
        />
      ),
    },
    {
      key: 'routes',
      label: 'Routing',
      children: (
        <>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setRouteModal(true)}
            style={{ marginBottom: 12 }}
          >
            Add Route
          </Button>
          <Table
            columns={rtColumns}
            dataSource={routes || []}
            rowKey={(r) => `${r.dst || 'default'}-${r.dev}`}
            loading={rtLoading}
            size="small"
          />
        </>
      ),
    },
    {
      key: 'nat',
      label: 'NAT',
      children: (
        <>
          <Space style={{ marginBottom: 12 }}>
            <Button type="primary" onClick={() => setNatModal(true)}>
              Add Masquerade
            </Button>
            <Button onClick={() => setPortFwdModal(true)}>Add Port Forward</Button>
          </Space>
          <pre
            style={{
              background: '#f5f5f5',
              padding: 12,
              borderRadius: 4,
              fontSize: 12,
              maxHeight: 400,
              overflow: 'auto',
            }}
          >
            {JSON.stringify(nat, null, 2)}
          </pre>
        </>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Network</Typography.Title>
        <Button
          icon={<ReloadOutlined />}
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['interfaces'] });
            queryClient.invalidateQueries({ queryKey: ['routes'] });
          }}
        />
      </div>
      <Card>
        <Tabs items={items} />
      </Card>

      <Modal
        title="Add Route"
        open={routeModal}
        onCancel={() => setRouteModal(false)}
        onOk={() => routeForm.submit()}
        confirmLoading={addRouteMut.isPending}
      >
        <Form form={routeForm} layout="vertical" onFinish={(v) => addRouteMut.mutate(v)}>
          <Form.Item name="destination" label="Destination" rules={[{ required: true }]}>
            <Input placeholder="10.0.0.0/24" />
          </Form.Item>
          <Form.Item name="gateway" label="Gateway" rules={[{ required: true }]}>
            <Input placeholder="192.168.1.1" />
          </Form.Item>
          <Form.Item name="interface" label="Interface">
            <Input placeholder="eth0 (optional)" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Add Masquerade"
        open={natModal}
        onCancel={() => setNatModal(false)}
        onOk={() => natForm.submit()}
        confirmLoading={masqMut.isPending}
      >
        <Form form={natForm} layout="vertical" onFinish={(v) => masqMut.mutate(v)}>
          <Form.Item name="out_interface" label="Outbound Interface" rules={[{ required: true }]}>
            <Input placeholder="eth0" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Add Port Forward"
        open={portFwdModal}
        onCancel={() => setPortFwdModal(false)}
        onOk={() => fwdForm.submit()}
        confirmLoading={fwdMut.isPending}
      >
        <Form
          form={fwdForm}
          layout="vertical"
          onFinish={(v) =>
            fwdMut.mutate({ ...v, dport: Number(v.dport), dest_port: Number(v.dest_port) })
          }
        >
          <Form.Item name="protocol" label="Protocol" rules={[{ required: true }]} initialValue="tcp">
            <Select>
              <Select.Option value="tcp">TCP</Select.Option>
              <Select.Option value="udp">UDP</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="dport" label="External Port" rules={[{ required: true }]}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="dest_ip" label="Destination IP" rules={[{ required: true }]}>
            <Input placeholder="192.168.1.100" />
          </Form.Item>
          <Form.Item name="dest_port" label="Destination Port" rules={[{ required: true }]}>
            <Input type="number" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Interfaces;
