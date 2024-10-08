import configparser
import os
import requests
import subprocess
import shutil

### Getting the discord key from the .env file ###
config = configparser.ConfigParser()
config.read('.env')
groq_key = config['DEFAULT']['GROQ_API_KEY']
directory_path = '/tmp/analyzer'

# Set API key and endpoint URL
# GROQ_API_KEY = "your_api_key_here"
url = "https://api.groq.com/openai/v1/chat/completions"

def check_journalctl_and_export_logs():
    # Check if journalctl exists
    try:
        subprocess.run(["which", "journalctl"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("journalctl is not installed on this system.")
        return

    # Create the /tmp/analyzer directory if it doesn't exist
    os.makedirs("/tmp/analyzer", exist_ok=True)

    # Export error logs (priority err, crit, alert, and emerg)
    error_log_file = "/tmp/analyzer/error_logs.json"
    error_log_command = f"journalctl -p err | tail -1000 > {error_log_file}"
    subprocess.run(error_log_command, shell=True, check=True)

    # Grab the usage from top for performance analytics
    top_file = "/tmp/analyzer/performance_logs.json"
    top_command = f"top -b -n 1 > top_snapshot.txt | tail -50 > {top_file}"
    subprocess.run(error_log_command, shell=True, check=True)

    print("Logs exported successfully to /tmp/analyzer/")

    
def remove_tmp_dir():
    tmp_dir = "/tmp/analyzer"
    if os.path.exists(tmp_dir):
        try:
            shutil.rmtree(tmp_dir)
            print(f"Removed {tmp_dir} directory.")
        except Exception as e:
            print(f"Error removing {tmp_dir} directory: {e}")
    else:
        print(f"{tmp_dir} directory does not exist.")

def send_log_files_to_groq(api_key, directory_path, api_endpoint):
    # """
    # Sends all log files in the specified directory to the Groq API.

    # Args:
    #     api_key (str): The Groq API key.
    #     directory_path (str): The path to the directory containing log files.
    #     api_endpoint (str): The Groq API endpoint URL.

    # Returns:
    #     None
    # """
    # Set up headers for the request
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Check if the directory exists
    if os.path.exists(directory_path):
        # List all log files in the directory
        all_files = [f for f in os.listdir(directory_path)]
        for file_name in all_files:
            file_path = os.path.join(directory_path, file_name)
            
            # Check if the current item is a file
            if os.path.isfile(file_path):
                # Read the file content
                with open(file_path, 'r') as file:
                    file_data = file.read()
            
            # Prepare the data to send
            data = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Analyze this log and provide any helpful troubleshooting tips for any issues that are found. Dont report on anything that is harmless and can be ignored. Only report on actionable items that are a priority for troubleshooting.\n\
                    Responses should be formatted like the following example:\n\
                    // AUTH ISSUES //\n\
                    Describe any issues with authorization here.\n\
                    // RECOMMENDATION //\n\
                    Describe any troubleshooting tips for the authorization issues found.\n\
                    \n\n\
                    // SYSTEM ISSUES //\n\
                    Describe any issues with the system here.\n\
                    // RECOMMENDATION //\n\
                    \n\n\
                    // PERFORMANCE ISSUES //\n\
                    Describe any issues with the system here.\n\
                    // RECOMMENDATION //\n\
                    Describe any troubleshooting tips for the system issues found.\n\
                    \
                    Log data:\n{file_data}"
                }
            ],
            "model": "llama-3.1-70b-versatile",
            "temperature": 0,
            "max_tokens": 1024,
            # "top_p": 1,
            "stream": False,
            "stop": None
            }

            # Send the data to Groq API
            response = requests.post(api_endpoint, json=data, headers=headers)
            # Make the HTTP request
            # response = requests.post(url, headers=headers, data=json.dumps(data))

            # Get the response content as a JSON object
            response_json = response.json()
            groq_response= (response_json['choices'][0]['message']['content'])
                        
            
            
            # Print response
            # print(f'Response from Groq API for {log_file}:', response.json())
            print(groq_response)
    else:
        print(f'{directory_path} directory does not exist.')

# # Example usage

# 
# api_endpoint = 'https://api.groq.com/openai/v1/chat/completions'


if __name__ == "__main__":
    check_journalctl_and_export_logs()
    send_log_files_to_groq(groq_key, directory_path, url)
    remove_tmp_dir()
    