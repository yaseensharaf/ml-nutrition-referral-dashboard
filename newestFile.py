import os

# The path to the folder containing the CSV files
data_folder = 'data'

# Variable to hold the name of the most recent file
data_recent_file_name = ''
def recent_file(): 
    # Get all files in the folder
    files_in_folder = os.listdir(data_folder)

    # Filter out only CSV files
    csv_files = [file for file in files_in_folder if file.endswith('.csv')]

    # Check if there are any CSV files in the folder
    if csv_files:
        # Assume the first CSV file is the most recent initially
        data_recent_file_name = csv_files[0]
        # Fetch the creation time (or the closest equivalent) of the first file
        most_recent_file_time = os.path.getctime(os.path.join(data_folder, data_recent_file_name))

        # Loop through the CSV files to find the most recent
        for file in csv_files:
            file_path = os.path.join(data_folder, file)
            # Use getctime() to get the file creation time
            file_time = os.path.getctime(file_path)

            # Update if this file's creation time is more recent
            if file_time > most_recent_file_time:
                most_recent_file_time = file_time
                data_recent_file_name = file

        return data_recent_file_name
    else:
        print("No CSV files found in the folder.")

