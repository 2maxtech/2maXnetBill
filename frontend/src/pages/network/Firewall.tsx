import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Typography, Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { getFirewallRuleset, addFirewallRule, deleteFirewallRule } from '../../api/network';

const Firewall = () => {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const { data: ruleset, isLoading } = useQuery({
    queryKey: ['firewall-ruleset'],
    queryFn: () => getFirewallRuleset().then((r) => r.data),
  });

  const addMut = useMutation({
    mutationFn: addFirewallRule,
    onSuccess: () => {
      message.success('Rule added');
      setModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['firewall-ruleset'] });
    },
    onError: () => message.error('Failed to add rule'),
  });

  const deleteMut = useMutation({
    mutationFn: deleteFirewallRule,
    onSuccess: () => {
      message.success('Rule deleted');
      queryClient.invalidateQueries({ queryKey: ['firewall-ruleset'] });
    },
    onError: () => message.error('Failed to delete rule'),
  });

  // Extract rules from nftables JSON format
  const rules: any[] = [];
  if (ruleset?.nftables) {
    ruleset.nftables.forEach((item: any) => {
      if (item.rule) {
        rules.push({ ...item.rule, key: `${item.rule.table}-${item.rule.chain}-${item.rule.handle}` });
      }
    });
  }

  const columns = [
    { title: 'Table', dataIndex: 'table', key: 'table', width: 100 },
    { title: 'Chain', dataIndex: 'chain', key: 'chain', width: 120 },
    { title: 'Family', dataIndex: 'family', key: 'family', width: 80 },
    {
      title: 'Expression',
      key: 'expr',
      render: (_: unknown, r: any) => (
        <code style={{ fontSize: 12 }}>{JSON.stringify(r.expr)}</code>
      ),
      ellipsis: true,
    },
    { title: 'Handle', dataIndex: 'handle', key: 'handle', width: 70 },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, r: any) => (
        <Popconfirm
          title="Delete this rule?"
          onConfirm={() =>
            deleteMut.mutate({ table: r.table, chain: r.chain, handle: r.handle, family: r.family })
          }
        >
          <Button type="link" danger size="small" icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Firewall Rules</Typography.Title>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries({ queryKey: ['firewall-ruleset'] })}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            Add Rule
          </Button>
        </Space>
      </div>
      <Card>
        <Table columns={columns} dataSource={rules} loading={isLoading} rowKey="key" size="small" />
      </Card>

      <Modal
        title="Add Firewall Rule"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={addMut.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(v) => addMut.mutate(v)}>
          <Form.Item name="table" label="Table" rules={[{ required: true }]} initialValue="filter">
            <Input />
          </Form.Item>
          <Form.Item name="chain" label="Chain" rules={[{ required: true }]} initialValue="input">
            <Input />
          </Form.Item>
          <Form.Item
            name="rule"
            label="Rule"
            rules={[{ required: true }]}
            extra="e.g. tcp dport 80 accept"
          >
            <Input.TextArea rows={2} placeholder="tcp dport 80 accept" />
          </Form.Item>
          <Form.Item name="family" label="Family" initialValue="inet">
            <Select>
              <Select.Option value="inet">inet</Select.Option>
              <Select.Option value="ip">ip</Select.Option>
              <Select.Option value="ip6">ip6</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Firewall;
