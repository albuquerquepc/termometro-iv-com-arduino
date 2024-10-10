import serial
import serial.tools.list_ports
import time

def list_serial_ports():
    """List all available serial ports."""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def read_from_serial(port, baud_rate=9600):
    """Continuously read from the specified serial port and print the output."""
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            print(f"Connected to {port} at {baud_rate} baud.")
            while True:
                # Read the line from the serial port
                line = ser.readline().decode('utf-8').strip()
                
                # Print the line to the terminal
                if line:
                    print(f"Received: {line}")
                time.sleep(0.1)  # Sleep briefly to avoid flooding the terminal
    except serial.SerialException as e:
        print(f"Error connecting to {port}: {e}")
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")

if __name__ == "__main__":
    print("Available serial ports:")
    ports = list_serial_ports()
    if not ports:
        print("No serial ports found!")
    else:
        for i, port in enumerate(ports):
            print(f"{i}: {port}")
        
        # Ask the user to choose a port
        port_index = int(input(f"Select a port by index (0 to {len(ports)-1}): "))
        selected_port = ports[port_index]
        
        # Start reading from the selected port
        read_from_serial(selected_port)
