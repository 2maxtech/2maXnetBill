import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Card, Input, Select, Button, Space, Modal, Form, Typography, message, Popconfirm } from 'antd';
import { PlusOutlined, SearchOutlined, KeyOutlined, DeleteOutlined, EditOutlined, EyeOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCustomers, createCustomer, deleteCustomer, updateCustomer } from '../../api/customers';
import { getPlans } from '../../api/plans';
import { getRouters, getAreas } from '../../api/routers';
import StatusTag from '../../components/StatusTag';
import dayjs from 'dayjs';

const generatePassword = () => {
  const chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789';
  return Array.from({ length: 8 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
};

const CustomerList = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [modalOpen, setModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<any>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['customers', page, pageSize, search, statusFilter],
    queryFn: () => getCustomers({ page, page_size: pageSize, search: search || undefined, status: statusFilter }),
  });

  const { data: plansData } = useQuery({
    queryKey: ['plans-active'],
    queryFn: () => getPlans({ active_only: true }),
  });

  const { data: routersData } = useQuery({
    queryKey: ['routers'],
    queryFn: () => getRouters(),
  });

  const { data: areasData } = useQuery({
    queryKey: ['areas'],
    queryFn: () => getAreas(),
  });

  const createMutation = useMutation({
    mutationFn: createCustomer,
    onSuccess: () => {
      message.success('Customer created');
      setModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
    onError: () => message.error('Failed to create customer'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCustomer(id),
    onSuccess: () => {
      message.success('Customer terminated');
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
    onError: () => message.error('Failed to terminate customer'),
  });

  const editMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) => updateCustomer(id, data),
    onSuccess: () => {
      message.success('Customer updated');
      setEditModalOpen(false);
      setEditingCustomer(null);
      editForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
    onError: () => message.error('Failed to update customer'),
  });

  const openEditModal = (record: any) => {
    setEditingCustomer(record);
    editForm.setFieldsValue({
      full_name: record.full_name,
      email: record.email,
      phone: record.phone,
      address: record.address,
      pppoe_username: record.pppoe_username,
      pppoe_password: '',
      plan_id: record.plan_id,
      mac_address: record.mac_address || '',
      router_id: record.router_id || undefined,
      area_id: record.area_id || undefined,
    });
    setEditModalOpen(true);
  };

  const columns = [
    { title: 'Name', dataIndex: 'full_name', key: 'name', render: (text: string, record: any) => <a onClick={() => navigate(`/customers/${record.id}`)}>{text}</a> },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'PPPoE User', dataIndex: 'pppoe_username', key: 'pppoe' },
    { title: 'Plan', key: 'plan', render: (_: any, record: any) => record.plan?.name || '-' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (status: string) => <StatusTag status={status} /> },
    { title: 'Created', dataIndex: 'created_at', key: 'created', render: (d: string) => dayjs(d).format('YYYY-MM-DD') },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/customers/${record.id}`)} />
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)} />
          <Popconfirm
            title="Terminate this customer?"
            description="This will set their status to terminated."
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="Terminate"
            okButtonProps={{ danger: true }}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Customers</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>Add Customer</Button>
      </div>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Input placeholder="Search..." prefix={<SearchOutlined />} value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} allowClear style={{ width: 250 }} />
          <Select placeholder="Status" value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1); }} allowClear style={{ width: 150 }}>
            <Select.Option value="active">Active</Select.Option>
            <Select.Option value="suspended">Suspended</Select.Option>
            <Select.Option value="disconnected">Disconnected</Select.Option>
            <Select.Option value="terminated">Terminated</Select.Option>
          </Select>
        </Space>
        <Table
          dataSource={data?.data?.items}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={{ current: page, pageSize, total: data?.data?.total, onChange: (p, ps) => { setPage(p); setPageSize(ps); }, showSizeChanger: true, showTotal: (total) => `${total} customers` }}
        />
      </Card>

      <Modal title="Add Customer" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()} confirmLoading={createMutation.isPending} width={600}>
        <Form form={form} layout="vertical" onFinish={(values) => createMutation.mutate(values)}>
          <Form.Item name="full_name" label="Full Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}><Input /></Form.Item>
          <Form.Item name="phone" label="Phone" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="address" label="Address"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="pppoe_username" label="PPPoE Username" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="pppoe_password" label="PPPoE Password" rules={[{ required: true }]}>
            <Input.Password
              addonAfter={
                <Button
                  size="small"
                  type="text"
                  icon={<KeyOutlined />}
                  onClick={() => form.setFieldValue('pppoe_password', generatePassword())}
                >
                  Generate
                </Button>
              }
            />
          </Form.Item>
          <Form.Item name="plan_id" label="Plan" rules={[{ required: true }]}>
            <Select placeholder="Select plan">
              {plansData?.data?.map((p: any) => <Select.Option key={p.id} value={p.id}>{p.name} — ₱{p.monthly_price}/mo</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="mac_address" label="MAC Address"><Input placeholder="AA:BB:CC:DD:EE:FF" /></Form.Item>
          <Form.Item name="area_id" label="Area">
            <Select placeholder="Select area" allowClear>
              {areasData?.data?.map((a: any) => <Select.Option key={a.id} value={a.id}>{a.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="router_id" label="Router Override">
            <Select placeholder="Default router" allowClear>
              {routersData?.data?.map((r: any) => <Select.Option key={r.id} value={r.id}>{r.name}</Select.Option>)}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Customer Modal */}
      <Modal
        title="Edit Customer"
        open={editModalOpen}
        onCancel={() => { setEditModalOpen(false); setEditingCustomer(null); editForm.resetFields(); }}
        onOk={() => editForm.submit()}
        confirmLoading={editMutation.isPending}
        width={600}
      >
        <Form form={editForm} layout="vertical" onFinish={(values) => editMutation.mutate({ id: editingCustomer?.id, data: values })}>
          <Form.Item name="full_name" label="Full Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}><Input /></Form.Item>
          <Form.Item name="phone" label="Phone" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="address" label="Address"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="pppoe_username" label="PPPoE Username" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="pppoe_password" label="PPPoE Password (leave blank to keep current)"><Input.Password /></Form.Item>
          <Form.Item name="plan_id" label="Plan" rules={[{ required: true }]}>
            <Select placeholder="Select plan">
              {plansData?.data?.map((p: any) => <Select.Option key={p.id} value={p.id}>{p.name} — ₱{p.monthly_price}/mo</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="mac_address" label="MAC Address"><Input placeholder="AA:BB:CC:DD:EE:FF" /></Form.Item>
          <Form.Item name="area_id" label="Area">
            <Select placeholder="Select area" allowClear>
              {areasData?.data?.map((a: any) => <Select.Option key={a.id} value={a.id}>{a.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="router_id" label="Router Override">
            <Select placeholder="Default router" allowClear>
              {routersData?.data?.map((r: any) => <Select.Option key={r.id} value={r.id}>{r.name}</Select.Option>)}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CustomerList;
