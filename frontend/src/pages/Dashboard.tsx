import { Row, Col, Card, Typography, Badge } from 'antd';
import {
  TeamOutlined, WifiOutlined, DollarOutlined, WarningOutlined,
  ArrowUpOutlined, ArrowDownOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import ReactECharts from 'echarts-for-react';
import StatCard from '../components/StatCard';
import { getCustomers } from '../api/customers';
import { useAuth } from '../hooks/useAuth';

const Dashboard = () => {
  const { user } = useAuth();

  const { data: customersData } = useQuery({
    queryKey: ['customers-count'],
    queryFn: () => getCustomers({ page: 1, page_size: 1 }),
  });

  const totalCustomers = customersData?.data?.total ?? 0;

  const trafficChartOption = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#3d2a0a',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#e2e8f0' },
    },
    legend: { data: ['Download', 'Upload'], textStyle: { color: '#64748b' } },
    grid: { left: 16, right: 16, top: 40, bottom: 24, containLabel: true },
    xAxis: {
      type: 'category',
      data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#94a3b8' },
    },
    yAxis: {
      type: 'value',
      name: 'Mbps',
      nameTextStyle: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#94a3b8' },
    },
    series: [
      {
        name: 'Download',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.15, color: '#e8700a' },
        data: [20, 15, 30, 65, 80, 55, 35],
        itemStyle: { color: '#e8700a' },
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 4,
      },
      {
        name: 'Upload',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.15, color: '#f9a825' },
        data: [5, 3, 8, 15, 20, 12, 8],
        itemStyle: { color: '#f9a825' },
        lineStyle: { width: 2 },
        symbol: 'circle',
        symbolSize: 4,
      },
    ],
  };

  const hourOfDay = new Date().getHours();
  const greeting = hourOfDay < 12 ? 'Good morning' : hourOfDay < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <div>
      {/* Welcome Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #1c1306 0%, #3d2a0a 100%)',
        borderRadius: 12,
        padding: '20px 28px',
        marginBottom: 24,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <Typography.Title level={4} style={{ color: '#ffffff', margin: 0, fontWeight: 600 }}>
            {greeting}, {user?.username ?? 'Admin'}
          </Typography.Title>
          <Typography.Text style={{ color: '#94a3b8', fontSize: 13 }}>
            Here's what's happening on your network today.
          </Typography.Text>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Badge status="success" />
          <Typography.Text style={{ color: '#10b981', fontSize: 13, fontWeight: 500 }}>
            Network Online
          </Typography.Text>
        </div>
      </div>

      {/* Stat Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Online Customers"
            value="--"
            prefix={<WifiOutlined />}
            valueStyle={{ color: '#10b981' }}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Total Customers"
            value={totalCustomers}
            prefix={<TeamOutlined />}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Monthly Revenue"
            value="--"
            prefix={<DollarOutlined />}
            valueStyle={{ color: '#e8700a' }}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Overdue Invoices"
            value="--"
            prefix={<WarningOutlined />}
            valueStyle={{ color: '#f59e0b' }}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* Traffic Chart */}
        <Col xs={24} lg={16}>
          <Card
            title={
              <span style={{ color: '#1c1306', fontWeight: 600 }}>Network Traffic</span>
            }
            extra={
              <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#94a3b8' }}>
                <span><ArrowDownOutlined style={{ color: '#e8700a' }} /> Download</span>
                <span><ArrowUpOutlined style={{ color: '#f9a825' }} /> Upload</span>
              </div>
            }
            style={{ borderRadius: 12 }}
            styles={{ header: { borderBottom: '1px solid #f1f5f9' } }}
          >
            <ReactECharts option={trafficChartOption} style={{ height: 300 }} />
          </Card>
        </Col>

        {/* System Health */}
        <Col xs={24} lg={8}>
          <Card
            title={<span style={{ color: '#1c1306', fontWeight: 600 }}>System Health</span>}
            style={{ borderRadius: 12, height: '100%' }}
            styles={{ header: { borderBottom: '1px solid #f1f5f9' } }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, paddingTop: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography.Text style={{ color: '#475569', fontSize: 13 }}>Router / Firewall</Typography.Text>
                <span style={{
                  background: 'rgba(16,185,129,0.1)',
                  color: '#10b981',
                  fontSize: 11,
                  fontWeight: 600,
                  padding: '2px 10px',
                  borderRadius: 20,
                }}>ONLINE</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography.Text style={{ color: '#475569', fontSize: 13 }}>PPPoE Server</Typography.Text>
                <span style={{
                  background: 'rgba(16,185,129,0.1)',
                  color: '#10b981',
                  fontSize: 11,
                  fontWeight: 600,
                  padding: '2px 10px',
                  borderRadius: 20,
                }}>ONLINE</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography.Text style={{ color: '#475569', fontSize: 13 }}>Billing Engine</Typography.Text>
                <span style={{
                  background: 'rgba(16,185,129,0.1)',
                  color: '#10b981',
                  fontSize: 11,
                  fontWeight: 600,
                  padding: '2px 10px',
                  borderRadius: 20,
                }}>ONLINE</span>
              </div>
              <div style={{
                marginTop: 8,
                padding: '12px 14px',
                background: '#f8fafc',
                borderRadius: 8,
                border: '1px solid #e2e8f0',
              }}>
                <Typography.Text style={{ color: '#94a3b8', fontSize: 12 }}>
                  MikroTik integration active. Live PPPoE stats available in Active Users.
                </Typography.Text>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
