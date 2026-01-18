import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import sys

def download_video(iframe_url):
    print(f"Analyzing {iframe_url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Referer": "https://iframe.mediadelivery.net/"
    }

    try:
        # Step 1: Get the iframe content
        response = requests.get(iframe_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Step 2: Extract video URL and title
        video_url_meta = soup.find("meta", property="og:video:url")
        title_meta = soup.find("title")
        
        if not video_url_meta:
            print("Error: Could not find video URL in metadata.")
            return

        video_url = video_url_meta["content"]
        filename = title_meta.text.strip() if title_meta else "video.mp4"
        
        # Sanitize filename
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '-', '_', '.')]).rstrip()
        if not filename.endswith('.mp4'):
            filename += '.mp4'

        print(f"Found video: {filename}")
        print(f"Direct URL: {video_url}")

        # Step 3: Download the video
        print("Starting download...")
        # Use a stream to handle large files
        with requests.get(video_url, headers=headers, stream=True) as r:
            r.raise_for_status()
            total_size_in_bytes = int(r.headers.get('content-length', 0))
            block_size = 1024 * 1024 # 1MB chunk size
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

            with open(filename, 'wb') as f:
                for data in r.iter_content(block_size):
                    progress_bar.update(len(data))
                    f.write(data)
            progress_bar.close()

        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            print("ERROR, something went wrong")
        else:
            print(f"Successfully downloaded: {filename}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    url = "https://iframe.mediadelivery.net/play/371698/d51fedf4-db74-47de-b3fd-585f3ea643f2"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    download_video(url)
