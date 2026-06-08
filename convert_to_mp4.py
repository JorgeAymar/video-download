
import os
import subprocess
import glob

def run():
    # Find the webm file
    files = glob.glob("*.webm")
    if not files:
        print("No webm files found.")
        return

    # Pick the most recent or likely one
    latest_file = max(files, key=os.path.getmtime)
    print(f"Found file: {latest_file}")
    
    output_file = os.path.splitext(latest_file)[0] + ".mp4"
    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists.")
        return

    # Simpler filename for ffmpeg command safety
    temp_input = "temp_input.webm"
    temp_output = "temp_output.mp4"
    
    os.rename(latest_file, temp_input)
    
    try:
        print("Starting conversion to MP4 (this may take a while)...")
        # Use simple conversion
        cmd = ["ffmpeg", "-i", temp_input, "-c:v", "libx264", "-c:a", "aac", temp_output]
        subprocess.run(cmd, check=True)
        
        # Rename back
        os.rename(temp_output, output_file)
        os.remove(temp_input) # Remove original webm if successful
        print(f"Conversion complete: {output_file}")
        
    except Exception as e:
        print(f"Error converting: {e}")
        # Restore name
        if os.path.exists(temp_input):
            os.rename(temp_input, latest_file)

if __name__ == "__main__":
    run()
