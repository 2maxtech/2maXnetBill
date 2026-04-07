<script setup lang="ts">
import { ref } from 'vue'

const installCmd = 'curl -fsSL https://raw.githubusercontent.com/2maxtech/NetLedger/main/scripts/install-onpremise.sh | sudo bash'
const updateCmd = 'cd /opt/netledger && git pull && docker compose -f docker-compose.onpremise.yml up -d --build'

const copiedInstall = ref(false)
const copiedUpdate = ref(false)

function copyInstall() {
  navigator.clipboard.writeText(installCmd)
  copiedInstall.value = true
  setTimeout(() => (copiedInstall.value = false), 2000)
}

function copyUpdate() {
  navigator.clipboard.writeText(updateCmd)
  copiedUpdate.value = true
  setTimeout(() => (copiedUpdate.value = false), 2000)
}
</script>

<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <!-- Navbar -->
    <nav class="fixed top-0 w-full bg-gray-950/80 backdrop-blur-md border-b border-gray-800 z-50">
      <div class="max-w-5xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-2 sm:gap-3">
          <img src="/logo-2.png" class="w-7 h-7 sm:w-9 sm:h-9" alt="NetLedger" />
          <div class="flex flex-col -space-y-1">
            <span class="text-base sm:text-xl font-bold text-white">NetLedger</span>
            <span class="text-[9px] sm:text-[10px] text-gray-500 font-medium">by 2max.tech</span>
          </div>
        </router-link>
        <div class="flex items-center gap-2 sm:gap-3">
          <router-link to="/" class="px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium text-gray-400 hover:text-white transition-colors">
            Back to Home
          </router-link>
          <router-link to="/login" class="px-3 sm:px-5 py-1.5 sm:py-2 text-xs sm:text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-lg transition-colors">
            Login
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="pt-28 sm:pt-36 pb-12 sm:pb-16 px-4 sm:px-6">
      <div class="max-w-5xl mx-auto text-center">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium mb-6">
          <span class="w-1.5 h-1.5 rounded-full bg-primary" />
          Self-Hosted
        </div>
        <h1 class="text-3xl sm:text-5xl font-bold text-white leading-tight">
          Self-Hosted <span class="text-primary">NetLedger</span>
        </h1>
        <p class="text-base sm:text-lg text-gray-400 mt-4 max-w-2xl mx-auto leading-relaxed">
          Run your ISP billing on your own server. Full control, your data stays on your network, no cloud dependency.
        </p>
      </div>
    </section>

    <!-- System Requirements -->
    <section class="py-10 sm:py-14 px-4 sm:px-6">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-xl sm:text-2xl font-bold text-white mb-6">System Requirements</h2>
        <div class="rounded-xl border border-gray-800 overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-900">
                <th class="text-left px-5 py-3 text-gray-400 font-medium"></th>
                <th class="text-left px-5 py-3 text-gray-400 font-medium">Minimum</th>
                <th class="text-left px-5 py-3 text-gray-400 font-medium">Recommended</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-800">
              <tr class="hover:bg-gray-900/50 transition-colors">
                <td class="px-5 py-3 font-medium text-gray-300">CPU</td>
                <td class="px-5 py-3 text-gray-400">2 cores</td>
                <td class="px-5 py-3 text-primary font-medium">4 cores</td>
              </tr>
              <tr class="hover:bg-gray-900/50 transition-colors">
                <td class="px-5 py-3 font-medium text-gray-300">RAM</td>
                <td class="px-5 py-3 text-gray-400">2 GB</td>
                <td class="px-5 py-3 text-primary font-medium">4 GB</td>
              </tr>
              <tr class="hover:bg-gray-900/50 transition-colors">
                <td class="px-5 py-3 font-medium text-gray-300">Storage</td>
                <td class="px-5 py-3 text-gray-400">20 GB</td>
                <td class="px-5 py-3 text-primary font-medium">40 GB</td>
              </tr>
              <tr class="hover:bg-gray-900/50 transition-colors">
                <td class="px-5 py-3 font-medium text-gray-300">OS</td>
                <td class="px-5 py-3 text-gray-400">Ubuntu 22.04+ / Debian 12+</td>
                <td class="px-5 py-3 text-primary font-medium">Ubuntu 24.04</td>
              </tr>
              <tr class="hover:bg-gray-900/50 transition-colors">
                <td class="px-5 py-3 font-medium text-gray-300">Network</td>
                <td class="px-5 py-3 text-gray-400">LAN access to MikroTik router</td>
                <td class="px-5 py-3 text-gray-500">--</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Installation -->
    <section class="py-10 sm:py-14 px-4 sm:px-6">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-xl sm:text-2xl font-bold text-white mb-2">Installation</h2>
        <p class="text-sm text-gray-400 mb-6">Run this single command on a fresh Debian/Ubuntu server:</p>

        <div class="relative rounded-xl bg-gray-900 border border-gray-800 p-5 overflow-x-auto group">
          <code class="text-primary text-sm font-mono break-all">{{ installCmd }}</code>
          <button
            @click="copyInstall"
            class="absolute top-3 right-3 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
            :class="copiedInstall ? 'text-green-400 bg-green-900/30' : 'text-gray-400 bg-gray-800 hover:bg-gray-700'"
          >
            {{ copiedInstall ? 'Copied!' : 'Copy' }}
          </button>
        </div>
        <p class="text-xs text-gray-500 mt-3">
          The installer checks system requirements, installs Docker (if needed), downloads NetLedger, generates secure credentials, and starts all services. Takes about 2 minutes.
        </p>
      </div>
    </section>

    <!-- Quick Start -->
    <section class="py-10 sm:py-14 px-4 sm:px-6">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-xl sm:text-2xl font-bold text-white mb-6">Quick Start</h2>
        <p class="text-sm text-gray-400 mb-8">After the installer finishes, follow these steps to get your ISP billing up and running:</p>

        <div class="space-y-4">
          <div v-for="(step, i) in quickStartSteps" :key="i"
            class="flex items-start gap-4 rounded-xl bg-gray-900 border border-gray-800 p-5 hover:border-gray-700 transition-colors">
            <span class="w-8 h-8 rounded-lg bg-primary/10 text-primary text-sm font-bold flex items-center justify-center shrink-0 mt-0.5">
              {{ i + 1 }}
            </span>
            <div>
              <p class="text-sm font-medium text-white">{{ step.title }}</p>
              <p class="text-sm text-gray-400 mt-1">{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Free Tier -->
    <section class="py-10 sm:py-14 px-4 sm:px-6">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-xl sm:text-2xl font-bold text-white mb-6">What's Included — Free During Beta</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="item in freeTierItems" :key="item"
            class="flex items-start gap-3 rounded-xl bg-gray-900 border border-gray-800 p-4">
            <svg class="w-5 h-5 text-green-500 mt-0.5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
            </svg>
            <span class="text-sm text-gray-300">{{ item }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Updating -->
    <section class="py-10 sm:py-14 px-4 sm:px-6">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-xl sm:text-2xl font-bold text-white mb-2">Updating</h2>
        <p class="text-sm text-gray-400 mb-6">Pull the latest version and rebuild:</p>

        <div class="relative rounded-xl bg-gray-900 border border-gray-800 p-5 overflow-x-auto group">
          <code class="text-primary text-sm font-mono break-all">{{ updateCmd }}</code>
          <button
            @click="copyUpdate"
            class="absolute top-3 right-3 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
            :class="copiedUpdate ? 'text-green-400 bg-green-900/30' : 'text-gray-400 bg-gray-800 hover:bg-gray-700'"
          >
            {{ copiedUpdate ? 'Copied!' : 'Copy' }}
          </button>
        </div>
      </div>
    </section>

    <!-- Useful Commands -->
    <section class="py-10 sm:py-14 px-4 sm:px-6">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-xl sm:text-2xl font-bold text-white mb-6">Useful Commands</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="cmd in usefulCommands" :key="cmd.label"
            class="rounded-xl bg-gray-900 border border-gray-800 p-4">
            <p class="text-xs text-gray-500 font-medium mb-2">{{ cmd.label }}</p>
            <code class="text-sm text-primary font-mono">{{ cmd.command }}</code>
          </div>
        </div>
      </div>
    </section>

    <!-- Support CTA -->
    <section class="py-10 sm:py-14 px-4 sm:px-6">
      <div class="max-w-5xl mx-auto">
        <div class="rounded-xl bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 p-8 sm:p-10 text-center">
          <h2 class="text-xl font-bold text-white mb-2">Need Help?</h2>
          <p class="text-gray-400 text-sm mb-5">Contact 2max Tech support for installation assistance</p>
          <a href="mailto:support@2max.tech"
            class="inline-flex items-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-xl transition-colors">
            support@2max.tech
          </a>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="py-8 sm:py-10 px-4 sm:px-6 border-t border-gray-800">
      <div class="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <img src="/logo-2.png" class="w-5 h-5" alt="NetLedger" />
          <span class="text-sm text-gray-500">NetLedger by 2max Tech</span>
        </div>
        <p class="text-sm text-gray-600">&copy; {{ new Date().getFullYear() }} 2max Tech</p>
      </div>
    </footer>
  </div>
</template>

<script lang="ts">
const quickStartSteps = [
  { title: 'Open your server in a browser', desc: 'Navigate to http://your-server-ip — the setup wizard will appear on first visit.' },
  { title: 'Complete the setup wizard', desc: 'Enter your company name and create your admin account.' },
  { title: 'Add your MikroTik router', desc: 'Go to Settings > Routers and add your MikroTik router IP, username, and password.' },
  { title: 'Import customers from MikroTik', desc: 'NetLedger can import existing PPPoE subscribers directly from your router.' },
  { title: 'Set up plans and pricing', desc: 'Create bandwidth plans with monthly pricing that map to MikroTik PPPoE profiles.' },
  { title: 'Configure billing', desc: 'Go to Settings > Billing to set your billing cycle, grace period, and enforcement rules.' },
  { title: 'Optional: Set up SMTP for email notifications', desc: 'Configure email settings in Settings > Notifications to send invoices and payment reminders.' },
]

const freeTierItems = [
  'Unlimited subscribers',
  'Unlimited routers',
  'Billing & invoicing',
  'Customer portal',
  'Throttle/disconnect enforcement',
  'Hotspot & vouchers',
  'Email & SMS notifications',
]

const usefulCommands = [
  { label: 'View logs', command: 'cd /opt/netledger && docker compose -f docker-compose.onpremise.yml logs -f' },
  { label: 'Stop services', command: 'cd /opt/netledger && docker compose -f docker-compose.onpremise.yml down' },
  { label: 'Restart services', command: 'cd /opt/netledger && docker compose -f docker-compose.onpremise.yml restart' },
  { label: 'Check status', command: 'cd /opt/netledger && docker compose -f docker-compose.onpremise.yml ps' },
]
</script>
