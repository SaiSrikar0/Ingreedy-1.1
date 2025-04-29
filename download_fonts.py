import os
import requests
from pathlib import Path

# Font URLs (using Google Fonts)
FONT_URLS = {
    'Poppins-Regular': 'https://fonts.gstatic.com/s/poppins/v20/pxiEyp8kv8JHgFVrJJfecg.woff2',
    'Poppins-Light': 'https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLDz8Z1xlFQ.woff2',
    'Poppins-Medium': 'https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLGT9Z1xlFQ.woff2',
    'Poppins-Bold': 'https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLCz7Z1xlFQ.woff2'
}

def download_fonts():
    # Create fonts directory if it doesn't exist
    fonts_dir = Path('app/static/fonts')
    fonts_dir.mkdir(parents=True, exist_ok=True)
    
    # Download each font
    for font_name, url in FONT_URLS.items():
        try:
            # Download woff2 version
            response = requests.get(url)
            response.raise_for_status()
            
            # Save the font file
            font_path = fonts_dir / f'{font_name}.woff2'
            with open(font_path, 'wb') as f:
                f.write(response.content)
            
            print(f'Downloaded {font_name}.woff2')
            
        except Exception as e:
            print(f'Error downloading {font_name}: {e}')

if __name__ == '__main__':
    download_fonts() 