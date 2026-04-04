import { useNavigate, useLocation } from 'react-router-dom';
import { Menu } from 'antd';
import type { MenuProps } from 'antd';
import {
  DashboardOutlined, TeamOutlined, AppstoreOutlined,
  FileTextOutlined, DollarOutlined, UserOutlined, DesktopOutlined, FileSearchOutlined,
  WifiOutlined, CloudServerOutlined, EnvironmentOutlined, TagsOutlined,
  CustomerServiceOutlined, GlobalOutlined, FireOutlined, AuditOutlined, SettingOutlined,
} from '@ant-design/icons';

type MenuItem = Required<MenuProps>['items'][number];

const menuItems: MenuItem[] = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/customers', icon: <TeamOutlined />, label: 'Customers' },
  { key: '/plans', icon: <AppstoreOutlined />, label: 'Plans' },
  {
    key: 'billing',
    icon: <FileTextOutlined />,
    label: 'Billing',
    children: [
      { key: '/billing/invoices', icon: <FileTextOutlined />, label: 'Invoices' },
      { key: '/billing/payments', icon: <DollarOutlined />, label: 'Payments' },
      { key: '/billing/expenses', icon: <DollarOutlined />, label: 'Expenses' },
      { key: '/billing/vouchers', icon: <TagsOutlined />, label: 'Vouchers' },
    ],
  },
  { key: '/active-users', icon: <WifiOutlined />, label: 'Active Users' },
  { key: '/hotspot', icon: <FireOutlined />, label: 'Hotspot' },
  { key: '/routers', icon: <CloudServerOutlined />, label: 'Routers' },
  { key: '/areas', icon: <EnvironmentOutlined />, label: 'Areas' },
  { key: '/tickets', icon: <CustomerServiceOutlined />, label: 'Tickets' },
  {
    key: 'system',
    icon: <DesktopOutlined />,
    label: 'System',
    children: [
      { key: '/system/users', icon: <UserOutlined />, label: 'Staff Users' },
      { key: '/ipam', icon: <GlobalOutlined />, label: 'IPAM' },
      { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
      { key: '/audit-logs', icon: <AuditOutlined />, label: 'Audit Logs' },
      { key: '/system/status', icon: <DesktopOutlined />, label: 'System Status' },
      { key: '/system/logs', icon: <FileSearchOutlined />, label: 'Logs' },
    ],
  },
];

const SideMenu = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const onClick: MenuProps['onClick'] = (e) => {
    navigate(e.key);
  };

  return (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[location.pathname]}
      defaultOpenKeys={['billing', 'system']}
      items={menuItems}
      onClick={onClick}
      style={{
        borderRight: 0,
        paddingTop: 8,
        background: 'transparent',
      }}
    />
  );
};

export default SideMenu;
