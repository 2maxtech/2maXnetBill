import { Table, Card, Typography, Empty, Button } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

const columns = [
  { title: 'Payment #', dataIndex: 'id', key: 'id' },
  { title: 'Customer', dataIndex: 'customer_name', key: 'customer' },
  { title: 'Invoice', dataIndex: 'invoice_id', key: 'invoice' },
  { title: 'Amount', key: 'amount', render: (_: unknown, r: any) => `₱${r.amount}` },
  { title: 'Method', dataIndex: 'method', key: 'method' },
  { title: 'Reference', dataIndex: 'reference_number', key: 'ref' },
  { title: 'Received By', dataIndex: 'received_by', key: 'by' },
  { title: 'Date', dataIndex: 'received_at', key: 'date' },
];

const Payments = () => (
  <div>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
      <Typography.Title level={4} style={{ margin: 0 }}>Payments</Typography.Title>
      <Button type="primary" icon={<PlusOutlined />} disabled>Record Payment</Button>
    </div>
    <Card>
      <Table columns={columns} dataSource={[]} rowKey="id" locale={{ emptyText: <Empty description="Billing API not yet configured. This page will be functional when billing endpoints are implemented." /> }} />
    </Card>
  </div>
);

export default Payments;
