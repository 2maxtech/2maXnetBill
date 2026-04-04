import { useState } from 'react';
import { Card, Form, Input, Button, Typography, message } from 'antd';
import { UserOutlined, LockOutlined, WifiOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { portalLogin } from '../../api/portal';

const PortalLogin = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      const res = await portalLogin(values.email, values.password);
      localStorage.setItem('portal_token', res.data.access_token);
      localStorage.setItem('portal_customer', JSON.stringify(res.data.customer));
      navigate('/portal');
    } catch {
      message.error('Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' }}>
      <Card style={{ width: 400, borderRadius: 8 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <WifiOutlined style={{ fontSize: 40, color: '#0d9488' }} />
          <Typography.Title level={3} style={{ margin: '8px 0 4px' }}>2maXnet</Typography.Title>
          <Typography.Text type="secondary">Customer Portal</Typography.Text>
        </div>
        <Form onFinish={onFinish} layout="vertical">
          <Form.Item name="email" rules={[{ required: true, message: 'Enter your email' }]}>
            <Input prefix={<UserOutlined />} placeholder="Email address" size="large" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: 'Enter your password' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="Password" size="large" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block size="large" loading={loading} style={{ background: '#0d9488' }}>
            Sign In
          </Button>
        </Form>
      </Card>
    </div>
  );
};

export default PortalLogin;
