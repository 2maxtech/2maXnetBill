<script setup lang="ts">
import { ref } from 'vue'

const activeStep = ref(0)

const steps = [
  {
    title: 'Connect Your Router',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7"/>',
    content: [
      { type: 'text', value: 'NetLedger connects to your MikroTik router via a secure WireGuard VPN tunnel. No ports are exposed to the public internet — your router stays invisible to outsiders.' },
      { type: 'heading', value: 'Prerequisites' },
      { type: 'steps', value: [
        'MikroTik running RouterOS v7.x or newer',
        'REST API enabled (System → Packages → "rest" should be installed; enabled by default on port 80)',
        'Internet access on your MikroTik (needed to establish the WireGuard tunnel)',
      ]},
      { type: 'heading', value: 'Add Router in NetLedger' },
      { type: 'steps', value: [
        'Go to Routers page',
        'Click "Add Router"',
        'Enter: Name, any placeholder URL (e.g. http://10.10.10.1), Username, Password',
        'Click Save — the URL will be automatically updated after VPN setup',
      ]},
      { type: 'heading', value: 'Set Up WireGuard VPN Tunnel' },
      { type: 'steps', value: [
        'On the Routers page, click the "VPN" button next to your router',
        'Step 1: Copy the generated MikroTik script and paste it into WinBox Terminal or SSH',
        'Step 2: On your MikroTik, run /interface/wireguard/print and copy the Public Key (not the private key!)',
        'Paste the public key back into the VPN setup form and click "Activate VPN"',
        'Done! Your router URL is automatically updated to the secure tunnel IP',
      ]},
      { type: 'heading', value: 'Verify Connection' },
      { type: 'steps', value: [
        'Your router should show a green "Connected" badge on the Routers page',
        'All management (customer provisioning, bandwidth changes, disconnects) works through this encrypted tunnel',
      ]},
    ],
  },
  {
    title: 'Secure Your Router',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/>',
    content: [
      { type: 'text', value: 'This is critical. Your MikroTik REST API (port 80) must be restricted so that only NetLedger can access it through the VPN tunnel. Without this, your PPPoE customers on the same LAN could access and control your router.' },
      { type: 'heading', value: 'Restrict REST API to VPN Tunnel Only' },
      { type: 'text', value: 'Run this command on your MikroTik to restrict port 80 (REST API) to the WireGuard tunnel subnet only:' },
      { type: 'code', value: '/ip service set www address=10.10.10.0/24' },
      { type: 'text', value: 'This means only devices on the 10.10.10.0/24 subnet (the VPN tunnel) can reach the REST API. Your PPPoE customers, LAN devices, and anyone on the internet will be blocked.' },
      { type: 'heading', value: 'Why This Matters' },
      { type: 'steps', value: [
        'Your PPPoE customers are on the same physical network as your router',
        'Without this restriction, any subscriber could open http://router-ip/rest/ and access the API',
        'With the restriction, only NetLedger (via the encrypted VPN tunnel) can manage your router',
        'WinBox (port 8291) and SSH (port 22) are NOT affected — you can still access them normally',
      ]},
      { type: 'heading', value: 'Optional: Create a Dedicated API User' },
      { type: 'steps', value: [
        'Go to System → Users → Add on your MikroTik',
        'Create a user like "netledger-api" with group "full"',
        'Use this user in NetLedger instead of your admin account',
        'This way if the API credentials are compromised, your admin account stays safe',
      ]},
      { type: 'alert', value: 'Do not skip this step. If your REST API is open to the LAN, any tech-savvy subscriber can read your PPPoE secrets, change bandwidth profiles, or disable other customers.' },
    ],
  },
  {
    title: 'Import or Create Plans',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>',
    content: [
      { type: 'text', value: 'Plans define the bandwidth and pricing for your residential subscribers. NetLedger uses the plan name as the MikroTik profile name, so imported plans keep their original names.' },
      { type: 'heading', value: 'Import Existing Plans (Recommended)' },
      { type: 'steps', value: [
        'Go to Routers → click "Import" on your router',
        'NetLedger reads all PPPoE profiles and secrets from your MikroTik',
        'Set the monthly price for each plan before importing',
        'Click Import — Plans and Customers are created automatically',
        'Existing MikroTik profile names are preserved (no duplicates created)',
      ]},
      { type: 'heading', value: 'Create a New Plan' },
      { type: 'steps', value: [
        'Go to Plans → click "Add Plan"',
        'Enter: Plan Name (this becomes the MikroTik profile name, e.g. "20mbps_Plan1")',
        'Download/Upload Speed, Monthly Price',
        'Optional: MikroTik settings — local address, remote address (IP pool), DNS server, parent queue',
        'Optional: Data Cap (GB), FUP speeds',
        'Click Save — profile is created on MikroTik automatically when a customer is assigned this plan',
      ]},
      { type: 'alert', value: 'The plan name is used as the MikroTik PPP profile name. If you have existing profiles like "50mbps_ISP1", name your plan exactly the same to avoid creating duplicates.' },
    ],
  },
  {
    title: 'Add Customers',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/>',
    content: [
      { type: 'text', value: 'When you add a customer, NetLedger creates a PPPoE secret on your MikroTik with the correct bandwidth profile. The customer can connect immediately using their credentials.' },
      { type: 'heading', value: 'Add a Customer' },
      { type: 'steps', value: [
        'Go to Customers → click "Add Customer"',
        'Fill in: Full Name, Phone, Address',
        'PPPoE Username & Password (or click Generate for random password)',
        'Select Plan and Router',
        'Click Save — PPPoE secret is created on MikroTik instantly',
      ]},
      { type: 'heading', value: 'Customer Actions' },
      { type: 'steps', value: [
        'Throttle — reduces speed to 1Mbps, kicks session so new speed applies immediately',
        'Disconnect — disables PPPoE secret + kicks session (customer can\'t connect)',
        'Reconnect — re-enables PPPoE secret + restores original speed profile',
        'Change Plan — updates MikroTik profile to new plan speeds instantly',
        'Delete — removes customer + PPPoE secret from MikroTik (requires admin password)',
      ]},
      { type: 'heading', value: 'Customer History' },
      { type: 'text', value: 'Click on any customer to view their History tab — a timeline of all invoices, payments, throttle/disconnect events, and notifications. Useful when a customer calls to dispute charges.' },
    ],
  },
  {
    title: 'Billing & Enforcement',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z"/>',
    content: [
      { type: 'text', value: 'NetLedger handles the entire billing cycle automatically — invoice generation, overdue detection, graduated enforcement (throttle then disconnect), and auto-reconnect on payment.' },
      { type: 'heading', value: 'Automatic Daily Schedule' },
      { type: 'steps', value: [
        '2:00 AM — Generate monthly invoices (1st of month)',
        '6:00 AM — Mark past-due invoices as overdue',
        '7:00 AM — Enforce: throttle overdue subscribers, disconnect long-overdue ones',
        '9:00 AM — Send billing reminders (SMS/email)',
        'Every 5 min — Process pending notification queue',
      ]},
      { type: 'heading', value: 'How Enforcement Works' },
      { type: 'steps', value: [
        '3+ days overdue → Throttle to 1Mbps (session kicked, reconnects at slow speed)',
        '5+ days overdue → Disconnect (PPPoE secret disabled, session kicked)',
        '35+ days overdue → Flagged for termination',
        'Customer pays → auto-reconnect with original speed (no manual action needed)',
      ]},
      { type: 'text', value: 'Customize these thresholds in Settings → Billing. You can also send invoice notifications via email and SMS (configure in Settings → SMTP and Settings → SMS).' },
      { type: 'heading', value: 'Customer Portal' },
      { type: 'text', value: 'Your customers can view their invoices, usage, and submit tickets through a self-service portal. The portal URL is generated automatically from your company name — find it in Settings → Branding. Share this URL with your customers.' },
    ],
  },
  {
    title: 'Hotspot & Vouchers',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.047 8.287 8.287 0 009 9.601a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 18a3.75 3.75 0 00.495-7.468 5.99 5.99 0 00-1.925 3.547 5.975 5.975 0 01-2.133-1.001A3.75 3.75 0 0012 18z"/>',
    content: [
      { type: 'text', value: 'Hotspot is separate from residential PPPoE billing. It\'s for prepaid WiFi access — generate voucher codes, sell them to customers, and they log in through the MikroTik captive portal.' },
      { type: 'heading', value: 'Set Up Hotspot Profiles' },
      { type: 'steps', value: [
        'Go to Hotspot → Users & Sessions → Profiles tab',
        'Select your router from the dropdown',
        'Click "Add Profile" to create speed/time packages',
        'Example: Name "1hr-5M", Rate Limit "5M/10M", Session Timeout "1h"',
        'These profiles are created directly on your MikroTik — no need to open WinBox',
      ]},
      { type: 'heading', value: 'Generate Vouchers' },
      { type: 'steps', value: [
        'Go to Hotspot → Vouchers',
        'Click "Generate Batch"',
        'Select your router and a hotspot profile',
        'Set quantity and duration (in hours)',
        'Generated codes can be copied individually or all at once',
        'Print or distribute the codes to customers',
      ]},
      { type: 'heading', value: 'How Vouchers Work' },
      { type: 'steps', value: [
        'Customer connects to your WiFi → captive portal appears',
        'Customer enters the voucher code as both username and password',
        'MikroTik creates a hotspot user with the speed/time limit from the voucher profile',
        'Access expires after the configured duration',
      ]},
      { type: 'alert', value: 'Hotspot requires a hotspot server configured on your MikroTik (IP → Hotspot → Setup). The hotspot server, IP pool, and captive portal page are managed on the router — NetLedger handles profiles and vouchers.' },
    ],
  },
  {
    title: 'Branding & Settings',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>',
    content: [
      { type: 'text', value: 'Customize your company branding for invoices and the customer portal. Set up email and SMS notifications to keep your subscribers informed.' },
      { type: 'heading', value: 'Company Branding' },
      { type: 'steps', value: [
        'Go to Settings → Branding',
        'Enter Company Name, Address, Phone, Email',
        'Upload your logo (appears on invoices and customer portal)',
        'Set Invoice Prefix (e.g. "INV-") and Footer text',
        'Your Customer Portal URL is shown here — share it with your subscribers',
      ]},
      { type: 'heading', value: 'Email & SMS Notifications' },
      { type: 'steps', value: [
        'Settings → SMTP: configure your mail server (Gmail: smtp.gmail.com, port 587, App Password)',
        'Settings → SMS: configure your SMS provider API',
        'Notifications are sent automatically when invoices are generated and when due dates approach',
        'Use "Send Test" buttons to verify both work before going live',
      ]},
      { type: 'heading', value: 'Billing Settings' },
      { type: 'steps', value: [
        'Settings → Billing: customize enforcement thresholds',
        'Days before due to send reminder (default: 5)',
        'Days after due to throttle (default: 3)',
        'Days after due to disconnect (default: 5)',
        'Days after due to terminate (default: 35)',
        'Toggle auto-generation and notification sending',
      ]},
    ],
  },
]
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Setup Guide</h1>
      <p class="text-sm text-gray-500 mt-0.5">Follow these steps to get your ISP billing system running</p>
    </div>

    <!-- Progress bar -->
    <div class="flex items-center gap-1">
      <button
        v-for="(step, i) in steps"
        :key="i"
        @click="activeStep = i"
        :class="[
          'flex-1 h-2 rounded-full transition-colors',
          i <= activeStep ? 'bg-primary' : 'bg-gray-200'
        ]"
      />
    </div>

    <!-- Step navigation -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
      <button
        v-for="(step, i) in steps"
        :key="i"
        @click="activeStep = i"
        :class="[
          'flex flex-col items-center gap-2 p-3 rounded-xl border text-center transition-all',
          i === activeStep
            ? 'border-primary bg-primary/5 shadow-sm'
            : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'
        ]"
      >
        <div :class="[
          'w-8 h-8 rounded-lg flex items-center justify-center',
          i === activeStep ? 'bg-primary/10' : 'bg-gray-100'
        ]">
          <svg :class="['w-4 h-4', i === activeStep ? 'text-primary' : 'text-gray-500']" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" v-html="step.icon" />
        </div>
        <span :class="['text-xs font-medium leading-tight', i === activeStep ? 'text-primary' : 'text-gray-600']">
          {{ step.title }}
        </span>
      </button>
    </div>

    <!-- Step content -->
    <div class="rounded-xl bg-white shadow-sm border border-gray-100 p-6 lg:p-8">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
          <svg class="w-5 h-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" v-html="steps[activeStep].icon" />
        </div>
        <div>
          <p class="text-xs font-medium text-primary uppercase tracking-wider">Step {{ activeStep + 1 }} of {{ steps.length }}</p>
          <h2 class="text-lg font-semibold text-gray-900">{{ steps[activeStep].title }}</h2>
        </div>
      </div>

      <div class="space-y-5">
        <template v-for="(block, bi) in steps[activeStep].content" :key="bi">
          <p v-if="block.type === 'text'" class="text-sm text-gray-600 leading-relaxed">{{ block.value }}</p>

          <h3 v-if="block.type === 'heading'" class="text-sm font-semibold text-gray-800 pt-2">{{ block.value }}</h3>

          <ol v-if="block.type === 'steps'" class="space-y-2 pl-1">
            <li v-for="(s, si) in (block.value as string[])" :key="si" class="flex items-start gap-3">
              <span class="w-6 h-6 rounded-full bg-gray-100 text-gray-500 text-xs font-semibold flex items-center justify-center shrink-0 mt-0.5">{{ si + 1 }}</span>
              <span class="text-sm text-gray-600">{{ s }}</span>
            </li>
          </ol>

          <div v-if="block.type === 'code'" class="rounded-lg bg-gray-900 p-4 overflow-x-auto">
            <code class="text-sm font-mono text-green-400">{{ block.value }}</code>
          </div>

          <div v-if="block.type === 'alert'" class="flex items-start gap-3 rounded-lg bg-amber-50 border border-amber-200 p-4">
            <svg class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg>
            <p class="text-sm text-amber-800">{{ block.value }}</p>
          </div>
        </template>
      </div>

      <!-- Navigation -->
      <div class="flex items-center justify-between mt-8 pt-6 border-t border-gray-100">
        <button
          v-if="activeStep > 0"
          @click="activeStep--"
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z" clip-rule="evenodd"/></svg>
          Previous
        </button>
        <div v-else />
        <button
          v-if="activeStep < steps.length - 1"
          @click="activeStep++"
          class="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-lg transition-colors"
        >
          Next Step
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z" clip-rule="evenodd"/></svg>
        </button>
        <router-link
          v-else
          to="/dashboard"
          class="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
        >
          Go to Dashboard
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd"/></svg>
        </router-link>
      </div>
    </div>
  </div>
</template>
