from firebase_admin import credentials, storage
import firebase_admin

cred = credentials.Certificate("opticalmarkrecognition-f7059-firebase-adminsdk-ytgau-c14ddee08f.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'opticalmarkrecognition-f7059.appspot.com'  # Replace with your Firebase storage bucket
})



def upload_file_to_firebase(local_file_path, filename=None):
    """
    Uploads a file from a local path to Firebase Storage and returns the download URL.
    
    :param local_file_path: The local path of the file to upload.
    :param filename: The desired filename for the file in Firebase Storage (if None, uses the original filename).
    :return: The public download URL of the uploaded file.
    """
    try:
        # Use the provided filename or derive from the local file path
        if not filename:
            filename = local_file_path.split('/')[-1]
        
        # Get the Firebase storage bucket
        bucket = storage.bucket()
        blob = bucket.blob(filename)

        # Upload the local file to Firebase Storage
        blob.upload_from_filename(local_file_path)

        # Make the blob publicly accessible
        blob.make_public()

        # Get the download URL
        download_url = blob.public_url

        print(f"File uploaded successfully. Download URL: {download_url}")
        return download_url

    except Exception as e:
        print(f"Error uploading file: {e}")
        return None