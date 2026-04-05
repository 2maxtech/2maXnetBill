#!/bin/bash
echo "========================================"
echo "  MULTI-TENANT ISOLATION TEST"
echo "========================================"

# Register ISP #2
echo ""
echo "=== Register ISP #2: SpeedNet ==="
curl -s -X POST http://localhost/api/v1/auth/register -H "Content-Type: application/json" \
  -d '{"company_name":"SpeedNet Corp","full_name":"Ana Reyes","email":"ana@speednet.ph","phone":"0917222","username":"ana_admin","password":"SpeedNet123"}'
echo ""

# Login both ISPs
T1=$(curl -s -X POST http://localhost/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"carlo","password":"FiberPH123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
T2=$(curl -s -X POST http://localhost/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"ana_admin","password":"SpeedNet123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Both ISPs logged in"

# ISP1 creates data
echo ""
echo "=== FiberPH creates plan + customer ==="
curl -s -X POST http://localhost/api/v1/plans/ -H "Authorization: Bearer $T1" -H "Content-Type: application/json" \
  -d '{"name":"FiberPH 20Mbps","download_mbps":20,"upload_mbps":10,"monthly_price":899}' > /dev/null
curl -s -X POST http://localhost/api/v1/customers/ -H "Authorization: Bearer $T1" -H "Content-Type: application/json" \
  -d '{"full_name":"Juan FiberPH","email":"juan@fiberph.net","phone":"123","address":"Manila","pppoe_username":"fph.juan","pppoe_password":"Pass1234","plan_id":"'$(curl -s http://localhost/api/v1/plans/ -H "Authorization: Bearer $T1" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")'"}'  > /dev/null
echo "  Done"

# ISP2 creates data
echo ""
echo "=== SpeedNet creates plan + customer ==="
curl -s -X POST http://localhost/api/v1/plans/ -H "Authorization: Bearer $T2" -H "Content-Type: application/json" \
  -d '{"name":"SpeedNet 50Mbps","download_mbps":50,"upload_mbps":25,"monthly_price":1499}' > /dev/null
curl -s -X POST http://localhost/api/v1/customers/ -H "Authorization: Bearer $T2" -H "Content-Type: application/json" \
  -d '{"full_name":"Pedro SpeedNet","email":"pedro@speednet.ph","phone":"456","address":"Cebu","pppoe_username":"sn.pedro","pppoe_password":"Pass5678","plan_id":"'$(curl -s http://localhost/api/v1/plans/ -H "Authorization: Bearer $T2" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")'"}'  > /dev/null
echo "  Done"

echo ""
echo "========================================"
echo "  ISOLATION CHECK"
echo "========================================"

echo ""
echo "=== FiberPH sees: ==="
C1=$(curl -s "http://localhost/api/v1/customers/?page_size=10" -H "Authorization: Bearer $T1")
echo "  Customers: $(echo $C1 | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")"
echo "$C1" | python3 -c "import sys,json; [print('    - '+c['full_name']) for c in json.load(sys.stdin)['items']]"
echo "  Plans: $(curl -s http://localhost/api/v1/plans/ -H "Authorization: Bearer $T1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d)); [print('    - '+p['name']) for p in d]")"

echo ""
echo "=== SpeedNet sees: ==="
C2=$(curl -s "http://localhost/api/v1/customers/?page_size=10" -H "Authorization: Bearer $T2")
echo "  Customers: $(echo $C2 | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")"
echo "$C2" | python3 -c "import sys,json; [print('    - '+c['full_name']) for c in json.load(sys.stdin)['items']]"
echo "  Plans: $(curl -s http://localhost/api/v1/plans/ -H "Authorization: Bearer $T2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d)); [print('    - '+p['name']) for p in d]")"

echo ""
echo "=== Super Admin ==="
SA=$(curl -s -X POST http://localhost/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "  Organizations:"
curl -s http://localhost/api/v1/system/organizations/ -H "Authorization: Bearer $SA" | python3 -c "
import sys,json
for o in json.load(sys.stdin):
    print('    %s (%s) id=%s' % (o.get('company_name',''), o['username'], o['id'][:8]))
"

# Impersonate FiberPH
CARLO_ID=$(curl -s http://localhost/api/v1/system/organizations/ -H "Authorization: Bearer $SA" | python3 -c "import sys,json; [print(o['id']) for o in json.load(sys.stdin) if o['username']=='carlo']" | head -1)
echo ""
echo "=== Super Admin impersonates FiberPH: ==="
echo "  Customers:"
curl -s "http://localhost/api/v1/customers/?page_size=10" -H "Authorization: Bearer $SA" -H "X-Tenant-Id: $CARLO_ID" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('    total=%d' % d['total'])
for c in d['items']: print('    - %s' % c['full_name'])
"

# Impersonate SpeedNet
ANA_ID=$(curl -s http://localhost/api/v1/system/organizations/ -H "Authorization: Bearer $SA" | python3 -c "import sys,json; [print(o['id']) for o in json.load(sys.stdin) if o['username']=='ana_admin']" | head -1)
echo ""
echo "=== Super Admin impersonates SpeedNet: ==="
echo "  Customers:"
curl -s "http://localhost/api/v1/customers/?page_size=10" -H "Authorization: Bearer $SA" -H "X-Tenant-Id: $ANA_ID" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('    total=%d' % d['total'])
for c in d['items']: print('    - %s' % c['full_name'])
"

echo ""
echo "=== ISOLATION TEST COMPLETE ==="
