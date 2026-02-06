import requests
import time
import os

# Create directory if it doesn't exist
os.makedirs('downloads/images', exist_ok=True)

# Download 10 images
for i in range(1, 11):
    url = 'https://picsum.photos/400/300'
    filename = f'downloads/images/img_{i:03d}.jpg'
    
    print(f'Downloading image {i}/10...')
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f'Saved: {filename}')
    
    # Sleep 2 seconds between downloads (except after the last one)
    if i < 10:
        time.sleep(2)

print('All images downloaded successfully!')
