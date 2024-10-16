from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
import os
from flask import Flask, render_template, request, send_file, redirect, url_for

app = Flask(__name__)

# Get Azure Storage details from environment variables or configuration
AZURE_STORAGE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
BLOB_CONTAINER_NAME = os.getenv('BLOB_CONTAINER_NAME')
FILE_SHARE_PATH = "/mnt/myfiles"  # Path to your mounted Azure File Share

# Use Azure Managed Identity or other credentials
credential = DefaultAzureCredential()

blob_service_client = BlobServiceClient(
    account_url=f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=credential
)

container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

# Route to list files in Azure Blob Storage
@app.route('/')
def list_files():
    blob_list = container_client.list_blobs()
    return render_template('index.html', blobs=blob_list)

# Route to upload file to Azure Blob Storage
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    uploaded_file = request.files['file']
    blob_client = container_client.get_blob_client(uploaded_file.filename)

    # Upload the file to Azure Blob Storage
    blob_client.upload_blob(uploaded_file.read(), overwrite=True)

    return redirect(url_for('list_files'))

# Route to download files from Azure Blob Storage
@app.route('/download/<blob_name>')
def download_file(blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    download_stream = blob_client.download_blob()

    # Save the downloaded file temporarily
    local_filename = os.path.join('/tmp', blob_name)
    with open(local_filename, 'wb') as f:
        f.write(download_stream.readall())

    # Send the file to the client
    return send_file(local_filename, as_attachment=True)

# Route to list files in Azure File Share
@app.route('/list-files')
def list_azure_files():
    files = os.listdir(FILE_SHARE_PATH)
    return render_template('index.html', files=files)

# Route to upload file to Azure File Share
@app.route('/upload-to-file-share', methods=['POST'])
def upload_to_file_share():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    uploaded_file = request.files['file']
    file_path = os.path.join(FILE_SHARE_PATH, uploaded_file.filename)

    # Save the file to the Azure File Share
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.read())

    return redirect(url_for('list_azure_files'))

if __name__ == '__main__':
    app.run(debug=True)
