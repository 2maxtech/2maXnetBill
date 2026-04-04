import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, Card, Typography, Select, Space, Button, message, DatePicker, Popconfirm, Modal } from 'antd';
import { PlusOutlined, ReloadOutlined, DownloadOutlined, PrinterOutlined, UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import StatusTag from '../../components/StatusTag';
import { getInvoices, generateInvoices, updateInvoice, downloadInvoicePdf } from '../../api/billing';
import { getCustomers } from '../../api/customers';
import type { Invoice } from '../../api/billing';

const Invoices = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);

  const [genForCustomerOpen, setGenForCustomerOpen] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | undefined>();
  const [customerSearch, setCustomerSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['invoices', page, statusFilter, dateRange],
    queryFn: () =>
      getInvoices({
        page,
        size: 20,
        status: statusFilter,
        from_date: dateRange?.[0]?.format('YYYY-MM-DD'),
        to_date: dateRange?.[1]?.format('YYYY-MM-DD'),
      }).then((r) => r.data),
  });

  const { data: customersData } = useQuery({
    queryKey: ['customers-search', customerSearch],
    queryFn: () => getCustomers({ page: 1, page_size: 50, search: customerSearch || undefined }),
    enabled: genForCustomerOpen,
  });

  const generateMut = useMutation({
    mutationFn: (customerId?: string) => generateInvoices(customerId),
    onSuccess: (res) => {
      message.success(`Generated ${res.data.generated} invoice(s), skipped ${res.data.skipped}`);
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
    onError: () => message.error('Failed to generate invoices'),
  });

  const voidMut = useMutation({
    mutationFn: (id: string) => updateInvoice(id, { status: 'void' }),
    onSuccess: () => {
      message.success('Invoice voided');
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
    onError: () => message.error('Failed to void invoice'),
  });

  const handleGenerateForCustomer = () => {
    if (!selectedCustomerId) return;
    generateMut.mutate(selectedCustomerId, {
      onSuccess: () => {
        setGenForCustomerOpen(false);
        setSelectedCustomerId(undefined);
        setCustomerSearch('');
      },
    });
  };

  const columns = [
    {
      title: 'Customer',
      dataIndex: 'customer_name',
      key: 'customer',
      ellipsis: true,
    },
    {
      title: 'Amount',
      key: 'amount',
      render: (_: unknown, r: Invoice) => `₱${Number(r.amount).toLocaleString('en-PH', { minimumFractionDigits: 2 })}`,
      width: 120,
    },
    {
      title: 'Paid',
      key: 'total_paid',
      render: (_: unknown, r: Invoice) => r.total_paid ? `₱${Number(r.total_paid).toLocaleString('en-PH', { minimumFractionDigits: 2 })}` : '₱0.00',
      width: 120,
    },
    {
      title: 'Due Date',
      dataIndex: 'due_date',
      key: 'due',
      width: 110,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => <StatusTag status={s} />,
      width: 100,
    },
    {
      title: 'Issued',
      dataIndex: 'issued_at',
      key: 'issued',
      render: (d: string) => dayjs(d).format('YYYY-MM-DD'),
      width: 110,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 160,
      render: (_: unknown, r: Invoice) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={async () => {
              try {
                const res = await downloadInvoicePdf(r.id);
                const url = window.URL.createObjectURL(new Blob([res.data]));
                const link = document.createElement('a');
                link.href = url;
                link.download = `invoice-${r.id.slice(0, 8)}.pdf`;
                link.click();
                window.URL.revokeObjectURL(url);
              } catch { message.error('Failed to download PDF'); }
            }}
          >
            PDF
          </Button>
          <Button
            type="link"
            size="small"
            icon={<PrinterOutlined />}
            onClick={() => window.open(`/api/v1/billing/invoices/${r.id}/pdf`, '_blank')}
          />
          {r.status !== 'void' && r.status !== 'paid' ? (
            <Popconfirm title="Void this invoice?" onConfirm={() => voidMut.mutate(r.id)}>
              <Button type="link" size="small" danger>Void</Button>
            </Popconfirm>
          ) : null}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Invoices</Typography.Title>
        <Space>
          <Button
            icon={<UserOutlined />}
            onClick={() => setGenForCustomerOpen(true)}
          >
            Generate for Customer
          </Button>
          <Popconfirm
            title="Generate invoices for all active customers?"
            onConfirm={() => generateMut.mutate(undefined)}
          >
            <Button
              type="primary"
              icon={<PlusOutlined />}
              loading={generateMut.isPending}
            >
              Generate Invoices
            </Button>
          </Popconfirm>
        </Space>
      </div>
      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Select
            placeholder="Filter by status"
            allowClear
            style={{ width: 150 }}
            value={statusFilter}
            onChange={setStatusFilter}
          >
            <Select.Option value="pending">Pending</Select.Option>
            <Select.Option value="paid">Paid</Select.Option>
            <Select.Option value="overdue">Overdue</Select.Option>
            <Select.Option value="void">Void</Select.Option>
          </Select>
          <DatePicker.RangePicker
            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs | null, dayjs.Dayjs | null] | null)}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries({ queryKey: ['invoices'] })}
          />
        </Space>
        <Table
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: 20,
            total: data?.total || 0,
            onChange: setPage,
            showTotal: (total) => `${total} invoices`,
          }}
        />
      </Card>

      {/* Generate for specific customer modal */}
      <Modal
        title="Generate Invoice for Customer"
        open={genForCustomerOpen}
        onCancel={() => { setGenForCustomerOpen(false); setSelectedCustomerId(undefined); setCustomerSearch(''); }}
        onOk={handleGenerateForCustomer}
        confirmLoading={generateMut.isPending}
        okButtonProps={{ disabled: !selectedCustomerId }}
        okText="Generate"
      >
        <Select
          showSearch
          style={{ width: '100%' }}
          placeholder="Search and select customer"
          filterOption={false}
          onSearch={setCustomerSearch}
          value={selectedCustomerId}
          onChange={setSelectedCustomerId}
          notFoundContent={customersData ? 'No customers found' : 'Type to search'}
        >
          {customersData?.data?.items?.map((c: any) => (
            <Select.Option key={c.id} value={c.id}>{c.full_name} ({c.pppoe_username})</Select.Option>
          ))}
        </Select>
      </Modal>
    </div>
  );
};

export default Invoices;
