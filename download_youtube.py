import os
import re
import sys
import boto3
from pytube import YouTube, Playlist
from tqdm import tqdm
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from colorama import Fore, Style, init

init(autoreset=True)

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

    progress = tqdm(total=total_size, unit='B', unit_scale=True, desc="Uploading to S3")

    def upload_progress(chunk):
        progress.update(chunk)

    try:
        s3.upload_file(file_path, bucket_name, s3_file_name, Callback=upload_progress)
        progress.close()

        print(Fore.GREEN + f"Upload Successful: {s3_file_name}")
        return True
    except FileNotFoundError:
        print(Fore.RED + "The file was not found")
        progress.close()
        return False
    except NoCredentialsError:
        print(Fore.RED + "Credentials not available")
        progress.close()
        return False
    except ClientError as e:
        print(Fore.RED + f"Client error: {e}")
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
    except ClientError as e:
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
    except ClientError as e:
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

def check_credentials(bucket_name):
    s3 = boto3.client('s3')
    try:
        # Check if the credentials can list all buckets
        s3.list_buckets()
        print(Fore.GREEN + "AWS credentials are valid.")

        # Check if the credentials can list the specified bucket's contents
        s3.list_objects_v2(Bucket=bucket_name)
        print(Fore.GREEN + f"Access to bucket '{bucket_name}' is granted.")
        return True
    except NoCredentialsError:
        print(Fore.RED + "AWS credentials are not available or valid.")
        return False
    except PartialCredentialsError:
        print(Fore.RED + "AWS credentials are partially valid.")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print(Fore.RED + f"Access to bucket '{bucket_name}' is denied.")
        else:
            print(Fore.RED + f"An error occurred: {e}")
        return False

def process_youtube_videos(urls, save_path, bucket_name):
    if not bucket_name:
        raise ValueError("No bucket name provided. Please specify a valid S3 bucket name.")

    if not bucket_exists(bucket_name):
        create_bucket_response = input(f"The bucket '{bucket_name}' does not exist. Do you want to create it? (Y/N): ").strip().lower()
        if create_bucket_response == 'y':
            if not create_bucket(bucket_name):
                print("Failed to create bucket. Exiting.")
                return
        elif create_bucket_response == 'n':
            print("Bucket does not exist and will not be created. Exiting.")
            return
        else:
            print("Invalid response. Please enter 'Y' or 'N'.")
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
    bucket_name = ""  # Enter the S3 bucket name here
    if not bucket_name:
        bucket_name = input("Enter the S3 bucket name: ").strip()
        if not bucket_name:
            print(Fore.RED + "Error: No bucket name provided.")
            sys.exit(1)

    if not check_credentials(bucket_name):
        print(Fore.RED + "Exiting due to invalid AWS credentials.")
        sys.exit(1)
    else:
        urls = input("Enter the YouTube video or playlist URLs (comma separated): ").split(',')
        save_path = os.path.expanduser("~/")  # Home directory

        process_youtube_videos(urls, save_path, bucket_name)
