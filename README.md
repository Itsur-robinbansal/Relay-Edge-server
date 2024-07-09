# Optimized Data Forwarding and Cache Management System for Networked Edge Servers

## Project Overview

This project involves the development of an optimized data forwarding and cache management system for a network of edge servers. The system is designed to improve responsiveness and efficiency by handling concurrent service requests using multithreading and managing resources with statistical methods and the Landlord algorithm.

## Features

- **Multithreading**: Handles multiple service requests concurrently to improve responsiveness.
- **Cache Management**: Utilizes the Landlord algorithm for efficient resource allocation and cache management.
- **Statistical Methods**: Applies statistical methods to optimize data forwarding and cache utilization.
- **Latency Reduction**: Achieves significant reductions in latency and improves bandwidth utilization.

## Requirements

- Python 3.x
- Required Python libraries: numpy, pandas, threading

## Files in the Repository

- `main.py`: The main script to run the optimized data forwarding and cache management system.
- `testinglord.py`: A script to test the functionalities and performance of the system.
- `Google1-median.csv` to `GoogleN-median.csv`: Sample CSV files used for testing and benchmarking the system.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Itsur-robinbansal/Relay-edge-server
    ```

2. Install the required Python libraries:
    ```bash
    pip install numpy pandas
    ```

## Usage

1. Prepare your CSV files named as `Google1-median.csv`, `Google2-median.csv`, ..., `GoogleN-median.csv`.

2. Run the main script:
    ```bash
    python main.py
    ```

## Contributing

If you would like to contribute to the project, please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries or issues, please open an issue on the repository or contact [Robin Bansal](https://github.com/Itsur-robinbansal).
