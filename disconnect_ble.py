import asyncio
from bleak import BleakScanner, BleakClient

async def scan_and_disconnect_devices():
    """
    Scan for BLE devices, connect to each, list services, and disconnect.
    """
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=5.0)
    
    if not devices:
        print("No BLE devices found")
        return
    
    print(f"\nFound {len(devices)} device(s):\n")
    
    for device in devices:
        print(f"Device: {device.name or 'Unknown'} ({device.address})")
        
        try:
            # Connect to the device
            async with BleakClient(device.address, timeout=5.0) as client:
                print(f"  ✓ Connected: {client.is_connected}")
                
                # List all services
                print(f"  Services found: {len(client.services)}")
                for service in client.services:
                    print(f"    Service: {service.uuid}")
                    for char in service.characteristics:
                        print(f"      Characteristic: {char.uuid} (Properties: {char.properties})")
                
                print(f"  ✓ Disconnected from {device.address}")
                # The 'async with' block automatically disconnects when exiting
                
        except Exception as e:
            print(f"  ✗ Skipping (device not available or cannot connect): {e}")
        
        print()  # Empty line between devices

def main():
    asyncio.run(scan_and_disconnect_devices())

if __name__ == "__main__":
    main()
