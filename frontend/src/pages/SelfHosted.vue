<script setup lang="ts">
function copyLinuxCmd() {
  window.navigator.clipboard.writeText('curl -fsSL https://netl.2max.tech/install.sh | sudo bash')
}

function copyWinCommands() {
  const cmds = [
    'mkdir C:\\NetLedger; cd C:\\NetLedger',
    'Invoke-WebRequest -Uri "https://netl.2max.tech/docker-compose.yml" -OutFile "docker-compose.yml"',
    'Invoke-WebRequest -Uri "https://netl.2max.tech/env.example" -OutFile ".env"',
    'docker compose pull',
    'docker compose up -d',
    'docker compose exec backend alembic upgrade head',
  ].join('\n')
  window.navigator.clipboard.writeText(cmds)
}
</script>

<template>
  <div class="min-h-screen bg-white">
    <!-- Navbar -->
    <nav class="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-gray-100 z-50">
      <div class="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
        <router-link to="/" class="flex items-center gap-3">
          <img src="/logo-2.png" class="w-9 h-9" />
          <div>
            <span class="text-xl font-bold text-gray-900 block leading-tight">NetLedger</span>
            <span class="text-[10px] text-gray-400 font-medium">by 2max.tech</span>
          </div>
        </router-link>
        <div class="flex items-center gap-3">
          <router-link to="/login" class="px-5 py-2 text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-lg transition-colors">
            Login
          </router-link>
        </div>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto px-6 pt-28 pb-20">
      <div class="text-center mb-12">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium mb-4">
          Self-Hosted Installation
        </div>
        <h1 class="text-4xl font-bold text-gray-900">Install NetLedger on Your Server</h1>
        <p class="text-lg text-gray-500 mt-3">Run NetLedger on your own hardware — full control, no cloud dependency</p>
      </div>

      <!-- Requirements -->
      <section class="mb-12">
        <h2 class="text-xl font-bold text-gray-900 mb-4">Requirements</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="rounded-xl border border-gray-100 p-5">
            <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center mb-3">
              <svg class="w-5 h-5 text-blue-600" viewBox="0 0 20 20" fill="currentColor"><path d="M4.632 3.533A2 2 0 016.577 2h6.846a2 2 0 011.945 1.533l1.976 8.234A3.489 3.489 0 0016 11.5H4c-.476 0-.93.095-1.344.267l1.976-8.234z"/><path fill-rule="evenodd" d="M4 13a2 2 0 100 4h12a2 2 0 100-4H4z" clip-rule="evenodd"/></svg>
            </div>
            <h3 class="font-semibold text-gray-900 text-sm">Hardware</h3>
            <ul class="mt-2 text-sm text-gray-500 space-y-1">
              <li>2 GB RAM minimum</li>
              <li>20 GB disk space</li>
              <li>Any x64 or ARM64 CPU</li>
            </ul>
          </div>
          <div class="rounded-xl border border-gray-100 p-5">
            <div class="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center mb-3">
              <svg class="w-5 h-5 text-green-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3.25 4A2.25 2.25 0 001 6.25v7.5A2.25 2.25 0 003.25 16h7.5A2.25 2.25 0 0013 13.75v-7.5A2.25 2.25 0 0010.75 4h-7.5zM15 9.25a.75.75 0 000 1.5h4.25a.75.75 0 000-1.5H15z" clip-rule="evenodd"/></svg>
            </div>
            <h3 class="font-semibold text-gray-900 text-sm">Operating System</h3>
            <ul class="mt-2 text-sm text-gray-500 space-y-1">
              <li>Debian 12 (recommended)</li>
              <li>Ubuntu 22.04 / 24.04</li>
              <li>Any Linux with Docker</li>
            </ul>
          </div>
          <div class="rounded-xl border border-gray-100 p-5">
            <div class="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center mb-3">
              <svg class="w-5 h-5 text-orange-600" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M.676 6.941A12.964 12.964 0 0110 4c3.456 0 6.626 1.35 8.964 3.555a.75.75 0 01-1.028 1.09A11.466 11.466 0 0010 5.5a11.466 11.466 0 00-7.936 3.145.75.75 0 11-1.028-1.09l.64.286z" clip-rule="evenodd"/></svg>
            </div>
            <h3 class="font-semibold text-gray-900 text-sm">Network</h3>
            <ul class="mt-2 text-sm text-gray-500 space-y-1">
              <li>Same LAN as MikroTik</li>
              <li>No port forwarding needed</li>
              <li>Port 80 available on server</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Quick Install -->
      <section class="mb-12">
        <h2 class="text-xl font-bold text-gray-900 mb-4">Quick Install (Linux)</h2>
        <p class="text-sm text-gray-500 mb-4">Run this single command on a fresh Debian/Ubuntu server:</p>
        <div class="relative rounded-xl bg-gray-900 p-5 overflow-x-auto">
          <code class="text-green-400 text-sm font-mono">curl -fsSL https://netl.2max.tech/install.sh | sudo bash</code>
          <button
            @click="copyLinuxCmd"
            class="absolute top-3 right-3 px-2.5 py-1 text-xs text-gray-400 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            Copy
          </button>
        </div>
        <p class="text-xs text-gray-400 mt-2">This installs Docker (if needed), downloads NetLedger, and starts all services. Takes about 2 minutes.</p>
      </section>

      <!-- What it does -->
      <section class="mb-12">
        <h2 class="text-xl font-bold text-gray-900 mb-4">What the installer does</h2>
        <div class="rounded-xl border border-gray-100 divide-y divide-gray-100">
          <div v-for="(step, i) in installSteps" :key="i" class="flex items-start gap-4 p-4">
            <span class="w-7 h-7 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">{{ i + 1 }}</span>
            <div>
              <p class="text-sm font-medium text-gray-900">{{ step.title }}</p>
              <p class="text-sm text-gray-500 mt-0.5">{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Manual Install -->
      <section class="mb-12">
        <h2 class="text-xl font-bold text-gray-900 mb-4">Manual Install (Docker Compose)</h2>
        <p class="text-sm text-gray-500 mb-4">If you prefer to set things up manually:</p>

        <div class="space-y-4">
          <div>
            <h3 class="text-sm font-semibold text-gray-800 mb-2">1. Create a directory and docker-compose.yml</h3>
            <div class="rounded-xl bg-gray-900 p-4 overflow-x-auto">
              <pre class="text-sm text-gray-300 font-mono">mkdir -p /opt/netledger && cd /opt/netledger</pre>
            </div>
          </div>

          <div>
            <h3 class="text-sm font-semibold text-gray-800 mb-2">2. Create .env file</h3>
            <div class="rounded-xl bg-gray-900 p-4 overflow-x-auto">
              <pre class="text-sm text-gray-300 font-mono whitespace-pre">POSTGRES_USER=netledger
POSTGRES_PASSWORD=<span class="text-green-400">your-secure-password</span>
POSTGRES_DB=netledger
DATABASE_URL=postgresql+asyncpg://netledger:<span class="text-green-400">your-secure-password</span>@db:5432/netledger
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<span class="text-green-400">generate-a-random-64-char-string</span></pre>
            </div>
          </div>

          <div>
            <h3 class="text-sm font-semibold text-gray-800 mb-2">3. Start NetLedger</h3>
            <div class="rounded-xl bg-gray-900 p-4 overflow-x-auto">
              <pre class="text-sm text-gray-300 font-mono whitespace-pre">docker compose pull
docker compose up -d
docker compose exec backend alembic upgrade head</pre>
            </div>
          </div>

          <div>
            <h3 class="text-sm font-semibold text-gray-800 mb-2">4. Open in browser</h3>
            <p class="text-sm text-gray-500">Navigate to <code class="text-primary bg-primary/5 px-1.5 py-0.5 rounded">http://your-server-ip</code> and login with <code class="text-primary bg-primary/5 px-1.5 py-0.5 rounded">admin / admin123</code></p>
          </div>
        </div>
      </section>

      <!-- Windows -->
      <section class="mb-12">
        <h2 class="text-xl font-bold text-gray-900 mb-4">Windows Installation</h2>
        <div class="rounded-xl border border-gray-100 p-6">
          <div class="space-y-4">
            <div>
              <h3 class="text-sm font-semibold text-gray-800 mb-2">1. Install Docker Desktop</h3>
              <p class="text-sm text-gray-500">Download and install <a href="https://www.docker.com/products/docker-desktop/" target="_blank" class="text-primary hover:underline">Docker Desktop for Windows</a>. Requires Windows 10/11 with WSL2 enabled.</p>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-gray-800 mb-2">2. Open PowerShell as Administrator and run:</h3>
              <div class="rounded-xl bg-gray-900 p-4 overflow-x-auto">
                <pre class="text-sm text-gray-300 font-mono whitespace-pre">mkdir C:\NetLedger; cd C:\NetLedger
Invoke-WebRequest -Uri "https://netl.2max.tech/docker-compose.yml" -OutFile "docker-compose.yml"
Invoke-WebRequest -Uri "https://netl.2max.tech/env.example" -OutFile ".env"
docker compose pull
docker compose up -d
docker compose exec backend alembic upgrade head</pre>
              </div>
              <button
                @click="copyWinCommands"
                class="mt-2 px-3 py-1.5 text-xs text-gray-500 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Copy Commands
              </button>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-gray-800 mb-2">3. Open browser</h3>
              <p class="text-sm text-gray-500">Go to <code class="text-primary bg-primary/5 px-1.5 py-0.5 rounded">http://localhost</code> and login with <code class="text-primary bg-primary/5 px-1.5 py-0.5 rounded">admin / admin123</code></p>
            </div>
          </div>
        </div>
      </section>

      <!-- After Install -->
      <section class="mb-12">
        <h2 class="text-xl font-bold text-gray-900 mb-4">After Installation</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="rounded-xl border border-gray-100 p-5">
            <h3 class="font-semibold text-gray-900 text-sm mb-2">First Steps</h3>
            <ol class="text-sm text-gray-500 space-y-1.5 list-decimal list-inside">
              <li>Change default admin password</li>
              <li>Go to Setup Guide in the sidebar</li>
              <li>Add your MikroTik router (local IP works!)</li>
              <li>Create service plans</li>
              <li>Add customers</li>
            </ol>
          </div>
          <div class="rounded-xl border border-gray-100 p-5">
            <h3 class="font-semibold text-gray-900 text-sm mb-2">Useful Commands</h3>
            <div class="text-sm text-gray-500 space-y-1.5 font-mono">
              <p><span class="text-gray-400">#</span> View logs</p>
              <p class="text-primary">docker compose logs -f</p>
              <p><span class="text-gray-400">#</span> Stop</p>
              <p class="text-primary">docker compose down</p>
              <p><span class="text-gray-400">#</span> Update</p>
              <p class="text-primary">docker compose pull && docker compose up -d</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Support -->
      <section class="rounded-xl bg-gradient-to-br from-sidebar to-gray-900 p-8 text-center">
        <h2 class="text-xl font-bold text-white mb-2">Need Help?</h2>
        <p class="text-gray-400 text-sm mb-4">Contact 2max Tech support for installation assistance</p>
        <a href="mailto:support@2max.tech" class="inline-flex items-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-primary hover:bg-primary-hover rounded-xl transition-colors">
          support@2max.tech
        </a>
      </section>
    </div>

    <!-- Footer -->
    <footer class="py-8 px-6 border-t border-gray-100">
      <div class="max-w-4xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-2">
          <img src="/logo-2.png" class="w-5 h-5" />
          <span class="text-sm text-gray-500">NetLedger by 2max Tech</span>
        </div>
        <p class="text-sm text-gray-400">&copy; {{ new Date().getFullYear() }} 2max Tech</p>
      </div>
    </footer>
  </div>
</template>

<script lang="ts">
const installSteps = [
  { title: 'Installs Docker', desc: 'Automatically installs Docker Engine and Docker Compose if not already present' },
  { title: 'Creates configuration', desc: 'Generates secure random passwords for the database and secret key' },
  { title: 'Downloads NetLedger', desc: 'Pulls the latest NetLedger Docker images (backend, frontend, database, Redis)' },
  { title: 'Starts all services', desc: 'Launches 6 containers: PostgreSQL, Redis, Backend API, Frontend, Celery Worker, Celery Beat' },
  { title: 'Sets up database', desc: 'Runs database migrations to create all tables' },
  { title: 'Creates admin account', desc: 'Creates the default admin user (admin / admin123) — change this after first login!' },
]
</script>
