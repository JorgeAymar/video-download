import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
import argparse
import sys

# Target Iframe URLs found on the page (Default fallback)
DEFAULT_URLS = [
    "https://iframe.mediadelivery.net/embed/371698/d51fedf4-db74-47de-b3fd-585f3ea643f2",
    "https://iframe.mediadelivery.net/embed/371698/a8da8e48-799e-48b0-b080-5c28b87d2f6d",
    "https://iframe.mediadelivery.net/embed/371698/db2ee6d4-baac-4c51-aba9-f81f079f1e45",
    "https://iframe.mediadelivery.net/embed/371698/edf08764-f42e-4931-9e54-61f5c8efe1fd"
]

# Headers - Critical for access
# Default Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_headers(url):
    """Return appropriate headers based on the URL domain."""
    headers = DEFAULT_HEADERS.copy()
    
    if "hotmart" in url:
        headers["Referer"] = "https://hotmart.com/"
        headers["Origin"] = "https://hotmart.com"
    elif "sistemalow2high" in url or "iframe.mediadelivery.net" in url:
        headers["Referer"] = "https://sistemalow2high.com/"
        headers["Origin"] = "https://sistemalow2high.com"
    elif "ninjasuite.app.clientclub.net" in url:
        headers["Referer"] = "https://ninjasuite.app.clientclub.net/"
        headers["Origin"] = "https://ninjasuite.app.clientclub.net"
    
    return headers

def sanitize_filename(name):
    """Clean filename."""
    return "".join([c for c in name if c.isalnum() or c in (' ', '-', '_', '.')]).strip()

def download_video(iframe_url):
    print(f"\nProcessing: {iframe_url}")
    
    try:
        # 1. Get the iframe content to find the actual video URL
        # Note: We must use the correct Referer here too
        headers = get_headers(iframe_url)
        r = requests.get(iframe_url, headers=headers)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 2. Extract metadata
        og_video = soup.find("meta", property="og:video:url")
        og_title = soup.find("meta", property="og:title")
        
        if not og_video:
            print(f"FAILED: Could not find video URL in {iframe_url}")
            
            # Fallback: Try to find any MP4 or m3u8 URL in the raw text (often inside JSON blobs)
            import re
            print("Attempting regex search for video file...")
            # Look for common video patterns
            video_pattern = re.search(r'(https?://[^"]+\.(?:mp4|m3u8)[^"]*)', r.text)
            
            if video_pattern:
                video_url = video_pattern.group(1)
                # content-type check or cleaning might be needed, but let's try raw first
                # often json has escaped slashes like https:\/\/...
                video_url = video_url.replace('\\/', '/')
                print(f"Regex found potential video URL: {video_url}")
                
                # Use a default title if not found
                title = og_title["content"] if og_title else f"hotmart_video_{iframe_url[-10:]}"
            else:
                print("Debug: Meta tags found:")
                for meta in soup.find_all("meta"):
                    print(f"  - {meta}")
                return
        else:
            video_url = og_video["content"]
            title = og_title["content"] if og_title else f"video_{iframe_url.split('/')[-1]}"
        
        filename = sanitize_filename(title)
        if not filename.endswith(".mp4"):
            filename += ".mp4"
            
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            if file_size > 1024 * 1024: # 1MB
                print(f"Skipping {filename} (already exists, {file_size/1024/1024:.2f} MB)")
                return
            else:
                print(f"File {filename} exists but is small ({file_size} bytes). Deleting and overwriting...")
                os.remove(filename)

        print(f"Found: {filename}")
        print(f"Source: {video_url}")

        if ".m3u8" in video_url or "loom.com" in video_url:
            print(f"Detected Stream/Loom: {video_url}")
            print(f"Delegating to yt-dlp for robust download...")
            
            # Use yt-dlp which is much better at handling headers/sessions than ffmpeg
            # Pass Referer and User-Agent
            user_agent = headers.get("User-Agent", DEFAULT_HEADERS["User-Agent"])
            
            if "loom.com" in video_url:
                # Loom videos from Ninjasuite need the correct Referer
                # Check directly with ninjasuite referer
                referer = "https://ninjasuite.app.clientclub.net/"
                
                # IMPORTANT: Pass the original Loom Embed URL (iframe_url) to yt-dlp, not the extracted luna URL
                # yt-dlp handles the signature generation better from the embed page.
                target_url = iframe_url
                
                cmd = [
                    "yt-dlp",
                    "--referer", referer,
                    "--force-overwrites",
                    "--recode-video", "mp4",
                    "-o", filename,
                    target_url
                ]
            else:
                 # HLS / Hotmart streams needing specific headers
                 # Origin matches the iframe domain where the player is hosted
                origin = "https://cf-embed.play.hotmart.com"
                
                cmd = [
                    "yt-dlp", 
                    "--referer", iframe_url, 
                    "--user-agent", user_agent,
                    "--add-header", f"Origin: {origin}", 
                    "--force-overwrites",
                    "--recode-video", "mp4",
                    "-o", filename,
                    video_url
                ]
            
            # Run yt-dlp
            import subprocess
            try:
                subprocess.run(cmd, check=True)
                print(f"Done: {filename}")
            except subprocess.CalledProcessError as e:
                print(f"yt-dlp failed: {e}")
            except FileNotFoundError:
                print("Error: yt-dlp not found. Please install it with 'pip install yt-dlp' or 'brew install yt-dlp'.")
                
        else:
            # 3. Direct Download (MP4)
            with requests.get(video_url, headers=headers, stream=True) as v_req:
                v_req.raise_for_status()
                total_size = int(v_req.headers.get('content-length', 0))
                
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    with open(filename, 'wb') as f:
                        for chunk in v_req.iter_content(chunk_size=1024*1024): # 1MB chunks
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                                
            print(f"Done: {filename}")

    except Exception as e:
        print(f"ERROR downloading {iframe_url}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download videos from iframe.mediadelivery.net URLs.")
    parser.add_argument("urls", metavar="URL", type=str, nargs="*", help="Optional list of URLs to download. If empty, uses default list.")
    
    args = parser.parse_args()

    if args.urls:
        target_urls = args.urls
    else:
        # Interactive Mode: Avoids shell quoting/truncation issues
        print("\n--- Interactive Mode ---")
        print("Pegue la URL completa del video aquí y presione Enter (o presione Enter vacío para usar la lista predeterminada):")
        try:
            user_input = input().strip()
        except EOFError:
            user_input = ""
            
        if user_input:
            # Handle potential surrounding quotes from copy-paste
            user_input = user_input.strip("'").strip('"')
            target_urls = [user_input]
        else:
            print("Usando lista predeterminada...")
            target_urls = DEFAULT_URLS

    print(f"Starting batch download of {len(target_urls)} videos...")
    
    for url in target_urls:
        download_video(url)
    
    print("\nAll downloads finished.")
