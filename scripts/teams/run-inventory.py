#!/usr/bin/env python3
"""
Wrapper to run Teams inventory with pre-flight checks

Usage:
    python scripts/teams/run-inventory.py
    python scripts/teams/run-inventory.py --check-only
    python scripts/teams/run-inventory.py --archive-only
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

def check_prerequisites():
    """Check if required tools are installed"""
    print("Checking prerequisites...")
    
    checks = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        checks.append(("Python 3.8+", False))
    else:
        checks.append(("Python 3.8+", True))
    
    # Check Azure CLI
    result = subprocess.run(["az", "--version"], capture_output=True, text=True)
    checks.append(("Azure CLI", result.returncode == 0))
    
    # Check .env.local
    env_file = Path(".env.local")
    checks.append((".env.local exists", env_file.exists()))
    
    # Check inventory directory
    inventory_dir = Path("inventory")
    checks.append(("inventory/ directory", inventory_dir.exists()))
    
    # Check Python script
    script = Path("scripts/teams/inventory-teams-config.py")
    checks.append(("inventory script exists", script.exists()))
    
    # Print results
    all_pass = True
    for check, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
        if not passed:
            all_pass = False
    
    return all_pass

def check_env_vars():
    """Check if required env vars are set"""
    print("\nChecking environment variables in .env.local...")
    
    from dotenv import load_dotenv
    load_dotenv(".env.local")
    
    vars_to_check = [
        "GRAPH_TENANT_ID",
        "GRAPH_CLIENT_ID",
        "ENTRA_GROUP_ID",
        "AWS_WEBHOOK_ENDPOINT",
    ]
    
    all_set = True
    for var in vars_to_check:
        value = os.getenv(var, "NOT SET")
        
        if value == "NOT SET" or value.startswith("<"):
            status = "✗"
            all_set = False
        else:
            # Mask value for security
            display = value[:10] + "..." if len(value) > 10 else value
            status = "✓"
            value = display
        
        print(f"  {status} {var}: {value}")
    
    if not all_set:
        print("\n⚠️  Some env vars are not configured in .env.local")
        print("Please update them before running inventory:")
        print("  Edit .env.local and replace placeholder values")
    
    return all_set

def run_inventory():
    """Run the inventory script"""
    print("\n" + "=" * 80)
    print("Running Teams Configuration Inventory")
    print("=" * 80)
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/teams/inventory-teams-config.py"],
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running inventory: {e}")
        return False

def create_archive():
    """Create backup archive of inventory directory"""
    print("\nCreating backup archive...")
    
    try:
        import zipfile
        
        inventory_dir = Path("inventory")
        if not inventory_dir.exists():
            print("⚠️  No inventory directory to archive")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"teams-config-inventory-{timestamp}.zip"
        
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in inventory_dir.glob("**/*"):
                if f.is_file():
                    zf.write(f, arcname=f.relative_to(inventory_dir.parent))
        
        size = Path(archive_name).stat().st_size
        print(f"✓ Archive created: {archive_name} ({size:,} bytes)")
        return True
    except Exception as e:
        print(f"⚠️  Could not create archive: {e}")
        return False

def show_summary():
    """Show what was exported"""
    print("\n" + "=" * 80)
    print("Inventory Export Summary")
    print("=" * 80)
    
    inventory_dir = Path("inventory")
    if not inventory_dir.exists():
        print("No inventory directory found")
        return
    
    files = list(inventory_dir.glob("*"))
    if not files:
        print("No files exported")
        return
    
    print(f"\n📁 Exported {len(files)} files to inventory/:\n")
    
    total_size = 0
    for f in sorted(files):
        if f.is_file():
            size = f.stat().st_size
            total_size += size
            
            if f.name == "teams-config-inventory.md":
                icon = "📄"
            elif f.name.endswith(".json"):
                icon = "📋"
            elif f.name.endswith(".zip"):
                icon = "📦"
            else:
                icon = "📄"
            
            print(f"  {icon} {f.name:40s} {size:>10,d} bytes")
    
    print(f"\n  Total size: {total_size:,} bytes")
    
    print("\n📖 Main Documentation: inventory/teams-config-inventory.md")
    print("\n⚠️  Next Steps:")
    print("  1. Review: inventory/teams-config-inventory.md")
    print("  2. Manually add Teams PowerShell exports:")
    print("     - Connect-MicrosoftTeams")
    print("     - Get-CsTeamsAppSetupPolicy | ConvertTo-Json | Out-File ...")
    print("  3. Commit to git:")
    print("     git add inventory/")
    print("     git commit -m 'docs: export Teams configuration'")

def main():
    parser = argparse.ArgumentParser(
        description="Run Teams Configuration Inventory with pre-flight checks"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check prerequisites, don't run inventory"
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip prerequisite checks and run inventory directly"
    )
    parser.add_argument(
        "--archive-only",
        action="store_true",
        help="Only create archive of existing inventory"
    )
    
    args = parser.parse_args()
    
    # Archive only mode
    if args.archive_only:
        create_archive()
        return
    
    # Check only mode
    if not args.skip_checks:
        if not check_prerequisites():
            print("\n⚠️  Some prerequisites are missing")
            print("  See above for details")
            if not args.check_only:
                response = input("\nContinue anyway? (y/n) ")
                if response.lower() != 'y':
                    sys.exit(1)
        
        if not check_env_vars():
            if not args.check_only:
                response = input("\nContinue with partial configuration? (y/n) ")
                if response.lower() != 'y':
                    sys.exit(1)
    
    if args.check_only:
        print("\n✓ Prerequisite check complete")
        return
    
    # Run inventory
    if not run_inventory():
        print("\n❌ Inventory failed. Check output above for errors.")
        sys.exit(1)
    
    # Create archive
    create_archive()
    
    # Show summary
    show_summary()
    
    print("\n✓ Inventory complete!")

if __name__ == "__main__":
    main()
