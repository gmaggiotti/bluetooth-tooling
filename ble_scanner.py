import asyncio
import argparse
import sys
from bleak import BleakScanner, BleakClient

async def get_device_info(address: str):
    """Get detailed information about a specific BLE device by address"""
    print(f"Getting detailed information for device: {address}")
    
    try:
        # First, try to find the device through scanning
        print("Scanning for device...")
        device_found = None
        advertisement_info = None
        
        def detection_callback(device, advertisement_data):
            nonlocal device_found, advertisement_info
            if device.address.lower() == address.lower():
                device_found = device
                advertisement_info = advertisement_data
        
        scanner = BleakScanner(detection_callback)
        await scanner.start()
        await asyncio.sleep(10)  # Scan for 10 seconds
        await scanner.stop()
        
        if not device_found:
            print(f"Device with address {address} not found during scan.")
            return
        
        print("\n=== BASIC DEVICE INFORMATION ===")
        print(f"Name: {device_found.name or 'Unknown'}")
        print(f"Address: {device_found.address}")
        print(f"Details: {device_found.details}")
        # print(f"Metadata: {device_found.metadata}")
        
        print("\n=== ADVERTISEMENT DATA ===")
        if advertisement_info:
            print(f"RSSI: {advertisement_info.rssi} dBm")
            print(f"Local Name: {advertisement_info.local_name or 'Not provided'}")
            print(f"TX Power: {advertisement_info.tx_power}")
            print(f"Service UUIDs: {list(advertisement_info.service_uuids) if advertisement_info.service_uuids else 'None'}")
            
            if advertisement_info.manufacturer_data:
                print("Manufacturer Data:")
                for company_id, data in advertisement_info.manufacturer_data.items():
                    print(f"  Company ID {company_id}: {data.hex()}")
            else:
                print("Manufacturer Data: None")
            
            if advertisement_info.service_data:
                print("Service Data:")
                for service_uuid, data in advertisement_info.service_data.items():
                    print(f"  Service {service_uuid}: {data.hex()}")
            else:
                print("Service Data: None")
        
        # Try to connect and get services/characteristics
        print(f"\n=== ATTEMPTING CONNECTION ===")
        try:
            async with BleakClient(address) as client:
                if client.is_connected:
                    print("✓ Successfully connected!")
                    
                    print("\n=== SERVICES AND CHARACTERISTICS ===")
                    
                    for service in client.services:
                        print(f"\nService: {service.uuid}")
                        print(f"  Description: {service.description}")
                        
                        for characteristic in service.characteristics:
                            print(f"  Characteristic: {characteristic.uuid}")
                            print(f"    Description: {characteristic.description}")
                            print(f"    Properties: {characteristic.properties}")
                            
                            for descriptor in characteristic.descriptors:
                                print(f"    Descriptor: {descriptor.uuid}")
                                print(f"      Description: {descriptor.description}")
                else:
                    print("✗ Failed to connect")
        
        except Exception as connect_error:
            print(f"✗ Connection failed: {connect_error}")
            print("  This is normal for many BLE devices that don't accept connections")
    
    except Exception as e:
        print(f"Error getting device information: {e}")


async def scan_ble_devices(scan_time: int = 5, dbm_max: int = -80):
    """Scan for BLE devices and display basic information"""
    print(f"Starting BLE scan for {scan_time} seconds...")
    
    # Dictionary to store discovered devices with their RSSI
    discovered_devices = {}
    
    def detection_callback(device, advertisement_data):
        """Callback function to handle detected devices"""
        discovered_devices[device.address] = {
            'device': device,
            'rssi': advertisement_data.rssi,
            'name': device.name or "Unknown",
            'advertisement_data': advertisement_data
        }
    
    # Create scanner and start scanning
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(scan_time)
    await scanner.stop()
    
    if not discovered_devices:
        print("No BLE devices found.")
        return
    # Filter devices by RSSI
    filtered_devices = {addr: info for addr, info in discovered_devices.items() if info['rssi'] > dbm_max}
    
    if not filtered_devices:
        print(f"No BLE devices found with RSSI > {dbm_max} dBm (found {len(discovered_devices)} total, all filtered out).")
        return
    
    print(f"\nFound {len(filtered_devices)} device(s):")
    print("-" * 80)
    for address, info in filtered_devices.items():
        device_name = info['name']
        rssi = info['rssi']
        ad_data = info['advertisement_data']
        
        print(f"Name: {device_name}")
        print(f"Address: {address}")
        print(f"RSSI: {rssi} dBm")
        
        # Show service UUIDs if available
        if ad_data.service_uuids:
            print(f"Services: {list(ad_data.service_uuids)}")
        
        # Show manufacturer data if available
        if ad_data.manufacturer_data:
            manufacturer_info = []
            for company_id, data in ad_data.manufacturer_data.items():
                manufacturer_info.append(f"ID:{company_id}")
            print(f"Manufacturer: {', '.join(manufacturer_info)}")
        
        print("-" * 40)
    
    print("Scan complete.")


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="BLE Scanner - Scan for BLE devices or get detailed device information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scanner.py                           # Scan for 5 seconds (default)
  python scanner.py --scan-time 10           # Scan for 10 seconds
  python scanner.py --address AA:BB:CC:DD:EE:FF  # Get detailed info for specific device
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--address', '-a',
        type=str,
        help='Get detailed information for a specific device address (e.g., AA:BB:CC:DD:EE:FF)'
    )
    group.add_argument(
        '--scan-time', '-t',
        type=int,
        default=5,
        help='Time in seconds to scan for devices (default: 5)'
    )
    group.add_argument(
        '--dbm-max', '-d',
        type=int,
        default=-80,
        help='Filter out devices with weak signal strength'
    )
    
    args = parser.parse_args()
    
    try:
        if args.address:
            # Get detailed info for specific device
            asyncio.run(get_device_info(args.address))
        else:
            # Scan for devices
            asyncio.run(scan_ble_devices(args.scan_time, args.dbm_max))
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()