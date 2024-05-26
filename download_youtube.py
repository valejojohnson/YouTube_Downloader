import os
import re
import boto3
from pytube import YouTube, Playlist
from tqdm import tqdm
from botocore.exceptions import NoCredentialsError

def sanitize_filename(filename):
    return re.sub(r'[^A-Za-z0-9]+', '_', filename)

def download_youtube_video(video_url, save_path):
    try:
        yt = YouTube(video_url)
        video = yt.streams.get_highest_resolution()

        # Initialize progress bar
        total_size = video.filesize
        progress = tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading {yt.title}")

        def progress_function(chunk, file_handle, bytes_remaining):
            progress.update(total_size - bytes_remaining - progress.n)

        yt.register_on_progress_callback(progress_function)
        video_path = video.download(save_path)
        progress.close()

        print(f"Downloaded: {yt.title}")
        return video_path, yt.author, yt.title
    except Exception as e:
        print(f"An error occurred during download: {e}")
        return None, None, None

def upload_to_s3(file_path, bucket_name, s3_file_name):
    s3 = boto3.client('s3')
    total_size = os.path.getsize(file_path)

    progress = tqdm(total=total_size, unit='B', unit_scale=True, desc="Uploading")

    def upload_progress(chunk):
        progress.update(chunk)

    try:
        s3.upload_file(file_path, bucket_name, s3_file_name, Callback=upload_progress)
        progress.close()

        print(f"Upload Successful: {s3_file_name}")
        return True
    except FileNotFoundError:
        print("The file was not found")
        progress.close()
        return False
    except NoCredentialsError:
        print("Credentials not available")
        progress.close()
        return False

def delete_local_file(file_path):
    try:
        os.remove(file_path)
        print(f"Deleted local file: {file_path}")
    except Exception as e:
        print(f"An error occurred while deleting the file: {e}")

def file_exists_in_s3(bucket_name, s3_file_name):
    s3 = boto3.client('s3')
    try:
        s3.head_object(Bucket=bucket_name, Key=s3_file_name)
        print(f"File already exists in S3: {s3_file_name}")
        return True
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise

def bucket_exists(bucket_name):
    s3 = boto3.client('s3')
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket exists: {bucket_name}")
        return True
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise

def create_bucket(bucket_name):
    s3 = boto3.client('s3')
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"Bucket created: {bucket_name}")
        return True
    except Exception as e:
        print(f"An error occurred while creating the bucket: {e}")
        return False

def process_youtube_videos(urls, save_path, bucket_name):
    if not bucket_exists(bucket_name):
        create_bucket_response = input(f"The bucket '{bucket_name}' does not exist. Do you want to create it? (yes/no): ").strip().lower()
        if create_bucket_response == 'yes':
            if not create_bucket(bucket_name):
                print("Failed to create bucket. Exiting.")
                return
        else:
            print("Bucket does not exist and will not be created. Exiting.")
            return

    for url in urls:
        if 'playlist' in url:
            playlist = Playlist(url)
            playlist_folder_name = sanitize_filename(playlist.title)
            for video_url in playlist.video_urls:
                process_single_video(video_url, save_path, bucket_name, playlist_folder_name)
        else:
            process_single_video(url, save_path, bucket_name)

def process_single_video(url, save_path, bucket_name, playlist_folder_name=None):
    yt = YouTube(url)
    s3_folder_name = sanitize_filename(yt.author)
    if playlist_folder_name:
        s3_file_name = f"{s3_folder_name}/{playlist_folder_name}/{sanitize_filename(yt.title)}.mp4"
    else:
        s3_file_name = f"{s3_folder_name}/{sanitize_filename(yt.title)}.mp4"

    if not file_exists_in_s3(bucket_name, s3_file_name):
        video_path, channel_name, title = download_youtube_video(url, save_path)
        if video_path and channel_name and title:
            sanitized_video_path = os.path.join(save_path, sanitize_filename(title) + '.mp4')
            os.rename(video_path, sanitized_video_path)
            if upload_to_s3(sanitized_video_path, bucket_name, s3_file_name):
                delete_local_file(sanitized_video_path)
    else:
        print(f"Skipping download of {yt.title} as it already exists in S3.")

if __name__ == "__main__":
    urls = input("Enter the YouTube video or playlist URLs (comma separated): ").split(',')
    save_path = os.path.expanduser("~/")  # Home directory
    bucket_name = 'bucket-name-goes-here' # Just the bucket name not the full ARN

    process_youtube_videos(urls, save_path, bucket_name)
