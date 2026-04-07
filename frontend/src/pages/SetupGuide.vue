<script setup lang="ts">
import { ref } from 'vue'

const activeStep = ref(0)

const steps = [
  {
    title: 'Connect Your Router',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7"/>',
    content: [
      { type: 'text', value: 'Add your MikroTik router to NetLedger by providing its IP address, username, and password. The connection method depends on your deployment.' },
      { type: 'heading', value: 'SaaS (Hosted by NetLedger)' },
      { type: 'steps', value: [
        'Your router connects via a secure WireGuard VPN tunnel -- no ports exposed to the internet',
        'Go to Routers page and click "Add Router"',
        'Enter: Name, any placeholder URL (e.g. http://10.10.10.1), Username, Password',
        'Click Save, then click the "VPN" button next to your router',
        'Copy the generated MikroTik script and paste it into WinBox Terminal or SSH',
        'On your MikroTik, run /interface/wireguard/print and copy the Public Key',
        'Paste the public key back into the VPN setup form and click "Activate VPN"',
        'Your router URL is automatically updated to the secure tunnel IP',
      ]},
      { type: 'heading', value: 'On-Premise (Self-Hosted)' },
      { type: 'steps', value: [
        'Your NetLedger server and router are on the same LAN -- no VPN needed',
        'Go to Routers page and click "Add Router"',
        'Enter: Name, Router URL (e.g. http://192.168.88.1), Username, Password',
        'Click Save -- NetLedger connects directly to the router via the REST API',
      ]},
      { type: 'heading', value: 'Verify Connection' },
      { type: 'steps', value: [
        'Your router should show a green "Connected" badge on the Routers page',
        'All management (customer provisioning, bandwidth changes, disconnects) works through this connection',
      ]},
    ],
  },
  {
    title: 'Secure Your Router',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/>',
    content: [
      { type: 'text', value: 'Restrict the MikroTik REST API so that only NetLedger can access it. Without this, your PPPoE customers on the same network could access and control your router.' },
      { type: 'heading', value: 'SaaS: Restrict to VPN Subnet' },
      { type: 'text', value: 'Run this command on your MikroTik to restrict port 80 (REST API) to the WireGuard tunnel subnet only:' },
      { type: 'code', value: '/ip service set www address=10.10.10.0/24' },
      { type: 'heading', value: 'On-Premise: Restrict to Server IP' },
      { type: 'text', value: 'Run this command on your MikroTik, replacing <server-ip> with your NetLedger server\'s LAN IP:' },
      { type: 'code', value: '/ip service set www address=<server-ip>/32' },
      { type: 'heading', value: 'Why This Matters' },
      { type: 'steps', value: [
        'Your PPPoE customers are on the same physical network as your router',
        'Without this restriction, any subscriber could open http://router-ip/rest/ and access the API',
        'With the restriction, only NetLedger can manage your router',
        'WinBox (port 8291) and SSH (port 22) are NOT affected -- you can still access them normally',
      ]},
      { type: 'heading', value: 'Optional: Create a Dedicated API User' },
      { type: 'steps', value: [
        'Go to System -> Users -> Add on your MikroTik',
        'Create a user like "netledger-api" with group "full"',
        'Use this user in NetLedger instead of your admin account',
      ]},
      { type: 'alert', value: 'Do not skip this step. If your REST API is open to the LAN, any tech-savvy subscriber can read your PPPoE secrets, change bandwidth profiles, or disable other customers.' },
    ],
  },
  {
    title: 'Import or Create Plans',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>',
    content: [
      { type: 'text', value: 'Plans define the bandwidth and pricing for your subscribers. You can import existing MikroTik PPPoE profiles or create plans manually.' },
      { type: 'heading', value: 'Import from MikroTik (Recommended)' },
      { type: 'steps', value: [
        'Go to Routers -> click "Import" on your router',
        'NetLedger reads all PPPoE profiles and secrets from your MikroTik',
        'Set the monthly price for each plan before importing',
        'Click Import -- Plans and Customers are created automatically',
        'Existing MikroTik profile names are preserved (no duplicates created)',
      ]},
      { type: 'heading', value: 'Create a New Plan Manually' },
      { type: 'steps', value: [
        'Go to Plans -> click "Add Plan"',
        'Enter: Plan Name (this becomes the MikroTik profile name, e.g. "20mbps_Plan1")',
        'Set Download/Upload Speed and Monthly Price',
        'Optional: MikroTik settings -- local address, remote address (IP pool), DNS server, parent queue',
        'Optional: Data Cap (GB), FUP speeds',
        'Click Save -- profile is created on MikroTik automatically when a customer is assigned this plan',
      ]},
      { type: 'alert', value: 'The plan name is used as the MikroTik PPP profile name. If you have existing profiles like "50mbps_ISP1", name your plan exactly the same to avoid creating duplicates.' },
    ],
  },
  {
    title: 'Import or Add Customers',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/>',
    content: [
      { type: 'text', value: 'Import your existing PPPoE secrets from MikroTik, or add customers manually. When you add a customer, NetLedger creates the PPPoE secret on your router automatically.' },
      { type: 'heading', value: 'Import from MikroTik' },
      { type: 'steps', value: [
        'If you imported plans in the previous step, your customers were already imported',
        'NetLedger reads PPPoE secrets and matches them to the imported plans',
        'Customer names are taken from the PPPoE comment field (if set on MikroTik)',
      ]},
      { type: 'heading', value: 'Add a Customer Manually' },
      { type: 'steps', value: [
        'Go to Customers -> click "Add Customer"',
        'Fill in: Full Name, Phone, Email, Address',
        'PPPoE Username & Password (or click Generate for random password)',
        'Select Plan and Router',
        'Click Save -- PPPoE secret is created on MikroTik instantly',
      ]},
      { type: 'heading', value: 'Customer Actions' },
      { type: 'steps', value: [
        'Throttle -- reduces speed to 1Mbps, kicks session so new speed applies immediately',
        'Disconnect -- disables PPPoE secret + kicks session (customer can\'t connect)',
        'Reconnect -- re-enables PPPoE secret + restores original speed profile',
        'Change Plan -- updates MikroTik profile to new plan speeds instantly',
        'Delete -- removes customer + PPPoE secret from MikroTik (requires admin password)',
      ]},
    ],
  },
  {
    title: 'Configure Billing',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z"/>',
    content: [
      { type: 'text', value: 'Configure your billing cycle and enforcement rules in Settings -> Billing. NetLedger handles invoice generation, overdue detection, and graduated enforcement automatically.' },
      { type: 'heading', value: 'Billing Settings' },
      { type: 'steps', value: [
        'Go to Settings -> Billing',
        'Set the billing due day (e.g. 15th of each month)',
        'Configure enforcement thresholds:',
        'Days after due to throttle (default: 3) -- reduces speed to 1Mbps',
        'Days after due to disconnect (default: 5) -- disables PPPoE secret',
        'Toggle auto-generate invoices on/off',
      ]},
      { type: 'heading', value: 'How Enforcement Works' },
      { type: 'steps', value: [
        'Invoices are generated automatically on the 1st of each month',
        'Overdue invoices are detected daily',
        'Throttle is applied after the configured number of days past due',
        'Disconnect follows after more days past due',
        'When a customer pays, they are auto-reconnected at original speed -- no manual action needed',
      ]},
      { type: 'alert', value: 'Make sure to set your enforcement thresholds before going live. The defaults (3 days throttle, 5 days disconnect) work well for most ISPs.' },
    ],
  },
  {
    title: 'Set Up Notifications',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"/>',
    content: [
      { type: 'text', value: 'Set up email and SMS notifications to keep your subscribers informed about invoices, due dates, and account status.' },
      { type: 'heading', value: 'Email (SMTP)' },
      { type: 'steps', value: [
        'Go to Settings -> SMTP',
        'Configure your mail server (Gmail: smtp.gmail.com, port 587, use App Password)',
        'Use "Send Test" to verify it works before going live',
      ]},
      { type: 'heading', value: 'SMS (Semaphore)' },
      { type: 'steps', value: [
        'Go to Settings -> SMS',
        'Enter your Semaphore API key and sender name',
        'Use "Send Test" to verify',
      ]},
      { type: 'heading', value: 'Notification Templates' },
      { type: 'text', value: 'Customize message templates in Settings -> Notifications. Available placeholders:' },
      { type: 'steps', value: [
        '{customer_name} -- subscriber\'s full name',
        '{amount} -- invoice amount',
        '{due_date} -- payment due date',
        '{portal_url} -- link to the customer self-service portal',
      ]},
      { type: 'text', value: 'Notifications are sent automatically when invoices are generated and when due dates approach.' },
    ],
  },
  {
    title: 'Branding & Customer Portal',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M9.53 16.122a3 3 0 00-5.78 1.128 2.25 2.25 0 01-2.4 2.245 4.5 4.5 0 008.4-2.245c0-.399-.078-.78-.22-1.128zm0 0a15.998 15.998 0 003.388-1.62m-5.043-.025a15.994 15.994 0 011.622-3.395m3.42 3.42a15.995 15.995 0 004.764-4.648l3.876-5.814a1.151 1.151 0 00-1.597-1.597L14.146 6.32a15.996 15.996 0 00-4.649 4.763m3.42 3.42a6.776 6.776 0 00-3.42-3.42"/>',
    content: [
      { type: 'text', value: 'Set up your company branding for invoices and the customer self-service portal.' },
      { type: 'heading', value: 'Company Branding' },
      { type: 'steps', value: [
        'Go to Settings -> Branding',
        'Enter Company Name, Address, Phone, Email',
        'Upload your logo (appears on invoices and customer portal)',
        'Set your portal slug -- this becomes your customer portal URL',
      ]},
      { type: 'heading', value: 'Customer Portal' },
      { type: 'text', value: 'Your subscribers can view invoices, check usage, and submit support tickets through the self-service portal. Share the portal URL with your customers.' },
    ],
  },
  {
    title: 'Hotspot & Vouchers',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.047 8.287 8.287 0 009 9.601a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 18a3.75 3.75 0 00.495-7.468 5.99 5.99 0 00-1.925 3.547 5.975 5.975 0 01-2.133-1.001A3.75 3.75 0 0012 18z"/>',
    content: [
      { type: 'text', value: 'Optional. Hotspot is for prepaid WiFi access -- generate voucher codes, sell them to customers, and they log in through the MikroTik captive portal.' },
      { type: 'heading', value: 'Set Up Hotspot Profiles' },
      { type: 'steps', value: [
        'Go to Hotspot -> Users & Sessions -> Profiles tab',
        'Select your router from the dropdown',
        'Click "Add Profile" to create speed/time packages (e.g. "1hr-5M")',
        'Profiles are created directly on your MikroTik',
      ]},
      { type: 'heading', value: 'Generate Vouchers' },
      { type: 'steps', value: [
        'Go to Hotspot -> Vouchers',
        'Click "Generate Batch" -- select router, profile, quantity, and duration',
        'Generated codes can be copied individually or all at once',
        'Customer enters voucher code as both username and password on the captive portal',
      ]},
      { type: 'alert', value: 'Hotspot requires a hotspot server configured on your MikroTik (IP -> Hotspot -> Setup). NetLedger handles profiles and vouchers; the captive portal page is managed on the router.' },
    ],
  },
  {
    title: 'LibreQoS Integration',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/>',
    content: [
      { type: 'text', value: 'Optional. If you run LibreQoS for traffic shaping, NetLedger can automatically sync subscriber speeds to your LibreQoS instance.' },
      { type: 'heading', value: 'Setup' },
      { type: 'steps', value: [
        'In NetLedger, go to Settings -> LibreQoS',
        'Generate an API token for LibreQoS to pull subscriber data',
        'On your LibreQoS server, configure the API endpoint to point to your NetLedger instance',
        'Set up a cron job on the LibreQoS server to periodically pull updated subscriber speeds',
      ]},
      { type: 'heading', value: 'How It Works' },
      { type: 'steps', value: [
        'NetLedger exposes a read-only API with subscriber IPs and plan speeds',
        'LibreQoS pulls this data and applies traffic shaping rules',
        'When you change a customer\'s plan in NetLedger, LibreQoS picks up the new speed on the next sync',
      ]},
    ],
  },
]
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Setup Guide</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Follow these steps to get your ISP billing system running</p>
    </div>

    <!-- Note -->
    <div class="flex items-start gap-3 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 p-4">
      <svg class="w-5 h-5 text-blue-500 shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clip-rule="evenodd"/></svg>
      <p class="text-sm text-blue-800 dark:text-blue-300">This guide applies to both SaaS and self-hosted installations.</p>
    </div>

    <!-- Progress bar -->
    <div class="flex items-center gap-1">
      <button
        v-for="(step, i) in steps"
        :key="i"
        @click="activeStep = i"
        :class="[
          'flex-1 h-2 rounded-full transition-colors',
          i <= activeStep ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'
        ]"
      />
    </div>

    <!-- Step navigation -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
      <button
        v-for="(step, i) in steps"
        :key="i"
        @click="activeStep = i"
        :class="[
          'flex flex-col items-center gap-2 p-3 rounded-xl border text-center transition-all',
          i === activeStep
            ? 'border-primary bg-primary/5 shadow-sm'
            : 'border-gray-100 dark:border-gray-700 hover:border-gray-200 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'
        ]"
      >
        <div :class="[
          'w-8 h-8 rounded-lg flex items-center justify-center',
          i === activeStep ? 'bg-primary/10' : 'bg-gray-100 dark:bg-gray-700'
        ]">
          <svg :class="['w-4 h-4', i === activeStep ? 'text-primary' : 'text-gray-500 dark:text-gray-400']" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" v-html="step.icon" />
        </div>
        <span :class="['text-xs font-medium leading-tight', i === activeStep ? 'text-primary' : 'text-gray-600 dark:text-gray-400']">
          {{ step.title }}
        </span>
      </button>
    </div>

    <!-- Step content -->
    <div class="rounded-xl bg-white dark:bg-gray-800 shadow-sm border border-gray-100 dark:border-gray-700 p-6 lg:p-8">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
          <svg class="w-5 h-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" v-html="steps[activeStep].icon" />
        </div>
        <div>
          <p class="text-xs font-medium text-primary uppercase tracking-wider">Step {{ activeStep + 1 }} of {{ steps.length }}</p>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ steps[activeStep].title }}</h2>
        </div>
      </div>

      <div class="space-y-5">
        <template v-for="(block, bi) in steps[activeStep].content" :key="bi">
          <p v-if="block.type === 'text'" class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{{ block.value }}</p>

          <h3 v-if="block.type === 'heading'" class="text-sm font-semibold text-gray-800 dark:text-gray-200 pt-2">{{ block.value }}</h3>

          <ol v-if="block.type === 'steps'" class="space-y-2 pl-1">
            <li v-for="(s, si) in (block.value as string[])" :key="si" class="flex items-start gap-3">
              <span class="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 text-xs font-semibold flex items-center justify-center shrink-0 mt-0.5">{{ si + 1 }}</span>
              <span class="text-sm text-gray-600 dark:text-gray-400">{{ s }}</span>
            </li>
          </ol>

          <div v-if="block.type === 'code'" class="rounded-lg bg-gray-900 p-4 overflow-x-auto">
            <code class="text-sm font-mono text-green-400">{{ block.value }}</code>
          </div>

          <div v-if="block.type === 'alert'" class="flex items-start gap-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 p-4">
            <svg class="w-5 h-5 text-amber-500 shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg>
            <p class="text-sm text-amber-800 dark:text-amber-300">{{ block.value }}</p>
          </div>
        </template>
      </div>

      <!-- Navigation -->
      <div class="flex items-center justify-between mt-8 pt-6 border-t border-gray-100 dark:border-gray-700">
        <button
          v-if="activeStep > 0"
          @click="activeStep--"
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
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
