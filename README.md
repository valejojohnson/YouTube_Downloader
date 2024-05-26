# YouTube Video Downloader and S3 Uploader

This script downloads YouTube videos or playlists, saves them locally, and then uploads them to an Amazon S3 bucket. If the video already exists in the S3 bucket, it skips the download to save time and bandwidth.

## Requirements

- Python 3.6+
- boto3
- pytube
- tqdm

## Setup

Before running the script, make sure you have the following installed:

```bash
pip install boto3 pytube tqdm
```

## How to Run

- Clone this repository or download the script.
- Open a terminal and navigate to the directory containing the script.
- Run the script with the following command: ```python script_name.py```
- Enter the YouTube video or playlist URLs when prompted (comma separated).

The script will process each URL, download the videos, and upload them to the specified S3 bucket. 

## Example Usage

```bash
Enter the YouTube video or playlist URLs (comma separated): https://www.youtube.com/watch?v=dQw4w9WgXcQ,https://www.youtube.com/playlist?list=PLynQtb_VREEqDwCoADCy4FTYuF_xYP9E3
```

## Features

- Sanitize Filenames: Converts video titles to safe filenames by replacing non-alphanumeric characters with underscores.
- Progress Bars: Displays progress bars for both downloading and uploading processes.
- Check Existing Files: Skips downloading if the file already exists in the S3 bucket.
- Bucket Management: Checks if the S3 bucket exists and prompts to create it if not.

## Script Details

- sanitize_filename(filename): Sanitizes the filename by replacing non-alphanumeric characters with underscores.
- download_youtube_video(video_url, save_path): Downloads a YouTube video and returns the local file path, author, and title.
- upload_to_s3(file_path, bucket_name, s3_file_name): Uploads a local file to an S3 bucket.
- delete_local_file(file_path): Deletes the local file after uploading to S3.
- file_exists_in_s3(bucket_name, s3_file_name): Checks if a file already exists in the S3 bucket.
- bucket_exists(bucket_name): Checks if an S3 bucket exists.
- create_bucket(bucket_name): Creates an S3 bucket if it does not exist.
- process_youtube_videos(urls, save_path, bucket_name): Processes multiple YouTube video URLs or playlists.
- process_single_video(url, save_path, bucket_name, playlist_folder_name=None): Processes a single YouTube video URL.

## Host Machine Requirements

Operating System: Any OS that supports Python
Internet connection
AWS account with S3 access
Sufficient storage for downloading videos locally

## Notes

Ensure you have enough space in your local machine to store the downloaded videos before they are uploaded to S3.
The script uses the highest resolution available for downloading videos.
Make sure your AWS credentials are configured properly to allow access to S3.

## Troubleshooting

File Not Found Error: Ensure the file path is correct and you have the necessary permissions.
No Credentials Error: Make sure your AWS credentials are set up correctly.
Feel free to modify the script to suit your needs!

Enjoy downloading and uploading your favorite YouTube videos!