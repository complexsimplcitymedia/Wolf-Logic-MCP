# NFS Server Setup - Client Dumps Directory

## Add NFS Export (Run on 181 - csmcloud-server)

```bash
# Add to /etc/exports (requires sudo):
sudo bash -c 'cat >> /etc/exports << EOF
/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps 100.110.0.0/16(rw,sync,no_subtree_check,no_root_squash) 100.250.0.0/16(rw,sync,no_subtree_check,no_root_squash)
EOF'

# Apply export
sudo exportfs -ra

# Restart NFS server
sudo systemctl restart nfs-kernel-server

# Verify export
sudo exportfs -v | grep client-dumps
```

## Network Ranges
- **100.110.0.0/16** - Main Tailscale mesh (includes 181, 245)
- **100.250.0.0/16** - Extended network range

Both ranges have full read/write access to `data/client-dumps/`.
