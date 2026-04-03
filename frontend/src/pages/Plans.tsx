import { useState } from 'react';
import { Table, Card, Button, Modal, Form, Input, InputNumber, Typography, Popconfirm, Space, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPlans, createPlan, updatePlan, deletePlan, type Plan } from '../api/plans';
import StatusTag from '../components/StatusTag';
import dayjs from 'dayjs';

const Plans = () => {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({ queryKey: ['plans'], queryFn: () => getPlans() });

  const createMut = useMutation({
    mutationFn: createPlan,
    onSuccess: () => { message.success('Plan created'); closeModal(); queryClient.invalidateQueries({ queryKey: ['plans'] }); },
    onError: () => message.error('Failed to create plan'),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) => updatePlan(id, data),
    onSuccess: () => { message.success('Plan updated'); closeModal(); queryClient.invalidateQueries({ queryKey: ['plans'] }); },
    onError: () => message.error('Failed to update plan'),
  });

  const deleteMut = useMutation({
    mutationFn: deletePlan,
    onSuccess: () => { message.success('Plan deactivated'); queryClient.invalidateQueries({ queryKey: ['plans'] }); },
  });

  const closeModal = () => { setModalOpen(false); setEditingPlan(null); form.resetFields(); };

  const openEdit = (plan: Plan) => {
    setEditingPlan(plan);
    form.setFieldsValue(plan);
    setModalOpen(true);
  };

  const onFinish = (values: Record<string, unknown>) => {
    if (editingPlan) updateMut.mutate({ id: editingPlan.id, data: values });
    else createMut.mutate(values);
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Download (Mbps)', dataIndex: 'download_mbps', key: 'down' },
    { title: 'Upload (Mbps)', dataIndex: 'upload_mbps', key: 'up' },
    { title: 'Price (₱)', dataIndex: 'monthly_price', key: 'price', render: (v: string) => `₱${v}` },
    { title: 'Status', key: 'status', render: (_: unknown, r: Plan) => <StatusTag status={r.is_active ? 'active' : 'terminated'} /> },
    { title: 'Created', dataIndex: 'created_at', key: 'created', render: (d: string) => dayjs(d).format('YYYY-MM-DD') },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, record: Plan) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm title="Deactivate this plan?" onConfirm={() => deleteMut.mutate(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Plans</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>Add Plan</Button>
      </div>
      <Card>
        <Table dataSource={data?.data} columns={columns} rowKey="id" loading={isLoading} pagination={false} />
      </Card>
      <Modal title={editingPlan ? 'Edit Plan' : 'Add Plan'} open={modalOpen} onCancel={closeModal} onOk={() => form.submit()} confirmLoading={createMut.isPending || updateMut.isPending}>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="download_mbps" label="Download (Mbps)" rules={[{ required: true }]}><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="upload_mbps" label="Upload (Mbps)" rules={[{ required: true }]}><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="monthly_price" label="Monthly Price (₱)" rules={[{ required: true }]}><InputNumber min={0} precision={2} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Plans;
