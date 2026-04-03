import { Table, Card, Typography, Empty, Select, Space } from 'antd';
import StatusTag from '../../components/StatusTag';

const columns = [
  { title: 'Invoice #', dataIndex: 'id', key: 'id' },
  { title: 'Customer', dataIndex: 'customer_name', key: 'customer' },
  { title: 'Amount', key: 'amount', render: (_: unknown, r: any) => `₱${r.amount}` },
  { title: 'Due Date', dataIndex: 'due_date', key: 'due' },
  { title: 'Status', dataIndex: 'status', key: 'status', render: (s: string) => <StatusTag status={s} /> },
  { title: 'Issued', dataIndex: 'issued_at', key: 'issued' },
];

const Invoices = () => (
  <div>
    <Typography.Title level={4}>Invoices</Typography.Title>
    <Card>
      <Space style={{ marginBottom: 16 }}>
        <Select placeholder="Filter by status" allowClear style={{ width: 150 }} disabled>
          <Select.Option value="pending">Pending</Select.Option>
          <Select.Option value="paid">Paid</Select.Option>
          <Select.Option value="overdue">Overdue</Select.Option>
          <Select.Option value="void">Void</Select.Option>
        </Select>
      </Space>
      <Table columns={columns} dataSource={[]} rowKey="id" locale={{ emptyText: <Empty description="Billing API not yet configured. This page will be functional when billing endpoints are implemented." /> }} />
    </Card>
  </div>
);

export default Invoices;
