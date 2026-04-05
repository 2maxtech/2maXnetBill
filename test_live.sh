#!/bin/bash
set -e

TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
AUTH="Authorization: Bearer $TOKEN"
echo "=== Logged in ==="

echo "=== Adding Router ==="
ROUTER=$(curl -s -X POST http://localhost/api/v1/routers/ -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"MikroTik-Main","url":"http://192.168.40.30","username":"admin","password":"SeafoodCity12#","is_active":true}')
ROUTER_ID=$(echo $ROUTER | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Router: $ROUTER_ID"
curl -s "http://localhost/api/v1/routers/$ROUTER_ID/status" -H "$AUTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print('  connected=%s identity=%s v%s' % (d['connected'], d.get('identity',''), d.get('version','')))"

echo "=== Creating Plans ==="
PLAN1_ID=$(curl -s -X POST http://localhost/api/v1/plans/ -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"Basic 10Mbps","download_mbps":10,"upload_mbps":5,"monthly_price":799}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
PLAN2_ID=$(curl -s -X POST http://localhost/api/v1/plans/ -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"Premium 50Mbps","download_mbps":50,"upload_mbps":25,"monthly_price":1499,"data_cap_gb":500}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
PLAN3_ID=$(curl -s -X POST http://localhost/api/v1/plans/ -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"Unlimited 100Mbps","download_mbps":100,"upload_mbps":50,"monthly_price":2499}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "  Basic=$PLAN1_ID"
echo "  Premium=$PLAN2_ID"
echo "  Unlimited=$PLAN3_ID"

echo "=== Creating Area ==="
AREA_ID=$(curl -s -X POST http://localhost/api/v1/areas/ -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"Barangay Centro","description":"Main coverage","router_id":"'$ROUTER_ID'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "  Area=$AREA_ID"

echo "=== Creating 5 Customers ==="
C1_ID=$(curl -s -X POST http://localhost/api/v1/customers/ -H "$AUTH" -H "Content-Type: application/json" -d '{"full_name":"Juan Dela Cruz","email":"juan@email.com","phone":"09171234567","address":"123 Main St","pppoe_username":"juan.delacruz","pppoe_password":"Pass1234","plan_id":"'$PLAN1_ID'","router_id":"'$ROUTER_ID'","area_id":"'$AREA_ID'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "  1. Juan (Basic) = $C1_ID"

C2_ID=$(curl -s -X POST http://localhost/api/v1/customers/ -H "$AUTH" -H "Content-Type: application/json" -d '{"full_name":"Maria Santos","email":"maria@email.com","phone":"09181234567","address":"456 Rizal Ave","pppoe_username":"maria.santos","pppoe_password":"Pass5678","plan_id":"'$PLAN2_ID'","router_id":"'$ROUTER_ID'","area_id":"'$AREA_ID'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "  2. Maria (Premium) = $C2_ID"

C3_ID=$(curl -s -X POST http://localhost/api/v1/customers/ -H "$AUTH" -H "Content-Type: application/json" -d '{"full_name":"Pedro Reyes","email":"pedro@email.com","phone":"09191234567","address":"789 Mabini St","pppoe_username":"pedro.reyes","pppoe_password":"Pass9012","plan_id":"'$PLAN3_ID'","router_id":"'$ROUTER_ID'","area_id":"'$AREA_ID'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "  3. Pedro (Unlimited) = $C3_ID"

C4_ID=$(curl -s -X POST http://localhost/api/v1/customers/ -H "$AUTH" -H "Content-Type: application/json" -d '{"full_name":"Ana Garcia","email":"ana@email.com","phone":"09201234567","address":"101 Luna St","pppoe_username":"ana.garcia","pppoe_password":"PassAna1","plan_id":"'$PLAN1_ID'","router_id":"'$ROUTER_ID'","area_id":"'$AREA_ID'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "  4. Ana (Basic) = $C4_ID"

C5_ID=$(curl -s -X POST http://localhost/api/v1/customers/ -H "$AUTH" -H "Content-Type: application/json" -d '{"full_name":"Roberto Lim","email":"roberto@email.com","phone":"09211234567","address":"202 Bonifacio St","pppoe_username":"roberto.lim","pppoe_password":"PassRob1","plan_id":"'$PLAN2_ID'","router_id":"'$ROUTER_ID'","area_id":"'$AREA_ID'"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "  5. Roberto (Premium) = $C5_ID"

echo "=== Verify PPPoE secrets on MikroTik ==="
curl -s http://192.168.40.30/rest/ppp/secret -u admin:SeafoodCity12# | python3 -c "
import sys,json
for s in json.load(sys.stdin):
    print('  %s -> profile=%s' % (s['name'], s.get('profile','default')))
"

echo "=== Generating Invoices ==="
curl -s -X POST http://localhost/api/v1/billing/invoices/generate -H "$AUTH" -H "Content-Type: application/json" -d '{}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  Generated=%s Skipped=%s' % (d['generated'], d['skipped']))"

echo "=== Invoices ==="
INVOICES=$(curl -s 'http://localhost/api/v1/billing/invoices?size=10' -H "$AUTH")
echo "$INVOICES" | python3 -c "
import sys,json
for i in json.load(sys.stdin)['items']:
    print('  %s: P%s [%s]' % (i['customer_name'], i['amount'], i['status']))
"

JUAN_INV=$(echo "$INVOICES" | python3 -c "import sys,json; [print(i['id']) for i in json.load(sys.stdin)['items'] if 'Juan' in i['customer_name']]" | head -1)
MARIA_INV=$(echo "$INVOICES" | python3 -c "import sys,json; [print(i['id']) for i in json.load(sys.stdin)['items'] if 'Maria' in i['customer_name']]" | head -1)
PEDRO_INV=$(echo "$INVOICES" | python3 -c "import sys,json; [print(i['id']) for i in json.load(sys.stdin)['items'] if 'Pedro' in i['customer_name']]" | head -1)
ANA_INV=$(echo "$INVOICES" | python3 -c "import sys,json; [print(i['id']) for i in json.load(sys.stdin)['items'] if 'Ana G' in i['customer_name']]" | head -1)

echo "=== Payments ==="
echo "  Juan pays FULL P799 via GCash"
curl -s -X POST http://localhost/api/v1/billing/payments -H "$AUTH" -H "Content-Type: application/json" -d '{"invoice_id":"'$JUAN_INV'","amount":799,"method":"gcash","reference_number":"GC-20260404-001"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('    OK: P%s' % d.get('amount','err'))"

echo "  Maria pays PARTIAL P500 of P1499 cash"
curl -s -X POST http://localhost/api/v1/billing/payments -H "$AUTH" -H "Content-Type: application/json" -d '{"invoice_id":"'$MARIA_INV'","amount":500,"method":"cash"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('    OK: P%s' % d.get('amount','err'))"

echo "  Pedro, Ana, Roberto = NO PAYMENT"

echo "=== Marking Pedro + Ana OVERDUE ==="
curl -s -X PUT "http://localhost/api/v1/billing/invoices/$PEDRO_INV" -H "$AUTH" -H "Content-Type: application/json" -d '{"status":"overdue"}' > /dev/null
curl -s -X PUT "http://localhost/api/v1/billing/invoices/$ANA_INV" -H "$AUTH" -H "Content-Type: application/json" -d '{"status":"overdue"}' > /dev/null
echo "  Done"

echo "=== Disconnecting Ana (non-payment) ==="
curl -s -X POST "http://localhost/api/v1/customers/$C4_ID/disconnect" -H "$AUTH" | python3 -c "import sys,json; print('  %s' % json.load(sys.stdin))"

echo "=== Throttling Pedro (overdue warning) ==="
curl -s -X POST "http://localhost/api/v1/customers/$C3_ID/throttle" -H "$AUTH" | python3 -c "import sys,json; print('  %s' % json.load(sys.stdin))"

echo "=== Adding 3 Expenses ==="
curl -s -X POST http://localhost/api/v1/expenses/ -H "$AUTH" -H "Content-Type: application/json" -d '{"category":"internet","description":"Fiber uplink monthly","amount":8500,"date":"2026-04-01"}' > /dev/null
curl -s -X POST http://localhost/api/v1/expenses/ -H "$AUTH" -H "Content-Type: application/json" -d '{"category":"electricity","description":"Tower site power","amount":3200,"date":"2026-04-03"}' > /dev/null
curl -s -X POST http://localhost/api/v1/expenses/ -H "$AUTH" -H "Content-Type: application/json" -d '{"category":"equipment","description":"2x CPE for installs","amount":4800,"date":"2026-04-02"}' > /dev/null
echo "  P16,500 total expenses"

echo "=== Creating Support Ticket ==="
curl -s -X POST http://localhost/api/v1/tickets/ -H "$AUTH" -H "Content-Type: application/json" -d '{"customer_id":"'$C3_ID'","subject":"Slow internet after throttle","priority":"high","message":"Speed dropped to 1Mbps, was 100Mbps before"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  %s [%s]' % (d.get('subject','err'), d.get('priority','')))"

echo "=== Generating 5 Vouchers ==="
curl -s -X POST http://localhost/api/v1/vouchers/generate -H "$AUTH" -H "Content-Type: application/json" -d '{"plan_id":"'$PLAN1_ID'","count":5,"duration_days":30}' | python3 -c "
import sys,json; d=json.load(sys.stdin)
if isinstance(d,list):
    for v in d: print('  %s' % v['code'])
else: print('  Error: %s' % d)
"

echo "=== Creating IP Pool ==="
curl -s -X POST http://localhost/api/v1/ipam/pools -H "$AUTH" -H "Content-Type: application/json" -d '{"name":"PPPoE Pool","router_id":"'$ROUTER_ID'","subnet":"192.168.50.0/24","range_start":"192.168.50.2","range_end":"192.168.50.254"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  %s: %s-%s' % (d['name'], d['range_start'], d['range_end']))"

echo ""
echo "============================================"
echo "         FINAL DASHBOARD STATE"
echo "============================================"
curl -s http://localhost/api/v1/network/dashboard -H "$AUTH" | python3 -c "
import sys,json; d=json.load(sys.stdin)
s=d['subscribers']; b=d['billing']; m=d['mikrotik']
print('SUBSCRIBERS: %d total | %d active | %d suspended | %d disconnected' % (s['total'], s['active'], s['suspended'], s['disconnected']))
print('REVENUE:     MRR=P%s | Collected=P%s | Billed=P%s' % ('{:,.0f}'.format(b['mrr']), '{:,.0f}'.format(b['collected_this_month']), '{:,.0f}'.format(b['billed_this_month'])))
print('OVERDUE:     %d invoices | P%s' % (b['overdue_count'], '{:,.0f}'.format(b['overdue_amount'])))
print('MIKROTIK:    connected=%s | sessions=%s | cpu=%s%% | interfaces=%d' % (m['connected'], m['active_sessions'], m['cpu_load'], len(m.get('interfaces',[]))))
print('PAYMENTS:    %d recent' % len(d['recent_payments']))
"
echo ""
echo "=== LIVE TEST COMPLETE - Open http://192.168.40.40 ==="
