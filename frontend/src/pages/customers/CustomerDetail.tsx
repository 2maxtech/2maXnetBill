import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Space, Typography, Tabs, Popconfirm, message, Spin, Empty, Modal, Form, Input, Select, Table } from 'antd';
import { ArrowLeftOutlined, DisconnectOutlined, LinkOutlined, ThunderboltOutlined, EditOutlined, SwapOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCustomer, disconnectCustomer, reconnectCustomer, throttleCustomer, updateCustomer, changePlan, deleteCustomer } from '../../api/customers';
import { getInvoices } from '../../api/billing';
import { getPlans } from '../../api/plans';
import { getRouters, getAreas } from '../../api/routers';
import StatusTag from '../../components/StatusTag';
import dayjs from 'dayjs';

const CustomerDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [editOpen, setEditOpen] = useState(false);
  const [editForm] = Form.useForm();

  const [changePlanOpen, setChangePlanOpen] = useState(false);
  const [selectedPlanId, setSelectedPlanId] = useState<string | undefined>();

  const { data, isLoading } = useQuery({
    queryKey: ['customer', id],
    queryFn: () => getCustomer(id!),
    enabled: !!id,
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

  const { data: invoicesData } = useQuery({
    queryKey: ['customer-invoices', id],
    queryFn: () => getInvoices({ customer_id: id!, size: 50 }).then((r) => r.data),
    enabled: !!id,
  });

  const customer = data?.data;

  const onActionSuccess = (action: string) => {
    message.success(`Customer ${action}`);
    queryClient.invalidateQueries({ queryKey: ['customer', id] });
  };

  const disconnectMut = useMutation({ mutationFn: () => disconnectCustomer(id!), onSuccess: () => onActionSuccess('disconnected') });
  const reconnectMut = useMutation({ mutationFn: () => reconnectCustomer(id!), onSuccess: () => onActionSuccess('reconnected') });
  const throttleMut = useMutation({ mutationFn: () => throttleCustomer(id!), onSuccess: () => onActionSuccess('throttled') });

  const editMut = useMutation({
    mutationFn: (values: Record<string, unknown>) => updateCustomer(id!, values),
    onSuccess: () => {
      message.success('Customer updated');
      setEditOpen(false);
      editForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['customer', id] });
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
    onError: () => message.error('Failed to update customer'),
  });

  const changePlanMut = useMutation({
    mutationFn: (planId: string) => changePlan(id!, planId),
    onSuccess: () => {
      message.success('Plan changed');
      setChangePlanOpen(false);
      setSelectedPlanId(undefined);
      queryClient.invalidateQueries({ queryKey: ['customer', id] });
    },
    onError: () => message.error('Failed to change plan'),
  });

  const deleteMut = useMutation({
    mutationFn: () => deleteCustomer(id!),
    onSuccess: () => {
      message.success('Customer terminated');
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      navigate('/customers');
    },
    onError: () => message.error('Failed to terminate customer'),
  });

  const openEdit = () => {
    if (!customer) return;
    editForm.setFieldsValue({
      full_name: customer.full_name,
      email: customer.email,
      phone: customer.phone,
      address: customer.address,
      pppoe_username: customer.pppoe_username,
      pppoe_password: '',
      plan_id: customer.plan_id,
      mac_address: (customer as any).mac_address || '',
      router_id: (customer as any).router_id || undefined,
      area_id: (customer as any).area_id || undefined,
    });
    setEditOpen(true);
  };

  if (isLoading) return <Spin size="large" />;
  if (!customer) return <Empty description="Customer not found" />;

  const invoiceColumns = [
    { title: 'Issued', dataIndex: 'issued_at', key: 'issued', render: (d: string) => dayjs(d).format('YYYY-MM-DD'), width: 110 },
    { title: 'Amount', key: 'amount', render: (_: unknown, r: any) => `₱${Number(r.amount).toLocaleString('en-PH', { minimumFractionDigits: 2 })}`, width: 120 },
    { title: 'Due Date', dataIndex: 'due_date', key: 'due', width: 110 },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <StatusTag status={s} />, width: 100 },
  ];

  const tabItems = [
    {
      key: 'overview',
      label: 'Overview',
      children: (
        <Descriptions column={2} bordered>
          <Descriptions.Item label="Full Name">{customer.full_name}</Descriptions.Item>
          <Descriptions.Item label="Status"><StatusTag status={customer.status} /></Descriptions.Item>
          <Descriptions.Item label="Email">{customer.email}</Descriptions.Item>
          <Descriptions.Item label="Phone">{customer.phone}</Descriptions.Item>
          <Descriptions.Item label="Address" span={2}>{customer.address || '-'}</Descriptions.Item>
          <Descriptions.Item label="PPPoE Username">{customer.pppoe_username}</Descriptions.Item>
          <Descriptions.Item label="PPPoE Password">••••••••</Descriptions.Item>
          <Descriptions.Item label="Plan">{customer.plan?.name || '-'}</Descriptions.Item>
          <Descriptions.Item label="Speed">{customer.plan ? `${customer.plan.download_mbps}/${customer.plan.upload_mbps} Mbps` : '-'}</Descriptions.Item>
          <Descriptions.Item label="Monthly Price">{customer.plan ? `₱${customer.plan.monthly_price}` : '-'}</Descriptions.Item>
          <Descriptions.Item label="Created">{dayjs(customer.created_at).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
        </Descriptions>
      ),
    },
    {
      key: 'billing',
      label: 'Billing',
      children: (
        <div>
          <Table
            columns={invoiceColumns}
            dataSource={invoicesData?.items || []}
            rowKey="id"
            pagination={{ pageSize: 10, showTotal: (total) => `${total} invoices` }}
            size="small"
          />
        </div>
      ),
    },
    {
      key: 'sessions',
      label: 'Sessions',
      children: <Empty description="Session history will be available when the endpoint is implemented" />,
    },
    {
      key: 'activity',
      label: 'Activity',
      children: <Empty description="Activity log will be available when the endpoint is implemented" />,
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/customers')}>Back</Button>
      </Space>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Space>
            <Typography.Title level={4} style={{ margin: 0 }}>{customer.full_name}</Typography.Title>
            <StatusTag status={customer.status} />
            <Typography.Text type="secondary">{customer.plan?.name}</Typography.Text>
          </Space>
          <Space>
            <Button icon={<EditOutlined />} onClick={openEdit}>Edit</Button>
            <Button icon={<SwapOutlined />} onClick={() => { setSelectedPlanId(customer.plan_id); setChangePlanOpen(true); }}>Change Plan</Button>
            {(customer.status === 'active') && (
              <>
                <Popconfirm title="Throttle this customer?" onConfirm={() => throttleMut.mutate()}>
                  <Button icon={<ThunderboltOutlined />} loading={throttleMut.isPending}>Throttle</Button>
                </Popconfirm>
                <Popconfirm title="Disconnect this customer?" onConfirm={() => disconnectMut.mutate()}>
                  <Button danger icon={<DisconnectOutlined />} loading={disconnectMut.isPending}>Disconnect</Button>
                </Popconfirm>
              </>
            )}
            {(customer.status === 'suspended') && (
              <>
                <Popconfirm title="Disconnect this customer?" onConfirm={() => disconnectMut.mutate()}>
                  <Button danger icon={<DisconnectOutlined />} loading={disconnectMut.isPending}>Disconnect</Button>
                </Popconfirm>
                <Popconfirm title="Reconnect this customer?" onConfirm={() => reconnectMut.mutate()}>
                  <Button type="primary" icon={<LinkOutlined />} loading={reconnectMut.isPending}>Reconnect</Button>
                </Popconfirm>
              </>
            )}
            {(customer.status === 'disconnected') && (
              <Popconfirm title="Reconnect this customer?" onConfirm={() => reconnectMut.mutate()}>
                <Button type="primary" icon={<LinkOutlined />} loading={reconnectMut.isPending}>Reconnect</Button>
              </Popconfirm>
            )}
            <Popconfirm
              title="Terminate this customer?"
              description="This will permanently set their status to terminated."
              onConfirm={() => deleteMut.mutate()}
              okText="Terminate"
              okButtonProps={{ danger: true }}
            >
              <Button danger icon={<DeleteOutlined />} loading={deleteMut.isPending}>Delete</Button>
            </Popconfirm>
          </Space>
        </div>
        <Tabs items={tabItems} />
      </Card>

      {/* Edit Customer Modal */}
      <Modal
        title="Edit Customer"
        open={editOpen}
        onCancel={() => { setEditOpen(false); editForm.resetFields(); }}
        onOk={() => editForm.submit()}
        confirmLoading={editMut.isPending}
        width={600}
      >
        <Form form={editForm} layout="vertical" onFinish={(values) => editMut.mutate(values)}>
          <Form.Item name="full_name" label="Full Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}><Input /></Form.Item>
          <Form.Item name="phone" label="Phone" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="address" label="Address"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="pppoe_username" label="PPPoE Username" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="pppoe_password" label="PPPoE Password (leave blank to keep current)"><Input.Password /></Form.Item>
          <Form.Item name="plan_id" label="Plan" rules={[{ required: true }]}>
            <Select placeholder="Select plan">
              {plansData?.data?.map((p: any) => (
                <Select.Option key={p.id} value={p.id}>{p.name} — ₱{p.monthly_price}/mo</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="mac_address" label="MAC Address"><Input placeholder="AA:BB:CC:DD:EE:FF" /></Form.Item>
          <Form.Item name="router_id" label="Router Override">
            <Select placeholder="Default router" allowClear>
              {routersData?.data?.map((r: any) => (
                <Select.Option key={r.id} value={r.id}>{r.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="area_id" label="Area">
            <Select placeholder="Select area" allowClear>
              {areasData?.data?.map((a: any) => (
                <Select.Option key={a.id} value={a.id}>{a.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Change Plan Modal */}
      <Modal
        title="Change Plan"
        open={changePlanOpen}
        onCancel={() => { setChangePlanOpen(false); setSelectedPlanId(undefined); }}
        onOk={() => { if (selectedPlanId) changePlanMut.mutate(selectedPlanId); }}
        confirmLoading={changePlanMut.isPending}
        okButtonProps={{ disabled: !selectedPlanId }}
      >
        <Select
          style={{ width: '100%' }}
          placeholder="Select new plan"
          value={selectedPlanId}
          onChange={setSelectedPlanId}
        >
          {plansData?.data?.map((p: any) => (
            <Select.Option key={p.id} value={p.id}>{p.name} — ₱{p.monthly_price}/mo ({p.download_mbps}/{p.upload_mbps} Mbps)</Select.Option>
          ))}
        </Select>
      </Modal>
    </div>
  );
};

export default CustomerDetail;
