import client from './client';

export const getSmtpSettings = () => client.get('/settings/smtp');
export const saveSmtpSettings = (data: any) => client.put('/settings/smtp', data);
export const testSmtp = (data: any) => client.post('/settings/smtp/test', data);

export const getSmsSettings = () => client.get('/settings/sms');
export const saveSmsSettings = (data: any) => client.put('/settings/sms', data);
export const testSms = (data: any) => client.post('/settings/sms/test', data);
