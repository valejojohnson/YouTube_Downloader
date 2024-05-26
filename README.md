# YouTube Downloader
### This is a Python script that takes an individual youtube video URL, or a Youtube playlist URL, and downloads the video(s).

- [x] Asks for individual video URL / Public Playlist URL
- [x] Checks if S3 bucket is present, if not, asks if we'd like to create one
- [x] Starts download of Youtube Video(s)
- [x] Saves downloaded file locally to host machine
- [x] Uploads to S3 bucket
- [x] Creates a folder with channel name, and stores video file inside channel named folder
- [x] If upload to S3 is successful, Deletes local video file from host machine.

# Requirements:
- [x] AWS Credentials stored on host machine
- [x] An S3 bucket created to store the video files

# How to Run: