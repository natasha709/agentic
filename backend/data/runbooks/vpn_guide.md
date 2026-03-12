# VPN Setup & Troubleshooting Guide

## Quick Status Check
```
ipconfig /all
ping vpn.company.com
nslookup vpn.company.com
```

## Common Issues & Solutions

### 1. **Authentication Failed**
```
Symptoms: "Invalid credentials" or 401 error
Solutions:
- Verify username/password
- Check if MFA is required
- Reset password if locked
- Try alternate credentials
```

### 2. **Connection Timeout**
```
Symptoms: Hangs on "Connecting..." 
Solutions:
- Test internet connectivity first
- Try different VPN server/region
- Disable firewall temporarily
- Check MTU settings (set to 1400)
```

### 3. **DNS Resolution Failure**
```
Symptoms: Can't resolve VPN server hostname
Solutions:
- Flush DNS: `ipconfig /flushdns`
- Try IP address directly
- Check corporate DNS servers
- Use 8.8.8.8 temporarily
```

### 4. **Split Tunnel Issues**
```
Symptoms: Internet works but internal sites don't
Solutions:
- Verify VPN client split tunnel config
- Check route table: `route print`
- Add manual routes if needed
```

## Verification Commands
```
# After successful connection
ipconfig /all | findstr "VPN"
route print
nslookup internal.company.com
```

## Escalation Criteria
- Multiple users affected → Network team
- Hardware VPN appliance → Vendor support
- Certificate errors → PKI team
