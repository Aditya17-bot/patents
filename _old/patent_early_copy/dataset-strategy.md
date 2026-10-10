# Dataset Search Strategy for Patent Validation

## General Approach

1. Identify the patent's primary technical domain
2. Determine what physical parameters need validation
3. Search Kaggle for datasets with those parameters
4. Prefer datasets with: sensor readings, time-series data, spatial coordinates, physical measurements

## Domain-Specific Search Patterns

### Agriculture / Precision Farming
Search queries:
- "precision agriculture sensor data"
- "soil moisture sensor dataset"
- "crop spraying GPS data"
- "agricultural IoT sensor readings"
- "smart irrigation dataset"

Look for columns: GPS coordinates, soil moisture, temperature, humidity, flow rate, timestamps, field boundaries

### Healthcare / Medical Devices
Search queries:
- "patient monitoring sensor data"
- "ECG EEG physiological signals"
- "medical IoT dataset"
- "clinical sensor readings"

Look for columns: vital signs, timestamps, device IDs, dosage values, patient parameters

### IoT / Cyber-Physical Systems
Search queries:
- "IoT sensor data anomaly detection"
- "industrial IoT sensor readings"
- "smart building sensor data"
- "SCADA system data"

Look for columns: sensor readings, actuator states, timestamps, device IDs, control signals

### Digital Forensics / Security
Search queries:
- "network intrusion detection dataset"
- "digital forensics dataset"
- "cyber security log data"
- "malware detection features"

Look for columns: timestamps, source/destination, protocol data, feature vectors, labels

### Energy / Carbon / Cloud
Search queries:
- "energy consumption dataset"
- "carbon emissions data center"
- "cloud workload traces"
- "renewable energy generation data"

Look for columns: power consumption, carbon intensity, timestamps, workload metrics, resource utilization

### Quantum Computing
Search queries:
- "quantum computing benchmark"
- "quantum circuit simulation results"
- "qubit error rates dataset"

Look for columns: gate fidelity, error rates, circuit depth, execution time, qubit counts

## Kaggle MCP Integration Instructions

Include these exact instructions in the Antigravity prompt:

```
KAGGLE DATASET DOWNLOAD:
1. Use Kaggle MCP tool to search: kaggle.datasets.list(search="[search term]")
2. Download: kaggle.datasets.download("[owner/dataset-name]")
3. The dataset will be downloaded as a zip file
4. Unzip: import zipfile; zipfile.ZipFile('[filename].zip').extractall('[target_dir]')
5. Load with pandas: pd.read_csv('[path_to_csv]')
6. Explore: df.head(), df.describe(), df.columns
```

## Dataset Quality Criteria

A good dataset for patent validation should have:
- ≥500 rows (preferably ≥1000 for statistical significance)
- Real-world measurements (not synthetic)
- Timestamps or sequential ordering
- Multiple feature columns that map to patent components
- Documented column descriptions
- Appropriate license for research use
