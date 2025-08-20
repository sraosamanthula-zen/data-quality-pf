# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy",
#     "pandas",
# ]
# ///

import pandas as pd
import numpy as np

# Define constants for the dataset
num_columns = 15
num_unique_rows = 5000
num_total_rows = 10000

# Generate random data for the first half
data = np.random.randint(0, 100, size=(num_unique_rows, num_columns))

# Duplicate the data to create the second half
duplicated_data = np.vstack((data, data))

# Create a DataFrame with the specific column names
columns = [f'Column{i+1}' for i in range(num_columns)]
df = pd.DataFrame(duplicated_data, columns=columns)

# Save DataFrame to CSV
df.to_csv('data/inputs/test/example_dataset_1.csv', index=False)

# Output the head of the dataframe just to verify
print(df.head())
