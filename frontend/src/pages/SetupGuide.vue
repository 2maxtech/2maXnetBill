<script setup lang="ts">
import { ref } from 'vue'

const activeStep = ref(0)

const steps = [
  {
    title: 'Add Your MikroTik Router',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7"/>',
    content: [
      { type: 'text', value: 'NetLedger connects to your MikroTik router via the REST API (RouterOS v7+). You need to make the router reachable from NetLedger.' },
      { type: 'heading', value: 'Option A: MikroTik DDNS (Easiest)' },
      { type: 'steps', value: [
        'Open WinBox or WebFig on your MikroTik',
        'Go to IP → Cloud',
        'Enable "DDNS Enabled" — you\'ll get a hostname like abc123.sn.mynetname.net',
        'Make sure the REST API port (default 80) is accessible from the internet',
        'In your MikroTik firewall, add a rule to allow port 80 input only from the NetLedger platform IP (contact 2max Tech support for the IP to whitelist)',
      ]},
      { type: 'heading', value: 'Option B: Public IP + Port Forward' },
      { type: 'steps', value: [
        'If your MikroTik has a public IP, the REST API is already accessible',
        'If behind NAT, forward port 80 (or custom port) to your MikroTik\'s internal IP',
        'Add firewall rule to allow REST API port only from the NetLedger platform IP (contact 2max Tech support for the IP)',
      ]},
      { type: 'heading', value: 'Option C: WireGuard VPN (Most Secure)' },
      { type: 'steps', value: [
        'Set up WireGuard on your MikroTik (IP → WireGuard)',
        'Contact 2max Tech support to get the WireGuard peer config for your account',
        'Add the peer on your MikroTik — use the WireGuard tunnel IP as your router URL in NetLedger',
        'No ports exposed to the public internet',
      ]},
      { type: 'heading', value: 'Enable REST API on MikroTik' },
      { type: 'steps', value: [
        'Open WinBox → System → Packages → check that "rest" package is installed',
        'On RouterOS 7.x, REST API is enabled by default on port 80',
        'Test by visiting http://your-router-ip/rest/system/identity in a browser',
        'You should see JSON like {"name":"MikroTik"}',
      ]},
      { type: 'heading', value: 'Add Router in NetLedger' },
      { type: 'steps', value: [
        'Go to Routers page in NetLedger',
        'Click "Add Router"',
        'Enter: Name, URL (e.g. http://abc123.sn.mynetname.net), Username, Password',
        'Click Save — NetLedger will test the connection automatically',
        'Green "Connected" badge = success!',
      ]},
      { type: 'alert', value: 'Security Tip: Create a dedicated API user on your MikroTik with limited permissions instead of using the admin account. Go to System → Users → Add, set group to "full" or a custom group with API access.' },
    ],
  },
  {
    title: 'Set Up PPPoE Server',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M8.288 15.038a5.25 5.25 0 017.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M1.924 8.674c5.565-5.565 14.587-5.565 20.152 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 011.06 0z"/>',
    content: [
      { type: 'text', value: 'If you don\'t already have a PPPoE server on your MikroTik, set one up. If you already have one running, skip to the next step.' },
      { type: 'heading', value: 'Create IP Pool' },
      { type: 'steps', value: [
        'Open WinBox → IP → Pool',
        'Click "+" to add new pool',
        'Name: pppoe-pool',
        'Addresses: 10.10.10.2-10.10.10.254 (or your preferred range)',
        'Click OK',
      ]},
      { type: 'heading', value: 'Create PPPoE Profile' },
      { type: 'steps', value: [
        'Go to PPP → Profiles',
        'Click "+" to add new profile',
        'Name: default (or your preferred name)',
        'Local Address: 10.10.10.1',
        'Remote Address: pppoe-pool',
        'Click OK',
      ]},
      { type: 'heading', value: 'Create PPPoE Server' },
      { type: 'steps', value: [
        'Go to PPP → PPPoE Servers',
        'Click "+" to add new server',
        'Service Name: NetLedger-PPPoE',
        'Interface: select the interface connected to your customers (e.g. ether2 or a bridge)',
        'Default Profile: select the profile you created',
        'Click OK',
      ]},
      { type: 'alert', value: 'NetLedger manages PPPoE secrets and bandwidth profiles automatically. You don\'t need to create secrets manually — NetLedger does this when you add customers.' },
    ],
  },
  {
    title: 'Create Service Plans',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>',
    content: [
      { type: 'text', value: 'Plans define the bandwidth and pricing for your subscribers. When you create a plan, NetLedger automatically creates a matching MikroTik PPPoE profile with the correct rate-limit.' },
      { type: 'heading', value: 'Create a Plan' },
      { type: 'steps', value: [
        'Go to Plans page',
        'Click "Add Plan"',
        'Enter: Plan Name (e.g. "Basic 10Mbps")',
        'Download Speed (Mbps): 10',
        'Upload Speed (Mbps): 5',
        'Monthly Price: 799',
        'Optional: Data Cap (GB), FUP speeds',
        'Click Save',
      ]},
      { type: 'text', value: 'NetLedger creates a MikroTik profile named "10M-5M" with rate-limit "5M/10M". This profile is automatically assigned to customers on this plan.' },
      { type: 'heading', value: 'Import Existing Plans' },
      { type: 'steps', value: [
        'If you already have PPPoE profiles on your MikroTik with rate-limits, NetLedger can import them',
        'Go to Routers → click "Import" on your router',
        'NetLedger will create Plans from your existing profiles and Customers from existing PPPoE secrets',
        'Review imported data and set pricing manually (imported plans default to ₱0)',
      ]},
    ],
  },
  {
    title: 'Add Customers',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/>',
    content: [
      { type: 'text', value: 'When you add a customer, NetLedger automatically creates a PPPoE secret on your MikroTik router with the correct bandwidth profile. The customer can then connect using their PPPoE credentials.' },
      { type: 'heading', value: 'Add a Customer' },
      { type: 'steps', value: [
        'Go to Customers page',
        'Click "Add Customer"',
        'Fill in: Full Name, Email, Phone, Address',
        'PPPoE Username: choose a unique username (e.g. juan.delacruz)',
        'PPPoE Password: enter or click "Generate" for a random password',
        'Select Plan: choose from your created plans',
        'Select Router: choose which MikroTik to provision on',
        'Optional: Area, MAC Address',
        'Click Save',
      ]},
      { type: 'text', value: 'NetLedger will: 1) Create the PPPoE secret on MikroTik, 2) Set the bandwidth profile, 3) Enable the account. The customer can now connect!' },
      { type: 'heading', value: 'Customer Actions' },
      { type: 'steps', value: [
        'Disconnect — disables PPPoE secret + kills active session (customer can\'t connect)',
        'Reconnect — re-enables PPPoE secret + restores bandwidth profile',
        'Throttle — changes profile to 1Mbps throttle (customer stays connected but slow)',
        'Change Plan — updates bandwidth profile to new plan speeds instantly',
      ]},
    ],
  },
  {
    title: 'Generate Invoices & Collect Payments',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z"/>',
    content: [
      { type: 'text', value: 'NetLedger generates monthly invoices for all active subscribers based on their plan pricing. You can also generate invoices for individual customers.' },
      { type: 'heading', value: 'Generate Invoices' },
      { type: 'steps', value: [
        'Go to Billing → Invoices',
        'Click "Generate Invoices" to generate for ALL active customers',
        'Or click "Generate for Customer" to generate for a specific customer',
        'Invoices are created with "pending" status and the customer\'s plan price',
      ]},
      { type: 'heading', value: 'Record Payments' },
      { type: 'steps', value: [
        'Go to Billing → Payments',
        'Click "Record Payment"',
        'Select the invoice (shows customer name and amount)',
        'Enter amount paid and payment method (Cash, GCash, Maya, Bank Transfer, etc.)',
        'Optional: reference number for digital payments',
        'If fully paid, invoice status changes to "paid" automatically',
      ]},
      { type: 'heading', value: 'Overdue Enforcement' },
      { type: 'steps', value: [
        'Mark unpaid invoices as "overdue" manually or let the automated Celery task handle it',
        'Graduated enforcement: First throttle (slow speed), then disconnect (no service)',
        'When customer pays, click Reconnect to restore service immediately',
        'Invoice PDF can be downloaded or printed from the invoice actions',
      ]},
    ],
  },
  {
    title: 'Configure Company Branding',
    icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>',
    content: [
      { type: 'text', value: 'Customize your invoice PDFs with your company branding. Each ISP operator has their own branding settings.' },
      { type: 'heading', value: 'Set Up Branding' },
      { type: 'steps', value: [
        'Go to Settings → Branding tab',
        'Enter your Company Name, Address, Phone, Email',
        'Upload your Company Logo (click "Browse Logo" to select an image file)',
        'Set Invoice Number Prefix (e.g. "INV-" or "FPH-")',
        'Add Invoice Footer Text (e.g. "Thank you for choosing FiberPH!")',
        'Click Save',
      ]},
      { type: 'heading', value: 'Set Up Email Notifications' },
      { type: 'steps', value: [
        'Go to Settings → SMTP tab',
        'Enter your mail server details (host, port, username, password)',
        'For Gmail: use smtp.gmail.com, port 587, and an App Password',
        'Click "Send Test" to verify it works',
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
