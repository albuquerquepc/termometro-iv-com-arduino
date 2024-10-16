import serial
import time

# Configure the serial port. Replace 'COM3' with your port name
SERIAL_PORT = '/dev/ttyACM0'  # Change this to your Arduino's port
BAUD_RATE = 9600  # Same baud rate as in Arduino code

def main():
    try:
        # Initialize the serial connection
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            time.sleep(2)  # Give time for the connection to establish
            
            print("Reading data from Arduino...")
            while True:
                # Read a line from the serial output
                line = ser.readline()  # Read raw bytes
                if line:  # Check if the line is not empty
                    try:
                        decoded_line = line.decode('utf-8').strip()  # Try to decode
                        print(f"Received: {decoded_line}")  # Print the data to the terminal
                    except UnicodeDecodeError:
                        # If decoding fails, print the byte values
                        print(f"Received raw bytes: {line.hex()}")  # Print in hex format

    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    except KeyboardInterrupt:
        print("Program terminated by user.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
